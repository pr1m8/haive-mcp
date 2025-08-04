"""Module exports."""

import lazy_loader as lazy

# Define submodules to lazy load
submodules = [
    "agents",
    "cli",
    "complete_mcp_with_parent_retriever",
    "comprehensive_mcp_web",
    "config",
    "csv_viewer",
    "discovery",
    "documentation",
    "downloader",
    "dynamic_activation_mcp",
    "dynamic_mcp_tool",
    "enhance_mcp_data",
    "enhanced_parent_self_query_retriever",
    "fastapi_mcp_server",
    "fastmcp_runner",
    "haive_agent_mcp_integration",
    "installers",
    "integrated_launcher",
    "integrated_mcp_system",
    "launcher",
    "manager",
    "mcp_rag_agent",
    "mcp_simple_rag_agent",
    "mcp_simple_tool_agent",
    "mixins",
    "production_mcp_tool",
    "self_query_mcp_agent",
    "servers",
    "simple_faiss_retriever",
    "simple_rag_mcp_agent",
    "tools",
    "utils",
    "working_enhanced_retriever",
]

# Define specific attributes from submodules to expose
# TODO: Customize this based on actual exports from each submodule
submod_attrs = {
    "agents": [],  # TODO: Add specific exports from agents
    "cli": [],  # TODO: Add specific exports from cli
    "complete_mcp_with_parent_retriever": [],  # TODO: Add specific exports from complete_mcp_with_parent_retriever
    "comprehensive_mcp_web": [],  # TODO: Add specific exports from comprehensive_mcp_web
    "config": [],  # TODO: Add specific exports from config
    "csv_viewer": [],  # TODO: Add specific exports from csv_viewer
    "discovery": [],  # TODO: Add specific exports from discovery
    "documentation": [],  # TODO: Add specific exports from documentation
    "downloader": [],  # TODO: Add specific exports from downloader
    "dynamic_activation_mcp": [],  # TODO: Add specific exports from dynamic_activation_mcp
    "dynamic_mcp_tool": [],  # TODO: Add specific exports from dynamic_mcp_tool
    "enhance_mcp_data": [],  # TODO: Add specific exports from enhance_mcp_data
    "enhanced_parent_self_query_retriever": [],  # TODO: Add specific exports from enhanced_parent_self_query_retriever
    "fastapi_mcp_server": [],  # TODO: Add specific exports from fastapi_mcp_server
    "fastmcp_runner": [],  # TODO: Add specific exports from fastmcp_runner
    "haive_agent_mcp_integration": [],  # TODO: Add specific exports from haive_agent_mcp_integration
    "installers": [],  # TODO: Add specific exports from installers
    "integrated_launcher": [],  # TODO: Add specific exports from integrated_launcher
    "integrated_mcp_system": [],  # TODO: Add specific exports from integrated_mcp_system
    "launcher": [],  # TODO: Add specific exports from launcher
    "manager": [],  # TODO: Add specific exports from manager
    "mcp_rag_agent": [],  # TODO: Add specific exports from mcp_rag_agent
    "mcp_simple_rag_agent": [],  # TODO: Add specific exports from mcp_simple_rag_agent
    "mcp_simple_tool_agent": [],  # TODO: Add specific exports from mcp_simple_tool_agent
    "mixins": [],  # TODO: Add specific exports from mixins
    "production_mcp_tool": [],  # TODO: Add specific exports from production_mcp_tool
    "self_query_mcp_agent": [],  # TODO: Add specific exports from self_query_mcp_agent
    "servers": [],  # TODO: Add specific exports from servers
    "simple_faiss_retriever": [],  # TODO: Add specific exports from simple_faiss_retriever
    "simple_rag_mcp_agent": [],  # TODO: Add specific exports from simple_rag_mcp_agent
    "tools": [],  # TODO: Add specific exports from tools
    "utils": [],  # TODO: Add specific exports from utils
    "working_enhanced_retriever": [],  # TODO: Add specific exports from working_enhanced_retriever
}

# Attach lazy loading - this creates __getattr__, __dir__, and __all__
__getattr__, __dir__, __all__ = lazy.attach(
    __name__, submodules=submodules, submod_attrs=submod_attrs
)

# Add any eager imports here (lightweight utilities, etc.)
# Example: from .metadata import SomeUtility
# __all__ += ['SomeUtility']
