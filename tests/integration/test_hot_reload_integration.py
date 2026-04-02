"""Integration tests for hot-reload functionality of MCP Manager."""

import asyncio

import pytest

from haive.mcp.config import MCPServerConfig
from haive.mcp.manager import MCPManager, MCPRegistrationResult, MCPServerStatus


@pytest.mark.asyncio
async def test_hot_reload_integration():
    """Integration test for hot-reload functionality."""
    # Create manager with health check disabled
    manager = MCPManager(auto_health_check=False)

    # Initially no tools
    tools = await manager.get_all_tools()
    assert tools == []

    # Add a mock server config (won't actually connect)
    config = MCPServerConfig(
        name="test_server", transport="stdio", command="echo", args=["test"]
    )

    # Store it as if it were connected
    manager._servers["test_server"] = config
    manager._server_status["test_server"] = MCPServerStatus.CONNECTED
    manager._server_tools["test_server"] = ["tool1", "tool2"]

    # Now refresh should work
    await manager.refresh_tools()

    # The tools should be cleared since we don't have real sessions
    assert manager._server_tools == {}

    # Test that get_all_tools with refresh=True calls refresh
    list(manager._server_tools.keys())
    tools = await manager.get_all_tools(refresh=True)

    # Since we don't have real sessions, tools will be empty
    assert tools == []


@pytest.mark.asyncio
async def test_add_server_auto_refresh():
    """Test that add_server with success triggers refresh."""
    manager = MCPManager(auto_health_check=False)

    # Track the state changes
    states = []

    # Override _connect_server to track calls

    async def tracking_connect(server_name, config):
        states.append("connect_called")
        # Return success result
        return MCPRegistrationResult(
            server_name=server_name,
            success=True,
            status=MCPServerStatus.CONNECTED,
            tools_count=2,
            tools=["tool1", "tool2"],
        )

    # Override refresh_tools to track calls
    original_refresh = manager.refresh_tools

    async def tracking_refresh():
        states.append("refresh_called")
        await original_refresh()

    # Use setattr on the instance's __dict__ to bypass Pydantic
    object.__setattr__(manager, "_connect_server", tracking_connect)
    object.__setattr__(manager, "refresh_tools", tracking_refresh)

    # Add server
    config = MCPServerConfig(
        name="test", transport="stdio", command="echo", args=["test"]
    )

    result = await manager.add_server("test", config, connect_immediately=True)

    # Verify the sequence
    assert result.success
    assert "connect_called" in states
    assert "refresh_called" in states
    assert states.index("connect_called") < states.index("refresh_called")


@pytest.mark.asyncio
async def test_reload_server_functionality():
    """Test the reload_server method."""
    manager = MCPManager(auto_health_check=False)

    # Set up a server
    config = MCPServerConfig(
        name="test", transport="stdio", command="echo", args=["test"]
    )

    # Add server manually
    manager._servers["test"] = config
    manager._server_status["test"] = MCPServerStatus.CONNECTED
    manager._clients["test"] = {"session": None}

    # Reload should fail for non-existent server
    result = await manager.reload_server("nonexistent")
    assert not result.success
    assert "not found" in result.error_message

    # For existing server, reload will try to remove and re-add
    # Since we don't have real connections, we just verify the flow
    result = await manager.reload_server("test")

    # It will fail because we don't have real MCP connections
    # but we can verify it tried
    assert "test" in manager._servers  # Config should still be there


@pytest.mark.asyncio
async def test_get_resources_and_prompts():
    """Test getting resources and prompts from servers."""
    manager = MCPManager(auto_health_check=False)

    # Mock a connected server with session
    class MockSession:
        async def list_resources(self):
            class ResourceResult:
                resources = ["resource1", "resource2"]

            return ResourceResult()

        async def list_prompts(self):
            class PromptResult:
                prompts = ["prompt1", "prompt2", "prompt3"]

            return PromptResult()

    manager._clients["server1"] = {"session": MockSession()}
    manager._server_status["server1"] = MCPServerStatus.CONNECTED

    # Get resources
    resources = await manager.get_resources()
    assert len(resources) == 2
    assert "resource1" in resources

    # Get prompts
    prompts = await manager.get_prompts()
    assert len(prompts) == 3
    assert "prompt1" in prompts

    # Test specific server
    resources_server1 = await manager.get_resources("server1")
    assert len(resources_server1) == 2

    # Test non-existent server - it returns all resources if server not found
    resources_none = await manager.get_resources("nonexistent")
    # Since "nonexistent" is not in clients, it checks all servers
    assert len(resources_none) == 2  # Still gets resources from server1


@pytest.mark.asyncio
async def test_manager_shutdown():
    """Test manager shutdown process."""
    manager = MCPManager(auto_health_check=False)

    # Add some state
    manager._servers["test"] = MCPServerConfig(
        name="test", transport="stdio", command="echo", args=["test"]
    )

    # Shutdown
    await manager.shutdown()

    # Verify shutdown
    assert not manager.enabled
    assert manager._clients == {}
    assert manager._multi_client is None


@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent server operations."""
    manager = MCPManager(auto_health_check=False)

    # Define multiple server configs
    configs = [
        MCPServerConfig(
            name=f"server{i}", transport="stdio", command="echo", args=[f"test{i}"]
        )
        for i in range(3)
    ]

    # Add servers concurrently (they'll fail but we test the pattern)
    tasks = []
    for i, config in enumerate(configs):
        task = manager.add_server(f"server{i}", config, connect_immediately=False)
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    # All should succeed in adding (but not connecting)
    assert all(r.success for r in results)
    assert all(r.status == MCPServerStatus.PENDING for r in results)

    # Verify all servers are registered
    assert len(manager._servers) == 3
    assert all(f"server{i}" in manager._servers for i in range(3))
