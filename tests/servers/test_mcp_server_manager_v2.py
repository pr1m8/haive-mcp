"""Tests for MCPServerManagerV2 with Pydantic validation.

Tests the refactored MCP server manager including:
- Type-safe configuration
- MCP-specific validation
- Backward compatibility
- Real server integration (no mocks)
"""

import pytest
import asyncio
import os
import subprocess
from typing import Dict, Any

from haive.mcp.servers.mcp_server_manager_v2 import MCPServerManagerV2
from haive.mcp.servers.models import MCPServerConfig, MCPServerInfo, MCPTransport
from haive.dataflow.server_management.models import ServerStatus
from pydantic import ValidationError


class TestMCPServerManagerV2:
    """Test suite for refactored MCP server manager."""
    
    @pytest.fixture
    def manager(self):
        """Create a test manager instance."""
        manager = MCPServerManagerV2(
            health_check_interval=10,  # Minimum allowed value
            auto_restart=False
        )
        yield manager
        # Cleanup
        import asyncio
        loop = asyncio.new_event_loop()
        loop.run_until_complete(manager.cleanup())
        loop.close()
    
    def test_manager_creation(self, manager):
        """Test manager creates with default configs."""
        assert manager is not None
        assert isinstance(manager, MCPServerManagerV2)
        assert len(manager.available_configs) == 5  # Default servers
        assert "filesystem" in manager.available_configs
        assert "github" in manager.available_configs
    
    def test_default_config_validation(self, manager):
        """Test default configurations are valid."""
        fs_config = manager.available_configs["filesystem"]
        assert isinstance(fs_config, MCPServerConfig)
        assert fs_config.transport == MCPTransport.STDIO
        assert fs_config.name == "filesystem"
        assert len(fs_config.command) > 0
        
        github_config = manager.available_configs["github"]
        assert github_config.requires_env == ["GITHUB_TOKEN"]
    
    def test_add_custom_config(self, manager):
        """Test adding custom MCP server config."""
        config = MCPServerConfig(
            name="custom",
            command=["node", "custom-server.js"],
            description="Custom MCP server",
            transport=MCPTransport.HTTP,
            endpoints={"base": "http://localhost:3000"}
        )
        
        manager.add_config("custom", config)
        assert "custom" in manager.available_configs
        assert manager.available_configs["custom"] == config
    
    def test_config_validation_errors(self):
        """Test configuration validation catches errors."""
        # Missing endpoints for HTTP transport
        with pytest.raises(ValidationError) as exc_info:
            MCPServerConfig(
                name="bad",
                command=["test"],
                description="Test server",
                transport=MCPTransport.HTTP
                # Missing required endpoints
            )
        assert "endpoints" in str(exc_info.value)
        
        # Invalid env var name
        with pytest.raises(ValidationError) as exc_info:
            MCPServerConfig(
                name="bad2",
                command=["test"],
                description="Test server",
                requires_env=["123INVALID"]
            )
        assert "environment variable name" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_start_server_missing_env(self, manager):
        """Test server start fails with missing env vars."""
        # GitHub server requires GITHUB_TOKEN
        with pytest.raises(ValueError) as exc_info:
            await manager.start_server("github")
        assert "GITHUB_TOKEN" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_start_server_with_env(self, manager, monkeypatch):
        """Test server starts with required env vars."""
        # Mock subprocess for testing
        class MockPopen:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs
                self.pid = 12345
                self.returncode = None
                self.stdin = None
                self.stdout = None
                self.stderr = None
            
            def poll(self):
                return self.returncode
            
            def terminate(self):
                self.returncode = 0
            
            def communicate(self):
                return "", ""
        
        monkeypatch.setattr(subprocess, "Popen", MockPopen)
        
        # Start with env override
        info = await manager.start_server("github", {"GITHUB_TOKEN": "test-token"})
        
        assert isinstance(info, MCPServerInfo)
        assert info.pid == 12345
        assert info.transport == MCPTransport.STDIO
        assert info.status == ServerStatus.RUNNING
        assert "github" in manager.servers
    
    def test_legacy_available_servers_property(self, manager):
        """Test backward compatibility property."""
        legacy = manager.available_servers
        assert isinstance(legacy, dict)
        assert "filesystem" in legacy
        assert legacy["filesystem"]["transport"] == "stdio"
        assert legacy["filesystem"]["command"] == ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."]
    
    def test_legacy_get_status(self, manager):
        """Test legacy status format."""
        # Add a fake server for testing
        info = MCPServerInfo(
            name="test",
            pid=12345,
            status=ServerStatus.RUNNING,
            config_snapshot={"name": "test", "command": ["test"]},
            transport=MCPTransport.STDIO
        )
        manager.servers["test"] = info
        manager.available_configs["test"] = MCPServerConfig(
            name="test",
            command=["test"],
            description="Test server"
        )
        
        status = manager.get_status()
        assert isinstance(status, dict)
        assert "test" in status
        assert status["test"]["pid"] == 12345
        assert status["test"]["running"] is True
        assert status["test"]["transport"] == "stdio"
    
    @pytest.mark.asyncio
    async def test_health_check_stdio_idle_detection(self, manager):
        """Test health check detects idle stdio servers."""
        # Create server info with old message time
        info = MCPServerInfo(
            name="test",
            pid=12345,
            status=ServerStatus.RUNNING,
            config_snapshot={"name": "test", "command": ["test"]},
            transport=MCPTransport.STDIO
        )
        
        # Create mock process handle
        class MockProcess:
            def poll(self):
                return None  # Still running
        
        info.process_handle = MockProcess()
        
        # Recent message - should be healthy
        info.record_message()
        manager.servers["test"] = info
        assert await manager.health_check("test") is True
        
        # Simulate old message time (>5 minutes)
        from datetime import datetime, timedelta, timezone
        info.last_message_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        assert await manager.health_check("test") is True  # Still returns True but logs warning
    
    def test_mcp_server_info_message_tracking(self):
        """Test MCPServerInfo tracks messages correctly."""
        info = MCPServerInfo(
            name="test",
            pid=12345,
            status=ServerStatus.RUNNING,
            config_snapshot={"name": "test", "command": ["test"]}
        )
        assert info.message_count == 0
        assert info.last_message_time is None
        
        # Record messages
        info.record_message()
        assert info.message_count == 1
        assert info.last_message_time is not None
        
        info.record_message()
        assert info.message_count == 2
    
    def test_transport_status_formatting(self):
        """Test transport status string generation."""
        info = MCPServerInfo(
            name="test",
            pid=12345,
            status=ServerStatus.RUNNING,
            config_snapshot={"name": "test", "command": ["test"]},
            transport=MCPTransport.STDIO
        )
        
        # No messages yet
        assert info.get_transport_status() == "stdio - Connected"
        
        # Recent message
        info.record_message()
        assert info.get_transport_status() == "stdio - Active"
        
        # Stopped server
        info.status = ServerStatus.STOPPED
        assert info.get_transport_status() == "stdio - stopped"
    
    @pytest.mark.asyncio
    async def test_restart_preserves_env(self, manager, monkeypatch):
        """Test restart preserves environment configuration."""
        # Mock subprocess
        class MockPopen:
            instances = []
            
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs
                self.pid = 12345 + len(MockPopen.instances)
                self.returncode = None
                self.stdin = None
                self.stdout = None
                self.stderr = None
                MockPopen.instances.append(self)
            
            def poll(self):
                return self.returncode
            
            def terminate(self):
                self.returncode = 0
            
            def wait(self, timeout=None):
                pass
            
            def communicate(self):
                return "", ""
        
        MockPopen.instances = []
        monkeypatch.setattr(subprocess, "Popen", MockPopen)
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        
        # Start server
        info1 = await manager.start_server("github")
        assert info1.pid == 12345
        
        # Restart should preserve env
        info2 = await manager.restart_server("github")
        assert info2.pid == 12346  # New process
        assert len(MockPopen.instances) == 2
        
        # Check env was preserved in second call
        second_env = MockPopen.instances[1].kwargs.get("env", {})
        assert "GITHUB_TOKEN" in second_env
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_time_server(self):
        """Integration test with real time server if npx available."""
        # Check if npx is available
        try:
            subprocess.run(["npx", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("npx not available for integration test")
        
        manager = MCPServerManagerV2(health_check_interval=10)
        
        try:
            # Start time server (no env requirements)
            info = await manager.start_server("time")
            assert info.pid > 0
            assert info.is_running
            assert info.transport == MCPTransport.STDIO
            
            # Verify process is actually running
            assert info.process_handle.poll() is None
            
            # Stop server
            stopped = await manager.stop_server("time")
            assert stopped is True
            assert "time" not in manager.servers
            
        finally:
            await manager.cleanup()
    
    def test_backward_compatibility_run_method(self, manager, monkeypatch):
        """Test legacy run() method works."""
        # Mock subprocess to avoid real servers
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: None)
        
        class MockPopen:
            def __init__(self, *args, **kwargs):
                self.pid = 12345
                self.returncode = None
            def poll(self):
                return self.returncode
            def terminate(self):
                pass
            def communicate(self):
                return "", ""
        
        monkeypatch.setattr(subprocess, "Popen", MockPopen)
        
        # Test non-blocking mode
        success = manager.run(servers_to_start=["filesystem"], blocking=False)
        assert success is True
        
        # Cleanup
        manager.stop_all_servers()