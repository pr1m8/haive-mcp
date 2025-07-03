"""Pytest configuration and fixtures for haive-mcp tests.

This module provides common fixtures and configuration for all tests
in the haive-mcp package.

Fixtures:
    mock_mcp_client: Mock MCP client for testing
    test_server_config: Test server configuration
    test_engine: Test LLM engine
    temp_directory: Temporary directory for file operations
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add the src directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from haive.mcp.config import MCPConfig, MCPServerConfig


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing.
    
    Returns:
        Mock MCP client with common methods stubbed.
    """
    client = MagicMock()
    
    # Mock tool loading
    mock_tools = [
        MagicMock(name="read_file", description="Read a file"),
        MagicMock(name="write_file", description="Write a file"),
        MagicMock(name="list_files", description="List files"),
    ]
    
    client.load_tools = AsyncMock(return_value=mock_tools)
    client.execute_tool = AsyncMock(return_value={"result": "success"})
    client.get_server_info = AsyncMock(return_value={
        "name": "test-server",
        "version": "1.0.0",
        "capabilities": ["tools", "resources"]
    })
    
    return client


@pytest.fixture
def test_server_config():
    """Create a test server configuration.
    
    Returns:
        MCPServerConfig: Test server configuration
    """
    return MCPServerConfig(
        name="test-server",
        transport="stdio",
        command="python",
        args=["test_server.py"],
        capabilities=["file_ops", "search"],
        env={"TEST_MODE": "true"}
    )


@pytest.fixture
def test_mcp_config(test_server_config):
    """Create a test MCP configuration.
    
    Args:
        test_server_config: Test server configuration fixture
        
    Returns:
        MCPConfig: Test MCP configuration
    """
    return MCPConfig(
        enabled=True,
        servers={"test": test_server_config},
        auto_discover=False
    )


@pytest.fixture
def test_engine():
    """Create a mock LLM engine for testing.
    
    Returns:
        Mock engine with required methods
    """
    engine = MagicMock()
    engine.name = "test-engine"
    engine.llm_config = MagicMock(model="gpt-4")
    engine.create_runnable = MagicMock()
    
    return engine


@pytest.fixture
def temp_directory(tmp_path):
    """Create a temporary directory for file operations.
    
    Args:
        tmp_path: Pytest tmp_path fixture
        
    Returns:
        Path: Temporary directory path
    """
    test_dir = tmp_path / "mcp_test"
    test_dir.mkdir()
    
    # Create some test files
    (test_dir / "test1.txt").write_text("Test content 1")
    (test_dir / "test2.txt").write_text("Test content 2")
    
    subdir = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "test3.txt").write_text("Test content 3")
    
    return test_dir


@pytest.fixture
def mock_server_discovery():
    """Create a mock server discovery instance.
    
    Returns:
        Mock discovery with test servers
    """
    discovery = MagicMock()
    
    test_servers = [
        {
            "name": "filesystem-server",
            "description": "File system operations",
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
            "capabilities": ["file_read", "file_write"]
        },
        {
            "name": "github-server",
            "description": "GitHub operations",
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "capabilities": ["repo_read", "issue_create"]
        }
    ]
    
    discovery.discover_all = AsyncMock(return_value=test_servers)
    discovery.get_servers_by_capability = MagicMock(
        side_effect=lambda cap: [s for s in test_servers if cap in s.get("capabilities", [])]
    )
    
    return discovery


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_mcp: marks tests that require MCP to be installed"
    )


# Async test support
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
