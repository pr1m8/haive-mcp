#!/usr/bin/env python3
"""Direct test of FastMCP server functionality."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path so we can import our servers
sys.path.insert(0, str(Path(__file__).parent / "src"))

from haive.mcp.servers.dataflow_server import mcp as dataflow_mcp
from haive.mcp.servers.example_server import mcp as example_mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_fastmcp_tools():
    """Test FastMCP tools directly."""
    logger.info("=== Testing FastMCP Tools ===\n")

    # Get all tools from example server
    logger.info("Example Server Tools:")
    for tool_name, tool_func in example_mcp._tools.items():
        logger.info(
            f"  - {tool_name}: {tool_func.__doc__.strip() if tool_func.__doc__ else 'No description'}"
        )

    # Test read_file tool
    logger.info("\nTesting read_file tool...")
    try:
        # Read this test file itself
        content = await example_mcp._tools["read_file"](__file__)
        logger.info(f"✓ Successfully read file, length: {len(content)} chars")
    except Exception as e:
        logger.exception(f"✗ Error reading file: {e}")

    # Test list_directory tool
    logger.info("\nTesting list_directory tool...")
    try:
        files = await example_mcp._tools["list_directory"](".", "*.py")
        logger.info(f"✓ Found {len(files)} Python files in current directory")
        for f in files[:5]:  # Show first 5
            logger.info(f"  - {f}")
    except Exception as e:
        logger.exception(f"✗ Error listing directory: {e}")

    # Test write_file tool
    logger.info("\nTesting write_file tool...")
    try:
        test_file = "test_output.txt"
        result = await example_mcp._tools["write_file"](
            test_file, "Hello from MCP server!"
        )
        logger.info(f"✓ {result}")

        # Clean up
        Path(test_file).unlink(missing_ok=True)
    except Exception as e:
        logger.exception(f"✗ Error writing file: {e}")


async def test_fastmcp_prompts():
    """Test FastMCP prompts."""
    logger.info("\n=== Testing FastMCP Prompts ===\n")

    # Get all prompts
    logger.info("Available Prompts:")
    for prompt_name, prompt_func in example_mcp._prompts.items():
        logger.info(
            f"  - {prompt_name}: {prompt_func.__doc__.strip() if prompt_func.__doc__ else 'No description'}"
        )

    # Test code review prompt
    logger.info("\nTesting code_review_prompt...")
    try:
        test_code = """
def calculate_sum(numbers):
    total = 0
    for i in range(len(numbers)):
        total = total + numbers[i]
    return total
"""
        prompt = await example_mcp._prompts["code_review_prompt"](test_code, "python")
        logger.info("✓ Generated code review prompt:")
        logger.info(prompt[:200] + "..." if len(prompt) > 200 else prompt)
    except Exception as e:
        logger.exception(f"✗ Error generating prompt: {e}")


async def test_dataflow_server():
    """Test dataflow MCP server."""
    logger.info("\n=== Testing Dataflow Server ===\n")

    # Check if dataflow is available
    server_info = await dataflow_mcp._server_info()
    logger.info(f"Dataflow available: {server_info['dataflow_available']}")

    if server_info["dataflow_available"]:
        # Test list_components
        logger.info("\nTesting list_components tool...")
        try:
            components = await dataflow_mcp._tools["list_components"]("all")
            logger.info("✓ Component types found:")
            for comp_type, items in components.items():
                if not comp_type.startswith("error"):
                    logger.info(f"  - {comp_type}: {len(items)} components")
        except Exception as e:
            logger.exception(f"✗ Error listing components: {e}")

        # Test create_agent_config
        logger.info("\nTesting create_agent_config tool...")
        try:
            config = await dataflow_mcp._tools["create_agent_config"](
                "simple", "TestAgent", "gpt-4", 0.7
            )
            logger.info("✓ Generated agent config:")
            logger.info(f"  Name: {config['config']['name']}")
            logger.info("  Type: simple")
            logger.info(f"  Model: {config['config']['engine']['model']}")
        except Exception as e:
            logger.exception(f"✗ Error creating agent config: {e}")
    else:
        logger.warning("⚠ Dataflow not available, skipping dataflow tests")


async def test_mcp_protocol():
    """Test MCP protocol methods."""
    logger.info("\n=== Testing MCP Protocol ===\n")

    # Test server capabilities
    logger.info("Testing server capabilities...")

    # Example server
    example_caps = await example_mcp._server_info()
    logger.info(f"Example Server: {example_caps['name']} v{example_caps['version']}")
    logger.info(f"  Tools: {len(example_caps['capabilities']['tools'])}")
    logger.info(f"  Prompts: {len(example_caps['capabilities']['prompts'])}")

    # Dataflow server
    dataflow_caps = await dataflow_mcp._server_info()
    logger.info(
        f"\nDataflow Server: {dataflow_caps['name']} v{dataflow_caps['version']}"
    )
    logger.info(f"  Tools: {len(dataflow_caps['capabilities']['tools'])}")
    logger.info(f"  Prompts: {len(dataflow_caps['capabilities']['prompts'])}")


async def main():
    """Run all tests."""
    logger.info("=== Direct FastMCP Testing ===\n")

    await test_fastmcp_tools()
    await test_fastmcp_prompts()
    await test_dataflow_server()
    await test_mcp_protocol()

    logger.info("\n✅ Direct FastMCP tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
