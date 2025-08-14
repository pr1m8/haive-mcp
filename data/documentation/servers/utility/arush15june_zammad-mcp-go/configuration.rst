Configuration for arush15june/zammad-mcp-go
==========================================

This page contains configuration information for the arush15june/zammad-mcp-go MCP server.

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
       "arush15june/zammad-mcp-go": {
         "command": "npx",
         "args": ["arush15june/zammad-mcp-go"]
       }
     }
   }
