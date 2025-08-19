"""Pytest configuration and shared fixtures for MCP tests."""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory that's cleaned up after the test."""
    temp_dir = tempfile.mkdtemp(prefix="mcp_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for tests that need it."""
    mock = MagicMock()
    mock.return_value.returncode = 0
    mock.return_value.stdout = ""
    mock.return_value.stderr = ""
    return mock


@pytest.fixture
def sample_mcp_servers():
    """Sample MCP server data for testing."""
    return [
        {
            "name": "@modelcontextprotocol/server-filesystem",
            "stars": 5432,
            "category": "utility",
            "install_command": "npm install -g @modelcontextprotocol/server-filesystem",
            "repository_url": "https://github.com/modelcontextprotocol/servers"
        },
        {
            "name": "mcp-server-python-example",
            "stars": 234,
            "category": "example",
            "install_command": "pip install mcp-server-python-example",
            "repository_url": "https://github.com/example/mcp-python"
        },
        {
            "name": "custom-mcp-server",
            "stars": 0,
            "category": "custom",
            "install_command": "",
            "repository_url": "https://github.com/user/custom-mcp"
        }
    ]


@pytest.fixture
def mock_mcp_server_response():
    """Mock response for MCP server communication."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "status": "success",
            "data": "Mock response data"
        }
    }


# Skip markers for different test categories
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_network: mark test as requiring network access"
    )