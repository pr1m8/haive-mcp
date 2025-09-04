MCP Browser Plugin Guide
========================

Complete guide to using the MCPBrowserPlugin for managing your 63+ downloaded MCP servers.

Overview
--------

The MCPBrowserPlugin provides a comprehensive interface for:

* **Server Discovery** - Scan directories for MCP servers
* **Metadata Management** - Track server capabilities and versions
* **Intelligent Caching** - Performance optimization with TTL
* **FastAPI Integration** - Built-in web API endpoints
* **Search and Filtering** - Find servers by category or capability

Basic Usage
-----------

Creating the Plugin
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.plugins import MCPBrowserPlugin
   from pathlib import Path

   # Basic plugin creation
   plugin = MCPBrowserPlugin(
       server_directory=Path("/home/will/Downloads/mcp_servers"),
       cache_ttl=3600  # 1 hour cache
   )

   print(f"Plugin: {plugin.name}")
   print(f"Type: {plugin.plugin_type}")
   print(f"Directory: {plugin.server_directory}")
   print(f"Cache TTL: {plugin.cache_ttl}s")

Factory Methods
~~~~~~~~~~~~~~~

Create plugins from different sources:

.. code-block:: python

   # From directory scan
   plugin = MCPBrowserPlugin.from_directory_scan(
       Path("/home/will/Downloads/mcp_servers")
   )

   # From installer results  
   installer_results = [
       {"name": "postgres-server", "success": True},
       {"name": "brave-search", "success": True},
       # ... more results
   ]
   
   plugin = MCPBrowserPlugin.from_installer_results(
       installer_results,
       base_directory=Path("/home/will/Downloads/mcp_servers")
   )

Server Management
-----------------

Loading Servers
~~~~~~~~~~~~~~~

.. code-block:: python

   # Load all servers (uses caching)
   servers = await plugin.load_servers()
   print(f"Found {len(servers)} MCP servers")

   # Print server details
   for server in servers:
       print(f"📦 {server.name} v{server.version}")
       print(f"   Capabilities: {', '.join(server.capabilities)}")
       print(f"   Size: {server.file_size / 1024:.1f} KB")
       print(f"   Path: {server.local_path}")
       print(f"   Verified: {'✅' if server.is_verified else '❌'}")
       print()

Server Information Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each server provides comprehensive information:

.. code-block:: python

   from haive.mcp.models import DownloadedServerInfo

   # Example server structure
   server: DownloadedServerInfo = servers[0]

   # Basic info (from BaseServerInfo)
   print(f"Name: {server.name}")                    # "postgresql-server"
   print(f"Description: {server.description}")      # "PostgreSQL MCP server"
   print(f"Version: {server.version}")              # "1.2.0"
   print(f"Capabilities: {server.capabilities}")    # ["database", "sql"]

   # MCP-specific (from MCPServerInfo)
   print(f"MCP Version: {server.mcp_version}")      # "0.1.0"
   print(f"Transport: {server.transport_types}")    # ["stdio"]
   print(f"Command: {server.command_template}")     # "npx -y @model..."

   # Local installation (from DownloadedServerInfo)
   print(f"Local Path: {server.local_path}")        # Path object
   print(f"File Size: {server.file_size}")          # bytes
   print(f"Installed: {server.installed_date}")     # datetime
   print(f"Source: {server.download_source}")       # "npm"
   print(f"Verified: {server.is_verified}")         # bool

Filtering and Search
--------------------

Category Filtering
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Filter by single category
   database_servers = await plugin.filter_by_category("database")
   ai_servers = await plugin.filter_by_category("ai-tools")
   web_servers = await plugin.filter_by_category("web")

   print(f"Database servers: {len(database_servers)}")
   for server in database_servers:
       print(f"  - {server.name}")

   print(f"AI tool servers: {len(ai_servers)}")  
   for server in ai_servers:
       print(f"  - {server.name}")

Multi-Category Filtering
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Custom filtering logic
   async def filter_by_multiple_categories(
       plugin: MCPBrowserPlugin, 
       categories: List[str]
   ) -> List[DownloadedServerInfo]:
       """Filter servers that have ANY of the specified capabilities"""
       servers = await plugin.load_servers()
       return [
           server for server in servers
           if any(cap in server.capabilities for cap in categories)
       ]

   # Find servers with database OR ai-tools capabilities
   mixed_servers = await filter_by_multiple_categories(
       plugin, ["database", "ai-tools"]
   )

Text Search
~~~~~~~~~~~

.. code-block:: python

   # Search by server name
   postgres_servers = await plugin.search_servers("postgres")
   openai_servers = await plugin.search_servers("openai")

   print(f"PostgreSQL-related: {len(postgres_servers)}")
   print(f"OpenAI-related: {len(openai_servers)}")

   # Advanced search function
   async def advanced_search(
       plugin: MCPBrowserPlugin,
       name_query: str = "",
       description_query: str = "",
       min_version: str = "0.0.0"
   ) -> List[DownloadedServerInfo]:
       """Advanced server search"""
       servers = await plugin.load_servers()
       results = []
       
       for server in servers:
           # Name matching
           if name_query and name_query.lower() not in server.name.lower():
               continue
           
           # Description matching    
           if description_query and description_query.lower() not in server.description.lower():
               continue
           
           # Version comparison (simplified)
           if server.version < min_version:
               continue
               
           results.append(server)
       
       return results

   # Usage
   recent_db_servers = await advanced_search(
       plugin,
       name_query="sql",
       min_version="1.0.0"
   )

Caching System
--------------

Understanding Caching
~~~~~~~~~~~~~~~~~~~~~~

The plugin implements intelligent caching:

.. code-block:: python

   # Check cache status
   def check_cache_status(plugin: MCPBrowserPlugin):
       if plugin.cached_servers is None:
           print("❌ Cache empty")
       elif plugin._is_cache_valid():
           print("✅ Cache valid")
           print(f"   Cached servers: {len(plugin.cached_servers)}")
           age = datetime.now() - plugin.cache_timestamp
           print(f"   Cache age: {age.total_seconds():.0f}s")
       else:
           print("⚠️  Cache expired")

   # Check before and after loading
   check_cache_status(plugin)
   servers = await plugin.load_servers()
   check_cache_status(plugin)

Manual Cache Management
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Refresh cache manually
   await plugin.refresh_cache()
   print("Cache refreshed")

   # Clear cache
   plugin.clear_cache()
   print("Cache cleared")

   # Check if cache needs refresh
   if not plugin._is_cache_valid():
       print("Cache needs refresh")
       await plugin.refresh_cache()

FastAPI Integration
-------------------

Basic Web API
~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import FastAPI

   # Create FastAPI app
   app = FastAPI(
       title="MCP Server Browser",
       description="Browse and manage MCP servers",
       version="1.0.0"
   )

   # Mount plugin router
   plugin = MCPBrowserPlugin(
       server_directory=Path("/home/will/Downloads/mcp_servers")
   )
   app.include_router(plugin.get_router(), prefix="/mcp")

   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=8000)

Available Endpoints
~~~~~~~~~~~~~~~~~~~

The plugin provides these endpoints:

.. code-block:: text

   GET  /mcp/servers                    # List all servers
   GET  /mcp/servers/{server_name}      # Get specific server
   GET  /mcp/categories                 # List all categories
   GET  /mcp/search?q={query}           # Search servers
   GET  /mcp/stats                      # Server statistics
   POST /mcp/cache/refresh              # Refresh cache

Testing the API
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start the server
   python app.py

   # Test endpoints
   curl http://localhost:8000/mcp/servers
   curl http://localhost:8000/mcp/servers/postgresql-server
   curl http://localhost:8000/mcp/categories
   curl http://localhost:8000/mcp/search?q=database
   curl -X POST http://localhost:8000/mcp/cache/refresh

Custom API Extensions
~~~~~~~~~~~~~~~~~~~~~

Extend the plugin's router:

.. code-block:: python

   from fastapi import APIRouter, HTTPException

   class ExtendedMCPBrowserPlugin(MCPBrowserPlugin):
       def get_router(self) -> APIRouter:
           # Get base router
           router = super().get_router()
           
           # Add custom endpoints
           @router.get("/health")
           async def health_check():
               return {
                   "status": "healthy",
                   "plugin": self.name,
                   "cache_valid": self._is_cache_valid()
               }
           
           @router.get("/servers/by-size")
           async def servers_by_size():
               servers = await self.load_servers()
               return sorted(
                   [{"name": s.name, "size": s.file_size} for s in servers],
                   key=lambda x: x["size"],
                   reverse=True
               )
           
           @router.post("/servers/{server_name}/verify")
           async def verify_server(server_name: str):
               servers = await self.load_servers()
               server = next((s for s in servers if s.name == server_name), None)
               
               if not server:
                   raise HTTPException(404, "Server not found")
               
               # Custom verification logic
               is_valid = server.local_path.exists() and server.file_size > 0
               
               return {
                   "server": server_name,
                   "verified": is_valid,
                   "exists": server.local_path.exists(),
                   "size": server.file_size
               }
           
           return router

Real-World Examples
-------------------

Server Analytics Dashboard
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   from collections import Counter
   from datetime import datetime, timedelta

   async def create_analytics_dashboard():
       """Create analytics for MCP servers"""
       plugin = MCPBrowserPlugin(
           server_directory=Path("/home/will/Downloads/mcp_servers")
       )
       
       servers = await plugin.load_servers()
       
       # Basic statistics
       total_servers = len(servers)
       total_size = sum(s.file_size for s in servers)
       verified_count = sum(1 for s in servers if s.is_verified)
       
       print("📊 MCP Server Analytics")
       print("=" * 30)
       print(f"Total Servers: {total_servers}")
       print(f"Total Size: {total_size / (1024*1024):.1f} MB")
       print(f"Verified: {verified_count} ({verified_count/total_servers*100:.1f}%)")
       print()
       
       # Capability analysis
       all_capabilities = []
       for server in servers:
           all_capabilities.extend(server.capabilities)
       
       capability_counts = Counter(all_capabilities)
       print("📈 Top Capabilities:")
       for capability, count in capability_counts.most_common(10):
           print(f"  {capability}: {count} servers")
       print()
       
       # Installation timeline
       recent_installs = [
           s for s in servers 
           if s.installed_date > datetime.now() - timedelta(days=7)
       ]
       print(f"📅 Recent Installs (7 days): {len(recent_installs)}")
       for server in sorted(recent_installs, key=lambda s: s.installed_date, reverse=True):
           print(f"  {server.name} - {server.installed_date.strftime('%Y-%m-%d %H:%M')}")

   # Run analytics
   asyncio.run(create_analytics_dashboard())

Server Health Checker
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def check_server_health():
       """Check health of all MCP servers"""
       plugin = MCPBrowserPlugin(
           server_directory=Path("/home/will/Downloads/mcp_servers")
       )
       
       servers = await plugin.load_servers()
       
       print("🏥 Server Health Check")
       print("=" * 30)
       
       healthy = 0
       issues = []
       
       for server in servers:
           # Check if file exists
           if not server.local_path.exists():
               issues.append(f"❌ {server.name}: File missing")
               continue
           
           # Check file size
           actual_size = server.local_path.stat().st_size
           if actual_size != server.file_size:
               issues.append(f"⚠️  {server.name}: Size mismatch")
               continue
           
           # Check if it's a valid package
           if server.download_source == "npm":
               package_json = server.local_path / "package.json"
               if not package_json.exists():
                   issues.append(f"⚠️  {server.name}: Missing package.json")
                   continue
           
           healthy += 1
       
       print(f"✅ Healthy servers: {healthy}/{len(servers)}")
       print(f"⚠️  Issues found: {len(issues)}")
       
       if issues:
           print("\\nIssues:")
           for issue in issues:
               print(f"  {issue}")

   # Run health check
   asyncio.run(check_server_health())

Server Migration Tool
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def migrate_servers(source_dir: Path, target_dir: Path):
       """Migrate servers from one directory to another"""
       source_plugin = MCPBrowserPlugin(server_directory=source_dir)
       
       print(f"🚚 Migrating servers: {source_dir} → {target_dir}")
       
       servers = await source_plugin.load_servers()
       target_dir.mkdir(parents=True, exist_ok=True)
       
       migrated = 0
       errors = []
       
       for server in servers:
           try:
               target_path = target_dir / server.local_path.name
               
               # Copy directory
               if server.local_path.is_dir():
                   shutil.copytree(server.local_path, target_path, dirs_exist_ok=True)
               else:
                   shutil.copy2(server.local_path, target_path)
               
               print(f"✅ Migrated: {server.name}")
               migrated += 1
               
           except Exception as e:
               error_msg = f"❌ Failed {server.name}: {e}"
               errors.append(error_msg)
               print(error_msg)
       
       print(f"\\n📊 Migration Complete:")
       print(f"  Migrated: {migrated}/{len(servers)}")
       print(f"  Errors: {len(errors)}")
       
       # Verify migration
       target_plugin = MCPBrowserPlugin(server_directory=target_dir)
       target_servers = await target_plugin.load_servers()
       print(f"  Verified: {len(target_servers)} servers in target")

Performance Tips
----------------

Efficient Server Loading
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Use caching for repeated operations
   plugin = MCPBrowserPlugin(
       server_directory=Path("/servers"),
       cache_ttl=7200  # 2 hours for infrequent changes
   )

   # Load once, use multiple times
   servers = await plugin.load_servers()
   
   # All these use cached data
   db_servers = [s for s in servers if "database" in s.capabilities]
   ai_servers = [s for s in servers if "ai-tools" in s.capabilities]
   large_servers = [s for s in servers if s.file_size > 1000000]

Batch Operations
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Batch process servers efficiently
   async def batch_process_servers(plugin: MCPBrowserPlugin):
       servers = await plugin.load_servers()
       
       # Group by capability for batch processing
       by_capability = {}
       for server in servers:
           for cap in server.capabilities:
               if cap not in by_capability:
                   by_capability[cap] = []
               by_capability[cap].append(server)
       
       # Process each group
       for capability, capability_servers in by_capability.items():
           print(f"Processing {len(capability_servers)} {capability} servers...")
           # Batch processing logic here

Memory Management
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Clear cache when memory is a concern
   if len(plugin.cached_servers) > 1000:  # Large server count
       plugin.clear_cache()
       
   # Use model_dump for serialization without keeping objects
   server_data = [s.model_dump() for s in servers]
   del servers  # Free memory

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Server directory not found**

.. code-block:: python

   from pathlib import Path

   server_dir = Path("/home/will/Downloads/mcp_servers")
   if not server_dir.exists():
       print(f"❌ Directory not found: {server_dir}")
       server_dir.mkdir(parents=True, exist_ok=True)
       print(f"✅ Created directory: {server_dir}")

**Cache invalidation issues**

.. code-block:: python

   # Force cache refresh
   plugin.clear_cache()
   servers = await plugin.load_servers()

**Import errors**

.. code-block:: python

   try:
       from haive.mcp.plugins import MCPBrowserPlugin
   except ImportError as e:
       print(f"Import error: {e}")
       print("Try: poetry install or pip install -e .")

Debug Mode
~~~~~~~~~~

Enable detailed logging:

.. code-block:: python

   import logging

   # Enable debug logging
   logging.basicConfig(level=logging.DEBUG)
   logger = logging.getLogger("haive.mcp")

   # Plugin operations will now show debug info
   plugin = MCPBrowserPlugin(server_directory=Path("/servers"))
   servers = await plugin.load_servers()

Next Steps
----------

- :doc:`fastapi-integration` - Advanced web API patterns
- :doc:`real-world-examples` - Production usage examples
- :doc:`performance-optimization` - Scaling and optimization