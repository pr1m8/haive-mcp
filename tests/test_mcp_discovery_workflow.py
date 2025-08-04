#!/usr/bin/env python3
"""Complete MCP Discovery to Agent Usage Workflow Demo.

This demonstrates:
1. Searching for MCP tools using the discovery system
2. Installing the discovered tool
3. Configuring it for use with a haive agent
4. Creating an agent that uses the discovered MCP tool

We'll use the calculator MCP server as our example.
"""

import asyncio
import subprocess
from typing import Any

from haive.core.engine.aug_llm import AugLLMConfig

from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig


class MCPDiscoveryWorkflow:
    """Demonstrates the complete MCP discovery to usage workflow."""

    def __init__(self):
        self.discovered_tools = []
        self.installed_tools = []

    async def step1_search_for_tools(self, search_query: str) -> list[dict[str, Any]]:
        """Step 1: Search for MCP tools using discovery system."""
        # In a real implementation, this would use the MCP discovery agent
        # For this demo, we'll simulate the search results we got from npm
        search_results = [
            {
                "name": "@wrtnlabs/calculator-mcp",
                "description": "Calculator MCP",
                "version": "0.2.1",
                "install_command": "npm install -g @wrtnlabs/calculator-mcp",
                "npx_command": "npx @wrtnlabs/calculator-mcp",
                "capabilities": ["basic_math", "scientific_calculations"],
            },
            {
                "name": "mathjs-mcp-server",
                "description": "An MCP server for parsing and calculating mathematical expressions using mathjs",
                "version": "1.0.4",
                "install_command": "npm install -g mathjs-mcp-server",
                "npx_command": "npx mathjs-mcp-server",
                "capabilities": [
                    "expression_parsing",
                    "advanced_math",
                    "unit_conversion",
                ],
            },
            {
                "name": "calculator-mcp-server",
                "description": "一个简单的计算器MCP服务器 (A simple calculator MCP server)",
                "version": "1.0.4",
                "install_command": "npm install -g calculator-mcp-server",
                "npx_command": "npx calculator-mcp-server",
                "capabilities": ["basic_arithmetic"],
            },
        ]

        for _i, _tool in enumerate(search_results, 1):
            pass

        self.discovered_tools = search_results
        return search_results

    async def step2_show_installation(self, tool_index: int = 0) -> dict[str, Any]:
        """Step 2: Show how to install the selected MCP tool."""
        selected_tool = self.discovered_tools[tool_index]

        # For demo, we'll use npx approach (doesn't require actual installation)

        # Verify npx is available
        try:
            result = subprocess.run(
                ["npx", "--version"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                pass
            else:
                pass
        except Exception:
            pass

        self.installed_tools.append(selected_tool)
        return selected_tool

    async def step3_configure_for_agent(self, tool: dict[str, Any]) -> MCPConfig:
        """Step 3: Configure the MCP tool for use with a haive agent."""
        # Create MCP configuration
        mcp_config = MCPConfig(
            enabled=True,
            servers={
                "calculator": MCPServerConfig(
                    name="calculator",
                    transport="stdio",
                    command="npx",
                    args=["-y", tool["name"]],  # Use the discovered tool name
                    capabilities=tool["capabilities"],
                    description=tool["description"],
                )
            },
        )

        return mcp_config

    async def step4_create_agent_with_tool(self, mcp_config: MCPConfig) -> MCPAgent:
        """Step 4: Create a haive agent with the discovered MCP tool."""
        # Create LLM engine
        engine = AugLLMConfig(
            name="calculator_engine",
            temperature=0.3,
            system_message="You are a helpful assistant with access to a calculator. Use it for any mathematical calculations.",
        )

        # Create MCP agent
        agent = MCPAgent(engine=engine, mcp_config=mcp_config, name="math_assistant")

        # Initialize the agent
        try:
            await agent.setup()

            # Show available tools
            if hasattr(agent, "_mcp_tools"):
                pass
        except Exception:
            pass

        return agent

    async def step5_demo_usage(self, agent: MCPAgent):
        """Step 5: Demonstrate using the agent with the MCP tool."""
        # Example calculations
        test_queries = [
            "What is 15 * 23?",
            "Calculate the square root of 144",
            "What's 2^10?",
            "Solve: (5 + 3) * 2 - 4",
        ]

        for query in test_queries:
            try:
                # In a real scenario, this would use the MCP calculator
                await agent.arun({"messages": [{"role": "user", "content": query}]})
            except Exception:
                # Simulate responses for demo
                if (
                    "15 * 23" in query
                    or "square root of 144" in query
                    or "2^10" in query
                    or "(5 + 3) * 2 - 4" in query
                ):
                    pass


async def main():
    """Run the complete MCP discovery to usage workflow."""
    workflow = MCPDiscoveryWorkflow()

    # Step 1: Search for tools
    await workflow.step1_search_for_tools("calculator")

    # Step 2: Show installation process
    selected_tool = await workflow.step2_show_installation(
        tool_index=1
    )  # Select mathjs-mcp-server

    # Step 3: Configure for agent
    mcp_config = await workflow.step3_configure_for_agent(selected_tool)

    # Step 4: Create agent with tool
    agent = await workflow.step4_create_agent_with_tool(mcp_config)

    # Step 5: Demo usage
    await workflow.step5_demo_usage(agent)


if __name__ == "__main__":
    asyncio.run(main())
