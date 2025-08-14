Configuration for Cognitive-Stack/ares-devops-mcp
================================================

This page contains configuration information for the Cognitive-Stack/ares-devops-mcp MCP server.

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
       "Cognitive-Stack/ares-devops-mcp": {
         "command": "npx",
         "args": ["Cognitive-Stack/ares-devops-mcp"]
       }
     }
   }
