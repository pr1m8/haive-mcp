# AGENTS.md - haive-mcp Architecture & Agent Guide

## What is haive-mcp?

haive-mcp is a Python package that connects AI agents to external tools via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It provides:

- A **pre-indexed database of 1,960+ MCP servers** with README parsing and install command extraction
- An **installer service** that searches, plans, approves (HITL), and connects to servers
- **Multiple agent types** for different use cases (auto-discovery, static config, tool sharing)
- **4 transport types**: stdio (npx/uvx), SSE, HTTP streaming, Docker containers
- **Config generation** for langchain-mcp-adapters, Claude Desktop, and native haive-mcp format
- A **Rich TUI** for interactive server browsing and installation

## How Everything Links Together

```
                          ┌─────────────────────┐
                          │    User / Agent      │
                          └──────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
              │    TUI     │   │    CLI     │   │  Python   │
              │  (Rich)    │   │  (Click)   │   │   API     │
              └─────┬──────┘   └─────┬──────┘   └─────┬─────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  MCPInstallerService │
                          │  (search → plan →   │
                          │   approve → install) │
                          └──────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼──────┐
              │MCPSelfQuery│   │   Doc      │   │  LLM       │
              │ (ranked    │   │  Loader    │   │  Fallback   │
              │  search)   │   │(README     │   │ (derive     │
              │            │   │ parsing)   │   │  install)   │
              └─────┬──────┘   └─────┬──────┘   └────────────┘
                    │                │
              ┌─────▼────────────────▼─────┐
              │   Server Database          │
              │   1,960 servers (JSON)     │
              │   992 enriched docs        │
              └────────────────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  Config Generation   │
                          │  ├── MCPServerConfig │
                          │  ├── langchain fmt   │
                          │  └── Claude Desktop  │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  MCP Connection      │
                          │  ├── StdioTransport  │
                          │  ├── SSE/HTTP        │
                          │  ├── DockerTransport │
                          │  └── langchain-mcp   │
                          │      -adapters       │
                          └─────────────────────┘
```

## Agents

### IntelligentMCPAgent

**Purpose**: Auto-discovers and installs MCP servers based on what the user needs.

**How it works**:
1. User sends a message ("Query my PostgreSQL database")
2. Agent uses LLM to analyze what capabilities are needed (`["database"]`)
3. Searches the 1,960 server database via `MCPInstallerService`
4. Plans installation with install command extraction from README
5. HITL approval (configurable -- auto-approve or interactive)
6. Connects and verifies tools are available
7. Executes the original task with the new tools

**Built-in tools**: `discover_mcp_servers`, `install_mcp_server`, `list_mcp_status`, `reload_mcp_server`

**File**: `src/haive/mcp/agents/intelligent_mcp_agent.py`

### MCPAgent

**Purpose**: Production agent with static, pre-configured MCP servers.

**When to use**: You know exactly which servers you need upfront.

**File**: `src/haive/mcp/agents/mcp_agent.py`

### TransferableMCPAgent

**Purpose**: Share MCP tools between agents in multi-agent workflows.

**File**: `src/haive/mcp/agents/transferable_mcp_agent.py`

### BasicMCPAgent

**Purpose**: Simplified agent for basic MCP usage.

**File**: `src/haive/mcp/agents/basic_mcp_agent.py`

### DocumentationAgent

**Purpose**: Agent specialized for working with MCP server documentation.

**File**: `src/haive/mcp/agents/documentation_agent.py`

## Core Components

### MCPInstallerService (`installer_service.py`)

The main orchestrator. Full pipeline:

```
search(query) → plan_install(name) → approve(plan) → install(plan)
```

**Install method cascade**:
1. README extraction (90% confidence) -- parses `npx`, `uvx`, `pip install`
2. LLM fallback (70% confidence) -- asks an LLM to derive the command
3. Pattern fallback (40% confidence) -- guesses from repo name

**Config output**: `generate_langchain_config()`, `generate_claude_desktop_config()`, `generate_mcp_server_config()`

### MCPSelfQuery (`self_query.py`)

Ranked search engine over the 1,960 server database. Scores: name match (50) > category (30) > description (20).

### MCPDocumentationLoader (`documentation/doc_loader.py`)

Loads server data from `ALL_MCP_SERVERS_COMPLETE.json` (1,960 entries) and enriches with individual document files from `documents/` (992 files with full READMEs, stars, descriptions).

### MCPManager (`manager.py`)

Server lifecycle management: add, remove, reload, health check, get tools.

### Config (`config.py`)

Pydantic models: `MCPConfig`, `MCPServerConfig`, `MCPTransport` (stdio, sse, streamable_http, docker).

### Transports (`client/transport.py`)

`StdioTransport`, `HttpTransport`, `SseTransport`, `WebSocketTransport`, `DockerTransport` -- all implement the same async interface.

## Data

```
data/mcp_servers/
├── ALL_MCP_SERVERS_COMPLETE.json   # 1,960 servers (5.5 MB index)
├── organized_servers.json          # Alternative organized format (6.8 MB)
├── documents/                      # 992 individual server docs with READMEs
├── processed/                      # 1,000 processed docs
└── raw_readmes/                    # 949 raw README files
```

## CLI & TUI

```bash
haive-mcp discover "database"        # Search servers
haive-mcp install "postgres"         # Full install pipeline
haive-mcp self-query                 # Interactive Rich TUI
haive-mcp transports                 # List transport types
haive-mcp status                     # Show config
```

The TUI (`self-query`) is a navigable Rich interface with numbered menus:
1. Search → table → pick → detail panel → install?
2. Browse categories → pick → servers → pick → detail
3. Install → search → pick → plan → confirm → connect
4. Generate config → search → pick → langchain + Claude JSON

## Dependencies

| Package | Purpose |
|---------|---------|
| `mcp` | Official MCP SDK |
| `fastmcp` | Build custom MCP servers |
| `langchain-mcp-adapters` | Bridge MCP tools to LangChain |
| `langchain-mcp-tools` | Additional MCP tool utilities |
| `rich` | TUI rendering |
| `click` | CLI framework |
| `pydantic` | Config validation |
| `aiohttp` | HTTP client (GitHub README fetching) |

## Testing

54 unit tests covering config, Docker transport, self-query, installer service, and install command derivation.

```bash
poetry run pytest tests/unit/ -v
```

## File Map

```
src/haive/mcp/
├── __init__.py              # Package exports
├── __main__.py              # CLI entry point (haive-mcp)
├── config.py                # MCPConfig, MCPServerConfig, MCPTransport
├── manager.py               # MCPManager - server lifecycle
├── self_query.py            # MCPSelfQuery - ranked search
├── installer_service.py     # MCPInstallerService - full install pipeline
├── tui.py                   # Rich TUI
├── agents/
│   ├── intelligent_mcp_agent.py   # Auto-discovery + HITL
│   ├── mcp_agent.py               # Static config agent
│   ├── transferable_mcp_agent.py  # Tool sharing
│   ├── basic_mcp_agent.py         # Simplified agent
│   └── documentation_agent.py     # Doc-aware agent
├── client/
│   ├── transport.py         # Stdio, HTTP, SSE, WebSocket, Docker transports
│   ├── mcp_client.py        # Native MCP client
│   ├── connection.py        # Connection management
│   ├── protocol.py          # MCP protocol implementation
│   └── exceptions.py        # Client exceptions
├── documentation/
│   └── doc_loader.py        # Load + enrich + extract from server database
├── discovery/               # Server discovery system
├── downloader/              # Server download + installation
├── installers/              # Installation strategies (npm, pip, git, docker)
├── mixins/                  # MCPMixin for existing agents
├── plugins/                 # Plugin system (browser plugin)
├── registry/                # Server config converter
├── servers/                 # Server management infrastructure
├── tools/                   # Server selector, tester, AI assistant
└── utils/                   # Utilities
```
