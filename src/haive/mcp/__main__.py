"""CLI entry point for haive-mcp.

Usage:
    python -m haive.mcp [command] [options]
    haive-mcp [command] [options]
"""

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="haive-mcp")
def cli():
    """haive-mcp - Dynamic MCP integration for Haive agents."""


@cli.command()
def status():
    """Show status of configured MCP servers."""
    from haive.mcp.config import MCPConfig

    config = MCPConfig()
    click.echo(f"MCP enabled: {config.enabled}")
    click.echo(f"Servers configured: {len(config.servers)}")
    click.echo(f"Auto-discover: {config.auto_discover}")
    click.echo(f"Health checks: {config.enable_health_checks}")


@cli.command()
@click.argument("capability", required=False, default=None)
def discover(capability: str | None):
    """Discover MCP servers by capability.

    If no capability is specified, lists all available categories.
    """
    from haive.mcp.self_query import MCPSelfQuery

    engine = MCPSelfQuery()
    click.echo(f"MCP Server Database: {engine.server_count} servers\n")

    if capability:
        results = engine.search(capability)
        click.echo(f"Found {len(results)} servers matching '{capability}':\n")
        for s in results[:15]:
            name = s.get("name", "?")
            desc = (s.get("description") or "")[:60]
            click.echo(f"  {name}")
            if desc:
                click.echo(f"    {desc}")
    else:
        cats = engine.get_categories()
        click.echo("Categories:\n")
        for cat, count in cats.items():
            click.echo(f"  {cat:<30} ({count} servers)")


@cli.command("self-query")
def self_query_cmd():
    """Interactive TUI for browsing, searching, and installing MCP servers."""
    from haive.mcp.tui import run_tui

    run_tui()


@cli.command()
@click.argument("query")
@click.option("--no-approve", is_flag=True, help="Skip HITL approval")
@click.option("--format", "fmt", type=click.Choice(["haive", "langchain", "claude"]),
              default="langchain", help="Config output format")
def install(query: str, no_approve: bool, fmt: str):
    """Search, plan, approve, and install an MCP server.

    Full pipeline: search DB → derive install cmd → HITL approve → connect & verify.
    Falls back to LLM if README extraction fails.
    """
    import asyncio
    from haive.mcp.installer_service import MCPInstallerService

    async def _run():
        service = MCPInstallerService(require_approval=not no_approve)

        # Search
        results = service.search(query, limit=5)
        if not results:
            click.echo(f"No servers found for '{query}'")
            return

        click.echo(f"\nFound {len(results)} servers for '{query}':\n")
        for i, r in enumerate(results[:5], 1):
            detail = service.get_detail(r["name"])
            cmd = (detail or {}).get("install_command", "(unknown)")
            click.echo(f"  {i}. {r['name']}")
            if cmd:
                click.echo(f"     {cmd}")

        # Plan install for top result
        click.echo()
        plan = await service.plan_install(results[0]["name"])
        if plan is None:
            click.echo("Could not create install plan.")
            return

        # Show plan
        click.echo(f"Install plan:")
        click.echo(f"  Server:  {plan.server_name}")
        click.echo(f"  Command: {plan.install_command}")
        click.echo(f"  Method:  {plan.method.value}")

        # Approve
        approved = await service.approve(plan)
        if not approved:
            click.echo("Installation rejected.")
            return

        # Install
        click.echo(f"\nConnecting to {plan.server_name}...")
        result = await service.install(plan)

        if result.success:
            click.echo(f"Success! {result.message}")
            if result.tools_discovered:
                click.echo(f"Tools: {', '.join(result.tools_discovered[:10])}")
        else:
            click.echo(f"Failed: {result.message}")

        # Output config in requested format
        click.echo(f"\nConfig ({fmt}):")
        import json as _json
        if fmt == "langchain":
            cfg = service.generate_langchain_config(plan.server_name)
        elif fmt == "claude":
            cfg = service.generate_claude_desktop_config(plan.server_name)
        else:
            cfg = plan.config
        click.echo(_json.dumps(cfg, indent=2))

    asyncio.run(_run())


@cli.command()
def transports():
    """List supported transport types."""
    from haive.mcp.config import MCPTransport

    click.echo("Supported MCP transport types:\n")
    for transport in MCPTransport:
        descriptions = {
            "stdio": "Standard I/O (subprocess) - most common, works with npx/uvx",
            "sse": "Server-Sent Events (HTTP streaming)",
            "streamable_http": "HTTP streaming for continuous data",
            "docker": "Docker container (isolated execution)",
        }
        desc = descriptions.get(transport.value, "")
        click.echo(f"  {transport.value:<20} {desc}")


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
