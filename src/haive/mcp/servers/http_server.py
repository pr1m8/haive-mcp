#!/usr/bin/env python3
"""HTTP-based MCP server for haive using FastAPI and SSE transport."""

from datetime import datetime
import json
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn

from mcp.server import FastMCP
from mcp.server.sse import SSEServerTransport


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Haive MCP Server", version="1.0.0")

# Create FastMCP server
mcp = FastMCP("haive-http-server")


# === MCP Tools ===
@mcp.tool()
async def echo(message: str) -> str:
    """Echo back a message."""
    return f"Echo: {message}"


@mcp.tool()
async def get_server_time() -> str:
    """Get the current server time."""
    return datetime.now().isoformat()


@mcp.tool()
async def calculate(operation: str, a: float, b: float) -> float:
    """Perform a calculation.

    Args:
        operation: One of 'add', 'subtract', 'multiply', 'divide'
        a: First number
        b: Second number

    Returns:
        Result of the calculation
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else float("inf"),
    }

    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")

    return operations[operation](a, b)


@mcp.tool()
async def list_tools() -> list[str]:
    """List all available tools."""
    # This would normally come from the MCP server's internal registry
    return ["echo", "get_server_time", "calculate", "list_tools", "get_system_info"]


@mcp.tool()
async def get_system_info() -> dict[str, Any]:
    """Get system information."""
    import os
    import platform

    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "cwd": os.getcwd(),
        "timestamp": datetime.now().isoformat(),
    }


# === MCP Resources ===
@mcp.resource("server://info")
async def server_info_resource() -> str:
    """Get server information as a resource."""
    info = {
        "name": "haive-http-server",
        "version": "1.0.0",
        "transport": "sse",
        "timestamp": datetime.now().isoformat(),
    }
    return json.dumps(info, indent=2)


@mcp.resource("server://status")
async def server_status_resource() -> str:
    """Get server status."""
    status = {
        "status": "running",
        "uptime": "N/A",  # Would calculate actual uptime
        "requests_handled": 0,  # Would track actual requests
        "timestamp": datetime.now().isoformat(),
    }
    return json.dumps(status, indent=2)


# === MCP Prompts ===
@mcp.prompt()
async def help_prompt() -> list[dict[str, str]]:
    """Get help using this MCP server."""
    return [
        {
            "role": "system",
            "content": "You are a helpful assistant that knows how to use the Haive MCP server.",
        },
        {
            "role": "user",
            "content": """Please help me understand how to use this MCP server. 

Available tools:
- echo: Echo back a message
- get_server_time: Get current server time
- calculate: Perform calculations (add, subtract, multiply, divide)
- list_tools: List all available tools
- get_system_info: Get system information

What would you like to do?""",
        },
    ]


# === FastAPI Routes ===
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Haive MCP Server",
        "version": "1.0.0",
        "transport": ["sse", "http"],
        "endpoints": {"sse": "/sse", "health": "/health", "info": "/info"},
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/info")
async def info():
    """Server information endpoint."""
    return {
        "name": "haive-http-server",
        "version": "1.0.0",
        "capabilities": {
            "tools": [
                "echo",
                "get_server_time",
                "calculate",
                "list_tools",
                "get_system_info",
            ],
            "resources": ["server://info", "server://status"],
            "prompts": ["help_prompt"],
        },
        "transport": {"type": "sse", "endpoint": "/sse"},
    }


# SSE transport instance
sse_transport = None


@app.post("/sse")
async def handle_sse(request: Request):
    """Handle SSE connections for MCP protocol."""
    global sse_transport

    if sse_transport is None:
        sse_transport = SSEServerTransport("/sse")

    # Handle the SSE connection
    async def event_generator():
        try:
            # Process MCP messages through the transport
            async for message in sse_transport.handle_connection(request):
                yield f"data: {json.dumps(message)}\n\n"
        except Exception as e:
            logger.error(f"SSE error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# === Main entry point ===
def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the HTTP MCP server."""
    logger.info(f"Starting Haive MCP HTTP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # Run the server
    run_server()
