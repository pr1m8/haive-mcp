"""Haive MCP Package - Model Context Protocol integration for Haive agents.

This package provides comprehensive integration with the Model Context Protocol (MCP),
enabling Haive agents to connect to and use MCP servers that provide tools, resources,
and prompts. The package includes agents, mixins, discovery systems, and management
tools for working with MCP servers.

Key Features:
    - MCP-enabled agents with automatic server integration
    - Server discovery and analysis capabilities  
    - AI-enhanced server selection and recommendations
    - 992+ pre-documented MCP servers database
    - Multiple transport support (stdio, SSE, WebSocket)
    - Dynamic server addition and management
    - Tool transfer between agents
    - Graceful degradation and error handling

Core Components:
    - MCPAgent: Ready-to-use agent with MCP capabilities
    - MCPMixin: Add MCP functionality to any Haive agent
    - MCPManager: Dynamic server management and tool discovery
    - MCPServerDiscovery: Automatic server discovery system
    - MCPConfig: Type-safe configuration models

Usage Example:
    ```python
    from haive.mcp.agents import MCPAgent
    from haive.mcp.config import MCPConfig, MCPServerConfig
    from haive.core.engine.aug_llm import AugLLMConfig
    from haive.core.models.llm.base import OpenAILLMConfig

    # Configure engine
    engine = AugLLMConfig(
        llm_config=OpenAILLMConfig(model="gpt-4o-mini"),
        name="mcp_engine"
    )

    # Create MCP agent
    agent = MCPAgent(
        engine=engine,
        mcp_config=MCPConfig(
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
    )

    # Use the agent
    await agent.setup()
    result = await agent.arun("List the files in the current directory")
    ```

Package Structure:
    - agents/: MCP-enabled agent implementations
    - mixins/: MCP mixin for extending existing agents
    - discovery/: Server discovery and analysis tools
    - tools/: AI-enhanced MCP tools and utilities
    - config.py: Configuration models and validation
    - manager.py: Dynamic MCP server management

For detailed documentation, see the individual module documentation and the
README.md file in the package root.
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
