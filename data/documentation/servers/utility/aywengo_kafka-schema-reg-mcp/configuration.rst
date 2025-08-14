Configuration for aywengo/kafka-schema-reg-mcp
=============================================

This page contains configuration information for the aywengo/kafka-schema-reg-mcp MCP server.

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
       "aywengo/kafka-schema-reg-mcp": {
         "command": "npx",
         "args": ["aywengo/kafka-schema-reg-mcp"]
       }
     }
   }
