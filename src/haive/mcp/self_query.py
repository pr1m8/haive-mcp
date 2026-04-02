"""Self-query interface for MCP server discovery.

Provides an interactive textual interface for querying the MCP server database,
searching by capability, category, or free-text, and getting installation
instructions for discovered servers.

Usage:
    poetry run python -m haive.mcp discover
    poetry run python -m haive.mcp self-query
"""

from __future__ import annotations

import json
import logging
from typing import Any

from haive.mcp.documentation.doc_loader import MCPDocumentationLoader

logger = logging.getLogger(__name__)


class MCPSelfQuery:
    """Self-query engine for the MCP server database.

    Provides search, filtering, and detail retrieval for the 1,960+ MCP servers
    in the pre-indexed database.
    """

    def __init__(self, loader: MCPDocumentationLoader | None = None):
        self.loader = loader or MCPDocumentationLoader()
        self._servers: dict[str, dict[str, Any]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Load server data if not already loaded."""
        if not self._loaded:
            self._servers = self.loader.load_all_mcp_documents()
            self._loaded = True

    @property
    def server_count(self) -> int:
        """Total number of servers in the database."""
        self._ensure_loaded()
        return len(self._servers)

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search servers by free-text query.

        Searches across name, description, category, and source fields.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of matching server documents, sorted by relevance
        """
        self._ensure_loaded()
        if not query.strip():
            return []
        query_lower = query.lower()
        scored: list[tuple[int, dict[str, Any]]] = []

        for server in self._servers.values():
            score = 0
            name = (server.get("name") or "").lower()
            desc = (server.get("description") or "").lower()
            category = (server.get("category") or "").lower()
            source = (server.get("source") or "").lower()
            repo = (server.get("repository_url") or "").lower()

            # Exact name match
            if query_lower == name:
                score += 100
            elif query_lower in name:
                score += 50
            # Description match
            if query_lower in desc:
                score += 20
            # Category match
            if query_lower in category:
                score += 30
            # Source/repo match
            if query_lower in source or query_lower in repo:
                score += 10

            if score > 0:
                scored.append((score, server))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:limit]]

    def get_categories(self) -> dict[str, int]:
        """Get all server categories with counts.

        Returns:
            Dictionary mapping category names to server counts
        """
        self._ensure_loaded()
        categories: dict[str, int] = {}
        for server in self._servers.values():
            cat = server.get("category") or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1
        return dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))

    def get_server_detail(self, name: str) -> dict[str, Any] | None:
        """Get detailed information about a specific server.

        Enriches the server with data from its individual document file
        (full README, description, stars, derived install command).

        Args:
            name: Server name (exact or partial match)

        Returns:
            Server detail dictionary or None
        """
        self._ensure_loaded()

        # Use enriched data (pulls from documents/ files)
        enriched = self.loader.get_enriched_server(name)
        if enriched is None:
            return None

        return self._build_detail(enriched)

    def _build_detail(self, server: dict[str, Any]) -> dict[str, Any]:
        """Build a detailed view of a server."""
        setup = self.loader.extract_setup_info(server)
        return {
            "name": server.get("name", ""),
            "description": server.get("description", ""),
            "category": server.get("category", ""),
            "repository_url": server.get("repository_url", ""),
            "source": server.get("source", ""),
            "install_command": server.get("install_command", ""),
            "stars": server.get("stars"),
            "languages": server.get("languages", []),
            "license": server.get("license"),
            "setup_info": setup,
        }


def _print_results(results: list[dict[str, Any]], limit: int = 20) -> None:
    """Print search results."""
    for i, s in enumerate(results[:limit], 1):
        desc = (s.get("description") or "")[:65]
        name = s.get("name", "?")
        cat = s.get("category", "")
        line = f"  {i:2}. {name}"
        if cat:
            line += f"  [{cat}]"
        print(line)
        if desc:
            print(f"      {desc}")


def _print_detail(detail: dict[str, Any]) -> None:
    """Print server detail."""
    name = detail["name"]
    print(f"\n  {name}")
    print(f"  {'=' * len(name)}")
    if detail.get("description"):
        print(f"  {detail['description'][:120]}")
    if detail.get("category"):
        print(f"  Category:  {detail['category']}")
    if detail.get("repository_url"):
        print(f"  Repo:      {detail['repository_url']}")
    if detail.get("install_command"):
        print(f"  Install:   {detail['install_command']}")
    if detail.get("stars"):
        print(f"  Stars:     {detail['stars']}")
    if detail.get("languages"):
        print(f"  Languages: {', '.join(detail['languages'])}")
    if detail.get("license"):
        print(f"  License:   {detail['license']}")
    setup = detail.get("setup_info", {})
    if setup.get("installation"):
        print(f"  Steps:")
        for step in setup["installation"][:5]:
            print(f"    $ {step}")
    if setup.get("capabilities"):
        print(f"  Capabilities: {', '.join(setup['capabilities'][:10])}")


def run_interactive():
    """Run the interactive self-query interface with install support."""
    import asyncio
    import json as _json

    query_engine = MCPSelfQuery()
    _last_results: list[dict[str, Any]] = []

    print(f"\n  haive-mcp  |  {query_engine.server_count} MCP servers")
    print(f"  {'=' * 42}")
    print("  Commands:")
    print("    <query>             Search servers (default action)")
    print("    detail <name>       Show server details + install command")
    print("    install <name>      Search, plan, approve, and install")
    print("    config <name>       Generate configs (langchain, claude, haive)")
    print("    categories          List all categories")
    print("    category <name>     List servers in a category")
    print("    help                Show this help")
    print("    quit                Exit")
    print()

    while True:
        try:
            user_input = input("mcp> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("quit", "exit", "q"):
            break

        elif cmd == "help":
            print("  search <query>   Search servers by keyword")
            print("  detail <name>    Server details with install command")
            print("  install <name>   Full install pipeline with HITL")
            print("  config <name>    Generate configs for langchain/claude/haive")
            print("  categories       List all 14 categories")
            print("  category <name>  Servers in a category")
            print("  quit             Exit")
            print()

        elif cmd == "search" and arg:
            results = query_engine.search(arg)
            _last_results = results
            if results:
                print(f"\n  {len(results)} results for '{arg}':\n")
                _print_results(results)
                print()
            else:
                print(f"  No servers found for '{arg}'\n")

        elif cmd == "categories":
            cats = query_engine.get_categories()
            print(f"\n  {len(cats)} categories:\n")
            for cat, count in cats.items():
                print(f"    {cat:<30} {count:>4} servers")
            print()

        elif cmd == "category" and arg:
            results = query_engine.loader.search_servers_by_category(arg)
            if results:
                print(f"\n  {len(results)} servers in '{arg}':\n")
                for s in results[:25]:
                    print(f"    - {s.get('name', '?')}")
                if len(results) > 25:
                    print(f"    ... and {len(results) - 25} more")
                print()
            else:
                print(f"  No servers in category '{arg}'\n")

        elif cmd == "detail" and arg:
            detail = query_engine.get_server_detail(arg)
            if detail:
                _print_detail(detail)
                print()
            else:
                print(f"  Server '{arg}' not found\n")

        elif cmd == "config" and arg:
            config = query_engine.loader.generate_server_config(arg)
            if config:
                print(f"\n  --- langchain-mcp-adapters ---")
                lc = {arg: {k: v for k, v in config.items() if v}}
                print(f"  {_json.dumps(lc, indent=2)}")
                print(f"\n  --- Claude Desktop (mcp.json) ---")
                claude = {"mcpServers": {arg: {"command": config["command"], "args": config.get("args", [])}}}
                if config.get("env"):
                    claude["mcpServers"][arg]["env"] = config["env"]
                print(f"  {_json.dumps(claude, indent=2)}")
                print()
            else:
                print(f"  Could not generate config for '{arg}'\n")

        elif cmd == "install" and arg:
            try:
                from haive.mcp.installer_service import MCPInstallerService

                async def _do_install():
                    svc = MCPInstallerService(require_approval=True)
                    plan = await svc.plan_install(arg)
                    if plan is None:
                        print(f"  Could not plan install for '{arg}'\n")
                        return
                    print(f"\n  Install plan:")
                    print(f"    Server:     {plan.server_name}")
                    print(f"    Command:    {plan.install_command}")
                    print(f"    Method:     {plan.method.value} ({plan.confidence:.0%} confidence)")
                    if plan.repository_url:
                        print(f"    Repository: {plan.repository_url}")
                    print()
                    approved = await svc.approve(plan)
                    if not approved:
                        print("  Rejected.\n")
                        return
                    print(f"  Connecting...")
                    result = await svc.install(plan)
                    if result.success:
                        print(f"  {result.message}")
                        if result.tools_discovered:
                            print(f"  Tools: {', '.join(result.tools_discovered[:10])}")
                    else:
                        print(f"  Failed: {result.message}")
                    print()

                asyncio.run(_do_install())
            except Exception as e:
                print(f"  Install error: {e}\n")

        else:
            # Default: treat input as search query
            results = query_engine.search(user_input)
            _last_results = results
            if results:
                print(f"\n  {len(results)} results:\n")
                _print_results(results, limit=10)
                print()
            else:
                print(f"  No results. Try: search <keyword>\n")
