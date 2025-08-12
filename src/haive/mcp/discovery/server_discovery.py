"""Simple MCP server discovery placeholder."""

from typing import Any


class MCPServerDiscovery:
    """Placeholder for MCP server discovery."""

    def __init__(self):
        """Initialize discovery."""
        self.discovered_servers = {}

    async def discover_all(self) -> dict[str, Any]:
        """Discover all servers - placeholder."""
        return {}

    def get_discovery_report(self) -> dict[str, Any]:
        """Get discovery report - placeholder."""
        return {"servers": 0, "sources": []}

    def create_mcp_config(self) -> dict[str, Any]:
        """Create MCP config - placeholder."""
        return {}


# Module-level functions for compatibility
def get_discovery_report() -> dict[str, Any]:
    """Get discovery report - creates a temporary instance."""
    discovery = MCPServerDiscovery()
    return discovery.get_discovery_report()


def create_mcp_config() -> dict[str, Any]:
    """Create MCP config - creates a temporary instance."""
    discovery = MCPServerDiscovery()
    return discovery.create_mcp_config()
