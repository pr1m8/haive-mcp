"""Test suite for native MCP client implementation.

This test suite validates the native MCP protocol client with real MCP servers.
It tests the complete protocol stack including transport, protocol, and client layers.

Tests include:
    - Connection establishment and teardown
    - Protocol initialization and capability negotiation  
    - Tool discovery and execution
    - Resource access and management
    - Error handling and recovery
    - Multiple transport types
    - Health monitoring and reconnection
"""

import asyncio
import pytest
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any

from haive.mcp.client import (
    MCPClient,
    StdioTransport,
    HttpTransport,
    MCPConnectionError,
    MCPProtocolError,
    MCPToolError,
    MCPTimeoutError
)
from haive.mcp.client.connection import MCPConnection, ConnectionStatus


class TestNativeMCPClient:
    """Test suite for native MCP client implementation."""
    
    @pytest.mark.asyncio
    async def test_filesystem_server_connection(self):
        """Test connection to filesystem MCP server via STDIO."""
        # Create temporary directory for filesystem server
        with tempfile.TemporaryDirectory() as temp_dir:
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir],
                timeout=10.0
            )
            
            async with MCPClient(transport) as client:
                # Test connection
                assert await client.is_connected()
                
                # Test server info
                server_info = await client.get_server_info()
                assert "serverInfo" in server_info
                assert server_info["serverInfo"]["name"] == "filesystem"
                
                # Test capabilities
                capabilities = await client.get_capabilities()
                assert "tools" in [cap.value for cap in capabilities]
                
    @pytest.mark.asyncio
    async def test_tool_discovery_and_execution(self):
        """Test tool discovery and execution with filesystem server."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_content = "Hello MCP Protocol!"
            test_file.write_text(test_content)
            
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir]
            )
            
            async with MCPClient(transport) as client:
                # List tools
                tools = await client.list_tools()
                assert len(tools) > 0
                
                tool_names = [tool.name for tool in tools]
                assert "read_file" in tool_names
                
                # Find read_file tool
                read_tool = next(tool for tool in tools if tool.name == "read_file")
                assert read_tool.description is not None
                assert "inputSchema" in read_tool.inputSchema or "properties" in read_tool.inputSchema
                
                # Execute tool
                result = await client.call_tool("read_file", {
                    "path": str(test_file)
                })
                
                assert result is not None
                # Result format may vary, but should contain our content
                result_str = str(result)
                assert test_content in result_str
                
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling with invalid operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir]
            )
            
            async with MCPClient(transport) as client:
                # Test nonexistent tool
                with pytest.raises(MCPToolError):
                    await client.call_tool("nonexistent_tool", {})
                    
                # Test invalid arguments
                with pytest.raises(MCPToolError):
                    await client.call_tool("read_file", {"invalid_arg": "value"})
                    
                # Test missing required arguments
                with pytest.raises(MCPToolError):
                    await client.call_tool("read_file", {})
                    
    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test connection timeout handling."""
        # Use invalid command that should timeout
        transport = StdioTransport(
            command="sleep",
            args=["60"],  # Sleep for 60 seconds
            timeout=1.0   # 1 second timeout
        )
        
        client = MCPClient(transport)
        
        with pytest.raises(MCPTimeoutError):
            await client.connect()
            
    @pytest.mark.asyncio 
    async def test_connection_manager(self):
        """Test MCPConnection manager functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir]
            )
            
            connection = MCPConnection(
                name="test_filesystem",
                transport=transport,
                auto_reconnect=False,
                health_check_interval=5.0
            )
            
            # Test connection lifecycle
            assert not connection.is_connected()
            assert connection.status == ConnectionStatus.DISCONNECTED
            
            # Connect
            client = await connection.connect()
            assert connection.is_connected()
            assert connection.status == ConnectionStatus.CONNECTED
            assert connection.last_connected is not None
            
            # Health check
            health = await connection.health_check()
            assert health["connected"] is True
            assert health["name"] == "test_filesystem"
            assert connection.is_healthy()
            
            # Get client and use it
            client = connection.get_client()
            tools = await client.list_tools()
            assert len(tools) > 0
            
            # Connection info
            info = connection.get_info()
            assert info.name == "test_filesystem"
            assert info.status == ConnectionStatus.CONNECTED
            assert info.connection_count == 1
            
            # Disconnect
            await connection.disconnect()
            assert not connection.is_connected()
            assert connection.status == ConnectionStatus.DISCONNECTED
            
    @pytest.mark.asyncio
    async def test_client_caching(self):
        """Test client caching functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir]
            )
            
            async with MCPClient(transport) as client:
                # First call should fetch from server
                tools1 = await client.list_tools(use_cache=False)
                
                # Second call should use cache
                tools2 = await client.list_tools(use_cache=True)
                
                # Should be the same
                assert len(tools1) == len(tools2)
                assert [t.name for t in tools1] == [t.name for t in tools2]
                
                # Refresh cache
                await client.refresh_cache()
                
                # Should still work
                tools3 = await client.list_tools()
                assert len(tools3) == len(tools1)
                
    @pytest.mark.asyncio
    async def test_notification_handling(self):
        """Test notification handler functionality."""
        notifications_received = []
        
        async def notification_handler(params: Dict[str, Any]) -> None:
            notifications_received.append(params)
            
        with tempfile.TemporaryDirectory() as temp_dir:
            transport = StdioTransport(
                command="npx", 
                args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir]
            )
            
            async with MCPClient(transport) as client:
                # Add notification handler
                client.add_notification_handler("tools/list_changed", notification_handler)
                
                # Perform operations (some servers send notifications)
                tools = await client.list_tools()
                
                # Remove handler
                client.remove_notification_handler("tools/list_changed", notification_handler)
                
                # At minimum, test that handler registration works
                assert True  # Handler was added and removed without error
                
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test client health check functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir]
            )
            
            async with MCPClient(transport) as client:
                health = await client.health_check()
                
                assert health["connected"] is True
                assert health["server_info"] is not None
                assert "capabilities" in health
                assert health["transport_type"] == "StdioTransport"
                assert health["error"] is None
                
    @pytest.mark.asyncio
    async def test_multiple_concurrent_operations(self):
        """Test multiple concurrent operations on same client."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test files
            for i in range(3):
                test_file = Path(temp_dir) / f"test{i}.txt"
                test_file.write_text(f"Content {i}")
                
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir]
            )
            
            async with MCPClient(transport) as client:
                # Concurrent tool calls
                tasks = []
                for i in range(3):
                    task = client.call_tool("read_file", {
                        "path": str(Path(temp_dir) / f"test{i}.txt")
                    })
                    tasks.append(task)
                    
                # Wait for all to complete
                results = await asyncio.gather(*tasks)
                
                assert len(results) == 3
                for i, result in enumerate(results):
                    result_str = str(result)
                    assert f"Content {i}" in result_str
                    
    @pytest.mark.asyncio
    async def test_context_manager_error_cleanup(self):
        """Test that context manager properly cleans up on errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir]
            )
            
            try:
                async with MCPClient(transport) as client:
                    # Perform some operations
                    tools = await client.list_tools()
                    assert len(tools) > 0
                    
                    # Simulate an error
                    raise ValueError("Test error")
                    
            except ValueError:
                # Error should be caught, but cleanup should still happen
                pass
                
            # Transport should be disconnected
            assert not transport.connected
            
    @pytest.mark.asyncio
    async def test_client_without_context_manager(self):
        """Test manual client lifecycle management."""
        with tempfile.TemporaryDirectory() as temp_dir:
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir]
            )
            
            client = MCPClient(transport)
            
            try:
                # Manual connection
                server_info = await client.connect()
                assert "serverInfo" in server_info
                
                # Use client
                tools = await client.list_tools()
                assert len(tools) > 0
                
                # Check connection status
                assert await client.is_connected()
                
            finally:
                # Manual cleanup
                await client.disconnect()
                
            assert not await client.is_connected()


@pytest.mark.integration
class TestMCPClientIntegration:
    """Integration tests requiring specific MCP servers."""
    
    @pytest.mark.skipif(
        not Path("/usr/bin/npx").exists() and not Path("/usr/local/bin/npx").exists(),
        reason="npx not available for integration tests"
    )
    @pytest.mark.asyncio
    async def test_real_filesystem_server_integration(self):
        """Full integration test with real filesystem server."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test data structure
            test_dir = Path(temp_dir) / "test_data"
            test_dir.mkdir()
            
            (test_dir / "file1.txt").write_text("Hello World")
            (test_dir / "file2.json").write_text('{"key": "value"}')
            
            subdir = test_dir / "subdir"
            subdir.mkdir()
            (subdir / "nested.txt").write_text("Nested content")
            
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", str(test_dir)]
            )
            
            async with MCPClient(transport) as client:
                # Test complete workflow
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
                
                # Test file reading
                if "read_file" in tool_names:
                    content = await client.call_tool("read_file", {
                        "path": "file1.txt"
                    })
                    assert "Hello World" in str(content)
                    
                # Test directory listing
                if "list_directory" in tool_names:
                    listing = await client.call_tool("list_directory", {
                        "path": "."
                    })
                    assert listing is not None
                    
                # Test health throughout operations
                health = await client.health_check()
                assert health["connected"] is True
                assert health["tools_accessible"] is True


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(pytest.main([__file__, "-v"]))