Configuration for kaz56-t/mcp-latest-document
============================================

This page contains configuration information for the kaz56-t/mcp-latest-document MCP server.

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
       "kaz56-t/mcp-latest-document": {
         "command": "npx",
         "args": ["kaz56-t/mcp-latest-document"]
       }
     }
   }
