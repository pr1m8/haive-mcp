Configuration for Multi Chat MCP Server (Google Chat)
=====================================================

This page contains configuration information for the Multi Chat MCP Server (Google Chat) MCP server.

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
       "Multi Chat MCP Server (Google Chat)": {
         "command": "npx",
         "args": ["Multi Chat MCP Server (Google Chat)"]
       }
     }
   }