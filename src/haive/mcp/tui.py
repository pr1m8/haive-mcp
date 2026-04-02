"""Interactive TUI for MCP server discovery and installation.

A navigable terminal interface built with Rich. Browse categories,
search servers, view details, generate configs, and install -- all
with numbered menus instead of free-form commands.

Usage:
    haive-mcp self-query
    python -m haive.mcp self-query
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from haive.mcp.self_query import MCPSelfQuery

console = Console()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_server_table(
    servers: list[dict[str, Any]],
    title: str = "Servers",
    show_index: bool = True,
) -> Table:
    """Build a Rich table of servers."""
    table = Table(title=title, show_lines=False, pad_edge=False, expand=True)
    if show_index:
        table.add_column("#", style="bold cyan", width=4, justify="right")
    table.add_column("Name", style="bold white", ratio=3)
    table.add_column("Category", style="dim", ratio=1)
    table.add_column("Install Command", style="green", ratio=3)

    for i, s in enumerate(servers, 1):
        name = s.get("name", "?")
        cat = s.get("category", "")
        cmd = s.get("install_command", "")
        row = [name, cat, cmd or "[dim]--[/dim]"]
        if show_index:
            row.insert(0, str(i))
        table.add_row(*row)

    return table


def _make_detail_panel(detail: dict[str, Any]) -> Panel:
    """Build a Rich panel with server detail."""
    lines: list[str] = []

    if detail.get("description"):
        lines.append(f"[italic]{detail['description'][:200]}[/italic]")
        lines.append("")

    fields = [
        ("Category", detail.get("category")),
        ("Repository", detail.get("repository_url")),
        ("Install", detail.get("install_command")),
        ("Stars", detail.get("stars")),
        ("Languages", ", ".join(detail.get("languages", [])) or None),
        ("License", detail.get("license")),
    ]
    for label, value in fields:
        if value:
            lines.append(f"[bold]{label}:[/bold] {value}")

    setup = detail.get("setup_info", {})
    if setup.get("installation"):
        lines.append("")
        lines.append("[bold]Install steps:[/bold]")
        for step in setup["installation"][:5]:
            lines.append(f"  [green]$ {step}[/green]")

    if setup.get("capabilities"):
        lines.append("")
        lines.append(f"[bold]Capabilities:[/bold] {', '.join(setup['capabilities'][:8])}")

    return Panel(
        "\n".join(lines) if lines else "[dim]No details available[/dim]",
        title=f"[bold cyan]{detail.get('name', '?')}[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )


# ------------------------------------------------------------------
# Screens
# ------------------------------------------------------------------

def _show_main_menu(sq: MCPSelfQuery) -> str:
    """Show the main menu and return the user's choice."""
    console.print()
    console.print(
        Panel(
            f"[bold]haive-mcp[/bold]  ·  [cyan]{sq.server_count}[/cyan] MCP servers",
            border_style="bright_blue",
            padding=(0, 2),
        )
    )
    console.print()
    console.print("  [bold cyan]1[/bold cyan]  Search servers")
    console.print("  [bold cyan]2[/bold cyan]  Browse categories")
    console.print("  [bold cyan]3[/bold cyan]  Install a server")
    console.print("  [bold cyan]4[/bold cyan]  Generate config")
    console.print("  [bold cyan]q[/bold cyan]  Quit")
    console.print()
    return Prompt.ask("Choose", choices=["1", "2", "3", "4", "q"], default="1")


def _search_screen(sq: MCPSelfQuery) -> list[dict[str, Any]]:
    """Search screen -- returns selected results."""
    query = Prompt.ask("\n[bold]Search[/bold]")
    if not query.strip():
        return []

    results = sq.search(query, limit=15)
    if not results:
        console.print(f"[dim]No servers found for '{query}'[/dim]")
        return []

    # Enrich with install commands
    enriched = []
    for r in results:
        detail = sq.get_server_detail(r["name"])
        enriched.append({
            **r,
            "install_command": (detail or {}).get("install_command", ""),
        })

    console.print()
    console.print(_make_server_table(enriched, title=f"Results for '{query}'"))
    return enriched


def _pick_server(servers: list[dict[str, Any]], sq: MCPSelfQuery) -> dict[str, Any] | None:
    """Let user pick a server from a list, then show detail."""
    if not servers:
        return None

    console.print()
    try:
        idx = IntPrompt.ask(
            "Select server #  [dim](0 to go back)[/dim]",
            default=0,
        )
    except (KeyboardInterrupt, EOFError):
        return None

    if idx < 1 or idx > len(servers):
        return None

    server = servers[idx - 1]
    detail = sq.get_server_detail(server["name"])
    if detail:
        console.print()
        console.print(_make_detail_panel(detail))
    return detail


def _categories_screen(sq: MCPSelfQuery) -> list[dict[str, Any]]:
    """Browse categories and pick one."""
    cats = sq.get_categories()
    cat_list = list(cats.items())

    table = Table(title="Categories", show_lines=False, expand=True)
    table.add_column("#", style="bold cyan", width=4, justify="right")
    table.add_column("Category", style="bold white", ratio=2)
    table.add_column("Servers", style="dim", ratio=1, justify="right")

    for i, (cat, count) in enumerate(cat_list, 1):
        table.add_row(str(i), cat, str(count))

    console.print()
    console.print(table)
    console.print()

    try:
        idx = IntPrompt.ask(
            "Select category #  [dim](0 to go back)[/dim]",
            default=0,
        )
    except (KeyboardInterrupt, EOFError):
        return []

    if idx < 1 or idx > len(cat_list):
        return []

    cat_name = cat_list[idx - 1][0]
    results = sq.loader.search_servers_by_category(cat_name)

    enriched = []
    for r in results[:20]:
        name = r.get("name", "?")
        detail = sq.get_server_detail(name)
        enriched.append({
            **r,
            "install_command": (detail or {}).get("install_command", ""),
        })

    console.print()
    console.print(_make_server_table(enriched, title=f"Category: {cat_name}"))
    return enriched


def _install_screen(sq: MCPSelfQuery) -> None:
    """Full install flow: search → pick → approve → connect."""
    query = Prompt.ask("\n[bold]Search to install[/bold]")
    if not query.strip():
        return

    results = sq.search(query, limit=10)
    if not results:
        console.print(f"[dim]No servers found for '{query}'[/dim]")
        return

    enriched = []
    for r in results:
        detail = sq.get_server_detail(r["name"])
        enriched.append({
            **r,
            "install_command": (detail or {}).get("install_command", ""),
        })

    console.print()
    console.print(_make_server_table(enriched, title=f"Install: '{query}'"))
    console.print()

    try:
        idx = IntPrompt.ask(
            "Select server to install #  [dim](0 to cancel)[/dim]",
            default=0,
        )
    except (KeyboardInterrupt, EOFError):
        return

    if idx < 1 or idx > len(enriched):
        return

    server = enriched[idx - 1]

    # Plan
    from haive.mcp.installer_service import MCPInstallerService

    async def _do_install():
        svc = MCPInstallerService(require_approval=False)
        plan = await svc.plan_install(server["name"])
        if plan is None:
            console.print("[red]Could not create install plan.[/red]")
            return

        console.print()
        console.print(Panel(
            f"[bold]Server:[/bold]  {plan.server_name}\n"
            f"[bold]Command:[/bold] [green]{plan.install_command}[/green]\n"
            f"[bold]Method:[/bold]  {plan.method.value} ({plan.confidence:.0%} confidence)"
            + (f"\n[bold]Repo:[/bold]    {plan.repository_url}" if plan.repository_url else ""),
            title="[bold yellow]Install Plan[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        ))
        console.print()

        if not Confirm.ask("Proceed with installation?", default=True):
            console.print("[dim]Cancelled.[/dim]")
            return

        with console.status("[bold green]Connecting..."):
            result = await svc.install(plan)

        if result.success:
            console.print(f"\n[bold green]Success![/bold green] {result.message}")
            if result.tools_discovered:
                tool_table = Table(title="Discovered Tools", show_lines=False)
                tool_table.add_column("Tool", style="green")
                for t in result.tools_discovered:
                    tool_table.add_row(t)
                console.print()
                console.print(tool_table)
        else:
            console.print(f"\n[bold red]Failed:[/bold red] {result.message}")

        # Offer config export
        console.print()
        if Confirm.ask("Export config?", default=True):
            _show_configs(svc, plan.server_name)

    asyncio.run(_do_install())


def _config_screen(sq: MCPSelfQuery) -> None:
    """Generate configs for a server."""
    query = Prompt.ask("\n[bold]Server name or search[/bold]")
    if not query.strip():
        return

    # Try direct match first, then search
    config = sq.loader.generate_server_config(query)
    server_name = query

    if config is None:
        results = sq.search(query, limit=5)
        if not results:
            console.print(f"[dim]No servers found for '{query}'[/dim]")
            return

        enriched = []
        for r in results:
            detail = sq.get_server_detail(r["name"])
            enriched.append({**r, "install_command": (detail or {}).get("install_command", "")})

        console.print()
        console.print(_make_server_table(enriched, title="Select server"))
        console.print()

        try:
            idx = IntPrompt.ask("Select #  [dim](0 to cancel)[/dim]", default=0)
        except (KeyboardInterrupt, EOFError):
            return
        if idx < 1 or idx > len(enriched):
            return

        server_name = enriched[idx - 1]["name"]
        config = sq.loader.generate_server_config(server_name)

    if config is None:
        console.print("[dim]Could not generate config.[/dim]")
        return

    from haive.mcp.installer_service import MCPInstallerService
    svc = MCPInstallerService(require_approval=False)
    _show_configs(svc, server_name)


def _show_configs(svc: Any, server_name: str) -> None:
    """Display configs in all formats."""
    lc = svc.generate_langchain_config(server_name)
    claude = svc.generate_claude_desktop_config(server_name)

    if lc:
        console.print(Panel(
            json.dumps(lc, indent=2),
            title="[bold]langchain-mcp-adapters[/bold]",
            border_style="green",
        ))

    if claude:
        console.print(Panel(
            json.dumps(claude, indent=2),
            title="[bold]Claude Desktop (mcp.json)[/bold]",
            border_style="blue",
        ))


# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------

def run_tui():
    """Run the navigable TUI."""
    sq = MCPSelfQuery()

    while True:
        try:
            choice = _show_main_menu(sq)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye![/dim]")
            break

        if choice == "q":
            console.print("[dim]Bye![/dim]")
            break

        elif choice == "1":
            servers = _search_screen(sq)
            if servers:
                detail = _pick_server(servers, sq)
                if detail and detail.get("install_command"):
                    console.print()
                    if Confirm.ask("Install this server?", default=False):
                        _install_from_detail(sq, detail)

        elif choice == "2":
            servers = _categories_screen(sq)
            if servers:
                detail = _pick_server(servers, sq)
                if detail and detail.get("install_command"):
                    console.print()
                    if Confirm.ask("Install this server?", default=False):
                        _install_from_detail(sq, detail)

        elif choice == "3":
            _install_screen(sq)

        elif choice == "4":
            _config_screen(sq)


def _install_from_detail(sq: MCPSelfQuery, detail: dict[str, Any]) -> None:
    """Install a server from its detail dict."""
    from haive.mcp.installer_service import MCPInstallerService

    async def _go():
        svc = MCPInstallerService(require_approval=False)
        plan = await svc.plan_install(detail["name"])
        if plan is None:
            console.print("[red]Could not plan install.[/red]")
            return

        console.print(f"\n  [green]{plan.install_command}[/green]")
        console.print()
        if not Confirm.ask("Proceed?", default=True):
            return

        with console.status("[bold green]Connecting..."):
            result = await svc.install(plan)

        if result.success:
            console.print(f"[bold green]Success![/bold green] {result.message}")
            if result.tools_discovered:
                for t in result.tools_discovered[:10]:
                    console.print(f"  [green]·[/green] {t}")
        else:
            console.print(f"[bold red]Failed:[/bold red] {result.message}")

    asyncio.run(_go())
