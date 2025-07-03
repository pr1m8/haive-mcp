"""Haive MCP - Model Context Protocol Integration for Haive.

The haive-mcp package provides comprehensive MCP support for the Haive framework,
enabling discovery, management, and integration of MCP servers with AI agents.

This package consists of several modules:

    manager: Core MCP manager for server lifecycle management
    discovery: Server discovery from npm, PyPI, GitHub, and local sources
    downloader: Server download and installation utilities
    servers: MCP server implementations using FastMCP
    agents: MCP-enabled agent implementations
    tools: Utility tools for MCP operations
    config: Configuration models and validation

Typical usage example:

    ```python
    from haive.mcp import MCPManager, MCPConfig, MCPServerConfig
    from haive.mcp.discovery import discover_servers
    
    # Discover available servers
    servers = await discover_servers()
    
    # Create manager with configuration
    config = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                name="filesystem",
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"]
            )
        }
    )
    
    manager = MCPManager(config)
    await manager.initialize()
    
    # Execute a tool
    result = await manager.execute_tool(
        server="filesystem",
        tool="read_file",
        params={"path": "file.txt"}
    )
    ```

Attributes:
    __version__: Package version string
    MCPConfig: Main configuration model
    MCPServerConfig: Server configuration model
    MCPManager: Server lifecycle manager
    MCPAgent: MCP-enabled agent
    TransferableMCPAgent: Agent with tool transfer capabilities
    MCPDocumentationAgent: Documentation processing agent
"""

__version__ = "0.1.0"

# Import core MCP components
try:
    from haive.mcp.config import MCPConfig, MCPServerConfig
    from haive.mcp.manager import MCPManager
    
    # Try to import agents if available
    try:
        from haive.mcp.agents.mcp_agent import MCPAgent
        from haive.mcp.mixins.mcp_mixin import MCPMixin
        AGENTS_AVAILABLE = True
    except ImportError:
        AGENTS_AVAILABLE = False

    # Try to import discovery if available
    try:
        from haive.mcp.discovery.analyzer import MCPServerAnalyzer
        from haive.mcp.discovery.server_discovery import MCPServerDiscovery
        DISCOVERY_AVAILABLE = True
    except ImportError:
        DISCOVERY_AVAILABLE = False

    MCP_AVAILABLE = True
except ImportError:
    # Graceful degradation if MCP components aren't fully implemented
    MCP_AVAILABLE = False
    AGENTS_AVAILABLE = False
    DISCOVERY_AVAILABLE = False

__all__ = [
    "__version__",
]

if MCP_AVAILABLE:
    __all__.extend([
        "MCPConfig",
        "MCPServerConfig", 
        "MCPManager",
    ])

if AGENTS_AVAILABLE:
    __all__.extend([
        "MCPAgent",
        "MCPMixin",
    ])

if DISCOVERY_AVAILABLE:
    __all__.extend([
        "MCPServerAnalyzer",
        "MCPServerDiscovery",
    ])
