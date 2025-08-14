Configuration for kennyckk/mcp_hkbus
===================================

This page contains configuration information for the kennyckk/mcp_hkbus MCP server.

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
       "kennyckk/mcp_hkbus": {
         "command": "npx",
         "args": ["kennyckk/mcp_hkbus"]
       }
     }
   }
