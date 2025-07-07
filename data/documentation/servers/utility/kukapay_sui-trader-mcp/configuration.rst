Configuration for kukapay/sui-trader-mcp
========================================

This page contains configuration information for the kukapay/sui-trader-mcp MCP server.

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
       "kukapay_sui-trader-mcp": {
         "command": "npx",
         "args": ["kukapay/sui-trader-mcp"]
       }
     }
   }