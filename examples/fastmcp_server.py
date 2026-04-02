#!/usr/bin/env python3
"""FastMCP Server - Create custom MCP servers with FastMCP.

Demonstrates building your own MCP server using FastMCP, which can then
be connected to by haive-mcp agents. This is useful for exposing your
own tools and resources via the MCP protocol.

Usage:
    poetry run python examples/fastmcp_server.py

Then in another terminal, connect to it:
    poetry run python examples/basic_mcp_agent.py  # (after updating config)

References:
    - FastMCP docs: https://gofastmcp.com
    - MCP spec: https://spec.modelcontextprotocol.io
"""

from fastmcp import FastMCP

# Create a FastMCP server
mcp = FastMCP("my-haive-tools")


@mcp.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! Welcome to Haive."


@mcp.tool()
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: A mathematical expression (e.g., "2 + 3 * 4")
    """
    # Only allow safe math operations
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: expression contains invalid characters"
    try:
        result = eval(expression)  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("config://app")
def get_app_config() -> str:
    """Get the application configuration."""
    return '{"app": "haive-mcp", "version": "0.1.0", "status": "running"}'


if __name__ == "__main__":
    # Run the server (defaults to stdio transport)
    mcp.run()
