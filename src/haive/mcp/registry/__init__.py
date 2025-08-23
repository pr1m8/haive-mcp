"""Registry Management for MCP Servers.

This module provides comprehensive tools for managing the MCP server registry,
supporting the transition from Git-based to NPM package-based server distribution.

Key Features
------------

**Server Registry Management**
    - Converting GitHub repositories to npm package format
    - Validating npm package existence and compatibility
    - Organizing servers into logical categories
    - Expanding the registry from the 1900+ server database

**Phase 3+ Implementation**
    The registry system supports Phase 3+ of the MCP implementation plan,
    focusing on package-based installation rather than Git cloning for
    improved reliability and performance.

Available Classes
-----------------

Server Management
~~~~~~~~~~~~~~~~~
- :class:`ServerConverter` - Convert GitHub repos to npm packages
- :class:`ServerConverterConfig` - Configuration for server conversion

Registry Operations
~~~~~~~~~~~~~~~~~~~
- **Package Validation**: Verify npm package existence
- **Category Organization**: Logical server grouping
- **Database Expansion**: Scale from existing server collections

Usage Example
-------------

.. code-block:: python

    from haive.mcp.registry import ServerConverter

    # Convert GitHub repo to npm package
    converter = ServerConverter()
    package_info = converter.convert_repo_to_package(
        "github.com/user/mcp-server",
        category="development"
    )

.. seealso::
   - :mod:`haive.mcp.downloader` for package installation
   - :mod:`haive.mcp.discovery` for server discovery
"""

from .server_converter import ServerConverter, ServerConversion, NPMPackageValidator

__all__ = [
    "ServerConverter", 
    "ServerConversion", 
    "NPMPackageValidator"
]