"""MCP tools for intelligent server selection and management.

This package provides tools to help AI agents and users intelligently select,
filter, and manage MCP servers based on various criteria.
"""

from haive.mcp.tools.ai_assistant import (
    MCPAssistant,
    ServerRecommendation,
    SmartConfiguration,
    TaskMatcher,
)
from haive.mcp.tools.server_selector import (
    MCPServerSelector,
    ServerFilter,
    ServerScore,
    TaskAnalyzer,
    TaskRequirements,
)
from haive.mcp.tools.server_tester import (
    HealthMonitor,
    HealthStatus,
    MCPServerTester,
    TestResult,
)


__all__ = [
    "HealthMonitor",
    "HealthStatus",
    "MCPAssistant",
    "MCPServerSelector",
    "MCPServerTester",
    "ServerFilter",
    "ServerRecommendation",
    "ServerScore",
    "SmartConfiguration",
    "TaskAnalyzer",
    "TaskMatcher",
    "TaskRequirements",
    "TestResult",
]
