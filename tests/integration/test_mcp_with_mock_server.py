"""Test MCP with a mock server that actually responds."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.models.llm.base import LLMConfig

from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.mixins.mcp_mixin import MCPMixin
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class MockMCPAgent(MCPMixin, BaseModel):
    """Mock agent with MCP capabilities for testing."""
    
    name: str = Field(default="mock_mcp_agent")
    engine: Optional[AugLLMConfig] = Field(default=None)
    tools: List[Any] = Field(default_factory=list)
    
    async def setup(self):
        """Setup the agent including MCP initialization."""
        if self.mcp_config and self.mcp_config.enabled and not self.mcp_config.lazy_init:
            success = await self.initialize_mcp()
            return success
        return True


class MockTool:
    """Mock MCP tool for testing."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def ainvoke(self, arguments: Dict[str, Any]) -> str:
        """Mock tool execution."""
        return f"Mock tool {self.name} executed with {arguments}"


@pytest.fixture
def test_engine():
    """Create a test engine configuration."""
    return AugLLMConfig(
        llm_config=LLMConfig(provider="openai", model="gpt-4o-mini", temperature=0.1),
        name="test_engine",
    )


@pytest.fixture
def mock_mcp_config():
    """Create mock MCP configuration."""
    return MCPConfig(
        enabled=True,
        servers={
            "mock_server": MCPServerConfig(
                name="mock_server",
                transport="stdio",
                command="mock_command",
                args=["mock", "args"],
                capabilities=["read_file", "write_file", "list_dir"],
                description="Mock MCP server for testing",
            )
        },
    )


class TestMCPWithMockServer:
    """Test MCP functionality with mocked server responses."""
    
    @pytest.mark.asyncio
    async def test_successful_mcp_initialization(self, test_engine, mock_mcp_config):
        """Test successful MCP initialization with mock server."""
        agent = MockMCPAgent(
            engine=test_engine,
            mcp_config=mock_mcp_config
        )
        
        # Mock the MCP dependencies and client
        with patch('haive.mcp.mixins.mcp_mixin.MCP_AVAILABLE', True), \
             patch('haive.mcp.mixins.mcp_mixin.MultiServerMCPClient') as mock_client_class:
            
            # Mock client instance
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock tools
            mock_tools = [
                MockTool("read_file", "Read a file"),
                MockTool("write_file", "Write to a file"),
                MockTool("list_dir", "List directory contents")
            ]
            mock_client.get_tools.return_value = mock_tools
            
            # Mock successful server connection test
            with patch.object(agent, '_test_server_connection', return_value=True):
                result = await agent.initialize_mcp()
                
                assert result is True
                assert agent._mcp_initialized is True
                assert len(agent._mcp_tools) == 3
                assert "read_file" in agent._mcp_tools
                assert "write_file" in agent._mcp_tools
                assert "list_dir" in agent._mcp_tools
    
    @pytest.mark.asyncio
    async def test_mcp_tool_execution(self, test_engine, mock_mcp_config):
        """Test executing MCP tools."""
        agent = MockMCPAgent(
            engine=test_engine,
            mcp_config=mock_mcp_config
        )
        
        with patch('haive.mcp.mixins.mcp_mixin.MCP_AVAILABLE', True), \
             patch('haive.mcp.mixins.mcp_mixin.MultiServerMCPClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Setup mock tools
            mock_tool = MockTool("read_file")
            mock_client.get_tools.return_value = [mock_tool]
            
            with patch.object(agent, '_test_server_connection', return_value=True):
                await agent.initialize_mcp()
                
                # Execute tool
                result = await agent.call_mcp_tool("read_file", {"path": "/test/file.txt"})
                assert "Mock tool read_file executed" in result
                assert "/test/file.txt" in result
    
    @pytest.mark.asyncio
    async def test_dynamic_server_refresh(self, test_engine):
        """Test dynamically refreshing MCP servers."""
        # Start with one server
        initial_config = MCPConfig(
            enabled=True,
            servers={
                "server1": MCPServerConfig(
                    name="server1",
                    transport="stdio",
                    command="mock1",
                    capabilities=["read"]
                )
            }
        )
        
        agent = MockMCPAgent(
            engine=test_engine,
            mcp_config=initial_config
        )
        
        with patch('haive.mcp.mixins.mcp_mixin.MCP_AVAILABLE', True), \
             patch('haive.mcp.mixins.mcp_mixin.MultiServerMCPClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Initial tools
            initial_tools = [MockTool("read_file")]
            mock_client.get_tools.return_value = initial_tools
            
            with patch.object(agent, '_test_server_connection', return_value=True):
                await agent.initialize_mcp()
                
                assert len(agent._mcp_tools) == 1
                assert "read_file" in agent._mcp_tools
                
                # Add another server dynamically
                agent.mcp_config.servers["server2"] = MCPServerConfig(
                    name="server2",
                    transport="stdio",
                    command="mock2",
                    capabilities=["write"]
                )
                
                # New tools after refresh
                new_tools = [
                    MockTool("read_file"),
                    MockTool("write_file")
                ]
                mock_client.get_tools.return_value = new_tools
                
                # Refresh
                await agent.refresh_mcp_servers()
                
                assert len(agent._mcp_tools) == 2
                assert "read_file" in agent._mcp_tools
                assert "write_file" in agent._mcp_tools
    
    @pytest.mark.asyncio
    async def test_server_failure_handling(self, test_engine):
        """Test handling of server connection failures."""
        config = MCPConfig(
            enabled=True,
            servers={
                "good_server": MCPServerConfig(
                    name="good_server",
                    transport="stdio",
                    command="good_cmd"
                ),
                "bad_server": MCPServerConfig(
                    name="bad_server",
                    transport="stdio",
                    command="bad_cmd"
                )
            }
        )
        
        agent = MockMCPAgent(
            engine=test_engine,
            mcp_config=config
        )
        
        with patch('haive.mcp.mixins.mcp_mixin.MCP_AVAILABLE', True), \
             patch('haive.mcp.mixins.mcp_mixin.MultiServerMCPClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.get_tools.return_value = [MockTool("test_tool")]
            
            # Mock connection tests - good_server succeeds, bad_server fails
            async def mock_test_connection(name, config):
                return name == "good_server"
            
            with patch.object(agent, '_test_server_connection', side_effect=mock_test_connection):
                result = await agent.initialize_mcp()
                
                # Should succeed with at least one server
                assert result is True
                assert agent._mcp_initialized is True
                
                # Check server status
                status = agent.get_mcp_status()
                assert "good_server" in status["connected_servers"]
                assert "bad_server" in status["failed_servers"]
    
    @pytest.mark.asyncio
    async def test_mcp_without_dependencies(self, test_engine, mock_mcp_config):
        """Test MCP behavior when dependencies are not available."""
        agent = MockMCPAgent(
            engine=test_engine,
            mcp_config=mock_mcp_config
        )
        
        # Mock MCP dependencies as unavailable
        with patch('haive.mcp.mixins.mcp_mixin.MCP_AVAILABLE', False):
            result = await agent.initialize_mcp()
            
            assert result is False
            assert not agent._mcp_initialized
            assert len(agent._mcp_tools) == 0
    
    @pytest.mark.asyncio
    async def test_lazy_initialization(self, test_engine, mock_mcp_config):
        """Test lazy initialization of MCP."""
        mock_mcp_config.lazy_init = True
        
        agent = MockMCPAgent(
            engine=test_engine,
            mcp_config=mock_mcp_config
        )
        
        # Setup should not initialize MCP with lazy_init=True
        await agent.setup()
        assert not agent._mcp_initialized
        
        with patch('haive.mcp.mixins.mcp_mixin.MCP_AVAILABLE', True), \
             patch('haive.mcp.mixins.mcp_mixin.MultiServerMCPClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.get_tools.return_value = [MockTool("lazy_tool")]
            
            with patch.object(agent, '_test_server_connection', return_value=True):
                # Manual initialization
                result = await agent.initialize_mcp()
                
                assert result is True
                assert agent._mcp_initialized is True
                assert "lazy_tool" in agent._mcp_tools


class TestMCPIntegrationScenarios:
    """Test real-world MCP integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_research_workflow_with_mcp(self, test_engine):
        """Test a research workflow using MCP tools."""
        config = MCPConfig(
            enabled=True,
            servers={
                "filesystem": MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="mock_fs",
                    capabilities=["read_file", "list_dir"]
                ),
                "web": MCPServerConfig(
                    name="web",
                    transport="stdio", 
                    command="mock_web",
                    capabilities=["fetch_url", "search"]
                )
            }
        )
        
        agent = MockMCPAgent(engine=test_engine, mcp_config=config, name="researcher")
        
        with patch('haive.mcp.mixins.mcp_mixin.MCP_AVAILABLE', True), \
             patch('haive.mcp.mixins.mcp_mixin.MultiServerMCPClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Research tools
            tools = [
                MockTool("read_file", "Read local files"),
                MockTool("list_dir", "List directory contents"),
                MockTool("fetch_url", "Fetch web content"),
                MockTool("search", "Search the web")
            ]
            mock_client.get_tools.return_value = tools
            
            with patch.object(agent, '_test_server_connection', return_value=True):
                await agent.setup()
                
                # Simulate research workflow
                status = agent.get_mcp_status()
                assert status["tool_count"] == 4
                assert len(status["connected_servers"]) == 2
                
                # Test individual tool usage
                file_result = await agent.call_mcp_tool("read_file", {"path": "research.txt"})
                assert "research.txt" in file_result
                
                web_result = await agent.call_mcp_tool("fetch_url", {"url": "https://example.com"})
                assert "https://example.com" in web_result
    
    @pytest.mark.asyncio 
    async def test_collaborative_agents_workflow(self, test_engine):
        """Test multiple agents collaborating with shared MCP resources."""
        shared_config = MCPConfig(
            enabled=True,
            servers={
                "shared_db": MCPServerConfig(
                    name="shared_db",
                    transport="stdio",
                    command="mock_db",
                    capabilities=["query", "insert", "update"]
                )
            }
        )
        
        # Create multiple agents
        reader_agent = MockMCPAgent(
            engine=test_engine, 
            mcp_config=shared_config, 
            name="reader"
        )
        writer_agent = MockMCPAgent(
            engine=test_engine, 
            mcp_config=shared_config, 
            name="writer"
        )
        
        with patch('haive.mcp.mixins.mcp_mixin.MCP_AVAILABLE', True), \
             patch('haive.mcp.mixins.mcp_mixin.MultiServerMCPClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            db_tools = [
                MockTool("query", "Query database"),
                MockTool("insert", "Insert data"),
                MockTool("update", "Update records")
            ]
            mock_client.get_tools.return_value = db_tools
            
            with patch.object(reader_agent, '_test_server_connection', return_value=True), \
                 patch.object(writer_agent, '_test_server_connection', return_value=True):
                
                # Setup both agents
                await reader_agent.setup()
                await writer_agent.setup()
                
                # Both should have access to the same tools
                assert len(reader_agent._mcp_tools) == 3
                assert len(writer_agent._mcp_tools) == 3
                
                # Test collaborative workflow
                read_result = await reader_agent.call_mcp_tool("query", {"sql": "SELECT * FROM data"})
                write_result = await writer_agent.call_mcp_tool("insert", {"data": {"key": "value"}})
                
                assert "SELECT * FROM data" in read_result
                assert "key" in write_result