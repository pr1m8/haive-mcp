Configuration for offorte/offorte-mcp-server
============================================

This page contains configuration information for the offorte/offorte-mcp-server MCP server.

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
       "offorte_offorte-mcp-server": {
         "command": "npx",
         "args": ["offorte/offorte-mcp-server"]
       }
     }
   }