Configuration
=============

The haive-mcp package provides flexible configuration options for MCP servers, discovery, and agent integration.

Configuration Classes
--------------------

MCPTransport
~~~~~~~~~~~~

.. autoclass:: haive.mcp.config.MCPTransport
   :members:
   :undoc-members:

Supported transport types:

- **stdio**: Standard input/output communication (most common)
- **sse**: Server-Sent Events for HTTP streaming  
- **streamable_http**: HTTP streaming for continuous data transfer

MCPServerConfig
~~~~~~~~~~~~~~~

.. autoclass:: haive.mcp.config.MCPServerConfig
   :members:
   :undoc-members:

Key configuration fields:

.. code-block:: python

    MCPServerConfig(
        name="server_name",           # Unique identifier
        enabled=True,                 # Whether to activate
        transport="stdio",            # Communication method
        command="npx",                # Executable command  
        args=["-y", "package-name"],  # Command arguments
        url="http://localhost:3000",  # For HTTP transports
        env={"KEY": "value"},         # Environment variables
        api_key="secret",             # Authentication key
        category="filesystem",        # Organizational category
        description="Server purpose", # Human-readable description
        capabilities=["read", "write"], # Server capabilities
        timeout=30,                   # Connection timeout (seconds)
        retry_attempts=3,             # Retry count on failure
        auto_start=True,              # Auto-start on init
        health_check_interval=60      # Health check frequency
    )

MCPConfig
~~~~~~~~~

.. autoclass:: haive.mcp.config.MCPConfig
   :members:
   :undoc-members:

Main configuration options:

.. code-block:: python

    MCPConfig(
        enabled=True,                 # Enable MCP functionality
        auto_discover=True,           # Auto-discover servers
        lazy_init=False,              # Initialize immediately
        servers={},                   # Server configurations
        discovery_paths=[],           # Paths to search for configs
        categories=["dev", "data"],   # Filter by categories
        required_capabilities=[],     # Required server capabilities
        global_timeout=60,            # Global operation timeout
        max_concurrent_servers=10,    # Max concurrent connections
        enable_health_checks=True,    # Enable health monitoring
        on_server_connected="callback", # Connection callback
        on_server_failed="callback",   # Failure callback  
        on_tool_discovered="callback"  # Tool discovery callback
    )

Configuration Examples
---------------------

Basic Filesystem Server
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from haive.mcp.config import MCPConfig, MCPServerConfig

    config = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                name="filesystem",
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"],
                env={"ALLOWED_PATHS": "/home/user/documents"},
                capabilities=["file_read", "file_write", "directory_list"],
                timeout=30
            )
        }
    )

Multi-Server Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    config = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                name="filesystem",
                transport="stdio", 
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"],
                category="storage"
            ),
            "github": MCPServerConfig(
                name="github",
                transport="stdio",
                command="npx", 
                args=["-y", "@modelcontextprotocol/server-github"],
                env={"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")},
                category="development"
            ),
            "postgres": MCPServerConfig(
                name="postgres",
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-postgres"], 
                env={"DATABASE_URL": "postgresql://localhost/dev"},
                category="database"
            )
        },
        categories=["development", "database"],  # Only load these categories
        required_capabilities=["database_query"], # Must have DB access
        max_concurrent_servers=5,
        enable_health_checks=True
    )

HTTP-Based Server
~~~~~~~~~~~~~~~~

.. code-block:: python

    config = MCPConfig(
        enabled=True,
        servers={
            "api_server": MCPServerConfig(
                name="api_server",
                transport="sse",  # Server-Sent Events
                url="http://localhost:3000/mcp",
                api_key="your-api-key",
                timeout=60,
                health_check_interval=30
            )
        }
    )

Custom Server Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    config = MCPConfig(
        enabled=True,
        servers={
            "custom_server": MCPServerConfig(
                name="custom_server",
                transport="stdio",
                command="python",
                args=["/path/to/my_server.py", "--port", "8080"],
                env={
                    "SERVER_MODE": "production",
                    "LOG_LEVEL": "INFO",
                    "API_KEY": os.getenv("CUSTOM_API_KEY")
                },
                capabilities=["custom_tool", "data_analysis"],
                category="custom",
                description="My custom MCP server implementation",
                timeout=45,
                retry_attempts=5,
                health_check_interval=120
            )
        }
    )

Discovery Configuration
----------------------

Automatic Server Discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    config = MCPConfig(
        enabled=True,
        auto_discover=True,
        discovery_paths=[
            "~/.mcp/servers",      # User config directory
            ".mcp/servers",        # Project-local configs
            "mcp_servers",         # Custom directory
            "/etc/mcp/servers"     # System-wide configs
        ],
        categories=["filesystem", "development"],  # Filter discovered servers
        required_capabilities=["file_read"]        # Capability requirements
    )

Manual Server Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    config = MCPConfig(
        enabled=True,
        auto_discover=False,  # Disable auto-discovery
        servers={
            # Explicitly configured servers only
            "filesystem": MCPServerConfig(...),
            "github": MCPServerConfig(...)
        }
    )

Environment Variables
--------------------

You can also configure MCP servers using environment variables:

.. code-block:: bash

    # Enable MCP
    export MCP_ENABLED=true
    
    # Set global timeout
    export MCP_GLOBAL_TIMEOUT=120
    
    # Configure filesystem server
    export MCP_FILESYSTEM_ENABLED=true
    export MCP_FILESYSTEM_COMMAND=npx
    export MCP_FILESYSTEM_ARGS="-y,@modelcontextprotocol/server-filesystem"
    export MCP_FILESYSTEM_ALLOWED_PATHS="/home/user"
    
    # Configure GitHub server  
    export MCP_GITHUB_ENABLED=true
    export MCP_GITHUB_TOKEN="your_github_token"

Configuration Files
------------------

JSON Configuration
~~~~~~~~~~~~~~~~~

Create a ``mcp_config.json`` file:

.. code-block:: json

    {
        "enabled": true,
        "auto_discover": true,
        "servers": {
            "filesystem": {
                "name": "filesystem",
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "capabilities": ["file_read", "file_write"],
                "timeout": 30
            },
            "github": {
                "name": "github", 
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
                "capabilities": ["repo_access"]
            }
        }
    }

YAML Configuration
~~~~~~~~~~~~~~~~~

Create a ``mcp_config.yaml`` file:

.. code-block:: yaml

    enabled: true
    auto_discover: true
    global_timeout: 60
    max_concurrent_servers: 10
    
    servers:
      filesystem:
        name: filesystem
        transport: stdio
        command: npx
        args:
          - "-y"
          - "@modelcontextprotocol/server-filesystem"
        env:
          ALLOWED_PATHS: "/home/user/documents"
        capabilities:
          - file_read
          - file_write
          - directory_list
        timeout: 30
        
      github:
        name: github
        transport: stdio 
        command: npx
        args:
          - "-y"
          - "@modelcontextprotocol/server-github"
        env:
          GITHUB_TOKEN: "${GITHUB_TOKEN}"
        capabilities:
          - repo_access
          - issue_management

Loading Configurations
---------------------

.. code-block:: python

    import json
    import yaml
    from haive.mcp.config import MCPConfig

    # From JSON
    with open("mcp_config.json") as f:
        config_data = json.load(f)
    config = MCPConfig(**config_data)

    # From YAML
    with open("mcp_config.yaml") as f:
        config_data = yaml.safe_load(f)
    config = MCPConfig(**config_data)

    # From environment (using a helper function)
    config = MCPConfig.from_env()

Best Practices
--------------

1. **Use categories** to organize servers by purpose
2. **Set appropriate timeouts** based on server complexity
3. **Enable health checks** for production environments  
4. **Use environment variables** for sensitive data like API keys
5. **Start with lazy_init=True** for faster startup times
6. **Monitor server health** and implement failure callbacks
7. **Test configurations** in development before production deployment