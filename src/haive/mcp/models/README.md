# MCP Models Module

This module contains the Pydantic models for MCP (Model Context Protocol) server information and management.

## Server Information Hierarchy

Our MCP models follow a clear inheritance hierarchy:

```
BaseServerInfo (from haive-dataflow)
    ↓
MCPServerInfo (MCP-specific metadata)
    ↓
DownloadedServerInfo (local installation details)
```

## Models

### MCPServerInfo

Extends BaseServerInfo with MCP-specific metadata:

```python
from haive.mcp.models import MCPServerInfo

server = MCPServerInfo(
    name="postgres-server",
    description="PostgreSQL MCP server",
    version="1.2.0",
    capabilities=["database", "sql", "queries"],
    mcp_version="0.1.0",
    transport_types=["stdio", "sse"],
    command_template="npx -y @modelcontextprotocol/server-postgres {connection_string}"
)
```

### DownloadedServerInfo

Extends MCPServerInfo with local installation details:

```python
from haive.mcp.models import DownloadedServerInfo
from pathlib import Path
from datetime import datetime

downloaded_server = DownloadedServerInfo(
    name="postgres-server",
    description="PostgreSQL MCP server",
    version="1.2.0",
    capabilities=["database", "sql"],
    
    # Local installation details
    local_path=Path("/home/will/Downloads/mcp_servers/postgres-server"),
    file_size=1024000,  # bytes
    installed_date=datetime.now(),
    download_source="npm",
    is_verified=True
)
```

## Usage Examples

### Creating Server Information

```python
from haive.mcp.models import MCPServerInfo, DownloadedServerInfo
from pathlib import Path

# Basic MCP server info
mcp_server = MCPServerInfo(
    name="brave-search",
    description="Brave Search MCP server",
    version="1.0.0",
    capabilities=["search", "web", "research"],
    mcp_version="0.1.0",
    transport_types=["stdio"],
    command_template="npx -y @modelcontextprotocol/server-brave-search"
)

# Downloaded server with local details
downloaded = DownloadedServerInfo(
    **mcp_server.model_dump(),  # Inherit all MCP fields
    local_path=Path("/downloads/brave-search"),
    file_size=512000,
    download_source="npm"
)
```

### Validation and Serialization

```python
# Pydantic validation
try:
    server = MCPServerInfo(
        name="invalid server",  # Will be cleaned
        capabilities=["AI", "Database"]  # Will be normalized
    )
    print(f"Validated name: {server.name}")  # "invalid-server"
    print(f"Capabilities: {server.capabilities}")  # ["ai-tools", "database"]
except ValidationError as e:
    print(f"Validation failed: {e}")

# Serialization
server_dict = server.model_dump()
server_json = server.model_dump_json()

# Deserialization
restored_server = MCPServerInfo.model_validate(server_dict)
```

### Working with Collections

```python
from typing import List

# Type-safe collections
servers: List[DownloadedServerInfo] = []

# Add servers with validation
for server_data in raw_server_list:
    try:
        server = DownloadedServerInfo.model_validate(server_data)
        servers.append(server)
    except ValidationError:
        continue  # Skip invalid servers

# Filter and search
ai_servers = [s for s in servers if "ai-tools" in s.capabilities]
postgres_servers = [s for s in servers if "postgres" in s.name.lower()]
```

## Validation Features

### Name Normalization

Server names are automatically normalized:
- Spaces → hyphens
- Uppercase → lowercase
- Special characters removed

```python
server = MCPServerInfo(name="My Server Name!")
print(server.name)  # "my-server-name"
```

### Capability Standardization

Capabilities are mapped to standard categories:

```python
server = MCPServerInfo(
    name="test",
    capabilities=["AI", "Database", "Web Search"]
)
print(server.capabilities)  # ["ai-tools", "database", "web"]
```

### Path Validation

Local paths are validated and normalized:

```python
downloaded = DownloadedServerInfo(
    name="test",
    local_path="~/Downloads/server"  # Expands to absolute path
)
print(downloaded.local_path)  # Path("/home/user/Downloads/server")
```

## Factory Methods

### From Package.json

```python
# Create from npm package.json
server = MCPServerInfo.from_package_json(
    package_json_path=Path("node_modules/@server/package.json")
)
```

### From Directory Scan

```python
# Create DownloadedServerInfo from directory
server = DownloadedServerInfo.from_directory(
    Path("/downloads/mcp_servers/postgres-server")
)
```

## Integration with Platform

These models integrate with our platform architecture:

```python
from haive.mcp.plugins import MCPBrowserPlugin

# Plugin uses these models internally
plugin = MCPBrowserPlugin()
servers: List[DownloadedServerInfo] = await plugin.load_servers()

# Type-safe operations
for server in servers:
    print(f"{server.name}: {len(server.capabilities)} capabilities")
    if server.is_verified:
        print(f"  Installed: {server.installed_date}")
```

## Related Documentation

- [Platform Base Models](../../dataflow/platform/models/README.md) - BaseServerInfo and platform inheritance
- [MCPBrowserPlugin](../plugins/README.md) - Plugin using these models
- [Architecture Overview](../../../docs/source/architecture.rst) - Pydantic-first design principles