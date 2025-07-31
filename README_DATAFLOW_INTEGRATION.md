# Haive MCP Dataflow Integration

This document describes the integration between Haive's MCP (Model Context Protocol) system and the Dataflow registry/discovery system.

## Overview

The integration provides:
- **MCP Server** exposing Haive's dataflow capabilities as MCP tools and resources
- **AugLLMConfig Extension** adding MCP support to Haive's core engine
- **Dynamic Tool Discovery** from the dataflow registry
- **Component Management** via MCP tools

## Components

### 1. Dataflow MCP Server (`dataflow_mcp_server.py`)

A FastMCP server that exposes Haive's dataflow system through MCP:

#### Tools
- `query_registry`: Search for components in the Haive registry
- `discover_components`: Discover agents and tools in the system
- `create_agent`: Create new Haive agents with configuration
- `execute_tool`: Execute registered Haive tools

#### Resources
- `registry://entities`: Complete registry state grouped by type
- `registry://statistics`: Statistics about registered components

#### Prompts
- `component_search_prompt`: Help find suitable components
- `agent_configuration_prompt`: Guide agent configuration

### 2. AugLLMConfig MCP Extension (`aug_llm_mcp_extension.py`)

Extends AugLLMConfig with MCP capabilities:

```python
class MCPAugLLMConfig(AugLLMConfig):
    mcp_config: Optional[MCPConfig]
    mcp_resources: Optional[List[MCPResource]]
    mcp_prompts: Optional[Dict[str, MCPPromptTemplate]]
```

Features:
- Automatic MCP tool discovery and wrapping
- Resource injection into agent context
- Prompt template integration
- Enhanced system prompts with MCP information

### 3. Integration Pattern

```python
# Create MCP-enabled agent configuration
config = await create_mcp_enabled_aug_config(
    name="research_agent",
    model="gpt-4o-mini",
    mcp_servers={
        "dataflow": MCPServerConfig(
            transport="stdio",
            command="python",
            args=["dataflow_mcp_server.py"]
        )
    }
)

# MCP tools are automatically discovered and added
# Resources and prompts enhance the agent's capabilities
```

## Usage Examples

### Starting the MCP Server

```bash
# Run the dataflow MCP server
python dataflow_mcp_server.py

# Or use it with an MCP client
npx @modelcontextprotocol/inspector python dataflow_mcp_server.py
```

### Using from an Agent

```python
from haive.mcp.integration.aug_llm_mcp_extension import create_mcp_enabled_aug_config
from haive.agents import ReactAgent

# Create MCP-enabled configuration
config = await create_mcp_enabled_aug_config(
    name="mcp_agent",
    mcp_servers={
        "dataflow": MCPServerConfig(...)
    }
)

# Create agent with MCP tools
agent = ReactAgent(engine=config)
await agent.setup()

# Agent now has access to:
# - dataflow_query_registry tool
# - dataflow_discover_components tool  
# - dataflow_create_agent tool
# - Registry resources
# - Configuration prompts
```

### Direct MCP Client Usage

```python
from mcp.client import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to server
server_params = StdioServerParameters(
    command="python",
    args=["dataflow_mcp_server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Query registry
        agents = await session.call_tool(
            "query_registry",
            arguments={"entity_type": "agent"}
        )
        
        # Create agent
        result = await session.call_tool(
            "create_agent",
            arguments={
                "request": {
                    "name": "assistant",
                    "model": "gpt-4o-mini",
                    "tools": ["calculator"]
                }
            }
        )
```

## Architecture Benefits

1. **Separation of Concerns**: MCP server handles protocol, dataflow handles registry
2. **Dynamic Discovery**: Tools and agents discovered at runtime
3. **Extensibility**: Easy to add new MCP tools for dataflow operations
4. **Integration**: Seamless use of MCP tools in Haive agents
5. **Standards-Based**: Uses MCP protocol for interoperability

## Future Enhancements

1. **Real Dataflow Graphs**: Execute actual dataflow graphs as MCP tools
2. **State Management**: Persist agent state through MCP resources
3. **Event Streaming**: Use SSE transport for real-time updates
4. **Tool Composition**: Create composite tools from registry components
5. **Performance Monitoring**: Expose metrics as MCP resources

## Running the Example

```bash
# Install dependencies
cd packages/haive-mcp
poetry install

# Run the example
poetry run python examples/dataflow_mcp_example.py
```

This will demonstrate:
- Connecting to the dataflow MCP server
- Querying the registry
- Discovering components
- Creating agents
- Accessing resources
- Using prompts

## Integration Points

The integration connects several Haive systems:

1. **haive-core**: AugLLMConfig for agent configuration
2. **haive-dataflow**: Registry and discovery systems
3. **haive-mcp**: MCP protocol implementation
4. **haive-agents**: Agent implementations using MCP tools

This creates a unified system where MCP servers can expose any Haive functionality, and agents can seamlessly use MCP tools alongside native tools.