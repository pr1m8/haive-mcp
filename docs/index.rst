.. haive-mcp documentation master file

haive-mcp: Model Context Protocol Integration for Haive
========================================================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started:
   :hidden:

   installation
   quickstart
   configuration

.. toctree::
   :maxdepth: 3
   :caption: API Reference:
   :hidden:

   api/modules
   api/config
   api/manager
   api/agents
   api/discovery
   api/servers

.. toctree::
   :maxdepth: 2
   :caption: User Guide:
   :hidden:

   guides/basic_usage
   guides/advanced_features
   guides/custom_servers
   guides/integration

.. toctree::
   :maxdepth: 2
   :caption: MCP Servers:
   :hidden:

   mcp_servers

.. toctree::
   :maxdepth: 2
   :caption: Development:
   :hidden:

   development
   contributing
   changelog

Welcome to haive-mcp
--------------------

**haive-mcp** provides comprehensive Model Context Protocol (MCP) integration for the Haive AI Agent Framework. 
This package combines documentation processing of 992+ MCP servers, intelligent discovery, and production-ready 
agents to make MCP servers easily accessible.

Key Features
------------

* 📚 **992+ MCP Server Database** - Pre-processed documentation from GitHub repositories
* 🤖 **Intelligent Discovery** - LLM-powered capability analysis and server matching  
* 🔧 **Auto-Configuration** - Convert documentation to working configs automatically
* 🔄 **Tool Transfer** - Share tools between agents dynamically
* 🤝 **Production Agents** - Ready-to-use agents with MCP capabilities
* ⚡ **Mass Installation** - Install all documented servers automatically
* 🛡️ **Type-Safe** - Full Pydantic model validation and error handling

Quick Example
-------------

.. code-block:: python

    from haive.mcp.agents import MCPDocumentationAgent
    from haive.core.engine import AugLLMConfig

    # Create documentation research agent  
    engine = AugLLMConfig(name="doc_research")
    doc_agent = MCPDocumentationAgent.create_for_mcp_setup(engine=engine)
    await doc_agent.setup()

    # Find servers by capability
    database_servers = await doc_agent.find_servers_by_capability("database", limit=10)
    
    # Generate implementation guide
    guide = await doc_agent.generate_implementation_guide(
        server_names=["modelcontextprotocol/server-postgres"],
        target_agent_type="development_assistant"
    )

API Documentation Overview
--------------------------

The API documentation is organized into the following sections:

Core Components
~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/generated
   :template: custom-module-template.rst
   :recursive:

   haive.mcp.config
   haive.mcp.manager

Agents
~~~~~~

.. autosummary::
   :toctree: api/generated
   :template: custom-module-template.rst
   :recursive:

   haive.mcp.agents.mcp_agent
   haive.mcp.agents.documentation_agent
   haive.mcp.agents.transferable_mcp_agent

Discovery & Installation
~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/generated
   :template: custom-module-template.rst
   :recursive:

   haive.mcp.discovery
   haive.mcp.downloader

MCP Servers
~~~~~~~~~~~

.. autosummary::
   :toctree: api/generated
   :template: custom-module-template.rst
   :recursive:

   haive.mcp.servers.dataflow_mcp_server
   haive.mcp.servers.example_server_fastmcp

Utilities
~~~~~~~~~

.. autosummary::
   :toctree: api/generated
   :template: custom-module-template.rst
   :recursive:

   haive.mcp.documentation.doc_loader
   haive.mcp.mixins.mcp_mixin

Installation
------------

.. code-block:: bash

    # Install the entire Haive package (recommended)
    poetry install --all-extras

    # Quick setup
    poetry run python install.py

    # Full setup with MCP servers
    poetry run python setup_all.py

Getting Started
---------------

To get started with haive-mcp:

1. :doc:`Install the package <installation>` with Poetry
2. :doc:`Follow the quickstart guide <quickstart>` to create your first MCP agent
3. :doc:`Learn about configuration <configuration>` options
4. Explore the API reference for detailed documentation

Examples
--------

Basic MCP Agent
~~~~~~~~~~~~~~~

.. code-block:: python

    from haive.mcp.agents import MCPAgent
    from haive.mcp.config import MCPConfig, MCPServerConfig
    
    # Configure MCP server
    config = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"]
            )
        }
    )
    
    # Create agent with MCP
    agent = MCPAgent(
        engine=engine,
        mcp_config=config,
        name="file_assistant"
    )
    
    await agent.setup()

Multi-Server Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Configure multiple servers
    config = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(...),
            "github": MCPServerConfig(...),
            "postgres": MCPServerConfig(...)
        }
    )

Contributing
------------

We welcome contributions! Please see the :doc:`Development Guide <development>` for:

* Setting up a development environment
* Code style guidelines
* Testing requirements
* Documentation standards

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`