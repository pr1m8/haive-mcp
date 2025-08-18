"""Haive MCP - Dynamic Model Context Protocol Integration.

This package provides dynamic MCP (Model Context Protocol) integration for Haive agents,
enabling them to discover and use external tools and resources at runtime.

Key Components:
    - MCPManager: Central manager for MCP server lifecycle and tool management
    - MCPAgent: Production-ready agent with static MCP configuration
    - IntelligentMCPAgent: AI-powered agent with automatic server discovery
    - TransferableMCPAgent: Agent that can share tools with other agents

Example:
    Basic MCP agent usage:

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

    Dynamic discovery with IntelligentMCPAgent:

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
"""

# Agent implementations
from haive.mcp.agents import (
    IntelligentMCPAgent,
    MCPAgent,
    TransferableMCPAgent,
)

# Core components
from haive.mcp.config import (
    MCPConfig,
    MCPServerConfig,
    MCPTransport,
)

# Discovery components
from haive.mcp.discovery import (
    MCPServerDiscovery,
)

# Documentation loader
from haive.mcp.documentation import (
    MCPDocumentationLoader,
)
from haive.mcp.manager import (
    MCPHealthStatus,
    MCPManager,
    MCPRegistrationResult,
)

# Mixins for adding MCP to existing agents
from haive.mcp.mixins import (
    MCPDiscoveryMixin,
    MCPMixin,
)

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
    "MCPDiscoveryMixin",
    # Discovery
    "MCPServerDiscovery",
    # Documentation
    "MCPDocumentationLoader",
]

# Version info
__version__ = "0.1.0"
