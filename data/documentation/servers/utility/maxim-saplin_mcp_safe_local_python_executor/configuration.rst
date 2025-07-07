Configuration for maxim-saplin/mcp_safe_local_python_executor
=============================================================

This page contains configuration information for the maxim-saplin/mcp_safe_local_python_executor MCP server.

.. contents:: Table of Contents
   :depth: 2
   :local:

Basic Configuration
-------------------

**Installation Method:** manual

**Setup Complexity:** 4/5

**Transport Types:** stdio

Environment Variables
---------------------

.. note::
   Environment variables may be required for this server to function properly.
   Check the repository documentation for specific requirements.


Transport Configuration
-----------------------

This server supports the following transport types:

* ``stdio``

For Claude Desktop configuration:

.. code-block:: json

   {
     "mcpServers": {
       "maxim-saplin_mcp_safe_local_python_executor": {
         "command": "npx",
         "args": ["maxim-saplin/mcp_safe_local_python_executor"]
       }
     }
   }