#!/usr/bin/env python3
"""Test MCP models and basic functionality."""

from haive.dataflow.registry.models import (
    MCPPromptDefinition,
    MCPResourceDefinition,
    MCPServerConfig,
    MCPServerHealth,
    MCPToolDefinition,
    MCPTransport,
)


def test_mcp_transport_enum():
    """Test MCPTransport enum values."""
    assert MCPTransport.STDIO.value == "stdio"
    assert MCPTransport.HTTP.value == "http"
    assert MCPTransport.SSE.value == "sse"


def test_mcp_server_config():
    """Test MCPServerConfig model."""
    # Test stdio transport config
    stdio_config = MCPServerConfig(
        name="test-stdio-server",
        transport=MCPTransport.STDIO,
        command="test-command",
        args=["--test", "--verbose"],
        capabilities=["read", "write"],
    )

    assert stdio_config.name == "test-stdio-server"
    assert stdio_config.transport == MCPTransport.STDIO
    assert stdio_config.command == "test-command"
    assert len(stdio_config.args) == 2
    assert "read" in stdio_config.capabilities

    # Test HTTP transport config
    http_config = MCPServerConfig(
        name="test-http-server",
        transport=MCPTransport.HTTP,
        url="http://localhost:8080/mcp",
        capabilities=["search", "fetch"],
    )

    assert http_config.name == "test-http-server"
    assert http_config.transport == MCPTransport.HTTP
    assert http_config.url == "http://localhost:8080/mcp"
    assert http_config.command is None

    # Test model dump
    dump = stdio_config.model_dump()
    assert dump["name"] == "test-stdio-server"
    assert dump["transport"] == "stdio"


def test_mcp_tool_definition():
    """Test MCPToolDefinition model."""
    tool = MCPToolDefinition(
        name="read_file",
        description="Read contents of a file",
        server_name="filesystem-server",
        schema={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path"}},
            "required": ["path"],
        },
        tags=["filesystem", "read"],
    )

    assert tool.name == "read_file"
    assert tool.server_name == "filesystem-server"
    assert tool.schema["properties"]["path"]["type"] == "string"
    assert "filesystem" in tool.tags


def test_mcp_resource_definition():
    """Test MCPResourceDefinition model."""
    resource = MCPResourceDefinition(
        name="project-docs",
        uri="file:///docs/project",
        description="Project documentation",
        server_name="docs-server",
        mime_type="text/markdown",
    )

    assert resource.name == "project-docs"
    assert resource.uri == "file:///docs/project"
    assert resource.mime_type == "text/markdown"


def test_mcp_prompt_definition():
    """Test MCPPromptDefinition model."""
    prompt = MCPPromptDefinition(
        name="code-review",
        description="Review code for best practices",
        server_name="ai-server",
        template="Please review the following code for best practices:\n\n{code}",
        variables=[
            {
                "name": "code",
                "description": "Code to review",
                "required": True,
            }
        ],
    )

    assert prompt.name == "code-review"
    assert len(prompt.variables) == 1
    assert prompt.variables[0]["required"] is True


def test_mcp_server_health():
    """Test MCPServerHealth model."""
    from datetime import datetime

    # Healthy server
    health = MCPServerHealth(
        server_name="test-server",
        is_healthy=True,
        last_check=datetime.now(),
        response_time_ms=50.5,
        error_count=0,
        capabilities_available=["read", "write", "search"],
    )

    assert health.is_healthy is True
    assert health.response_time_ms == 50.5
    assert health.error_count == 0
    assert len(health.capabilities_available) == 3

    # Unhealthy server
    unhealthy = MCPServerHealth(
        server_name="failing-server",
        is_healthy=False,
        last_check=datetime.now(),
        error_count=5,
        error_details="Connection timeout",
        capabilities_available=[],
    )

    assert unhealthy.is_healthy is False
    assert unhealthy.error_count == 5
    assert unhealthy.error_details == "Connection timeout"
    assert len(unhealthy.capabilities_available) == 0


if __name__ == "__main__":
    # Run tests
    test_mcp_transport_enum()

    test_mcp_server_config()

    test_mcp_tool_definition()

    test_mcp_resource_definition()

    test_mcp_prompt_definition()

    test_mcp_server_health()
