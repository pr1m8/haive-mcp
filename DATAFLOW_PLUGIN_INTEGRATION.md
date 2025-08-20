# Haive-Dataflow Plugin Integration

**Created**: 2025-08-19
**Purpose**: Explain how MCP plugins integrate with haive-dataflow platform system
**Status**: Active Integration

## 🔌 Plugin System Architecture

Our MCP system uses the **haive-dataflow plugin platform** as its foundation, creating a unified plugin ecosystem across all Haive packages.

### Inheritance Hierarchy

```
haive-dataflow/platform/models.py:
    BasePlatform
        ↓
    PluginPlatform  
        ↓
haive-mcp/plugins/browser_plugin.py:
    MCPBrowserPlugin
```

## 🏗️ Four-Layer Complete Architecture

### Layer 0: Dataflow Platform (Foundation)
**Package**: `haive-dataflow`  
**Location**: `haive.dataflow.platform.models`
**Purpose**: Unified plugin system for all Haive packages

```python
from haive.dataflow.platform.models import BasePlatform, PluginPlatform

# Foundation classes that provide:
# - Platform lifecycle management
# - Standardized configuration
# - Plugin discovery and registration
# - Cross-package plugin communication
```

### Layer 1: Native Protocol Client
**Package**: `haive-mcp`
**Location**: `src/haive/mcp/client/`
**Purpose**: Direct MCP protocol communication

```python
from haive.mcp.client import MCPClient, StdioTransport

# Raw protocol implementation
transport = StdioTransport("npx", ["-y", "@modelcontextprotocol/server-filesystem"])
async with MCPClient(transport) as client:
    tools = await client.list_tools()
```

### Layer 2: MCP Plugin (Management)
**Package**: `haive-mcp`
**Location**: `src/haive/mcp/plugins/browser_plugin.py`
**Purpose**: MCP-specific platform extension

```python
from haive.mcp.plugins import MCPBrowserPlugin

# Inherits full platform capabilities + MCP-specific features
plugin = MCPBrowserPlugin()  # Gets all PluginPlatform features automatically
await plugin.initialize()
servers = plugin.get_servers()
```

### Layer 3: Agent Integration
**Package**: `haive-agents` (future)
**Purpose**: Haive agent framework integration

## 🔄 Cross-Package Integration Flow

### 1. Platform Registration
```python
# haive-dataflow registers the MCP plugin
from haive.dataflow.platform.registry import PlatformRegistry
from haive.mcp.plugins import MCPBrowserPlugin

registry = PlatformRegistry()
registry.register_plugin("mcp_browser", MCPBrowserPlugin)
```

### 2. Plugin Discovery
```python
# Other packages can discover MCP capabilities
available_plugins = registry.list_plugins()
mcp_plugin = registry.get_plugin("mcp_browser")
mcp_servers = await mcp_plugin.get_available_servers()
```

### 3. Inter-Plugin Communication
```python
# Plugins can communicate through the platform
dataflow_plugin = registry.get_plugin("dataflow_processor")
mcp_plugin = registry.get_plugin("mcp_browser")

# MCP plugin provides tools to dataflow
tools = await mcp_plugin.get_tools_for_dataflow()
await dataflow_plugin.register_external_tools("mcp", tools)
```

## 📋 What MCPBrowserPlugin Inherits

### From BasePlatform (haive-dataflow):
- `platform_id`: Unique identifier
- `status`: Platform status management
- `metadata`: Platform metadata
- `lifecycle methods`: initialize(), start(), stop(), cleanup()
- `configuration`: Standardized config handling

### From PluginPlatform (haive-dataflow):
- `entry_point`: Plugin entry point definition
- `routes`: FastAPI route registration
- `priorities`: Plugin loading priorities
- `dependencies`: Plugin dependency management
- `discovery`: Plugin discovery mechanisms

### MCP-Specific Extensions:
- `servers`: MCP server management
- `install_reports`: Installation tracking
- `health_monitoring`: Server health checks
- `bulk_operations`: Mass server operations

## 🎯 Integration Benefits

### 1. **Unified Plugin System**
All Haive packages use the same plugin architecture:
- haive-core: Core platform plugins
- haive-dataflow: Data processing plugins
- haive-mcp: MCP server plugins
- haive-agents: Agent capability plugins
- haive-games: Game environment plugins

### 2. **Cross-Package Communication**
```python
# Example: Dataflow processor uses MCP tools
from haive.dataflow.platform.registry import get_plugin

mcp_plugin = get_plugin("mcp_browser")
dataflow_plugin = get_plugin("dataflow_processor")

# Dataflow can use any MCP server as a processing node
filesystem_tools = await mcp_plugin.get_server_tools("filesystem")
await dataflow_plugin.add_processing_node("mcp_filesystem", filesystem_tools)
```

### 3. **Standardized Configuration**
```python
# All plugins use same config pattern
plugin_config = {
    "mcp_browser": {
        "servers_data_file": "path/to/servers.csv",
        "max_concurrent_connections": 10,
        "health_check_interval": 60
    },
    "dataflow_processor": {
        "max_nodes": 100,
        "processing_timeout": 300
    }
}
```

### 4. **Plugin Discovery**
```python
# Automatic discovery across all packages
from haive.dataflow.platform import discover_all_plugins

plugins = discover_all_plugins()
# Returns plugins from haive-mcp, haive-agents, haive-games, etc.

mcp_plugins = [p for p in plugins if p.category == "mcp"]
agent_plugins = [p for p in plugins if p.category == "agents"]
```

## 🔧 Implementation Example

### Complete Integration Flow

```python
from haive.dataflow.platform.registry import PlatformRegistry
from haive.mcp.plugins import MCPBrowserPlugin
from haive.mcp.client import MCPClient, StdioTransport

# 1. Platform system manages the plugin
registry = PlatformRegistry()
mcp_plugin = MCPBrowserPlugin()

# 2. Plugin inherits all platform capabilities
await mcp_plugin.initialize()  # From BasePlatform
mcp_plugin.register_routes(app)  # From PluginPlatform

# 3. Plugin provides MCP-specific features
servers = await mcp_plugin.discover_servers()  # MCP-specific
config = mcp_plugin.get_server_config("filesystem")  # MCP-specific

# 4. Native client handles protocol
transport = StdioTransport(config.command, config.args)
async with MCPClient(transport) as client:
    tools = await client.list_tools()
    
# 5. Plugin exposes to other packages
registry.register_capability("mcp_tools", tools)
```

### Web Interface Integration

```python
# FastAPI app gets routes from all plugins
from fastapi import FastAPI
from haive.dataflow.platform.web import setup_platform_routes

app = FastAPI()

# Platform automatically registers all plugin routes
setup_platform_routes(app)  # Includes MCP plugin routes

# Routes available:
# /api/platforms/         - Platform management (dataflow)
# /api/mcp/servers/       - MCP server management (mcp plugin)
# /api/agents/            - Agent management (future)
# /api/games/             - Game environments (future)
```

## 🚀 Future Plugin Extensions

### 1. Agent Platform Plugin (haive-agents)
```python
class AgentPlatformPlugin(PluginPlatform):
    """Plugin for agent lifecycle management."""
    
    async def create_mcp_enabled_agent(self, servers: List[str]):
        # Gets MCP tools from MCP plugin
        mcp_plugin = self.registry.get_plugin("mcp_browser")
        tools = await mcp_plugin.get_tools_for_servers(servers)
        
        # Creates agent with MCP tools
        return Agent(tools=tools)
```

### 2. Game Environment Plugin (haive-games)
```python
class GamePlatformPlugin(PluginPlatform):
    """Plugin for game environment management."""
    
    async def create_game_with_mcp_tools(self, game_type: str):
        # Uses MCP tools in game environments
        mcp_plugin = self.registry.get_plugin("mcp_browser")
        tools = await mcp_plugin.get_game_suitable_tools()
        
        return GameEnvironment(type=game_type, external_tools=tools)
```

## 📊 Current Status

✅ **haive-dataflow Platform**: Complete plugin foundation  
✅ **MCP Browser Plugin**: Complete MCP-specific platform extension  
🔄 **Native Protocol Client**: In progress (Phase 2)  
📅 **Agent Integration**: Planned (Phase 4)  
📅 **Cross-Package Discovery**: Planned (Phase 5)  

The **haive-dataflow plugin system** provides the foundation that allows our MCP implementation to integrate seamlessly with the entire Haive ecosystem, while the **native protocol client** provides the actual MCP communication capabilities that the plugin manages and exposes.