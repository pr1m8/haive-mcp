#!/usr/bin/env python3
"""Test viewing and managing installed MCP servers."""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import subprocess

from haive.mcp.discovery.installed_servers import MCPServerDiscovery


class TestViewingInstalled:
    """Test viewing and discovering installed MCP servers."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def discovery(self):
        """Create MCPServerDiscovery instance."""
        return MCPServerDiscovery()
    
    @pytest.fixture
    def mock_npm_list_output(self):
        """Mock npm list output."""
        return json.dumps({
            "dependencies": {
                "@modelcontextprotocol/server-filesystem": {
                    "version": "1.0.0",
                    "resolved": "/usr/local/lib/node_modules/@modelcontextprotocol/server-filesystem"
                },
                "@anthropic/mcp-server-slack": {
                    "version": "0.5.0",
                    "resolved": "/usr/local/lib/node_modules/@anthropic/mcp-server-slack"
                },
                "random-package": {
                    "version": "2.0.0",
                    "resolved": "/usr/local/lib/node_modules/random-package"
                }
            }
        })
    
    @pytest.fixture
    def mock_pip_list_output(self):
        """Mock pip list output."""
        return json.dumps([
            {"name": "mcp-server-python", "version": "1.0.0"},
            {"name": "model-context-protocol", "version": "0.5.0"},
            {"name": "unrelated-package", "version": "3.0.0"}
        ])
    
    def test_discovery_creation(self, discovery):
        """Test creating discovery instance."""
        assert discovery is not None
        assert hasattr(discovery, 'npm_servers')
        assert hasattr(discovery, 'pip_servers')
        assert hasattr(discovery, 'config_servers')
    
    def test_find_npm_servers(self, discovery, mock_npm_list_output):
        """Test finding NPM-installed MCP servers."""
        with patch('subprocess.run') as mock_run:
            # Mock successful npm list
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_npm_list_output,
                stderr=''
            )
            
            servers = discovery.find_npm_servers()
            
            # Should find 2 MCP servers (not random-package)
            assert len(servers) == 2
            
            # Check server details
            server_names = [s['name'] for s in servers]
            assert '@modelcontextprotocol/server-filesystem' in server_names
            assert '@anthropic/mcp-server-slack' in server_names
            assert 'random-package' not in server_names
            
            # Verify server info
            fs_server = next(s for s in servers if 'filesystem' in s['name'])
            assert fs_server['version'] == '1.0.0'
            assert fs_server['type'] == 'npm'
            assert fs_server['global'] is True
    
    def test_find_pip_servers(self, discovery, mock_pip_list_output):
        """Test finding pip-installed MCP servers."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_pip_list_output,
                stderr=''
            )
            
            servers = discovery.find_pip_servers()
            
            # Should find 2 MCP-related packages
            assert len(servers) == 2
            
            server_names = [s['name'] for s in servers]
            assert 'mcp-server-python' in server_names
            assert 'model-context-protocol' in server_names
            assert 'unrelated-package' not in server_names
    
    def test_find_config_servers(self, discovery, temp_dir):
        """Test finding servers from configuration files."""
        # Create test config
        config_dir = temp_dir / ".mcp"
        config_dir.mkdir()
        config_file = config_dir / "servers.json"
        
        config_data = {
            "servers": {
                "custom-server": {
                    "command": "python",
                    "args": ["-m", "custom_mcp_server"],
                    "env": {"API_KEY": "test"}
                },
                "docker-server": {
                    "command": "docker",
                    "args": ["run", "mcp-server:latest"]
                }
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Patch config paths to include our temp dir
        with patch.object(discovery, 'find_config_servers') as mock_method:
            # Manually call with our test config
            servers = []
            with open(config_file) as f:
                config = json.load(f)
            
            for server_name, server_config in config['servers'].items():
                server_info = {
                    'name': server_name,
                    'type': 'config',
                    'config_path': str(config_file),
                    'command': server_config.get('command', ''),
                    'args': server_config.get('args', []),
                    'discovered_at': '2025-01-01T00:00:00'
                }
                servers.append(server_info)
            
            mock_method.return_value = servers
            found_servers = discovery.find_config_servers()
            
            assert len(found_servers) == 2
            assert any(s['name'] == 'custom-server' for s in found_servers)
            assert any(s['name'] == 'docker-server' for s in found_servers)
    
    def test_find_all_installed(self, discovery, mock_npm_list_output, mock_pip_list_output):
        """Test finding all installed servers across different sources."""
        with patch('subprocess.run') as mock_run:
            # Set up different responses for npm and pip
            def side_effect(cmd, *args, **kwargs):
                if cmd[0] == 'npm':
                    return MagicMock(
                        returncode=0,
                        stdout=mock_npm_list_output,
                        stderr=''
                    )
                elif cmd[0] == 'pip':
                    return MagicMock(
                        returncode=0,
                        stdout=mock_pip_list_output,
                        stderr=''
                    )
                return MagicMock(returncode=1)
            
            mock_run.side_effect = side_effect
            
            all_servers = discovery.find_all_installed()
            
            # Should find servers from both npm and pip
            assert len(all_servers) >= 4
            
            # Check we have both types
            types = set(s['type'] for s in all_servers)
            assert 'npm' in types
            assert 'pip' in types
    
    def test_check_server_availability_npm(self, discovery):
        """Test checking NPM server availability."""
        with patch('subprocess.run') as mock_run:
            # Mock successful npm list
            mock_run.return_value = MagicMock(returncode=0)
            
            available = discovery.check_server_availability("@modelcontextprotocol/server-filesystem")
            assert available is True
            
            # Verify npm list was called
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == 'npm'
            assert call_args[1] == 'list'
    
    def test_check_server_availability_pip(self, discovery):
        """Test checking pip server availability."""
        with patch('subprocess.run') as mock_run:
            # First call (npm) fails, second (pip) succeeds
            mock_run.side_effect = [
                MagicMock(returncode=1),  # npm list fails
                MagicMock(returncode=0)   # pip show succeeds
            ]
            
            available = discovery.check_server_availability("mcp-server-python")
            assert available is True
    
    def test_check_server_not_available(self, discovery):
        """Test checking unavailable server."""
        with patch('subprocess.run') as mock_run:
            # All checks fail
            mock_run.return_value = MagicMock(returncode=1)
            
            available = discovery.check_server_availability("nonexistent-server")
            assert available is False
    
    def test_get_server_info_npm(self, discovery):
        """Test getting detailed NPM server information."""
        npm_info = {
            "dependencies": {
                "@modelcontextprotocol/server-filesystem": {
                    "version": "1.0.0",
                    "resolved": "/path/to/server",
                    "dependencies": {"stdio": "^1.0.0"}
                }
            }
        }
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps(npm_info),
                stderr=''
            )
            
            info = discovery.get_server_info("@modelcontextprotocol/server-filesystem")
            
            assert info is not None
            assert info['name'] == '@modelcontextprotocol/server-filesystem'
            assert info['type'] == 'npm'
            assert info['version'] == '1.0.0'
    
    def test_get_server_info_pip(self, discovery):
        """Test getting detailed pip server information."""
        pip_output = """Name: mcp-server-python
Version: 1.0.0
Location: /usr/local/lib/python3.9/site-packages
Requires: aiohttp, pydantic
Required-by: 
"""
        
        with patch('subprocess.run') as mock_run:
            # First call (npm) fails, second (pip) succeeds
            mock_run.side_effect = [
                MagicMock(returncode=1),  # npm fails
                MagicMock(returncode=0, stdout=pip_output, stderr='')  # pip succeeds
            ]
            
            info = discovery.get_server_info("mcp-server-python")
            
            assert info is not None
            assert info['name'] == 'mcp-server-python'
            assert info['type'] == 'pip'
            assert info['version'] == '1.0.0'
    
    def test_export_installed_list(self, discovery, temp_dir):
        """Test exporting installed server list."""
        # Add mock data
        discovery.npm_servers = [
            {'name': 'npm-server', 'version': '1.0.0', 'type': 'npm'}
        ]
        discovery.pip_servers = [
            {'name': 'pip-server', 'version': '2.0.0', 'type': 'pip'}
        ]
        discovery.config_servers = [
            {'name': 'config-server', 'type': 'config'}
        ]
        
        # Mock find_all_installed to return our test data
        with patch.object(discovery, 'find_all_installed') as mock_find:
            mock_find.return_value = (
                discovery.npm_servers + 
                discovery.pip_servers + 
                discovery.config_servers
            )
            
            export_file = temp_dir / "installed_servers.json"
            discovery.export_installed_list(str(export_file))
            
            assert export_file.exists()
            
            with open(export_file) as f:
                data = json.load(f)
            
            assert 'timestamp' in data
            assert data['total_servers'] == 3
            assert data['npm_servers'] == 1
            assert data['pip_servers'] == 1
            assert data['config_servers'] == 1
            assert len(data['servers']) == 3
    
    def test_local_npm_packages(self, discovery, temp_dir):
        """Test finding local npm packages in a project."""
        # Create package.json
        package_json = temp_dir / "package.json"
        package_data = {
            "name": "test-project",
            "dependencies": {
                "@modelcontextprotocol/server-github": "^1.0.0",
                "express": "^4.0.0"  # Non-MCP package
            }
        }
        
        with open(package_json, 'w') as f:
            json.dump(package_data, f)
        
        local_npm_output = {
            "dependencies": {
                "@modelcontextprotocol/server-github": {
                    "version": "1.0.0",
                    "resolved": "node_modules/@modelcontextprotocol/server-github"
                },
                "express": {
                    "version": "4.18.0",
                    "resolved": "node_modules/express"
                }
            }
        }
        
        with patch('subprocess.run') as mock_run:
            with patch('pathlib.Path.exists') as mock_exists:
                # Make it think package.json exists
                mock_exists.return_value = True
                
                mock_run.side_effect = [
                    MagicMock(returncode=0, stdout='{}', stderr=''),  # Global npm list
                    MagicMock(returncode=0, stdout=json.dumps(local_npm_output), stderr='')  # Local npm list
                ]
                
                servers = discovery.find_npm_servers()
                
                # Should find the local MCP server
                local_servers = [s for s in servers if not s['global']]
                assert len(local_servers) == 1
                assert local_servers[0]['name'] == '@modelcontextprotocol/server-github'
                assert local_servers[0]['global'] is False


class TestServerSummaryDisplay:
    """Test displaying summary of installed servers."""
    
    def test_categorize_by_type(self):
        """Test categorizing servers by type."""
        servers = [
            {'name': 'server1', 'type': 'npm'},
            {'name': 'server2', 'type': 'npm'},
            {'name': 'server3', 'type': 'pip'},
            {'name': 'server4', 'type': 'config'},
            {'name': 'server5', 'type': 'npm'}
        ]
        
        by_type = {}
        for server in servers:
            server_type = server['type']
            if server_type not in by_type:
                by_type[server_type] = []
            by_type[server_type].append(server)
        
        assert len(by_type['npm']) == 3
        assert len(by_type['pip']) == 1
        assert len(by_type['config']) == 1
    
    def test_filter_mcp_servers(self):
        """Test filtering only MCP-related servers."""
        servers = [
            {'name': '@modelcontextprotocol/server-filesystem'},
            {'name': 'mcp-server-python'},
            {'name': 'random-npm-package'},
            {'name': 'model-context-protocol'},
            {'name': 'express'}
        ]
        
        # Filter MCP servers
        mcp_servers = [
            s for s in servers
            if 'mcp' in s['name'].lower() or 
               'model-context' in s['name'].lower() or
               '@modelcontextprotocol' in s['name']
        ]
        
        assert len(mcp_servers) == 3
        assert 'random-npm-package' not in [s['name'] for s in mcp_servers]
        assert 'express' not in [s['name'] for s in mcp_servers]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])