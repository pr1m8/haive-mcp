#!/usr/bin/env python3
"""Haive Dataflow MCP Server - Provides access to haive-dataflow registry and components."""

import asyncio
import json
import logging
from typing import Any

from haive.dataflow import (
    EntityType,
    discover_agents,
    discover_engines,
    discover_tools,
    registry_system,
)
from mcp.server.fastmcp import FastMCP

# Import haive-dataflow components
try:
    DATAFLOW_AVAILABLE = True
except ImportError:
    DATAFLOW_AVAILABLE = False
    logging.warning("haive-dataflow not available. Some features will be disabled.")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("haive-dataflow-server")


# Registry Tools
@mcp.tool()
async def list_components(component_type: str = "all") -> dict[str, Any]:
    """List components registered in haive-dataflow.

    Args:
        component_type: Type of components to list (agent, tool, engine, game, mcp_server, or all)

    Returns:
        Dictionary of components by type
    """
    if not DATAFLOW_AVAILABLE:
        return {"error": "haive-dataflow not available"}

    try:
        results = {}

        if component_type == "all":
            # Get all component types
            for entity_type in EntityType:
                components = registry_system.get_entities_by_type(entity_type)
                results[entity_type.value] = [
                    {
                        "name": c.get("name", "Unknown"),
                        "description": c.get("description", ""),
                        "id": c.get("id", ""),
                    }
                    for c in components
                ]
        else:
            # Get specific type
            try:
                entity_type = EntityType(component_type)
                components = registry_system.get_entities_by_type(entity_type)
                results[component_type] = [
                    {
                        "name": c.get("name", "Unknown"),
                        "description": c.get("description", ""),
                        "id": c.get("id", ""),
                        "metadata": c.get("metadata", {}),
                    }
                    for c in components
                ]
            except ValueError:
                return {"error": f"Invalid component type: {component_type}"}

        return results

    except Exception as e:
        logger.error(f"Error listing components: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_component_details(component_id: str) -> dict[str, Any]:
    """Get detailed information about a specific component.

    Args:
        component_id: ID of the component

    Returns:
        Component details
    """
    if not DATAFLOW_AVAILABLE:
        return {"error": "haive-dataflow not available"}

    try:
        component = registry_system.get_entity(component_id)
        if not component:
            return {"error": f"Component not found: {component_id}"}

        # Get configurations
        configs = registry_system.get_configurations(component_id)

        # Get dependencies
        deps = registry_system.get_dependencies(component_id)

        # Get environment vars
        env_vars = registry_system.get_environment_vars(component_id)

        return {
            "component": component,
            "configurations": configs,
            "dependencies": deps,
            "environment_vars": env_vars,
        }

    except Exception as e:
        logger.error(f"Error getting component details: {e}")
        return {"error": str(e)}


@mcp.tool()
async def register_component(
    name: str,
    component_type: str,
    description: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Register a new component in haive-dataflow.

    Args:
        name: Component name
        component_type: Type of component (agent, tool, engine, etc.)
        description: Component description
        metadata: Optional metadata dictionary

    Returns:
        Registration result with component ID
    """
    if not DATAFLOW_AVAILABLE:
        return {"error": "haive-dataflow not available"}

    try:
        entity_type = EntityType(component_type)
        component_id = registry_system.register_entity(
            name=name,
            entity_type=entity_type,
            description=description,
            metadata=metadata or {},
        )

        return {
            "status": "success",
            "component_id": component_id,
            "message": f"Successfully registered {name} as {component_type}",
        }

    except ValueError:
        return {"error": f"Invalid component type: {component_type}"}
    except Exception as e:
        logger.error(f"Error registering component: {e}")
        return {"error": str(e)}


@mcp.tool()
async def discover_components(component_type: str) -> dict[str, Any]:
    """Run discovery for a specific component type.

    Args:
        component_type: Type to discover (agents, tools, engines, games)

    Returns:
        Discovery results
    """
    if not DATAFLOW_AVAILABLE:
        return {"error": "haive-dataflow not available"}

    try:
        if component_type == "agents":
            ids = discover_agents()
            return {"discovered": len(ids), "component_ids": ids}
        if component_type == "tools":
            ids = discover_tools()
            return {"discovered": len(ids), "component_ids": ids}
        if component_type == "engines":
            ids = discover_engines()
            return {"discovered": len(ids), "component_ids": ids}
        return {"error": f"Discovery not supported for type: {component_type}"}

    except Exception as e:
        logger.error(f"Error discovering components: {e}")
        return {"error": str(e)}


# Agent Tools
@mcp.tool()
async def create_agent_config(
    agent_type: str, name: str, model: str = "gpt-4", temperature: float = 0.7
) -> dict[str, Any]:
    """Create a configuration for a haive agent.

    Args:
        agent_type: Type of agent (simple, react, rag, multi)
        name: Name for the agent
        model: LLM model to use
        temperature: Temperature setting

    Returns:
        Agent configuration
    """
    configs = {
        "simple": {
            "name": name,
            "engine": {
                "provider": "openai",
                "model": model,
                "temperature": temperature,
            },
            "system_prompt": f"You are {name}, a helpful AI assistant.",
        },
        "react": {
            "name": name,
            "engine": {
                "provider": "openai",
                "model": model,
                "temperature": temperature,
            },
            "tools": [],
            "max_iterations": 10,
        },
        "rag": {
            "name": name,
            "engine": {
                "provider": "openai",
                "model": model,
                "temperature": temperature,
            },
            "retriever": {
                "type": "vector",
                "collection": f"{name}_docs",
            },
        },
        "multi": {
            "name": name,
            "agents": [],
            "coordination": "sequential",
        },
    }

    if agent_type not in configs:
        return {"error": f"Unknown agent type: {agent_type}"}

    return {
        "config": configs[agent_type],
        "instructions": f"Use this configuration to create a {agent_type} agent in haive",
    }


# Prompts
@mcp.prompt()
async def component_search_prompt(query: str) -> str:
    """Generate a prompt for searching haive components.

    Args:
        query: Search query

    Returns:
        Search prompt
    """
    return f"""Help me find haive components that match the following criteria:

Query: {query}

Please search through:
1. Agents - AI agents with various capabilities
2. Tools - Functions and utilities
3. Engines - LLM configurations
4. Games - Interactive game environments
5. MCP Servers - Model Context Protocol servers

For each matching component, provide:
- Name and type
- Description
- Key features
- How to use it

Focus on components most relevant to: {query}"""


@mcp.prompt()
async def agent_creation_prompt(requirements: str) -> str:
    """Generate a prompt for creating a new haive agent.

    Args:
        requirements: Requirements for the agent

    Returns:
        Agent creation prompt
    """
    return f"""Help me create a haive agent with the following requirements:

{requirements}

Please provide:
1. Recommended agent type (simple, react, rag, multi)
2. Suggested configuration
3. Required tools or dependencies
4. Example code to create and use the agent
5. Best practices for this use case

Make sure the solution uses haive's agent framework effectively."""


# Resources
@mcp.resource("haive://registry/components")
async def list_all_components_resource() -> str:
    """Resource listing all registered components."""
    result = await list_components("all")
    return json.dumps(result, indent=2)


@mcp.resource("haive://registry/component/{component_id}")
async def get_component_resource(component_id: str) -> str:
    """Resource for specific component details."""
    result = await get_component_details(component_id)
    return json.dumps(result, indent=2)


# Server info
@mcp.server_info()
async def get_server_info() -> dict[str, Any]:
    """Get server information."""
    return {
        "name": "haive-dataflow-server",
        "version": "1.0.0",
        "description": "MCP server for haive-dataflow registry and component management",
        "author": "Haive Team",
        "capabilities": {
            "tools": [
                "list_components",
                "get_component_details",
                "register_component",
                "discover_components",
                "create_agent_config",
            ],
            "resources": [
                "haive://registry/components",
                "haive://registry/component/{id}",
            ],
            "prompts": ["component_search_prompt", "agent_creation_prompt"],
        },
        "dataflow_available": DATAFLOW_AVAILABLE,
    }


if __name__ == "__main__":
    logger.info("Starting haive-dataflow MCP server...")
    logger.info(f"Dataflow available: {DATAFLOW_AVAILABLE}")

    # Run the server
    asyncio.run(mcp.run())
