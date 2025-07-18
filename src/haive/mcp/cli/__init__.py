"""Command-line interface tools for MCP management.

This module provides CLI utilities for managing MCP servers, including
installation, configuration, discovery, and monitoring. The CLI tools
make it easy to work with MCP servers from the command line.

The main CLI tool is mcp_manager.py, which provides commands for:
- Installing MCP servers from npm
- Discovering available servers
- Managing server configurations
- Testing server connections
- Monitoring server health

Functions:
    main: Entry point for the MCP CLI
    install_server: Install an MCP server from npm
    list_servers: List installed MCP servers
    test_server: Test a server connection
    discover_servers: Discover available servers

Example:
    Using the MCP CLI from Python::

        from haive.mcp.cli import mcp_manager

        # Install a server
        await mcp_manager.install_server("@modelcontextprotocol/server-filesystem")

        # List installed servers
        servers = await mcp_manager.list_servers()
        for server in servers:
            print(f"- {server.name}: {server.status}")

        # Test a server
        result = await mcp_manager.test_server("filesystem")
        if result.success:
            print(f"Server is working! Tools: {result.tools}")

Command Line Usage:
    The CLI can be used directly from the command line::

        # Install a server
        poetry run python -m haive.mcp.cli install @modelcontextprotocol/server-filesystem

        # List servers
        poetry run python -m haive.mcp.cli list

        # Test a server
        poetry run python -m haive.mcp.cli test filesystem

        # Discover servers
        poetry run python -m haive.mcp.cli discover --category filesystem

CLI Commands:
    - **install**: Install MCP servers from npm
    - **list**: List installed servers and their status
    - **test**: Test server connections and functionality
    - **discover**: Find available servers by category
    - **config**: Manage server configurations
    - **logs**: View server logs and diagnostics

See Also:
    haive.mcp.manager: Core MCP management functionality
    haive.mcp.discovery: Server discovery system
    haive.mcp.config: Configuration management
"""

from haive.mcp.cli.mcp_manager import main


__all__ = ["main"]
