"""Real integration tests for MCP without mocks."""

import pytest

from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.models.llm.base import LLMConfig
from haive.mcp.agents import MCPAgent
from haive.mcp.agents.transferable_mcp_agent import TransferableMCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.discovery import MCPServerDiscovery


@pytest.fixture
def real_engine():
    """Create a real engine configuration."""
    return AugLLMConfig(
        llm_config=LLMConfig(provider="openai", model="gpt-4o-mini", temperature=0.1),
        name="test_engine",
    )


@pytest.fixture
def test_mcp_config():
    """Create test MCP configuration with a simple server."""
    return MCPConfig(
        enabled=True,
        servers={
            "echo": MCPServerConfig(
                name="echo",
                transport="stdio",
                command="echo",
                args=["MCP Echo Server"],
                capabilities=["echo"],
                description="Simple echo server for testing",
            )
        },
    )


class TestRealMCPIntegration:
    """Test real MCP integration without mocks."""

    def test_mcp_agent_creation(self, real_engine, test_mcp_config):
        """Test creating an MCP agent with real configuration."""
        agent = MCPAgent(
            engine=real_engine, mcp_config=test_mcp_config, name="test_mcp_agent"
        )

        assert agent.name == "test_mcp_agent"
        assert agent.mcp_config == test_mcp_config
        assert not agent._mcp_initialized

    def test_mcp_agent_convenience_method(self, real_engine):
        """Test creating MCP agent with convenience method."""
        agent = MCPAgent.create_with_mcp_servers(
            engine=real_engine,
            server_configs={
                "echo": {"transport": "stdio", "command": "echo", "args": ["test"]}
            },
            name="convenience_agent",
        )

        assert agent.name == "convenience_agent"
        assert agent.mcp_config.enabled
        assert "echo" in agent.mcp_config.servers

    @pytest.mark.asyncio
    async def test_mcp_initialization_with_echo(self, real_engine, test_mcp_config):
        """Test MCP initialization with echo server."""
        agent = MCPAgent(
            engine=real_engine, mcp_config=test_mcp_config, name="echo_test_agent"
        )

        # Echo command should fail to provide MCP tools
        # This tests graceful failure handling
        result = await agent.initialize_mcp()

        # Should handle the failure gracefully
        assert result is False or len(agent._mcp_tools) == 0

    def test_transferable_agent_creation(self, real_engine, test_mcp_config):
        """Test creating transferable MCP agents."""
        agents = TransferableMCPAgent.create_collaborative_agents(
            engine=real_engine,
            mcp_config=test_mcp_config,
            num_agents=3,
            shared_client=True,
        )

        assert len(agents) == 3
        assert all(agent.share_client for agent in agents)
        assert all(
            agent.client_pool_key == agents[0].client_pool_key for agent in agents
        )

    @pytest.mark.asyncio
    async def test_tool_transfer(self, real_engine):
        """Test tool transfer between agents."""
        # Create two agents
        config = MCPConfig(enabled=True, servers={})  # No servers for this test

        agent1 = TransferableMCPAgent(
            engine=real_engine, mcp_config=config, name="agent1"
        )

        agent2 = TransferableMCPAgent(
            engine=real_engine, mcp_config=config, name="agent2"
        )

        # Initialize agents
        await agent1.initialize_mcp()
        await agent2.initialize_mcp()

        # Even without servers, transfer mechanism should work
        status1 = agent1.get_transfer_status()
        assert status1["shared_client"] is True
        assert status1["transferred_tools"] == []


class TestMCPDiscovery:
    """Test MCP discovery functionality."""

    def test_discovery_initialization(self):
        """Test discovery system initialization."""
        discovery = MCPServerDiscovery()

        assert discovery.config is not None
        assert discovery.analyzer is not None
        assert len(discovery.discovered_servers) == 0

    @pytest.mark.asyncio
    async def test_discovery_with_filters(self):
        """Test discovery with capability filters."""
        config = MCPConfig(enabled=True, required_capabilities=["file_operations"])

        discovery = MCPServerDiscovery(config)

        # Add some test servers
        discovery.discovered_servers = {
            "fs": MCPServerConfig(
                name="fs",
                transport="stdio",
                command="test",
                capabilities=["file_operations", "directory_list"],
            ),
            "web": MCPServerConfig(
                name="web",
                transport="stdio",
                command="test",
                capabilities=["web_fetch"],
            ),
        }

        # Get servers by capability
        file_servers = discovery.get_servers_by_capability("file_operations")
        assert len(file_servers) == 1
        assert file_servers[0].name == "fs"

        web_servers = discovery.get_servers_by_capability("web_fetch")
        assert len(web_servers) == 1
        assert web_servers[0].name == "web"

    def test_discovery_report(self):
        """Test discovery report generation."""
        discovery = MCPServerDiscovery()

        # Add test servers
        discovery.discovered_servers = {
            "server1": MCPServerConfig(
                name="server1",
                transport="stdio",
                command="test",
                category="filesystem",
                capabilities=["read", "write"],
            ),
            "server2": MCPServerConfig(
                name="server2",
                transport="sse",
                command="test",
                category="web",
                capabilities=["fetch", "post"],
            ),
        }

        report = discovery.get_discovery_report()

        assert report["total_servers"] == 2
        assert report["categories"]["filesystem"] == 1
        assert report["categories"]["web"] == 1
        assert "read" in report["unique_capabilities"]
        assert "fetch" in report["unique_capabilities"]


class TestMCPConfigValidation:
    """Test MCP configuration validation."""

    def test_server_config_validation(self):
        """Test MCPServerConfig validation."""
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

    def test_mcp_config_validation(self):
        """Test MCPConfig validation."""
        config = MCPConfig(
            enabled=True,
            servers={
                "test": MCPServerConfig(name="test", transport="stdio", command="test")
            },
            categories=["dev", "util"],
            required_capabilities=["file_ops"],
        )

        assert config.enabled
        assert len(config.servers) == 1
        assert config.categories == ["dev", "util"]
        assert config.required_capabilities == ["file_ops"]
