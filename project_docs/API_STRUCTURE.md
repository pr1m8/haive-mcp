# Haive-MCP API Structure

**Updated**: January 2025  
**Status**: Source code reorganized for clarity

## 📦 Package Structure

```
haive.mcp/
├── Core Components (Root Level)
│   ├── manager.py          # MCPManager - Central server lifecycle management
│   ├── config.py           # Configuration classes (MCPConfig, MCPServerConfig)
│   └── cli.py              # Command-line interface
│
├── agents/                 # Agent implementations
│   ├── mcp_agent.py        # Production agent with static MCP config
│   ├── intelligent_mcp_agent.py  # AI-powered agent with auto-discovery
│   ├── transferable_mcp_agent.py # Agent with tool sharing capabilities
│   └── documentation_agent.py    # Documentation-focused agent
│
├── discovery/              # Server discovery components
│   ├── server_discovery.py # AI-powered server discovery
│   └── discovery_models.py # Discovery data models
│
├── documentation/          # Documentation loading
│   ├── loader.py           # MCPDocumentationLoader
│   └── processor.py        # Documentation processing
│
├── mixins/                 # Mixins for existing agents
│   ├── mcp_mixin.py        # Basic MCP capabilities
│   └── discovery_mixin.py  # Discovery capabilities
│
├── servers/                # Server implementations
│   └── (MCP server wrappers)
│
├── tools/                  # Tool implementations
│   └── (Tool wrappers and utilities)
│
├── utils/                  # Utility functions
│   ├── validation.py       # Configuration validation
│   └── helpers.py          # Helper functions
│
├── retrieval/              # RAG and retrieval components
│   ├── simple_faiss_retriever.py
│   └── enhanced_parent_self_query_retriever.py
│
├── integration/            # Integration components
│   ├── haive_agent_mcp_integration.py
│   └── fastapi_mcp_server.py
│
├── examples/               # Example implementations
│   ├── simple_rag_mcp_agent.py
│   └── mcp_simple_tool_agent.py
│
└── archive/                # Experimental/deprecated code
```

## 🎯 Core APIs

### 1. MCPManager

Central manager for MCP server lifecycle and tool management.

```python
from haive.mcp import MCPManager, MCPServerConfig

# Create manager
manager = MCPManager()

# Add servers dynamically
await manager.add_server("filesystem", MCPServerConfig(
    name="filesystem",
    transport="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem"]
))

# Get all available tools
tools = await manager.get_all_tools()

# Health monitoring
health = await manager.check_health("filesystem")
```

### 2. MCPAgent

Production-ready agent with static MCP configuration.

```python
from haive.mcp import MCPAgent, MCPConfig
from haive.core.engine import AugLLMConfig

agent = MCPAgent(
    engine=AugLLMConfig(),
    mcp_config=MCPConfig(
        enabled=True,
        servers={
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"]
            }
        }
    )
)

await agent.setup()
result = await agent.arun({"messages": [...]})
```

### 3. IntelligentMCPAgent

AI-powered agent with automatic server discovery.

```python
from haive.mcp import IntelligentMCPAgent

agent = IntelligentMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True,      # Enable AI discovery
    require_approval=True    # HITL approval
)

# Agent automatically discovers and installs needed servers
result = await agent.arun({
    "messages": [{"role": "user", "content": "Search web and save to database"}]
})
```

### 4. TransferableMCPAgent

Agent that can share tools with other agents.

```python
from haive.mcp import TransferableMCPAgent

# Create agents
agent1 = TransferableMCPAgent(engine=config1)
agent2 = TransferableMCPAgent(engine=config2)

# Transfer tools
await agent1.transfer_tools_to(agent2, tool_names=["filesystem", "github"])
```

## 🔧 Configuration

### MCPConfig

Main configuration for MCP functionality.

```python
from haive.mcp import MCPConfig, MCPServerConfig

config = MCPConfig(
    enabled=True,
    auto_discover=False,
    require_approval=True,
    servers={
        "filesystem": MCPServerConfig(
            name="filesystem",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            env={"HOME": "/home/user"}
        )
    }
)
```

### MCPServerConfig

Configuration for individual MCP servers.

```python
server_config = MCPServerConfig(
    name="github",
    transport="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"],
    env={"GITHUB_TOKEN": "your_token"},
    working_dir="/tmp",
    startup_timeout=30.0
)
```

## 🎨 Mixins

Add MCP capabilities to existing agents.

### MCPMixin

```python
from haive.agents import SimpleAgent
from haive.mcp.mixins import MCPMixin

class MyCustomAgent(MCPMixin, SimpleAgent):
    """Custom agent with MCP capabilities."""
    pass
```

### MCPDiscoveryMixin

```python
from haive.mcp.mixins import MCPDiscoveryMixin

class MyDiscoveryAgent(MCPDiscoveryMixin, SimpleAgent):
    """Agent with automatic MCP discovery."""
    pass
```

## 🔍 Discovery

### MCPServerDiscovery

AI-powered server discovery system.

```python
from haive.mcp.discovery import MCPServerDiscovery

discovery = MCPServerDiscovery()

# Find servers for a capability
servers = await discovery.find_servers_for_capability(
    "file system operations"
)

# Get server details
details = await discovery.get_server_details("filesystem")
```

## 📚 Documentation Loader

### MCPDocumentationLoader

Access to MCP server documentation database.

```python
from haive.mcp.documentation import MCPDocumentationLoader

loader = MCPDocumentationLoader()

# Load all server documentation
docs = loader.load_all_servers()

# Search for servers
results = loader.search_servers("database operations")

# Get specific server info
info = loader.get_server_info("postgresql")
```

## 🚀 Quick Start Examples

### Basic File Operations

```python
from haive.mcp import MCPAgent
from haive.core.engine import AugLLMConfig

# Create filesystem agent
agent = MCPAgent.create_with_mcp_servers(
    engine=AugLLMConfig(),
    server_configs={
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"]
        }
    }
)

await agent.setup()

# Use for file operations
result = await agent.arun({
    "messages": [{"role": "user", "content": "List files in current directory"}]
})
```

### Dynamic Multi-Tool Agent

```python
from haive.mcp import IntelligentMCPAgent

# Create agent with auto-discovery
agent = IntelligentMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True
)

# Agent discovers and installs needed tools automatically
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Search GitHub for Python MCP examples and save interesting ones to a local file"
    }]
})
# Agent will discover and install both GitHub and filesystem servers
```

## 🔗 Integration Patterns

### With Existing Haive Agents

```python
# Add MCP to existing agent using mixin
from haive.agents import ReactAgent
from haive.mcp.mixins import MCPMixin

class MCPReactAgent(MCPMixin, ReactAgent):
    """ReactAgent with MCP capabilities."""
    pass

# Use like normal ReactAgent but with MCP
agent = MCPReactAgent(
    engine=config,
    mcp_config=mcp_config
)
```

### Multi-Agent Systems

```python
from haive.mcp import TransferableMCPAgent
from haive.agents.multi import MultiAgent

# Create specialized MCP agents
web_agent = TransferableMCPAgent(name="web_specialist")
db_agent = TransferableMCPAgent(name="db_specialist")

# Combine in multi-agent system
multi_agent = MultiAgent(
    agents=[web_agent, db_agent],
    mode="collaborative"
)
```

## 📖 Further Reading

- [Architecture Overview](architecture/README.md)
- [Integration Guide](integration/README.md)
- [Usage Patterns](guides/usage-patterns.md)
- [Examples](examples/README.md)
