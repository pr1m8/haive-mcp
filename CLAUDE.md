# CLAUDE.md - Haive MCP Package Guide

**Purpose**: Central guide for working with the haive-mcp package
**Version**: 2.0
**Last Updated**: 2026-04-02

## Package Overview

Haive MCP (Model Context Protocol) enables **dynamic, runtime integration** of tools from **1,960+ MCP servers**. Agents can discover and integrate tools based on task requirements without predefined configuration.

## Directory Structure

```
haive-mcp/
├── src/haive/mcp/
│   ├── __init__.py              # Main exports
│   ├── __main__.py              # CLI entry point (haive-mcp command)
│   ├── config.py                # MCPConfig, MCPServerConfig, MCPTransport
│   ├── manager.py               # MCPManager for server lifecycle
│   ├── agents/                  # MCP-enabled agent implementations
│   ├── client/                  # Native MCP client + transports
│   ├── discovery/               # Server discovery system
│   ├── documentation/           # Documentation loader (1,960+ servers)
│   ├── downloader/              # Server download and installation
│   ├── installers/              # Installation strategies
│   ├── integration/             # FastAPI and agent integration
│   ├── mixins/                  # MCPMixin for existing agents
│   ├── plugins/                 # Plugin system (browser, etc.)
│   ├── registry/                # Server configuration converter
│   ├── servers/                 # Server management infrastructure
│   ├── tools/                   # Server selector, tester, AI assistant
│   └── utils/                   # Utility scripts
├── examples/                    # Runnable examples
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── data/mcp_servers/            # Pre-indexed server database
├── configs/                     # YAML configurations
├── docs/                        # Sphinx documentation
├── project_docs/                # Internal docs (guides, architecture)
└── scripts/                     # Setup and utility scripts
```

## Quick Start

```bash
# Install
poetry install

# CLI
poetry run haive-mcp --help
poetry run haive-mcp transports
poetry run haive-mcp discover "database"

# Run examples
poetry run python examples/basic_mcp_agent.py

# Run tests
poetry run pytest tests/unit/ -v
```

## Transport Types

| Transport | Value | Use Case |
|-----------|-------|----------|
| STDIO | `stdio` | CLI-based servers via npx/uvx (most common) |
| SSE | `sse` | HTTP streaming servers |
| Streamable HTTP | `streamable_http` | Continuous data transfer |
| Docker | `docker` | Isolated container execution |

## Key Patterns

### Static Configuration
```python
from haive.mcp.config import MCPConfig, MCPServerConfig, MCPTransport

config = MCPConfig(
    enabled=True,
    servers={
        "filesystem": MCPServerConfig(
            name="filesystem",
            transport=MCPTransport.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
        )
    }
)
```

### Docker Transport
```python
MCPServerConfig(
    name="postgres",
    transport=MCPTransport.DOCKER,
    command="mcp/postgres",  # Docker image
    env={"POSTGRES_HOST": "host.docker.internal"},
    docker_volumes=["/data:/data:ro"],
    docker_network="host",
)
```

### Dynamic Discovery
```python
from haive.mcp.agents import IntelligentMCPAgent

agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True,
    require_approval=True,
)
```

## Dependencies

- `mcp` - Official MCP SDK
- `fastmcp` - FastMCP for building servers
- `langchain-mcp-adapters` - LangChain bridge for MCP tools
- `langchain-mcp-tools` - Additional MCP tool utilities
- `click` - CLI framework

## Testing

```bash
# Unit tests (fast, no external deps)
poetry run pytest tests/unit/ -v

# Integration tests (require MCP servers / network)
poetry run pytest tests/integration/ -v
```

## Important Notes

1. **Async first** - All MCP operations are async, use `await`
2. **Transport choice** - Use `stdio` for npx/uvx servers, `docker` for containerized
3. **Server installation** - Servers install via `npx` (Node.js) or `uvx` (Python)
4. **No mocks** - Test with real MCP servers where possible
