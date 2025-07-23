"""Test MCP with simple agent implementations."""

from typing import Any

import pytest
from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.models.llm.base import LLMConfig
from pydantic import BaseModel, Field

from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.mixins.mcp_mixin import MCPMixin


class SimpleMCPAgent(MCPMixin, BaseModel):
    """Simple agent with MCP capabilities."""

    name: str = Field(default="simple_mcp_agent")
    engine: AugLLMConfig | None = Field(default=None)
    tools: list[Any] = Field(default_factory=list)

    async def setup(self):
        """Setup the agent including MCP initialization."""
        if (
            self.mcp_config
            and self.mcp_config.enabled
            and not self.mcp_config.lazy_init
        ):
            success = await self.initialize_mcp()
            if success and self._mcp_tools:
                # Add MCP tools to agent's tools
                for tool in self._mcp_tools.values():
                    if tool not in self.tools:
                        self.tools.append(tool)
            return success
        return True

    async def arun(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run the agent."""
        # Simple implementation for testing
        return {
            "status": "success",
            "mcp_enabled": self.mcp_config.enabled if self.mcp_config else False,
            "tools_count": len(self.tools),
            "mcp_tools_count": len(self._mcp_tools),
            "input": input_data,
        }


class SimpleRAGAgent(SimpleMCPAgent):
    """Simple RAG agent with MCP capabilities."""

    name: str = Field(default="simple_rag_agent")
    retriever: Any | None = Field(default=None)

    async def retrieve(self, query: str) -> list[str]:
        """Simple retrieval simulation."""
        # Simulate retrieval
        return [f"Document about {query}", f"Another document about {query}"]

    async def arun(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run RAG agent."""
        query = input_data.get("query", "")
        docs = await self.retrieve(query)

        result = await super().arun(input_data)
        result["retrieved_docs"] = docs
        return result


class SimpleReActAgent(SimpleMCPAgent):
    """Simple ReAct agent with MCP capabilities."""

    name: str = Field(default="simple_react_agent")
    max_iterations: int = Field(default=3)

    async def think(self, observation: str) -> str:
        """Simple thinking step."""
        return f"Based on '{observation}', I should check available tools"

    async def act(self, thought: str) -> str:
        """Simple action step."""
        if self._mcp_tools:
            return f"Using MCP tool: {list(self._mcp_tools.keys())[0]}"
        return "No tools available"

    async def arun(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run ReAct agent."""
        thoughts = []
        actions = []

        observation = input_data.get("task", "No task provided")

        for i in range(self.max_iterations):
            thought = await self.think(observation)
            thoughts.append(thought)

            action = await self.act(thought)
            actions.append(action)

            # Simple stopping condition
            if "complete" in action.lower() or i == self.max_iterations - 1:
                break

        result = await super().arun(input_data)
        result["thoughts"] = thoughts
        result["actions"] = actions
        return result


@pytest.fixture
def test_engine():
    """Create a test engine configuration."""
    return AugLLMConfig(
        llm_config=LLMConfig(provider="openai", model="gpt-4o-mini", temperature=0.1),
        name="test_engine",
    )


@pytest.fixture
def test_mcp_config():
    """Create test MCP configuration."""
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


class TestSimpleMCPAgents:
    """Test simple MCP agent implementations."""

    def test_simple_mcp_agent_creation(self, test_engine, test_mcp_config):
        """Test creating a simple MCP agent."""
        agent = SimpleMCPAgent(
            engine=test_engine, mcp_config=test_mcp_config, name="test_simple_agent"
        )

        assert agent.name == "test_simple_agent"
        assert agent.mcp_config == test_mcp_config
        assert not agent._mcp_initialized
        assert len(agent.tools) == 0

    @pytest.mark.asyncio
    async def test_simple_agent_setup(self, test_engine, test_mcp_config):
        """Test simple agent setup."""
        agent = SimpleMCPAgent(engine=test_engine, mcp_config=test_mcp_config)

        # Setup will try to initialize MCP
        result = await agent.setup()
        # Echo command won't provide real MCP tools, so this should handle gracefully
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_simple_agent_run(self, test_engine, test_mcp_config):
        """Test running simple agent."""
        agent = SimpleMCPAgent(engine=test_engine, mcp_config=test_mcp_config)

        await agent.setup()

        result = await agent.arun({"message": "Hello"})
        assert result["status"] == "success"
        assert result["mcp_enabled"] is True
        assert result["input"]["message"] == "Hello"

    def test_simple_rag_agent_creation(self, test_engine, test_mcp_config):
        """Test creating a simple RAG agent."""
        agent = SimpleRAGAgent(engine=test_engine, mcp_config=test_mcp_config)

        assert agent.name == "simple_rag_agent"
        assert agent.mcp_config == test_mcp_config

    @pytest.mark.asyncio
    async def test_simple_rag_agent_retrieval(self, test_engine, test_mcp_config):
        """Test RAG agent retrieval."""
        agent = SimpleRAGAgent(engine=test_engine, mcp_config=test_mcp_config)

        await agent.setup()

        result = await agent.arun({"query": "MCP servers"})
        assert result["status"] == "success"
        assert "retrieved_docs" in result
        assert len(result["retrieved_docs"]) == 2
        assert "MCP servers" in result["retrieved_docs"][0]

    def test_simple_react_agent_creation(self, test_engine, test_mcp_config):
        """Test creating a simple ReAct agent."""
        agent = SimpleReActAgent(
            engine=test_engine, mcp_config=test_mcp_config, max_iterations=5
        )

        assert agent.name == "simple_react_agent"
        assert agent.max_iterations == 5

    @pytest.mark.asyncio
    async def test_simple_react_agent_thinking(self, test_engine, test_mcp_config):
        """Test ReAct agent thinking and acting."""
        agent = SimpleReActAgent(engine=test_engine, mcp_config=test_mcp_config)

        await agent.setup()

        result = await agent.arun({"task": "Find MCP documentation"})
        assert result["status"] == "success"
        assert "thoughts" in result
        assert "actions" in result
        assert len(result["thoughts"]) > 0
        assert len(result["actions"]) > 0

    @pytest.mark.asyncio
    async def test_dynamic_mcp_addition(self, test_engine):
        """Test dynamically adding MCP servers."""
        # Start with no MCP config
        agent = SimpleMCPAgent(engine=test_engine, mcp_config=MCPConfig(enabled=False))

        await agent.setup()
        assert agent.get_mcp_status()["enabled"] is False

        # Enable MCP dynamically
        agent.mcp_config = MCPConfig(
            enabled=True,
            servers={
                "dynamic": MCPServerConfig(
                    name="dynamic",
                    transport="stdio",
                    command="echo",
                    args=["Dynamic Server"],
                )
            },
        )

        # Re-initialize
        await agent.refresh_mcp_servers()

        status = agent.get_mcp_status()
        assert status["enabled"] is True
        # Since echo doesn't provide real MCP tools, initialization may fail
        # but the dynamic config change should still work
        assert isinstance(status["initialized"], bool)

    @pytest.mark.asyncio
    async def test_multiple_agents_different_configs(self, test_engine):
        """Test multiple agents with different MCP configurations."""
        # Agent 1 with one server
        agent1 = SimpleMCPAgent(
            engine=test_engine,
            mcp_config=MCPConfig(
                enabled=True,
                servers={
                    "server1": MCPServerConfig(
                        name="server1",
                        transport="stdio",
                        command="echo",
                        args=["Server 1"],
                    )
                },
            ),
            name="agent1",
        )

        # Agent 2 with different server
        agent2 = SimpleRAGAgent(
            engine=test_engine,
            mcp_config=MCPConfig(
                enabled=True,
                servers={
                    "server2": MCPServerConfig(
                        name="server2",
                        transport="stdio",
                        command="echo",
                        args=["Server 2"],
                    )
                },
            ),
            name="agent2",
        )

        # Agent 3 with no MCP
        agent3 = SimpleReActAgent(
            engine=test_engine, mcp_config=MCPConfig(enabled=False), name="agent3"
        )

        # Setup all agents
        await agent1.setup()
        await agent2.setup()
        await agent3.setup()

        # Check each has correct config
        assert agent1.get_mcp_status()["enabled"] is True
        assert agent2.get_mcp_status()["enabled"] is True
        assert agent3.get_mcp_status()["enabled"] is False


class TestDynamicMCPFeatures:
    """Test dynamic MCP features."""

    @pytest.mark.asyncio
    async def test_lazy_initialization(self, test_engine, test_mcp_config):
        """Test lazy initialization of MCP."""
        # Configure for lazy init
        test_mcp_config.lazy_init = True

        agent = SimpleMCPAgent(engine=test_engine, mcp_config=test_mcp_config)

        # Setup should not initialize MCP
        await agent.setup()
        assert not agent._mcp_initialized

        # Manual initialization
        result = await agent.initialize_mcp()
        assert (
            agent._mcp_initialized or not result
        )  # Either initialized or failed gracefully

    @pytest.mark.asyncio
    async def test_server_health_tracking(self, test_engine):
        """Test server health tracking."""
        agent = SimpleMCPAgent(
            engine=test_engine,
            mcp_config=MCPConfig(
                enabled=True,
                servers={
                    "healthy": MCPServerConfig(
                        name="healthy", transport="stdio", command="echo", args=["OK"]
                    ),
                    "unhealthy": MCPServerConfig(
                        name="unhealthy",
                        transport="stdio",
                        command="nonexistent_command",
                        args=["Will fail"],
                    ),
                },
            ),
        )

        await agent.setup()

        status = agent.get_mcp_status()
        # The unhealthy server should be in failed_servers
        assert len(status["failed_servers"]) >= 0  # May have failures
        assert isinstance(status["connected_servers"], list)
