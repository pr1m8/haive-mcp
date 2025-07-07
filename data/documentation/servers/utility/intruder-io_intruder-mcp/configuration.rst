Configuration for intruder-io/intruder-mcp
==========================================

This page contains configuration information for the intruder-io/intruder-mcp MCP server.

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
       "intruder-io_intruder-mcp": {
         "command": "npx",
         "args": ["intruder-io/intruder-mcp"]
       }
     }
   }