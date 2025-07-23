#!/usr/bin/env python3
"""Test client for HTTP MCP server."""

import asyncio
import json
import logging

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_http_server():
    """Test the HTTP MCP server."""
    base_url = "http://localhost:8001"

    async with aiohttp.ClientSession() as session:
        # Test root endpoint
        logger.info("Testing root endpoint...")
        async with session.get(f"{base_url}/") as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"✓ Server info: {json.dumps(data, indent=2)}")
            else:
                logger.error(f"✗ Failed to get server info: {resp.status}")

        # Test tools listing
        logger.info("\nTesting tools endpoint...")
        async with session.get(f"{base_url}/tools") as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"✓ Available tools: {data['count']}")
                for tool_name, tool_info in data["tools"].items():
                    logger.info(f"  - {tool_name}: {tool_info['description']}")
            else:
                logger.error(f"✗ Failed to list tools: {resp.status}")

        # Test tool execution
        logger.info("\nTesting tool execution...")

        # Test hello tool
        payload = {"tool": "hello", "params": {"name": "Haive"}}
        async with session.post(f"{base_url}/execute", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"✓ hello result: {data['result']}")
            else:
                logger.error(f"✗ Failed to execute hello: {resp.status}")

        # Test add tool
        payload = {"tool": "add", "params": {"x": 10, "y": 32}}
        async with session.post(f"{base_url}/execute", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"✓ add(10, 32) = {data['result']}")
            else:
                logger.error(f"✗ Failed to execute add: {resp.status}")

        # Test get_time tool
        payload = {"tool": "get_time", "params": {}}
        async with session.post(f"{base_url}/execute", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"✓ Current time: {data['result']}")
            else:
                logger.error(f"✗ Failed to execute get_time: {resp.status}")

        # Test invalid tool
        payload = {"tool": "invalid_tool", "params": {}}
        async with session.post(f"{base_url}/execute", json=payload) as resp:
            if resp.status == 400:
                data = await resp.json()
                logger.info(f"✓ Correctly rejected invalid tool: {data['error']}")
            else:
                logger.error("✗ Should have rejected invalid tool")


async def main():
    """Run the test."""
    logger.info("=== HTTP MCP Server Test ===\n")

    logger.info("Make sure the server is running with:")
    logger.info("  poetry run python src/haive/mcp/servers/simple_http_server.py\n")

    try:
        await test_http_server()
        logger.info("\n✅ All tests completed!")
    except aiohttp.ClientError as e:
        logger.error(f"\n❌ Connection error: {e}")
        logger.error("Is the server running?")


if __name__ == "__main__":
    asyncio.run(main())
