"""MCP-enabled agent implementations.

This module provides pre-built agent classes that integrate Model Context Protocol
(MCP) capabilities with the Haive agent framework. These agents can connect to
MCP servers to access tools, resources, and prompts.

The module includes several specialized agent types:
- MCPAgent: Basic agent with MCP support
- TransferableMCPAgent: Agent with tool/resource transfer capabilities
- MCPDocumentationAgent: Agent specialized for MCP documentation processing

Classes:
    MCPAgent: Core MCP-enabled agent
    TransferableMCPAgent: Agent with transfer capabilities
    MCPDocumentationAgent: Documentation processing agent (when available)

Example:
    Creating and using an MCP agent::

        from haive.mcp.agents import MCPAgent
        from haive.mcp.config import MCPConfig, MCPServerConfig
        from haive.core.engine import AugLLMConfig

        # Configure MCP servers
        mcp_config = MCPConfig(
            servers={
                "filesystem": MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem"]
                ),
                "github": MCPServerConfig(
                    name="github", 
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-github"],
                    env={"GITHUB_TOKEN": "your-token"}
                )
            }
        )

        # Create agent
        agent = MCPAgent(
            engine=AugLLMConfig(name="mcp-engine"),
            mcp_config=mcp_config,
            name="multi-server-agent"
        )

        # Initialize and use
        await agent.setup()
        result = await agent.arun({
            "messages": [{"role": "user", "content": "List files and check GitHub"}]
        })

Advanced Usage:
    Using transferable agents for collaboration::

        from haive.mcp.agents import TransferableMCPAgent

        # Create collaborative agents
        agent1 = TransferableMCPAgent(engine=engine, mcp_config=config1)
        agent2 = TransferableMCPAgent(engine=engine, mcp_config=config2)

        # Share tools between agents
        await agent1.setup()
        await agent2.setup()
        
        # Transfer specific tools
        await agent1.transfer_tools_to_agent(
            agent2, 
            tool_names=["read_file", "write_file"]
        )
        
        # Or transfer all tools
        await agent1.transfer_all_tools_to_agent(agent2)

Agent Comparison:
    - **MCPAgent**: Standard MCP integration, suitable for most use cases
    - **TransferableMCPAgent**: When you need dynamic tool sharing between agents
    - **MCPDocumentationAgent**: For processing MCP server documentation

See Also:
    haive.mcp.mixins.mcp_mixin: MCPMixin for custom agents
    haive.mcp.config: MCP configuration options
    haive.agents.base: Base agent classes
"""

# from haive.mcp.agents.documentation_agent import MCPDocumentationAgent
from haive.mcp.agents.mcp_agent import MCPAgent
from haive.mcp.agents.transferable_mcp_agent import TransferableMCPAgent

__all__ = ["MCPAgent", "TransferableMCPAgent"]  # "MCPDocumentationAgent"