Installation
============

Installing haive-mcp
--------------------

The haive-mcp package is part of the Haive framework. You can install it using Poetry:

.. code-block:: bash

    # Install the entire Haive package (recommended)
    poetry install --all-extras

    # Or install just the MCP components
    poetry install --extras mcp

Prerequisites
-------------

Before using haive-mcp, you'll need:

1. **Python 3.9+**
2. **Node.js 16+** (for MCP servers)
3. **Git** (for server discovery)

Optional Dependencies
--------------------

For full functionality, install these optional dependencies:

.. code-block:: bash

    # For MCP server adapters
    pip install langchain-mcp-adapters

    # For FastMCP server development
    pip install fastmcp

    # For documentation building
    pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

MCP Server Installation
----------------------

Many MCP servers are available as npm packages. Install them globally:

.. code-block:: bash

    # Filesystem server
    npm install -g @modelcontextprotocol/server-filesystem

    # GitHub server
    npm install -g @modelcontextprotocol/server-github

    # PostgreSQL server
    npm install -g @modelcontextprotocol/server-postgres

Verification
-----------

Verify your installation:

.. code-block:: python

    # Test basic import
    from haive.mcp import MCPConfig, MCPServerConfig, MCPManager
    print("✓ haive-mcp imported successfully")

    # Test MCP server discovery
    from haive.mcp.discovery import discover_servers
    servers = await discover_servers()
    print(f"✓ Found {len(servers)} MCP servers")

Development Installation
-----------------------

For development, clone the repository and install in editable mode:

.. code-block:: bash

    git clone https://github.com/your-repo/haive
    cd haive
    poetry install --all-extras --with dev

    # Run tests
    poetry run pytest packages/haive-mcp/tests/

Troubleshooting
--------------

Common Issues
~~~~~~~~~~~~~

**ImportError: No module named 'mcp'**
    Install the MCP adapters: ``pip install langchain-mcp-adapters``

**MCP server not found**
    Ensure the server is installed globally with npm and accessible in PATH

**Permission denied when starting server**
    Check that npm global packages are installed correctly and have proper permissions

**Connection timeout**
    Increase the timeout in MCPServerConfig or check server startup time

Getting Help
~~~~~~~~~~~~

If you encounter issues:

1. Check the `troubleshooting guide <troubleshooting.html>`_
2. Review the `examples <examples.html>`_
3. File an issue on the GitHub repository
4. Join the community Discord for real-time help