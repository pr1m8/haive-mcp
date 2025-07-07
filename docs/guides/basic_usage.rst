Basic Usage
===========

This guide covers the fundamental usage patterns for haive-mcp.

Creating Your First MCP Agent
-----------------------------

The simplest way to get started is with the MCPAgent class:

.. code-block:: python

    from haive.mcp import MCPAgent, MCPConfig, MCPServerConfig
    from haive.core.engine.aug_llm import AugLLMConfig

    # Create engine configuration
    engine = AugLLMConfig(
        name="basic_mcp_agent",
        llm_config={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }
    )

    # Configure MCP
    mcp_config = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                name="filesystem",
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"]
            )
        }
    )

    # Create agent
    agent = MCPAgent(
        engine=engine,
        mcp_config=mcp_config,
        name="file_assistant"
    )

    # Initialize and use
    await agent.setup()

Working with Files
-----------------

Once you have a filesystem MCP server configured, you can perform file operations:

.. code-block:: python

    # Read a file
    result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Read the contents of README.md and summarize it"
        }]
    })

    # List directory contents
    result = await agent.arun({
        "messages": [{
            "role": "user", 
            "content": "What files are in the current directory?"
        }]
    })

    # Create and write files
    result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Create a new file called 'notes.txt' with a summary of our conversation"
        }]
    })

Working with GitHub
------------------

With a GitHub MCP server, you can interact with repositories:

.. code-block:: python

    # Configure GitHub server
    github_config = MCPServerConfig(
        name="github",
        transport="stdio", 
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_TOKEN": "your_github_token"}
    )

    # Add to MCP config
    mcp_config.servers["github"] = github_config

    # Use with agent
    result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Create a new issue in my repository about improving documentation"
        }]
    })

Database Operations
------------------

With a PostgreSQL MCP server:

.. code-block:: python

    # Configure PostgreSQL server
    postgres_config = MCPServerConfig(
        name="postgres",
        transport="stdio",
        command="npx", 
        args=["-y", "@modelcontextprotocol/server-postgres"],
        env={"DATABASE_URL": "postgresql://user:pass@localhost/mydb"}
    )

    # Query the database
    result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Show me the schema of the users table and count how many users we have"
        }]
    })

Tool Discovery and Inspection
-----------------------------

You can inspect what tools are available from your MCP servers:

.. code-block:: python

    # Get all MCP tools
    mcp_tools = agent.get_mcp_tools()
    print(f"Available MCP tools: {len(mcp_tools)}")

    for tool in mcp_tools:
        print(f"- {tool.name}: {tool.description}")

    # Get tools from specific server
    fs_tools = [t for t in mcp_tools if 'filesystem' in t.name]
    print(f"Filesystem tools: {[t.name for t in fs_tools]}")

    # Check tool schemas
    for tool in fs_tools[:3]:  # First 3 tools
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        if hasattr(tool, 'args_schema'):
            print(f"Parameters: {tool.args_schema}")

Error Handling
-------------

Handle MCP server errors gracefully:

.. code-block:: python

    try:
        await agent.setup()
    except Exception as e:
        print(f"MCP setup failed: {e}")
        # Continue with limited functionality
        
    # Check server health
    if hasattr(agent, 'mcp_health'):
        for server, health in agent.mcp_health.items():
            if health['status'] != 'connected':
                print(f"Server {server} is {health['status']}")

Resource Management
------------------

MCP servers can provide resources (data sources):

.. code-block:: python

    # Get available resources
    resources = agent.get_mcp_resources()
    print(f"Available resources: {len(resources)}")

    for resource in resources:
        print(f"- {resource.uri}: {resource.name}")

    # Use resources in prompts
    result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Analyze the data from the customer_data resource"
        }]
    })

Custom System Messages
---------------------

Enhance your agent with MCP-aware system messages:

.. code-block:: python

    engine = AugLLMConfig(
        name="enhanced_agent",
        system_message=\"\"\"You are an AI assistant with access to:
        - File system operations (read, write, list files)
        - GitHub repository management
        - Database queries and analysis
        
        Use these tools to help users with their tasks.
        Always explain what tools you're using and why.
        \"\"\",
        llm_config={
            "provider": "openai",
            "model": "gpt-4o-mini"
        }
    )

Batch Operations
---------------

Perform multiple operations efficiently:

.. code-block:: python

    # Process multiple files
    result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": \"\"\"Please:
            1. List all Python files in the current directory
            2. Read the first 3 files
            3. Create a summary report of their contents
            4. Save the report as 'code_summary.md'
            \"\"\"
        }]
    })

Configuration Updates
--------------------

Update MCP configuration at runtime:

.. code-block:: python

    # Add a new server dynamically
    new_server = MCPServerConfig(
        name="sqlite",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-sqlite"],
        env={"DB_PATH": "./app.db"}
    )

    # Update configuration
    agent.mcp_config.servers["sqlite"] = new_server

    # Reinitialize MCP
    await agent.setup()

Monitoring and Debugging
------------------------

Enable detailed logging to troubleshoot issues:

.. code-block:: python

    import logging

    # Enable MCP debug logging
    logging.getLogger("haive.mcp").setLevel(logging.DEBUG)
    logging.getLogger("langchain_mcp_adapters").setLevel(logging.DEBUG)

    # Create agent with debugging
    agent = MCPAgent(
        engine=engine,
        mcp_config=mcp_config,
        name="debug_agent"
    )

    # Monitor server health
    await agent.setup()
    
    # Print health status
    if hasattr(agent, '_server_health'):
        for server, health in agent._server_health.items():
            print(f"{server}: {health}")

Best Practices
-------------

1. **Always call agent.setup()** after creating an MCPAgent
2. **Handle connection failures gracefully** - servers may be unavailable
3. **Use appropriate timeouts** for different types of operations
4. **Monitor server health** in production environments
5. **Cache tool lists** if you need to check them frequently
6. **Use specific, descriptive server names** for easier debugging
7. **Set environment variables** for sensitive data like API keys
8. **Test with simple operations first** before complex workflows