Configuration for j3k0/speech.sh
================================

This page contains configuration information for the j3k0/speech.sh MCP server.

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
       "j3k0_speech.sh": {
         "command": "npx",
         "args": ["j3k0/speech.sh"]
       }
     }
   }