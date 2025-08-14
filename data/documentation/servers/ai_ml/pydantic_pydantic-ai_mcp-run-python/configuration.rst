Configuration for pydantic/pydantic-ai/mcp-run-python
====================================================

This page contains configuration information for the pydantic/pydantic-ai/mcp-run-python MCP server.

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
       "pydantic/pydantic-ai/mcp-run-python": {
         "command": "npx",
         "args": ["pydantic/pydantic-ai/mcp-run-python"]
       }
     }
   }
