"""Utility functions for MCP operations.

This module provides utility functions and helpers for working with MCP servers,
including validation, parsing, logging, and common operations that are used
across the haive-mcp package.

Functions:
    validate_server_config: Validate MCP server configuration
    parse_server_response: Parse responses from MCP servers
    format_tool_description: Format tool descriptions for display
    extract_server_capabilities: Extract capabilities from server metadata
    setup_mcp_logging: Configure logging for MCP operations

Example:
    Basic utility usage::

        from haive.mcp.utils import validate_server_config, setup_mcp_logging
        from haive.mcp.config import MCPServerConfig

        # Set up MCP-specific logging
        setup_mcp_logging(level="DEBUG")

        # Validate a server configuration
        config = MCPServerConfig(
            name="my-server",
            transport="stdio",
            command="npx",
            args=["my-mcp-server"]
        )

        is_valid, errors = validate_server_config(config)
        if not is_valid:
            print(f"Configuration errors: {errors}")

Advanced Usage:
    Parsing MCP server responses::

        from haive.mcp.utils import parse_server_response

        # Parse a tool response
        response = {"result": {"data": "example"}, "error": None}
        data, error = parse_server_response(response)

        if error:
            logger.error(f"Server error: {error}")
        else:
            process_data(data)

See Also:
    haive.mcp.config: Configuration models and validation
    haive.mcp.manager: Core manager using these utilities
    haive.mcp.discovery: Discovery utilities for finding servers
"""

# Import utility functions as they are implemented
# Currently, this module serves as a namespace for future utilities

__all__ = [
    # Add exported functions here as they are implemented
    # "validate_server_config",
    # "parse_server_response",
    # "format_tool_description",
    # "extract_server_capabilities",
    # "setup_mcp_logging",
]
