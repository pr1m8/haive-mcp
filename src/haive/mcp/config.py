"""MCP configuration types for flexible server management.

This module provides Pydantic models for configuring Model Context Protocol (MCP)
servers and their integration with Haive agents. It includes comprehensive validation
and type safety for all MCP-related configurations.

The configuration system supports:
    - Multiple transport types (stdio, SSE, HTTP streaming, Docker)
    - Server-specific settings and capabilities
    - Environment variables and authentication
    - Discovery and filtering options
    - Health monitoring and retry logic

Classes:
    MCPTransport: Enumeration of supported MCP transport types
    MCPServerConfig: Configuration for individual MCP servers
    MCPConfig: Complete MCP configuration for agents

Examples:
    Creating an MCP server configuration:

    .. code-block:: python

        from haive.mcp.config import MCPConfig, MCPServerConfig, MCPTransport

        # Configure a filesystem MCP server
        fs_server = MCPServerConfig(
            name="filesystem",
            transport=MCPTransport.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            capabilities=["file_read", "file_write", "directory_list"],
            category="filesystem",
            description="Local filesystem operations"
        )

        # Create complete MCP config
        config = MCPConfig(
            enabled=True,
            servers={"filesystem": fs_server},
            auto_discover=True,
            lazy_init=True
        )

Note:
    All configuration models use Pydantic v2 for validation and serialization.
"""

from enum import Enum

from pydantic import BaseModel, Field


class MCPTransport(str, Enum):
    """MCP transport types.

    Defines the communication transport mechanisms supported by MCP servers.

    Attributes:
        STDIO: Standard input/output communication (default for CLI-based servers)
        SSE: Server-Sent Events for HTTP-based streaming
        STREAMABLE_HTTP: HTTP streaming for continuous data transfer
        DOCKER: Run MCP server inside a Docker container via stdio
    """

    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"
    DOCKER = "docker"


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server.

    Represents the complete configuration needed to connect to and use an MCP server.
    Supports multiple transport types and provides extensive customization options.

    Attributes:
        name: Unique identifier for the server
        enabled: Whether this server should be activated
        transport: Communication transport type (stdio, sse, streamable_http, docker)
        command: Executable command for stdio transport, or Docker image for docker transport
        args: Command arguments for stdio transport, or extra ``docker run`` flags for docker
        url: Server URL for HTTP-based transports
        env: Environment variables to set when starting server / passed to container
        api_key: Optional API key for authentication
        category: Server category for organization (e.g., "filesystem", "database")
        description: Human-readable description of server functionality
        capabilities: List of capabilities provided by the server
        timeout: Connection timeout in seconds
        retry_attempts: Number of retry attempts on connection failure
        auto_start: Whether to automatically start the server
        health_check_interval: Interval for health checks in seconds
        docker_volumes: Volume mounts for docker transport (e.g., ``["/host/path:/container/path"]``)
        docker_ports: Port mappings for docker transport (e.g., ``["8080:8080"]``)
        docker_network: Docker network to attach to (e.g., ``"host"``)

    Examples:
        Creating a GitHub MCP server config:

        .. code-block:: python

            config = MCPServerConfig(
                name="github",
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env={"GITHUB_TOKEN": "your_token"},
                capabilities=["repo_access", "issue_management"],
                category="development",
                description="GitHub repository operations"
            )
    """

    # Basic identification
    name: str = Field(..., description="Server name")
    enabled: bool = Field(default=True, description="Whether server is enabled")

    # Connection configuration
    transport: MCPTransport = Field(default=MCPTransport.STDIO)
    command: str | None = Field(None, description="Command to start server")
    args: list[str] | None = Field(
        default_factory=list, description="Command arguments"
    )
    url: str | None = Field(None, description="URL for HTTP-based transports")

    # Environment and authentication
    env: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    api_key: str | None = Field(None, description="API key if required")

    # Metadata
    category: str | None = Field(None, description="Server category")
    description: str | None = Field(None, description="Server description")
    capabilities: list[str] = Field(
        default_factory=list, description="Server capabilities"
    )

    # Advanced settings
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    retry_attempts: int = Field(default=3, description="Retry attempts on failure")
    auto_start: bool = Field(default=True, description="Auto-start server on init")
    health_check_interval: int | None = Field(
        None, description="Health check interval in seconds"
    )

    # Docker transport settings
    docker_volumes: list[str] = Field(
        default_factory=list,
        description="Volume mounts for docker transport (e.g., ['/host:/container'])",
    )
    docker_ports: list[str] = Field(
        default_factory=list,
        description="Port mappings for docker transport (e.g., ['8080:8080'])",
    )
    docker_network: str | None = Field(
        None, description="Docker network to attach to"
    )

    model_config = {"extra": "allow"}  # Allow additional fields for flexibility


class MCPConfig(BaseModel):
    """Complete MCP configuration for an agent.

    This class provides the main configuration structure for MCP integration with Haive agents.
    It controls server discovery, filtering, initialization, and runtime behavior.

    Attributes:
        enabled: Whether MCP functionality is enabled
        auto_discover: Automatically discover servers from configured paths
        lazy_init: Initialize servers on-demand rather than at startup
        servers: Dictionary mapping server names to their configurations
        discovery_paths: List of paths to search for MCP server configurations
        categories: Optional filter for server categories
        required_capabilities: Optional list of required server capabilities
        global_timeout: Timeout for all MCP operations in seconds
        max_concurrent_servers: Maximum number of concurrent server connections
        enable_health_checks: Whether to enable periodic server health checks
        on_server_connected: Optional callback name when server connects
        on_server_failed: Optional callback name when server fails
        on_tool_discovered: Optional callback name when tool is discovered

    Examples:
        Creating a comprehensive MCP configuration:

        .. code-block:: python

            config = MCPConfig(
                enabled=True,
                servers={
                    "filesystem": MCPServerConfig(...),
                    "github": MCPServerConfig(...),
                },
                categories=["development", "filesystem"],
                required_capabilities=["file_read"],
                global_timeout=120,
                max_concurrent_servers=5
            )
    """

    # Control flags
    enabled: bool = Field(default=False, description="Whether MCP is enabled")
    auto_discover: bool = Field(
        default=True, description="Auto-discover servers from registry"
    )
    lazy_init: bool = Field(default=True, description="Initialize servers on-demand")

    # Server configurations
    servers: dict[str, MCPServerConfig] = Field(default_factory=dict)

    # Discovery settings
    discovery_paths: list[str] = Field(
        default_factory=lambda: ["~/.mcp/servers", ".mcp/servers", "mcp_servers"],
        description="Paths to search for server configs",
    )

    # Filtering
    categories: list[str] | None = Field(None, description="Filter servers by category")
    required_capabilities: list[str] | None = Field(
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
    on_server_connected: str | None = Field(
        None, description="Callback when server connects"
    )
    on_server_failed: str | None = Field(None, description="Callback when server fails")
    on_tool_discovered: str | None = Field(
        None, description="Callback when tool is discovered"
    )
