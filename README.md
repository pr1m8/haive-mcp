# haive-mcp

[![PyPI version](https://img.shields.io/pypi/v/haive-mcp.svg)](https://pypi.org/project/haive-mcp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/haive-mcp.svg)](https://pypi.org/project/haive-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/pr1m8/haive-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/pr1m8/haive-mcp/actions/workflows/ci.yml)
[![Docs](https://github.com/pr1m8/haive-mcp/actions/workflows/docs.yml/badge.svg)](https://pr1m8.github.io/haive-mcp/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/haive-mcp.svg)](https://pypi.org/project/haive-mcp/)

**Dynamic MCP integration for AI agents** — search 1,960+ servers, install with HITL approval, connect via LangChain or Docker.

`haive-mcp` enables runtime discovery and integration of tools from the **Model Context Protocol (MCP)** ecosystem. Instead of hard-coding tool integrations, your agents can search the MCP registry, install relevant servers (with human approval), and use them as standard LangChain tools.

---

## What is MCP?

**Model Context Protocol** is Anthropic's open standard for connecting LLM applications to external tools and data sources. There are 1,960+ MCP servers covering everything from databases to file systems to GitHub APIs to browser automation.

`haive-mcp` is the bridge between MCP and the Haive agent framework. It provides:

1. **Server discovery** — search across the entire MCP registry by capability
2. **Multiple transports** — STDIO (npx/uvx), SSE, Streamable HTTP, Docker
3. **HITL approval** — Human-in-the-loop gating for server installation
4. **LangChain bridge** — MCP tools work as standard LangChain tools
5. **Docker isolation** — run servers in containers for security
6. **Intelligent agent** — `IntelligentMCPAgent` auto-discovers tools for tasks

---

## Why dynamic MCP?

**Static tool libraries are limiting.** You either:
- Pre-install tools you might never need (bloat)
- Don't have a tool when you need it (hard-coded constraint)

**Dynamic MCP integration:** Your agent has access to 1,960+ servers on demand. Need to query a database? It finds and installs `mcp/postgres`. Need to scrape a website? It pulls `playwright-mcp`. Need GitHub access? `github-mcp-server`. With HITL approval gates so the user controls what gets installed.

---

## Installation

```bash
pip install haive-mcp
```

---

## Transport Types

MCP servers communicate over different transports. `haive-mcp` supports all four:

| Transport | Value | Use Case | Example |
|-----------|-------|----------|---------|
| **STDIO** | `stdio` | CLI servers via npx/uvx (most common) | `npx @modelcontextprotocol/server-filesystem` |
| **SSE** | `sse` | HTTP streaming servers | Long-running services |
| **Streamable HTTP** | `streamable_http` | Continuous data | Real-time feeds |
| **Docker** | `docker` | Isolated containers | Untrusted servers, complex deps |

---

## Usage Patterns

### 1. Static Configuration

Hand-pick servers and configure them upfront:

```python
from haive.mcp.config import MCPConfig, MCPServerConfig, MCPTransport
from haive.mcp.manager import MCPManager

config = MCPConfig(
    enabled=True,
    servers={
        "filesystem": MCPServerConfig(
            name="filesystem",
            transport=MCPTransport.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
        ),
        "github": MCPServerConfig(
            name="github",
            transport=MCPTransport.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."},
        ),
        "postgres": MCPServerConfig(
            name="postgres",
            transport=MCPTransport.DOCKER,
            command="mcp/postgres",
            env={"POSTGRES_HOST": "host.docker.internal"},
            docker_volumes=["/data:/data:ro"],
            docker_network="host",
        ),
    }
)

# Connect and get tools
manager = MCPManager(config)
await manager.connect_all()
tools = await manager.get_all_tools()

# Use with any Haive agent
from haive.agents.react.agent import ReactAgent
from haive.core.engine.aug_llm import AugLLMConfig

agent = ReactAgent(
    engine=AugLLMConfig(tools=tools),
    max_iterations=5,
)
result = await agent.arun("List files in /workspace and create a summary issue on GitHub")
```

### 2. Dynamic Discovery (IntelligentMCPAgent)

Let the agent discover and install tools as needed:

```python
from haive.mcp.agents import IntelligentMCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

agent = IntelligentMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True,        # Search registry for relevant servers
    require_approval=True,      # HITL approval before installing
)

result = await agent.arun(
    "Find Python repositories on GitHub about quantum computing"
)
# Agent flow:
# 1. Searches MCP registry for "github"
# 2. Finds github-mcp-server
# 3. Asks for approval to install
# 4. Installs via npx
# 5. Connects to server
# 6. Calls github_search_repositories tool
# 7. Returns results
```

### 3. CLI

Manage MCP servers from the command line:

```bash
# Install the CLI (comes with haive-mcp)
pip install haive-mcp

# Discover servers
haive-mcp discover "database"
haive-mcp discover "web scraping"
haive-mcp discover "github"

# List available transports
haive-mcp transports

# Install a specific server
haive-mcp install postgres

# Test a server
haive-mcp test filesystem

# Show server tools
haive-mcp tools filesystem
```

---

## HITL Approval Flow

When `require_approval=True`, the agent pauses and asks before installing any new server:

```
🔍 Searching MCP registry for 'database'...
✅ Found: postgres-mcp (mcp/postgres)
   Description: PostgreSQL database access via MCP
   Tools: query, schema, list_tables, describe_table
   Transport: stdio
   Trust: ⭐⭐⭐⭐⭐ (1.2k installs)

❓ Install postgres-mcp? [y/N]: y
📦 Installing via npx...
✅ Installed and connected
🔧 Available tools: query, schema, list_tables, describe_table
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              IntelligentMCPAgent                │
│  (auto_discover + HITL approval)                │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│  Discovery   │          │   MCPMgr     │
│              │          │              │
│ • Search     │          │ • Lifecycle  │
│ • Documentation│        │ • Connection │
│ • 1960+ servers│        │ • Tools      │
└──────────────┘          └──────┬───────┘
                                 │
                ┌────────────────┼────────────────┐
                ▼                ▼                ▼
        ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
        │   STDIO     │  │     SSE     │  │   Docker    │
        │  npx/uvx    │  │   HTTP      │  │  Container  │
        └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Documentation

📖 **Full documentation:** https://pr1m8.github.io/haive-mcp/

---

## Related Packages

| Package | Description |
|---------|-------------|
| [haive-core](https://pypi.org/project/haive-core/) | Foundation: engines, graphs |
| [haive-agents](https://pypi.org/project/haive-agents/) | Production agents (use MCP tools) |
| [haive-tools](https://pypi.org/project/haive-tools/) | Static tool implementations |

---

## License

MIT © [pr1m8](https://github.com/pr1m8)
