Configuration for <div align="center"><img src="https://raw.githubusercontent.com/pietrozullo/mcp-use/refs/heads/main/docs/favicon.svg" height="20"/></div>
===========================================================================================================================================================

This page contains configuration information for the <div align="center"><img src="https://raw.githubusercontent.com/pietrozullo/mcp-use/refs/heads/main/docs/favicon.svg" height="20"/></div> MCP server.

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
       "<div align="center"><img src="https:__raw.githubusercontent.com_pietrozullo_mcp-use_refs_heads_main_docs_favicon.svg" height="20"_><_div>": {
         "command": "npx",
         "args": ["<div align="center"><img src="https://raw.githubusercontent.com/pietrozullo/mcp-use/refs/heads/main/docs/favicon.svg" height="20"/></div>"]
       }
     }
   }