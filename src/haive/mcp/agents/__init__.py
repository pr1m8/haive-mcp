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

try:
    from haive.mcp.agents.transferable_mcp_agent import (
        TransferableMCPAgent,
    )
except ImportError:
    TransferableMCPAgent = None

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
