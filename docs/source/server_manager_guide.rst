Server Manager Guide
====================

Complete guide to managing MCP servers in haive-mcp's 1900+ server ecosystem.

Overview
--------

The MCP Server Manager provides centralized control over server lifecycle, discovery, and monitoring across the entire ecosystem of 1900+ available servers.

Server Manager Components
-------------------------

Core Manager
~~~~~~~~~~~~

The main interface for server management:

.. code-block:: python

   from haive.mcp.manager import MCPManager
   
   # Initialize manager
   manager = MCPManager()
   
   # Discover available servers
   available = await manager.discover_servers()
   print(f"Found {len(available)} servers")
   
   # Install a server
   await manager.install_server("filesystem")
   
   # Start a server
   await manager.start_server("filesystem")
   
   # Get server status
   status = manager.get_server_status("filesystem")

Server Lifecycle Management
---------------------------

Installation
~~~~~~~~~~~~

Managing server installation from various sources:

.. code-block:: python

   from haive.mcp.manager import MCPManager
   from haive.mcp.installer import InstallerType
   
   manager = MCPManager()
   
   # Install from NPM
   await manager.install_server(
       name="filesystem",
       installer_type=InstallerType.NPM,
       package="@modelcontextprotocol/server-filesystem"
   )
   
   # Install from Git
   await manager.install_server(
       name="custom",
       installer_type=InstallerType.GIT,
       repository="https://github.com/user/mcp-server.git"
   )
   
   # Install from Python package
   await manager.install_server(
       name="python-server",
       installer_type=InstallerType.PIP,
       package="mcp-python-server"
   )
   
   # Install with Docker
   await manager.install_server(
       name="containerized",
       installer_type=InstallerType.DOCKER,
       image="user/mcp-server:latest"
   )

Starting and Stopping
~~~~~~~~~~~~~~~~~~~~~

Control server runtime:

.. code-block:: python

   # Start server with configuration
   await manager.start_server(
       name="filesystem",
       config={
           "root_dirs": ["/home/user", "/data"],
           "allow_write": True
       }
   )
   
   # Stop server gracefully
   await manager.stop_server("filesystem", timeout=10)
   
   # Restart server
   await manager.restart_server("filesystem")
   
   # Stop all servers
   await manager.stop_all_servers()

Health Monitoring
~~~~~~~~~~~~~~~~~

Monitor server health and performance:

.. code-block:: python

   # Check individual server health
   health = await manager.health_check("filesystem")
   print(f"Status: {health['status']}")
   print(f"Uptime: {health['uptime_seconds']}s")
   print(f"Memory: {health['memory_mb']}MB")
   
   # Monitor all servers
   all_health = await manager.health_check_all()
   for server, health in all_health.items():
       print(f"{server}: {health['status']}")
   
   # Set up automatic health monitoring
   manager.enable_health_monitoring(
       interval=60,  # Check every 60 seconds
       on_unhealthy=lambda s: print(f"Server {s} is unhealthy")
   )

Discovery and Registry
----------------------

Server Discovery
~~~~~~~~~~~~~~~~

Discover servers from the 1900+ available:

.. code-block:: python

   from haive.mcp.discovery import DiscoveryEngine
   
   discovery = DiscoveryEngine()
   
   # Discover by capability
   file_servers = await discovery.find_by_capability("file_operations")
   
   # Discover by category
   ai_servers = await discovery.find_by_category("ai_enhanced")
   
   # Discover by keywords
   search_servers = await discovery.search("web search browser")
   
   # Get server details
   details = await discovery.get_server_details("filesystem")
   print(f"Name: {details['name']}")
   print(f"Description: {details['description']}")
   print(f"Tools: {details['tools']}")

Registry Management
~~~~~~~~~~~~~~~~~~~

Manage local server registry:

.. code-block:: python

   from haive.mcp.registry import ServerRegistry
   
   registry = ServerRegistry()
   
   # Register custom server
   registry.register_server({
       "name": "custom-server",
       "version": "1.0.0",
       "transport": "stdio",
       "command": "python",
       "args": ["custom_server.py"],
       "tools": ["custom_tool1", "custom_tool2"]
   })
   
   # Update registry from remote
   await registry.update_from_remote()
   
   # Export registry
   registry.export_to_file("servers.json")
   
   # Import registry
   registry.import_from_file("servers.json")

Batch Operations
----------------

Managing Multiple Servers
~~~~~~~~~~~~~~~~~~~~~~~~~~

Perform operations on multiple servers:

.. code-block:: python

   # Install multiple servers
   servers_to_install = ["filesystem", "github", "postgres"]
   results = await manager.batch_install(servers_to_install)
   
   for server, result in results.items():
       if result['success']:
           print(f"✅ {server} installed")
       else:
           print(f"❌ {server} failed: {result['error']}")
   
   # Start servers by category
   await manager.start_category("core")
   
   # Update all installed servers
   updates = await manager.update_all_servers()
   print(f"Updated {len(updates)} servers")

Parallel Operations
~~~~~~~~~~~~~~~~~~~

Execute operations in parallel:

.. code-block:: python

   import asyncio
   
   async def parallel_server_setup():
       """Set up multiple servers in parallel."""
       tasks = [
           manager.install_server("filesystem"),
           manager.install_server("github"),
           manager.install_server("postgres"),
           manager.install_server("search")
       ]
       
       results = await asyncio.gather(*tasks, return_exceptions=True)
       
       for i, result in enumerate(results):
           if isinstance(result, Exception):
               print(f"Server {i} failed: {result}")
           else:
               print(f"Server {i} installed successfully")

Configuration Management
------------------------

Server Profiles
~~~~~~~~~~~~~~~

Define reusable server profiles:

.. code-block:: python

   # Define profiles
   profiles = {
       "development": {
           "servers": ["filesystem", "github"],
           "config": {
               "filesystem": {"root_dirs": ["./src", "./tests"]},
               "github": {"repo": "user/project"}
           }
       },
       "production": {
           "servers": ["filesystem", "postgres", "redis"],
           "config": {
               "filesystem": {"root_dirs": ["/app/data"]},
               "postgres": {"connection": "postgresql://prod"},
               "redis": {"url": "redis://cache:6379"}
           }
       }
   }
   
   # Apply profile
   await manager.apply_profile(profiles["development"])
   
   # Switch profiles
   await manager.switch_profile("production")

Dynamic Configuration
~~~~~~~~~~~~~~~~~~~~~

Update server configuration at runtime:

.. code-block:: python

   # Update single server config
   await manager.update_config(
       "filesystem",
       {"root_dirs": ["/new/path"]}
   )
   
   # Hot reload configuration
   await manager.reload_config("filesystem")
   
   # Get current configuration
   config = manager.get_config("filesystem")
   print(f"Current config: {config}")

Monitoring and Logging
----------------------

Metrics Collection
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.monitoring import ServerMetrics
   
   metrics = ServerMetrics(manager)
   
   # Get server metrics
   stats = metrics.get_server_stats("filesystem")
   print(f"Requests: {stats['total_requests']}")
   print(f"Errors: {stats['error_count']}")
   print(f"Avg latency: {stats['avg_latency_ms']}ms")
   
   # Get aggregated metrics
   total_stats = metrics.get_total_stats()
   print(f"Total servers: {total_stats['server_count']}")
   print(f"Total requests: {total_stats['total_requests']}")

Logging
~~~~~~~

.. code-block:: python

   import logging
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   # Enable debug logging for specific server
   manager.set_log_level("filesystem", logging.DEBUG)
   
   # Get server logs
   logs = manager.get_server_logs("filesystem", lines=100)
   for log in logs:
       print(log)

Error Handling
--------------

Handling Server Failures
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.manager import ServerError, ServerNotFoundError
   
   try:
       await manager.start_server("nonexistent")
   except ServerNotFoundError as e:
       print(f"Server not found: {e}")
       # Attempt to discover and install
       await manager.auto_install_server("nonexistent")
   except ServerError as e:
       print(f"Server error: {e}")
       # Attempt recovery
       await manager.recover_server(e.server_name)

Automatic Recovery
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Enable auto-recovery
   manager.enable_auto_recovery(
       max_retries=3,
       retry_delay=5,
       on_recovery_failed=lambda s: print(f"Failed to recover {s}")
   )
   
   # Set up watchdog
   manager.start_watchdog(
       check_interval=30,
       restart_on_failure=True
   )

Best Practices
--------------

1. **Use profiles** for different environments
2. **Monitor health** regularly in production
3. **Log important events** for debugging
4. **Handle errors gracefully** with recovery strategies
5. **Update servers regularly** for security and features
6. **Use batch operations** for efficiency
7. **Configure resource limits** to prevent resource exhaustion

CLI Usage
---------

The server manager is also available via CLI:

.. code-block:: bash

   # List installed servers
   haive-mcp manager list
   
   # Install a server
   haive-mcp manager install filesystem
   
   # Start a server
   haive-mcp manager start filesystem
   
   # Check health
   haive-mcp manager health
   
   # Apply profile
   haive-mcp manager profile apply development

Next Steps
----------

- Review :doc:`managing_mcp_servers` for operational details
- Check :doc:`advanced_config` for configuration options
- Explore the :doc:`API Reference <autoapi/haive/mcp/manager/index>`