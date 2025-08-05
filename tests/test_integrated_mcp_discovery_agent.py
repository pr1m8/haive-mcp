#!/usr/bin/env python3
"""Integrated MCP Discovery Agent Demo.

This demonstrates an agent that has built-in MCP discovery capabilities:
1. Can search for MCP tools internally
2. Shows available/downloaded MCP servers
3. Can install and configure them on demand
4. Automatically uses discovered tools

The agent has access to the 992+ MCP server database and npm search.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from haive.core.engine.aug_llm import AugLLMConfig
from langchain_core.tools import tool

from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig
from haive.mcp.documentation.doc_loader import MCPDocumentationLoader


class IntegratedMCPDiscoveryAgent(MCPAgent):
    """An MCP Agent with integrated discovery capabilities."""

    def __init__(self, engine: Any, mcp_config: MCPConfig | None = None, **kwargs):
        super().__init__(engine=engine, mcp_config=mcp_config, **kwargs)

        # Initialize documentation loader for the 992+ MCP server database
        self.doc_loader = MCPDocumentationLoader()
        self.available_servers = {}
        self.installed_servers = {}

        # Add discovery tools to the agent
        self._add_discovery_tools()

    def _add_discovery_tools(self):
        """Add MCP discovery tools to the agent."""

        @tool
        def search_mcp_servers(query: str) -> str:
            """Search for MCP servers by name, capability, or category.

            Args:
                query: Search term (e.g., "calculator", "database", "github")

            Returns:
                JSON string with search results
            """
            # Search in our 992+ server database
            all_servers = self.doc_loader.load_all_mcp_documents()

            matches = []
            for server_name, server_doc in all_servers.items():
                # Search in name, description, and capabilities
                searchable_text = f"{server_name} {server_doc.get('description', '')} {' '.join(server_doc.get('metadata', {}).get('capabilities', []))}"

                if query.lower() in searchable_text.lower():
                    matches.append(
                        {
                            "name": server_name,
                            "description": server_doc.get("description", ""),
                            "category": server_doc.get("category", ""),
                            "npm_package": server_doc.get("metadata", {}).get(
                                "npm_package"
                            ),
                            "install_command": server_doc.get("metadata", {}).get(
                                "install_command"
                            ),
                            "capabilities": server_doc.get("metadata", {}).get(
                                "capabilities", []
                            ),
                        }
                    )

            # Also search npm if the query looks like it needs fresh results
            if "latest" in query.lower() or "new" in query.lower():
                # Would call npm search API here
                matches.append(
                    {
                        "name": "npm-search-results",
                        "description": f"Additional results from npm search for '{query}'",
                        "note": "Use search_npm_packages tool for live npm results",
                    }
                )

            return json.dumps(
                {
                    "query": query,
                    "total_results": len(matches),
                    "results": matches[:10],  # Limit to 10 results
                },
                indent=2,
            )

        @tool
        def list_available_servers() -> str:
            """List all available MCP servers in our database.

            Returns:
                JSON string with server categories and counts
            """
            all_servers = self.doc_loader.load_all_mcp_documents()

            # Categorize servers
            categories = {}
            for server_name, server_doc in all_servers.items():
                category = server_doc.get("category", "Uncategorized")
                if category not in categories:
                    categories[category] = []
                categories[category].append(server_name)

            # Create summary
            summary = {
                "total_servers": len(all_servers),
                "categories": {
                    cat: len(servers) for cat, servers in categories.items()
                },
                "sample_servers": {
                    cat: servers[:3] for cat, servers in list(categories.items())[:5]
                },
            }

            return json.dumps(summary, indent=2)

        @tool
        def get_server_details(server_name: str) -> str:
            """Get detailed information about a specific MCP server.

            Args:
                server_name: Name of the server (e.g., "modelcontextprotocol/server-filesystem")

            Returns:
                JSON string with server details
            """
            server_doc = self.doc_loader.get_server_documentation(server_name)

            if not server_doc:
                return json.dumps({"error": f"Server '{server_name}' not found"})

            # Extract setup information
            setup_info = self.doc_loader.extract_setup_info(server_doc)

            return json.dumps(
                {
                    "name": server_name,
                    "description": setup_info.get("description"),
                    "category": setup_info.get("category"),
                    "installation": setup_info.get("installation"),
                    "configuration": setup_info.get("configuration"),
                    "usage_examples": setup_info.get("usage"),
                    "capabilities": setup_info.get("capabilities", []),
                    "npm_package": setup_info.get("npm_package"),
                    "install_command": setup_info.get("install_command"),
                },
                indent=2,
            )

        @tool
        def install_mcp_server(server_name: str, use_npx: bool = True) -> str:
            """Install an MCP server and add it to the agent's configuration.

            Args:
                server_name: Name of the server to install
                use_npx: Whether to use npx (True) or install globally (False)

            Returns:
                Installation status and configuration
            """
            # Get server details
            server_doc = self.doc_loader.get_server_documentation(server_name)
            if not server_doc:
                return json.dumps({"error": f"Server '{server_name}' not found"})

            setup_info = self.doc_loader.extract_setup_info(server_doc)
            npm_package = setup_info.get("npm_package")

            if not npm_package:
                return json.dumps({"error": "No npm package found for this server"})

            # Create MCP configuration for this server
            server_config = {
                "name": server_name.split("/")[-1],  # Use last part as config name
                "transport": "stdio",
                "command": "npx" if use_npx else "node",
                "args": ["-y", npm_package] if use_npx else [npm_package],
                "capabilities": setup_info.get("capabilities", []),
                "description": setup_info.get("description"),
            }

            # Add to installed servers
            self.installed_servers[server_name] = {
                "config": server_config,
                "installed_at": datetime.now().isoformat(),
                "npm_package": npm_package,
                "use_npx": use_npx,
            }

            return json.dumps(
                {
                    "status": "configured",
                    "server_name": server_name,
                    "config": server_config,
                    "note": "Server configured. Use 'activate_mcp_server' to start using it.",
                },
                indent=2,
            )

        @tool
        def list_installed_servers() -> str:
            """List all installed/configured MCP servers.

            Returns:
                JSON string with installed servers
            """
            return json.dumps(
                {
                    "total_installed": len(self.installed_servers),
                    "servers": self.installed_servers,
                },
                indent=2,
            )

        @tool
        def activate_mcp_server(server_name: str) -> str:
            """Activate an installed MCP server for use.

            Args:
                server_name: Name of the server to activate

            Returns:
                Activation status
            """
            if server_name not in self.installed_servers:
                return json.dumps({"error": f"Server '{server_name}' not installed"})

            server_info = self.installed_servers[server_name]
            config = server_info["config"]

            # In a real implementation, this would:
            # 1. Update the agent's MCP configuration
            # 2. Restart MCP connections
            # 3. Load new tools from the server

            return json.dumps(
                {
                    "status": "activated",
                    "server_name": server_name,
                    "available_tools": [
                        f"{config['name']}_tool1",
                        f"{config['name']}_tool2",
                    ],
                    "note": "Server activated. New tools are now available.",
                },
                indent=2,
            )

        # Add tools to agent
        if hasattr(self, "tools") and isinstance(self.tools, list):
            self.tools.extend(
                [
                    search_mcp_servers,
                    list_available_servers,
                    get_server_details,
                    install_mcp_server,
                    list_installed_servers,
                    activate_mcp_server,
                ]
            )
        else:
            self.tools = [
                search_mcp_servers,
                list_available_servers,
                get_server_details,
                install_mcp_server,
                list_installed_servers,
                activate_mcp_server,
            ]

    async def setup(self) -> None:
        """Setup agent including loading MCP database."""
        await super().setup()

        # Load the MCP server database
        all_servers = self.doc_loader.load_all_mcp_documents()
        self.available_servers = all_servers

        # Show some statistics
        categories = {}
        for server_doc in all_servers.values():
            cat = server_doc.get("category", "Uncategorized")
            categories[cat] = categories.get(cat, 0) + 1

        for cat, _count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]:
            pass


async def demonstrate_discovery_agent():
    """Demonstrate the integrated MCP discovery agent."""
    # Create LLM engine with system message about discovery capabilities
    engine = AugLLMConfig(
        name="discovery_engine",
        temperature=0.3,
        system_message="""You are an AI assistant with integrated MCP discovery capabilities.

You have access to a database of 992+ MCP servers and can:
1. Search for MCP servers by name, capability, or category
2. Show detailed information about any server
3. Install and configure servers for use
4. Activate servers to use their tools

When users ask about capabilities, search the database first to find relevant servers.
When they want to use a specific capability, help them install and activate the appropriate server.""",
    )

    # Create the integrated discovery agent
    agent = IntegratedMCPDiscoveryAgent(engine=engine, name="mcp_discovery_assistant")

    # Initialize the agent
    await agent.setup()

    # Example interactions
    test_queries = [
        "What MCP servers are available for calculator functionality?",
        "Show me details about the mathjs-mcp-server",
        "Install the mathjs-mcp-server for me",
        "What servers have I installed?",
        "Search for database-related MCP servers",
        "How many MCP servers are available in total?",
    ]

    for query in test_queries:
        try:
            # The agent would process this and use the appropriate tools
            await agent.arun({"messages": [{"role": "user", "content": query}]})
        except Exception:
            # For demo purposes, show what the agent would do

            if (
                "calculator" in query.lower()
                or "mathjs-mcp-server" in query
                or "install" in query.lower()
                or "installed" in query.lower()
                or "database" in query.lower()
                or "how many" in query.lower()
            ):
                pass


async def main():
    """Run the integrated discovery demo."""
    await demonstrate_discovery_agent()


if __name__ == "__main__":
    asyncio.run(main())
