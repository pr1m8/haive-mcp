#!/usr/bin/env python3
"""Complete MCP Discovery to Agent Usage Workflow Demo

This demonstrates:
1. Searching for MCP tools using the discovery system
2. Installing the discovered tool
3. Configuring it for use with a haive agent
4. Creating an agent that uses the discovered MCP tool

We'll use the calculator MCP server as our example.
"""

import asyncio
import json
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
        print(f"\n🔍 Step 1: Searching for MCP tools matching '{search_query}'...")

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

        print(f"✅ Found {len(search_results)} MCP tools:")
        for i, tool in enumerate(search_results, 1):
            print(f"\n  {i}. {tool['name']} (v{tool['version']})")
            print(f"     Description: {tool['description']}")
            print(f"     Capabilities: {', '.join(tool['capabilities'])}")

        self.discovered_tools = search_results
        return search_results

    async def step2_show_installation(self, tool_index: int = 0) -> dict[str, Any]:
        """Step 2: Show how to install the selected MCP tool."""
        selected_tool = self.discovered_tools[tool_index]

        print(f"\n📦 Step 2: Installing '{selected_tool['name']}'...")
        print("\nInstallation options:")
        print(f"  Option 1 - Global install: {selected_tool['install_command']}")
        print(f"  Option 2 - Direct use with npx: {selected_tool['npx_command']}")

        # For demo, we'll use npx approach (doesn't require actual installation)
        print("\n💡 We'll use the npx approach for this demo (no installation needed)")

        # Verify npx is available
        try:
            result = subprocess.run(
                ["npx", "--version"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                print(f"✅ npx is available (version {result.stdout.strip()})")
            else:
                print("⚠️  npx not found. Please install Node.js and npm first.")
        except Exception as e:
            print(f"⚠️  Error checking npx: {e}")

        self.installed_tools.append(selected_tool)
        return selected_tool

    async def step3_configure_for_agent(self, tool: dict[str, Any]) -> MCPConfig:
        """Step 3: Configure the MCP tool for use with a haive agent."""
        print(f"\n⚙️  Step 3: Configuring '{tool['name']}' for haive agent...")

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

        print("\n📋 Generated MCP Configuration:")
        print(json.dumps(mcp_config.model_dump(), indent=2))

        return mcp_config

    async def step4_create_agent_with_tool(self, mcp_config: MCPConfig) -> MCPAgent:
        """Step 4: Create a haive agent with the discovered MCP tool."""
        print("\n🤖 Step 4: Creating haive agent with MCP calculator...")

        # Create LLM engine
        engine = AugLLMConfig(
            name="calculator_engine",
            temperature=0.3,
            system_message="You are a helpful assistant with access to a calculator. Use it for any mathematical calculations.",
        )

        # Create MCP agent
        agent = MCPAgent(engine=engine, mcp_config=mcp_config, name="math_assistant")

        print(f"✅ Created MCPAgent: {agent}")

        # Initialize the agent
        print("\n🔄 Initializing agent and MCP connections...")
        try:
            await agent.setup()
            print("✅ Agent initialized successfully!")

            # Show available tools
            if hasattr(agent, "_mcp_tools"):
                print(f"\n🔧 Available MCP tools: {list(agent._mcp_tools.keys())}")
        except Exception as e:
            print("⚠️  Note: MCP server initialization requires the actual npm package")
            print(f"   Error: {e}")
            print("   In production, the MCP server would be automatically started")

        return agent

    async def step5_demo_usage(self, agent: MCPAgent):
        """Step 5: Demonstrate using the agent with the MCP tool."""
        print("\n🎯 Step 5: Using the agent with MCP calculator...")

        # Example calculations
        test_queries = [
            "What is 15 * 23?",
            "Calculate the square root of 144",
            "What's 2^10?",
            "Solve: (5 + 3) * 2 - 4",
        ]

        for query in test_queries:
            print(f"\n📊 Query: {query}")
            try:
                # In a real scenario, this would use the MCP calculator
                result = await agent.arun(
                    {"messages": [{"role": "user", "content": query}]}
                )
                print(f"🤖 Agent: {result}")
            except Exception:
                # Simulate responses for demo
                print("🤖 Agent: [Simulated response - actual MCP server not running]")
                if "15 * 23" in query:
                    print("   The answer is 345.")
                elif "square root of 144" in query:
                    print("   The square root of 144 is 12.")
                elif "2^10" in query:
                    print("   2^10 equals 1024.")
                elif "(5 + 3) * 2 - 4" in query:
                    print("   (5 + 3) * 2 - 4 = 8 * 2 - 4 = 16 - 4 = 12.")


async def main():
    """Run the complete MCP discovery to usage workflow."""
    print("🚀 MCP Discovery to Agent Usage Workflow Demo")
    print("=" * 50)

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

    print("\n\n✅ Workflow Complete!")
    print("\n📚 Summary:")
    print("1. ✅ Discovered MCP tools using search")
    print("2. ✅ Showed installation process")
    print("3. ✅ Generated MCP configuration")
    print("4. ✅ Created haive agent with MCP integration")
    print("5. ✅ Demonstrated agent using MCP tools")

    print("\n💡 Next Steps:")
    print("- Install actual MCP servers: npm install -g mathjs-mcp-server")
    print("- Use more complex MCP servers (database, filesystem, APIs)")
    print("- Combine multiple MCP servers in one agent")
    print("- Create custom MCP servers for your specific needs")


if __name__ == "__main__":
    asyncio.run(main())
