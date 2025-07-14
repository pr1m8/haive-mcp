#!/usr/bin/env python3
"""
Haive Agent + MCP Tool Integration

Demonstrates the complete workflow:
1. Discover an MCP server/tool
2. Install and configure it
3. Create a haive agent that uses the MCP tool
4. Show the agent executing with the discovered tool
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from haive.agents.simple import SimpleAgent
from haive.agents.react import ReactAgent
from haive.core.engine.aug_llm import AugLLMConfig
from langchain_core.tools import Tool

# Import our MCP components
from integrated_mcp_system import IntegratedMCPSystem
from fastmcp_runner import MCPProcessManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HaiveMCPIntegration:
    """Integrates discovered MCP tools with Haive agents"""
    
    def __init__(self):
        self.mcp_system = IntegratedMCPSystem()
        self.process_manager = MCPProcessManager()
        self.mcp_tools = {}
        
    async def discover_tool(self, query: str) -> Optional[Dict[str, Any]]:
        """Discover an MCP tool/server by query"""
        
        logger.info(f"🔍 Searching for: {query}")
        
        # Search for tools
        results = await self.mcp_system.search_servers(query, method="auto")
        
        if not results['documents']:
            logger.warning("No tools found matching query")
            return None
            
        # Return the first match
        doc = results['documents'][0]
        metadata = doc.metadata
        
        logger.info(f"✅ Found: {metadata.get('server_name', 'Unknown')}")
        logger.info(f"   Category: {metadata.get('category', 'unknown')}")
        logger.info(f"   Stars: {metadata.get('stars', 0)} ⭐")
        logger.info(f"   Tools: {metadata.get('tools_count', 0)}")
        
        return metadata
    
    async def install_and_configure(self, server_name: str) -> bool:
        """Install and configure an MCP server"""
        
        logger.info(f"📦 Installing {server_name}...")
        
        # Install the server
        installation = await self.mcp_system.install_and_configure(server_name)
        
        if installation.status == 'installed':
            logger.info(f"✅ {installation.message}")
            return True
        else:
            logger.error(f"❌ {installation.message}")
            return False
    
    async def start_mcp_server(self, server_name: str) -> bool:
        """Start an MCP server"""
        
        logger.info(f"🚀 Starting {server_name}...")
        
        result = await self.process_manager.start_server(server_name)
        
        if result['success']:
            logger.info(f"✅ {result['message']} (PID: {result.get('pid', 'N/A')})")
            return True
        else:
            logger.error(f"❌ {result['error']}")
            return False
    
    def create_mcp_tool(self, server_name: str, tool_info: Dict[str, Any]) -> Tool:
        """Create a LangChain tool from MCP server info"""
        
        # This is a simplified example - in reality, you'd need to:
        # 1. Connect to the running MCP server
        # 2. Query its available tools
        # 3. Create proper tool wrappers
        
        def mcp_tool_function(query: str) -> str:
            """Execute MCP tool - placeholder implementation"""
            # In a real implementation, this would:
            # 1. Send the query to the MCP server
            # 2. Receive and process the response
            # 3. Return the result
            
            return f"[MCP Tool '{server_name}' executed with query: {query}]"
        
        tool = Tool(
            name=server_name.replace('-', '_'),
            description=f"MCP tool: {tool_info.get('description', 'No description')}",
            func=mcp_tool_function
        )
        
        return tool
    
    async def create_agent_with_mcp_tool(
        self, 
        agent_type: str = "simple",
        tool_query: str = "calculator"
    ) -> Optional[Any]:
        """Create a haive agent with a discovered MCP tool"""
        
        # 1. Discover a tool
        tool_info = await self.discover_tool(tool_query)
        if not tool_info:
            return None
            
        server_name = tool_info.get('server_name', 'unknown')
        
        # 2. Install and configure (skip if already installed)
        servers = self.mcp_system.get_fastmcp_servers()
        if server_name not in servers:
            success = await self.install_and_configure(server_name)
            if not success:
                return None
        
        # 3. Start the MCP server
        success = await self.start_mcp_server(server_name)
        if not success:
            return None
        
        # 4. Create tool wrapper
        mcp_tool = self.create_mcp_tool(server_name, tool_info)
        
        # 5. Create haive agent with the tool
        config = AugLLMConfig(
            temperature=0.7,
            system_message=f"You are an assistant with access to the {server_name} tool."
        )
        
        if agent_type == "simple":
            agent = SimpleAgent(
                name=f"agent_with_{server_name}",
                engine=config,
                tools=[mcp_tool]
            )
        elif agent_type == "react":
            agent = ReactAgent(
                name=f"react_agent_with_{server_name}",
                engine=config,
                tools=[mcp_tool]
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        logger.info(f"✅ Created {agent_type} agent with {server_name} tool")
        
        return agent

async def demo_discovery_to_agent():
    """Demonstrate the complete workflow"""
    
    print("\n" + "="*60)
    print("🚀 Haive Agent + MCP Tool Integration Demo")
    print("="*60 + "\n")
    
    integration = HaiveMCPIntegration()
    
    # Example 1: Simple agent with calculator tool
    print("📋 Example 1: Simple Agent with Calculator Tool")
    print("-" * 40)
    
    agent = await integration.create_agent_with_mcp_tool(
        agent_type="simple",
        tool_query="calculator tool"
    )
    
    if agent:
        # Test the agent
        result = await agent.arun("Calculate 25 * 4")
        print(f"\n🤖 Agent response: {result}")
    
    print("\n" + "="*60 + "\n")
    
    # Example 2: React agent with database tool
    print("📋 Example 2: React Agent with Database Tool")
    print("-" * 40)
    
    react_agent = await integration.create_agent_with_mcp_tool(
        agent_type="react",
        tool_query="database query tool"
    )
    
    if react_agent:
        # Test the agent
        result = await react_agent.arun("Query the database for user information")
        print(f"\n🤖 Agent response: {result}")
    
    # Stop all MCP servers when done
    await integration.process_manager.stop_all_servers()

async def demo_manual_integration():
    """Demonstrate manual integration steps"""
    
    print("\n" + "="*60)
    print("🔧 Manual MCP Tool Integration Steps")
    print("="*60 + "\n")
    
    # Step 1: Search for tools
    print("Step 1: Searching for Python web scraping tools...")
    
    integration = HaiveMCPIntegration()
    results = await integration.mcp_system.search_servers(
        "Python web scraping tools", 
        method="self_query"
    )
    
    if results['documents']:
        print(f"Found {len(results['documents'])} tools:")
        for i, doc in enumerate(results['documents'][:3], 1):
            metadata = doc.metadata
            print(f"\n{i}. {metadata.get('server_name', 'Unknown')}")
            print(f"   Category: {metadata.get('category', 'unknown')}")
            print(f"   Language: {metadata.get('language', 'unknown')}")
            print(f"   Stars: {metadata.get('stars', 0)} ⭐")
    
    # Step 2: Show configuration
    print("\n\nStep 2: Example FastMCP configuration:")
    
    example_config = {
        "name": "web-scraper",
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "web_scraper_mcp"],
        "env": {"API_KEY": "your-key-here"},
        "active": True
    }
    
    print(json.dumps(example_config, indent=2))
    
    # Step 3: Show agent creation
    print("\n\nStep 3: Creating haive agent with MCP tool:")
    
    print("""
from haive.agents.react import ReactAgent
from haive.core.engine.aug_llm import AugLLMConfig
from langchain_core.tools import Tool

# Create MCP tool wrapper
def web_scraper_tool(url: str) -> str:
    # Connect to MCP server and execute
    return f"Scraped content from {url}"

scraper_tool = Tool(
    name="web_scraper",
    description="Scrape web pages",
    func=web_scraper_tool
)

# Create agent with tool
agent = ReactAgent(
    name="web_research_agent",
    engine=AugLLMConfig(),
    tools=[scraper_tool]
)

# Use the agent
result = await agent.arun("Scrape https://example.com")
    """)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        asyncio.run(demo_manual_integration())
    else:
        asyncio.run(demo_discovery_to_agent())