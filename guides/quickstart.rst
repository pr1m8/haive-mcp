Quick Start Guide
================

This guide will get you up and running with Haive MCP in 5 minutes.

Installation
------------

Install the haive-mcp package:

.. code-block:: bash

   poetry add haive-mcp
   # or
   pip install haive-mcp

Basic Usage
-----------

Creating Your First MCP Plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.plugins import MCPBrowserPlugin
   from pathlib import Path

   # Create MCP browser plugin
   plugin = MCPBrowserPlugin(
       server_directory=Path("/home/will/Downloads/mcp_servers"),
       cache_ttl=3600  # 1 hour cache
   )

   print(f"Created plugin: {plugin.name}")
   print(f"Plugin type: {plugin.plugin_type}")
   print(f"Enabled: {plugin.enabled}")

Loading MCP Servers
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Load all servers from directory
   servers = await plugin.load_servers()
   print(f"Found {len(servers)} MCP servers")

   # Print server details
   for server in servers[:3]:  # First 3 servers
       print(f"- {server.name} v{server.version}")
       print(f"  Capabilities: {', '.join(server.capabilities)}")
       print(f"  Local path: {server.local_path}")
       print()

Filtering and Searching
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Filter by category
   ai_servers = await plugin.filter_by_category("ai-tools")
   database_servers = await plugin.filter_by_category("database")
   
   print(f"AI tools: {len(ai_servers)} servers")
   print(f"Database: {len(database_servers)} servers")

   # Search servers
   postgres_servers = await plugin.search_servers("postgres")
   print(f"PostgreSQL servers: {len(postgres_servers)}")

FastAPI Integration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import FastAPI

   # Create FastAPI app
   app = FastAPI(title="MCP Server Browser")

   # Mount plugin router
   plugin = MCPBrowserPlugin()
   app.include_router(plugin.get_router(), prefix="/mcp")

   # Available endpoints:
   # GET /mcp/servers - List all servers
   # GET /mcp/servers/{server_name} - Get specific server
   # GET /mcp/categories - List categories
   # GET /mcp/search?q=query - Search servers

Working with Server Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.models import MCPServerInfo, DownloadedServerInfo

   # Create MCP server info
   server = MCPServerInfo(
       name="PostgreSQL Server",  # Auto-normalized to "postgresql-server"
       description="Database MCP server",
       version="1.2.0",
       capabilities=["database", "sql", "postgres"],
       mcp_version="0.1.0",
       transport_types=["stdio"],
       command_template="npx -y @modelcontextprotocol/server-postgres {connection_string}"
   )

   # Add local installation details
   downloaded_server = DownloadedServerInfo(
       **server.model_dump(),  # Inherit all MCP fields
       local_path=Path("/downloads/postgres-server"),
       file_size=1024000,  # bytes
       download_source="npm",
       is_verified=True
   )

   print(f"Server name: {downloaded_server.name}")
   print(f"Capabilities: {downloaded_server.capabilities}")
   print(f"Installed: {downloaded_server.installed_date}")

Real-World Example
------------------

Complete example managing MCP servers:

.. code-block:: python

   import asyncio
   from pathlib import Path
   from haive.mcp.plugins import MCPBrowserPlugin

   async def main():
       # Initialize plugin
       plugin = MCPBrowserPlugin(
           server_directory=Path("/home/will/Downloads/mcp_servers"),
           cache_ttl=3600
       )
       
       # Load servers
       print("Loading MCP servers...")
       servers = await plugin.load_servers()
       print(f"Loaded {len(servers)} servers")
       
       # Categorize servers
       categories = {}
       for server in servers:
           for capability in server.capabilities:
               if capability not in categories:
                   categories[capability] = []
               categories[capability].append(server.name)
       
       # Print categorized results
       print("\\nServer Categories:")
       for category, server_names in categories.items():
           print(f"  {category}: {len(server_names)} servers")
           for name in server_names[:3]:  # First 3
               print(f"    - {name}")
           if len(server_names) > 3:
               print(f"    ... and {len(server_names) - 3} more")
       
       # Find specific servers
       print("\\nDatabase Servers:")
       db_servers = [s for s in servers if "database" in s.capabilities]
       for server in db_servers:
           print(f"  - {server.name} v{server.version}")
           print(f"    Path: {server.local_path}")
           print(f"    Size: {server.file_size / 1024:.1f} KB")

   if __name__ == "__main__":
       asyncio.run(main())

Expected Output
~~~~~~~~~~~~~~~

.. code-block:: text

   Loading MCP servers...
   Loaded 63 servers

   Server Categories:
     database: 5 servers
       - postgresql-server
       - mysql-server
       - sqlite-server
       ... and 2 more
     ai-tools: 12 servers
       - openai-server
       - claude-server
       - huggingface-server
       ... and 9 more
     web: 8 servers
       - brave-search
       - web-scraper
       - http-client
       ... and 5 more

   Database Servers:
     - postgresql-server v1.2.0
       Path: /home/will/Downloads/mcp_servers/postgresql-server
       Size: 1024.0 KB
     - mysql-server v1.0.0
       Path: /home/will/Downloads/mcp_servers/mysql-server
       Size: 856.3 KB

Testing Your Setup
------------------

Quick validation test:

.. code-block:: python

   import pytest
   from pathlib import Path
   from haive.mcp.plugins import MCPBrowserPlugin
   from haive.mcp.models import MCPServerInfo

   def test_basic_setup():
       """Test basic MCP setup works"""
       # Create plugin
       plugin = MCPBrowserPlugin(
           server_directory=Path("/tmp/test_servers")
       )
       
       # Verify plugin creation
       assert plugin.name == "MCPBrowserPlugin"
       assert plugin.plugin_type == "browser"
       assert plugin.enabled is True
       
       # Test server info creation
       server = MCPServerInfo(
           name="Test Server",
           description="Test MCP server",
           capabilities=["test"]
       )
       
       assert server.name == "test-server"  # Auto-normalized
       assert "test" in server.capabilities

   # Run test
   test_basic_setup()
   print("✅ Basic setup test passed!")

Common Issues
-------------

**ImportError: No module named 'haive.mcp'**

.. code-block:: bash

   # Ensure package is installed
   poetry install
   # or
   pip install -e .

**ValidationError when creating servers**

.. code-block:: python

   # Check field validation
   from pydantic import ValidationError
   
   try:
       server = MCPServerInfo(name="", capabilities=[])  # Invalid
   except ValidationError as e:
       print(f"Validation error: {e}")

**FileNotFoundError for server directory**

.. code-block:: python

   # Ensure directory exists
   server_dir = Path("/home/will/Downloads/mcp_servers")
   server_dir.mkdir(parents=True, exist_ok=True)

Next Steps
----------

1. :doc:`platform-architecture` - Understand the design principles
2. :doc:`mcp-browser-plugin` - Deep dive into plugin features
3. :doc:`fastapi-integration` - Web API development
4. :doc:`real-world-examples` - Advanced usage patterns

.. note::
   This quickstart uses our Pydantic-first design principles - no ``__init__`` methods, 
   comprehensive validation, and intelligent inheritance patterns.