# Tutorial 1: Understanding MCP with Haive's Dynamic Discovery

## What is MCP?

The Model Context Protocol (MCP) is a standardized protocol that allows AI models to interact with external tools, resources, and data sources. With **Haive MCP**, agents can **automatically discover and integrate** tools from **1900+ MCP servers** at runtime, without any manual configuration.

## Core Concepts

### 1. **MCP Servers**

MCP servers are standalone programs that expose functionality to AI models. They can:

- Provide tools (functions the AI can call)
- Offer resources (data the AI can access)
- Supply prompts (templates for optimal usage)

### 2. **Transport Layers**

MCP supports multiple transport mechanisms:

- **stdio**: Communication via standard input/output
- **HTTP/SSE**: Web-based communication
- **WebSocket**: Real-time bidirectional communication

### 3. **Capabilities**

Each MCP server declares its capabilities:

- **Tools**: Executable functions
- **Resources**: Accessible data
- **Prompts**: Predefined templates

## How MCP Works

```
┌─────────────┐     MCP Protocol      ┌─────────────┐
│   AI Agent  │◄─────────────────────►│ MCP Server  │
│   (Client)  │                       │  (Provider) │
└─────────────┘                       └─────────────┘
      │                                      │
      │ 1. List available tools              │
      │─────────────────────────────────────►│
      │                                      │
      │ 2. Return tool definitions           │
      │◄─────────────────────────────────────│
      │                                      │
      │ 3. Call tool with parameters         │
      │─────────────────────────────────────►│
      │                                      │
      │ 4. Return tool results               │
      │◄─────────────────────────────────────│
```

## Key Benefits

1. **Standardization**: One protocol for all integrations
2. **Security**: Controlled access to resources
3. **Flexibility**: Support for various transport methods
4. **Extensibility**: Easy to add new capabilities

## Example: Filesystem Server

The filesystem MCP server provides tools for file operations:

```json
{
  "name": "@modelcontextprotocol/server-filesystem",
  "tools": [
    {
      "name": "read_file",
      "description": "Read contents of a file",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": { "type": "string" }
        }
      }
    },
    {
      "name": "write_file",
      "description": "Write contents to a file",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": { "type": "string" },
          "content": { "type": "string" }
        }
      }
    }
  ]
}
```

## MCP vs Traditional APIs

| Feature            | MCP            | Traditional API       |
| ------------------ | -------------- | --------------------- |
| **Protocol**       | Standardized   | Varies per API        |
| **Discovery**      | Built-in       | Manual documentation  |
| **Type Safety**    | JSON Schema    | Varies                |
| **Tool Chaining**  | Native support | Custom implementation |
| **Error Handling** | Standardized   | API-specific          |

## Getting Started with Haive MCP

With Haive MCP, the process is dramatically simplified through **automatic discovery**:

1. **Create Agent**: Use `EnhancedMCPAgent` with desired capabilities
2. **Auto-Discovery**: Agent automatically finds and installs needed servers
3. **Dynamic Integration**: Tools are available instantly in your agent
4. **Just Use**: No manual configuration - tools work immediately

```python
import asyncio
from haive.mcp.agents.enhanced_mcp_agent import EnhancedMCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

async def quick_start():
    # Create agent that auto-discovers tools from 1900+ servers
    agent = EnhancedMCPAgent(
        name="discovery_agent",
        engine=AugLLMConfig(temperature=0.7),
        mcp_categories=["core"],  # Auto-install filesystem, database, search tools
        auto_install=True
    )
    
    # Initialize - agent discovers and installs tools automatically
    await agent.initialize_mcp()
    
    # Use immediately - tools are ready!
    result = await agent.arun("List files and search for Python projects")
    return result

# Run the agent
asyncio.run(quick_start())
```

## Common Use Cases

- **File Operations**: Read/write files, manage directories
- **Database Access**: Query and modify databases
- **API Integration**: Connect to external services
- **Data Processing**: Transform and analyze data
- **System Control**: Execute commands, manage processes

## Best Practices

1. **Start Simple**: Begin with basic servers like filesystem
2. **Understand Transport**: Choose appropriate transport method
3. **Handle Errors**: Implement proper error handling
4. **Security First**: Never expose sensitive credentials
5. **Monitor Usage**: Track tool calls and performance

## Next Steps

- Continue to Tutorial 2: Setting Up Your First MCP Server
- Explore available MCP servers in the registry
- Read the MCP specification for deeper understanding

## Resources

- [MCP Specification](https://modelcontextprotocol.io/spec)
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Community Servers](https://github.com/topics/mcp-server)
