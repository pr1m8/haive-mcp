#!/usr/bin/env python3
"""Test specific MCP server download functionality."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock, AsyncMock

from haive.mcp.downloader.installers import (
    NPMInstaller,
    PipInstaller,
    GitInstaller,
    DockerInstaller,
    BinaryInstaller,
    CurlInstaller
)
from haive.mcp.downloader.config import (
    ServerConfig,
    ServerTemplate,
    InstallationMethod
)


class TestSpecificDownload:
    """Test downloading and installing specific MCP servers."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def npm_server_config(self):
        """Create NPM server configuration."""
        return ServerConfig(
            name="filesystem-server",
            source="@modelcontextprotocol/server-filesystem",
            transport="stdio",
            variables={"package": "@modelcontextprotocol/server-filesystem"}
        )
    
    @pytest.fixture
    def npm_template(self):
        """Create NPM server template."""
        return ServerTemplate(
            installation_method=InstallationMethod.NPM,
            command_pattern="{package}",
            args_pattern=["/path/to/serve"]
        )
    
    @pytest.fixture
    def git_server_config(self):
        """Create Git server configuration."""
        return ServerConfig(
            name="custom-mcp-server",
            source="https://github.com/example/mcp-server.git",
            transport="stdio",
            variables={"binary": "mcp-server"}
        )
    
    @pytest.fixture
    def git_template(self):
        """Create Git server template."""
        return ServerTemplate(
            installation_method=InstallationMethod.GIT,
            command_pattern="./build/{binary}",
            post_install=["npm install", "npm run build"]
        )


class TestNPMInstaller:
    """Test NPM installer functionality."""
    
    @pytest.fixture
    def npm_installer(self):
        """Create NPM installer instance."""
        return NPMInstaller()
    
    @pytest.mark.asyncio
    async def test_can_handle_npm(self, npm_installer, npm_server_config, npm_template):
        """Test NPM installer can handle NPM installations."""
        can_handle = await npm_installer.can_handle(npm_server_config, npm_template)
        assert can_handle is True
    
    @pytest.mark.asyncio
    async def test_cannot_handle_git(self, npm_installer, git_server_config, git_template):
        """Test NPM installer cannot handle Git installations."""
        can_handle = await npm_installer.can_handle(git_server_config, git_template)
        assert can_handle is False
    
    @pytest.mark.asyncio
    async def test_npm_install_global_success(self, npm_installer, npm_server_config, npm_template, temp_dir):
        """Test successful global NPM installation."""
        with patch.object(npm_installer, '_run_command') as mock_run:
            # Mock successful global install
            mock_run.return_value = {
                'returncode': 0,
                'stdout': 'Package installed successfully',
                'stderr': ''
            }
            
            result = await npm_installer.install(npm_server_config, npm_template, temp_dir)
            
            assert result['success'] is True
            assert result['method'] == 'npm'
            assert result['install_type'] == 'global'
            assert 'command' in result
            
            # Verify npm install command was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == 'npm'
            assert call_args[1] == 'install'
            assert call_args[2] == '-g'
    
    @pytest.mark.asyncio
    async def test_npm_install_local_fallback(self, npm_installer, npm_server_config, npm_template, temp_dir):
        """Test NPM local installation fallback when global fails."""
        with patch.object(npm_installer, '_run_command') as mock_run:
            # First call fails (global), second succeeds (local)
            mock_run.side_effect = [
                {'returncode': 1, 'stderr': 'Permission denied'},
                {'returncode': 0, 'stdout': 'Local install success'}
            ]
            
            result = await npm_installer.install(npm_server_config, npm_template, temp_dir)
            
            assert result['success'] is True
            assert result['install_type'] == 'local'
            assert 'install_dir' in result
            
            # Verify both global and local installs were attempted
            assert mock_run.call_count == 2
    
    @pytest.mark.asyncio
    async def test_npm_verify(self, npm_installer, npm_server_config, npm_template, temp_dir):
        """Test NPM installation verification."""
        with patch.object(npm_installer, '_run_command') as mock_run:
            # Mock successful verification
            mock_run.return_value = {'returncode': 0}
            
            verified = await npm_installer.verify(npm_server_config, npm_template, temp_dir)
            assert verified is True
            
            # Check npx command was used
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == 'npx'


class TestGitInstaller:
    """Test Git installer functionality."""
    
    @pytest.fixture
    def git_installer(self):
        """Create Git installer instance."""
        return GitInstaller()
    
    @pytest.mark.asyncio
    async def test_git_clone_success(self, git_installer, git_server_config, git_template, temp_dir):
        """Test successful Git clone and post-install."""
        with patch.object(git_installer, '_run_command') as mock_run:
            # Mock successful git clone and post-install commands
            mock_run.side_effect = [
                {'returncode': 0},  # git clone
                {'returncode': 0},  # npm install
                {'returncode': 0}   # npm run build
            ]
            
            result = await git_installer.install(git_server_config, git_template, temp_dir)
            
            assert result['success'] is True
            assert result['method'] == 'git'
            assert 'clone_dir' in result
            assert result['repo_url'] == git_server_config.source
            
            # Verify git clone was called
            first_call = mock_run.call_args_list[0][0][0]
            assert first_call[0] == 'git'
            assert first_call[1] == 'clone'
    
    @pytest.mark.asyncio
    async def test_git_clone_with_version(self, git_installer, git_server_config, git_template, temp_dir):
        """Test Git clone with specific version/branch."""
        git_server_config.version = "v1.0.0"
        
        with patch.object(git_installer, '_run_command') as mock_run:
            mock_run.return_value = {'returncode': 0}
            
            await git_installer.install(git_server_config, git_template, temp_dir)
            
            # Verify --branch flag was used
            call_args = mock_run.call_args_list[0][0][0]
            assert '--branch' in call_args
            assert 'v1.0.0' in call_args
    
    @pytest.mark.asyncio
    async def test_git_verify(self, git_installer, git_server_config, git_template, temp_dir):
        """Test Git installation verification."""
        # Create mock clone directory with .git
        clone_dir = temp_dir / git_server_config.name
        clone_dir.mkdir()
        (clone_dir / ".git").mkdir()
        
        verified = await git_installer.verify(git_server_config, git_template, temp_dir)
        assert verified is True


class TestPipInstaller:
    """Test Python pip installer functionality."""
    
    @pytest.fixture
    def pip_installer(self):
        """Create pip installer instance."""
        return PipInstaller()
    
    @pytest.fixture
    def pip_server_config(self):
        """Create pip server configuration."""
        return ServerConfig(
            name="mcp-python-server",
            source="mcp-python-server",
            transport="stdio",
            variables={"package": "mcp-python-server"}
        )
    
    @pytest.fixture
    def pip_template(self):
        """Create pip server template."""
        return ServerTemplate(
            installation_method=InstallationMethod.PIP,
            command_pattern="{package}"
        )
    
    @pytest.mark.asyncio
    async def test_pip_install_success(self, pip_installer, pip_server_config, pip_template, temp_dir):
        """Test successful pip installation."""
        with patch.object(pip_installer, '_run_command') as mock_run:
            mock_run.return_value = {'returncode': 0}
            
            result = await pip_installer.install(pip_server_config, pip_template, temp_dir)
            
            assert result['success'] is True
            assert result['method'] == 'pip'
            assert 'module' in result
            assert result['module'] == 'mcp_python_server'  # Hyphens replaced
    
    @pytest.mark.asyncio
    async def test_pip_verify_import(self, pip_installer, pip_server_config, pip_template, temp_dir):
        """Test pip installation verification via import."""
        with patch.object(pip_installer, '_run_command') as mock_run:
            mock_run.return_value = {'returncode': 0}
            
            verified = await pip_installer.verify(pip_server_config, pip_template, temp_dir)
            assert verified is True
            
            # Check python import command
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == 'python'
            assert call_args[1] == '-c'
            assert 'import' in call_args[2]


class TestDockerInstaller:
    """Test Docker installer functionality."""
    
    @pytest.fixture
    def docker_installer(self):
        """Create Docker installer instance."""
        return DockerInstaller()
    
    @pytest.fixture
    def docker_server_config(self):
        """Create Docker server configuration."""
        return ServerConfig(
            name="mcp-docker-server",
            source="mcpserver/example:latest",
            transport="docker",
            variables={"image": "mcpserver/example"},
            env_vars={"API_KEY": "test123"}
        )
    
    @pytest.fixture
    def docker_template(self):
        """Create Docker server template."""
        return ServerTemplate(
            installation_method=InstallationMethod.DOCKER,
            command_pattern="{image}"
        )
    
    @pytest.mark.asyncio
    async def test_docker_pull_success(self, docker_installer, docker_server_config, docker_template, temp_dir):
        """Test successful Docker image pull."""
        with patch.object(docker_installer, '_run_command') as mock_run:
            mock_run.return_value = {'returncode': 0}
            
            result = await docker_installer.install(docker_server_config, docker_template, temp_dir)
            
            assert result['success'] is True
            assert result['method'] == 'docker'
            assert result['transport'] == 'docker'
            
            # Check docker command includes env vars
            docker_args = result['args']
            assert '-e' in docker_args
            assert 'API_KEY=test123' in docker_args


class TestBinaryInstaller:
    """Test binary installer functionality."""
    
    @pytest.fixture
    def binary_installer(self):
        """Create binary installer instance."""
        return BinaryInstaller()
    
    @pytest.fixture
    def binary_server_config(self):
        """Create binary server configuration."""
        return ServerConfig(
            name="mcp-binary",
            source="https://github.com/example/releases/mcp-server-linux-amd64",
            transport="stdio",
            variables={"binary": "mcp-server"}
        )
    
    @pytest.fixture
    def binary_template(self):
        """Create binary server template."""
        return ServerTemplate(
            installation_method=InstallationMethod.BINARY,
            command_pattern="./{binary}"
        )
    
    @pytest.mark.asyncio
    async def test_binary_download_success(self, binary_installer, binary_server_config, binary_template, temp_dir):
        """Test successful binary download."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content.iter_chunked = AsyncMock(return_value=[b'binary content'])
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await binary_installer.install(binary_server_config, binary_template, temp_dir)
            
            assert result['success'] is True
            assert result['method'] == 'binary'
            assert 'binary_path' in result
            
            # Check binary was created
            binary_path = Path(result['binary_path'])
            assert binary_path.name == 'mcp-server'


class TestViewingInstalledServers:
    """Test viewing and discovering installed servers."""
    
    @pytest.mark.asyncio
    async def test_discover_installed_servers(self):
        """Test discovering installed MCP servers."""
        from haive.mcp.discovery.installed_servers import MCPServerDiscovery
        
        discovery = MCPServerDiscovery()
        
        # Mock npm list output
        npm_output = {
            "dependencies": {
                "@modelcontextprotocol/server-filesystem": {
                    "version": "1.0.0",
                    "resolved": "/path/to/server"
                }
            }
        }
        
        with patch.object(discovery, '_run_command') as mock_run:
            mock_run.return_value = {
                'returncode': 0,
                'stdout': json.dumps(npm_output),
                'stderr': ''
            }
            
            npm_servers = discovery.find_npm_servers()
            assert len(npm_servers) > 0
            assert npm_servers[0]['type'] == 'npm'
    
    def test_check_server_availability(self):
        """Test checking if a specific server is available."""
        from haive.mcp.discovery.installed_servers import MCPServerDiscovery
        
        discovery = MCPServerDiscovery()
        
        with patch('subprocess.run') as mock_run:
            # Mock successful npm list
            mock_run.return_value = MagicMock(returncode=0)
            
            available = discovery.check_server_availability("@modelcontextprotocol/server-filesystem")
            assert available is True
    
    def test_export_installed_list(self, temp_dir):
        """Test exporting list of installed servers."""
        from haive.mcp.discovery.installed_servers import MCPServerDiscovery
        
        discovery = MCPServerDiscovery()
        
        # Add mock data
        discovery.npm_servers = [{'name': 'test-server', 'version': '1.0.0'}]
        
        export_path = temp_dir / "installed.json"
        discovery.export_installed_list(str(export_path))
        
        assert export_path.exists()
        with open(export_path) as f:
            data = json.load(f)
        
        assert 'timestamp' in data
        assert 'servers' in data
        assert data['npm_servers'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])