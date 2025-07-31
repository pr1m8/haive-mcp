# MCP Discovery Module

Automatic discovery and analysis of MCP servers from various sources.

## Overview

The discovery module provides comprehensive MCP server discovery capabilities:
- npm package discovery (`@modelcontextprotocol/*`)
- PyPI package discovery (`mcp-*`)
- GitHub repository discovery
- Local server discovery
- Server capability analysis

## Key Components

### MCPServerDiscovery

Main discovery class for finding MCP servers.

```python
from haive.mcp.discovery import MCPServerDiscovery

discovery = MCPServerDiscovery()

# Discover all servers
servers = await discovery.discover_all()

# Discover from specific source
npm_servers = await discovery.discover_npm_servers()
pypi_servers = await discovery.discover_pypi_servers()

# Filter by capability
file_servers = discovery.get_servers_by_capability("file_operations")
```

### MCPServerAnalyzer

Analyzes MCP servers to extract capabilities and metadata.

```python
from haive.mcp.discovery import MCPServerAnalyzer

analyzer = MCPServerAnalyzer()

# Analyze a server
info = await analyzer.analyze_server("filesystem-server")
print(f"Capabilities: {info['capabilities']}")
print(f"Tools: {info['tools']}")
```

## Installation

This module is part of the `haive-mcp` package. Install it using:

```bash
poetry add haive-mcp
```

## Usage Examples

### Basic Discovery

```python
from haive.mcp.discovery import discover_servers

# Discover all available servers
servers = await discover_servers()

for server in servers:
    print(f"{server.name}: {server.description}")
    print(f"  Transport: {server.transport}")
    print(f"  Capabilities: {', '.join(server.capabilities)}")
```

### Filtered Discovery

```python
from haive.mcp.discovery import MCPServerDiscovery

discovery = MCPServerDiscovery()

# Find servers with specific capabilities
code_servers = discovery.get_servers_by_capability("code_analysis")
file_servers = discovery.get_servers_by_capability("file_operations")

# Find servers by category
dev_servers = discovery.get_servers_by_category("development")
```

## API Reference

For detailed API documentation, see the module docstrings and Sphinx documentation.

## See Also

- [MCP Manager](../manager.py) - Server lifecycle management
- [MCP Config](../config.py) - Configuration models
- [MCP Agents](../agents/) - MCP-enabled agents
