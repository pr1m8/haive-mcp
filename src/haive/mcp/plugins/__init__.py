# haive-mcp/src/haive/mcp/plugins/__init__.py
"""
MCP Plugins Module - Phase 2 Implementation

This module provides plugin implementations for the unified MCP platform architecture.
All plugins inherit from PluginPlatform and implement the Pydantic-first design pattern
with intelligent inheritance from our Phase 1 base platform models.

Plugin Architecture:
===================

Base Inheritance Chain:
- BasePlatform (haive-dataflow) - Foundation with core capabilities
- PluginPlatform (haive-dataflow) - Plugin-specific extensions
- MCPBrowserPlugin (this module) - Specialized for our 63 downloaded servers

Key Design Principles:
- Pure Pydantic models (no __init__ methods)
- Intelligent inheritance with platform capabilities
- Real data integration with our download infrastructure
- FastAPI route registration for web interface
- Intelligent caching for performance

Available Plugins:
=================

MCPBrowserPlugin:
- Manages our 63 successfully downloaded MCP servers
- Loads data from CSV files and install reports  
- Provides web interface for server browsing
- Implements intelligent caching with TTL
- Supports filtering by language, stars, and other criteria

Usage Examples:
==============

Basic plugin creation::

    from haive.mcp.plugins import MCPBrowserPlugin
    
    # Create plugin with default configuration
    plugin = MCPBrowserPlugin()
    
    # Initialize plugin (validates data sources)
    await plugin.initialize()
    
    # Get our downloaded servers
    servers = plugin.get_servers()
    print(f"Loaded {len(servers)} downloaded servers")

Custom configuration::

    plugin = MCPBrowserPlugin(
        servers_data_file=Path("custom/path/servers.csv"),
        install_reports_pattern="custom_install_*.json",
        cache_ttl_seconds=600  # 10 minutes
    )

FastAPI integration::

    from fastapi import FastAPI
    
    app = FastAPI()
    plugin = MCPBrowserPlugin()
    
    # Register plugin routes
    plugin.register_routes(app)
    
    # Routes available at /mcp/servers, /mcp/stats, etc.

Server filtering::

    # Get JavaScript servers
    js_servers = plugin.get_servers_by_language("JavaScript")
    
    # Get popular servers (>100 stars)
    popular = plugin.get_servers_by_stars(min_stars=100)
    
    # Get specific server
    server = plugin.get_server_by_name("AgentDeskAI/browser-tools-mcp")

Plugin Statistics:
=================

The plugin provides comprehensive statistics about our downloaded servers:
- Total server count
- Language distribution
- Star count statistics  
- Transport protocol usage
- Cache performance metrics
- Inheritance validation results

Phase 2 Status:
==============

✅ MCPBrowserPlugin implemented with full PluginPlatform inheritance
✅ Real data integration with our CSV and install report files
✅ Intelligent caching system with configurable TTL
✅ FastAPI routes for web interface
✅ Server filtering and search capabilities
✅ Comprehensive statistics and monitoring
✅ Error handling and validation
✅ Documentation and examples

Integration Notes:
=================

This plugin integrates with our existing infrastructure:
- CSV data from scratches/mcp-analysis/mcp_servers_data.csv
- Install reports matching pattern mcp_install_report_*.json
- Uses DownloadedServerInfo models from haive-dataflow
- Inherits all capabilities from PluginPlatform and BasePlatform
- Compatible with the broader haive-dataflow and haive-agp ecosystem

The plugin demonstrates the successful Phase 2 implementation of our unified
MCP platform plan, building on the validated Phase 1 foundation models.
"""

from .browser_plugin import MCPBrowserPlugin

# Export the plugin for external use
__all__ = [
    "MCPBrowserPlugin",
]

# Plugin registry for discovery
AVAILABLE_PLUGINS = {
    "mcp-browser": {
        "class": MCPBrowserPlugin,
        "description": "Browse and manage 63+ downloaded MCP servers",
        "entry_point": "haive.mcp.plugins:MCPBrowserPlugin",
        "routes_prefix": "/mcp",
        "provides_servers": True,
        "provides_discovery": True,
        "provides_health_checks": True,
    }
}

def get_plugin_registry():
    """Get registry of available plugins.
    
    Returns:
        Dictionary mapping plugin names to their configuration
    """
    return AVAILABLE_PLUGINS.copy()

def get_plugin_class(plugin_name: str):
    """Get plugin class by name.
    
    Args:
        plugin_name: Name of the plugin to retrieve
        
    Returns:
        Plugin class if found, None otherwise
    """
    plugin_info = AVAILABLE_PLUGINS.get(plugin_name)
    return plugin_info["class"] if plugin_info else None