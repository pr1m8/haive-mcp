# TODO - Haive MCP

## 🔄 Refactoring Tasks

### 1. Rename EnhancedMCPAgent to MCPAgent
- [ ] Rename class from `EnhancedMCPAgent` to `MCPAgent` in `/src/haive/mcp/agents/enhanced_mcp_agent.py`
- [ ] Update file name from `enhanced_mcp_agent.py` to `mcp_agent.py` (or keep existing `mcp_agent.py` and merge functionality)
- [ ] Update all imports across the codebase
- [ ] Update all documentation references
- [ ] Update all test files
- [ ] Consider deprecation path for existing MCPAgent if merging

### 2. Update Documentation After Rename
- [ ] Update all references in `docs/source/quickstart.rst`
- [ ] Update all references in `docs/source/guides.rst`
- [ ] Update all references in `docs/source/tutorials/01_understanding_mcp.md`
- [ ] Update all references in `docs/source/tutorials/02_first_mcp_server.md`
- [ ] Update all references in `docs/source/tutorials/03_installer_types.md`
- [ ] Update all references in `docs/source/tutorials.rst`
- [ ] Update all code examples in documentation
- [ ] Update API reference documentation

### 3. Update Tests After Rename
- [ ] Update `test_phase4_agent_integration.py`
- [ ] Update all test imports
- [ ] Ensure all tests still pass after rename

### 4. Consider Architecture
- [ ] Decide if current `MCPAgent` should be deprecated or merged
- [ ] Ensure backward compatibility if needed
- [ ] Update any factory methods or class methods

## 📝 Notes

The current `EnhancedMCPAgent` represents the fully-featured MCP integration with:
- Dynamic tool discovery
- Automatic server installation
- Native MCP protocol support
- Category-based server management
- Health monitoring and debugging

This should become the standard `MCPAgent` as it's the primary way users will interact with MCP functionality.

## 🎯 Priority

**HIGH** - This simplifies the API and makes it clearer for users that this is the main MCP agent implementation, not an "enhanced" variant.