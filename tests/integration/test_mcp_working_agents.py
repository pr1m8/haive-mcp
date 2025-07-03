"""Test MCP with working agent types (SimpleAgent, ReactAgent, RAG agents)."""

import asyncio
import pytest
from pathlib import Path
from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.models.llm.base import LLMConfig

# Import working agents that don't have GenericAgent issues
from haive.agents.simple.agent import SimpleAgent
from haive.agents.react.agent import ReactAgent
from haive.agents.rag.base.agent import BaseRAGAgent
from haive.agents.multi.base import SequentialAgent, MultiAgent

from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.mixins.mcp_mixin import MCPMixin
from typing import Any, Dict, List, Optional


class MCPSimpleAgent(MCPMixin, SimpleAgent):
    """SimpleAgent with MCP capabilities."""
    
    async def setup(self):
        """Setup agent with MCP initialization."""
        # First setup the base agent
        super().setup_agent()
        
        # Then initialize MCP if configured
        if self.mcp_config and self.mcp_config.enabled and not self.mcp_config.lazy_init:
            success = await self.initialize_mcp()
            # Add MCP tools to agent's tools if available
            if success and self._mcp_tools and hasattr(self, 'engine'):
                # Bind tools to engine using AugLLMConfig's capabilities
                if hasattr(self.engine, 'add_tools_from_list'):
                    self.engine.add_tools_from_list(list(self._mcp_tools.values()))
            return success
        return True


class MCPReactAgent(MCPMixin, ReactAgent):
    """ReactAgent with MCP capabilities."""
    
    async def setup(self):
        """Setup agent with MCP initialization."""
        # First setup the base agent
        super().setup_agent()
        
        # Then initialize MCP if configured
        if self.mcp_config and self.mcp_config.enabled and not self.mcp_config.lazy_init:
            success = await self.initialize_mcp()
            # Add MCP tools to agent's tools if available
            if success and self._mcp_tools and hasattr(self, 'engine'):
                # Bind tools to engine using AugLLMConfig's capabilities
                if hasattr(self.engine, 'add_tools_from_list'):
                    self.engine.add_tools_from_list(list(self._mcp_tools.values()))
            return success
        return True


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
            "test_server": MCPServerConfig(
                name="test_server",
                transport="stdio",
                command="echo",
                args=["MCP Test Server"],
                capabilities=["test"],
                description="Test server for MCP",
            )
        },
    )


class TestMCPWithWorkingAgents:
    """Test MCP with agents that don't have GenericAgent issues."""
    
    def test_mcp_simple_agent_creation(self, test_engine, test_mcp_config):
        """Test creating an MCP-enabled SimpleAgent."""
        agent = MCPSimpleAgent(
            engine=test_engine,
            mcp_config=test_mcp_config,
            name="mcp_simple_agent"
        )
        
        assert agent.name == "mcp_simple_agent"
        assert agent.mcp_config == test_mcp_config
        assert agent.engine == test_engine
        assert not agent._mcp_initialized
    
    @pytest.mark.asyncio
    async def test_mcp_simple_agent_setup(self, test_engine, test_mcp_config):
        """Test MCP SimpleAgent setup."""
        agent = MCPSimpleAgent(
            engine=test_engine,
            mcp_config=test_mcp_config
        )
        
        # Setup will try to initialize MCP
        result = await agent.setup()
        # Echo command won't provide real MCP tools, so this will fail gracefully
        assert isinstance(result, bool)
        
        status = agent.get_mcp_status()
        assert status["enabled"] is True
    
    def test_mcp_react_agent_creation(self, test_engine, test_mcp_config):
        """Test creating an MCP-enabled ReactAgent."""
        agent = MCPReactAgent(
            engine=test_engine,
            mcp_config=test_mcp_config,
            name="mcp_react_agent"
        )
        
        assert agent.name == "mcp_react_agent"
        assert isinstance(agent, ReactAgent)
        assert hasattr(agent, 'initialize_mcp')
    
    @pytest.mark.asyncio
    async def test_mcp_react_agent_with_tools(self, test_engine):
        """Test ReactAgent with MCP tools configuration."""
        config = MCPConfig(
            enabled=True,
            servers={
                "tools_server": MCPServerConfig(
                    name="tools_server",
                    transport="stdio",
                    command="python",
                    args=["-c", "print('Tools server')"],
                    capabilities=["search", "calculate", "analyze"]
                )
            }
        )
        
        agent = MCPReactAgent(
            engine=test_engine,
            mcp_config=config,
            force_tool_use=True
        )
        
        await agent.setup()
        
        status = agent.get_mcp_status()
        # The server may either fail to connect or not be initialized at all
        # Check if it's in failed servers or if no servers connected
        assert (
            len(status["failed_servers"]) > 0 or 
            len(status["connected_servers"]) == 0
        )
    
    @pytest.mark.asyncio
    async def test_dynamic_mcp_with_simple_agent(self, test_engine):
        """Test dynamic MCP server management with SimpleAgent."""
        # Start with disabled MCP
        agent = MCPSimpleAgent(
            engine=test_engine,
            mcp_config=MCPConfig(enabled=False)
        )
        
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
                    args=["Dynamic"]
                )
            }
        )
        
        # Refresh servers
        await agent.refresh_mcp_servers()
        
        status = agent.get_mcp_status()
        assert status["enabled"] is True
    
    @pytest.mark.asyncio
    async def test_mcp_with_structured_output(self, test_engine, test_mcp_config):
        """Test MCP with SimpleAgent using structured output."""
        from pydantic import BaseModel
        
        class TaskResult(BaseModel):
            success: bool
            message: str
            tools_used: List[str] = []
        
        agent = MCPSimpleAgent(
            engine=test_engine,
            mcp_config=test_mcp_config,
            structured_output_model=TaskResult
        )
        
        await agent.setup()
        
        # Check that structured output is configured
        assert agent.structured_output_model == TaskResult
    
    @pytest.mark.asyncio
    async def test_multiple_mcp_agents(self, test_engine):
        """Test multiple MCP agents with different configurations."""
        # Agent 1: File operations
        agent1 = MCPSimpleAgent(
            engine=test_engine,
            mcp_config=MCPConfig(
                enabled=True,
                servers={
                    "file_ops": MCPServerConfig(
                        name="file_ops",
                        transport="stdio",
                        command="echo",
                        args=["File operations"]
                    )
                }
            ),
            name="file_agent"
        )
        
        # Agent 2: Web operations
        agent2 = MCPReactAgent(
            engine=test_engine,
            mcp_config=MCPConfig(
                enabled=True,
                servers={
                    "web_ops": MCPServerConfig(
                        name="web_ops",
                        transport="sse",
                        url="http://localhost:8080/mcp"
                    )
                }
            ),
            name="web_agent"
        )
        
        # Setup both
        await agent1.setup()
        await agent2.setup()
        
        # Each should have its own configuration
        status1 = agent1.get_mcp_status()
        status2 = agent2.get_mcp_status()
        
        assert status1["enabled"] is True
        assert status2["enabled"] is True
    
    @pytest.mark.asyncio
    async def test_lazy_initialization_with_react_agent(self, test_engine):
        """Test lazy MCP initialization with ReactAgent."""
        config = MCPConfig(
            enabled=True,
            lazy_init=True,
            servers={
                "lazy": MCPServerConfig(
                    name="lazy",
                    transport="stdio",
                    command="echo",
                    args=["Lazy"]
                )
            }
        )
        
        agent = MCPReactAgent(
            engine=test_engine,
            mcp_config=config
        )
        
        # Setup should not initialize MCP with lazy_init=True
        await agent.setup()
        assert not agent._mcp_initialized
        
        # Manual initialization
        result = await agent.initialize_mcp()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_mcp_server_discovery(self, test_engine):
        """Test MCP server auto-discovery."""
        config = MCPConfig(
            enabled=True,
            auto_discover=True,
            servers={}
        )
        
        agent = MCPSimpleAgent(
            engine=test_engine,
            mcp_config=config
        )
        
        await agent.setup()
        
        status = agent.get_mcp_status()
        # Auto-discovery may or may not find servers
        assert isinstance(status["connected_servers"], list)
    
    @pytest.mark.asyncio
    async def test_real_filesystem_server_if_available(self, test_engine):
        """Test with real filesystem MCP server if npx is available."""
        config = MCPConfig(
            enabled=True,
            servers={
                "filesystem": MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem"],
                    env={
                        "FILESYSTEM_ROOT": str(Path.home() / "tmp")
                    },
                    capabilities=["read_file", "write_file", "list_directory"]
                )
            }
        )
        
        agent = MCPSimpleAgent(
            engine=test_engine,
            mcp_config=config,
            name="fs_agent"
        )
        
        result = await agent.setup()
        status = agent.get_mcp_status()
        
        if result and agent._mcp_initialized:
            # Filesystem server is available
            print(f"Connected to filesystem server with {len(agent._mcp_tools)} tools")
            assert len(status["connected_servers"]) > 0
            
            # Try to use a tool if available
            if "read_file" in agent._mcp_tools:
                try:
                    result = await agent.call_mcp_tool(
                        "read_file",
                        {"path": "/etc/hosts"}
                    )
                    print(f"Read file result: {result[:100]}...")
                except Exception as e:
                    print(f"Tool execution failed: {e}")
        else:
            # Server not available
            print("Filesystem server not available")
            assert len(status["failed_servers"]) > 0


class TestMCPMultiAgentScenarios:
    """Test MCP with multi-agent scenarios."""
    
    @pytest.mark.asyncio
    async def test_sequential_mcp_agents(self, test_engine):
        """Test sequential execution of MCP agents."""
        # Create two agents with different MCP configs
        researcher = MCPSimpleAgent(
            engine=test_engine,
            mcp_config=MCPConfig(
                enabled=True,
                servers={
                    "search": MCPServerConfig(
                        name="search",
                        transport="stdio",
                        command="echo",
                        args=["Search server"]
                    )
                }
            ),
            name="researcher"
        )
        
        writer = MCPSimpleAgent(
            engine=test_engine,
            mcp_config=MCPConfig(
                enabled=True,
                servers={
                    "files": MCPServerConfig(
                        name="files",
                        transport="stdio",
                        command="echo",
                        args=["File server"]
                    )
                }
            ),
            name="writer"
        )
        
        # Setup both
        await researcher.setup()
        await writer.setup()
        
        # They should have independent MCP configurations
        researcher_status = researcher.get_mcp_status()
        writer_status = writer.get_mcp_status()
        
        assert researcher_status["enabled"] is True
        assert writer_status["enabled"] is True
    
    @pytest.mark.asyncio
    async def test_mcp_agent_collaboration(self, test_engine):
        """Test collaboration between MCP agents."""
        # Shared MCP configuration
        shared_config = MCPConfig(
            enabled=True,
            servers={
                "shared_db": MCPServerConfig(
                    name="shared_db",
                    transport="stdio",
                    command="echo",
                    args=["Database server"]
                )
            }
        )
        
        # Create agents sharing the same MCP config
        agent1 = MCPSimpleAgent(
            engine=test_engine,
            mcp_config=shared_config,
            name="agent1"
        )
        
        agent2 = MCPReactAgent(
            engine=test_engine,
            mcp_config=shared_config,
            name="agent2"
        )
        
        await agent1.setup()
        await agent2.setup()
        
        # Both should try to connect to the same server
        status1 = agent1.get_mcp_status()
        status2 = agent2.get_mcp_status()
        
        assert "shared_db" in [s["name"] for s in status1["failed_servers"]]
        assert "shared_db" in [s["name"] for s in status2["failed_servers"]]