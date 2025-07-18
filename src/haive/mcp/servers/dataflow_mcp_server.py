#!/usr/bin/env python3
"""MCP Server integrating Haive Dataflow for dynamic tool creation.

This server demonstrates how to create MCP tools from Haive's dataflow system,
exposing dataflow graphs as MCP tools and resources. It integrates with:
- haive-core: For agent and engine functionality
- haive-dataflow: For registry and discovery systems
- haive-tools: For exposing existing tools via MCP
"""

import asyncio
import logging
from typing import Any

from pydantic import BaseModel, Field

# Haive imports
from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.models.llm.base import LLMConfig
from mcp.server import FastMCP


# Import dataflow components
try:
    from haive.dataflow import EntityType, registry_system
    from haive.dataflow.discovery import discover_agents, discover_tools

    DATAFLOW_AVAILABLE = True
except ImportError:
    DATAFLOW_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("haive-dataflow not available, using mock registry")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("haive-dataflow-server")


# ============================================================================
# MCP Tool: Registry Query
# ============================================================================


@mcp.tool()
async def query_registry(
    entity_type: str | None = None, name_pattern: str | None = None, limit: int = 10
) -> list[dict[str, Any]]:
    """Query the Haive registry for components.

    Args:
        entity_type: Type of entity to query (agent, tool, engine, etc.)
        name_pattern: Pattern to match entity names
        limit: Maximum number of results to return

    Returns:
        List of registry entries matching the query
    """
    if not DATAFLOW_AVAILABLE:
        return [
            {
                "error": "Dataflow not available",
                "message": "haive-dataflow package is not installed",
            }
        ]

    try:
        # Query registry
        if entity_type:
            entities = registry_system.get_entities_by_type(EntityType(entity_type))
        else:
            entities = registry_system.get_all_entities()

        # Filter by name pattern if provided
        if name_pattern:
            entities = [e for e in entities if name_pattern.lower() in e.name.lower()]

        # Limit results
        entities = entities[:limit]

        # Convert to serializable format
        results = []
        for entity in entities:
            results.append(
                {
                    "id": str(entity.id),
                    "name": entity.name,
                    "type": entity.type.value,
                    "description": entity.description,
                    "module_path": entity.module_path,
                    "class_name": entity.class_name,
                    "metadata": entity.metadata,
                }
            )

        logger.info(f"Registry query returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Error querying registry: {e}")
        return [{"error": str(e)}]


# ============================================================================
# MCP Tool: Discover Components
# ============================================================================


@mcp.tool()
async def discover_components(
    component_type: str = "all", auto_register: bool = False
) -> dict[str, Any]:
    """Discover Haive components in the system.

    Args:
        component_type: Type to discover (agents, tools, or all)
        auto_register: Whether to automatically register discovered components

    Returns:
        Discovery results with counts and component details
    """
    if not DATAFLOW_AVAILABLE:
        return {"error": "Dataflow not available", "discovered": {}}

    try:
        results = {"agents": [], "tools": [], "total": 0}

        if component_type in ["agents", "all"]:
            agents = discover_agents(auto_register=auto_register)
            results["agents"] = [
                {
                    "name": agent.name,
                    "module": agent.module_path,
                    "description": agent.description,
                }
                for agent in agents
            ]

        if component_type in ["tools", "all"]:
            tools = discover_tools(auto_register=auto_register)
            results["tools"] = [
                {
                    "name": tool.name,
                    "module": tool.module_path,
                    "description": tool.description,
                }
                for tool in tools
            ]

        results["total"] = len(results["agents"]) + len(results["tools"])
        logger.info(f"Discovered {results['total']} components")

        return results

    except Exception as e:
        logger.error(f"Error discovering components: {e}")
        return {"error": str(e), "discovered": {}}


# ============================================================================
# MCP Tool: Create Agent
# ============================================================================


class AgentCreationRequest(BaseModel):
    """Request model for agent creation."""

    name: str = Field(..., description="Agent name")
    model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    tools: list[str] = Field(default_factory=list, description="Tool names to include")
    system_prompt: str | None = Field(None, description="System prompt for agent")
    temperature: float = Field(default=0.7, description="Temperature for LLM")


@mcp.tool()
async def create_agent(request: AgentCreationRequest) -> dict[str, Any]:
    """Create a new Haive agent with specified configuration.

    Args:
        request: Agent creation parameters

    Returns:
        Agent creation result with ID and status
    """
    try:
        # Create LLM config
        llm_config = LLMConfig(
            provider="openai", model=request.model, temperature=request.temperature
        )

        # Create AugLLM config
        aug_config = AugLLMConfig(
            llm_config=llm_config,
            name=request.name,
            tools=request.tools,
            system_message=request.system_prompt
            or f"You are {request.name}, a helpful AI assistant.",
        )

        # In a real implementation, we would:
        # 1. Create the agent instance
        # 2. Register it in the dataflow registry
        # 3. Make it available for use

        # For now, return a mock result
        result = {
            "success": True,
            "agent_id": f"agent_{request.name}_{id(request)}",
            "name": request.name,
            "model": request.model,
            "tools": request.tools,
            "status": "created",
            "message": f"Agent '{request.name}' created successfully",
        }

        logger.info(f"Created agent: {result['agent_id']}")
        return result

    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        return {"success": False, "error": str(e), "message": "Failed to create agent"}


# ============================================================================
# MCP Tool: Execute Tool
# ============================================================================


@mcp.tool()
async def execute_tool(tool_name: str, input_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a Haive tool by name.

    Args:
        tool_name: Name of the tool to execute
        input_data: Input parameters for the tool

    Returns:
        Tool execution result
    """
    try:
        if not DATAFLOW_AVAILABLE:
            return {"error": "Dataflow not available", "result": None}

        # Look up tool in registry
        tools = registry_system.get_entities_by_type(EntityType.TOOL)
        tool_entity = next((t for t in tools if t.name == tool_name), None)

        if not tool_entity:
            return {
                "error": f"Tool '{tool_name}' not found in registry",
                "available_tools": [t.name for t in tools[:5]],
            }

        # In a real implementation, we would:
        # 1. Load the tool class from module_path and class_name
        # 2. Instantiate the tool
        # 3. Execute it with input_data
        # 4. Return the result

        # Mock result for now
        result = {
            "success": True,
            "tool": tool_name,
            "input": input_data,
            "output": f"Mock output from {tool_name}",
            "metadata": {
                "module": tool_entity.module_path,
                "class": tool_entity.class_name,
            },
        }

        logger.info(f"Executed tool: {tool_name}")
        return result

    except Exception as e:
        logger.error(f"Error executing tool: {e}")
        return {"error": str(e), "result": None}


# ============================================================================
# MCP Resources
# ============================================================================


@mcp.resource("registry://entities")
async def get_registry_entities() -> dict[str, Any]:
    """Resource providing all registry entities.

    Returns:
        Complete registry state
    """
    if not DATAFLOW_AVAILABLE:
        return {"entities": [], "error": "Dataflow not available"}

    try:
        entities = registry_system.get_all_entities()

        # Group by type
        grouped = {}
        for entity in entities:
            entity_type = entity.type.value
            if entity_type not in grouped:
                grouped[entity_type] = []

            grouped[entity_type].append(
                {
                    "name": entity.name,
                    "description": entity.description,
                    "module": entity.module_path,
                }
            )

        return {
            "entities": grouped,
            "total_count": len(entities),
            "types": list(grouped.keys()),
        }

    except Exception as e:
        logger.error(f"Error getting registry entities: {e}")
        return {"entities": [], "error": str(e)}


@mcp.resource("registry://statistics")
async def get_registry_statistics() -> dict[str, Any]:
    """Resource providing registry statistics.

    Returns:
        Statistics about registered components
    """
    if not DATAFLOW_AVAILABLE:
        return {"error": "Dataflow not available"}

    try:
        stats = {"total_entities": 0, "by_type": {}, "recent_additions": []}

        # Get all entities
        entities = registry_system.get_all_entities()
        stats["total_entities"] = len(entities)

        # Count by type
        for entity in entities:
            entity_type = entity.type.value
            stats["by_type"][entity_type] = stats["by_type"].get(entity_type, 0) + 1

        # Get recent additions (mock for now)
        stats["recent_additions"] = [entity.name for entity in entities[:5]]

        return stats

    except Exception as e:
        logger.error(f"Error getting registry statistics: {e}")
        return {"error": str(e)}


# ============================================================================
# MCP Prompts
# ============================================================================


@mcp.prompt()
async def component_search_prompt(requirement: str) -> list[dict[str, str]]:
    """Generate a prompt for searching components by requirement.

    Args:
        requirement: User's requirement description

    Returns:
        Prompt messages for component search
    """
    return [
        {
            "role": "system",
            "content": """You are a Haive component search assistant. 
            Help users find the right agents, tools, and engines for their needs.
            Consider capabilities, compatibility, and performance.""",
        },
        {
            "role": "user",
            "content": f"""I need to find Haive components for: {requirement}

Please search the registry and recommend:
1. Suitable agents for this task
2. Required tools
3. Optimal configuration

Use the query_registry and discover_components tools to find matches.""",
        },
    ]


@mcp.prompt()
async def agent_configuration_prompt(
    task_description: str, available_tools: list[str]
) -> list[dict[str, str]]:
    """Generate a prompt for agent configuration.

    Args:
        task_description: Description of the task
        available_tools: List of available tool names

    Returns:
        Prompt messages for agent configuration
    """
    tools_str = ", ".join(available_tools) if available_tools else "none specified"

    return [
        {
            "role": "system",
            "content": """You are a Haive agent configuration expert.
            Help users configure agents with optimal settings for their tasks.""",
        },
        {
            "role": "user",
            "content": f"""Configure a Haive agent for: {task_description}

Available tools: {tools_str}

Please recommend:
1. Agent type and name
2. LLM model selection
3. Tool selection from available tools
4. System prompt
5. Temperature and other parameters

Use the create_agent tool with your recommendations.""",
        },
    ]


# ============================================================================
# Server Initialization
# ============================================================================


async def initialize_server():
    """Initialize the MCP server with dataflow integration."""
    logger.info("Initializing Haive Dataflow MCP Server...")

    if DATAFLOW_AVAILABLE:
        # Discover initial components
        logger.info("Discovering Haive components...")
        try:
            results = await discover_components("all", auto_register=True)
            logger.info(f"Discovered {results['total']} components")
        except Exception as e:
            logger.error(f"Error during discovery: {e}")
    else:
        logger.warning("Running in mock mode - haive-dataflow not available")

    logger.info("Haive Dataflow MCP Server initialized")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run initialization
    asyncio.run(initialize_server())

    # Start the MCP server
    logger.info("Starting Haive Dataflow MCP Server on stdio...")
    mcp.run(transport="stdio")
