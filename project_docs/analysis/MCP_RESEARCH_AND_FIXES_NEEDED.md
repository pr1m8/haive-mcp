# MCP Research and Fixes Needed

**Created**: 2025-08-19
**Purpose**: Document what needs to be fixed and proper MCP implementation research
**Status**: Post-cleanup analysis

## ✅ Cleanup Completed

### What We Fixed
1. **Directory Structure Restored**: Moved 63 downloaded MCP servers from package root to `downloads/mcp_servers/`
2. **Source Code Backup**: Clean backup created at `../haive-mcp-backup/`
3. **Package Structure**: Now clean with proper src/, docs/, tests/, guides/ structure
4. **Functionality Verified**: Basic imports working correctly

### Current Structure
```
haive-mcp/
├── src/haive/mcp/           # Core package source
├── downloads/mcp_servers/   # 63 downloaded servers (proper location)
├── docs/                    # Documentation
├── tests/                   # Test files
├── guides/                  # User guides
└── [clean package files]
```

## 🔍 Issues That Need Fixing

### 1. **Installer Problems**
- **Issue**: Bulk installer was downloading to wrong location (package root instead of downloads/)
- **Files**: `src/haive/mcp/installer/bulk_installer.py`
- **Fix Needed**: Update download path configuration

### 2. **Multiple Installer Systems** 
- **Issue**: We have overlapping installer implementations:
  - `src/haive/mcp/downloader/installers.py` - Framework
  - `src/haive/mcp/installers/` - Pattern-based
  - `src/haive/mcp/installer/bulk_installer.py` - Star-based
- **Fix Needed**: Consolidate into unified system

### 3. **Import Warnings**
- **Issue**: Pydantic field name conflicts (`Field name "schema" shadows parent`)
- **Fix Needed**: Rename conflicting fields in models

### 4. **Configuration Management**
- **Issue**: Multiple config files scattered across project
- **Fix Needed**: Centralized configuration system

## 📚 MCP Research Needed

### Core Questions to Research:

#### 1. **What is MCP Actually?**
- Model Context Protocol specification
- How it differs from regular tool integration
- Official MCP documentation and examples

#### 2. **How Should MCP Servers Be Used?**
- Proper installation methods (npm, pip, git, docker)
- How to start/stop MCP servers
- Connection protocols (stdio, HTTP, SSE)
- Authentication and security

#### 3. **Real MCP Implementation Patterns**
- How other projects implement MCP
- Official MCP client libraries
- Best practices for server management

#### 4. **MCP Server Configuration**
- Standard configuration formats
- Server discovery mechanisms
- Tool registration and routing

### Research Sources:
1. **Official MCP Documentation**: https://modelcontextprotocol.io/
2. **MCP GitHub Repos**: https://github.com/modelcontextprotocol/
3. **Anthropic MCP Guide**: Check Claude Code documentation
4. **Real MCP Implementations**: Study downloaded servers for patterns

## 🔧 Proposed Fix Plan

### Phase 1: Research & Understanding (CURRENT)
- [ ] Study official MCP specification
- [ ] Analyze real MCP server implementations from our 63 downloads
- [ ] Understand proper connection and usage patterns
- [ ] Document findings

### Phase 2: Architecture Design
- [ ] Design proper MCP integration architecture
- [ ] Plan unified installer system
- [ ] Design server lifecycle management
- [ ] Plan configuration system

### Phase 3: Implementation
- [ ] Fix installer download paths
- [ ] Consolidate installer systems
- [ ] Fix import warnings
- [ ] Implement proper MCP usage patterns

### Phase 4: Testing & Validation
- [ ] Test with real MCP servers
- [ ] Validate connection patterns
- [ ] Performance testing
- [ ] Documentation updates

## 🎯 Immediate Next Steps

1. **Research Official MCP Docs** - Understand what MCP actually is
2. **Analyze Downloaded Servers** - Look at real implementations
3. **Study Connection Patterns** - How servers are actually used
4. **Document Findings** - Create proper implementation guide

## 📁 Key Files to Examine

### Downloaded Servers to Study:
- `downloads/mcp_servers/browser-tools-mcp/` - Browser automation
- `downloads/mcp_servers/fastapi_mcp/` - FastAPI integration
- `downloads/mcp_servers/mcp-agent/` - Agent building
- `downloads/mcp_servers/awesome-mcp-servers/` - Server collection

### Our Implementation:
- `src/haive/mcp/` - Our MCP implementation
- `docs/` - Current documentation
- `guides/` - User guides (may need updating)

## 🚨 Critical Insights Needed

1. **Are we implementing MCP correctly?** - Need to validate against spec
2. **Should we be downloading/cloning servers?** - Or connecting to running instances?
3. **What's the proper server lifecycle?** - Install → Configure → Connect → Use
4. **How do authentication and security work?** - For production usage

---

**Next Action**: Begin MCP research phase to understand proper implementation patterns.