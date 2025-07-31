Configuration for OthmaneBlial/term_mcp_deepseek
================================================

This page contains configuration information for the OthmaneBlial/term_mcp_deepseek MCP server.

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
       "OthmaneBlial_term_mcp_deepseek": {
         "command": "npx",
         "args": ["OthmaneBlial/term_mcp_deepseek"]
       }
     }
   }