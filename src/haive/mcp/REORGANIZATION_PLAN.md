# MCP Source Code Reorganization Plan

## Current Issues

1. Too many files at the root level (30+ files)
2. Mix of production code, experiments, and utilities
3. Unclear which components are core vs experimental
4. Duplicate functionality across files

## Proposed Structure

```
src/haive/mcp/
├── __init__.py              # Clean exports
├── manager.py               # Core MCPManager (keep at root - it's central)
├── config.py                # Core configuration (keep at root)
│
├── agents/                  # ✅ Already organized
│   ├── intelligent_mcp_agent.py
│   ├── mcp_agent.py
│   ├── transferable_mcp_agent.py
│   └── documentation_agent.py
│
├── discovery/               # ✅ Already exists
│   └── (server discovery components)
│
├── servers/                 # ✅ Already exists
│   └── (server implementations)
│
├── tools/                   # ✅ Already exists
│   └── (tool implementations)
│
├── mixins/                  # ✅ Already exists
│   └── (mixin classes)
│
├── utils/                   # ✅ Already exists
│   └── (utility functions)
│
├── retrieval/               # NEW - RAG/retrieval components
│   ├── simple_faiss_retriever.py
│   ├── enhanced_parent_self_query_retriever.py
│   ├── working_enhanced_retriever.py
│   └── complete_mcp_with_parent_retriever.py
│
├── examples/                # NEW - Move example implementations
│   ├── simple_rag_mcp_agent.py
│   ├── mcp_simple_rag_agent.py
│   ├── mcp_simple_tool_agent.py
│   ├── self_query_mcp_agent.py
│   └── self_query_mcp_agent_v2.py
│
├── integrations/            # ✅ Use existing integration directory
│   ├── haive_agent_mcp_integration.py
│   ├── fastapi_mcp_server.py
│   └── integrated_mcp_system.py
│
└── archive/                 # NEW - Experimental/old code
    ├── comprehensive_mcp_web.py
    ├── csv_viewer.py
    ├── dynamic_activation_mcp.py
    ├── dynamic_mcp_tool.py
    ├── enhance_mcp_data.py
    ├── fastmcp_runner.py
    ├── integrated_launcher.py
    ├── launcher.py
    ├── mcp_rag_agent.py
    └── production_mcp_tool.py
```

## Files to Keep at Root

1. `__init__.py` - Package initialization
2. `manager.py` - Core MCPManager class
3. `config.py` - Core configuration classes

## Action Items

### 1. Create New Directories

```bash
mkdir -p src/haive/mcp/retrieval
mkdir -p src/haive/mcp/examples
mkdir -p src/haive/mcp/archive
```

### 2. Move Files to Appropriate Locations

#### To `retrieval/`:

- simple_faiss_retriever.py
- enhanced_parent_self_query_retriever.py
- working_enhanced_retriever.py
- complete_mcp_with_parent_retriever.py

#### To `examples/`:

- simple_rag_mcp_agent.py
- mcp_simple_rag_agent.py
- mcp_simple_tool_agent.py
- self_query_mcp_agent.py
- self_query_mcp_agent_v2.py

#### To `integrations/`:

- haive_agent_mcp_integration.py
- fastapi_mcp_server.py
- integrated_mcp_system.py

#### To `archive/`:

- comprehensive_mcp_web.py
- csv_viewer.py
- dynamic_activation_mcp.py
- dynamic_mcp_tool.py
- enhance_mcp_data.py
- fastmcp_runner.py
- integrated_launcher.py
- launcher.py
- mcp_rag_agent.py
- production_mcp_tool.py

### 3. Update Imports

After moving files, update all imports to reflect new locations.

### 4. Clean Up **init**.py

Update to only export the core components:

- MCPManager
- MCPAgent
- IntelligentMCPAgent
- TransferableMCPAgent
- Core configuration classes

### 5. Add Google-style Docstrings

Focus on core components that don't have proper docstrings yet.
