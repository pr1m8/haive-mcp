"""MCP Server management module exports.

This module provides both the legacy MCPServerManager and the new
Pydantic-based MCPServerManagerV2 for managing Model Context Protocol servers.

Migration path:
    - Existing code can continue using MCPServerManager (with deprecation warning)
    - New code should use MCPServerManagerV2 for type safety
    - Use migrate_to_v2() helper to transition existing instances
"""

from haive.mcp.servers.dataflow_mcp_server import AgentCreationRequest
from haive.mcp.servers.http_server import run_server
from haive.mcp.servers.simple_http_server import create_app

# Import V2 and models first
from haive.mcp.servers.mcp_server_manager_v2 import MCPServerManagerV2
from haive.mcp.servers.models import MCPServerConfig, MCPServerInfo, MCPTransport

# Import compatibility wrapper (provides MCPServerManager)
from haive.mcp.servers.compatibility import MCPServerManager, migrate_to_v2

# SSEServerTransport = None  # TODO: Implement SSE transport

__all__ = [
    # Legacy exports (for compatibility)
    "AgentCreationRequest",
    "SSEServerTransport", 
    "create_app",
    "run_server",
    "MCPServerManager",
    
    # New V2 exports
    "MCPServerManagerV2",
    "MCPServerConfig",
    "MCPServerInfo", 
    "MCPTransport",
    "migrate_to_v2",
]
