# MCP Integration with haive-agents

This document describes the type-checked MCP (Model Context Protocol) integration with haive-agents.

## Overview

The MCP integration provides a seamless way to extend haive agents with MCP server capabilities. It includes:

- **Type-safe configuration** using Pydantic models
- **Dynamic server discovery** from multiple sources
- **Automatic tool registration** with agents
- **Component registry integration** for discoverability
- **Graceful error handling** and fallbacks

## Architecture

### Core Components

1. **MCPMixin** (`mixins/mcp_mixin.py`)

   - Provides MCP capabilities to any agent
   - Handles server connections and tool discovery
   - Integrates with component registry
   - Manages health monitoring and failures

2. **MCPAgent** (`agents/mcp_agent.py`)

   - Ready-to-use agent with MCP support
   - Extends SimpleAgent with MCPMixin
   - Provides convenience methods for common patterns

3. **MCPServerDiscovery** (`discovery/server_discovery.py`)

   - Discovers MCP servers from various sources
   - Filters based on capabilities and categories
   - Creates configurations dynamically

4. **MCPServerAnalyzer** (`discovery/analyzer.py`)
   - Analyzes objects to extract MCP configurations
   - Integrates with component discovery system
   - Supports multiple configuration formats

## Usage Examples

### Basic MCP Agent

```python
from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig

# Configure MCP
mcp_config = MCPConfig(
    enabled=True,
    servers={
        "filesystem": MCPServerConfig(
            name="filesystem",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            capabilities=["file_read", "file_write"]
        )
    }
)

# Create agent
agent = MCPAgent(
    engine=my_engine,
    mcp_config=mcp_config,
    name="mcp_assistant"
)

# Use the agent - MCP tools are automatically available
result = await agent.arun({
    "messages": [{"role": "user", "content": "List files in current directory"}]
})
```

### Using Convenience Methods

```python
# Create agent with multiple MCP servers
agent = MCPAgent.create_with_mcp_servers(
    engine=engine,
    server_configs={
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"]
        },
        "github": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": github_token}
        }
    }
)
```

### Dynamic Server Discovery

```python
from haive.mcp.discovery import MCPServerDiscovery

# Discover available servers
discovery = MCPServerDiscovery()
servers = await discovery.discover_all()

# Create agent with discovered servers
mcp_config = discovery.create_mcp_config()
agent = MCPAgent(engine=engine, mcp_config=mcp_config)
```

### Adding MCP to Existing Agents

```python
from haive.agents.simple import SimpleAgent
from haive.mcp.mixins import MCPMixin

class MyCustomAgent(MCPMixin, SimpleAgent):
    """Custom agent with MCP support."""

    async def setup(self):
        await super().setup()
        # MCP tools are now available
        if self._mcp_tools:
            print(f"Loaded {len(self._mcp_tools)} MCP tools")
```

## Configuration

### MCPConfig Structure

```python
MCPConfig(
    enabled=True,                    # Enable/disable MCP
    auto_discover=True,             # Auto-discover servers
    lazy_init=True,                 # Initialize on-demand
    servers={...},                  # Server configurations
    discovery_paths=[               # Paths to search
        "~/.mcp/servers",
        ".mcp/servers"
    ],
    categories=["dev", "util"],     # Filter by category
    required_capabilities=["file"]   # Required capabilities
)
```

### MCPServerConfig Options

```python
MCPServerConfig(
    name="server_name",
    transport="stdio",              # stdio, sse, streamable_http
    command="npx",                  # Command to run
    args=["-y", "package"],        # Command arguments
    url="http://...",              # For HTTP transports
    env={"KEY": "value"},          # Environment variables
    capabilities=["file_ops"],      # Server capabilities
    category="filesystem",          # Server category
    timeout=30,                     # Connection timeout
    retry_attempts=3,              # Retry on failure
    health_check_interval=60       # Health check interval
)
```

## Component Registry Integration

The MCP integration automatically registers servers and tools with the component registry:

```python
from haive.core.utils.component_discovery import create_component_registry

# MCP servers and tools are automatically registered
registry = create_component_registry()

# Search for MCP components
mcp_servers = registry.search_components(
    query="file operations",
    component_types=["mcp"]
)

# Find MCP tools
mcp_tools = registry.search_components(
    query="github",
    component_types=["tool"],
    tags=["mcp"]
)
```

## Advanced Features

### Capability-Based Tool Discovery

```python
# Find tools by capability
file_tools = await agent.discover_tools_by_capability("file_read")
web_tools = await agent.discover_tools_by_capability("web_fetch")
```

### Health Monitoring

```python
# Get MCP status
status = agent.get_mcp_status()
# {
#     "enabled": True,
#     "initialized": True,
#     "connected_servers": ["filesystem", "github"],
#     "failed_servers": [],
#     "tool_count": 15
# }

# Refresh failed servers
await agent.refresh_mcp_servers()
```

### Resource and Prompt Access

```python
# Get resources from MCP server
resources = await agent.get_mcp_resources("github", uris=["repo:owner/name"])

# Get prompts from MCP server
prompt = await agent.get_mcp_prompt("assistant", "greeting", {"name": "User"})
```

## Error Handling

The integration includes robust error handling:

- Failed server connections are tracked
- Tools from failed servers are excluded
- Retry logic for transient failures
- Graceful degradation when MCP is unavailable

## Testing

Run tests with:

```bash
pytest packages/haive-mcp/tests/test_mcp_integration.py
```

## Dependencies

- `langchain-mcp-adapters`: For MCP client functionality
- `mcp` or `fastmcp`: Core MCP implementation
- `pydantic`: For configuration models

Install with:

```bash
pip install langchain-mcp-adapters
```

## Future Enhancements

1. **Hooks System**: Implement proper hooks for tool discovery
2. **Server Templates**: Pre-configured server templates
3. **Authentication**: Enhanced authentication support
4. **Monitoring**: Detailed metrics and monitoring
5. **Caching**: Tool and resource caching
