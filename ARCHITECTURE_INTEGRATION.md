# MCP Architecture Integration Guide

**Created**: 2025-08-19
**Purpose**: Explain how the native protocol client integrates with existing plugin system
**Status**: Integration Design

## 🏗️ Three-Layer Architecture

Our MCP system has three distinct but integrated layers:

### Layer 1: Native Protocol Client (NEW - Phase 2)
**Location**: `src/haive/mcp/client/`
**Purpose**: Direct MCP protocol communication

```python
# Native protocol client - talks directly to MCP servers
from haive.mcp.client import MCPClient, StdioTransport

transport = StdioTransport("npx", ["-y", "@modelcontextprotocol/server-filesystem"])
async with MCPClient(transport) as client:
    tools = await client.list_tools()
    result = await client.call_tool("read_file", {"path": "/etc/hosts"})
```

**Responsibilities**:
- JSON-RPC protocol implementation
- Transport management (STDIO, HTTP, WebSocket)
- Connection lifecycle
- Raw tool execution
- Capability negotiation

### Layer 2: Browser Plugin (EXISTING - Management Layer) 
**Location**: `src/haive/mcp/plugins/browser_plugin.py`
**Purpose**: Web-based server management

```python
# Browser plugin - manages server discovery and health
from haive.mcp.plugins import MCPBrowserPlugin

plugin = MCPBrowserPlugin()
await plugin.load_downloaded_servers()  # Load our 63 servers
servers = plugin.get_available_servers()
health = await plugin.check_server_health("filesystem")
```

**Responsibilities**:
- Server registry management
- Installation tracking
- Health monitoring
- Web interface (FastAPI)
- Bulk operations UI

### Layer 3: Agent Integration (FUTURE - Phase 4)
**Location**: `src/haive/mcp/agents/` (enhanced)
**Purpose**: Haive agent framework integration

```python
# Agent integration - exposes MCP tools to agents
from haive.mcp.agents import MCPEnabledAgent

agent = MCPEnabledAgent(
    name="research_agent",
    mcp_servers=["filesystem", "github", "web_search"]
)
# Agent automatically gets tools from all MCP servers
result = await agent.arun("Search web for AI news and save to file")
```

**Responsibilities**:
- LangChain tool wrapping
- Agent tool registration
- Multi-server coordination
- State management

## 🔄 Integration Flow

### How the Layers Work Together

```python
# 1. Browser Plugin discovers available servers
browser = MCPBrowserPlugin()
available_servers = await browser.discover_installed_servers()

# 2. Native Client connects to specific servers
for server_config in available_servers:
    transport = StdioTransport(server_config.command, server_config.args)
    client = MCPClient(transport)
    await client.initialize()
    
    # 3. Agent Integration uses the client
    tools = await client.list_tools()
    agent.register_mcp_tools(server_config.name, tools, client)
```

### Data Flow

1. **Installation**: Browser Plugin manages server installation via bulk installer
2. **Discovery**: Browser Plugin discovers installed servers and their configs
3. **Connection**: Native Client establishes protocol connections
4. **Tool Exposure**: Agent Integration wraps MCP tools as LangChain tools
5. **Execution**: Agents call tools via Native Client protocol layer

## 📁 File Organization

```
src/haive/mcp/
├── client/                    # Layer 1: Native Protocol
│   ├── __init__.py
│   ├── mcp_client.py         # Main client class
│   ├── protocol.py           # MCP protocol implementation
│   ├── transport.py          # Transport layer (STDIO, HTTP, etc.)
│   └── exceptions.py         # Protocol exceptions
│
├── plugins/                   # Layer 2: Management
│   ├── __init__.py
│   └── browser_plugin.py     # Server management plugin
│
├── agents/                    # Layer 3: Agent Integration
│   ├── __init__.py
│   ├── mcp_agent.py          # Basic MCP-enabled agent
│   └── intelligent_mcp_agent.py  # Auto-discovery agent
│
├── manager.py                 # High-level orchestration
├── config.py                  # Configuration models
└── installer/                 # Installation management
    └── bulk_installer.py
```

## 🎯 Integration Examples

### Example 1: Plugin → Client Integration

```python
from haive.mcp.plugins import MCPBrowserPlugin
from haive.mcp.client import MCPClient, StdioTransport

# Browser plugin provides server discovery
plugin = MCPBrowserPlugin()
filesystem_config = await plugin.get_server_config("filesystem")

# Native client handles actual communication
transport = StdioTransport(
    command=filesystem_config.command,
    args=filesystem_config.args
)

async with MCPClient(transport) as client:
    tools = await client.list_tools()
    result = await client.call_tool("read_file", {"path": "/tmp/test.txt"})
```

### Example 2: Full Stack Integration

```python
from haive.mcp.manager import MCPManager  # High-level orchestrator

# MCPManager coordinates all layers
manager = MCPManager()

# Layer 2: Discovery and health checks
await manager.discover_servers()
health_report = await manager.health_check_all()

# Layer 1: Protocol connections
filesystem_client = await manager.get_client("filesystem")
github_client = await manager.get_client("github")

# Layer 3: Agent integration
research_agent = await manager.create_agent(
    name="research_agent",
    servers=["filesystem", "github", "web_search"]
)

# Agent now has tools from all three servers
result = await research_agent.arun("Clone repo X, analyze code, save report")
```

### Example 3: Plugin Web Interface → Client Actions

```python
# FastAPI route in browser plugin triggers client actions
from fastapi import APIRouter
from haive.mcp.client import MCPClient, StdioTransport

router = APIRouter()

@router.post("/api/servers/{server_name}/tools/{tool_name}/call")
async def call_tool_via_api(server_name: str, tool_name: str, args: dict):
    # Plugin gets server config
    config = await browser_plugin.get_server_config(server_name)
    
    # Native client executes the tool
    transport = StdioTransport(config.command, config.args)
    async with MCPClient(transport) as client:
        result = await client.call_tool(tool_name, args)
        
    return {"result": result}
```

## 🚀 Benefits of This Architecture

### 1. **Separation of Concerns**
- **Protocol**: Pure MCP implementation
- **Management**: Installation, discovery, health
- **Integration**: Agent framework binding

### 2. **Flexibility**
- Can use native client without web interface
- Can manage servers without running them
- Can run specific MCP tools without full agent

### 3. **Scalability**
- Protocol client handles multiple transports
- Plugin manages hundreds of servers
- Agent integration supports complex workflows

### 4. **Maintainability**
- Clear boundaries between layers
- Each layer can be tested independently
- Easy to add new features at appropriate layer

## 🔄 Current Status (Phase 2)

✅ **Layer 2 (Plugin)**: Complete - browser plugin working
🔄 **Layer 1 (Client)**: In Progress - native protocol client
📅 **Layer 3 (Agent)**: Planned - Phase 4

### What I'm Building Now

The **Native Protocol Client** (Layer 1) that will:
- Replace the current LangChain MCP adapter dependency
- Provide direct MCP protocol communication
- Support multiple transports (STDIO, HTTP, WebSocket)
- Handle capability negotiation
- Manage connection lifecycle

This will be used by both the Browser Plugin (for health checks and tool discovery) and the Agent Integration (for actual tool execution).

## 🎯 Next Steps

1. **Complete Native Client** - Finish MCPClient implementation
2. **Integration Testing** - Test client with real MCP servers
3. **Plugin Integration** - Update browser plugin to use native client
4. **Agent Integration** - Phase 4 implementation

The plugin doesn't "come into" the protocol client - rather, the protocol client **supports** the plugin by providing the low-level communication that the plugin's web interface and management features need.