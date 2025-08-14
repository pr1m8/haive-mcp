Configuration for charlesverge/mcp_open_interest
===============================================

This page contains configuration information for the charlesverge/mcp_open_interest MCP server.

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
       "charlesverge/mcp_open_interest": {
         "command": "npx",
         "args": ["charlesverge/mcp_open_interest"]
       }
     }
   }
