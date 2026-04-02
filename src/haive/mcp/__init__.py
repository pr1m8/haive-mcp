"""Haive MCP - Dynamic Model Context Protocol Integration.

This package provides dynamic MCP (Model Context Protocol) integration for Haive agents,
enabling them to discover and use external tools and resources at runtime.

Key Components
--------------

- **MCPManager**: Central manager for MCP server lifecycle and tool management
- **MCPAgent**: Production-ready agent with static MCP configuration  
- **IntelligentMCPAgent**: AI-powered agent with automatic server discovery
- **TransferableMCPAgent**: Agent that can share tools with other agents

Quick Start
-----------

Basic MCP Agent Usage
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from haive.mcp import MCPAgent, MCPConfig
    from haive.core.engine import AugLLMConfig

    # Create agent with MCP capabilities
    agent = MCPAgent(
        engine=AugLLMConfig(),
        mcp_config=MCPConfig(
            enabled=True,
            servers={
                "filesystem": {
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"]
                }
            }
        )
    )

    # Initialize and use
    await agent.setup()
    result = await agent.arun({"messages": [...]})

Dynamic Discovery with IntelligentMCPAgent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from haive.mcp import IntelligentMCPAgent

    # Create agent with auto-discovery
    agent = IntelligentMCPAgent(
        engine=AugLLMConfig(),
        auto_discover=True,
        require_approval=True
    )

    # Agent will automatically find and install needed MCP servers
    result = await agent.arun({
        "messages": [{"role": "user", "content": "Search web and save to database"}]
    })

Available Classes
-----------------

Configuration
~~~~~~~~~~~~~
- :class:`MCPConfig` - Main configuration for MCP integration
- :class:`MCPServerConfig` - Individual server configuration
- :class:`MCPTransport` - Transport protocol enumeration

Agents
~~~~~~
- :class:`MCPAgent` - Basic MCP-enabled agent
- :class:`IntelligentMCPAgent` - Agent with automatic discovery
- :class:`TransferableMCPAgent` - Agent with tool sharing capabilities

Management
~~~~~~~~~~
- :class:`MCPManager` - Server lifecycle management
- :class:`MCPHealthStatus` - Health monitoring
- :class:`MCPRegistrationResult` - Registration status

Utilities
~~~~~~~~~
- :class:`MCPMixin` - Add MCP capabilities to existing agents
- :class:`MCPServerDiscovery` - Discover available servers
- :class:`MCPDocumentationLoader` - Load server documentation
"""

# Agent implementations - handle missing dependencies gracefully
try:
    from haive.mcp.agents import (
        IntelligentMCPAgent,
        MCPAgent,
        TransferableMCPAgent,
    )
except ImportError as e:
    # Some agent implementations may depend on packages not available
    # Set to None to indicate they're not available
    IntelligentMCPAgent = None
    MCPAgent = None
    TransferableMCPAgent = None

# Core components
from haive.mcp.config import (
    MCPConfig,
    MCPServerConfig,
    MCPTransport,
)

# Discovery components - handle missing dependencies
try:
    from haive.mcp.discovery import (
        MCPServerDiscovery,
    )
except ImportError:
    MCPServerDiscovery = None

# Documentation loader - handle missing dependencies
try:
    from haive.mcp.documentation import (
        MCPDocumentationLoader,
    )
except ImportError:
    MCPDocumentationLoader = None

try:
    from haive.mcp.manager import (
        MCPHealthStatus,
        MCPManager,
        MCPRegistrationResult,
    )
except ImportError:
    MCPHealthStatus = None
    MCPManager = None
    MCPRegistrationResult = None

# Mixins for adding MCP to existing agents - handle missing dependencies
try:
    from haive.mcp.mixins import (
        MCPMixin,
    )
except ImportError:
    MCPMixin = None

# Plugin implementations - Phase 2
try:
    from haive.mcp.plugins import (
        MCPBrowserPlugin,
        get_plugin_registry,
        get_plugin_class,
    )
except ImportError:
    MCPBrowserPlugin = None
    get_plugin_registry = None
    get_plugin_class = None

__all__ = [
    # Configuration
    "MCPConfig",
    "MCPServerConfig",
    "MCPTransport",
    # Manager
    "MCPManager",
    "MCPRegistrationResult",
    "MCPHealthStatus",
    # Agents
    "MCPAgent",
    "IntelligentMCPAgent",
    "TransferableMCPAgent",
    # Mixins
    "MCPMixin",
    # Discovery
    "MCPServerDiscovery",
    # Documentation
    "MCPDocumentationLoader",
    # Plugins - Phase 2
    "MCPBrowserPlugin",
    "get_plugin_registry",
    "get_plugin_class",
]

# Version info
__version__ = "0.1.0"
