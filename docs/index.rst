haive-mcp Documentation
======================

Model Context Protocol (MCP) integration for the Haive AI framework.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   installation
   quickstart
   api/index
   examples
   contributing

Overview
--------

The haive-mcp package provides comprehensive MCP support for Haive, enabling:

* Discovery and management of MCP servers
* Integration with LangChain and LangGraph
* Server creation using FastMCP
* Tool, resource, and prompt management
* Seamless integration with haive-dataflow registry

Features
--------

* **Server Discovery**: Automatically discover MCP servers from npm, PyPI, GitHub, and local sources
* **Server Management**: Install, configure, and manage MCP servers
* **Tool Integration**: Seamlessly use MCP tools in your AI agents
* **FastMCP Support**: Create custom MCP servers with minimal code
* **LangChain Integration**: Use MCP tools with LangChain agents
* **Registry Integration**: Automatic registration with haive-dataflow

Quick Example
-------------

.. code-block:: python

   from haive.mcp import MCPManager, MCPConfig, MCPServerConfig
   
   # Create configuration
   config = MCPConfig(
       servers={
           "filesystem": MCPServerConfig(
               transport="stdio",
               command="npx",
               args=["-y", "@modelcontextprotocol/server-filesystem"]
           )
       }
   )
   
   # Create manager
   manager = MCPManager(config)
   await manager.initialize()
   
   # Execute a tool
   result = await manager.execute_tool(
       server="filesystem",
       tool="read_file",
       params={"path": "file.txt"}
   )

API Reference
-------------

.. autosummary::
   :toctree: api
   :recursive:

   haive.mcp

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`