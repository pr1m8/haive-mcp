"""Test hot-reload functionality of MCP Manager."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from haive.mcp.config import MCPServerConfig
from haive.mcp.manager import MCPManager, MCPRegistrationResult, MCPServerStatus


@pytest.mark.asyncio
async def test_get_all_tools_with_refresh():
    """Test that get_all_tools can refresh the tool list."""
    # Create manager with health check disabled
    manager = MCPManager(auto_health_check=False)

    # Mock the multi-client
    mock_client = MagicMock()
    mock_client.get_tools.return_value = ["tool1", "tool2"]
    manager._multi_client = mock_client

    # Track refresh calls
    refresh_called = False
    original_refresh = manager.refresh_tools

    async def mock_refresh():
        nonlocal refresh_called
        refresh_called = True
        return await original_refresh()

    # Replace method while preserving original functionality
    manager.refresh_tools = mock_refresh

    # Get tools without refresh
    tools = await manager.get_all_tools(refresh=False)
    assert tools == ["tool1", "tool2"]
    assert not refresh_called

    # Get tools with refresh
    tools = await manager.get_all_tools(refresh=True)
    assert tools == ["tool1", "tool2"]
    assert refresh_called


@pytest.mark.asyncio
async def test_add_server_triggers_refresh():
    """Test that adding a server triggers tool refresh on success."""
    # Create manager with health check disabled
    manager = MCPManager(auto_health_check=False)

    # Track refresh calls
    refresh_called = False

    async def mock_refresh():
        nonlocal refresh_called
        refresh_called = True

    # Mock internal methods
    async def mock_connect_server(server_name, config):
        return MCPRegistrationResult(
            server_name="test",
            success=True,
            status=MCPServerStatus.CONNECTED,
            tools_count=3,
            tools=["tool1", "tool2", "tool3"],
        )

    manager._connect_server = mock_connect_server
    manager.refresh_tools = mock_refresh

    # Add server with successful connection
    config = MCPServerConfig(
        name="test", transport="stdio", command="echo", args=["test"]
    )

    result = await manager.add_server("test", config, connect_immediately=True)

    # Verify refresh was called
    assert result.success
    assert refresh_called


@pytest.mark.asyncio
async def test_add_server_no_refresh_on_failure():
    """Test that failed server addition doesn't trigger refresh."""
    # Create manager with health check disabled
    manager = MCPManager(auto_health_check=False)

    # Track refresh calls
    refresh_called = False

    async def mock_refresh():
        nonlocal refresh_called
        refresh_called = True

    # Mock failed connection
    async def mock_connect_server(server_name, config):
        return MCPRegistrationResult(
            server_name="test",
            success=False,
            status=MCPServerStatus.FAILED,
            error_message="Connection failed",
        )

    manager._connect_server = mock_connect_server
    manager.refresh_tools = mock_refresh

    # Add server with failed connection
    config = MCPServerConfig(
        name="test", transport="stdio", command="echo", args=["test"]
    )

    result = await manager.add_server("test", config, connect_immediately=True)

    # Verify refresh was NOT called
    assert not result.success
    assert not refresh_called


@pytest.mark.asyncio
async def test_refresh_tools_rebuilds_client():
    """Test that refresh_tools rebuilds the multi-client."""
    # Create manager with health check disabled
    manager = MCPManager(auto_health_check=False)

    # Track rebuild calls
    rebuild_called = False

    async def mock_rebuild():
        nonlocal rebuild_called
        rebuild_called = True

    # Mock clients and sessions
    mock_session1 = MagicMock()
    mock_session1.list_tools = AsyncMock(
        return_value=MagicMock(tools=[MagicMock(name="tool1"), MagicMock(name="tool2")])
    )

    mock_session2 = MagicMock()
    mock_session2.list_tools = AsyncMock(
        return_value=MagicMock(tools=[MagicMock(name="tool3")])
    )

    # Set up manager state
    manager._clients = {
        "server1": {"session": mock_session1},
        "server2": {"session": mock_session2},
    }

    manager._server_status = {
        "server1": MCPServerStatus.CONNECTED,
        "server2": MCPServerStatus.CONNECTED,
    }

    # Mock rebuild method
    manager._rebuild_multi_client = mock_rebuild

    # Call refresh
    await manager.refresh_tools()

    # Verify tools were discovered
    assert manager._server_tools["server1"] == ["tool1", "tool2"]
    assert manager._server_tools["server2"] == ["tool3"]

    # Verify multi-client was rebuilt
    assert rebuild_called


@pytest.mark.asyncio
async def test_reload_server():
    """Test reloading a specific server."""
    # Create manager with health check disabled
    manager = MCPManager(auto_health_check=False)

    # Set up initial server
    config = MCPServerConfig(
        name="test", transport="stdio", command="echo", args=["test"]
    )

    manager._servers["test"] = config
    manager._server_status["test"] = MCPServerStatus.CONNECTED

    # Track method calls
    remove_called = False
    add_called = False

    async def mock_remove(server_name):
        nonlocal remove_called
        remove_called = True
        return True

    async def mock_add(server_name, config, connect_immediately):
        nonlocal add_called
        add_called = True
        return MCPRegistrationResult(
            server_name="test",
            success=True,
            status=MCPServerStatus.CONNECTED,
            tools_count=2,
        )

    # Mock methods
    manager.remove_server = mock_remove
    manager.add_server = mock_add

    # Reload server
    result = await manager.reload_server("test")

    # Verify sequence
    assert result.success
    assert remove_called
    assert add_called


@pytest.mark.asyncio
async def test_reload_nonexistent_server():
    """Test reloading a server that doesn't exist."""
    manager = MCPManager(auto_health_check=False)

    result = await manager.reload_server("nonexistent")

    assert not result.success
    assert "not found" in result.error_message


@pytest.mark.asyncio
async def test_get_resources():
    """Test getting resources from MCP servers."""
    manager = MCPManager(auto_health_check=False)

    # Mock session with resources
    mock_session = MagicMock()
    mock_session.list_resources = AsyncMock(
        return_value=MagicMock(resources=["resource1", "resource2"])
    )

    manager._clients = {"server1": {"session": mock_session}}
    manager._server_status = {"server1": MCPServerStatus.CONNECTED}

    # Get resources
    resources = await manager.get_resources()

    assert len(resources) == 2
    mock_session.list_resources.assert_called_once()


@pytest.mark.asyncio
async def test_get_prompts():
    """Test getting prompts from MCP servers."""
    manager = MCPManager(auto_health_check=False)

    # Mock session with prompts
    mock_session = MagicMock()
    mock_session.list_prompts = AsyncMock(
        return_value=MagicMock(prompts=["prompt1", "prompt2", "prompt3"])
    )

    manager._clients = {"server1": {"session": mock_session}}
    manager._server_status = {"server1": MCPServerStatus.CONNECTED}

    # Get prompts
    prompts = await manager.get_prompts()

    assert len(prompts) == 3
    mock_session.list_prompts.assert_called_once()
