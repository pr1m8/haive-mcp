"""MCP Server-specific models extending base server management framework.

This module provides MCP-specific server configuration and runtime information
models that extend the base server management framework from haive-dataflow.

Key Components:
    - MCPTransport: Enum for MCP transport types (stdio, http, etc.)
    - MCPServerConfig: MCP-specific server configuration
    - MCPServerInfo: MCP runtime information with transport details
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator, model_validator
from datetime import datetime, timezone

from haive.dataflow.server_management.models import BaseServerConfig, BaseServerInfo, ServerStatus


class MCPTransport(str, Enum):
    """MCP transport mechanism types.
    
    Defines the communication transport used by MCP servers.
    """
    STDIO = "stdio"      # Standard input/output transport
    HTTP = "http"        # HTTP-based transport
    WEBSOCKET = "websocket"  # WebSocket transport
    IPC = "ipc"          # Inter-process communication
    UNKNOWN = "unknown"  # Unknown or custom transport


class MCPServerConfig(BaseServerConfig):
    """MCP-specific server configuration.
    
    Extends BaseServerConfig with MCP-specific fields like transport type,
    required environment variables, and protocol version.
    
    Attributes:
        transport: MCP transport mechanism (stdio, http, etc.)
        requires_env: List of required environment variable names
        protocol_version: MCP protocol version (default: "1.0")
        capabilities: List of server capabilities/features
        endpoints: Optional endpoints for HTTP/WebSocket transports
        
    Example:
        >>> config = MCPServerConfig(
        ...     name="github",
        ...     command=["npx", "-y", "@modelcontextprotocol/server-github"],
        ...     description="GitHub repository access",
        ...     transport=MCPTransport.STDIO,
        ...     requires_env=["GITHUB_TOKEN"]
        ... )
    """
    
    transport: MCPTransport = Field(
        default=MCPTransport.STDIO,
        description="MCP transport mechanism"
    )
    
    requires_env: List[str] = Field(
        default_factory=list,
        description="Required environment variable names"
    )
    
    protocol_version: str = Field(
        default="1.0",
        pattern=r"^\d+\.\d+$",
        description="MCP protocol version"
    )
    
    capabilities: List[str] = Field(
        default_factory=list,
        description="Server capabilities (e.g., 'file_read', 'web_search')"
    )
    
    endpoints: Optional[Dict[str, str]] = Field(
        default=None,
        description="Endpoints for HTTP/WebSocket transports"
    )
    
    @field_validator("requires_env")
    @classmethod
    def validate_env_vars(cls, v: List[str]) -> List[str]:
        """Validate environment variable names."""
        for env_var in v:
            if not env_var.isidentifier():
                raise ValueError(f"Invalid environment variable name: {env_var}")
        return v
    
    @model_validator(mode="after")
    def validate_transport_config(self) -> "MCPServerConfig":
        """Validate transport-specific configuration."""
        if self.transport in [MCPTransport.HTTP, MCPTransport.WEBSOCKET]:
            if not self.endpoints:
                raise ValueError(f"{self.transport} transport requires endpoints configuration")
        return self


class MCPServerInfo(BaseServerInfo):
    """MCP-specific server runtime information.
    
    Extends BaseServerInfo with MCP-specific runtime details like transport
    info, connection status, and protocol negotiation results.
    
    Attributes:
        transport: Active transport type
        transport_info: Transport-specific connection details
        protocol_version: Negotiated protocol version
        capabilities_active: Currently active capabilities
        last_message_time: Timestamp of last message exchange
        message_count: Total messages exchanged
        
    Example:
        >>> info = MCPServerInfo(
        ...     pid=12345,
        ...     status=ServerStatus.RUNNING,
        ...     transport=MCPTransport.STDIO,
        ...     transport_info={"pipes": ["stdin", "stdout", "stderr"]}
        ... )
    """
    
    transport: MCPTransport = Field(
        default=MCPTransport.UNKNOWN,
        description="Active transport type"
    )
    
    transport_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Transport-specific connection details"
    )
    
    protocol_version: Optional[str] = Field(
        default=None,
        description="Negotiated protocol version"
    )
    
    capabilities_active: List[str] = Field(
        default_factory=list,
        description="Currently active capabilities"
    )
    
    last_message_time: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last message exchange"
    )
    
    message_count: int = Field(
        default=0,
        ge=0,
        description="Total messages exchanged"
    )
    
    def record_message(self) -> None:
        """Record a message exchange."""
        self.last_message_time = datetime.now(timezone.utc)
        self.message_count += 1
    
    def get_transport_status(self) -> str:
        """Get human-readable transport status."""
        if self.status != ServerStatus.RUNNING:
            return f"{self.transport.value} - {self.status.value}"
        
        if self.last_message_time:
            idle_time = (datetime.now(timezone.utc) - self.last_message_time).total_seconds()
            if idle_time < 60:
                return f"{self.transport.value} - Active"
            elif idle_time < 3600:
                return f"{self.transport.value} - Idle ({int(idle_time/60)}m)"
            else:
                return f"{self.transport.value} - Idle ({int(idle_time/3600)}h)"
        
        return f"{self.transport.value} - Connected"