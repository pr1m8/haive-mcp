"""MCP Mixins for extending agent capabilities.

This module provides mixins that add Model Context Protocol (MCP) support
to existing Haive agents. The mixins handle MCP client initialization,
tool registration, and server lifecycle management.

The primary mixin is MCPMixin, which can be combined with any BaseAgent
subclass to add MCP capabilities without modifying the base agent code.

Classes:
    MCPMixin: Core mixin adding MCP support to agents

Example:
    Creating a custom agent with MCP support::

        from haive.agents.base import BaseAgent
        from haive.mcp.mixins import MCPMixin
        from haive.mcp.config import MCPConfig

        class MyCustomMCPAgent(MCPMixin, BaseAgent):
            def __init__(self, engine, mcp_config: MCPConfig, **kwargs):
                super().__init__(engine=engine, mcp_config=mcp_config, **kwargs)

        # Use the agent
        agent = MyCustomMCPAgent(
            engine=engine,
            mcp_config=MCPConfig(
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
        await agent.setup()
        result = await agent.arun({
            "messages": [{"role": "user", "content": "List files"}]
        })

Advanced Usage:
    Mixing MCP with other capabilities::

        from haive.agents.mixins import MemoryMixin, ToolsMixin
        from haive.mcp.mixins import MCPMixin

        class AdvancedAgent(MCPMixin, MemoryMixin, ToolsMixin, BaseAgent):
            '''Agent with MCP, memory, and custom tools.'''
            pass

        # The MCP tools will be added to the agent's tool registry
        # alongside any custom tools defined by ToolsMixin

See Also:
    haive.mcp.agents.mcp_agent: Pre-built agent with MCP support
    haive.mcp.config: Configuration models for MCP
    haive.mcp.manager: Core MCP management functionality
"""

from haive.mcp.mixins.mcp_mixin import MCPMixin

__all__ = ["MCPMixin"]