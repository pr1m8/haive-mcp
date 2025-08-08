Example MCP Configurations
==========================

This page provides example configurations for common MCP server setups.

Basic Server Configuration
--------------------------

Filesystem Server
~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "mcpServers": {
       "filesystem": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-filesystem",
           "/path/to/allowed/directory"
         ]
       }
     }
   }

GitHub Server
~~~~~~~~~~~~~

.. code-block:: json

   {
     "mcpServers": {
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_TOKEN": "your-github-token"
         }
       }
     }
   }

PostgreSQL Server
~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "mcpServers": {
       "postgres": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-postgres",
           "postgresql://user:password@localhost/dbname"
         ]
       }
     }
   }

Multi-Server Setup
------------------

Development Environment
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "mcpServers": {
       "filesystem": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-filesystem",
           "/home/dev/projects"
         ]
       },
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_TOKEN": "${GITHUB_TOKEN}"
         }
       },
       "postgres": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-postgres",
           "${DATABASE_URL}"
         ]
       },
       "search": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-brave-search"],
         "env": {
           "BRAVE_API_KEY": "${BRAVE_API_KEY}"
         }
       }
     }
   }

AI/ML Workflow
~~~~~~~~~~~~~~

.. code-block:: json

   {
     "mcpServers": {
       "openai": {
         "command": "npx",
         "args": ["-y", "mcp-server-openai"],
         "env": {
           "OPENAI_API_KEY": "${OPENAI_API_KEY}"
         }
       },
       "memory": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-memory"]
       },
       "puppeteer": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
       }
     }
   }

Transport Types
---------------

stdio Transport (Default)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "mcpServers": {
       "example": {
         "command": "node",
         "args": ["server.js"],
         "transport": "stdio"
       }
     }
   }

SSE Transport
~~~~~~~~~~~~~

.. code-block:: json

   {
     "mcpServers": {
       "example-sse": {
         "transport": "sse",
         "url": "http://localhost:3000/sse"
       }
     }
   }

Haive Integration
-----------------

Using with MCPAgent
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.agents import MCPAgent
   from haive.mcp.config import MCPConfig, MCPServerConfig
   from haive.core.engine import AugLLMConfig

   # Configure MCP servers
   config = MCPConfig(
       enabled=True,
       servers={
           "filesystem": MCPServerConfig(
               transport="stdio",
               command="npx",
               args=["-y", "@modelcontextprotocol/server-filesystem", "/data"]
           ),
           "github": MCPServerConfig(
               transport="stdio",
               command="npx",
               args=["-y", "@modelcontextprotocol/server-github"],
               env={"GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]}
           )
       }
   )

   # Create agent with MCP capabilities
   agent = MCPAgent(
       name="dev_assistant",
       engine=AugLLMConfig(temperature=0.7),
       mcp_config=config
   )

   await agent.setup()

Using with Documentation Agent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.agents import MCPDocumentationAgent
   
   # Create documentation agent
   doc_agent = MCPDocumentationAgent.create_for_mcp_setup(
       engine=AugLLMConfig()
   )
   await doc_agent.setup()
   
   # Find servers by capability
   db_servers = await doc_agent.find_servers_by_capability(
       "database", 
       limit=5
   )
   
   # Generate configuration
   for server in db_servers:
       config = await doc_agent.generate_mcp_config(
           server["server_name"]
       )
       print(f"Server: {server['server_name']}")
       print(f"Config: {config.model_dump_json(indent=2)}")

Tips and Best Practices
-----------------------

1. **Environment Variables**: Use environment variables for sensitive data:

   .. code-block:: json

      {
        "env": {
          "API_KEY": "${API_KEY}",
          "DATABASE_URL": "${DATABASE_URL}"
        }
      }

2. **Path Restrictions**: Always restrict filesystem access:

   .. code-block:: json

      {
        "args": [
          "-y",
          "@modelcontextprotocol/server-filesystem",
          "/home/user/safe-directory"
        ]
      }

3. **Error Handling**: Check server availability before use:

   .. code-block:: python

      try:
          await agent.setup()
      except MCPServerError as e:
          logger.error(f"Failed to start MCP server: {e}")

4. **Resource Management**: Properly cleanup MCP connections:

   .. code-block:: python

      async with agent:
          result = await agent.arun("Query")
      # Automatically cleaned up