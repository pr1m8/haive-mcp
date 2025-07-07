Configuration for alimo7amed93/webhook-tester-mcp
=================================================

This page contains configuration information for the alimo7amed93/webhook-tester-mcp MCP server.

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
       "alimo7amed93_webhook-tester-mcp": {
         "command": "npx",
         "args": ["alimo7amed93/webhook-tester-mcp"]
       }
     }
   }