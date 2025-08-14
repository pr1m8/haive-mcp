Configuration for MVA-MCP-servers/filesystem
===========================================

This page contains configuration information for the MVA-MCP-servers/filesystem MCP server.

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
       "MVA-MCP-servers/filesystem": {
         "command": "npx",
         "args": ["MVA-MCP-servers/filesystem"]
       }
     }
   }
