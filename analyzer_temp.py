def create_component_info(self, server_config):
    """Create component info for registration with component discovery.
    
    Generates a standardized component information dictionary for
    registering an MCP server with the Haive component discovery system.
    
    Args:
        server_config: MCP server configuration to register
        
    Returns:
        Dict[str, Any]: Component info containing name, type, capabilities etc.
    """
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