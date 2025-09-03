Quick Start
===========

This guide will get you up and running with haive-mcp in 5 minutes.

Basic Setup
-----------

1. **Import the essentials**:

.. code-block:: python

    from haive.mcp import MCPAgent, MCPConfig, MCPServerConfig
    from haive.core.engine.aug_llm import AugLLMConfig

2. **Create an engine configuration**:

.. code-block:: python

    engine = AugLLMConfig(
        name="mcp_assistant",
        llm_config={
            "provider": "openai", 
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }
    )

3. **Configure an MCP server**:

.. code-block:: python

    mcp_config = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                name="filesystem",
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"],
                env={"ALLOWED_PATHS": "/tmp"}
            )
        }
    )

4. **Create and setup the agent**:

.. code-block:: python

    agent = MCPAgent(
        engine=engine,
        mcp_config=mcp_config,
        name="file_assistant"
    )
    
    # Initialize MCP connections
    await agent.setup()

5. **Use the agent**:

.. code-block:: python

    result = await agent.arun({
        "messages": [{
            "role": "user", 
            "content": "List the files in /tmp directory"
        }]
    })
    
    print(result["content"])

Complete Example
---------------

Here's a complete working example:

.. code-block:: python

    import asyncio
    from haive.mcp import MCPAgent, MCPConfig, MCPServerConfig
    from haive.core.engine.aug_llm import AugLLMConfig

    async def main():
        # Create engine
        engine = AugLLMConfig(
            name="mcp_demo",
            llm_config={"provider": "openai", "model": "gpt-4o-mini"}
        )
        
        # Configure filesystem MCP server
        mcp_config = MCPConfig(
            enabled=True,
            servers={
                "filesystem": MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem"],
                    capabilities=["file_read", "file_write", "directory_list"]
                )
            }
        )
        
        # Create agent
        agent = MCPAgent(
            engine=engine,
            mcp_config=mcp_config,
            name="file_assistant"
        )
        
        # Setup MCP connections
        await agent.setup()
        
        # Use the agent
        result = await agent.arun({
            "messages": [{
                "role": "user",
                "content": "What files are in the current directory?"
            }]
        })
        
        print(f"Agent response: {result['content']}")
        
        # List available tools
        tools = agent.get_mcp_tools()
        print(f"Available MCP tools: {[t.name for t in tools]}")

    if __name__ == "__main__":
        asyncio.run(main())

Factory Method Approach
----------------------

For simpler setup, use the factory method:

.. code-block:: python

    # One-liner agent creation
    agent = MCPAgent.create_with_mcp_servers(
        engine=engine,
        server_configs={
            "filesystem": {
                "transport": "stdio",
                "command": "npx", 
                "args": ["-y", "@modelcontextprotocol/server-filesystem"]
            },
            "github": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": "your_token_here"}
            }
        }
    )
    
    await agent.setup()

Multiple Servers Example
-----------------------

Working with multiple MCP servers:

.. code-block:: python

    mcp_config = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                name="filesystem",
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"]
            ),
            "github": MCPServerConfig(
                name="github", 
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env={"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")}
            ),
            "postgres": MCPServerConfig(
                name="postgres",
                transport="stdio", 
                command="npx",
                args=["-y", "@modelcontextprotocol/server-postgres"],
                env={"DATABASE_URL": "postgresql://localhost/mydb"}
            )
        },
        # Filter by capabilities
        required_capabilities=["database_query", "file_read"]
    )

Next Steps
----------

Now that you have a basic setup working:

1. **Explore more servers**: Check out the `MCP Server Registry <https://github.com/modelcontextprotocol/servers>`_
2. **Add custom tools**: Learn about `custom server development <guides/custom_servers.html>`_  
3. **Advanced features**: Read about `health monitoring and error handling <guides/advanced_features.html>`_
4. **Integration patterns**: See `integration examples <guides/integration.html>`_

Common Issues
------------

**Server won't start**
    - Ensure the MCP server is installed: ``npm list -g @modelcontextprotocol/server-filesystem``
    - Check that Node.js is in your PATH
    - Verify server permissions

**No tools discovered**
    - Enable debug logging to see connection details
    - Check server capabilities match your requirements  
    - Verify the server is actually running

**Timeout errors**
    - Increase the timeout in MCPServerConfig
    - Check server startup time
    - Monitor server health status

For more help, see the `troubleshooting guide <troubleshooting.html>`_.