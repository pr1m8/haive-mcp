Configuration for falahgs/Brave-Gemini-Research-MCP-Server
=========================================================

This page contains configuration information for the falahgs/Brave-Gemini-Research-MCP-Server MCP server.

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
       "falahgs/Brave-Gemini-Research-MCP-Server": {
         "command": "npx",
         "args": ["falahgs/Brave-Gemini-Research-MCP-Server"]
       }
     }
   }
