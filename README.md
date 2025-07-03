# haive-mcp

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency-poetry-blue.svg)](https://python-poetry.org/)
[![MCP 1.0](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io/)

Comprehensive Model Context Protocol (MCP) integration for Haive agents. This package combines **documentation processing of 992 MCP servers**, **intelligent discovery**, and **production-ready agents** to make MCP servers easily accessible.

## How It Works

The haive-mcp package provides a complete pipeline from **documentation to production**:

### 1. **Documentation Database (992 MCP Servers)**
We maintain a comprehensive database of 992 MCP servers scraped from GitHub, including:
- Setup instructions extracted from README files
- Tool and resource descriptions
- Installation commands and configuration
- Capability classifications (database, filesystem, etc.)

### 2. **Intelligent Documentation Processing**
The `MCPDocumentationAgent` uses LLM analysis to:
- Find servers by capability: `find_servers_by_capability("database")`
- Generate complete setup guides: `generate_implementation_guide()`
- Convert documentation into working configurations automatically

### 3. **Production-Ready Agents**
The `MCPAgent` uses discovered configurations to provide agents with:
- **Tools**: Functions the model can call (database queries, file operations, etc.)
- **Resources**: Data sources the application controls
- **Prompts**: User-defined templates for optimal tool usage

## Key Features

- 📚 **992 MCP Server Database**: Pre-processed documentation from GitHub
- 🤖 **Intelligent Discovery**: LLM-powered capability analysis and server matching
- 🔧 **Auto-Configuration**: Convert documentation to working configs automatically  
- 🔄 **Tool Transfer**: Share tools between agents dynamically
- 🤝 **Production Agents**: Ready-to-use agents with MCP capabilities
- ⚡ **Mass Installation**: Install all documented servers automatically
- 🛡️ **Type-Safe**: Full Pydantic model validation and error handling

## Installation

The package is part of the Haive ecosystem and should be installed via Poetry:

```bash
# Install the entire Haive package (recommended)
poetry install --all-extras

# Or install just the MCP package dependencies
cd packages/haive-mcp
poetry install --all-extras

# Quick setup (installs dependencies and creates directories)
poetry run python install.py

# Full setup (installs MCP servers and configures everything)
poetry run python setup_all.py

# Or use the simple runner
poetry run python run.py setup
```

## Complete Workflow

### 1. Research Phase: Discover Servers for Your Use Case

```python
from haive.mcp.agents import MCPDocumentationAgent
from haive.core.engine import AugLLMConfig

# Create documentation research agent  
engine = AugLLMConfig(name="doc_research")
doc_agent = MCPDocumentationAgent.create_for_mcp_setup(engine=engine)
await doc_agent.setup()

# Find servers by capability (searches 992 server database)
database_servers = await doc_agent.find_servers_by_capability("database", limit=10)
file_servers = await doc_agent.find_servers_by_capability("filesystem", limit=5)

print(f"Found {len(database_servers)} database servers")
print(f"Found {len(file_servers)} file system servers")

# Generate complete implementation guide
implementation_guide = await doc_agent.generate_implementation_guide(
    server_names=[
        "modelcontextprotocol/server-postgres",
        "modelcontextprotocol/server-filesystem", 
        "modelcontextprotocol/server-github"
    ],
    target_agent_type="development_assistant"
)

print("Setup Instructions:")
print(implementation_guide["setup_instructions"])
```

### 2. Production Phase: Use Discovered Configuration

```python
from haive.mcp.agents import MCPAgent

# Create production agent with auto-generated configuration
production_agent = MCPAgent(
    engine=engine,
    mcp_config=implementation_guide["combined_config"],  # Auto-generated!
    name="production_assistant"
)

# Initialize and use - agent now has database, file, and GitHub tools
await production_agent.setup()

result = await production_agent.arun({
    "messages": [{
        "role": "user", 
        "content": "Connect to the database, read the config file, and check GitHub repo status"
    }]
})
```

## Core Components

### MCPDocumentationAgent
Intelligent agent for researching and analyzing the 992-server database:
- `find_servers_by_capability(capability, limit)` - AI-powered server discovery
- `generate_implementation_guide(server_names, target_agent_type)` - Complete setup guides
- `process_mcp_server(server_name)` - Analyze specific server documentation

### MCPAgent  
Production agent that uses MCP servers:
- Connects to multiple MCP servers simultaneously
- Auto-discovers tools and resources from connected servers
- Integrates seamlessly with Haive agent framework

### MCPDocumentationLoader
Direct access to the documentation database:
```python
from haive.mcp.documentation import MCPDocumentationLoader

loader = MCPDocumentationLoader()
all_servers = loader.load_all_mcp_documents()  # 992 servers
postgres_doc = loader.get_server_documentation("modelcontextprotocol/server-postgres")
```

## Advanced Features

### Tool Transfer Between Agents
```python
from haive.mcp.agents import TransferableMCPAgent

# Create collaborative agents that can share tools
agent1 = TransferableMCPAgent(engine=engine, mcp_config=config1)
agent2 = TransferableMCPAgent(engine=engine, mcp_config=config2)

await agent1.setup()
await agent2.setup()

# Transfer specific tools between agents
await agent1.transfer_tools_to_agent(agent2, tool_names=["read_file", "query_db"])

# Or transfer all tools
await agent1.transfer_all_tools_to_agent(agent2)
```

### Mass Server Installation
```python
from haive.mcp.downloader import GeneralMCPDownloader

# Install all 992 documented servers automatically
downloader = GeneralMCPDownloader()
await downloader.download_all_servers()

# Or install specific servers
await downloader.install_server("@modelcontextprotocol/server-postgres")
```

## Configuration

Most configurations are auto-generated from documentation, but you can also create them manually:

```python
from haive.mcp.config import MCPConfig, MCPServerConfig

mcp_config = MCPConfig(
    enabled=True,
    servers={
        "postgres": MCPServerConfig(
            name="postgres",
            transport="stdio", 
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres"],
            env={"DATABASE_URL": "postgresql://..."}
        ),
        "filesystem": MCPServerConfig(
            name="filesystem",
            transport="stdio",
            command="npx", 
            args=["-y", "@modelcontextprotocol/server-filesystem"]
        )
    }
)
```

**But it's easier to use the documentation agent to generate configurations automatically!**

## Data Sources

The system leverages a comprehensive collection of MCP server documentation:
- **992 GitHub repositories** with MCP servers automatically scraped
- **README parsing** for setup instructions and configuration
- **LLM-powered capability extraction** for intelligent categorization
- **Installation command detection** from documentation
- **Pre-processed and cached** for fast access

This makes haive-mcp the most comprehensive MCP integration system available.

## Examples

```bash
# See complete examples
poetry run python examples/mcp_documentation_example.py
poetry run python examples/complete_mcp_integration.py
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_mcp_real.py -v

# Run with coverage
poetry run pytest --cov=haive.mcp

# Validate setup
poetry run python validate_setup.py

# Check health
poetry run python check_health.py

# Or use the runner
poetry run python run.py test
poetry run python run.py check
poetry run python run.py validate
```

## Dependencies

- `pydantic>=2.0` - Configuration validation
- `langchain-mcp-adapters` - MCP client implementation
- `mcp` or `fastmcp` - Core MCP protocol
- `langchain-core` - Tool interfaces
- `langgraph` - Graph workflows

## Contributing

1. Follow Google-style docstrings
2. Add type hints to all functions
3. Write tests for new features
4. Update documentation

## License

MIT License - see LICENSE file for details.

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Specification](https://github.com/modelcontextprotocol/specification)
- [Haive Framework](https://github.com/yourusername/haive)
