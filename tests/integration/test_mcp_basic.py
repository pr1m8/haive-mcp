"""Basic MCP tests that don't rely on haive-agents."""

import pytest
from pydantic import BaseModel

from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.mixins.mcp_mixin import MCPMixin


class TestMCPConfig:
    """Test MCP configuration classes."""

    def test_mcp_server_config_creation(self):
        """Test creating MCPServerConfig."""
        config = MCPServerConfig(
            name="test",
            transport="stdio",
            command="echo",
            args=["test"],
            capabilities=["echo"],
            description="Test server",
        )

        assert config.name == "test"
        assert config.transport == "stdio"
        assert config.command == "echo"
        assert config.args == ["test"]
        assert config.capabilities == ["echo"]
        assert config.enabled is True

    def test_mcp_config_creation(self):
        """Test creating MCPConfig."""
        server_config = MCPServerConfig(
            name="test", transport="stdio", command="echo", args=["test"]
        )

        config = MCPConfig(
            enabled=True, servers={"test": server_config}, auto_discover=False
        )

        assert config.enabled is True
        assert "test" in config.servers
        assert config.servers["test"] == server_config
        assert config.auto_discover is False

    def test_mcp_config_validation(self):
        """Test MCPConfig validation."""
        # Valid stdio config
        config = MCPServerConfig(
            name="test", transport="stdio", command="test-cmd", args=["arg1", "arg2"]
        )
        assert config.transport == "stdio"
        assert config.command == "test-cmd"

        # Valid SSE config
        config = MCPServerConfig(
            name="test", transport="sse", url="http://localhost:8080"
        )
        assert config.transport == "sse"
        assert config.url == "http://localhost:8080"


class SimpleMCPModel(MCPMixin, BaseModel):
    """Simple model with MCP capabilities for testing."""

    name: str = "test_model"


class TestMCPMixin:
    """Test MCP mixin functionality."""

    def test_mcp_mixin_creation(self):
        """Test creating a model with MCP mixin."""
        config = MCPConfig(enabled=True, servers={})

        model = SimpleMCPModel(mcp_config=config)
        assert model.mcp_config == config
        assert not model._mcp_initialized
        assert len(model._mcp_tools) == 0

    def test_mcp_status(self):
        """Test getting MCP status."""
        config = MCPConfig(enabled=True, servers={})
        model = SimpleMCPModel(mcp_config=config)

        status = model.get_mcp_status()
        assert status["enabled"] is True
        assert status["initialized"] is False
        assert status["connected_servers"] == []
        assert status["failed_servers"] == []
        assert status["available_tools"] == []
        assert status["tool_count"] == 0

    @pytest.mark.asyncio
    async def test_mcp_initialization_disabled(self):
        """Test MCP initialization when disabled."""
        config = MCPConfig(enabled=False)
        model = SimpleMCPModel(mcp_config=config)

        result = await model.initialize_mcp()
        assert result is False
        assert not model._mcp_initialized
