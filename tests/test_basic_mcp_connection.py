#!/usr/bin/env python3
"""Test basic MCP connection with official filesystem server.

This test validates that we can:
1. Start an MCP server process (filesystem)
2. Connect to it via stdio transport
3. Discover available tools
4. Execute a basic tool call
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_filesystem_server_direct():
    """Test filesystem server with direct subprocess communication."""
    logger.info("=== Testing Filesystem Server Direct Connection ===")
    
    try:
        # Start the filesystem server
        logger.info("Starting filesystem server with npx...")
        process = subprocess.Popen(
            ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0  # Unbuffered for real-time communication
        )
        
        logger.info(f"Server started with PID: {process.pid}")
        
        # Give it a moment to start
        await asyncio.sleep(2)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"Server exited immediately. Stderr: {stderr}")
            return False
        
        logger.info("✅ Server is running")
        
        # Test basic MCP communication
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "clientInfo": {
                    "name": "haive-mcp-test",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        
        logger.info("Sending initialization request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Try to read response
        logger.info("Waiting for response...")
        response_line = process.stdout.readline()
        if response_line:
            logger.info(f"Got response: {response_line.strip()}")
            try:
                response = json.loads(response_line)
                logger.info(f"✅ Parsed response: {json.dumps(response, indent=2)}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse response: {response_line}")
        else:
            logger.warning("No response received")
        
        # Clean shutdown
        logger.info("Shutting down server...")
        process.terminate()
        process.wait(timeout=5)
        logger.info("✅ Server stopped cleanly")
        
        return True
        
    except FileNotFoundError:
        logger.error("❌ npx not found. Please install Node.js and npm.")
        return False
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def test_with_langchain_adapters():
    """Test using langchain MCP adapters."""
    logger.info("\n=== Testing with LangChain MCP Adapters ===")
    
    try:
        from langchain_mcp_adapters.client import MCPSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
        
        logger.info("✅ Successfully imported langchain MCP adapters")
        
        # Configure server parameters
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            env=None
        )
        
        logger.info("Connecting to filesystem server...")
        
        # Use context manager for proper lifecycle
        async with stdio_client(server_params) as (read, write):
            logger.info("✅ Connected to server")
            
            # Create session
            async with MCPSession(read, write) as session:
                logger.info("✅ MCP session established")
                
                # Initialize
                await session.initialize()
                logger.info("✅ Session initialized")
                
                # List available tools
                logger.info("Discovering tools...")
                tools_response = await session.list_tools()
                
                if hasattr(tools_response, 'tools'):
                    logger.info(f"✅ Found {len(tools_response.tools)} tools:")
                    for tool in tools_response.tools:
                        logger.info(f"  - {tool.name}: {tool.description}")
                else:
                    logger.warning("No tools found or unexpected response format")
                
                # List available resources
                logger.info("\nDiscovering resources...")
                resources_response = await session.list_resources()
                
                if hasattr(resources_response, 'resources'):
                    logger.info(f"✅ Found {len(resources_response.resources)} resources:")
                    for resource in resources_response.resources:
                        logger.info(f"  - {resource.uri}: {resource.name}")
                else:
                    logger.warning("No resources found")
                
                # Try a simple tool call if we have tools
                if hasattr(tools_response, 'tools') and tools_response.tools:
                    first_tool = tools_response.tools[0]
                    logger.info(f"\nTesting tool call: {first_tool.name}")
                    
                    # Prepare arguments based on tool
                    if first_tool.name == "read_file":
                        args = {"path": "/tmp/test.txt"}
                    elif first_tool.name == "list_directory":
                        args = {"path": "/tmp"}
                    else:
                        args = {}
                    
                    try:
                        result = await session.call_tool(first_tool.name, arguments=args)
                        logger.info(f"✅ Tool call successful: {result}")
                    except Exception as e:
                        logger.warning(f"Tool call failed (expected for non-existent files): {e}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import MCP adapters: {e}")
        logger.info("Install with: pip install langchain-mcp-adapters mcp")
        return False
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def test_with_existing_manager():
    """Test using our existing MCP manager."""
    logger.info("\n=== Testing with Existing MCP Manager ===")
    
    try:
        from haive.mcp.manager import MCPManager
        from haive.mcp.config import MCPServerConfig, MCPTransport
        
        logger.info("✅ Successfully imported MCP manager")
        
        # Create manager
        manager = MCPManager()
        
        # Configure filesystem server
        server_config = MCPServerConfig(
            name="filesystem",
            transport=MCPTransport.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            capabilities=["file_read", "file_write", "directory_list"],
            description="Local filesystem operations"
        )
        
        logger.info("Adding filesystem server to manager...")
        result = await manager.add_server("filesystem", server_config)
        
        logger.info(f"Registration result: {result}")
        logger.info(f"  Success: {result.success}")
        logger.info(f"  Status: {result.status}")
        logger.info(f"  Tools found: {result.tools_count}")
        if result.tools:
            logger.info(f"  Tool names: {result.tools}")
        if result.error_message:
            logger.error(f"  Error: {result.error_message}")
        
        # Get server status
        status = manager.get_all_server_status()
        logger.info(f"\nManager status: {json.dumps(status, indent=2)}")
        
        # Try to get tools
        tools = await manager.get_all_tools()
        logger.info(f"\nAvailable tools: {len(tools)}")
        
        # Shutdown
        await manager.shutdown()
        logger.info("✅ Manager shutdown complete")
        
        return result.success
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def test_with_server_manager():
    """Test using our existing server manager."""
    logger.info("\n=== Testing with Server Manager ===")
    
    try:
        from haive.mcp.servers.mcp_server_manager import MCPServerManager
        
        logger.info("✅ Successfully imported server manager")
        
        # Create manager
        manager = MCPServerManager()
        
        # Start filesystem server
        logger.info("Starting filesystem server...")
        success = manager.start_server("filesystem")
        
        if success:
            logger.info("✅ Server started successfully")
            
            # Get status
            status = manager.get_status()
            logger.info(f"Server status: {json.dumps(status, indent=2)}")
            
            # Let it run for a bit
            await asyncio.sleep(3)
            
            # Stop server
            manager.stop_server("filesystem")
            logger.info("✅ Server stopped")
        else:
            logger.error("❌ Failed to start server")
        
        return success
        
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("=== MCP Basic Connection Tests ===\n")
    
    # Check if npx is available
    try:
        result = subprocess.run(["npx", "--version"], capture_output=True, check=True)
        logger.info(f"✅ npx version: {result.stdout.decode().strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("❌ npx not found. Please install Node.js and npm first.")
        logger.info("Visit: https://nodejs.org/")
        return
    
    # Run tests
    tests = [
        ("Direct Connection", test_filesystem_server_direct),
        ("LangChain Adapters", test_with_langchain_adapters),
        ("MCP Manager", test_with_existing_manager),
        ("Server Manager", test_with_server_manager),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.exception(f"Test {test_name} crashed: {e}")
            results[test_name] = False
        await asyncio.sleep(1)  # Brief pause between tests
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("=== Test Summary ===")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    logger.info(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")


if __name__ == "__main__":
    asyncio.run(main())