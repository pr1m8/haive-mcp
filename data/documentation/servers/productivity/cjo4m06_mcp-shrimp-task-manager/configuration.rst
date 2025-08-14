Configuration for cjo4m06/mcp-shrimp-task-manager
================================================

This page contains configuration information for the cjo4m06/mcp-shrimp-task-manager MCP server.

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
       "cjo4m06/mcp-shrimp-task-manager": {
         "command": "npx",
         "args": ["cjo4m06/mcp-shrimp-task-manager"]
       }
     }
   }
