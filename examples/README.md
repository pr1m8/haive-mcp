# Examples

Runnable examples demonstrating haive-mcp capabilities.

## Getting Started

```bash
# Install dependencies
poetry install

# Run any example
poetry run python examples/basic_mcp_agent.py
```

## Examples

| Example | Description |
|---------|-------------|
| [basic_mcp_agent.py](basic_mcp_agent.py) | Connect to MCP servers with static configuration |
| [intelligent_discovery.py](intelligent_discovery.py) | Auto-discover servers based on task needs |
| [dynamic_server_management.py](dynamic_server_management.py) | Add, monitor, and hot-reload servers at runtime |
| [tool_transfer.py](tool_transfer.py) | Share MCP tools between agents |
| [docker_transport.py](docker_transport.py) | Run MCP servers in Docker containers |
| [fastmcp_server.py](fastmcp_server.py) | Build custom MCP servers with FastMCP |
| [langchain_mcp_adapters.py](langchain_mcp_adapters.py) | Bridge MCP tools into LangChain/LangGraph |

## Prerequisites

- Python 3.12+
- Node.js (for npx-based MCP servers)
- Docker (for docker transport examples)
- API keys set as environment variables where needed
