Configuration for NFTGo/mcp-nftgo-api
====================================

This page contains configuration information for the NFTGo/mcp-nftgo-api MCP server.

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
       "NFTGo/mcp-nftgo-api": {
         "command": "npx",
         "args": ["NFTGo/mcp-nftgo-api"]
       }
     }
   }
