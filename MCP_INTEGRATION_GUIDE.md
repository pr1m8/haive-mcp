# MCP Integration Guide for Haive

## Overview

This guide demonstrates how to create, test, and integrate MCP (Model Context Protocol) servers with the Haive framework using FastMCP and LangChain adapters.

## What is MCP?

Model Context Protocol (MCP) is a standardized protocol for exposing tools, resources, and prompts to Large Language Models (LLMs). It enables:

- **Tools**: Functions that LLMs can call to perform actions
- **Resources**: Data sources that LLMs can read
- **Prompts**: Reusable prompt templates for common tasks

## Architecture

```
┌─────────────┐     ┌────────────────┐     ┌───────────────┐
│   LLM/AI    │────▶│ LangChain MCP  │────▶│  MCP Server   │
│  Assistant  │     │   Adapters     │     │  (FastMCP)    │
└─────────────┘     └────────────────┘     └───────────────┘
       │                     │                       │
       └─────────────────────┴───────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Haive Dataflow  │
                    │    Registry      │
                    └─────────────────┘
```

## Creating an MCP Server

### 1. Basic FastMCP Server

````python
from mcp.server import FastMCP

# Create server
mcp = FastMCP("my-server")

# Add tools
@mcp.tool()
async def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

# Add resources
@mcp.resource("file://{path}")
async def read_file(path: str) -> str:
    """Read a file resource."""
    with open(path, 'r') as f:
        return f.read()

# Add prompts
@mcp.prompt()
async def code_review(code: str) -> List[Dict[str, str]]:
    """Generate a code review prompt."""
    return [{
        "role": "user",
        "content": f"Please review this code:\n```\n{code}\n```"
    }]

# Run server
if __name__ == "__main__":
    mcp.run(transport="stdio")
````

### 2. HTTP-Based MCP Server

For production use, HTTP transport is often more reliable:

```python
from aiohttp import web
from mcp.server import FastMCP

mcp = FastMCP("http-server")

# Define tools...

# Create HTTP endpoints
routes = web.RouteTableDef()

@routes.get('/')
async def info(request):
    return web.json_response({
        "name": "http-server",
        "tools": ["hello", "calculate"],
        "transport": "http"
    })

@routes.post('/execute')
async def execute(request):
    data = await request.json()
    tool = data["tool"]
    params = data["params"]

    # Execute tool based on name
    result = await mcp._tools[tool](**params)

    return web.json_response({"result": result})

app = web.Application()
app.add_routes(routes)
web.run_app(app, port=8001)
```

## Integrating with Haive Dataflow

### 1. Register MCP Server in Registry

```python
from haive.dataflow import registry_system, EntityType, MCPServerConfig, MCPTransport

# Create server configuration
config = MCPServerConfig(
    name="my-mcp-server",
    transport=MCPTransport.STDIO,
    command="python",
    args=["my_server.py"],
    capabilities=["tools", "resources", "prompts"]
)

# Register in dataflow
server_id = registry_system.register_entity(
    name=config.name,
    entity_type=EntityType.MCP_SERVER,
    description="My custom MCP server",
    metadata={"config": config.model_dump()}
)
```

### 2. Use MCP Client

```python
from haive.dataflow.mcp.client import MCPClient

# Create client
client = MCPClient(registry_system)

# Initialize from registry
await client.initialize_from_registry()

# Get available tools
tools = await client.get_available_tools()

# Execute a tool
result = await client.execute_tool("hello", {"name": "World"})
```

### 3. LangChain Integration

```python
from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools

# Configure servers
servers = {
    "my-server": {
        "transport": "stdio",
        "command": "python",
        "args": ["my_server.py"]
    }
}

# Create client
mcp_client = MultiServerMCPClient(servers)

# Load tools for LangChain
tools = await load_mcp_tools(mcp_client)

# Use with LangChain agent
from langchain.agents import create_react_agent
agent = create_react_agent(llm, tools, prompt)
```

## Testing MCP Servers

### 1. Direct Testing

```python
# Test tools directly
from my_server import mcp

async def test_tools():
    result = await mcp._tools["hello"]("World")
    assert result == "Hello, World!"
```

### 2. HTTP Testing

```python
import aiohttp

async def test_http_server():
    async with aiohttp.ClientSession() as session:
        # Test tool execution
        resp = await session.post("http://localhost:8001/execute", json={
            "tool": "hello",
            "params": {"name": "Test"}
        })
        data = await resp.json()
        assert data["result"] == "Hello, Test!"
```

## Example Servers

### 1. File System Server

Located at: `src/haive/mcp/servers/example_server_fastmcp.py`

- Tools: read_file, write_file, list_directory, search_files
- Resources: file:// protocol support
- Prompts: code_review, refactor

### 2. Dataflow Server

Located at: `src/haive/mcp/servers/dataflow_server.py`

- Tools: list_components, register_component, discover_components
- Integration with haive-dataflow registry
- Component management capabilities

### 3. HTTP Server

Located at: `src/haive/mcp/servers/simple_http_server.py`

- Simple HTTP API for MCP tools
- Easy to test and deploy
- REST-style endpoints

## Best Practices

1. **Use Type Hints**: Always include type hints for tool parameters
2. **Provide Descriptions**: Add clear docstrings for tools
3. **Handle Errors**: Return meaningful error messages
4. **Test Thoroughly**: Test both direct execution and through adapters
5. **Use Async**: Make tools async for better performance
6. **Security**: Validate inputs and sanitize file paths

## Deployment

### Stdio Transport

```bash
# Run directly
python my_server.py

# Or with FastMCP CLI
fastmcp run my_server.py
```

### HTTP Transport

```bash
# Run with uvicorn (FastAPI)
uvicorn my_server:app --host 0.0.0.0 --port 8000

# Or with aiohttp
python http_server.py
```

## Troubleshooting

1. **Import Errors**: Make sure `mcp` and `langchain-mcp-adapters` are installed
2. **Connection Issues**: Check server is running and accessible
3. **Tool Not Found**: Verify tool is registered with correct name
4. **Async Errors**: Ensure all tool functions are async

## Next Steps

1. Create production-ready MCP servers for specific domains
2. Integrate with existing Haive agents
3. Build MCP server management UI
4. Add monitoring and health checks
5. Deploy servers as microservices
