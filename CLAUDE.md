# CLAUDE.md - Haive MCP Package Guide

**Purpose**: Central guide for working with the haive-mcp package
**Version**: 1.0
**Last Updated**: 2025-01-18

## 🎯 Package Overview

Haive MCP (Model Context Protocol) enables **dynamic, runtime integration** of tools from **1900+ MCP servers** from top GitHub repositories. Think of it as "USB-C for AI" - plug in any tool your agent needs, when it needs it.

**Key Innovation**: Agents can automatically discover and integrate tools based on their task requirements, without predefined configuration.

## 📁 Directory Structure

```
haive-mcp/
├── src/haive/mcp/
│   ├── __init__.py              # Main exports and module docstring
│   ├── config.py                # MCPConfig, MCPServerConfig classes
│   ├── manager.py               # MCPManager for dynamic server management
│   ├── cli.py                   # CLI tool for server selection
│   │
│   ├── agents/                  # MCP-enabled agent implementations
│   │   ├── mcp_agent.py         # Basic MCPAgent
│   │   ├── intelligent_mcp_agent.py  # Auto-discovery agent
│   │   ├── transferable_mcp_agent.py # Tool-sharing agent
│   │   └── documentation_agent.py    # Doc-aware agent
│   │
│   ├── mixins/                  # Add MCP to existing agents
│   │   └── mcp_mixin.py         # MCPMixin class
│   │
│   ├── tools/                   # MCP utility tools
│   │   ├── server_selector.py   # Intelligent server selection
│   │   ├── server_tester.py     # Server testing utilities
│   │   └── ai_assistant.py      # AI-powered configuration
│   │
│   ├── discovery/               # Server discovery system
│   │   └── server_discovery.py  # Discovery placeholder
│   │
│   ├── documentation/           # Documentation loading
│   │   └── doc_loader.py        # Load 1900+ server docs
│   │
│   ├── retrieval/              # Vector retrieval systems
│   │   └── *.py                # FAISS retrievers
│   │
│   ├── examples/               # Example implementations
│   │   └── *.py                # Usage examples
│   │
│   └── integration/            # Integration utilities
│       └── *.py                # Helper scripts
│
├── docs/source/                # Sphinx documentation
│   ├── index.rst               # Main docs (emphasizes 1900+ servers)
│   ├── quickstart.rst          # Dynamic discovery guide
│   └── *.rst                   # Other documentation
│
├── tests/                      # Test files
└── scripts/                    # Utility scripts
```

## 🚀 Quick Start Commands

```bash
# Install package with dependencies
poetry install

# Run CLI tool
poetry run python -m haive.mcp.cli --help

# List all 1900+ available servers
poetry run python -m haive.mcp.cli list-servers

# Get AI recommendations for a task
poetry run python -m haive.mcp.cli recommend "analyze GitHub repository" --ai-mode

# Interactive server selection
poetry run python -m haive.mcp.cli select

# Auto-configure for a task
poetry run python -m haive.mcp.cli auto-config "research AI papers" --output config.json
```

## 💻 Common Development Tasks

### 1. Adding a New MCP Server Integration

```python
# In src/haive/mcp/agents/custom_agent.py
from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig

class CustomMCPAgent(MCPAgent):
    """Your custom MCP-enabled agent."""
    
    def __init__(self, **kwargs):
        # Custom initialization
        super().__init__(**kwargs)
    
    @classmethod
    def create_for_task(cls, task: str, engine):
        """Factory method for task-specific setup."""
        # Auto-configure based on task
        config = cls._analyze_and_configure(task)
        return cls(engine=engine, mcp_config=config)
```

### 2. Creating a Custom Server Selector

```python
# In src/haive/mcp/tools/custom_selector.py
from haive.mcp.tools.server_selector import MCPServerSelector

class DomainSpecificSelector(MCPServerSelector):
    """Selector for specific domain (e.g., data science)."""
    
    def __init__(self):
        super().__init__()
        self.domain_keywords = ["data", "analysis", "ml", "visualization"]
    
    def recommend_for_domain(self, task: str):
        # Custom recommendation logic
        return self.filter_by_keywords(self.domain_keywords)
```

### 3. Working with the 1900+ Server Database

```python
from haive.mcp.documentation import MCPDocumentationLoader

# Load all server documentation
loader = MCPDocumentationLoader()
all_servers = loader.load_all_mcp_documents()
print(f"Available servers: {len(all_servers)}")  # 1900+

# Search by capability
file_servers = loader.search_servers_by_capability("file")
db_servers = loader.search_servers_by_capability("database")

# Get specific server info
fs_server = loader.get_server_documentation("modelcontextprotocol/server-filesystem")
setup_info = loader.extract_setup_info(fs_server)
```

### 4. Dynamic Tool Discovery Pattern

```python
from haive.mcp.agents import IntelligentMCPAgent

# Agent automatically discovers needed tools
agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True,      # Enable discovery
    require_approval=False   # Auto-install (for automation)
)

# Agent analyzes task and installs appropriate servers
result = await agent.arun({
    "messages": [{"role": "user", "content": "Search web for AI news and save to database"}]
})
# Agent will automatically discover and install web search + database servers
```

## 🧪 Testing

```bash
# Run all tests
poetry run pytest tests/

# Run specific test file
poetry run pytest tests/test_mcp_agent.py -v

# Test with real MCP servers (requires setup)
poetry run pytest tests/integration/ -v

# Test CLI commands
poetry run python -m haive.mcp.cli list-servers --prefix "anthropic/"
```

## 📝 Documentation

### Building Docs
```bash
# Build Sphinx documentation
cd docs
poetry run sphinx-build -b html source build

# View locally
python -m http.server 8000 --directory build
```

### Key Documentation Files
- `docs/source/index.rst` - Main page (emphasizes 1900+ servers)
- `docs/source/quickstart.rst` - Dynamic discovery examples
- `docs/source/api_reference.rst` - API documentation
- `docs/source/advanced.rst` - Custom server development

## 🔧 Common Patterns

### Pattern 1: Static MCP Configuration
```python
# When you know which servers you need
agent = MCPAgent(
    engine=engine,
    mcp_config=MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"]
            )
        }
    )
)
```

### Pattern 2: Dynamic Discovery
```python
# Let the agent figure out what it needs
agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True
)
# Agent will analyze task and install appropriate servers
```

### Pattern 3: Capability-Based Selection
```python
# Select servers by required capabilities
selector = MCPServerSelector()
servers = selector.filter_by_capabilities([
    "file_read", "file_write", "web_search"
])
config = selector.create_config_for_selection(servers)
```

### Pattern 4: Tool Transfer Between Agents
```python
# Share tools between agents
source_agent = TransferableMCPAgent(engine=engine1)
target_agent = MCPAgent(engine=engine2)

# Transfer MCP tools
tools = source_agent.export_mcp_tools()
target_agent.import_mcp_tools(tools)
```

## 🚨 Important Notes

1. **Server Count**: We have **1900+ MCP servers** from top GitHub repositories - always emphasize this!

2. **Dynamic Nature**: The key innovation is **runtime discovery** - agents find tools as needed

3. **No Mocks**: Always test with real MCP servers, never mock the protocol

4. **Async First**: All MCP operations are async - use `await` properly

5. **Error Handling**: MCP connections can fail - always handle gracefully

## 🔍 Debugging

```python
# Enable debug logging
import logging
logging.getLogger("haive.mcp").setLevel(logging.DEBUG)

# Check MCP status
status = agent.get_mcp_status()
print(f"Connected servers: {status['connected_servers']}")
print(f"Available tools: {status['tool_count']}")
print(f"Failed servers: {status['failed_servers']}")

# Test specific server
from haive.mcp.tools import test_mcp_server
result = await test_mcp_server("filesystem", timeout=30)
```

## 🎯 Key Files for Different Tasks

### Working on Agent Integration
- `src/haive/mcp/agents/mcp_agent.py` - Base implementation
- `src/haive/mcp/mixins/mcp_mixin.py` - Add to existing agents
- `src/haive/mcp/config.py` - Configuration structures

### Working on Discovery System
- `src/haive/mcp/agents/intelligent_mcp_agent.py` - Auto-discovery
- `src/haive/mcp/tools/server_selector.py` - Selection logic
- `src/haive/mcp/documentation/doc_loader.py` - Server database

### Working on CLI Tools
- `src/haive/mcp/cli.py` - Main CLI implementation
- `src/haive/mcp/tools/ai_assistant.py` - AI recommendations

### Working on Documentation
- `docs/source/index.rst` - Main documentation
- `docs/source/quickstart.rst` - Getting started guide
- `src/haive/mcp/DOCSTRING_EXAMPLE.md` - Docstring templates

## 🚀 Next Steps

1. **Implement Real Discovery** - Replace placeholder with actual registry connection
2. **Add More Examples** - Show integration with different agent types
3. **Performance Optimization** - Cache server metadata for faster discovery
4. **Enhanced Testing** - Add integration tests with popular MCP servers

---

**Remember**: The power of MCP is in its **1900+ servers** and **dynamic discovery**. Always highlight these capabilities when working on this package!