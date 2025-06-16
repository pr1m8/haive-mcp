"""
MCP mixin for adding Model Context Protocol capabilities to agents.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Set, Union

from haive.core.engine.agent.hooks import Hook, HookType
from haive.core.engine.agent.mcp_config import MCPConfig, MCPServerConfig
from pydantic import PrivateAttr

# Conditional imports
try:
    from langchain_core.tools import BaseTool
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MultiServerMCPClient = None
    BaseTool = None

logger = logging.getLogger(__name__)


class MCPMixin:
    """
    Mixin to add MCP capabilities to any agent.
    
    This mixin provides:
    - Dynamic MCP server discovery and connection
    - Automatic tool registration
    - Health monitoring
    - Graceful degradation when servers fail
    - Lazy initialization
    """
    
    # MCP configuration
    mcp_config: Optional[MCPConfig] = None
    
    # Private attributes for state management
    _mcp_client: Optional[MultiServerMCPClient] = PrivateAttr(default=None)
    _mcp_servers: Dict[str, MCPServerConfig] = PrivateAttr(default_factory=dict)
    _mcp_tools: Dict[str, BaseTool] = PrivateAttr(default_factory=dict)
    _mcp_initialized: bool = PrivateAttr(default=False)
    _failed_servers: Set[str] = PrivateAttr(default_factory=set)
    _server_health: Dict[str, Dict[str, Any]] = PrivateAttr(default_factory=dict)
    
    def __init__(self, **kwargs):
        """Initialize MCP mixin."""
        super().__init__(**kwargs)
        
        # Register hooks if MCP is configured
        if self.mcp_config and self.mcp_config.enabled:
            self._register_mcp_hooks()
    
    def _register_mcp_hooks(self):
        """Register MCP-related hooks."""
        # Tool discovery hook
        self.register_hook(Hook(
            name="mcp_tool_discovery",
            hook_type=HookType.TOOL_DISCOVERY,
            callback=self._discover_mcp_tools_hook,
            priority=100
        ))
        
        # Post-setup hook for initialization
        self.register_hook(Hook(
            name="mcp_initialization",
            hook_type=HookType.POST_SETUP,
            callback=self._initialize_mcp_hook,
            priority=90
        ))
    
    async def _initialize_mcp_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize MCP if not lazy loading."""
        if self.mcp_config and not self.mcp_config.lazy_init:
            await self.initialize_mcp()
        return context
    
    async def _discover_mcp_tools_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover and register MCP tools."""
        if not self._mcp_initialized:
            await self.initialize_mcp()
        
        # Add discovered tools to engine
        if self._mcp_tools and hasattr(self, 'engine') and hasattr(self.engine, 'tools'):
            for tool_name, tool in self._mcp_tools.items():
                if tool not in self.engine.tools:
                    self.engine.tools.append(tool)
                    
                # Update tool routes if engine supports it
                if hasattr(self.engine, 'tool_routes'):
                    self.engine.tool_routes[tool_name] = "mcp_tool_node"
        
        return context
    
    async def initialize_mcp(self) -> bool:
        """
        Initialize MCP servers and client.
        
        Returns:
            True if at least one server connected successfully
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP dependencies not available")
            return False
        
        if not self.mcp_config or not self.mcp_config.enabled:
            return False
        
        if self._mcp_initialized:
            return True
        
        try:
            # Discover servers if auto-discovery enabled
            if self.mcp_config.auto_discover:
                await self._discover_servers()
            
            # Connect to servers
            connected_servers = await self._connect_servers()
            
            if connected_servers:
                # Create MCP client with connected servers
                self._mcp_client = MultiServerMCPClient(connected_servers)
                
                # Discover tools
                await self._discover_tools()
                
                self._mcp_initialized = True
                logger.info(f"MCP initialized with {len(connected_servers)} servers")
                return True
            else:
                logger.warning("No MCP servers connected")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize MCP: {e}")
            return False
    
    async def _discover_servers(self):
        """Discover MCP servers from configured paths."""
        # This would implement server discovery from files/registry
        # For now, we'll use the configured servers
        pass
    
    async def _connect_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Connect to configured MCP servers.
        
        Returns:
            Dictionary of successfully connected server configurations
        """
        connected = {}
        
        for server_name, server_config in self.mcp_config.servers.items():
            if not server_config.enabled:
                continue
                
            if await self._test_server_connection(server_name, server_config):
                # Convert to format expected by MultiServerMCPClient
                connection_config = self._create_connection_config(server_config)
                connected[server_name] = connection_config
            else:
                self._failed_servers.add(server_name)
                logger.warning(f"Failed to connect to MCP server: {server_name}")
        
        return connected
    
    async def _test_server_connection(self, name: str, config: MCPServerConfig) -> bool:
        """Test if a server is reachable."""
        try:
            # Create temporary client to test connection
            test_config = {name: self._create_connection_config(config)}
            test_client = MultiServerMCPClient(test_config)
            
            # Try to get tools as a connection test
            await asyncio.wait_for(
                test_client.get_tools(server_name=name),
                timeout=config.timeout
            )
            
            # Clean up test client
            if hasattr(test_client, 'close'):
                await test_client.close()
                
            return True
            
        except Exception as e:
            logger.debug(f"Server {name} connection test failed: {e}")
            return False
    
    def _create_connection_config(self, server_config: MCPServerConfig) -> Dict[str, Any]:
        """Create connection configuration for MultiServerMCPClient."""
        config = {}
        
        if server_config.transport == "stdio":
            config["command"] = server_config.command
            config["args"] = server_config.args
            config["transport"] = "stdio"
        elif server_config.transport in ["sse", "streamable_http"]:
            config["url"] = server_config.url
            config["transport"] = server_config.transport
        
        # Add environment variables
        if server_config.env:
            config["env"] = server_config.env
        
        return config
    
    async def _discover_tools(self):
        """Discover tools from connected MCP servers."""
        if not self._mcp_client:
            return
        
        try:
            # Get all tools from all servers
            all_tools = await self._mcp_client.get_tools()
            
            # Store tools with server prefix for disambiguation
            for tool in all_tools:
                # Tools from MCP often have server prefix already
                tool_name = tool.name
                self._mcp_tools[tool_name] = tool
                
                # Track which server provides which tool
                server_name = tool_name.split('_')[0] if '_' in tool_name else "unknown"
                if server_name not in self._server_health:
                    self._server_health[server_name] = {"tools": []}
                self._server_health[server_name]["tools"].append(tool_name)
                
            logger.info(f"Discovered {len(self._mcp_tools)} MCP tools")
            
        except Exception as e:
            logger.error(f"Failed to discover MCP tools: {e}")
    
    @asynccontextmanager
    async def mcp_session(self, server_name: Optional[str] = None):
        """
        Context manager for MCP operations.
        
        Args:
            server_name: Optional specific server to use
            
        Yields:
            MCP client or session
        """
        if not self._mcp_initialized:
            await self.initialize_mcp()
        
        if server_name and self._mcp_client:
            # Use specific server session
            async with self._mcp_client.session(server_name) as session:
                yield session
        else:
            # Use the general client
            yield self._mcp_client
    
    async def call_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None
    ) -> Any:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            server_name: Optional specific server to use
            
        Returns:
            Tool execution result
        """
        if not self._mcp_initialized:
            await self.initialize_mcp()
        
        if tool_name not in self._mcp_tools:
            raise ValueError(f"MCP tool '{tool_name}' not found")
        
        tool = self._mcp_tools[tool_name]
        
        # Execute tool
        try:
            result = await tool.ainvoke(arguments)
            return result
        except Exception as e:
            logger.error(f"Error executing MCP tool {tool_name}: {e}")
            raise
    
    async def get_mcp_resources(
        self,
        server_name: str,
        uris: Optional[Union[str, List[str]]] = None
    ) -> List[Any]:
        """Get resources from an MCP server."""
        if not self._mcp_initialized:
            await self.initialize_mcp()
            
        if not self._mcp_client:
            raise RuntimeError("MCP client not initialized")
            
        return await self._mcp_client.get_resources(server_name, uris=uris)
    
    async def get_mcp_prompt(
        self,
        server_name: str,
        prompt_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """Get a prompt from an MCP server."""
        if not self._mcp_initialized:
            await self.initialize_mcp()
            
        if not self._mcp_client:
            raise RuntimeError("MCP client not initialized")
            
        return await self._mcp_client.get_prompt(server_name, prompt_name, arguments=arguments)
    
    def get_mcp_status(self) -> Dict[str, Any]:
        """Get current MCP status."""
        return {
            "enabled": self.mcp_config.enabled if self.mcp_config else False,
            "initialized": self._mcp_initialized,
            "connected_servers": list(set(self._mcp_servers.keys()) - self._failed_servers),
            "failed_servers": list(self._failed_servers),
            "available_tools": list(self._mcp_tools.keys()),
            "tool_count": len(self._mcp_tools)
        }
    
    async def refresh_mcp_servers(self):
        """Refresh MCP server connections."""
        # Reset state
        self._mcp_initialized = False
        self._failed_servers.clear()
        self._mcp_tools.clear()
        
        # Re-initialize
        await self.initialize_mcp()
    
    async def cleanup_mcp(self):
        """Clean up MCP resources."""
        if self._mcp_client and hasattr(self._mcp_client, 'close'):
            try:
                await self._mcp_client.close()
            except Exception as e:
                logger.error(f"Error closing MCP client: {e}")
        
        self._mcp_client = None
        self._mcp_initialized = False"""
MCP mixin for adding Model Context Protocol capabilities to agents.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Set, Union

from haive.core.engine.agent.hooks import Hook, HookType
from haive.core.engine.agent.mcp_config import MCPConfig, MCPServerConfig
from pydantic import PrivateAttr

# Conditional imports
try:
    from langchain_core.tools import BaseTool
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MultiServerMCPClient = None
    BaseTool = None

logger = logging.getLogger(__name__)


class MCPMixin:
    """
    Mixin to add MCP capabilities to any agent.
    
    This mixin provides:
    - Dynamic MCP server discovery and connection
    - Automatic tool registration
    - Health monitoring
    - Graceful degradation when servers fail
    - Lazy initialization
    """
    
    # MCP configuration
    mcp_config: Optional[MCPConfig] = None
    
    # Private attributes for state management
    _mcp_client: Optional[MultiServerMCPClient] = PrivateAttr(default=None)
    _mcp_servers: Dict[str, MCPServerConfig] = PrivateAttr(default_factory=dict)
    _mcp_tools: Dict[str, BaseTool] = PrivateAttr(default_factory=dict)
    _mcp_initialized: bool = PrivateAttr(default=False)
    _failed_servers: Set[str] = PrivateAttr(default_factory=set)
    _server_health: Dict[str, Dict[str, Any]] = PrivateAttr(default_factory=dict)
    
    def __init__(self, **kwargs):
        """Initialize MCP mixin."""
        super().__init__(**kwargs)
        
        # Register hooks if MCP is configured
        if self.mcp_config and self.mcp_config.enabled:
            self._register_mcp_hooks()
    
    def _register_mcp_hooks(self):
        """Register MCP-related hooks."""
        # Tool discovery hook
        self.register_hook(Hook(
            name="mcp_tool_discovery",
            hook_type=HookType.TOOL_DISCOVERY,
            callback=self._discover_mcp_tools_hook,
            priority=100
        ))
        
        # Post-setup hook for initialization
        self.register_hook(Hook(
            name="mcp_initialization",
            hook_type=HookType.POST_SETUP,
            callback=self._initialize_mcp_hook,
            priority=90
        ))
    
    async def _initialize_mcp_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize MCP if not lazy loading."""
        if self.mcp_config and not self.mcp_config.lazy_init:
            await self.initialize_mcp()
        return context
    
    async def _discover_mcp_tools_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover and register MCP tools."""
        if not self._mcp_initialized:
            await self.initialize_mcp()
        
        # Add discovered tools to engine
        if self._mcp_tools and hasattr(self, 'engine') and hasattr(self.engine, 'tools'):
            for tool_name, tool in self._mcp_tools.items():
                if tool not in self.engine.tools:
                    self.engine.tools.append(tool)
                    
                # Update tool routes if engine supports it
                if hasattr(self.engine, 'tool_routes'):
                    self.engine.tool_routes[tool_name] = "mcp_tool_node"
        
        return context
    
    async def initialize_mcp(self) -> bool:
        """
        Initialize MCP servers and client.
        
        Returns:
            True if at least one server connected successfully
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP dependencies not available")
            return False
        
        if not self.mcp_config or not self.mcp_config.enabled:
            return False
        
        if self._mcp_initialized:
            return True
        
        try:
            # Discover servers if auto-discovery enabled
            if self.mcp_config.auto_discover:
                await self._discover_servers()
            
            # Connect to servers
            connected_servers = await self._connect_servers()
            
            if connected_servers:
                # Create MCP client with connected servers
                self._mcp_client = MultiServerMCPClient(connected_servers)
                
                # Discover tools
                await self._discover_tools()
                
                self._mcp_initialized = True
                logger.info(f"MCP initialized with {len(connected_servers)} servers")
                return True
            else:
                logger.warning("No MCP servers connected")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize MCP: {e}")
            return False
    
    async def _discover_servers(self):
        """Discover MCP servers from configured paths."""
        # This would implement server discovery from files/registry
        # For now, we'll use the configured servers
        pass
    
    async def _connect_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Connect to configured MCP servers.
        
        Returns:
            Dictionary of successfully connected server configurations
        """
        connected = {}
        
        for server_name, server_config in self.mcp_config.servers.items():
            if not server_config.enabled:
                continue
                
            if await self._test_server_connection(server_name, server_config):
                # Convert to format expected by MultiServerMCPClient
                connection_config = self._create_connection_config(server_config)
                connected[server_name] = connection_config
            else:
                self._failed_servers.add(server_name)
                logger.warning(f"Failed to connect to MCP server: {server_name}")
        
        return connected
    
    async def _test_server_connection(self, name: str, config: MCPServerConfig) -> bool:
        """Test if a server is reachable."""
        try:
            # Create temporary client to test connection
            test_config = {name: self._create_connection_config(config)}
            test_client = MultiServerMCPClient(test_config)
            
            # Try to get tools as a connection test
            await asyncio.wait_for(
                test_client.get_tools(server_name=name),
                timeout=config.timeout
            )
            
            # Clean up test client
            if hasattr(test_client, 'close'):
                await test_client.close()
                
            return True
            
        except Exception as e:
            logger.debug(f"Server {name} connection test failed: {e}")
            return False
    
    def _create_connection_config(self, server_config: MCPServerConfig) -> Dict[str, Any]:
        """Create connection configuration for MultiServerMCPClient."""
        config = {}
        
        if server_config.transport == "stdio":
            config["command"] = server_config.command
            config["args"] = server_config.args
            config["transport"] = "stdio"
        elif server_config.transport in ["sse", "streamable_http"]:
            config["url"] = server_config.url
            config["transport"] = server_config.transport
        
        # Add environment variables
        if server_config.env:
            config["env"] = server_config.env
        
        return config
    
    async def _discover_tools(self):
        """Discover tools from connected MCP servers."""
        if not self._mcp_client:
            return
        
        try:
            # Get all tools from all servers
            all_tools = await self._mcp_client.get_tools()
            
            # Store tools with server prefix for disambiguation
            for tool in all_tools:
                # Tools from MCP often have server prefix already
                tool_name = tool.name
                self._mcp_tools[tool_name] = tool
                
                # Track which server provides which tool
                server_name = tool_name.split('_')[0] if '_' in tool_name else "unknown"
                if server_name not in self._server_health:
                    self._server_health[server_name] = {"tools": []}
                self._server_health[server_name]["tools"].append(tool_name)
                
            logger.info(f"Discovered {len(self._mcp_tools)} MCP tools")
            
        except Exception as e:
            logger.error(f"Failed to discover MCP tools: {e}")
    
    @asynccontextmanager
    async def mcp_session(self, server_name: Optional[str] = None):
        """
        Context manager for MCP operations.
        
        Args:
            server_name: Optional specific server to use
            
        Yields:
            MCP client or session
        """
        if not self._mcp_initialized:
            await self.initialize_mcp()
        
        if server_name and self._mcp_client:
            # Use specific server session
            async with self._mcp_client.session(server_name) as session:
                yield session
        else:
            # Use the general client
            yield self._mcp_client
    
    async def call_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None
    ) -> Any:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            server_name: Optional specific server to use
            
        Returns:
            Tool execution result
        """
        if not self._mcp_initialized:
            await self.initialize_mcp()
        
        if tool_name not in self._mcp_tools:
            raise ValueError(f"MCP tool '{tool_name}' not found")
        
        tool = self._mcp_tools[tool_name]
        
        # Execute tool
        try:
            result = await tool.ainvoke(arguments)
            return result
        except Exception as e:
            logger.error(f"Error executing MCP tool {tool_name}: {e}")
            raise
    
    async def get_mcp_resources(
        self,
        server_name: str,
        uris: Optional[Union[str, List[str]]] = None
    ) -> List[Any]:
        """Get resources from an MCP server."""
        if not self._mcp_initialized:
            await self.initialize_mcp()
            
        if not self._mcp_client:
            raise RuntimeError("MCP client not initialized")
            
        return await self._mcp_client.get_resources(server_name, uris=uris)
    
    async def get_mcp_prompt(
        self,
        server_name: str,
        prompt_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """Get a prompt from an MCP server."""
        if not self._mcp_initialized:
            await self.initialize_mcp()
            
        if not self._mcp_client:
            raise RuntimeError("MCP client not initialized")
            
        return await self._mcp_client.get_prompt(server_name, prompt_name, arguments=arguments)
    
    def get_mcp_status(self) -> Dict[str, Any]:
        """Get current MCP status."""
        return {
            "enabled": self.mcp_config.enabled if self.mcp_config else False,
            "initialized": self._mcp_initialized,
            "connected_servers": list(set(self._mcp_servers.keys()) - self._failed_servers),
            "failed_servers": list(self._failed_servers),
            "available_tools": list(self._mcp_tools.keys()),
            "tool_count": len(self._mcp_tools)
        }
    
    async def refresh_mcp_servers(self):
        """Refresh MCP server connections."""
        # Reset state
        self._mcp_initialized = False
        self._failed_servers.clear()
        self._mcp_tools.clear()
        
        # Re-initialize
        await self.initialize_mcp()
    
    async def cleanup_mcp(self):
        """Clean up MCP resources."""
        if self._mcp_client and hasattr(self._mcp_client, 'close'):
            try:
                await self._mcp_client.close()
            except Exception as e:
                logger.error(f"Error closing MCP client: {e}")
        
        self._mcp_client = None
        self._mcp_initialized = False