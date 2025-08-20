"""Registry management for MCP servers.

This module provides tools for managing the MCP server registry, including:
- Converting GitHub repositories to npm package format
- Validating npm package existence
- Organizing servers into categories
- Expanding the registry from the 1900+ server database

The registry system supports Phase 3+ of the MCP implementation plan,
focusing on package-based installation rather than Git cloning.
"""

from .server_converter import ServerConverter, ServerConversion, NPMPackageValidator

__all__ = [
    "ServerConverter", 
    "ServerConversion", 
    "NPMPackageValidator"
]