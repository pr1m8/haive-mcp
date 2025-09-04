Tutorials
=========

Welcome to the haive-mcp tutorials! These hands-on guides will walk you through using the Model Context Protocol (MCP) with Haive's 1900+ available servers.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   tutorials/01_understanding_mcp
   tutorials/02_first_mcp_server  
   tutorials/03_installer_types

Tutorial Overview
-----------------

**Tutorial 1: Understanding MCP**
   Learn what MCP is and how it enables dynamic tool integration with 1900+ available servers.

**Tutorial 2: Your First MCP Server**
   Create your first agent with automatic MCP server discovery and installation.

**Tutorial 3: Installer Types**
   Understand how different MCP servers are installed automatically behind the scenes.

Quick Start
-----------

Jump right in with a simple example:

.. code-block:: python

   import asyncio
   from haive.mcp.agents.enhanced_mcp_agent import EnhancedMCPAgent
   from haive.core.engine.aug_llm import AugLLMConfig

   async def quick_start():
       # Agent automatically discovers and installs tools from 1900+ servers
       agent = EnhancedMCPAgent(
           name="my_agent",
           engine=AugLLMConfig(),
           mcp_categories=["core"],  # Auto-install filesystem, database, search
           auto_install=True
       )
       
       await agent.initialize_mcp()
       result = await agent.arun("List files in current directory")
       print(result)

   asyncio.run(quick_start())

Next Steps
----------

After completing the tutorials:

- Explore the :doc:`examples` for real-world use cases
- Check out the :doc:`guides` for advanced topics
- Browse the :doc:`API Reference <autoapi/haive/mcp/index>` for detailed documentation