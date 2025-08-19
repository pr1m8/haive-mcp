# MCPBrowserPlugin Module

This module contains the MCPBrowserPlugin for managing and browsing our 63+ downloaded MCP servers.

## Overview

The MCPBrowserPlugin inherits from PluginPlatform and provides a comprehensive FastAPI-based interface for:
- Browsing downloaded MCP servers
- Filtering by categories and capabilities
- Caching server lists for performance
- Managing server metadata

## Usage

### Basic Plugin Creation

```python
from haive.mcp.plugins import MCPBrowserPlugin
from pathlib import Path

# Create plugin instance
plugin = MCPBrowserPlugin(
    server_directory=Path("/home/will/Downloads/mcp_servers"),
    cache_ttl=3600  # 1 hour cache
)

# Get FastAPI router for integration
router = plugin.get_router()
```

### Loading and Browsing Servers

```python
# Load all servers from directory
servers = await plugin.load_servers()
print(f"Found {len(servers)} MCP servers")

# Filter by category
ai_servers = await plugin.filter_by_category("ai-tools")
database_servers = await plugin.filter_by_category("database")

# Search servers
results = await plugin.search_servers("postgres")
```

### FastAPI Integration

```python
from fastapi import FastAPI

app = FastAPI()

# Create and mount plugin
plugin = MCPBrowserPlugin()
app.include_router(plugin.get_router(), prefix="/mcp")

# Available endpoints:
# GET /mcp/servers - List all servers
# GET /mcp/servers/{server_name} - Get specific server
# GET /mcp/categories - List categories
# GET /mcp/search?q=query - Search servers
```

## Architecture

The plugin follows Pydantic-first design principles:

```python
class MCPBrowserPlugin(PluginPlatform):
    """No __init__ method - pure Pydantic validation"""
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True  # For FastAPI router
    )
    
    # Configuration fields
    server_directory: Path = Field(...)
    cache_ttl: int = Field(default=3600)
    
    # Internal state (excluded from serialization)
    cached_servers: Optional[List[DownloadedServerInfo]] = Field(
        default=None,
        exclude=True
    )
```

## Server Information Hierarchy

The plugin works with our server information hierarchy:

1. **BaseServerInfo** - Common server properties
2. **MCPServerInfo** - MCP-specific metadata (capabilities, version)
3. **DownloadedServerInfo** - Local installation details (path, size, installed date)

## Caching Strategy

The plugin implements intelligent caching:
- Server lists are cached with configurable TTL
- Cache invalidates on directory changes
- Manual cache refresh available via `refresh_cache()`

## Factory Methods

The plugin provides factory methods for real data:

```python
# Create from bulk installer results
plugin = MCPBrowserPlugin.from_installer_results(
    installer_results,
    base_directory=Path("/home/will/Downloads/mcp_servers")
)

# Create from existing directory scan
plugin = MCPBrowserPlugin.from_directory_scan(
    Path("/home/will/Downloads/mcp_servers")
)
```

## Testing

See `test_plugin_with_real_data.py` for comprehensive examples using simulated real server data.

## Related Documentation

- [MCP Platform Models](../models/README.md) - Server information models
- [Platform Base Classes](../../platform/models/README.md) - BasePlatform and PluginPlatform
- [Architecture Overview](../../../docs/source/architecture.rst) - Pydantic-first design