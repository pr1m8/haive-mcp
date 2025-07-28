#!/usr/bin/env python3
"""Test MCP server integration with LangChain adapters."""

import asyncio
import logging
import subprocess
import time
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_example_server():
    """Test the example MCP server."""
    logger.info("Testing example MCP server...")

    # First, let's check if we have the required packages
    try:
        import mcp
        from mcp.server.fastmcp import FastMCP

        logger.info("✓ MCP SDK is installed")
    except ImportError:
        logger.error("✗ MCP SDK not installed. Run: pip install mcp")
        return False

    try:
        from langchain_mcp_adapters import MultiServerMCPClient, load_mcp_tools

        logger.info("✓ LangChain MCP adapters installed")
    except ImportError:
        logger.error(
            "✗ LangChain MCP adapters not installed. Run: pip install langchain-mcp-adapters"
        )
        return False

    # Start the example server as a subprocess
    server_path = Path(__file__).parent / "src/haive/mcp/servers/example_server.py"
    logger.info(f"Starting MCP server from: {server_path}")

    try:
        # Start server process
        server_process = subprocess.Popen(
            ["python", str(server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Give server time to start
        time.sleep(2)

        # Check if server is running
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            logger.error(f"Server failed to start. Stdout: {stdout}")
            logger.error(f"Stderr: {stderr}")
            return False

        logger.info("✓ MCP server started successfully")

        # Now test with LangChain MCP adapter
        # Create client configuration for stdio transport
        client_config = {
            "example-servef": {
                "transport": "stdio",
                "command": "python",
                "args": [str(server_path)],
            }
        }

        # Create MCP client
        mcp_client = MultiServerMCPClient(client_config)
        logger.info("✓ Created MultiServerMCPClient")

        # Load tools
        tools = await load_mcp_tools(mcp_client)
        logger.info(f"✓ Loaded {len(tools)} tools from MCP server")

        # List available tools
        for tool in tools:
            logger.info(f"  - Tool: {tool.name} - {tool.description}")

        # Test a tool
        if tools:
            test_tool = tools[0]
            logger.info(f"\nTesting tool: {test_tool.name}")

            if test_tool.name == "list_directory":
                result = await test_tool.arun(path=".", pattern="*.py")
                logger.info(f"Tool result: {result}")

        return True

    except Exception as e:
        logger.error(f"Error testing MCP server: {e}")
        return False

    finally:
        # Clean up server process
        if "server_process" in locals():
            server_process.terminate()
            server_process.wait()
            logger.info("Server process terminated")


async def test_langchain_integration():
    """Test direct LangChain integration without running a server."""
    logger.info("\nTesting LangChain MCP integration...")

    try:
        from langchain_core.tools import Tool

        # Create a simple tool
        def simple_function(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y

        # Convert to MCP-compatible tool
        tool = Tool(
            name="add_numbers",
            description="Add two numbers together",
            func=simple_function,
        )

        logger.info(f"✓ Created LangChain tool: {tool.name}")

        # Test the tool
        result = tool.run({"x": 5, "y": 3})
        logger.info(f"✓ Tool execution result: {result}")

        return True

    except Exception as e:
        logger.error(f"Error testing LangChain integration: {e}")
        return False


async def test_mcp_with_dataflow():
    """Test MCP integration with haive-dataflow."""
    logger.info("\nTesting MCP with haive-dataflow...")

    try:
        from haive.dataflow import (
            EntityType,
            MCPServerConfig,
            MCPTransport,
            registry_system,
        )
        from haive.dataflow.mcp.client import MCPClient

        logger.info("✓ Imported haive-dataflow MCP components")

        # Register our example server in the registry
        server_config = MCPServerConfig(
            name="example-filesystem-server",
            transport=MCPTransport.STDIO,
            command="python",
            args=[
                str(Path(__file__).parent / "src/haive/mcp/servers/example_server.py")
            ],
            capabilities=["read_file", "write_file", "list_directory", "search_files"],
        )

        server_id = registry_system.register_entity(
            name=server_config.name,
            entity_type=EntityType.MCP_SERVER,
            description="Example filesystem MCP servef",
            metadata={
                "config": server_config.model_dump(),
                "module_path": "haive.mcp.servers.example_server",
            },
        )

        logger.info(f"✓ Registered MCP server in dataflow: {server_id}")

        # Create MCP client
        mcp_client = MCPClient(registry_system)
        logger.info("✓ Created dataflow MCP client")

        # Initialize from registry
        success = await mcp_client.initialize_from_registry()
        logger.info(f"✓ MCP client initialization: {success}")

        if success:
            # Get available tools
            tools = await mcp_client.get_available_tools()
            logger.info(f"✓ Available tools: {len(tools)}")

        return True

    except Exception as e:
        logger.error(f"Error testing MCP with dataflow: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    logger.info("=== MCP Server Integration Tests ===\n")

    # Test 1: Basic LangChain integration
    test1_passed = await test_langchain_integration()

    # Test 2: Example MCP server
    test2_passed = await test_example_server()

    # Test 3: Dataflow integration
    test3_passed = await test_mcp_with_dataflow()

    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"LangChain Integration: {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    logger.info(f"Example MCP Server: {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    logger.info(f"Dataflow Integration: {'✓ PASSED' if test3_passed else '✗ FAILED'}")

    all_passed = test1_passed and test2_passed and test3_passed
    logger.info(
        f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}"
    )


if __name__ == "__main__":
    asyncio.run(main())
