#!/usr/bin/env python3
"""Test bulk download functionality for MCP servers."""

import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock, AsyncMock

from haive.mcp.installer.bulk_installer import MCPBulkInstaller


class TestBulkDownload:
    """Test bulk download and installation of MCP servers."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_csv_data(self, temp_dir):
        """Create sample CSV data for testing."""
        data = pd.DataFrame({
            'name': [
                'server-high-stars',
                'server-medium-stars',
                'server-low-stars',
                'server-no-stars',
                'ai-ml-server',
                'database-server'
            ],
            'stars': [5000, 500, 50, 0, 1000, 800],
            'category': ['utility', 'utility', 'utility', 'utility', 'ai_ml', 'database'],
            'install_command': [
                'npm install -g server-high',
                'npm install -g server-medium',
                'npm install -g server-low',
                'npm install -g server-no',
                'npm install -g ai-ml',
                'npm install -g database'
            ],
            'npm_package': [
                'server-high',
                'server-medium',
                'server-low',
                'server-no',
                'ai-ml-server',
                'database-server'
            ],
            'repository_url': [
                'https://github.com/org/server-high',
                'https://github.com/org/server-medium',
                'https://github.com/org/server-low',
                'https://github.com/org/server-no',
                'https://github.com/org/ai-ml',
                'https://github.com/org/database'
            ]
        })
        
        csv_path = Path(temp_dir) / "test_mcp_servers.csv"
        data.to_csv(csv_path, index=False)
        return csv_path
    
    @pytest.fixture
    def bulk_installer(self, sample_csv_data):
        """Create bulk installer with test data."""
        return MCPBulkInstaller(data_path=str(sample_csv_data))
    
    def test_bulk_installer_creation(self, bulk_installer):
        """Test bulk installer can be created and loads data."""
        assert bulk_installer is not None
        assert len(bulk_installer.df) == 6
        assert len(bulk_installer.servers_with_stars) == 5  # All except the 0-star one
    
    def test_filter_by_stars(self, bulk_installer):
        """Test filtering servers by star count."""
        # Get servers with 500+ stars
        high_star_servers = bulk_installer.servers_with_stars[
            bulk_installer.servers_with_stars['stars'] >= 500
        ]
        assert len(high_star_servers) == 4  # 5000, 1000, 800, 500 stars
        
        # Get servers with 1000+ stars
        very_high_star_servers = bulk_installer.servers_with_stars[
            bulk_installer.servers_with_stars['stars'] >= 1000
        ]
        assert len(very_high_star_servers) == 2  # 5000 and 1000 stars
    
    def test_filter_by_category(self, bulk_installer):
        """Test filtering servers by category."""
        ai_servers = bulk_installer.servers_with_stars[
            bulk_installer.servers_with_stars['category'] == 'ai_ml'
        ]
        assert len(ai_servers) == 1
        assert ai_servers.iloc[0]['name'] == 'ai-ml-server'
        
        db_servers = bulk_installer.servers_with_stars[
            bulk_installer.servers_with_stars['category'] == 'database'
        ]
        assert len(db_servers) == 1
        assert db_servers.iloc[0]['name'] == 'database-server'
    
    @patch('subprocess.run')
    def test_install_by_stars_mock(self, mock_run, bulk_installer):
        """Test install by stars functionality with mocked subprocess."""
        # Mock successful installation
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        
        # Install servers with 1000+ stars
        summary = bulk_installer.install_by_stars(min_stars=1000)
        
        assert summary['total_attempts'] == 2
        assert summary['successful'] == 2
        assert summary['failed'] == 0
        assert summary['success_rate'] == 100.0
        
        # Check that the right servers were installed
        assert 'server-high-stars' in bulk_installer.installed_servers
        assert 'ai-ml-server' in bulk_installer.installed_servers
    
    @patch('subprocess.run')
    def test_install_by_category_mock(self, mock_run, bulk_installer):
        """Test install by category functionality."""
        mock_run.return_value = MagicMock(returncode=0)
        
        # Install AI/ML servers
        summary = bulk_installer.install_by_category('ai_ml')
        
        assert summary['total_attempts'] == 1
        assert summary['successful'] == 1
        assert 'ai-ml-server' in bulk_installer.installed_servers
    
    @patch('subprocess.run')
    def test_install_top_n_mock(self, mock_run, bulk_installer):
        """Test installing top N servers by stars."""
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock user confirmation
        with patch('haive.mcp.installer.bulk_installer.console.input', return_value='y'):
            summary = bulk_installer.install_top_n(n=3)
        
        assert summary['total_attempts'] == 3
        assert summary['successful'] == 3
        
        # Check top 3 servers were installed
        assert 'server-high-stars' in bulk_installer.installed_servers
        assert 'ai-ml-server' in bulk_installer.installed_servers
        assert 'database-server' in bulk_installer.installed_servers
    
    @patch('subprocess.run')
    def test_failed_installation(self, mock_run, bulk_installer):
        """Test handling of failed installations."""
        # Mock failed installation
        mock_run.return_value = MagicMock(
            returncode=1, 
            stderr='Installation failed: Package not found'
        )
        
        summary = bulk_installer.install_by_stars(min_stars=5000)
        
        assert summary['total_attempts'] == 1
        assert summary['successful'] == 0
        assert summary['failed'] == 1
        assert summary['success_rate'] == 0.0
    
    def test_skip_already_installed(self, bulk_installer):
        """Test that already installed servers are skipped."""
        # Mark a server as installed
        bulk_installer.installed_servers.add('server-high-stars')
        
        # Try to install it again
        server = bulk_installer.servers_with_stars.iloc[0]
        result = bulk_installer._install_server(server)
        
        assert result is True  # Should return True but skip installation
        assert len(bulk_installer.install_log) == 0  # No new log entry
    
    def test_save_install_report(self, bulk_installer, temp_dir):
        """Test saving installation report."""
        # Add some mock installation data
        bulk_installer.installed_servers.add('test-server')
        bulk_installer.install_log.append({
            'timestamp': '2025-01-01T00:00:00',
            'name': 'test-server',
            'status': 'success',
            'command': 'npm install -g test-server',
            'error': ''
        })
        
        # Save report
        report_path = Path(temp_dir) / "test_report.json"
        bulk_installer.save_install_report(str(report_path))
        
        # Verify report
        assert report_path.exists()
        with open(report_path) as f:
            report = json.load(f)
        
        assert 'summary' in report
        assert 'installed_servers' in report
        assert 'install_log' in report
        assert 'test-server' in report['installed_servers']
    
    def test_get_summary(self, bulk_installer):
        """Test getting installation summary."""
        # Add various installation results
        bulk_installer.install_log = [
            {'status': 'success'},
            {'status': 'success'},
            {'status': 'failed'},
            {'status': 'timeout'},
            {'status': 'error'}
        ]
        
        summary = bulk_installer._get_summary()
        
        assert summary['total_attempts'] == 5
        assert summary['successful'] == 2
        assert summary['failed'] == 1
        assert summary['timeout'] == 1
        assert summary['error'] == 1
        assert summary['success_rate'] == 40.0


class TestBulkDownloadIntegration:
    """Integration tests for bulk download with real data."""
    
    @pytest.fixture
    def real_csv_path(self):
        """Get path to real CSV data if it exists."""
        csv_path = Path("/home/will/Projects/haive/backend/haive/packages/haive-mcp/scratches/mcp-analysis/mcp_servers_data.csv")
        if csv_path.exists():
            return csv_path
        pytest.skip("Real CSV data not available")
    
    def test_load_real_data(self, real_csv_path):
        """Test loading real MCP server data."""
        installer = MCPBulkInstaller(data_path=str(real_csv_path))
        
        assert len(installer.df) == 1960  # Total servers
        assert len(installer.servers_with_stars) == 194  # Servers with stars
        
        # Check star distribution
        high_star_servers = installer.servers_with_stars[
            installer.servers_with_stars['stars'] >= 1000
        ]
        assert len(high_star_servers) == 37  # As per our analysis
    
    def test_analyze_categories(self, real_csv_path):
        """Test analyzing server categories in real data."""
        installer = MCPBulkInstaller(data_path=str(real_csv_path))
        
        # Get category distribution
        categories = installer.servers_with_stars['category'].value_counts()
        
        # Should have various categories
        assert len(categories) > 0
        # Common categories should include utility, ai_ml, database, etc.


if __name__ == "__main__":
    pytest.main([__file__, "-v"])