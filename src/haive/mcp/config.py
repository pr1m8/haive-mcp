"""
MCP configuration types for flexible server management.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MCPTransport(str, Enum):
    """MCP transport types."""

    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    # Basic identification
    name: str = Field(..., description="Server name")
    enabled: bool = Field(default=True, description="Whether server is enabled")

    # Connection configuration
    transport: MCPTransport = Field(default=MCPTransport.STDIO)
    command: Optional[str] = Field(None, description="Command to start server")
    args: Optional[List[str]] = Field(
        default_factory=list, description="Command arguments"
    )
    url: Optional[str] = Field(None, description="URL for HTTP-based transports")

    # Environment and authentication
    env: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    api_key: Optional[str] = Field(None, description="API key if required")

    # Metadata
    category: Optional[str] = Field(None, description="Server category")
    description: Optional[str] = Field(None, description="Server description")
    capabilities: List[str] = Field(
        default_factory=list, description="Server capabilities"
    )

    # Advanced settings
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    retry_attempts: int = Field(default=3, description="Retry attempts on failure")
    auto_start: bool = Field(default=True, description="Auto-start server on init")
    health_check_interval: Optional[int] = Field(
        None, description="Health check interval in seconds"
    )

    class Config:
        extra = "allow"  # Allow additional fields for flexibility


class MCPConfig(BaseModel):
    """Complete MCP configuration for an agent."""

    # Control flags
    enabled: bool = Field(default=False, description="Whether MCP is enabled")
    auto_discover: bool = Field(
        default=True, description="Auto-discover servers from registry"
    )
    lazy_init: bool = Field(default=True, description="Initialize servers on-demand")

    # Server configurations
    servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)

    # Discovery settings
    discovery_paths: List[str] = Field(
        default_factory=lambda: ["~/.mcp/servers", ".mcp/servers", "mcp_servers"],
        description="Paths to search for server configs",
    )

    # Filtering
    categories: Optional[List[str]] = Field(
        None, description="Filter servers by category"
    )
    required_capabilities: Optional[List[str]] = Field(
        None, description="Required capabilities"
    )

    # Global settings
    global_timeout: int = Field(
        default=60, description="Global timeout for all operations"
    )
    max_concurrent_servers: int = Field(
        default=10, description="Max concurrent server connections"
    )
    enable_health_checks: bool = Field(
        default=True, description="Enable periodic health checks"
    )

    # Callbacks (stored as strings, resolved at runtime)
    on_server_connected: Optional[str] = Field(
        None, description="Callback when server connects"
    )
    on_server_failed: Optional[str] = Field(
        None, description="Callback when server fails"
    )
    on_tool_discovered: Optional[str] = Field(
        None, description="Callback when tool is discovered"
    )
