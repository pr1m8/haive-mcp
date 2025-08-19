#!/usr/bin/env python3
"""Working MCP integration test using the correct langchain-mcp-adapters API."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_mcp_with_langchain_adapters():
    """Test MCP using the correct langchain-mcp-adapters pattern."""
    logger.info("=== Testing MCP with LangChain Adapters ===")
    
    try:
        from langchain_mcp_adapters.client import (
            StdioConnection,
            MultiServerMCPClient,
            load_mcp_tools
        )
        from mcp.client.stdio import StdioServerParameters, stdio_client
        
        logger.info("✅ Successfully imported MCP components")
        
        # Method 1: Using stdio_client directly
        logger.info("\n--- Method 1: Direct stdio_client ---")
        
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            logger.info("✅ Connected to filesystem server")
            
            # Initialize session
            await write({
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "0.1.0",
                    "clientInfo": {
                        "name": "haive-mcp-test",
                        "version": "1.0.0"
                    },
                    "capabilities": {}
                },
                "id": 1
            })
            
            init_response = await read()
            logger.info(f"Initialize response: {init_response.get('result', {}).get('serverInfo', {})}")
            
            # Load tools using the helper
            logger.info("\nLoading tools with load_mcp_tools...")
            tools = await load_mcp_tools(read, write)
            logger.info(f"✅ Loaded {len(tools)} tools:")
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")
        
        # Method 2: Using MultiServerMCPClient
        logger.info("\n--- Method 2: MultiServerMCPClient ---")
        
        # Define connection configuration
        connections = {
            "filesystem": StdioConnection(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            )
        }
        
        # Create multi-server client
        async with MultiServerMCPClient(connections) as client:
            logger.info("✅ Connected via MultiServerMCPClient")
            
            # Get tools
            tools = client.get_tools()
            logger.info(f"✅ Got {len(tools)} tools from client:")
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")
                
            # Test a tool if available
            if tools:
                tool = tools[0]
                logger.info(f"\nTesting tool: {tool.name}")
                try:
                    # Prepare arguments based on tool
                    if tool.name == "list_directory":
                        result = await tool.ainvoke({"path": "/tmp"})
                    elif tool.name == "read_file":
                        result = await tool.ainvoke({"path": "/tmp/test.txt"})
                    else:
                        result = await tool.ainvoke({})
                    
                    logger.info(f"✅ Tool result: {result}")
                except Exception as e:
                    logger.warning(f"Tool execution failed (expected): {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def test_integration_with_haive_agent():
    """Test how to integrate MCP tools with a Haive agent."""
    logger.info("\n=== Testing Integration with Haive Agent ===")
    
    try:
        from langchain_mcp_adapters.client import StdioConnection, MultiServerMCPClient
        from haive.agents.simple import SimpleAgent
        from haive.core.engine.aug_llm import AugLLMConfig
        
        logger.info("✅ Imported Haive and MCP components")
        
        # Create MCP client
        connections = {
            "filesystem": StdioConnection(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            )
        }
        
        async with MultiServerMCPClient(connections) as mcp_client:
            logger.info("✅ Connected to MCP servers")
            
            # Get tools from MCP
            mcp_tools = mcp_client.get_tools()
            logger.info(f"✅ Got {len(mcp_tools)} tools from MCP")
            
            # Create Haive agent with MCP tools
            agent = SimpleAgent(
                name="mcp_enhanced_agent",
                engine=AugLLMConfig(
                    temperature=0.7,
                    system_message="You are a helpful assistant with access to filesystem tools."
                ),
                tools=mcp_tools  # Add MCP tools to agent!
            )
            
            logger.info("✅ Created Haive agent with MCP tools")
            logger.info(f"   Agent has {len(agent.tools) if hasattr(agent, 'tools') else 0} tools")
            
            # The agent can now use MCP tools!
            # In a real scenario, you would:
            # result = await agent.arun({"messages": [{"role": "user", "content": "List files in /tmp"}]})
            
        return True
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def test_our_mcp_agent():
    """Test our MCPAgent class."""
    logger.info("\n=== Testing Our MCPAgent ===")
    
    try:
        from haive.mcp.agents.mcp_agent import MCPAgent
        from haive.mcp.config import MCPConfig, MCPServerConfig
        from haive.core.engine.aug_llm import AugLLMConfig
        
        logger.info("✅ Imported MCPAgent")
        
        # Create MCP configuration
        mcp_config = MCPConfig(
            enabled=True,
            servers={
                "filesystem": MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    capabilities=["file_read", "file_write", "directory_list"]
                )
            }
        )
        
        # Create agent
        agent = MCPAgent(
            name="test_mcp_agent",
            engine=AugLLMConfig(temperature=0.7),
            mcp_config=mcp_config
        )
        
        logger.info("✅ Created MCPAgent")
        
        # Initialize MCP
        await agent.setup()
        
        # Check status
        status = agent.get_mcp_status()
        logger.info(f"MCP Status: {status}")
        
        return status['enabled']
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("=== Working MCP Integration Tests ===\n")
    
    tests = [
        ("LangChain Adapters", test_mcp_with_langchain_adapters),
        ("Haive Integration", test_integration_with_haive_agent),
        ("MCPAgent Class", test_our_mcp_agent),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.exception(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("=== Test Summary ===")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    # Conclusions
    logger.info("\n=== Conclusions ===")
    logger.info("1. langchain-mcp-adapters provides the bridge between MCP and LangChain")
    logger.info("2. We can use stdio_client for direct communication")
    logger.info("3. MultiServerMCPClient manages multiple MCP servers")
    logger.info("4. MCP tools can be added to Haive agents as regular tools")
    logger.info("5. Our current implementation needs to use these patterns correctly")


if __name__ == "__main__":
    asyncio.run(main())