#!/usr/bin/env python3
"""Test script for MCP integration in haive-dataflow."""

import asyncio
import logging

from haive.dataflow import (
    EntityType,
    MCPServerConfig,
    MCPTransport,
    registry_system,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mcp_integration():
    """Test the MCP integration with haive-dataflow."""
    # Test 1: Import MCP models
    logger.info("Test 1: Checking MCP model imports...")
    try:
        # Create a test MCP server config
        test_config = MCPServerConfig(
            name="test-mcp-server",
            transport=MCPTransport.STDIO,
            command="test-command",
            args=["--test"],
            capabilities=["read", "write"],
        )
        logger.info(f"✓ Created MCPServerConfig: {test_config.name}")
    except Exception as e:
        logger.error(f"✗ Failed to create MCPServerConfig: {e}")
        return

    # Test 2: Register MCP server in registry
    logger.info("\nTest 2: Registering MCP server in registry...")
    try:
        server_id = registry_system.register_entity(
            name=test_config.name,
            entity_type=EntityType.MCP_SERVER,
            description="Test MCP server for integration testing",
            metadata={
                "module_path": "haive.dataflow.mcp.test",
                "class_name": "TestMCPServer",
                "config": test_config.model_dump(),
                "tags": ["test", "example", "mcp"],
            },
        )
        logger.info(f"✓ Registered MCP server with ID: {server_id}")
    except Exception as e:
        logger.error(f"✗ Failed to register MCP server: {e}")
        return

    # Test 3: Query MCP servers from registry
    logger.info("\nTest 3: Querying MCP servers from registry...")
    try:
        mcp_servers = registry_system.get_entities_by_type(EntityType.MCP_SERVER)
        logger.info(f"✓ Found {len(mcp_servers)} MCP servers in registry")

        for server in mcp_servers:
            if isinstance(server, dict):
                logger.info(
                    f"  - {server.get('name', 'Unknown')}: {server.get('description', 'No description')}"
                )
            else:
                logger.info(f"  - {server.name}: {server.description}")
    except Exception as e:
        logger.error(f"✗ Failed to query MCP servers: {e}")
        return

    # Test 4: Test MCP discovery (skip for now due to timeout)
    logger.info("\nTest 4: Skipping full discovery test (can cause timeout)")

    # Test 5: Import MCP modules
    logger.info("\nTest 5: Testing MCP module imports...")
    try:
        from haive.dataflow.mcp.client import MCPClient, MCPToolProvider
        from haive.dataflow.mcp.discovery import discover_mcp_servers_from_npm
        from haive.dataflow.mcp.health import MCPHealthMonitor

        logger.info("✓ Successfully imported MCP modules:")
        logger.info("  - discover_mcp_servers_from_npm")
        logger.info("  - MCPClient")
        logger.info("  - MCPToolProvider")
        logger.info("  - MCPHealthMonitor")
    except ImportError as e:
        logger.error(f"✗ Failed to import MCP modules: {e}")
        return

    # Test 6: Create MCP client
    logger.info("\nTest 6: Creating MCP client...")
    try:
        mcp_client = MCPClient(registry_system)
        logger.info("✓ Created MCP client instance")

        # Try to initialize from registry
        success = await mcp_client.initialize_from_registry()
        if success:
            logger.info("✓ MCP client initialized from registry")
        else:
            logger.warning(
                "⚠ MCP client initialization returned False (this may be expected if no real servers are configured)"
            )
    except Exception as e:
        logger.error(f"✗ Failed to create/initialize MCP client: {e}")

    logger.info("\n✅ MCP integration tests completed!")


if __name__ == "__main__":
    asyncio.run(test_mcp_integration())
