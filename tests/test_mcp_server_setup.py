#!/usr/bin/env python3
"""Test MCP server setup and management functionality."""

import asyncio
import pytest
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from haive.mcp.servers.mcp_server_manager import MCPServerManager
from haive.mcp.servers.simple_server import SimpleServer
from haive.mcp.servers.filesystem_server import FilesystemServer
from haive.mcp.servers.time_server import TimeServer


class TestMCPServerSetup:
    """Test MCP server setup and management."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self):
        """Create MCPServerManager instance."""
        return MCPServerManager()
    
    def test_server_manager_creation(self, manager):
        """Test server manager can be created."""
        assert manager is not None
        assert hasattr(manager, 'servers')
        assert hasattr(manager, 'running_servers')
    
    def test_available_servers(self, manager):
        """Test listing available servers."""
        available = manager.get_available_servers()
        assert isinstance(available, list)
        assert "filesystem" in available
        assert "time" in available
        assert "simple" in available
    
    def test_server_status_when_none_running(self, manager):
        """Test server status when no servers are running."""
        status = manager.get_status()
        assert isinstance(status, dict)
        for server_name, server_status in status.items():
            assert server_status['running'] is False
            assert server_status['pid'] is None
    
    @pytest.mark.asyncio
    async def test_start_simple_server(self, manager):
        """Test starting the simple server."""
        # Start server
        success = manager.start_server("simple")
        assert success is True
        
        # Check status
        status = manager.get_status()
        assert status['simple']['running'] is True
        assert status['simple']['pid'] is not None
        
        # Stop server
        manager.stop_server("simple")
        
    @pytest.mark.asyncio
    async def test_start_filesystem_server(self, manager):
        """Test starting the filesystem server."""
        success = manager.start_server("filesystem")
        assert success is True
        
        status = manager.get_status()
        assert status['filesystem']['running'] is True
        
        manager.stop_server("filesystem")
    
    def test_start_invalid_server(self, manager):
        """Test starting an invalid server."""
        success = manager.start_server("nonexistent")
        assert success is False
    
    def test_stop_server_not_running(self, manager):
        """Test stopping a server that's not running."""
        success = manager.stop_server("simple")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_server_lifecycle(self, manager):
        """Test full server lifecycle - start, check, stop."""
        # Start
        assert manager.start_server("time") is True
        
        # Check running
        status = manager.get_status()
        assert status['time']['running'] is True
        time_pid = status['time']['pid']
        assert time_pid is not None
        
        # Stop
        assert manager.stop_server("time") is True
        
        # Verify stopped
        status = manager.get_status()
        assert status['time']['running'] is False
        assert status['time']['pid'] is None
    
    def test_stop_all_servers(self, manager):
        """Test stopping all servers."""
        # Start multiple servers
        manager.start_server("simple")
        manager.start_server("time")
        
        # Stop all
        manager.stop_all_servers()
        
        # Verify all stopped
        status = manager.get_status()
        for server_status in status.values():
            assert server_status['running'] is False
    
    def test_non_interactive_mode(self, manager):
        """Test non-interactive mode."""
        # Should not raise any errors
        manager.run_non_interactive()
        
        # Default servers should be started
        status = manager.get_status()
        assert any(s['running'] for s in status.values())
        
        # Clean up
        manager.stop_all_servers()


class TestSimpleServer:
    """Test the simple MCP server."""
    
    def test_simple_server_creation(self):
        """Test creating a simple server."""
        server = SimpleServer()
        assert server is not None
        assert hasattr(server, 'handle_request')
    
    @pytest.mark.asyncio
    async def test_simple_server_echo(self):
        """Test simple server echo functionality."""
        server = SimpleServer()
        
        # Mock request
        request = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"message": "Hello, MCP!"},
            "id": 1
        }
        
        response = await server.handle_request(request)
        assert response is not None
        assert response.get("result") == "Echo: Hello, MCP!"


class TestTimeServer:
    """Test the time MCP server."""
    
    def test_time_server_creation(self):
        """Test creating a time server."""
        server = TimeServer()
        assert server is not None
    
    @pytest.mark.asyncio
    async def test_time_server_current_time(self):
        """Test time server current time functionality."""
        server = TimeServer()
        
        request = {
            "jsonrpc": "2.0",
            "method": "get_current_time",
            "params": {},
            "id": 1
        }
        
        response = await server.handle_request(request)
        assert response is not None
        assert "result" in response
        assert "timestamp" in response["result"]
        assert "formatted" in response["result"]


class TestFilesystemServer:
    """Test the filesystem MCP server."""
    
    @pytest.fixture
    def fs_server(self, temp_dir):
        """Create filesystem server with temp directory."""
        return FilesystemServer(root_path=temp_dir)
    
    def test_filesystem_server_creation(self, fs_server):
        """Test creating a filesystem server."""
        assert fs_server is not None
        assert hasattr(fs_server, 'root_path')
    
    @pytest.mark.asyncio
    async def test_filesystem_list_files(self, fs_server, temp_dir):
        """Test filesystem server list files functionality."""
        # Create test files
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, MCP!")
        
        request = {
            "jsonrpc": "2.0",
            "method": "list_files",
            "params": {"path": "."},
            "id": 1
        }
        
        response = await fs_server.handle_request(request)
        assert response is not None
        assert "result" in response
        assert "files" in response["result"]
        assert any(f["name"] == "test.txt" for f in response["result"]["files"])
    
    @pytest.mark.asyncio
    async def test_filesystem_read_file(self, fs_server, temp_dir):
        """Test filesystem server read file functionality."""
        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_content = "Hello, MCP filesystem!"
        test_file.write_text(test_content)
        
        request = {
            "jsonrpc": "2.0",
            "method": "read_file",
            "params": {"path": "test.txt"},
            "id": 1
        }
        
        response = await fs_server.handle_request(request)
        assert response is not None
        assert response.get("result", {}).get("content") == test_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])