User Guide
==========

Complete guide for using haive-mcp to integrate with 1900+ MCP servers.

Getting Started
---------------

Haive-mcp makes it incredibly simple to use MCP servers:

1. **No manual installation** - Servers are installed automatically
2. **No configuration files** - Discovery happens at runtime
3. **No tool registration** - Tools are available instantly
4. **1900+ servers available** - Access to extensive ecosystem

Basic Usage
-----------

Creating Your First Agent
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.agents.enhanced_mcp_agent import EnhancedMCPAgent
   from haive.core.engine.aug_llm import AugLLMConfig

   # Create agent with automatic discovery
   agent = EnhancedMCPAgent(
       name="my_assistant",
       engine=AugLLMConfig(temperature=0.7),
       mcp_categories=["core"],  # Start with core tools
       auto_install=True
   )

   # Initialize (discovers and installs servers)
   await agent.initialize_mcp()

   # Use the agent
   result = await agent.arun("Help me organize my files")

Understanding Categories
~~~~~~~~~~~~~~~~~~~~~~~~

MCP servers are organized into categories for easy discovery:

- **core** - Essential everyday tools
- **ai_enhanced** - AI-powered capabilities
- **enhanced_filesystem** - Advanced file operations
- **time_utilities** - Scheduling and time management
- **browser_automation** - Web interaction
- **crypto_finance** - Financial tools
- **github_enhanced** - Development tools
- **notifications** - Communication tools

Common Tasks
------------

File Management
~~~~~~~~~~~~~~~

.. code-block:: python

   agent = EnhancedMCPAgent(
       name="file_manager",
       engine=AugLLMConfig(),
       mcp_categories=["enhanced_filesystem"],
       auto_install=True
   )
   await agent.initialize_mcp()
   
   # Organize files
   await agent.arun("Organize files by type and date")
   
   # Search content
   await agent.arun("Find all Python files with 'TODO' comments")

Data Analysis
~~~~~~~~~~~~~

.. code-block:: python

   agent = EnhancedMCPAgent(
       name="analyst",
       engine=AugLLMConfig(),
       mcp_categories=["core", "ai_enhanced"],
       auto_install=True
   )
   await agent.initialize_mcp()
   
   # Analyze data
   await agent.arun("Analyze CSV files and create summary statistics")

Web Research
~~~~~~~~~~~~

.. code-block:: python

   agent = EnhancedMCPAgent(
       name="researcher",
       engine=AugLLMConfig(),
       mcp_categories=["core", "browser_automation"],
       auto_install=True
   )
   await agent.initialize_mcp()
   
   # Research topics
   await agent.arun("Research recent AI developments and create a report")

Advanced Features
-----------------

Custom Server Selection
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.tools.server_selector import MCPServerSelector

   # Select servers by capability
   selector = MCPServerSelector()
   servers = selector.filter_by_capabilities(["file_read", "web_search"])
   
   # Create agent with specific servers
   agent = EnhancedMCPAgent(
       name="custom",
       engine=AugLLMConfig(),
       specific_servers=servers,
       auto_install=True
   )

Health Monitoring
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Check agent health
   health = await agent.health_check_mcp()
   print(f"Connected servers: {health['connected_count']}")
   print(f"Available tools: {health['tool_count']}")
   
   # Get detailed status
   status = agent.get_mcp_status()
   for server, info in status['servers'].items():
       print(f"{server}: {info['status']}")

Tool Discovery
~~~~~~~~~~~~~~

.. code-block:: python

   # List all available tools
   tools = agent.list_mcp_tools()
   for tool in tools:
       print(f"Tool: {tool['name']}")
       print(f"  Description: {tool['description']}")
       print(f"  Server: {tool['server']}")

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Issue: Slow initialization**
   Increase timeout: ``initialization_timeout=120``

**Issue: Tool not found**
   Check available tools: ``agent.list_mcp_tools()``

**Issue: Server connection failed**
   Verify prerequisites: Node.js, network access

**Issue: Memory usage high**
   Limit categories: Use specific categories instead of "all"

Debug Mode
~~~~~~~~~~

.. code-block:: python

   import logging
   
   # Enable debug logging
   logging.getLogger("haive.mcp").setLevel(logging.DEBUG)
   
   # Create agent with verbose output
   agent = EnhancedMCPAgent(
       name="debug",
       engine=AugLLMConfig(),
       mcp_categories=["core"],
       auto_install=True,
       verbose=True
   )

Best Practices
--------------

1. **Start simple** - Begin with "core" category
2. **Add categories as needed** - Don't load everything at once
3. **Reuse agents** - Initialize once, use many times
4. **Monitor health** - Regular health checks in production
5. **Handle errors** - Implement proper error handling
6. **Cache agents** - Store initialized agents for reuse

Next Steps
----------

- Explore :doc:`tutorials` for hands-on learning
- Review :doc:`examples` for code samples
- Check :doc:`guides` for architectural patterns
- Browse the :doc:`API Reference <autoapi/haive/mcp/index>`