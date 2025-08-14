Configuration for BrightLin/mcp-server-port-cleaner
==================================================

This page contains configuration information for the BrightLin/mcp-server-port-cleaner MCP server.

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
       "BrightLin/mcp-server-port-cleaner": {
         "command": "npx",
         "args": ["BrightLin/mcp-server-port-cleaner"]
       }
     }
   }
