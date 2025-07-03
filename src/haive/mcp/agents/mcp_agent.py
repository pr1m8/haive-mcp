"""MCP-enabled agent implementation that demonstrates integration with haive-agents.

This module provides a ready-to-use agent class that combines SimpleAgent capabilities
with MCP (Model Context Protocol) support. The MCPAgent class offers seamless
integration with MCP servers, automatic tool discovery, and convenient factory methods.

The agent supports:
    - Multiple MCP server connections
    - Automatic tool registration
    - Capability-based tool discovery
    - Retry logic for failed operations
    - Convenient factory methods for common patterns

Classes:
    MCPAgent: Main agent class with MCP capabilities

Functions:
    create_filesystem_agent: Factory for filesystem MCP agent
    create_github_agent: Factory for GitHub MCP agent
    create_multi_mcp_agent: Factory for multi-server MCP agent

Example:
    Creating and using an MCP agent::

        from haive.mcp.agents import MCPAgent
        from haive.mcp.config import MCPConfig, MCPServerConfig

        # Method 1: Direct instantiation
        agent = MCPAgent(
            engine=engine,
            mcp_config=MCPConfig(
                enabled=True,
                servers={
                    "fs": MCPServerConfig(
                        name="fs",
                        transport="stdio",
                        command="npx",
                        args=["-y", "@modelcontextprotocol/server-filesystem"]
                    )
                }
            )
        )

        # Method 2: Using convenience factory
        agent = MCPAgent.create_with_mcp_servers(
            engine=engine,
            server_configs={
                "filesystem": {
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"]
                }
            }
        )

        # Initialize and use
        await agent.setup()
        result = await agent.arun({"messages": [...]})
"""

from typing import Any, Dict, List, Optional, Type

from haive.agents.simple import SimpleAgent
from pydantic import Field

from haive.mcp.config import MCPConfig, MCPServerConfig, MCPTransport
from haive.mcp.mixins.mcp_mixin import MCPMixin


class MCPAgent(MCPMixin, SimpleAgent):
    """
    An agent with MCP (Model Context Protocol) capabilities.

    This agent extends SimpleAgent with the ability to connect to and use
    MCP servers for additional tools and resources.

    Example:
        ```python
        from haive.mcp.agents import MCPAgent
        from haive.mcp.config import MCPConfig, MCPServerConfig

        # Configure MCP servers
        mcp_config = MCPConfig(
            enabled=True,
            servers={
                "filesystem": MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem"],
                    capabilities=["file_read", "file_write", "directory_list"]
                ),
                "github": MCPServerConfig(
                    name="github",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-github"],
                    env={"GITHUB_TOKEN": "your_token"},
                    capabilities=["repo_access", "issue_management"]
                )
            }
        )

        # Create agent with MCP
        agent = MCPAgent(
            engine=my_engine,
            mcp_config=mcp_config,
            name="mcp_assistant"
        )

        # Tools from MCP servers are automatically available
        result = await agent.arun({
            "messages": [{"role": "user", "content": "List files in current directory"}]
        })
        ```
    """

    mcp_config: Optional[MCPConfig] = Field(
        default=None, description="MCP configuration for connecting to MCP servers"
    )

    def setup_agent(self):
        """Override setup_agent to configure MCP after base setup."""
        # Call parent setup_agent first
        super().setup_agent()
        
        # Setup MCP after base initialization
        if self.mcp_config and self.mcp_config.enabled:
            self.setup_mcp()

    async def setup(self):
        """Setup agent including MCP initialization.
        
        This async setup method should be called after agent creation
        to initialize MCP connections.
        """
        # Initialize MCP if configured
        if (
            self.mcp_config
            and self.mcp_config.enabled
            and not self.mcp_config.lazy_init
        ):
            success = await self.initialize_mcp()
            if success and self._mcp_tools:
                # Add MCP tools to agent
                await self._setup_mcp_tools()

    @classmethod
    def create_with_mcp_servers(
        cls,
        engine: Any,
        server_configs: Dict[str, Dict[str, Any]],
        name: Optional[str] = None,
        **kwargs,
    ) -> "MCPAgent":
        """Create an MCP agent with server configurations.

        Convenience factory method that simplifies agent creation by accepting
        server configurations as dictionaries instead of MCPServerConfig objects.

        Args:
            engine: The LLM engine configuration (AugLLMConfig)
            server_configs: Dictionary mapping server names to their configurations.
                Each config should include transport, command/url, and optional settings.
            name: Optional agent name (defaults to "mcp_agent")
            **kwargs: Additional agent configuration parameters

        Returns:
            MCPAgent: Configured agent instance ready for initialization

        Raises:
            ValueError: If server configurations are invalid

        Example:
            Creating an agent with multiple servers::

                agent = MCPAgent.create_with_mcp_servers(
                    engine=engine,
                    server_configs={
                        "filesystem": {
                            "transport": "stdio",
                            "command": "npx",
                            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                            "capabilities": ["file_read", "file_write"]
                        },
                        "github": {
                            "transport": "stdio",
                            "command": "npx",
                            "args": ["-y", "@modelcontextprotocol/server-github"],
                            "env": {"GITHUB_TOKEN": token}
                        }
                    },
                    name="multi_mcp_agent"
                )

                await agent.setup()
        """
        # Convert dict configs to MCPServerConfig objects
        servers = {}
        for server_name, config in server_configs.items():
            servers[server_name] = MCPServerConfig(name=server_name, **config)

        # Create MCP config
        mcp_config = MCPConfig(enabled=True, servers=servers)

        return cls(
            engine=engine, mcp_config=mcp_config, name=name or "mcp_agent", **kwargs
        )

    def get_available_capabilities(self) -> List[str]:
        """Get all available capabilities from connected MCP servers."""
        capabilities = []

        if self._mcp_initialized:
            for server_config in self._mcp_servers.values():
                capabilities.extend(server_config.capabilities)

        return list(set(capabilities))

    async def discover_tools_by_capability(self, capability: str) -> List[Any]:
        """
        Discover tools that provide a specific capability.

        Args:
            capability: The capability to search for

        Returns:
            List of tools that provide the capability
        """
        matching_tools = []

        # Find servers with the capability
        for server_name, server_config in self._mcp_servers.items():
            if capability in server_config.capabilities:
                # Get tools from this server
                server_tools = [
                    tool
                    for tool_name, tool in self._mcp_tools.items()
                    if tool_name.startswith(f"{server_name}_")
                ]
                matching_tools.extend(server_tools)

        return matching_tools

    async def call_tool_with_retry(
        self, tool_name: str, arguments: Dict[str, Any], max_retries: int = 3
    ) -> Any:
        """
        Call an MCP tool with retry logic.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            max_retries: Maximum retry attempts

        Returns:
            Tool result
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await self.call_mcp_tool(tool_name, arguments)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Check if server is still healthy
                    server_name = tool_name.split("_")[0] if "_" in tool_name else None
                    if server_name and server_name in self._failed_servers:
                        # Try to reconnect
                        await self.refresh_mcp_servers()

        raise last_error

    @property
    def tool_count(self) -> int:
        """Get total number of available tools including MCP tools."""
        base_tools = len(self.tools) if hasattr(self, "tools") else 0
        mcp_tools = len(self._mcp_tools) if self._mcp_initialized else 0
        return base_tools + mcp_tools

    def __repr__(self) -> str:
        """String representation of the agent."""
        status = self.get_mcp_status()
        return (
            f"MCPAgent(name='{self.name}', "
            f"mcp_enabled={status['enabled']}, "
            f"connected_servers={len(status['connected_servers'])}, "
            f"tool_count={status['tool_count']})"
        )


# Example usage patterns
def create_filesystem_agent(engine: Any) -> MCPAgent:
    """Create an agent with filesystem MCP server."""
    return MCPAgent.create_with_mcp_servers(
        engine=engine,
        server_configs={
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "capabilities": ["file_read", "file_write", "directory_list"],
                "description": "Access to local filesystem operations",
            }
        },
        name="filesystem_assistant",
    )


def create_github_agent(engine: Any, github_token: str) -> MCPAgent:
    """Create an agent with GitHub MCP server."""
    return MCPAgent.create_with_mcp_servers(
        engine=engine,
        server_configs={
            "github": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": github_token},
                "capabilities": ["repo_access", "issue_management", "pr_operations"],
                "description": "GitHub repository operations",
            }
        },
        name="github_assistant",
    )


def create_multi_mcp_agent(engine: Any, github_token: Optional[str] = None) -> MCPAgent:
    """Create an agent with multiple MCP servers."""
    server_configs = {
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
            "capabilities": ["file_operations"],
        },
        "time": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-time"],
            "capabilities": ["time_queries"],
        },
        "fetch": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-fetch"],
            "capabilities": ["web_fetch"],
        },
    }

    # Add GitHub if token provided
    if github_token:
        server_configs["github"] = {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": github_token},
            "capabilities": ["github_operations"],
        }

    return MCPAgent.create_with_mcp_servers(
        engine=engine, server_configs=server_configs, name="multi_mcp_assistant"
    )
