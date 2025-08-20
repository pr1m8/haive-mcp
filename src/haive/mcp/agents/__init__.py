"""Module exports."""

# Handle missing dependencies gracefully
try:
    from haive.mcp.agents.documentation_agent import (
        MCPDocumentationAgent,
    )
except ImportError:
    # DocumentAgent dependency not available
    MCPDocumentationAgent = None
try:
    from haive.mcp.agents.intelligent_mcp_agent import (
        ApprovalStatus,
        HITLApprovalRequest,
        IntelligentMCPAgent,
        ServerRecommendation,
        create_auto_discovering_agent,
        create_manual_discovery_agent,
    )
except ImportError:
    # Dependencies not available
    ApprovalStatus = None
    HITLApprovalRequest = None
    IntelligentMCPAgent = None
    ServerRecommendation = None
    create_auto_discovering_agent = None
    create_manual_discovery_agent = None

# Import from mcp_agent (formerly enhanced_mcp_agent)
try:
    from haive.mcp.agents.mcp_agent import (
        MCPAgent,
        MCPIntegrationStats,
        create_mcp_agent,
    )
except ImportError:
    MCPAgent = None
    MCPIntegrationStats = None
    create_mcp_agent = None

try:
    from haive.mcp.agents.transferable_mcp_agent import (
        TransferableMCPAgent,
    )
except ImportError:
    TransferableMCPAgent = None

# Import from basic_mcp_agent (formerly mcp_agent)
try:
    from haive.mcp.agents.basic_mcp_agent import (
        BasicMCPAgent,
        create_filesystem_agent,
        create_github_agent,
        create_multi_mcp_agent,
    )
except ImportError:
    BasicMCPAgent = None
    create_filesystem_agent = None
    create_github_agent = None
    create_multi_mcp_agent = None

__all__ = [
    "ApprovalStatus",
    "BasicMCPAgent",
    "HITLApprovalRequest",
    "IntelligentMCPAgent",
    "MCPAgent",
    "MCPDocumentationAgent",
    "MCPIntegrationStats",
    "ServerRecommendation",
    "TransferableMCPAgent",
    "create_auto_discovering_agent",
    "create_filesystem_agent",
    "create_github_agent",
    "create_manual_discovery_agent",
    "create_mcp_agent",
    "create_multi_mcp_agent",
]
