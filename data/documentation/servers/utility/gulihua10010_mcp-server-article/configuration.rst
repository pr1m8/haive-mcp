Configuration for gulihua10010/mcp-server-article
================================================

This page contains configuration information for the gulihua10010/mcp-server-article MCP server.

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
       "gulihua10010/mcp-server-article": {
         "command": "npx",
         "args": ["gulihua10010/mcp-server-article"]
       }
     }
   }
