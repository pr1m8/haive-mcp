Configuration for Nebula-Block-Data/nebulablock-mcp-server
=========================================================

This page contains configuration information for the Nebula-Block-Data/nebulablock-mcp-server MCP server.

.. contents:: Table of Contents
   :depth: 2
   :local:

Basic Configuration
-------------------

**Installation Method:** npm

**Setup Complexity:** 1/5

**Transport Types:** stdio

Environment Variables
---------------------

.. note::
   Environment variables may be required for this server to function properly.
   Check the repository documentation for specific requirements.

No environment variables documented.

Transport Configuration
-----------------------

This server supports the following transport types:

* ``stdio``

For Claude Desktop configuration:

.. code-block:: json

   {
     "mcpServers": {
       "Nebula-Block-Data/nebulablock-mcp-server": {
         "command": "npx",
         "args": ["Nebula-Block-Data/nebulablock-mcp-server"]
       }
     }
   }
