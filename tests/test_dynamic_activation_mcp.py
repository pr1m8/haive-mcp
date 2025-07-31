"""Tests for Dynamic Activation Pattern - MCP Components.

This module tests the MCP components of the Dynamic Activation Pattern
using real components (no mocks) following the Haive testing philosophy.

Based on:
- @project_docs/active/patterns/dynamic_activation_pattern.md
- @project_docs/active/standards/testing/philosophy.md (no mocks)
- MCP protocol specification
"""

from typing import Any

import pytest
from haive.core.registry import RegistryItem
from haive.core.schema.prebuilt.meta_state import MetaStateSchema

from haive.mcp.dynamic_activation_mcp import (
    DynamicActivationMCPServer,
    DynamicMCPRegistry,
    DynamicMCPState,
    MCPTool,
)


class TestMCPTool:
    """Test suite for MCPTool with real components."""

    def test_mcp_tool_creation(self):
        """Test creating MCPTool with proper validation."""

        def test_handler(input_data: dict[str, Any]) -> str:
            """Test handler function."""
            return f"Handler executed with: {input_data}"

        tool = MCPTool(
            name="test_calculator",
            description="A test calculator tool",
            input_schema={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
            handler=test_handler,
            metadata={"category": "math", "version": "1.0"},
        )

        assert tool.name == "test_calculator"
        assert tool.description == "A test calculator tool"
        assert tool.input_schema["type"] == "object"
        assert tool.handler == test_handler
        assert tool.metadata["category"] == "math"
        assert tool.metadata["version"] == "1.0"

    def test_mcp_tool_with_complex_schema(self):
        """Test MCPTool with complex input schema."""

        def complex_handler(input_data: dict[str, Any]) -> dict[str, Any]:
            """Complex handler function."""
            return {"result": input_data, "status": "success"}

        complex_schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "options": {
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "default": 10},
                        "include_metadata": {"type": "boolean", "default": True},
                    },
                },
            },
            "required": ["query"],
        }

        tool = MCPTool(
            name="search_tool",
            description="Search tool with complex options",
            input_schema=complex_schema,
            handler=complex_handler,
        )

        assert tool.name == "search_tool"
        assert (
            tool.input_schema["properties"]["options"]["properties"]["max_results"][
                "default"
            ]
            == 10
        )
        assert tool.handler == complex_handler


class TestDynamicMCPRegistry:
    """Test suite for DynamicMCPRegistry with real components."""

    def test_mcp_registry_creation(self):
        """Test creating DynamicMCPRegistry."""
        registry = DynamicMCPRegistry()

        assert registry.items == {}
        assert registry.active_items == set()
        assert registry.max_active is None

    def test_mcp_tool_registration(self):
        """Test registering MCP tools in registry."""
        registry = DynamicMCPRegistry()

        # Create test MCP tool
        def calculator_handler(input_data: dict[str, Any]) -> float:
            """Calculator handler."""
            return eval(input_data["expression"])

        tool = MCPTool(
            name="calculator",
            description="Mathematical calculator",
            input_schema={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
            handler=calculator_handler,
        )

        # Create registry item
        item = RegistryItem(
            id="calc_001",
            name="Calculator",
            description="Mathematical calculator tool",
            component=tool,
        )

        # Register item
        registry.register(item)

        # Verify registration
        assert "calc_001" in registry.items
        assert registry.items["calc_001"].component.name == "calculator"
        assert isinstance(registry.items["calc_001"].component, MCPTool)

    @pytest.mark.asyncio
    async def test_mcp_tool_activation(self):
        """Test activating MCP tools."""
        registry = DynamicMCPRegistry()

        # Create and register MCP tool
        def search_handler(input_data: dict[str, Any]) -> str:
            """Search handler."""
            return f"Search results for: {input_data['query']}"

        tool = MCPTool(
            name="search",
            description="Web search tool",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            handler=search_handler,
        )

        item = RegistryItem(
            id="search_001",
            name="Search",
            description="Web search tool",
            component=tool,
        )

        registry.register(item)

        # Activate tool
        activated_tool = await registry.activate_mcp_tool("search_001")

        # Verify activation
        assert activated_tool is not None
        assert isinstance(activated_tool, MCPTool)
        assert activated_tool.name == "search"
        assert "search_001" in registry.active_items

    def test_tool_schemas_extraction(self):
        """Test extracting tool schemas for MCP registration."""
        registry = DynamicMCPRegistry()

        # Create multiple tools with different schemas
        tools = [
            MCPTool(
                name="calculator",
                description="Math calculator",
                input_schema={
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"],
                },
                handler=lambda x: eval(x["expression"]),
            ),
            MCPTool(
                name="text_processor",
                description="Text processor",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
                handler=lambda x: x["text"].upper(),
            ),
        ]

        # Register tools
        for i, tool in enumerate(tools):
            item = RegistryItem(
                id=f"tool_{i:03d}",
                name=tool.name.title(),
                description=tool.description,
                component=tool,
            )
            registry.register(item)

        # Get tool schemas
        schemas = registry.get_tool_schemas()

        # Verify schemas
        assert len(schemas) == 2
        assert "calculator" in schemas
        assert "text_processor" in schemas
        assert schemas["calculator"]["properties"]["expression"]["type"] == "string"
        assert schemas["text_processor"]["properties"]["text"]["type"] == "string"


class TestDynamicMCPState:
    """Test suite for DynamicMCPState with real components."""

    def test_mcp_state_creation(self):
        """Test creating DynamicMCPState."""
        state = DynamicMCPState(
            mcp_client_id="client_123",
            mcp_session_id="session_456",
            mcp_protocol_version="1.0",
        )

        assert state.mcp_client_id == "client_123"
        assert state.mcp_session_id == "session_456"
        assert state.mcp_protocol_version == "1.0"
        assert state.tool_call_history == []

    def test_tool_call_tracking(self):
        """Test tracking tool calls in MCP state."""
        state = DynamicMCPState(
            mcp_client_id="client_123", mcp_session_id="session_456"
        )

        # Track a tool call
        state.track_tool_call(
            tool_name="calculator", input_data={"expression": "2 + 2"}, result=4
        )

        # Verify tracking
        assert len(state.tool_call_history) == 1
        assert state.tool_call_history[0]["tool"] == "calculator"
        assert state.tool_call_history[0]["input"] == {"expression": "2 + 2"}
        assert state.tool_call_history[0]["result"] == "4"
        assert state.tool_call_history[0]["client_id"] == "client_123"
        assert state.tool_call_history[0]["session_id"] == "session_456"
        assert "timestamp" in state.tool_call_history[0]

    def test_multiple_tool_calls_tracking(self):
        """Test tracking multiple tool calls."""
        state = DynamicMCPState(mcp_client_id="client_123")

        # Track multiple tool calls
        calls = [
            {"tool": "calculator", "input": {"expression": "1 + 1"}, "result": 2},
            {
                "tool": "search",
                "input": {"query": "python"},
                "result": "search results",
            },
            {"tool": "calculator", "input": {"expression": "3 * 4"}, "result": 12},
        ]

        for call in calls:
            state.track_tool_call(call["tool"], call["input"], call["result"])

        # Verify all calls are tracked
        assert len(state.tool_call_history) == 3
        assert state.tool_call_history[0]["tool"] == "calculator"
        assert state.tool_call_history[1]["tool"] == "search"
        assert state.tool_call_history[2]["tool"] == "calculator"


class TestDynamicActivationMCPServer:
    """Test suite for DynamicActivationMCPServer with real components."""

    @pytest.fixture
    def temp_tools_file(self, tmp_path):
        """Create temporary tools file for MCP testing."""
        tools_content = """
        # MCP Test Tools

        ## Calculator
        - **Name**: calculator
        - **Description**: Mathematical calculations
        - **Input**: Expression strings
        - **Output**: Numerical results

        ## Text Processor
        - **Name**: text_processor
        - **Description**: Text processing and manipulation
        - **Input**: Text strings
        - **Output**: Processed text

        ## Data Validator
        - **Name**: data_validator
        - **Description**: Validate data formats
        - **Input**: Data objects
        - **Output**: Validation results
        """
        tools_file = tmp_path / "mcp_tools.md"
        tools_file.write_text(tools_content)
        return str(tools_file)

    def test_mcp_server_creation(self, temp_tools_file):
        """Test creating DynamicActivationMCPServer."""
        server = DynamicActivationMCPServer(
            name="test_mcp_server", discovery_source=temp_tools_file
        )

        assert server.name == "test_mcp_server"
        assert server.discovery_source == temp_tools_file
        assert isinstance(server.tool_registry, DynamicMCPRegistry)
        assert isinstance(server.state, DynamicMCPState)
        assert isinstance(server.meta_state, MetaStateSchema)
        assert server._discovery_agent is not None
        assert server._is_running is False

    def test_mcp_server_configuration(self, temp_tools_file):
        """Test MCP server configuration options."""
        config = {"auto_discover": True, "max_tools": 50, "cache_ttl": 7200}

        server = DynamicActivationMCPServer(
            name="configured_server",
            discovery_source=temp_tools_file,
            discovery_config=config,
        )

        assert server.discovery_config["auto_discover"] is True
        assert server.discovery_config["max_tools"] == 50
        assert server.discovery_config["cache_ttl"] == 7200

    @pytest.mark.asyncio
    async def test_mcp_server_lifecycle(self, temp_tools_file):
        """Test MCP server start/stop lifecycle."""
        server = DynamicActivationMCPServer(
            name="lifecycle_server", discovery_source=temp_tools_file
        )

        # Initially not running
        assert server._is_running is False

        # Start server
        await server.start()
        assert server._is_running is True
        assert server.meta_state.execution_status == "running"

        # Stop server
        await server.stop()
        assert server._is_running is False
        assert server.meta_state.execution_status == "stopped"

    @pytest.mark.asyncio
    async def test_mcp_client_connection(self, temp_tools_file):
        """Test MCP client connection handling."""
        server = DynamicActivationMCPServer(
            name="connection_server", discovery_source=temp_tools_file
        )

        # Handle client connection
        client_info = {
            "name": "Test Client",
            "version": "1.0",
            "capabilities": ["tools"],
        }

        response = await server.handle_client_connect("client_123", client_info)

        # Verify connection response
        assert response["status"] == "connected"
        assert response["server_name"] == "connection_server"
        assert response["protocol_version"] == "1.0"
        assert "session_id" in response
        assert "available_tools" in response

        # Verify client tracking
        assert "client_123" in server._clients
        assert server.state.mcp_client_id == "client_123"
        assert server.state.mcp_session_id == response["session_id"]

    @pytest.mark.asyncio
    async def test_mcp_client_disconnection(self, temp_tools_file):
        """Test MCP client disconnection handling."""
        server = DynamicActivationMCPServer(
            name="disconnection_server", discovery_source=temp_tools_file
        )

        # Connect client first
        await server.handle_client_connect("client_123", {"name": "Test Client"})
        assert "client_123" in server._clients

        # Disconnect client
        await server.handle_client_disconnect("client_123")

        # Verify disconnection
        assert "client_123" not in server._clients
        assert server.state.mcp_client_id is None
        assert server.state.mcp_session_id is None

    @pytest.mark.asyncio
    async def test_mcp_tool_request_handling(self, temp_tools_file):
        """Test handling MCP tool requests."""
        server = DynamicActivationMCPServer(
            name="tool_request_server", discovery_source=temp_tools_file
        )

        # Start server
        await server.start()

        # Create and register a test tool
        def test_handler(input_data: dict[str, Any]) -> str:
            """Test handler."""
            return f"Processed: {input_data}"

        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            input_schema={
                "type": "object",
                "properties": {"input": {"type": "string"}},
                "required": ["input"],
            },
            handler=test_handler,
        )

        item = RegistryItem(
            id="test_001", name="Test Tool", description="Test tool", component=tool
        )

        server.tool_registry.register(item)
        await server.tool_registry.activate_mcp_tool("test_001")

        # Handle tool request
        request = {
            "tool": "test_tool",
            "input": {"input": "test data"},
            "client_id": "client_123",
        }

        response = await server.handle_tool_request(request)

        # Verify response
        assert response["success"] is True
        assert "result" in response

        # Verify tool call tracking
        assert len(server.state.tool_call_history) == 1
        assert server.state.tool_call_history[0]["tool"] == "test_tool"
        assert server.state.tool_call_history[0]["input"] == {"input": "test data"}

    @pytest.mark.asyncio
    async def test_mcp_tool_request_error_handling(self, temp_tools_file):
        """Test error handling in MCP tool requests."""
        server = DynamicActivationMCPServer(
            name="error_server", discovery_source=temp_tools_file
        )

        await server.start()

        # Request non-existent tool
        request = {
            "tool": "nonexistent_tool",
            "input": {"data": "test"},
            "client_id": "client_123",
        }

        response = await server.handle_tool_request(request)

        # Verify error response
        assert response["success"] is False
        assert "error" in response
        assert "not found" in response["error"].lower()

        # Verify error tracking
        assert len(server.state.tool_call_history) == 1
        assert server.state.tool_call_history[0]["tool"] == "nonexistent_tool"
        assert "error" in server.state.tool_call_history[0]["result"]

    def test_mcp_server_available_tools(self, temp_tools_file):
        """Test getting available tools for MCP clients."""
        server = DynamicActivationMCPServer(
            name="tools_server", discovery_source=temp_tools_file
        )

        # Create and register multiple tools
        tools = [
            MCPTool(
                name="calculator",
                description="Mathematical calculator",
                input_schema={
                    "type": "object",
                    "properties": {"expr": {"type": "string"}},
                },
                handler=lambda x: eval(x["expr"]),
            ),
            MCPTool(
                name="text_processor",
                description="Text processor",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                },
                handler=lambda x: x["text"].upper(),
            ),
        ]

        for i, tool in enumerate(tools):
            item = RegistryItem(
                id=f"tool_{i:03d}",
                name=tool.name.title(),
                description=tool.description,
                component=tool,
            )
            server.tool_registry.register(item)

        # Get available tools
        available_tools = server.get_available_tools()

        # Verify available tools
        assert len(available_tools) == 2
        tool_names = {tool["name"] for tool in available_tools}
        assert tool_names == {"calculator", "text_processor"}

        # Verify tool details
        for tool in available_tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert "active" in tool

    def test_mcp_server_statistics(self, temp_tools_file):
        """Test MCP server statistics."""
        server = DynamicActivationMCPServer(
            name="stats_server", discovery_source=temp_tools_file
        )

        # Get initial stats
        stats = server.get_server_stats()

        # Verify initial stats
        assert stats["server_name"] == "stats_server"
        assert stats["is_running"] is False
        assert stats["connected_clients"] == 0
        assert stats["protocol_version"] == "1.0"
        assert stats["tool_calls"] == 0
        assert stats["discovery_enabled"] is True

        # Verify registry stats are included
        assert "total_components" in stats
        assert "active_components" in stats
        assert "inactive_components" in stats


class TestMCPIntegration:
    """Integration tests for MCP dynamic activation."""

    @pytest.fixture
    def comprehensive_mcp_tools_file(self, tmp_path):
        """Create comprehensive MCP tools file for integration testing."""
        tools_content = """
        # Comprehensive MCP Tools

        ## Math Tools

        ### Calculator
        - **Name**: calculator
        - **Description**: Basic arithmetic calculator
        - **Input**: Mathematical expressions
        - **Output**: Numerical results
        - **Category**: math

        ### Statistics
        - **Name**: statistics
        - **Description**: Statistical analysis tool
        - **Input**: Data arrays and operation type
        - **Output**: Statistical results
        - **Category**: math

        ## Text Tools

        ### Text Analyzer
        - **Name**: text_analyzer
        - **Description**: Analyze text content
        - **Input**: Text strings
        - **Output**: Analysis results
        - **Category**: text

        ### Language Detector
        - **Name**: language_detector
        - **Description**: Detect text language
        - **Input**: Text strings
        - **Output**: Language codes
        - **Category**: text

        ## Utility Tools

        ### Validator
        - **Name**: validator
        - **Description**: Validate data formats
        - **Input**: Data objects
        - **Output**: Validation results
        - **Category**: utility

        ### Formatter
        - **Name**: formatter
        - **Description**: Format data output
        - **Input**: Data objects and format type
        - **Output**: Formatted data
        - **Category**: utility
        """
        tools_file = tmp_path / "comprehensive_mcp_tools.md"
        tools_file.write_text(tools_content)
        return str(tools_file)

    @pytest.mark.asyncio
    async def test_full_mcp_workflow(self, comprehensive_mcp_tools_file):
        """Test complete MCP workflow from server start to tool execution."""
        # Create MCP server
        server = DynamicActivationMCPServer(
            name="integration_server",
            discovery_source=comprehensive_mcp_tools_file,
            discovery_config={
                "auto_discover": True,
                "max_tools": 20,
                "cache_ttl": 3600,
            },
        )

        # Start server
        await server.start()
        assert server._is_running is True

        # Connect client
        client_response = await server.handle_client_connect(
            "client_123", {"name": "Integration Test Client", "version": "1.0"}
        )
        assert client_response["status"] == "connected"

        # Create and register test tools
        def calc_handler(input_data: dict[str, Any]) -> float:
            """Calculator handler."""
            return eval(input_data["expression"])

        def text_handler(input_data: dict[str, Any]) -> str:
            """Text handler."""
            return input_data["text"].upper()

        tools = [
            MCPTool(
                name="calculator",
                description="Mathematical calculator",
                input_schema={
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"],
                },
                handler=calc_handler,
            ),
            MCPTool(
                name="text_processor",
                description="Text processor",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
                handler=text_handler,
            ),
        ]

        # Register and activate tools
        for i, tool in enumerate(tools):
            item = RegistryItem(
                id=f"integration_tool_{i:03d}",
                name=tool.name.title(),
                description=tool.description,
                component=tool,
            )
            server.tool_registry.register(item)
            await server.tool_registry.activate_mcp_tool(f"integration_tool_{i:03d}")

        # Execute tool requests
        calc_request = {
            "tool": "calculator",
            "input": {"expression": "5 + 3"},
            "client_id": "client_123",
        }

        calc_response = await server.handle_tool_request(calc_request)
        assert calc_response["success"] is True
        assert calc_response["result"] == 8

        text_request = {
            "tool": "text_processor",
            "input": {"text": "hello world"},
            "client_id": "client_123",
        }

        text_response = await server.handle_tool_request(text_request)
        assert text_response["success"] is True
        assert text_response["result"] == "HELLO WORLD"

        # Verify tool call tracking
        assert len(server.state.tool_call_history) == 2
        assert server.state.tool_call_history[0]["tool"] == "calculator"
        assert server.state.tool_call_history[1]["tool"] == "text_processor"

        # Get server stats
        stats = server.get_server_stats()
        assert stats["tool_calls"] == 2
        assert stats["connected_clients"] == 1
        assert stats["active_components"] == 2

        # Disconnect client
        await server.handle_client_disconnect("client_123")
        assert len(server._clients) == 0

        # Stop server
        await server.stop()
        assert server._is_running is False

    @pytest.mark.asyncio
    async def test_mcp_server_with_discovery(self, comprehensive_mcp_tools_file):
        """Test MCP server with automatic tool discovery."""
        server = DynamicActivationMCPServer(
            name="discovery_server",
            discovery_source=comprehensive_mcp_tools_file,
            discovery_config={"auto_discover": True, "max_tools": 100},
        )

        # Start server (should trigger auto-discovery)
        await server.start()

        # Verify discovery agent is working
        assert server._discovery_agent is not None
        assert server.discovery_config["auto_discover"] is True

        # Test tool discovery and activation
        request = {
            "tool": "unknown_tool",
            "input": {"data": "test"},
            "client_id": "client_123",
        }

        # This should trigger discovery attempt
        response = await server.handle_tool_request(request)

        # May succeed or fail depending on discovery results
        assert "success" in response
        if not response["success"]:
            assert "error" in response

    @pytest.mark.asyncio
    async def test_mcp_server_performance_with_many_tools(
        self, comprehensive_mcp_tools_file
    ):
        """Test MCP server performance with many tools."""
        import time

        server = DynamicActivationMCPServer(
            name="performance_server", discovery_source=comprehensive_mcp_tools_file
        )

        # Create many tools
        tools = []
        for i in range(50):

            def handler(input_data: dict[str, Any]) -> str:
                return f"Tool {i} result: {input_data}"

            tool = MCPTool(
                name=f"tool_{i}",
                description=f"Test tool {i}",
                input_schema={
                    "type": "object",
                    "properties": {"input": {"type": "string"}},
                    "required": ["input"],
                },
                handler=handler,
            )
            tools.append(tool)

        # Register all tools
        start_time = time.time()

        for i, tool in enumerate(tools):
            item = RegistryItem(
                id=f"perf_tool_{i:03d}",
                name=tool.name.title(),
                description=tool.description,
                component=tool,
            )
            server.tool_registry.register(item)

        registration_time = time.time() - start_time

        # Activate all tools
        start_time = time.time()

        for i in range(50):
            await server.tool_registry.activate_mcp_tool(f"perf_tool_{i:03d}")

        activation_time = time.time() - start_time

        # Verify performance
        assert registration_time < 1.0  # Should register 50 tools in < 1 second
        assert activation_time < 2.0  # Should activate 50 tools in < 2 seconds

        # Verify correctness
        assert len(server.tool_registry.items) == 50
        assert len(server.tool_registry.active_items) == 50

        # Test stats performance
        start_time = time.time()
        stats = server.get_server_stats()
        stats_time = time.time() - start_time

        assert stats_time < 0.1  # Stats should be fast
        assert stats["total_components"] == 50
        assert stats["active_components"] == 50
