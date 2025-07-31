"""Unit tests for MCP configuration models.

This module tests the configuration models and validation logic
for MCP server configurations.

Classes:
    TestMCPServerConfig: Tests for MCPServerConfig model
    TestMCPConfig: Tests for MCPConfig model
"""

from pydantic import ValidationError
import pytest

from haive.mcp.config import MCPConfig, MCPServerConfig


class TestMCPServerConfig:
    """Test suite for MCPServerConfig model.

    Tests cover:
    - Valid configuration creation
    - Validation of required fields
    - Transport type validation
    - Environment variable handling
    """

    def test_valid_stdio_config(self):
        """Test creating valid stdio transport config.

        Verifies that a stdio server config can be created
        with all required fields.
        """
        config = MCPServerConfig(
            name="test-server",
            transport="stdio",
            command="python",
            args=["server.py"],
            capabilities=["tool1", "tool2"],
        )

        assert config.name == "test-server"
        assert config.transport == "stdio"
        assert config.command == "python"
        assert len(config.args) == 1
        assert "tool1" in config.capabilities

    def test_valid_http_config(self):
        """Test creating valid HTTP transport config.

        Verifies that an HTTP server config can be created
        with URL instead of command.
        """
        config = MCPServerConfig(
            name="http-server", transport="sse", url="http://localhost:8000/mcp"
        )

        assert config.name == "http-server"
        assert config.transport == "sse"
        assert config.url == "http://localhost:8000/mcp"
        assert config.command is None

    def test_invalid_transport(self):
        """Test invalid transport type raises error."""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                name="test",
                transport="invalid",  # Invalid transport
                command="test",
            )

    def test_stdio_without_command(self):
        """Test stdio transport can be created without command."""
        # Command is optional - can be provided later
        config = MCPServerConfig(name="test", transport="stdio")
        assert config.command is None
        assert config.transport == "stdio"

    def test_environment_variables(self):
        """Test environment variable configuration."""
        config = MCPServerConfig(
            name="test",
            transport="stdio",
            command="test",
            env={"API_KEY": "secret", "DEBUG": "true"},
        )

        assert config.env["API_KEY"] == "secret"
        assert config.env["DEBUG"] == "true"


class TestMCPConfig:
    """Test suite for MCPConfig model.

    Tests cover:
    - Configuration with multiple servers
    - Auto-discovery settings
    - Category filtering
    - Required capabilities
    """

    def test_empty_config(self):
        """Test creating empty MCP config."""
        config = MCPConfig()

        assert config.enabled is False  # Default is False
        assert config.servers == {}
        assert config.auto_discover is True  # Default is True

    def test_config_with_servers(self):
        """Test config with multiple servers."""
        server1 = MCPServerConfig(name="server1", transport="stdio", command="cmd1")
        server2 = MCPServerConfig(
            name="server2", transport="sse", url="http://localhost:8000"
        )

        config = MCPConfig(servers={"server1": server1, "server2": server2})

        assert len(config.servers) == 2
        assert "server1" in config.servers
        assert config.servers["server2"].transport == "sse"

    def test_discovery_settings(self):
        """Test auto-discovery configuration."""
        config = MCPConfig(
            auto_discover=True,
            discovery_paths=["~/.mcp", "/opt/mcp"],
            categories=["dev", "productivity"],
            required_capabilities=["file_ops"],
        )

        assert config.auto_discover is True
        assert len(config.discovery_paths) == 2
        assert "dev" in config.categories
        assert "file_ops" in config.required_capabilities

    def test_disabled_config(self):
        """Test disabled MCP configuration."""
        config = MCPConfig(enabled=False)

        assert config.enabled is False
        # Even if disabled, other fields should work
        config.servers["test"] = MCPServerConfig(
            name="test", transport="stdio", command="test"
        )
        assert len(config.servers) == 1

    def test_lazy_init_setting(self):
        """Test lazy initialization setting."""
        config = MCPConfig(lazy_init=True)

        assert config.lazy_init is True

    def test_config_serialization(self):
        """Test config can be serialized to dict."""
        config = MCPConfig(
            servers={
                "test": MCPServerConfig(name="test", transport="stdio", command="test")
            }
        )

        data = config.model_dump()
        assert isinstance(data, dict)
        assert "servers" in data
        assert "test" in data["servers"]
