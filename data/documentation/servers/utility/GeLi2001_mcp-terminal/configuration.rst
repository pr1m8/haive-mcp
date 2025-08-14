Configuration for GeLi2001/mcp-terminal
======================================

This page contains configuration information for the GeLi2001/mcp-terminal MCP server.

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
       "GeLi2001/mcp-terminal": {
         "command": "npx",
         "args": ["GeLi2001/mcp-terminal"]
       }
     }
   }
