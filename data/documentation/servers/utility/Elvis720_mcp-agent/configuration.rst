Configuration for Elvis720/mcp-agent
====================================

This page contains configuration information for the Elvis720/mcp-agent MCP server.

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
       "Elvis720_mcp-agent": {
         "command": "npx",
         "args": ["Elvis720/mcp-agent"]
       }
     }
   }