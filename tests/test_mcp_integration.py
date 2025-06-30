"""
Tests for MCP integration with haive-agents.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.discovery import MCPServerAnalyzer, MCPServerDiscovery
from haive.mcp.mixins.mcp_mixin import MCPMixin


class TestMCPMixin:
    """Test the MCP mixin functionality."""

    @pytest.fixture
    def mcp_config(self):
        """Create test MCP configuration."""
        return MCPConfig(
            enabled=True,
            servers={
                "test_server": MCPServerConfig(
                    name="test_server",
                    transport="stdio",
                    command="test",
                    args=["--test"],
                    capabilities=["test_capability"],
                )
            },
        )

    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client."""
        with patch("haive.mcp.mixins.mcp_mixin.MultiServerMCPClient") as mock:
            client = AsyncMock()
            client.get_tools = AsyncMock(return_value=[])
            mock.return_value = client
            yield mock

    def test_mixin_initialization(self, mcp_config):
        """Test MCP mixin initialization."""

        class TestAgent(MCPMixin):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        agent = TestAgent(mcp_config=mcp_config)

        assert agent.mcp_config == mcp_config
        assert not agent._mcp_initialized
        assert len(agent._mcp_tools) == 0

    @pytest.mark.asyncio
    async def test_mcp_initialization(self, mcp_config, mock_mcp_client):
        """Test MCP initialization process."""

        class TestAgent(MCPMixin):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        agent = TestAgent(mcp_config=mcp_config)

        # Mock connection test to succeed
        with patch.object(agent, "_test_server_connection", return_value=True):
            result = await agent.initialize_mcp()

        assert result is True
        assert agent._mcp_initialized
        assert "test_server" in agent._mcp_servers

    def test_get_mcp_status(self, mcp_config):
        """Test MCP status reporting."""

        class TestAgent(MCPMixin):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        agent = TestAgent(mcp_config=mcp_config)
        status = agent.get_mcp_status()

        assert status["enabled"] is True
        assert status["initialized"] is False
        assert status["tool_count"] == 0


class TestMCPAgent:
    """Test the MCP agent implementation."""

    @pytest.fixture
    def mock_engine(self):
        """Create mock engine config."""
        from haive.core.engine.aug_llm import AugLLMConfig
        from haive.core.models.llm.base import LLMConfig

        # Create a proper engine config
        engine_config = AugLLMConfig(
            llm=LLMConfig(model="gpt-4o-mini"), name="test_engine"
        )
        return engine_config

    def test_mcp_agent_creation(self, mock_engine):
        """Test creating an MCP agent."""
        agent = MCPAgent(engine=mock_engine, name="test_agent")

        assert agent.name == "test_agent"
        assert agent.mcp_config is None

    def test_create_with_mcp_servers(self, mock_engine):
        """Test convenience method for creating MCP agent."""
        agent = MCPAgent.create_with_mcp_servers(
            engine=mock_engine,
            server_configs={"test": {"transport": "stdio", "command": "test"}},
        )

        assert agent.mcp_config is not None
        assert agent.mcp_config.enabled is True
        assert "test" in agent.mcp_config.servers

    def test_get_available_capabilities(self, mock_engine):
        """Test getting available capabilities."""
        agent = MCPAgent.create_with_mcp_servers(
            engine=mock_engine,
            server_configs={
                "server1": {
                    "transport": "stdio",
                    "command": "test",
                    "capabilities": ["cap1", "cap2"],
                },
                "server2": {
                    "transport": "stdio",
                    "command": "test",
                    "capabilities": ["cap2", "cap3"],
                },
            },
        )

        # Mock initialized servers
        agent._mcp_initialized = True
        agent._mcp_servers = agent.mcp_config.servers

        capabilities = agent.get_available_capabilities()
        assert set(capabilities) == {"cap1", "cap2", "cap3"}


class TestMCPDiscovery:
    """Test MCP server discovery functionality."""

    def test_analyzer_can_analyze(self):
        """Test analyzer's ability to identify MCP configs."""
        analyzer = MCPServerAnalyzer()

        # Should recognize dict configs
        assert analyzer.can_analyze({"command": "test"})
        assert analyzer.can_analyze({"url": "http://test"})
        assert analyzer.can_analyze({"transport": "stdio"})

        # Should not recognize non-MCP objects
        assert not analyzer.can_analyze({"name": "test"})
        assert not analyzer.can_analyze("string")
        assert not analyzer.can_analyze(123)

    def test_analyzer_analyze_dict(self):
        """Test analyzing dictionary configurations."""
        analyzer = MCPServerAnalyzer()

        config_dict = {
            "name": "test",
            "command": "test-cmd",
            "args": ["--arg"],
            "capabilities": ["test"],
        }

        result = analyzer.analyze(config_dict)

        assert result is not None
        assert result.name == "test"
        assert result.command == "test-cmd"
        assert result.args == ["--arg"]
        assert result.capabilities == ["test"]

    @pytest.mark.asyncio
    async def test_discovery_filters(self):
        """Test discovery filtering."""
        config = MCPConfig(
            enabled=True, categories=["dev"], required_capabilities=["file_read"]
        )

        discovery = MCPServerDiscovery(config)

        # Mock some servers
        servers = {
            "server1": MCPServerConfig(
                name="server1",
                transport="stdio",
                command="test",
                category="dev",
                capabilities=["file_read", "file_write"],
            ),
            "server2": MCPServerConfig(
                name="server2",
                transport="stdio",
                command="test",
                category="util",
                capabilities=["time"],
            ),
            "server3": MCPServerConfig(
                name="server3",
                transport="stdio",
                command="test",
                category="dev",
                capabilities=["other"],
            ),
        }

        filtered = discovery._apply_filters(servers)

        # Only server1 should pass both filters
        assert len(filtered) == 1
        assert "server1" in filtered

    def test_get_servers_by_capability(self):
        """Test finding servers by capability."""
        discovery = MCPServerDiscovery()

        discovery.discovered_servers = {
            "server1": MCPServerConfig(
                name="server1",
                transport="stdio",
                command="test",
                capabilities=["file_read", "file_write"],
            ),
            "server2": MCPServerConfig(
                name="server2",
                transport="stdio",
                command="test",
                capabilities=["web_fetch"],
            ),
        }

        file_servers = discovery.get_servers_by_capability("file_read")
        assert len(file_servers) == 1
        assert file_servers[0].name == "server1"

        web_servers = discovery.get_servers_by_capability("web_fetch")
        assert len(web_servers) == 1
        assert web_servers[0].name == "server2"


@pytest.mark.asyncio
async def test_end_to_end_integration():
    """Test end-to-end MCP integration."""

    # Create mock engine
    engine = MagicMock()
    engine.bind_tools = MagicMock(return_value=engine)

    # Create MCP agent
    agent = MCPAgent.create_with_mcp_servers(
        engine=engine,
        server_configs={
            "test": {
                "transport": "stdio",
                "command": "echo",
                "args": ["test"],
                "capabilities": ["test"],
            }
        },
    )

    # Mock MCP client
    with patch("haive.mcp.mixins.mcp_mixin.MultiServerMCPClient") as mock_client:
        client = AsyncMock()
        client.get_tools = AsyncMock(return_value=[])
        mock_client.return_value = client

        # Mock connection test
        with patch.object(agent, "_test_server_connection", return_value=True):
            # Setup should initialize MCP
            await agent.setup()

    # Check status
    status = agent.get_mcp_status()
    assert status["enabled"] is True
    assert status["initialized"] is True
