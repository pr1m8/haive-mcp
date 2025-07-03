def create_component_info(self, server_config):
    """Create component info for registration with component discovery.""" 
    return {
        "name": server_config.name,
        "component_type": "mcp", 
        "capabilities": server_config.capabilities,
        "capability_categories": ["integration"],
        "tags": ["mcp", server_config.category] if server_config.category else ["mcp"],
        "description": server_config.description or f"MCP Server: {server_config.name}",
        "config": server_config.dict(),
        "transport": server_config.transport,
        "enabled": server_config.enabled
    }