Getting Started
===============

Welcome to haive-mcp! Get up and running with 1900+ MCP servers in minutes.

Quick Install
-------------

Install haive-mcp with a single command:

.. code-block:: bash

   pip install haive-mcp

That's it! No complex setup, no configuration files. The system automatically discovers and installs MCP servers as needed.

Your First Agent
----------------

Create an MCP-enabled agent in just a few lines:

.. code-block:: python

   import asyncio
   from haive.mcp.agents.enhanced_mcp_agent import EnhancedMCPAgent
   from haive.core.engine.aug_llm import AugLLMConfig

   async def main():
       # Create agent with automatic MCP discovery
       agent = EnhancedMCPAgent(
           name="my_assistant",
           engine=AugLLMConfig(temperature=0.7),
           mcp_categories=["core"],  # Auto-install filesystem, database, search
           auto_install=True
       )
       
       # Initialize (discovers and installs needed servers)
       await agent.initialize_mcp()
       
       # Use the agent - tools are automatically available!
       result = await agent.arun("List all Python files in the current directory")
       print(result)

   asyncio.run(main())

Key Features
------------

Zero Configuration
~~~~~~~~~~~~~~~~~~

Haive-mcp works out of the box:

- **No manual installation** of MCP servers
- **No configuration files** to write
- **No tool registration** needed
- **Automatic discovery** from 1900+ servers

Dynamic Discovery
~~~~~~~~~~~~~~~~~

The agent analyzes your task and automatically finds the right tools:

.. code-block:: python

   # Agent automatically discovers file tools for this task
   await agent.arun("Organize my documents by date")
   
   # Agent automatically discovers web search tools for this task
   await agent.arun("Research the latest AI developments")
   
   # Agent automatically discovers database tools for this task
   await agent.arun("Query the customer database for recent orders")

Rich Ecosystem
~~~~~~~~~~~~~~

Access to 1900+ MCP servers across categories:

- **Core Tools**: Filesystem, database, web search
- **AI Enhanced**: LLM integrations, embeddings, analysis
- **Developer Tools**: GitHub, code analysis, documentation
- **Data Tools**: Processing, visualization, transformation
- **Communication**: Email, Slack, notifications
- **And much more!**

Common Use Cases
----------------

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
   
   # The agent handles complex file operations
   await agent.arun("Organize all images by date taken and remove duplicates")

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
   
   # Analyze data with automatic tool selection
   await agent.arun("Analyze sales.csv and create a trend report with visualizations")

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
   
   # Research with web tools
   await agent.arun("Research competitors' pricing strategies and create a comparison")

Understanding Categories
------------------------

MCP servers are organized into logical categories:

**core**
   Essential everyday tools - filesystem, database, web search

**ai_enhanced**
   AI-powered capabilities - LLM chains, embeddings, analysis

**enhanced_filesystem**
   Advanced file operations - bulk processing, smart organization

**time_utilities**
   Date and scheduling - calendars, reminders, time zones

**browser_automation**
   Web interaction - scraping, testing, automation

**crypto_finance**
   Financial tools - trading, blockchain, analytics

**github_enhanced**
   Development tools - code analysis, PR management

**notifications**
   Communication - alerts, emails, messaging

Prerequisites
-------------

System Requirements
~~~~~~~~~~~~~~~~~~~

- Python 3.8 or higher
- Node.js 18+ (for NPM-based servers)
- 2GB RAM minimum
- Internet connection (for auto-discovery)

Optional Components
~~~~~~~~~~~~~~~~~~~

These enhance functionality but aren't required:

- Docker (for containerized servers)
- Git (for repository-based servers)
- Redis (for distributed caching)

Verification
------------

Verify your installation:

.. code-block:: python

   from haive.mcp import verify_installation
   
   # Check installation
   status = verify_installation()
   print(f"Installation status: {status}")
   
   # List available categories
   from haive.mcp.discovery import list_categories
   categories = list_categories()
   print(f"Available categories: {categories}")
   
   # Check server count
   from haive.mcp.registry import count_available_servers
   count = count_available_servers()
   print(f"Available servers: {count}")  # Should show 1900+

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Import Error**
   Ensure haive-mcp is installed: ``pip install haive-mcp``

**Node.js Not Found**
   Install Node.js from https://nodejs.org/ (v18+ required)

**Slow First Run**
   Initial discovery and caching takes time. Subsequent runs are faster.

**Connection Timeout**
   Check internet connection. Increase timeout: ``initialization_timeout=120``

Debug Mode
~~~~~~~~~~

Enable debug output for troubleshooting:

.. code-block:: python

   import logging
   logging.getLogger("haive.mcp").setLevel(logging.DEBUG)
   
   # Create agent with verbose output
   agent = EnhancedMCPAgent(
       name="debug",
       engine=AugLLMConfig(),
       mcp_categories=["core"],
       auto_install=True,
       verbose=True
   )

Getting Help
------------

Resources
~~~~~~~~~

- **Documentation**: Full docs at :doc:`index`
- **Tutorials**: Step-by-step guides at :doc:`tutorials`
- **Examples**: Code samples at :doc:`examples`
- **API Reference**: Detailed API at :doc:`autoapi/haive/mcp/index`

Community
~~~~~~~~~

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Discord**: Real-time help from the community

Next Steps
----------

Now that you're up and running:

1. **Follow the tutorials** - :doc:`tutorials` for hands-on learning
2. **Explore examples** - :doc:`examples` for real-world patterns
3. **Read the guides** - :doc:`guides` for best practices
4. **Check the API** - :doc:`autoapi/haive/mcp/index` for detailed reference

Welcome to the world of 1900+ MCP servers at your fingertips!