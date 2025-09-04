Managing MCP Servers
====================

Operational guide for managing MCP servers in production environments with 1900+ available servers.

Production Deployment
---------------------

Pre-Installation Setup
~~~~~~~~~~~~~~~~~~~~~~

Prepare your environment for MCP servers:

.. code-block:: bash

   # Install prerequisites
   sudo apt-get update
   sudo apt-get install -y nodejs npm python3-pip docker.io git
   
   # Verify installations
   node --version    # Should be v18+ 
   npm --version     # Should be v9+
   python3 --version # Should be 3.8+
   docker --version  # Should be 20+
   
   # Create MCP directories
   sudo mkdir -p /opt/mcp/{servers,configs,logs,data}
   sudo chown -R $USER:$USER /opt/mcp

Server Installation Strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose the right installation strategy:

.. code-block:: python

   from haive.mcp.manager import MCPManager, InstallStrategy
   
   manager = MCPManager()
   
   # Strategy 1: Pre-install all core servers
   await manager.batch_install(
       servers=["filesystem", "postgres", "github", "search"],
       strategy=InstallStrategy.PARALLEL,
       verify=True
   )
   
   # Strategy 2: On-demand installation
   agent = EnhancedMCPAgent(
       name="prod_agent",
       engine=AugLLMConfig(),
       mcp_categories=["core"],
       auto_install=True,  # Install as needed
       install_timeout=120
   )
   
   # Strategy 3: Docker-based deployment
   await manager.deploy_with_docker(
       compose_file="docker-compose.mcp.yml",
       env_file=".env.production"
   )

Health Monitoring
-----------------

Continuous Health Checks
~~~~~~~~~~~~~~~~~~~~~~~~

Implement robust health monitoring:

.. code-block:: python

   from haive.mcp.monitoring import HealthMonitor
   import asyncio
   
   class ProductionHealthMonitor:
       """Production-grade health monitoring."""
       
       def __init__(self, manager):
           self.manager = manager
           self.monitor = HealthMonitor(manager)
           self.alert_threshold = 3  # Failures before alert
           self.failure_counts = {}
       
       async def monitor_loop(self):
           """Continuous monitoring loop."""
           while True:
               try:
                   # Check all servers
                   health_status = await self.monitor.check_all()
                   
                   for server, status in health_status.items():
                       if status['healthy']:
                           # Reset failure count on success
                           self.failure_counts[server] = 0
                       else:
                           # Increment failure count
                           self.failure_counts[server] = \
                               self.failure_counts.get(server, 0) + 1
                           
                           # Alert if threshold reached
                           if self.failure_counts[server] >= self.alert_threshold:
                               await self.alert_unhealthy(server, status)
                               
                               # Attempt recovery
                               await self.attempt_recovery(server)
                   
                   # Log metrics
                   self.log_metrics(health_status)
                   
               except Exception as e:
                   print(f"Monitor error: {e}")
               
               # Wait before next check
               await asyncio.sleep(30)
       
       async def alert_unhealthy(self, server, status):
           """Send alerts for unhealthy servers."""
           # Send to monitoring system
           print(f"ALERT: {server} unhealthy - {status['error']}")
           # Could integrate with PagerDuty, Slack, etc.
       
       async def attempt_recovery(self, server):
           """Try to recover unhealthy server."""
           try:
               # Restart the server
               await self.manager.restart_server(server)
               print(f"Restarted {server}")
           except Exception as e:
               print(f"Recovery failed for {server}: {e}")

Metrics and Observability
~~~~~~~~~~~~~~~~~~~~~~~~~~

Track detailed metrics:

.. code-block:: python

   from prometheus_client import Counter, Histogram, Gauge
   import time
   
   # Define metrics
   mcp_requests = Counter('mcp_requests_total', 'Total MCP requests', ['server', 'tool'])
   mcp_errors = Counter('mcp_errors_total', 'Total MCP errors', ['server', 'error_type'])
   mcp_latency = Histogram('mcp_latency_seconds', 'MCP request latency', ['server'])
   mcp_active_servers = Gauge('mcp_active_servers', 'Number of active MCP servers')
   
   class MetricsCollector:
       """Collect and export metrics."""
       
       def track_request(self, server, tool, duration, success):
           """Track individual request metrics."""
           mcp_requests.labels(server=server, tool=tool).inc()
           mcp_latency.labels(server=server).observe(duration)
           
           if not success:
               mcp_errors.labels(server=server, error_type='request_failed').inc()
       
       def update_active_servers(self, count):
           """Update active server count."""
           mcp_active_servers.set(count)

Performance Optimization
------------------------

Connection Pooling
~~~~~~~~~~~~~~~~~~

Optimize connections for high throughput:

.. code-block:: python

   from haive.mcp.pooling import ConnectionPool
   
   # Configure connection pool
   pool_config = {
       "min_connections": 5,
       "max_connections": 50,
       "connection_timeout": 10,
       "idle_timeout": 300,
       "max_lifetime": 3600,
       "validation_interval": 60
   }
   
   pool = ConnectionPool(**pool_config)
   
   # Use with manager
   manager = MCPManager(connection_pool=pool)
   
   # Monitor pool statistics
   stats = pool.get_stats()
   print(f"Active connections: {stats['active']}")
   print(f"Idle connections: {stats['idle']}")
   print(f"Total created: {stats['total_created']}")

Caching Strategies
~~~~~~~~~~~~~~~~~~

Implement intelligent caching:

.. code-block:: python

   from haive.mcp.cache import MCPCache, CacheStrategy
   import redis
   
   # Redis-backed cache
   redis_client = redis.Redis(host='localhost', port=6379)
   
   cache = MCPCache(
       backend=redis_client,
       strategy=CacheStrategy.LRU,
       max_size=10000,
       ttl=3600
   )
   
   # Cache decorator for expensive operations
   @cache.cached(ttl=1800)
   async def expensive_mcp_operation(server, params):
       """Cached MCP operation."""
       return await manager.execute_tool(server, "expensive_tool", params)
   
   # Warm up cache
   async def warm_cache():
       """Pre-populate cache with common operations."""
       common_operations = [
           ("filesystem", {"action": "list", "path": "/"}),
           ("github", {"action": "list_repos"}),
           ("postgres", {"action": "list_tables"})
       ]
       
       for server, params in common_operations:
           await expensive_mcp_operation(server, params)

Load Balancing
~~~~~~~~~~~~~~

Distribute load across server instances:

.. code-block:: python

   from haive.mcp.loadbalancer import LoadBalancer, Strategy
   
   # Configure load balancer
   lb = LoadBalancer(
       strategy=Strategy.ROUND_ROBIN,
       health_check_interval=10
   )
   
   # Add server instances
   lb.add_instance("filesystem", "fs-1", "localhost:8001")
   lb.add_instance("filesystem", "fs-2", "localhost:8002")
   lb.add_instance("filesystem", "fs-3", "localhost:8003")
   
   # Use load-balanced servers
   async def balanced_request(tool, params):
       """Execute request on load-balanced server."""
       instance = lb.get_instance("filesystem")
       return await instance.execute(tool, params)

Disaster Recovery
-----------------

Backup and Restore
~~~~~~~~~~~~~~~~~~

Implement backup strategies:

.. code-block:: python

   from haive.mcp.backup import BackupManager
   import schedule
   
   backup_manager = BackupManager(
       backup_dir="/backup/mcp",
       retention_days=30
   )
   
   async def backup_servers():
       """Backup all server configurations and data."""
       # Backup configurations
       await backup_manager.backup_configs(manager.get_all_configs())
       
       # Backup server data
       for server in manager.list_servers():
           data = await manager.export_server_data(server)
           await backup_manager.backup_server_data(server, data)
       
       print(f"Backup completed: {backup_manager.last_backup}")
   
   async def restore_servers(backup_id):
       """Restore servers from backup."""
       # Restore configurations
       configs = await backup_manager.restore_configs(backup_id)
       for server, config in configs.items():
           await manager.apply_config(server, config)
       
       # Restore server data
       for server in configs.keys():
           data = await backup_manager.restore_server_data(server, backup_id)
           await manager.import_server_data(server, data)
       
       print(f"Restore completed from backup: {backup_id}")
   
   # Schedule regular backups
   schedule.every(6).hours.do(lambda: asyncio.run(backup_servers()))

Failover Strategies
~~~~~~~~~~~~~~~~~~~

Implement automatic failover:

.. code-block:: python

   class FailoverManager:
       """Manage server failover."""
       
       def __init__(self, manager):
           self.manager = manager
           self.primary_servers = {}
           self.backup_servers = {}
       
       def configure_failover(self, server, primary_url, backup_urls):
           """Configure failover for a server."""
           self.primary_servers[server] = primary_url
           self.backup_servers[server] = backup_urls
       
       async def handle_failure(self, server):
           """Handle server failure with failover."""
           if server not in self.backup_servers:
               raise Exception(f"No backup configured for {server}")
           
           # Try each backup
           for backup_url in self.backup_servers[server]:
               try:
                   # Switch to backup
                   await self.manager.switch_server_url(server, backup_url)
                   print(f"Failed over {server} to {backup_url}")
                   return True
               except Exception as e:
                   print(f"Backup {backup_url} failed: {e}")
           
           return False

Security Best Practices
------------------------

Access Control
~~~~~~~~~~~~~~

Implement fine-grained access control:

.. code-block:: python

   from haive.mcp.security import AccessControl, Permission
   
   # Configure access control
   ac = AccessControl()
   
   # Define roles
   ac.add_role("admin", [Permission.ALL])
   ac.add_role("developer", [
       Permission.READ,
       Permission.EXECUTE,
       Permission.LIST
   ])
   ac.add_role("viewer", [Permission.READ, Permission.LIST])
   
   # Assign permissions to servers
   ac.set_server_permissions("filesystem", {
       "admin": ["*"],
       "developer": ["read_file", "list_directory"],
       "viewer": ["list_directory"]
   })
   
   # Check permissions
   if ac.check_permission("developer", "filesystem", "write_file"):
       await manager.execute_tool("filesystem", "write_file", params)
   else:
       raise PermissionError("Insufficient permissions")

Audit Logging
~~~~~~~~~~~~~

Track all server operations:

.. code-block:: python

   from haive.mcp.audit import AuditLogger
   
   audit = AuditLogger(
       log_file="/var/log/mcp/audit.log",
       include_params=True,
       mask_sensitive=True
   )
   
   # Log server operations
   @audit.log_operation
   async def execute_sensitive_operation(server, tool, params):
       """Execute and audit sensitive operations."""
       result = await manager.execute_tool(server, tool, params)
       return result
   
   # Query audit logs
   logs = audit.query(
       server="filesystem",
       user="admin",
       start_time=datetime.now() - timedelta(hours=24)
   )

Scaling Strategies
------------------

Horizontal Scaling
~~~~~~~~~~~~~~~~~~

Scale servers horizontally:

.. code-block:: bash

   # Docker Swarm deployment
   docker swarm init
   docker service create \
     --name mcp-filesystem \
     --replicas 3 \
     --publish 8080:8080 \
     mcp/filesystem-server
   
   # Kubernetes deployment
   kubectl apply -f mcp-deployment.yaml
   kubectl scale deployment mcp-filesystem --replicas=5

Auto-scaling
~~~~~~~~~~~~

Implement auto-scaling based on load:

.. code-block:: python

   from haive.mcp.autoscale import AutoScaler
   
   autoscaler = AutoScaler(
       manager=manager,
       min_instances=2,
       max_instances=10,
       target_cpu=70,
       target_memory=80,
       scale_up_threshold=3,  # Consecutive checks
       scale_down_threshold=5
   )
   
   # Start auto-scaling
   await autoscaler.start()
   
   # Monitor scaling events
   autoscaler.on_scale_up = lambda s, n: print(f"Scaled up {s} to {n} instances")
   autoscaler.on_scale_down = lambda s, n: print(f"Scaled down {s} to {n} instances")

Maintenance Operations
----------------------

Rolling Updates
~~~~~~~~~~~~~~~

Update servers without downtime:

.. code-block:: python

   async def rolling_update(server_name, new_version):
       """Perform rolling update of server instances."""
       instances = manager.get_server_instances(server_name)
       
       for instance in instances:
           # Remove from load balancer
           lb.remove_instance(server_name, instance.id)
           
           # Update instance
           await instance.update(new_version)
           
           # Health check
           if await instance.health_check():
               # Add back to load balancer
               lb.add_instance(server_name, instance.id, instance.url)
           else:
               print(f"Update failed for {instance.id}")
               # Rollback if needed
               await instance.rollback()

Maintenance Mode
~~~~~~~~~~~~~~~~

Put servers in maintenance mode:

.. code-block:: python

   async def enter_maintenance_mode(server):
       """Put server in maintenance mode."""
       # Drain connections
       await manager.drain_connections(server, timeout=30)
       
       # Set maintenance flag
       await manager.set_maintenance_mode(server, True)
       
       # Redirect traffic to backup
       if server in backup_servers:
           await lb.redirect_traffic(server, backup_servers[server])
       
       print(f"{server} in maintenance mode")
   
   async def exit_maintenance_mode(server):
       """Exit maintenance mode."""
       # Health check
       if await manager.health_check(server):
           # Remove maintenance flag
           await manager.set_maintenance_mode(server, False)
           
           # Restore traffic
           await lb.restore_traffic(server)
           
           print(f"{server} back online")

Next Steps
----------

- Review :doc:`server_manager_guide` for manager details
- Check :doc:`advanced_config` for configuration
- Explore :doc:`advanced` for advanced patterns
- See the :doc:`API Reference <autoapi/haive/mcp/index>`