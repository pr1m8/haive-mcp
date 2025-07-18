#!/usr/bin/env python3
"""Simple HTTP MCP server example."""

from datetime import datetime

from aiohttp import web

from mcp.server import FastMCP


# Create MCP server
mcp = FastMCP("simple-http-mcp")


# Add some simple tools
@mcp.tool()
async def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}! Welcome to the MCP server."


@mcp.tool()
async def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y


@mcp.tool()
async def get_time() -> str:
    """Get current time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Simple HTTP routes
routes = web.RouteTableDef()


@routes.get("/")
async def index(request: web.Request) -> web.Response:
    """Root endpoint with server info."""
    return web.json_response(
        {
            "server": "simple-http-mcp",
            "version": "1.0.0",
            "endpoints": {
                "/": "Server info",
                "/tools": "List available tools",
                "/execute": "Execute a tool (POST)",
            },
        }
    )


@routes.get("/tools")
async def list_tools(request: web.Request) -> web.Response:
    """List available tools."""
    tools = []

    # Get tools from MCP server
    # Note: In real implementation, we'd use MCP's internal registry
    tools_info = {
        "hello": {
            "name": "hello",
            "description": "Say hello to someone",
            "parameters": {"name": {"type": "string", "description": "Name to greet"}},
        },
        "add": {
            "name": "add",
            "description": "Add two numbers",
            "parameters": {
                "x": {"type": "integer", "description": "First number"},
                "y": {"type": "integer", "description": "Second number"},
            },
        },
        "get_time": {
            "name": "get_time",
            "description": "Get current time",
            "parameters": {},
        },
    }

    return web.json_response({"tools": tools_info, "count": len(tools_info)})


@routes.post("/execute")
async def execute_tool(request: web.Request) -> web.Response:
    """Execute a tool."""
    try:
        data = await request.json()
        tool_name = data.get("tool")
        params = data.get("params", {})

        # Execute the appropriate tool
        if tool_name == "hello":
            result = await hello(params.get("name", "World"))
        elif tool_name == "add":
            result = await add(params.get("x", 0), params.get("y", 0))
        elif tool_name == "get_time":
            result = await get_time()
        else:
            return web.json_response(
                {"error": f"Unknown tool: {tool_name}"}, status=400
            )

        return web.json_response(
            {
                "tool": tool_name,
                "params": params,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def create_app() -> web.Application:
    """Create the web application."""
    app = web.Application()
    app.add_routes(routes)
    return app


if __name__ == "__main__":
    # Run the server
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8001)
