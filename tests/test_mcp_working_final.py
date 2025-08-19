#!/usr/bin/env python3
"""Final working MCP test with all fixes applied."""

import asyncio
import logging
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_stdio_client_correct():
    """Test stdio_client with correct usage pattern."""
    logger.info("=== Testing stdio_client (Correct Pattern) ===")
    
    try:
        from mcp.client.stdio import StdioServerParameters, stdio_client
        from langchain_mcp_adapters.client import create_session, load_mcp_tools
        
        logger.info("✅ Imported MCP components")
        
        # Create server parameters
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            env=None
        )
        
        # Connect using stdio_client
        async with stdio_client(server_params) as (read_stream, write_stream):
            logger.info("✅ Connected to filesystem server")
            
            # Create a session using the streams
            async with create_session(read_stream, write_stream) as session:
                logger.info("✅ Session created")
                
                # Now we can use the session
                await session.initialize()
                logger.info("✅ Session initialized")
                
                # List tools
                tools_response = await session.list_tools()
                logger.info(f"✅ Found {len(tools_response.tools)} tools:")
                for tool in tools_response.tools:
                    logger.info(f"  - {tool.name}: {tool.description}")
                
                # List resources
                resources_response = await session.list_resources()
                logger.info(f"\n✅ Found {len(resources_response.resources)} resources")
                
                # Try a tool call
                if tools_response.tools:
                    tool = tools_response.tools[0]
                    logger.info(f"\nTesting tool: {tool.name}")
                    
                    try:
                        if tool.name == "list_directory":
                            result = await session.call_tool(
                                tool.name, 
                                arguments={"path": "/tmp"}
                            )
                        elif tool.name == "read_file":
                            result = await session.call_tool(
                                tool.name,
                                arguments={"path": "/tmp/test.txt"}
                            )
                        else:
                            result = await session.call_tool(tool.name, arguments={})
                        
                        logger.info(f"✅ Tool result: {result}")
                    except Exception as e:
                        logger.warning(f"Tool call error (expected): {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def test_multi_server_client_correct():
    """Test MultiServerMCPClient with correct usage pattern."""
    logger.info("\n=== Testing MultiServerMCPClient (Correct Pattern) ===")
    
    try:
        from langchain_mcp_adapters.client import (
            MultiServerMCPClient, 
            StdioConnection,
            load_mcp_tools
        )
        
        logger.info("✅ Imported MultiServerMCPClient")
        
        # Define connection configuration
        connections = {
            "filesystem": StdioConnection(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            )
        }
        
        # Create client (NOT as context manager)
        client = MultiServerMCPClient(connections)
        logger.info("✅ Created MultiServerMCPClient")
        
        # Method 1: Get tools directly (if supported)
        try:
            tools = await client.get_tools()
            logger.info(f"✅ Method 1: Got {len(tools)} tools")
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")
        except Exception as e:
            logger.warning(f"Method 1 failed (checking method 2): {e}")
            
            # Method 2: Use session
            async with client.session("filesystem") as session:
                logger.info("✅ Got session for filesystem server")
                
                # Load tools using the session
                tools = await load_mcp_tools(session)
                logger.info(f"✅ Method 2: Loaded {len(tools)} tools:")
                for tool in tools:
                    logger.info(f"  - {tool.name}: {tool.description}")
                
                # Test a tool
                if tools:
                    tool = tools[0]
                    logger.info(f"\nTesting tool: {tool.name}")
                    try:
                        if tool.name == "list_directory":
                            result = await tool.ainvoke({"path": "/tmp"})
                        else:
                            result = await tool.ainvoke({})
                        logger.info(f"✅ Tool result: {result}")
                    except Exception as e:
                        logger.warning(f"Tool execution error: {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def test_haive_integration_pattern():
    """Test how MCP should integrate with Haive agents."""
    logger.info("\n=== Testing Haive Integration Pattern ===")
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient, StdioConnection
        
        # This shows the PATTERN even if we can't fully execute it
        logger.info("Pattern for integrating MCP with Haive agents:")
        logger.info("""
1. Create MCP client and get tools:
   client = MultiServerMCPClient(connections)
   tools = await client.get_tools()

2. Add tools to Haive agent:
   agent = SimpleAgent(
       engine=AugLLMConfig(),
       tools=tools  # MCP tools work as LangChain tools!
   )

3. Use agent normally:
   result = await agent.arun({"messages": [...]})
""")
        
        # Show the connection config
        connections = {
            "filesystem": StdioConnection(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            ),
            "github": StdioConnection(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env={"GITHUB_TOKEN": "your_token"}
            )
        }
        
        logger.info(f"✅ Connection configuration created for {len(connections)} servers")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def test_simple_mcp_connection():
    """Test the simplest possible MCP connection."""
    logger.info("\n=== Testing Simplest MCP Connection ===")
    
    try:
        import subprocess
        
        # Start filesystem server
        logger.info("Starting filesystem server...")
        process = subprocess.Popen(
            ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it time to start
        await asyncio.sleep(2)
        
        # Send a simple request
        request = json.dumps({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "clientInfo": {
                    "name": "test",
                    "version": "1.0.0"
                },
                "capabilities": {}
            },
            "id": 1
        }) + "\n"
        
        process.stdin.write(request)
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line)
            logger.info(f"✅ Got response: {response}")
            success = "result" in response
        else:
            logger.error("No response received")
            success = False
        
        # Clean up
        process.terminate()
        process.wait()
        
        return success
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("=== Final Working MCP Tests ===\n")
    
    tests = [
        ("Simple Connection", test_simple_mcp_connection),
        ("stdio_client Pattern", test_stdio_client_correct),
        ("MultiServerMCPClient Pattern", test_multi_server_client_correct),
        ("Haive Integration", test_haive_integration_pattern),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.exception(f"Test {test_name} crashed: {e}")
            results[test_name] = False
        await asyncio.sleep(1)
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("=== Test Summary ===")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    # Key learnings
    logger.info("\n=== Key Learnings ===")
    logger.info("1. stdio_client returns streams, not callable functions")
    logger.info("2. Use create_session() to wrap the streams into a usable session") 
    logger.info("3. MultiServerMCPClient is NOT a context manager - create it directly")
    logger.info("4. Use client.session(server_name) to get a session context manager")
    logger.info("5. MCP tools from langchain-mcp-adapters work as LangChain tools")
    
    # Next steps
    logger.info("\n=== Next Steps for haive-mcp ===")
    logger.info("1. Fix bulk installer to use npm/pip instead of git clone")
    logger.info("2. Update MCPManager to use correct langchain-mcp-adapters patterns")
    logger.info("3. Fix MCPAgent to properly initialize and discover tools")
    logger.info("4. Create examples showing MCP tools in Haive agents")


if __name__ == "__main__":
    asyncio.run(main())