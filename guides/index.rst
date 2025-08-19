Haive MCP Guides
================

Welcome to the Haive MCP (Model Context Protocol) guides! This section provides comprehensive tutorials and examples for working with our MCP platform architecture.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   quickstart
   installation
   basic-usage

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts

   platform-architecture
   pydantic-patterns
   server-management

.. toctree::
   :maxdepth: 2
   :caption: Plugins

   plugin-development
   mcp-browser-plugin
   custom-plugins

.. toctree::
   :maxdepth: 2
   :caption: Advanced Usage

   fastapi-integration
   caching-strategies
   real-world-examples

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics

   performance-optimization
   troubleshooting

Overview
--------

The Haive MCP package provides a Pydantic-first platform architecture for managing Model Context Protocol servers. Key features include:

* **Pure Pydantic Design** - No ``__init__`` methods, comprehensive validation
* **Intelligent Inheritance** - Platform-based architecture with ``BasePlatform`` → ``PluginPlatform``
* **Real Component Testing** - No mocks, validation with actual data
* **FastAPI Integration** - Built-in web API support
* **Server Management** - Handle 63+ downloaded MCP servers

Quick Start
-----------

.. code-block:: python

   from haive.mcp.plugins import MCPBrowserPlugin
   from pathlib import Path

   # Create MCP browser plugin
   plugin = MCPBrowserPlugin(
       server_directory=Path("/home/will/Downloads/mcp_servers"),
       cache_ttl=3600
   )

   # Load and browse servers
   servers = await plugin.load_servers()
   print(f"Found {len(servers)} MCP servers")

   # Get FastAPI router
   router = plugin.get_router()

Architecture Principles
-----------------------

Our MCP architecture follows these key principles:

1. **Pydantic-First Design**

   .. code-block:: python

      class MCPBrowserPlugin(PluginPlatform):
          """No __init__ method - pure Pydantic validation"""
          
          model_config = ConfigDict(
              arbitrary_types_allowed=True
          )
          
          server_directory: Path = Field(...)
          cache_ttl: int = Field(default=3600)

2. **Platform Inheritance**

   .. code-block:: python

      # Platform hierarchy
      BasePlatform (haive-dataflow)
          ↓
      PluginPlatform (haive-dataflow)  
          ↓
      MCPBrowserPlugin (haive-mcp)

3. **Server Information Models**

   .. code-block:: python

      BaseServerInfo → MCPServerInfo → DownloadedServerInfo

Community and Support
---------------------

* **Documentation**: :doc:`../README` 
* **Examples**: See :doc:`real-world-examples`
* **Testing**: Follow :doc:`testing-guide`
* **Issues**: Report problems in the main Haive repository

Next Steps
----------

1. Follow the :doc:`quickstart` guide to get up and running
2. Read about :doc:`platform-architecture` to understand the design
3. Try the :doc:`mcp-browser-plugin` tutorial
4. Explore :doc:`real-world-examples` for advanced usage