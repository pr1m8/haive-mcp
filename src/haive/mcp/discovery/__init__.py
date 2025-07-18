"""MCP server discovery and dynamic loading.

This module provides functionality for discovering, analyzing, and dynamically
loading MCP servers. It can find servers installed locally, analyze their
capabilities from documentation, and create configurations automatically.

The discovery system supports multiple sources:
- Local npm installations
- GitHub repositories
- Documentation files
- Registry lookups

Classes:
    MCPServerDiscovery: Main discovery engine
    MCPServerAnalyzer: Analyzes server capabilities from documentation

Example:
    Discovering and using MCP servers::

        from haive.mcp.discovery import MCPServerDiscovery
        from haive.mcp.agents import MCPAgent

        # Discover available servers
        discovery = MCPServerDiscovery()
        servers = await discovery.discover_all()

        print(f"Found {len(servers)} MCP servers:")
        for server in servers:
            print(f"  - {server.name}: {server.description}")
            print(f"    Capabilities: {', '.join(server.capabilities)}")

        # Find servers by capability
        file_servers = discovery.get_servers_by_capability("file_operations")
        print(f"\\nFile operation servers: {[s.name for s in file_servers]}")

        # Create configuration from discovered servers
        mcp_config = discovery.create_mcp_config(
            include_categories=["filesystem", "database"],
            required_capabilities=["read", "write"]
        )

        # Use with an agent
        agent = MCPAgent(engine=engine, mcp_config=mcp_config)

Advanced Usage:
    Analyzing server documentation::

        from haive.mcp.discovery import MCPServerAnalyzer

        analyzer = MCPServerAnalyzer()

        # Analyze a server from its documentation
        analysis = await analyzer.analyze_server(
            "modelcontextprotocol/server-filesystem"
        )

        print(f"Server: {analysis.name}")
        print(f"Tools: {analysis.tools}")
        print(f"Resources: {analysis.resources}")
        print(f"Setup: {analysis.setup_instructions}")

        # Batch analyze multiple servers
        servers_to_analyze = [
            "modelcontextprotocol/server-github",
            "modelcontextprotocol/server-postgres"
        ]

        results = await analyzer.batch_analyze(servers_to_analyze)
        for result in results:
            print(f"\\n{result.name}:")
            print(f"  Category: {result.category}")
            print(f"  Dependencies: {result.dependencies}")

Discovery Sources:
    - **Local**: Scans npm global and local installations
    - **Registry**: Queries MCP server registries
    - **Documentation**: Extracts from markdown files
    - **GitHub**: Searches GitHub for MCP servers

See Also:
    haive.mcp.config: Configuration models for discovered servers
    haive.mcp.manager: Managing discovered server connections
    haive.mcp.documentation: Documentation processing utilities
"""

from haive.mcp.discovery.analyzer import MCPServerAnalyzer
from haive.mcp.discovery.server_discovery import MCPServerDiscovery


__all__ = ["MCPServerAnalyzer", "MCPServerDiscovery"]
