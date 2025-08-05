"""Module exports."""

from haive.mcp.agents.documentation_agent import (
    MCPDocumentationAgent,
)
from haive.mcp.agents.intelligent_mcp_agent import (
    ApprovalStatus,
    HITLApprovalRequest,
    IntelligentMCPAgent,
    ServerRecommendation,
    create_auto_discovering_agent,
    create_manual_discovery_agent,
)

# Note: mcp_agent module may not exist, handle gracefully
try:
    from haive.mcp.agents.mcp_agent import (
        MCPAgent,
        create_filesystem_agent,
        create_github_agent,
        create_multi_mcp_agent,
    )
except ImportError:
    # Define fallback or skip these imports
    MCPAgent = None
    create_filesystem_agent = None
    create_github_agent = None
    create_multi_mcp_agent = None

from haive.mcp.agents.transferable_mcp_agent import (
    TransferableMCPAgent,
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
    "create_filesystem_agent",
    "create_github_agent",
    "create_manual_discovery_agent",
    "create_multi_mcp_agent",
]
