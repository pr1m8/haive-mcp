"""Backward compatibility layer for MCPServerManager migration.

This module provides a compatibility wrapper that allows existing code
using MCPServerManager to work with the new Pydantic-based implementation
without modification.

Example:
    Existing code will continue to work::
    
        from haive.mcp.servers import MCPServerManager  # Works via compatibility
        
        manager = MCPServerManager()
        manager.run()  # Legacy API still works
"""

import warnings
from typing import TYPE_CHECKING

from .mcp_server_manager_v2 import MCPServerManagerV2

if TYPE_CHECKING:
    from .mcp_server_manager import MCPServerManager as LegacyManager


class MCPServerManager(MCPServerManagerV2):
    """Compatibility wrapper for legacy MCPServerManager.
    
    This class provides full backward compatibility with the original
    MCPServerManager while using the new Pydantic-based implementation
    under the hood.
    
    Note:
        This is a transitional class. New code should use MCPServerManagerV2
        directly for better type safety and validation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with compatibility mode enabled."""
        # Enable legacy mode by default
        kwargs.setdefault("legacy_mode", True)
        
        # Initialize parent
        super().__init__(*args, **kwargs)
        
        # Warn about using legacy API
        warnings.warn(
            "MCPServerManager is using compatibility mode. "
            "Consider migrating to MCPServerManagerV2 for better type safety.",
            DeprecationWarning,
            stacklevel=2
        )
    
    def start_server(self, name: str, env_overrides=None):
        """Legacy synchronous start_server method."""
        return self.start_server_sync(name, env_overrides)
    
    def stop_server(self, name: str):
        """Legacy synchronous stop_server method."""
        return self.stop_server_sync(name)
    
    def check_server_startup(self, process, name, timeout=5.0):
        """Legacy synchronous startup check."""
        import asyncio
        
        # Create async wrapper
        async def _check():
            config = self.available_configs.get(name)
            if not config:
                return False, "Unknown server"
            
            info = self.info_class(transport=config.transport)
            return await self._check_mcp_startup(process, config, info, timeout)
        
        # Run in event loop
        try:
            loop = asyncio.new_event_loop()
            success = loop.run_until_complete(_check())
            loop.close()
            return success
        except Exception as e:
            return False, str(e)


def migrate_to_v2(legacy_manager: "LegacyManager") -> MCPServerManagerV2:
    """Helper to migrate from legacy to V2 manager.
    
    Args:
        legacy_manager: Existing MCPServerManager instance
        
    Returns:
        MCPServerManagerV2 with same configuration
        
    Example:
        >>> legacy = MCPServerManager()
        >>> legacy.start_server("filesystem")
        >>> v2_manager = migrate_to_v2(legacy)
        >>> # v2_manager now has same servers running
    """
    # Create V2 manager
    v2_manager = MCPServerManagerV2()
    
    # Copy configuration
    if hasattr(legacy_manager, "available_servers"):
        for name, config_dict in legacy_manager.available_servers.items():
            # Convert to new config format
            from .models import MCPServerConfig, MCPTransport
            
            transport = config_dict.get("transport", "stdio")
            if transport == "stdio":
                transport = MCPTransport.STDIO
            else:
                transport = MCPTransport.UNKNOWN
            
            new_config = MCPServerConfig(
                name=name,
                command=config_dict["command"],
                description=config_dict.get("description", ""),
                transport=transport,
                requires_env=config_dict.get("requires_env", [])
            )
            
            v2_manager.add_config(name, new_config)
    
    # Note: We can't migrate running servers as they have process handles
    # User will need to restart servers with V2 manager
    
    return v2_manager