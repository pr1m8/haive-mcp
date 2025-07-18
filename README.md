# haive-mcp

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency-poetry-blue.svg)](https://python-poetry.org/)
[![MCP 1.0](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io/)

Dynamic Model Context Protocol (MCP) integration for Haive agents with hot-reload capabilities, intelligent discovery, and human-in-the-loop approval workflows.

## What is haive-mcp?

haive-mcp brings the power of [Model Context Protocol](https://modelcontextprotocol.io/) to Haive agents, enabling them to dynamically discover, install, and use external tools and resources. With access to a database of 1,960+ MCP servers, your agents can automatically find and install the right tools for any task - all without restarting.

### Key Capabilities

- 🔄 **Hot-Reload** - Add servers and refresh tools without restart
- 🤖 **Intelligent Discovery** - AI analyzes needs and suggests servers
- 👤 **HITL Approval** - Human approval for server installations
- 📚 **1,960+ Servers** - Pre-indexed database of MCP servers
- 🔧 **Dynamic Tools** - Tools, resources, and prompts from MCP servers
- ⚡ **Real-time Updates** - Install and use immediately

## Quick Start

### Installation

```bash
# Install with poetry (recommended)
poetry add haive-mcp

# Or install from source
cd packages/haive-mcp
poetry install
```

### Basic Usage - Dynamic Discovery

```python
from haive.mcp.agents import IntelligentMCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

# Create an intelligent agent that auto-discovers MCP servers
agent = IntelligentMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True,      # Automatically find needed servers
    require_approval=True    # Ask before installing
)

await agent.setup()

# Agent automatically installs servers based on your needs!
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Search the web for Python async tutorials and save to a file"
    }]
})
# Agent detects need for:
# - Web search → installs brave-search server
# - File operations → installs filesystem server
# Then completes your task!
```

## Core Concepts

### 1. Dynamic Server Management

The `MCPManager` handles all server lifecycle operations with hot-reload support:

```python
from haive.mcp.manager import MCPManager
from haive.mcp.config import MCPServerConfig

manager = MCPManager()

# Add servers dynamically
await manager.add_server("filesystem", MCPServerConfig(
    name="filesystem",
    transport="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem"]
))

# Get all tools (with refresh)
tools = await manager.get_all_tools(refresh=True)

# Get resources and prompts
resources = await manager.get_resources()
prompts = await manager.get_prompts()

# Hot-reload a specific server
await manager.reload_server("filesystem")
```

### 2. Intelligent Discovery

The `IntelligentMCPAgent` uses AI to analyze user requests and automatically find appropriate MCP servers:

```python
# Agent with built-in discovery tools
agent = IntelligentMCPAgent(engine=engine)

# Use discovery tools directly
await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Use discover_mcp_servers to find database servers"
    }]
})

# Or let the agent auto-discover
agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True  # AI analyzes needs automatically
)
```

### 3. HITL Approval Workflows

Control server installations with human-in-the-loop approval:

```python
# Custom approval callback
async def my_approval_handler(request: HITLApprovalRequest) -> bool:
    print(f"🔔 Install {request.recommendation.server_name}?")
    print(f"Reason: {request.recommendation.reason}")
    print(f"Capabilities: {', '.join(request.recommendation.capabilities)}")
    
    # Your approval logic here
    user_input = input("Approve? (y/n): ")
    return user_input.lower() == 'y'

agent = IntelligentMCPAgent(
    engine=engine,
    require_approval=True,
    approval_callback=my_approval_handler
)
```

## Available Components

### Agents

#### IntelligentMCPAgent
The flagship agent with dynamic discovery and management:
- Auto-discovers needed MCP servers from 992+ database
- HITL approval workflows
- Built-in discovery and management tools
- Hot-reload support

#### MCPAgent
Production agent for static MCP configurations:
- Connect to multiple MCP servers
- Access all tools, resources, and prompts
- Integrates with Haive agent framework

#### TransferableMCPAgent
Agent that can share tools with other agents:
- Transfer specific tools between agents
- Share entire tool sets
- Collaborative multi-agent workflows

### Built-in Tools

The IntelligentMCPAgent includes these tools:

- **discover_mcp_servers(capability)** - Find servers by capability
- **install_mcp_server(server_name)** - Install with optional approval  
- **list_mcp_status()** - Get current server and tool status
- **reload_mcp_server(server_name)** - Hot-reload specific server

## Common Workflows

### 1. Auto-Discovery Workflow

```python
# Let the agent figure out what it needs
agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True,
    require_approval=True
)

# Agent analyzes request and installs needed servers
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Connect to PostgreSQL and analyze user data"
    }]
})
# Automatically installs postgres MCP server!
```

### 2. Manual Discovery Workflow

```python
# Control discovery manually
agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=False  # Manual control
)

# Discover database servers
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Use discover_mcp_servers to find database servers"
    }]
})

# Install specific server
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Install modelcontextprotocol/server-postgres"
    }]
})
```

### 3. Static Configuration Workflow

```python
# Traditional approach with known servers
from haive.mcp.config import MCPConfig, MCPServerConfig

config = MCPConfig(
    servers={
        "github": MCPServerConfig(
            name="github",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": token}
        )
    }
)

agent = MCPAgent(engine=engine, mcp_config=config)
```

### 4. Tool Transfer Workflow

```python
# Share tools between agents
agent1 = TransferableMCPAgent(engine=engine, mcp_config=config1)
agent2 = TransferableMCPAgent(engine=engine, mcp_config=config2)

await agent1.setup()
await agent2.setup()

# Transfer specific tools
await agent1.transfer_tools_to_agent(
    agent2, 
    tool_names=["file_read", "file_write"]
)
```

## Server Database

haive-mcp includes a pre-processed database of 1,960+ MCP servers from GitHub:

- Categorized by capability (database, filesystem, search, etc.)
- Extracted setup instructions and configurations
- Quality scores and popularity metrics
- Ready-to-use configurations

Access the database directly:

```python
from haive.mcp.documentation import MCPDocumentationLoader

loader = MCPDocumentationLoader()
all_servers = loader.load_all_mcp_documents()
print(f"Found {len(all_servers)} MCP servers")  # 1,960+ servers available

# Find specific server
postgres_doc = loader.get_server_documentation(
    "modelcontextprotocol/server-postgres"
)
```

## Configuration

### Environment Variables

```bash
# Optional: Set default MCP settings
export MCP_AUTO_DISCOVER=true
export MCP_REQUIRE_APPROVAL=false
export MCP_HEALTH_CHECK_INTERVAL=30
```

### Configuration Options

```python
# MCPManager options
manager = MCPManager(
    auto_health_check=True,      # Monitor server health
    health_check_interval=30.0,  # Check every 30 seconds
    max_retry_attempts=3,        # Retry failed connections
    connection_timeout=10.0      # Connection timeout
)

# IntelligentMCPAgent options
agent = IntelligentMCPAgent(
    auto_discover=True,          # Auto-discover servers
    require_approval=True,       # Require HITL approval
    approval_timeout=30.0,       # Approval timeout
    approval_callback=handler    # Custom approval handler
)
```

## Examples

Complete examples are provided in the `examples/` directory:

```bash
# Basic dynamic discovery
poetry run python examples/dynamic_mcp_workflow.py

# Static MCP configuration
poetry run python examples/mcp_agent_example.py

# Documentation processing
poetry run python examples/mcp_documentation_example.py
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run integration tests
poetry run pytest tests/test_hot_reload_integration.py -v

# Run with coverage
poetry run pytest --cov=haive.mcp
```

## Architecture

```
haive-mcp/
├── agents/                    # Agent implementations
│   ├── intelligent_mcp_agent  # Dynamic discovery agent
│   ├── mcp_agent             # Standard MCP agent
│   └── transferable_mcp      # Tool sharing agent
├── manager.py                # Dynamic server management
├── config.py                 # Configuration models
├── documentation/            # 992+ server database
└── mixins/                   # MCP capabilities mixin
```

## Advanced Usage

### Custom Server Discovery

```python
# Create custom discovery logic
class MyDiscoveryAgent(IntelligentMCPAgent):
    async def _analyze_capability_needs(self, user_message: str) -> list[str]:
        # Custom capability analysis
        if "spreadsheet" in user_message.lower():
            return ["excel", "sheets"]
        return await super()._analyze_capability_needs(user_message)
```

### Server Health Monitoring

```python
# Get health status
status = manager.get_all_server_status()
print(f"Connected: {status['summary']['connected_servers']}")
print(f"Failed: {status['summary']['failed_servers']}")

# Check specific server
health = await manager.check_server_health("postgres")
print(f"Response time: {health.response_time}s")
```

### Concurrent Operations

```python
# Add multiple servers concurrently
import asyncio

configs = [postgres_config, github_config, filesystem_config]
tasks = [
    manager.add_server(f"server{i}", cfg) 
    for i, cfg in enumerate(configs)
]
results = await asyncio.gather(*tasks)
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure MCP dependencies are installed
   poetry install --all-extras
   ```

2. **Server Connection Failed**
   ```python
   # Check server requirements
   result = await manager.add_server("test", config)
   if not result.success:
       print(f"Error: {result.error_message}")
   ```

3. **Tools Not Refreshing**
   ```python
   # Force refresh
   tools = await manager.get_all_tools(refresh=True)
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("haive.mcp").setLevel(logging.DEBUG)

# Check manager state
print(manager.get_all_server_status())
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Haive Framework](https://github.com/algebraic-ai/haive)

## Support

For issues and questions:
- GitHub Issues: [haive/issues](https://github.com/algebraic-ai/haive/issues)
- Documentation: [haive.readthedocs.io](https://haive.readthedocs.io)