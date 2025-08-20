Haive MCP Guides
================

Welcome to the Haive MCP (Model Context Protocol) guides! This section provides comprehensive tutorials and examples for working with our MCP platform architecture.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   quickstart
   installation
   basic-usage

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts

   platform-architecture
   pydantic-patterns
   server-management

.. toctree::
   :maxdepth: 2
   :caption: Plugins

   plugin-development
   mcp-browser-plugin
   custom-plugins

.. toctree::
   :maxdepth: 2
   :caption: Advanced Usage

   fastapi-integration
   caching-strategies
   real-world-examples

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics

   performance-optimization
   troubleshooting

Overview
--------

The Haive MCP package provides **dynamic, runtime integration** with **1900+ MCP servers** for AI agents. Key features include:

* **Dynamic Tool Discovery** - Agents automatically find and integrate tools
* **1900+ MCP Servers** - Access to vast ecosystem of tools and capabilities
* **Real-time Integration** - No pre-configuration needed, tools discovered at runtime
* **Native MCP Protocol** - Full protocol compliance with STDIO transport
* **Seamless Agent Integration** - Works with all Haive agents (SimpleAgent, ReactAgent, etc.)

Quick Start
-----------

.. code-block:: python

   import asyncio
   from haive.mcp.agents.enhanced_mcp_agent import EnhancedMCPAgent
   from haive.core.engine.aug_llm import AugLLMConfig

   async def quick_example():
       # Create MCP-enhanced agent
       agent = EnhancedMCPAgent(
           name="my_agent",
           engine=AugLLMConfig(temperature=0.7),
           mcp_categories=["core"],  # Auto-install filesystem, postgres, github tools
           auto_install=True
       )

       # Initialize MCP integration
       await agent.initialize_mcp()
       
       # Use agent with dynamically discovered tools
       result = await agent.arun("List files and search for Python projects")
       print(f"Result: {result}")

   asyncio.run(quick_example())

Architecture Principles
-----------------------

Our MCP architecture follows these key principles:

1. **Agent-First Integration**

   .. code-block:: python

      class EnhancedMCPAgent(SimpleAgent):
          """MCP-enhanced agent with automatic tool discovery."""
          
          mcp_categories: List[str] = Field(default_factory=list)
          auto_install: bool = Field(default=True)
          mcp_manager: MCPManager = Field(default_factory=MCPManager)

2. **Dynamic Tool Discovery**

   .. code-block:: python

      # Agent analyzes task requirements and installs appropriate servers
      agent = EnhancedMCPAgent(mcp_categories=["core"], auto_install=True)
      await agent.initialize_mcp()  # Auto-discovers and installs tools
      
      # Tools are available immediately
      result = await agent.arun("Use filesystem and web search")

3. **Native MCP Protocol**

   .. code-block:: python

      # Real MCP protocol communication
      MCPManager → MCPServerConfig → MCPClient (STDIO) → NPM Packages
      
      # No mocks, no simulations - real MCP servers

Community and Support
---------------------

* **Documentation**: :doc:`../README` 
* **Examples**: See :doc:`real-world-examples`
* **Testing**: Follow :doc:`testing-guide`
* **Issues**: Report problems in the main Haive repository

Next Steps
----------

1. Follow the :doc:`quickstart` guide to get up and running
2. Read about :doc:`platform-architecture` to understand the design
3. Try the :doc:`mcp-browser-plugin` tutorial
4. Explore :doc:`real-world-examples` for advanced usage