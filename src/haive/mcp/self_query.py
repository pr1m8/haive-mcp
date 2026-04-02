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


def run_interactive():
    """Run the interactive self-query interface."""
    query_engine = MCPSelfQuery()

    print(f"\n  MCP Server Discovery")
    print(f"  {query_engine.server_count} servers available\n")
    print("  Commands:")
    print("    search <query>    - Search servers by keyword")
    print("    categories        - List all categories")
    print("    category <name>   - List servers in a category")
    print("    detail <name>     - Show server details")
    print("    quit              - Exit\n")

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
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("quit", "exit", "q"):
            break

        elif cmd == "search" and arg:
            results = query_engine.search(arg)
            if results:
                print(f"\n  Found {len(results)} servers:\n")
                for i, s in enumerate(results, 1):
                    desc = (s.get("description") or "")[:70]
                    print(f"  {i:2}. {s.get('name', '?')}")
                    if desc:
                        print(f"      {desc}")
                print()
            else:
                print(f"  No servers found for '{arg}'\n")

        elif cmd == "categories":
            cats = query_engine.get_categories()
            print(f"\n  {len(cats)} categories:\n")
            for cat, count in cats.items():
                print(f"    {cat:<30} ({count} servers)")
            print()

        elif cmd == "category" and arg:
            results = query_engine.loader.search_servers_by_category(arg)
            if results:
                print(f"\n  {len(results)} servers in '{arg}':\n")
                for s in results[:20]:
                    print(f"    - {s.get('name', '?')}")
                if len(results) > 20:
                    print(f"    ... and {len(results) - 20} more")
                print()
            else:
                print(f"  No servers in category '{arg}'\n")

        elif cmd == "detail" and arg:
            detail = query_engine.get_server_detail(arg)
            if detail:
                print(f"\n  {detail['name']}")
                print(f"  {'=' * len(detail['name'])}")
                if detail["description"]:
                    print(f"  {detail['description']}")
                if detail["category"]:
                    print(f"  Category: {detail['category']}")
                if detail["repository_url"]:
                    print(f"  Repo: {detail['repository_url']}")
                if detail["install_command"]:
                    print(f"  Install: {detail['install_command']}")
                setup = detail.get("setup_info", {})
                if setup.get("installation"):
                    print(f"  Steps:")
                    for step in setup["installation"]:
                        print(f"    $ {step}")
                if setup.get("capabilities"):
                    print(f"  Capabilities: {', '.join(setup['capabilities'])}")
                print()
            else:
                print(f"  Server '{arg}' not found\n")

        else:
            # Treat as search by default
            if user_input:
                results = query_engine.search(user_input)
                if results:
                    print(f"\n  Found {len(results)} servers:\n")
                    for i, s in enumerate(results[:10], 1):
                        desc = (s.get("description") or "")[:70]
                        print(f"  {i:2}. {s.get('name', '?')}")
                        if desc:
                            print(f"      {desc}")
                    print()
                else:
                    print(f"  No results. Try: search <keyword>\n")
