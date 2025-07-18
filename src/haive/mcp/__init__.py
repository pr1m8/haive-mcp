"""Haive MCP - Dynamic Model Context Protocol Integration for Haive Agents.

haive-mcp brings the power of Model Context Protocol to Haive agents with dynamic
discovery, hot-reload capabilities, and intelligent server management. Access 1,960+
pre-indexed MCP servers and let your agents automatically find and install the
tools they need - all without restarting.

Key Features:
    - 🔄 Hot-Reload: Add servers and refresh tools without restart
    - 🤖 Intelligent Discovery: AI analyzes needs and suggests servers
    - 👤 HITL Approval: Human-in-the-loop approval workflows
    - 📚 1,960+ Servers: Pre-indexed database of MCP servers
    - 🔧 Dynamic Tools: Tools, resources, and prompts from MCP
    - ⚡ Real-time: Install and use immediately

Quick Start:

    ```python
    from haive.mcp.agents import IntelligentMCPAgent
    from haive.core.engine.aug_llm import AugLLMConfig

    # Create intelligent agent that auto-discovers servers
    agent = IntelligentMCPAgent(
        engine=AugLLMConfig(),
        auto_discover=True,      # Find servers automatically
        require_approval=True    # Ask before installing
    )
    
    await agent.setup()
    
    # Agent installs what it needs based on your request!
    result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Search the web for Python tutorials and save to file"
        }]
    })
    # Automatically installs web search + filesystem servers!
    ```

Components:
    - IntelligentMCPAgent: Dynamic discovery and management
    - MCPAgent: Production agent with static configs
    - MCPManager: Server lifecycle with hot-reload
    - TransferableMCPAgent: Share tools between agents
    - MCPDocumentationAgent: Process server documentation

Advanced Usage:

    ```python
    # Manual control with hot-reload
    manager = agent.mcp_manager
    await manager.add_server("github", github_config)
    tools = await manager.get_all_tools(refresh=True)
    
    # Custom approval workflows
    async def my_approval(request):
        print(f"Approve {request.recommendation.server_name}?")
        return input("y/n: ").lower() == 'y'
    
    agent = IntelligentMCPAgent(
        engine=engine,
        approval_callback=my_approval
    )
    ```

Attributes:
    __version__: Package version string
    MCPConfig: Main configuration model
    MCPServerConfig: Server configuration model
    MCPManager: Server lifecycle manager
    MCPAgent: MCP-enabled agent
    TransferableMCPAgent: Agent with tool transfer capabilities
    MCPDocumentationAgent: Documentation processing agent
"""

__version__ = "0.1.0"

# Import core MCP components
try:
    from haive.mcp.config import MCPConfig, MCPServerConfig
    from haive.mcp.manager import MCPManager

    # Try to import agents if available
    try:
        from haive.mcp.agents.mcp_agent import MCPAgent
        from haive.mcp.mixins.mcp_mixin import MCPMixin

        AGENTS_AVAILABLE = True
    except ImportError:
        AGENTS_AVAILABLE = False

    # Try to import discovery if available
    try:
        from haive.mcp.discovery.analyzer import MCPServerAnalyzer
        from haive.mcp.discovery.server_discovery import MCPServerDiscovery

        DISCOVERY_AVAILABLE = True
    except ImportError:
        DISCOVERY_AVAILABLE = False

    MCP_AVAILABLE = True
except ImportError:
    # Graceful degradation if MCP components aren't fully implemented
    MCP_AVAILABLE = False
    AGENTS_AVAILABLE = False
    DISCOVERY_AVAILABLE = False

__all__ = [
    "__version__",
]

if MCP_AVAILABLE:
    __all__.extend(
        [
            "MCPConfig",
            "MCPManager",
            "MCPServerConfig",
        ]
    )

if AGENTS_AVAILABLE:
    __all__.extend(
        [
            "MCPAgent",
            "MCPMixin",
        ]
    )

if DISCOVERY_AVAILABLE:
    __all__.extend(
        [
            "MCPServerAnalyzer",
            "MCPServerDiscovery",
        ]
    )
