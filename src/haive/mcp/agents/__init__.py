"""Module exports."""

from haive.mcp.agents.documentation_agent import (
    MCPDocumentationAgent,
    create_for_mcp_research,
    create_for_mcp_setup,
)
from haive.mcp.agents.intelligent_mcp_agent import (
    ApprovalStatus,
    HITLApprovalRequest,
    IntelligentMCPAgent,
    ServerRecommendation,
    create_auto_discovering_agent,
    create_manual_discovery_agent,
    get_pending_approvals,
    get_recommendation_history,
)

# Note: mcp_agent module may not exist, handle gracefully
try:
    from haive.mcp.agents.mcp_agent import (
        MCPAgent,
        create_filesystem_agent,
        create_github_agent,
        create_multi_mcp_agent,
        create_with_mcp_servers,
        get_available_capabilities,
        setup_agent,
        tool_count,
    )
except ImportError:
    # Define fallback or skip these imports
    MCPAgent = None
    create_filesystem_agent = None
    create_github_agent = None
    create_multi_mcp_agent = None
    create_with_mcp_servers = None
    get_available_capabilities = None
    setup_agent = None
    tool_count = None

from haive.mcp.agents.transferable_mcp_agent import (
    TransferableMCPAgent,
    create_collaborative_agents,
    get_transfer_status,
)

__all__ = [
    "ApprovalStatus",
    "HITLApprovalRequest",
    "IntelligentMCPAgent",
    "MCPAgent",
    "MCPDocumentationAgent",
    "ServerRecommendation",
    "TransferableMCPAgent",
    "create_auto_discovering_agent",
    "create_collaborative_agents",
    "create_filesystem_agent",
    "create_for_mcp_research",
    "create_for_mcp_setup",
    "create_github_agent",
    "create_manual_discovery_agent",
    "create_multi_mcp_agent",
    "create_with_mcp_servers",
    "get_available_capabilities",
    "get_pending_approvals",
    "get_recommendation_history",
    "get_transfer_status",
    "setup_agent",
    "tool_count",
]
