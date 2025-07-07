Configuration for ktanaka101/mcp-server-duckdb
==============================================

This page contains configuration information for the ktanaka101/mcp-server-duckdb MCP server.

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
       "ktanaka101_mcp-server-duckdb": {
         "command": "npx",
         "args": ["ktanaka101/mcp-server-duckdb"]
       }
     }
   }