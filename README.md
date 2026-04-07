# haive-mcp

[![PyPI version](https://img.shields.io/pypi/v/haive-mcp.svg)](https://pypi.org/project/haive-mcp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/haive-mcp.svg)](https://pypi.org/project/haive-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/pr1m8/haive-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/pr1m8/haive-mcp/actions/workflows/ci.yml)
[![Docs](https://github.com/pr1m8/haive-mcp/actions/workflows/docs.yml/badge.svg)](https://pr1m8.github.io/haive-mcp/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/haive-mcp.svg)](https://pypi.org/project/haive-mcp/)

**Dynamic MCP integration for AI agents** — search 1,960+ servers, install with HITL approval, connect via LangChain or Docker.

`haive-mcp` enables runtime discovery and integration of tools from the Model Context Protocol (MCP) ecosystem. Agents can find and use tools from 1,960+ MCP servers without predefined configuration.

## Installation

```bash
pip install haive-mcp
```

## Features

- **🔍 Server Discovery** — search across 1,960+ MCP servers
- **🚀 Multi-Transport** — STDIO, SSE, Streamable HTTP, Docker
- **🛡️ HITL Approval** — Human-in-the-loop for server installation
- **🤖 Intelligent Agent** — `IntelligentMCPAgent` auto-discovers tools for tasks
- **🐳 Docker Isolation** — run servers in containers for security
- **📦 LangChain Bridge** — MCP tools work as standard LangChain tools
- **⚡ CLI** — `haive-mcp` command for discovery and management

## Quick Start

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

### Dynamic Discovery
```python
from haive.mcp.agents import IntelligentMCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

agent = IntelligentMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True,
    require_approval=True,
)

result = await agent.arun("Search GitHub for Python repos about quantum computing")
# Auto-discovers and installs github-mcp-server, then uses it
```

### CLI
```bash
# Discover servers for a topic
haive-mcp discover "database"

# List available transports
haive-mcp transports

# Install a server
haive-mcp install postgres
```

## Transport Types

| Transport | Use Case |
|-----------|----------|
| `stdio` | CLI servers via npx/uvx (most common) |
| `sse` | HTTP streaming servers |
| `streamable_http` | Continuous data transfer |
| `docker` | Isolated container execution |

## Documentation

📖 **Full documentation:** https://pr1m8.github.io/haive-mcp/

## Related Packages

| Package | Description |
|---------|-------------|
| [haive-core](https://pypi.org/project/haive-core/) | Foundation: engines, graphs |
| [haive-agents](https://pypi.org/project/haive-agents/) | Production agents |
| [haive-tools](https://pypi.org/project/haive-tools/) | Static tool implementations |

## License

MIT © [pr1m8](https://github.com/pr1m8)
