# haive-mcp

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![MCP SDK](https://img.shields.io/badge/MCP_SDK-1.26-00C853?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCI+PHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiByeD0iNCIgZmlsbD0iIzAwQzg1MyIvPjx0ZXh0IHg9IjUiIHk9IjE3IiBmb250LXNpemU9IjEyIiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9Im1vbm9zcGFjZSI+TTwvdGV4dD48L3N2Zz4=)](https://modelcontextprotocol.io/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.13-FF6B35?logo=fastapi&logoColor=white)](https://gofastmcp.com/)
[![LangChain](https://img.shields.io/badge/LangChain_MCP-0.1.14-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langchain-mcp-adapters)
[![Tests](https://img.shields.io/badge/tests-32_passing-brightgreen?logo=pytest&logoColor=white)](#testing)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Poetry](https://img.shields.io/badge/poetry-managed-blueviolet?logo=poetry&logoColor=white)](https://python-poetry.org/)

**Dynamic MCP integration for AI agents** -- search 1,960+ servers, install with HITL approval, connect via LangChain or Docker, all at runtime.

---

## Highlights

| | Feature | Description |
|---|---|---|
| **1,960+** | Server Database | Pre-indexed MCP servers with README parsing and install extraction |
| **LLM Fallback** | Smart Install | Falls back to LLM when README parsing can't find the install command |
| **HITL** | Approval Flow | Human-in-the-loop approval before any server installation |
| **4 Transports** | stdio, SSE, HTTP, Docker | Run servers as subprocesses, HTTP endpoints, or Docker containers |
| **Config Export** | 3 Formats | Generate configs for haive-mcp, Claude Desktop, or langchain-mcp-adapters |
| **CLI** | `haive-mcp` | Search, discover, install, and manage servers from the terminal |

## Install

```bash
pip install haive-mcp        # from PyPI
# or
poetry add haive-mcp         # with Poetry
# or from source
git clone https://github.com/pr1m8/haive-mcp && cd haive-mcp && poetry install
```

## Quick Start

### Search and install a server (3 lines)

```python
from haive.mcp.installer_service import MCPInstallerService

service = MCPInstallerService(require_approval=False)
result = await service.search_and_install("filesystem")
# Searches 1,960 servers → extracts install cmd from README → connects → 14 tools ready
```

### Connect with langchain-mcp-adapters

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        "transport": "stdio",
    }
})
tools = await client.get_tools()  # 14 LangChain-compatible tools
```

### Static configuration

```python
from haive.mcp.config import MCPConfig, MCPServerConfig, MCPTransport

config = MCPConfig(
    enabled=True,
    servers={
        "github": MCPServerConfig(
            name="github",
            transport=MCPTransport.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": "..."},
        )
    },
)
```

## CLI

```bash
haive-mcp discover "database"              # Search 1,960 servers by keyword
haive-mcp discover                          # List all 14 categories
haive-mcp install "postgres"                # Search → plan → approve → connect
haive-mcp install "filesystem" --no-approve # Skip HITL approval
haive-mcp install "github" --format claude  # Output Claude Desktop config
haive-mcp self-query                        # Interactive TUI
haive-mcp transports                        # List transport types
haive-mcp status                            # Show current config
```

## Installer Service

Full pipeline: **search** the database, **plan** with install command extraction + LLM fallback, **approve** via HITL, **install** and verify tools.

```python
from haive.mcp.installer_service import MCPInstallerService

service = MCPInstallerService(
    require_approval=True,           # HITL before install (default)
    # approval_callback=my_func,     # custom approval logic
    # llm_callback=my_llm,           # custom LLM for fallback
)

# Step by step
plan = await service.plan_install("postgres")
# InstallPlan(server_name='Nile Postgres', install_command='npx -y nile-mcp-server',
#             method='readme', confidence=0.9)

approved = await service.approve(plan)    # interactive prompt or callback
result = await service.install(plan)      # connect and verify

# Or all at once
result = await service.search_and_install("filesystem")

# Generate configs for different targets
service.generate_langchain_config("postgres")       # MultiServerMCPClient format
service.generate_claude_desktop_config("postgres")   # mcp.json format
service.generate_mcp_server_config("postgres")       # MCPServerConfig object
```

**Install method cascade:**

| Priority | Method | Confidence | Source |
|----------|--------|------------|--------|
| 1 | README extraction | 90% | Parses `npx`, `uvx`, `pip install` from server READMEs |
| 2 | LLM fallback | 70% | Asks an LLM to derive the command from the README |
| 3 | Pattern fallback | 40% | Guesses from repository name conventions |

## Self-Query Engine

Search the 1,960 server database with ranked results:

```python
from haive.mcp.self_query import MCPSelfQuery

sq = MCPSelfQuery()
print(sq.server_count)                    # 1960

results = sq.search("database")           # ranked by name > category > description
categories = sq.get_categories()          # {'utility': 1262, 'ai_ml': 224, ...}
detail = sq.get_server_detail("postgres") # enriched with README, stars, install cmd
```

## Docker Transport

Run MCP servers in isolated containers:

```python
from haive.mcp.config import MCPServerConfig, MCPTransport

config = MCPServerConfig(
    name="postgres",
    transport=MCPTransport.DOCKER,
    command="mcp/postgres",                          # Docker image
    env={"POSTGRES_HOST": "host.docker.internal"},
    docker_volumes=["/data:/data:ro"],
    docker_network="host",
)
```

## Agents

### IntelligentMCPAgent

Auto-discovers and installs servers based on user needs:

```python
from haive.mcp.agents import IntelligentMCPAgent

agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True,       # analyze requests, find servers automatically
    require_approval=True,    # HITL before installing
)
await agent.setup()

result = await agent.arun({
    "messages": [{"role": "user", "content": "Query my PostgreSQL database"}]
})
# Agent detects need → searches 1,960 servers → asks approval → installs → uses
```

Built-in tools: `discover_mcp_servers`, `install_mcp_server`, `list_mcp_status`, `reload_mcp_server`

### MCPAgent

Production agent with static server configuration. See [examples/basic_mcp_agent.py](examples/basic_mcp_agent.py).

### TransferableMCPAgent

Share tools between agents for multi-agent workflows. See [examples/tool_transfer.py](examples/tool_transfer.py).

## Examples

| Example | Description |
|---------|-------------|
| [`basic_mcp_agent.py`](examples/basic_mcp_agent.py) | Connect to servers with static config |
| [`intelligent_discovery.py`](examples/intelligent_discovery.py) | Auto-discover servers for a task |
| [`dynamic_server_management.py`](examples/dynamic_server_management.py) | Add, monitor, and hot-reload servers |
| [`tool_transfer.py`](examples/tool_transfer.py) | Share MCP tools between agents |
| [`docker_transport.py`](examples/docker_transport.py) | Run servers in Docker containers |
| [`fastmcp_server.py`](examples/fastmcp_server.py) | Build custom MCP servers with FastMCP |
| [`langchain_mcp_adapters.py`](examples/langchain_mcp_adapters.py) | Bridge MCP tools into LangChain/LangGraph |
| [`search_and_install.py`](examples/search_and_install.py) | Full installer pipeline with HITL |

```bash
poetry run python examples/basic_mcp_agent.py
```

## Testing

```bash
poetry run pytest tests/unit/ -v              # 32+ unit tests
poetry run pytest tests/integration/ -v        # integration tests (needs MCP servers)
poetry run pytest tests/unit/ --cov=haive.mcp  # with coverage
```

## Architecture

```
haive-mcp/
├── src/haive/mcp/
│   ├── config.py                # MCPConfig, MCPServerConfig, MCPTransport (stdio/sse/http/docker)
│   ├── manager.py               # MCPManager - server lifecycle, hot-reload, health checks
│   ├── self_query.py            # MCPSelfQuery - ranked search across 1,960 servers
│   ├── installer_service.py     # MCPInstallerService - search → plan → approve → install
│   ├── agents/                  # IntelligentMCPAgent, MCPAgent, TransferableMCPAgent
│   ├── client/                  # Native transports: Stdio, HTTP, SSE, WebSocket, Docker
│   ├── documentation/           # MCPDocumentationLoader - README parsing, install extraction
│   ├── downloader/              # Server download, GitHub mass downloader
│   └── mixins/                  # MCPMixin - add MCP to any agent
├── examples/                    # 8 runnable examples
├── tests/unit/                  # Config, Docker transport, self-query, installer tests
├── data/mcp_servers/            # 1,960 server index + 992 enriched documents
└── configs/                     # YAML environment configs
```

## Configuration

```python
# Transport types
MCPTransport.STDIO            # npx/uvx subprocess (most common)
MCPTransport.SSE              # Server-Sent Events
MCPTransport.STREAMABLE_HTTP  # HTTP streaming
MCPTransport.DOCKER           # Docker container

# Environment variables
# MCP_AUTO_DISCOVER=true
# MCP_REQUIRE_APPROVAL=false
# MCP_HEALTH_CHECK_INTERVAL=30
```

See [.env.example](.env.example) for all available settings.

## References

- [Model Context Protocol](https://modelcontextprotocol.io/) -- specification
- [FastMCP](https://gofastmcp.com/) -- build MCP servers in Python
- [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) -- LangChain bridge
- [MCP Server Registry](https://github.com/wong2/awesome-mcp-servers) -- community servers

## License

MIT
