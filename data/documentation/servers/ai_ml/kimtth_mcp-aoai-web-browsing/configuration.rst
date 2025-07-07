Configuration for kimtth/mcp-aoai-web-browsing
==============================================

This page contains configuration information for the kimtth/mcp-aoai-web-browsing MCP server.

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
       "kimtth_mcp-aoai-web-browsing": {
         "command": "npx",
         "args": ["kimtth/mcp-aoai-web-browsing"]
       }
     }
   }