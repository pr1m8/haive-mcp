"""
MCP Server Installation System

Provides two approaches:
1. SafePatternInstaller - Uses predefined patterns (recommended)
2. AdvancedCodeInstaller - Uses LLM code generation (with human oversight)
"""

from .safe_pattern_installer import SafePatternInstaller, MCPServerPattern
from .advanced_code_installer import AdvancedCodeInstaller
from .config_manager import MCPConfigManager, MCPEnvironmentConfig

__all__ = [
    "SafePatternInstaller",
    "MCPServerPattern", 
    "AdvancedCodeInstaller",
    "MCPConfigManager",
    "MCPEnvironmentConfig",
]