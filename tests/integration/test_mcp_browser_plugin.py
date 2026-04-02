#!/usr/bin/env python
"""
Tests for MCPBrowserPlugin - Real Data Integration Testing

This test suite validates the MCPBrowserPlugin with simulated real downloaded server data,
demonstrating the complete Pydantic-first architecture and intelligent inheritance patterns.

Tests cover:
- Plugin initialization and inheritance validation
- Server loading from CSV and install report data  
- Caching mechanism with TTL
- Server filtering and search methods
- Plugin statistics generation
- FastAPI routes registration
- Performance and caching behavior
- Plugin cleanup
"""

import asyncio
import json
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd


@pytest.fixture
def sample_csv_data():
    """Sample CSV data representing our downloaded servers."""
    return [
        {
            "name": "server-filesystem",
            "description": "File system operations for MCP",
            "repository_url": "https://github.com/modelcontextprotocol/server-filesystem",
            "stars": 245,
            "language": "TypeScript",
            "updated_at": "2024-12-01T10:00:00Z",
            "license": "MIT",
            "topics": "mcp,filesystem,tools",
            "author": "Anthropic"
        },
        {
            "name": "server-postgres",
            "description": "PostgreSQL database operations",
            "repository_url": "https://github.com/modelcontextprotocol/server-postgres",
            "stars": 189,
            "language": "JavaScript",
            "updated_at": "2024-11-28T15:30:00Z",
            "license": "MIT",
            "topics": "mcp,database,postgresql",
            "author": "Anthropic"
        },
        {
            "name": "server-brave-search",
            "description": "Web search using Brave Search API",
            "repository_url": "https://github.com/modelcontextprotocol/server-brave-search",
            "stars": 156,
            "language": "Python",
            "updated_at": "2024-12-02T09:15:00Z",
            "license": "Apache-2.0",
            "topics": "mcp,search,web",
            "author": "Anthropic"
        },
        {
            "name": "server-puppeteer",
            "description": "Browser automation with Puppeteer",
            "repository_url": "https://github.com/modelcontextprotocol/server-puppeteer",
            "stars": 312,
            "language": "TypeScript",
            "updated_at": "2024-11-30T12:45:00Z",
            "license": "MIT",
            "topics": "mcp,browser,automation",
            "author": "Anthropic"
        },
        {
            "name": "server-memory",
            "description": "Persistent memory for MCP sessions",
            "repository_url": "https://github.com/modelcontextprotocol/server-memory",
            "stars": 78,
            "language": "Python",
            "updated_at": "2024-12-01T16:20:00Z",
            "license": "MIT",
            "topics": "mcp,memory,persistence",
            "author": "Anthropic"
        }
    ]


@pytest.fixture
def sample_install_report():
    """Sample install report from our bulk installer."""
    return {
        "session_id": "bulk-install-20250119-143022",
        "start_time": "2025-01-19T14:30:22Z",
        "end_time": "2025-01-19T14:45:15Z",
        "total_servers": 5,
        "success_count": 5,
        "failure_count": 0,
        "success_rate": 100.0,
        "installed_servers": [
            "server-filesystem",
            "server-postgres", 
            "server-brave-search",
            "server-puppeteer",
            "server-memory"
        ],
        "failed_servers": [],
        "install_log": [
            {
                "name": "server-filesystem",
                "command": "npx -y @modelcontextprotocol/server-filesystem",
                "status": "success",
                "duration_seconds": 12.3,
                "install_path": "./servers/server-filesystem",
                "package_json_exists": True
            },
            {
                "name": "server-postgres",
                "command": "npx -y @modelcontextprotocol/server-postgres",
                "status": "success",
                "duration_seconds": 8.7,
                "install_path": "./servers/server-postgres",
                "package_json_exists": True
            },
            {
                "name": "server-brave-search",
                "command": "pip install mcp-server-brave-search",
                "status": "success",
                "duration_seconds": 15.2,
                "install_path": "./servers/server-brave-search",
                "package_json_exists": False
            },
            {
                "name": "server-puppeteer",
                "command": "npx -y @modelcontextprotocol/server-puppeteer",
                "status": "success",
                "duration_seconds": 18.9,
                "install_path": "./servers/server-puppeteer",
                "package_json_exists": True
            },
            {
                "name": "server-memory",
                "command": "pip install mcp-server-memory",
                "status": "success",
                "duration_seconds": 9.1,
                "install_path": "./servers/server-memory",
                "package_json_exists": False
            }
        ]
    }


@pytest.fixture
def test_data_files(sample_csv_data, sample_install_report):
    """Create temporary data files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create CSV file
        csv_file = temp_path / "mcp_servers_data.csv"
        df = pd.DataFrame(sample_csv_data)
        df.to_csv(csv_file, index=False)
        
        # Create install report file
        report_file = temp_path / f"mcp_install_report_{sample_install_report['session_id']}.json"
        with open(report_file, 'w') as f:
            json.dump(sample_install_report, f, indent=2)
        
        yield temp_path, csv_file, report_file


@pytest.fixture
def plugin_instance(test_data_files):
    """Create a configured MCPBrowserPlugin instance."""
    import sys
    import importlib.util
    from pathlib import Path
    
    # Import dependencies
    mcp_src = Path(__file__).parent.parent / "src"
    dataflow_src = Path(__file__).parent.parent.parent / "haive-dataflow" / "src"
    
    sys.path.insert(0, str(mcp_src))
    sys.path.insert(0, str(dataflow_src))
    
    # Import the plugin directly
    plugin_path = mcp_src / "haive" / "mcp" / "plugins" / "browser_plugin.py"
    spec = importlib.util.spec_from_file_location("browser_plugin", plugin_path)
    browser_plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(browser_plugin_module)
    MCPBrowserPlugin = browser_plugin_module.MCPBrowserPlugin
    
    temp_path, csv_file, report_file = test_data_files
    
    # Change to temp directory for plugin to find files
    import os
    original_cwd = os.getcwd()
    os.chdir(temp_path)
    
    try:
        plugin = MCPBrowserPlugin(
            servers_data_file=csv_file,
            install_reports_pattern="mcp_install_report_*.json"
        )
        yield plugin
    finally:
        os.chdir(original_cwd)


class TestMCPBrowserPlugin:
    """Test suite for MCPBrowserPlugin."""

    @pytest.mark.asyncio
    async def test_plugin_initialization(self, plugin_instance):
        """Test plugin initialization and inheritance."""
        plugin = plugin_instance
        
        # Test basic properties
        assert plugin.platform_name == "MCP Server Browser"
        assert plugin.platform_id == "mcp-browser-plugin"
        assert plugin.priority == 10
        assert plugin.provides_servers is True
        assert plugin.provides_discovery is True
        
        # Test inheritance validation
        from haive.dataflow.platform.models import (
            PluginPlatform, 
            BasePlatform,
            validate_platform_inheritance
        )
        
        assert isinstance(plugin, PluginPlatform)
        assert isinstance(plugin, BasePlatform)
        
        inheritance = validate_platform_inheritance(plugin)
        assert inheritance['is_plugin_platform'] is True
        assert inheritance['is_base_platform'] is True
        assert inheritance['platform_type'] == 'MCPBrowserPlugin'
        
        # Test initialization
        await plugin.initialize()
        assert plugin.status.value == "active"

    @pytest.mark.asyncio
    async def test_server_loading(self, plugin_instance):
        """Test loading servers from real data."""
        plugin = plugin_instance
        await plugin.initialize()
        
        # Load servers
        servers = plugin.get_servers()
        assert len(servers) == 5
        
        # Test first server details
        first_server = servers[0]
        assert first_server.server_name == "server-filesystem"
        assert first_server.description == "File system operations for MCP"
        assert first_server.language == "TypeScript"
        assert first_server.stars == 245
        
        # Test inheritance validation for server
        from haive.dataflow.platform.models import validate_server_inheritance
        server_inheritance = validate_server_inheritance(first_server)
        assert server_inheritance['is_base_server'] is True
        assert server_inheritance['is_mcp_server'] is True
        assert server_inheritance['is_downloaded_server'] is True
        assert server_inheritance['inheritance_depth'] == 3
        
        # Test download summary structure
        download_summary = first_server.get_download_summary()
        assert 'download_info' in download_summary
        assert 'source_data' in download_summary
        assert 'repository_info' in download_summary
        assert download_summary['download_info']['bulk_install_session'] == "bulk-install-20250119-143022"

    def test_server_filtering(self, plugin_instance):
        """Test server filtering methods."""
        plugin = plugin_instance
        
        # Test language filtering
        python_servers = plugin.get_servers_by_language("Python")
        assert len(python_servers) == 2
        assert all(s.language == "Python" for s in python_servers)
        
        # Test star filtering
        popular_servers = plugin.get_servers_by_stars(min_stars=150)
        assert len(popular_servers) == 4
        assert all(s.stars >= 150 for s in popular_servers)
        
        # Test specific server lookup
        fs_server = plugin.get_server_by_name("server-filesystem")
        assert fs_server is not None
        assert fs_server.server_name == "server-filesystem"
        assert fs_server.repository_url == "https://github.com/modelcontextprotocol/server-filesystem"

    def test_plugin_statistics(self, plugin_instance):
        """Test plugin statistics generation."""
        plugin = plugin_instance
        stats = plugin.get_plugin_stats()
        
        # Test plugin info
        assert stats['plugin_info']['platform_id'] == "mcp-browser-plugin"
        assert stats['plugin_info']['platform_name'] == "MCP Server Browser"
        
        # Test server stats
        assert stats['server_stats']['total_servers'] == 5
        assert 'TypeScript' in stats['server_stats']['languages']
        assert 'Python' in stats['server_stats']['languages']
        assert stats['server_stats']['total_stars'] == 980
        assert stats['server_stats']['average_stars'] == 196.0
        
        # Test inheritance info
        assert stats['inheritance_info']['is_plugin_platform'] is True
        assert stats['inheritance_info']['provides_servers'] is True
        assert stats['inheritance_info']['plugin_priority'] == 10

    def test_caching_behavior(self, plugin_instance):
        """Test caching mechanism."""
        plugin = plugin_instance
        
        # First call - should load from data
        servers1 = plugin.get_servers()
        assert plugin.cached_servers is not None
        assert plugin.cache_timestamp is not None
        assert plugin._is_cache_valid() is True
        
        # Second call - should use cache
        servers2 = plugin.get_servers()
        assert len(servers1) == len(servers2)
        
        # Clear cache and test reload
        plugin.cached_servers = None
        plugin.cache_timestamp = None
        assert plugin._is_cache_valid() is False

    def test_fastapi_routes_setup(self, plugin_instance):
        """Test FastAPI routes registration."""
        plugin = plugin_instance
        
        # Create mock FastAPI app
        class MockFastAPI:
            def __init__(self):
                self.routers = []
                
            def include_router(self, router):
                self.routers.append(router)
        
        mock_app = MockFastAPI()
        
        # Register routes
        plugin.register_routes(mock_app)
        
        assert plugin.router is not None
        assert plugin.router.prefix == "/mcp"
        assert len(mock_app.routers) == 1
        assert plugin.router.tags == ['MCP Browser']

    @pytest.mark.asyncio
    async def test_plugin_cleanup(self, plugin_instance):
        """Test plugin cleanup."""
        plugin = plugin_instance
        
        # Initialize and load data
        await plugin.initialize()
        plugin.get_servers()  # Load servers to create cache
        
        assert plugin.cached_servers is not None
        assert plugin.cache_timestamp is not None
        
        # Perform cleanup
        await plugin.cleanup()
        
        assert plugin.cached_servers is None
        assert plugin.cache_timestamp is None

    def test_cache_ttl_configuration(self, plugin_instance):
        """Test cache TTL configuration."""
        plugin = plugin_instance
        
        # Test default TTL
        assert plugin.cache_ttl_seconds == 300  # 5 minutes
        
        # Test TTL validation (should be between 60 and 3600 seconds)
        plugin.cache_ttl_seconds = 120
        assert plugin.cache_ttl_seconds == 120

    def test_data_file_validation(self, plugin_instance):
        """Test data file validation."""
        plugin = plugin_instance
        
        # Test with existing file
        assert plugin.servers_data_file.exists()
        
        # Test with non-existent file path
        plugin.servers_data_file = Path("non_existent.csv")
        # Should handle gracefully during server loading
        servers = plugin.get_servers()
        assert isinstance(servers, list)  # Should return empty list, not error


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])