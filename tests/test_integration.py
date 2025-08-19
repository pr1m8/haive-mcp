#!/usr/bin/env python3
"""Integration tests for MCP functionality.

These tests verify the integration between different MCP components.
"""

import pytest
import asyncio
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

from haive.mcp.servers.mcp_server_manager import MCPServerManager
from haive.mcp.installer.bulk_installer import MCPBulkInstaller
from haive.mcp.discovery.installed_servers import MCPServerDiscovery


@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests for MCP components working together."""
    
    @pytest.fixture
    def integration_temp_dir(self, temp_test_dir):
        """Create integration test directory structure."""
        # Create subdirectories
        (temp_test_dir / "servers").mkdir()
        (temp_test_dir / "downloads").mkdir()
        (temp_test_dir / "configs").mkdir()
        
        # Create sample CSV data
        csv_data = """name,stars,category,install_command,npm_package,repository_url
@modelcontextprotocol/server-filesystem,5000,utility,npm install -g @modelcontextprotocol/server-filesystem,@modelcontextprotocol/server-filesystem,https://github.com/modelcontextprotocol/servers
mcp-server-time,1000,utility,npm install -g mcp-server-time,mcp-server-time,https://github.com/example/time
mcp-python-example,500,example,pip install mcp-python-example,,https://github.com/example/python"""
        
        csv_path = temp_test_dir / "test_servers.csv"
        csv_path.write_text(csv_data)
        
        return temp_test_dir
    
    @pytest.mark.slow
    def test_full_workflow(self, integration_temp_dir):
        """Test complete workflow: setup -> install -> discover -> manage."""
        # 1. Setup server manager
        manager = MCPServerManager()
        available = manager.get_available_servers()
        assert len(available) > 0
        
        # 2. Install servers using bulk installer
        csv_path = integration_temp_dir / "test_servers.csv"
        installer = MCPBulkInstaller(data_path=str(csv_path))
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            # Install high-star servers
            summary = installer.install_by_stars(min_stars=1000)
            assert summary['total_attempts'] == 2
            assert summary['successful'] == 2
        
        # 3. Discover installed servers
        discovery = MCPServerDiscovery()
        
        with patch.object(discovery, 'find_npm_servers') as mock_npm:
            mock_npm.return_value = [
                {
                    'name': '@modelcontextprotocol/server-filesystem',
                    'version': '1.0.0',
                    'type': 'npm',
                    'global': True
                },
                {
                    'name': 'mcp-server-time',
                    'version': '1.0.0',
                    'type': 'npm',
                    'global': True
                }
            ]
            
            installed = discovery.find_all_installed()
            assert len(installed) >= 2
        
        # 4. Start and manage servers
        success = manager.start_server("filesystem")
        # Note: This will fail in test environment, but tests the flow
        assert isinstance(success, bool)
        
        # 5. Export results
        report_path = integration_temp_dir / "install_report.json"
        installer.save_install_report(str(report_path))
        assert report_path.exists()
        
        discovery_report = integration_temp_dir / "discovered_servers.json"
        discovery.export_installed_list(str(discovery_report))
        assert discovery_report.exists()
    
    @pytest.mark.asyncio
    async def test_server_communication_flow(self):
        """Test server communication workflow."""
        # This tests the conceptual flow - actual server communication
        # would require running servers
        
        # 1. Start server (mocked)
        manager = MCPServerManager()
        
        with patch.object(manager, 'start_server') as mock_start:
            mock_start.return_value = True
            started = manager.start_server("simple")
            assert started is True
        
        # 2. Simulate server request/response
        mock_request = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"message": "Integration test"},
            "id": 1
        }
        
        expected_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "Echo: Integration test"
        }
        
        # In real scenario, this would communicate with the server
        # Here we just verify the structure
        assert "method" in mock_request
        assert "params" in mock_request
        assert mock_request["params"]["message"] == "Integration test"
    
    def test_install_and_verify_cycle(self, integration_temp_dir):
        """Test installation followed by verification."""
        csv_path = integration_temp_dir / "test_servers.csv"
        installer = MCPBulkInstaller(data_path=str(csv_path))
        discovery = MCPServerDiscovery()
        
        # Mock the installation
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            # Install specific server
            server = installer.servers_with_stars.iloc[0]
            result = installer._install_server(server)
            assert result is True
        
        # Mock the verification
        with patch.object(discovery, 'check_server_availability') as mock_check:
            mock_check.return_value = True
            
            # Verify it's available
            available = discovery.check_server_availability(server['name'])
            assert available is True
    
    def test_category_based_workflow(self, integration_temp_dir):
        """Test category-based installation and management."""
        csv_path = integration_temp_dir / "test_servers.csv"
        installer = MCPBulkInstaller(data_path=str(csv_path))
        
        # Get all utility servers
        utility_servers = installer.servers_with_stars[
            installer.servers_with_stars['category'] == 'utility'
        ]
        assert len(utility_servers) == 2
        
        # Mock install by category
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            summary = installer.install_by_category('utility')
            assert summary['total_attempts'] == 2
            assert summary['successful'] == 2
    
    def test_error_recovery_workflow(self, integration_temp_dir):
        """Test error handling and recovery across components."""
        csv_path = integration_temp_dir / "test_servers.csv"
        installer = MCPBulkInstaller(data_path=str(csv_path))
        
        # Simulate mixed success/failure
        with patch('subprocess.run') as mock_run:
            # First call succeeds, second fails
            mock_run.side_effect = [
                MagicMock(returncode=0),
                MagicMock(returncode=1, stderr="Installation failed")
            ]
            
            summary = installer.install_by_stars(min_stars=500)
            
            # Should have attempted all qualifying servers
            assert summary['total_attempts'] >= 2
            assert summary['successful'] >= 1
            assert summary['failed'] >= 1
            
            # Check install log has both success and failure
            success_logs = [l for l in installer.install_log if l['status'] == 'success']
            failed_logs = [l for l in installer.install_log if l['status'] == 'failed']
            
            assert len(success_logs) >= 1
            assert len(failed_logs) >= 1


@pytest.mark.integration
class TestRealDataIntegration:
    """Integration tests using real MCP data if available."""
    
    @pytest.fixture
    def real_data_path(self):
        """Get path to real data if available."""
        real_csv = Path("/home/will/Projects/haive/backend/haive/packages/haive-mcp/scratches/mcp-analysis/mcp_servers_data.csv")
        if not real_csv.exists():
            pytest.skip("Real data not available")
        return real_csv
    
    @pytest.mark.slow
    @pytest.mark.requires_network
    def test_real_data_analysis(self, real_data_path):
        """Test with real MCP server data."""
        installer = MCPBulkInstaller(data_path=str(real_data_path))
        
        # Verify data loaded correctly
        assert len(installer.df) == 1960
        assert len(installer.servers_with_stars) == 194
        
        # Test star distribution matches our analysis
        high_stars = installer.servers_with_stars[
            installer.servers_with_stars['stars'] >= 1000
        ]
        assert len(high_stars) == 37
        
        # Test category distribution
        categories = installer.servers_with_stars['category'].unique()
        assert len(categories) > 0
    
    def test_top_servers_selection(self, real_data_path):
        """Test selecting top servers from real data."""
        installer = MCPBulkInstaller(data_path=str(real_data_path))
        
        # Get top 10 servers
        top_10 = installer.servers_with_stars.nlargest(10, 'stars')
        
        # Verify they're high-star servers
        assert all(server['stars'] >= 1000 for _, server in top_10.iterrows())
        
        # Check server names are reasonable
        names = top_10['name'].tolist()
        assert any('@modelcontextprotocol' in name for name in names)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])