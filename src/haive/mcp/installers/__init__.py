"""MCP Server Installation System

Provides two approaches:
1. SafePatternInstaller - Uses predefined patterns (recommended)
2. AdvancedCodeInstaller - Uses LLM code generation (with human oversight)
"""

from haive.mcp.installers.advanced_code_installer import AdvancedCodeInstaller
from haive.mcp.installers.config_manager import MCPConfigManager, MCPEnvironmentConfig
from haive.mcp.installers.safe_pattern_installer import (
    MCPServerPattern,
    SafePatternInstaller,
)


__all__ = [
    "AdvancedCodeInstaller",
    "MCPConfigManager",
    "MCPEnvironmentConfig",
    "MCPServerPattern",
    "SafePatternInstaller",
]
