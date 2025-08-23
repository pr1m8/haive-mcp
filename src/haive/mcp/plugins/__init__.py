"""MCP Plugins Module.

This module provides plugin implementations for the unified MCP platform architecture.
All plugins inherit from PluginPlatform and implement the Pydantic-first design pattern
with intelligent inheritance from our Phase 1 base platform models.

Plugin Architecture
-------------------

Base Inheritance Chain
~~~~~~~~~~~~~~~~~~~~~~
- **BasePlatform** (haive-dataflow) - Foundation with core capabilities
- **PluginPlatform** (haive-dataflow) - Plugin-specific enhancements
- **MCPBrowserPlugin** (haive-mcp) - Browser automation plugin

Key Features
~~~~~~~~~~~~
- **Pydantic-First Design**: Full type safety and validation
- **Intelligent Inheritance**: Automatic capability composition
- **Phase 2 Implementation**: Advanced plugin functionality

Available Plugins
-----------------

Browser Plugin
~~~~~~~~~~~~~~
- :class:`MCPBrowserPlugin` - Browser automation and web interaction
- **Features**: Page navigation, element interaction, screenshot capture
- **Integration**: Works with Playwright and Selenium

Plugin Registry
~~~~~~~~~~~~~~~
- :func:`get_plugin_registry` - Get available plugin registry
- :func:`get_plugin_class` - Load plugin class by name

.. note::
   This is a Phase 2 implementation focusing on advanced plugin capabilities
   with full Pydantic integration and intelligent inheritance patterns.
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