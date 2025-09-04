Advanced Configuration
======================

Detailed configuration options for haive-mcp and its 1900+ MCP servers.

Configuration Overview
----------------------

Haive-mcp supports multiple configuration levels:

1. **Automatic** - Zero configuration with smart defaults
2. **Category-based** - Configure by server categories
3. **Server-specific** - Fine-tune individual servers
4. **Custom** - Full control over all aspects

Configuration Methods
---------------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Configure MCP behavior through environment variables:

.. code-block:: bash

   # Set MCP home directory
   export MCP_HOME=/opt/mcp
   
   # Configure timeout
   export MCP_TIMEOUT=60
   
   # Enable debug mode
   export MCP_DEBUG=true
   
   # Set server categories
   export MCP_CATEGORIES=core,ai_enhanced
   
   # Configure parallel installations
   export MCP_MAX_PARALLEL=5

Configuration Files
~~~~~~~~~~~~~~~~~~~

Use YAML or JSON configuration files:

.. code-block:: yaml

   # mcp_config.yaml
   mcp:
     enabled: true
     auto_discover: true
     auto_install: true
     timeout: 30
     
     categories:
       - core
       - ai_enhanced
       - time_utilities
     
     servers:
       filesystem:
         enabled: true
         timeout: 10
         args:
           - "--root-dir=/data"
       
       github:
         enabled: true
         env:
           GITHUB_TOKEN: "${GITHUB_TOKEN}"
     
     discovery:
       cache_ttl: 3600
       max_cache_size: 1000
     
     installation:
       parallel: true
       max_workers: 5
       retry_attempts: 3

Programmatic Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure directly in code:

.. code-block:: python

   from haive.mcp.config import MCPConfig, MCPServerConfig
   
   # Detailed configuration
   config = MCPConfig(
       enabled=True,
       auto_discover=True,
       auto_install=True,
       timeout=30,
       
       # Server categories
       categories=["core", "ai_enhanced"],
       
       # Specific server configs
       servers={
           "filesystem": MCPServerConfig(
               transport="stdio",
               command="npx",
               args=["-y", "@modelcontextprotocol/server-filesystem", "/data"],
               env={"NODE_ENV": "production"},
               timeout=10
           ),
           "custom": MCPServerConfig(
               transport="http",
               url="http://localhost:8080",
               headers={"Authorization": "Bearer token"}
           )
       },
       
       # Discovery settings
       discovery_config={
           "cache_enabled": True,
           "cache_ttl": 3600,
           "parallel_discovery": True
       },
       
       # Installation settings
       installation_config={
           "parallel": True,
           "max_workers": 5,
           "npm_registry": "https://registry.npmjs.org",
           "pip_index": "https://pypi.org/simple"
       }
   )
   
   # Use with agent
   agent = EnhancedMCPAgent(
       name="configured",
       engine=AugLLMConfig(),
       mcp_config=config
   )

Server Categories Configuration
--------------------------------

Core Category
~~~~~~~~~~~~~

Essential tools for everyday operations:

.. code-block:: python

   core_config = {
       "filesystem": {
           "root_dirs": ["/home/user", "/data"],
           "allow_write": True
       },
       "postgres": {
           "connection_string": "postgresql://localhost/mydb",
           "pool_size": 10
       },
       "brave-search": {
           "api_key": "YOUR_API_KEY",
           "safe_search": "moderate"
       }
   }

AI Enhanced Category
~~~~~~~~~~~~~~~~~~~~

AI-powered tools configuration:

.. code-block:: python

   ai_config = {
       "openai": {
           "api_key": "YOUR_OPENAI_KEY",
           "model": "gpt-4",
           "temperature": 0.7
       },
       "anthropic": {
           "api_key": "YOUR_ANTHROPIC_KEY",
           "model": "claude-3"
       },
       "huggingface": {
           "token": "YOUR_HF_TOKEN",
           "models": ["bert-base", "gpt2"]
       }
   }

Transport Configuration
-----------------------

STDIO Transport
~~~~~~~~~~~~~~~

For command-line based servers:

.. code-block:: python

   stdio_config = MCPServerConfig(
       transport="stdio",
       command="node",
       args=["server.js"],
       cwd="/opt/servers/custom",
       env={
           "NODE_ENV": "production",
           "LOG_LEVEL": "info"
       },
       startup_timeout=10,
       shutdown_timeout=5
   )

HTTP Transport
~~~~~~~~~~~~~~

For web-based servers:

.. code-block:: python

   http_config = MCPServerConfig(
       transport="http",
       url="https://api.example.com/mcp",
       headers={
           "Authorization": "Bearer token",
           "X-API-Version": "2.0"
       },
       timeout=30,
       retry_config={
           "max_attempts": 3,
           "backoff": "exponential",
           "max_delay": 10
       }
   )

SSE Transport
~~~~~~~~~~~~~

For real-time streaming:

.. code-block:: python

   sse_config = MCPServerConfig(
       transport="sse",
       url="https://stream.example.com/events",
       reconnect=True,
       reconnect_delay=5,
       max_reconnect_attempts=10
   )

Performance Tuning
------------------

Connection Pooling
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   performance_config = {
       "connection_pool": {
           "min_size": 5,
           "max_size": 20,
           "timeout": 30,
           "idle_timeout": 300,
           "max_lifetime": 3600
       },
       "cache": {
           "enabled": True,
           "type": "redis",
           "redis_url": "redis://localhost:6379",
           "ttl": 3600,
           "max_entries": 10000
       },
       "batch_processing": {
           "enabled": True,
           "batch_size": 100,
           "flush_interval": 5
       }
   }

Resource Limits
~~~~~~~~~~~~~~~

.. code-block:: python

   limits_config = {
       "memory": {
           "max_heap": "512M",
           "max_rss": "1G"
       },
       "cpu": {
           "max_usage": 0.8,
           "nice": 10
       },
       "io": {
           "max_open_files": 1000,
           "max_disk_usage": "10G"
       },
       "network": {
           "max_connections": 100,
           "bandwidth_limit": "10M"
       }
   }

Security Configuration
----------------------

Authentication
~~~~~~~~~~~~~~

.. code-block:: python

   auth_config = {
       "authentication": {
           "type": "oauth2",
           "client_id": "YOUR_CLIENT_ID",
           "client_secret": "YOUR_SECRET",
           "token_url": "https://auth.example.com/token",
           "scopes": ["read", "write"]
       },
       "api_keys": {
           "openai": "${OPENAI_API_KEY}",
           "anthropic": "${ANTHROPIC_API_KEY}",
           "github": "${GITHUB_TOKEN}"
       }
   }

Encryption
~~~~~~~~~~

.. code-block:: python

   encryption_config = {
       "tls": {
           "enabled": True,
           "verify": True,
           "cert_file": "/path/to/cert.pem",
           "key_file": "/path/to/key.pem",
           "ca_bundle": "/path/to/ca.pem"
       },
       "secrets": {
           "provider": "vault",
           "vault_url": "https://vault.example.com",
           "vault_token": "${VAULT_TOKEN}"
       }
   }

Logging Configuration
---------------------

.. code-block:: python

   logging_config = {
       "level": "INFO",
       "format": "json",
       "outputs": [
           {
               "type": "file",
               "path": "/var/log/mcp/agent.log",
               "rotation": "daily",
               "retention": 7
           },
           {
               "type": "console",
               "format": "colored"
           },
           {
               "type": "syslog",
               "host": "localhost",
               "port": 514
           }
       ],
       "filters": {
           "exclude_sensitive": True,
           "redact_patterns": ["api_key", "token", "password"]
       }
   }

Deployment Configurations
-------------------------

Development
~~~~~~~~~~~

.. code-block:: python

   dev_config = MCPConfig(
       enabled=True,
       auto_discover=True,
       auto_install=True,
       categories=["core"],
       timeout=60,
       debug=True,
       verbose=True
   )

Production
~~~~~~~~~~

.. code-block:: python

   prod_config = MCPConfig(
       enabled=True,
       auto_discover=False,  # Use explicit servers
       auto_install=False,   # Pre-installed servers only
       servers={
           # Explicitly configured servers
       },
       timeout=30,
       retry_attempts=3,
       health_check_interval=60,
       monitoring_enabled=True,
       metrics_port=9090
   )

Configuration Validation
------------------------

.. code-block:: python

   from haive.mcp.config import validate_config
   
   # Validate configuration
   errors = validate_config(config)
   if errors:
       for error in errors:
           print(f"Configuration error: {error}")
   else:
       print("Configuration valid")

Next Steps
----------

- Review :doc:`advanced` for advanced patterns
- Check :doc:`guides/platform-architecture` for system design
- Explore the :doc:`API Reference <autoapi/haive/mcp/index>`