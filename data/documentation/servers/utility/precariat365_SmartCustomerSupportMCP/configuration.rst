Configuration for precariat365/SmartCustomerSupportMCP
=====================================================

This page contains configuration information for the precariat365/SmartCustomerSupportMCP MCP server.

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
       "precariat365/SmartCustomerSupportMCP": {
         "command": "npx",
         "args": ["precariat365/SmartCustomerSupportMCP"]
       }
     }
   }
