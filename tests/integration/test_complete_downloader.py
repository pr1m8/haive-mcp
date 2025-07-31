#!/usr/bin/env python3
"""Integration tests for the complete downloader system using pytest.

This module tests the full download workflow with real servers.
"""

import json
from pathlib import Path
import sys

import pytest


# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.haive.mcp.downloader.legacy_core import (
    GeneralMCPDownloader,
    InstallationMethod,
    ServerConfig,
    ServerTemplate,
)


class TestGeneralMCPDownloader:
    """Integration tests for the complete MCP downloader."""

    @pytest.fixture
    def test_install_dir(self, tmp_path):
        """Create test installation directory."""
        install_dir = tmp_path / "mcp_servers"
        install_dir.mkdir(parents=True, exist_ok=True)
        return install_dir

    @pytest.fixture
    def downloader(self, test_install_dir):
        """Create downloader instance with test directory."""
        return GeneralMCPDownloader(install_dir=str(test_install_dir))

    def test_downloader_initialization(self, downloader):
        """Test that downloader initializes properly."""
        assert downloader is not None
        assert len(downloader.installers) > 0
        assert len(downloader.templates) > 0
        assert hasattr(downloader, "servers")

    def test_default_templates_loaded(self, downloader):
        """Test that default templates are loaded."""
        expected_templates = [
            "npm_official",
            "npm_community",
            "git_repo",
            "docker_image",
        ]

        for template_name in expected_templates:
            assert template_name in downloader.templates
            template = downloader.templates[template_name]
            assert template.name == template_name
            assert isinstance(template.installation_method, InstallationMethod)

    def test_default_servers_configured(self, downloader):
        """Test that default servers are configured."""
        assert len(downloader.servers) > 0

        # Should have filesystem server
        filesystem_servers = [s for s in downloader.servers if s.name == "filesystem"]
        assert len(filesystem_servers) > 0

        filesystem = filesystem_servers[0]
        assert filesystem.template == "npm_official"
        assert filesystem.enabled is True

    @pytest.mark.asyncio
    async def test_download_single_server(self, downloader):
        """Test downloading a single MCP server."""
        # Use filesystem server as it's most likely to work
        result = await downloader.download_servers(
            server_names=["filesystem"], max_concurrent=1
        )

        assert "total" in result
        assert "successful" in result
        assert "failed" in result
        assert result["total"] >= 1

        # Check result structure
        assert "success_rate" in result
        assert "successful_servers" in result
        assert "failed_servers" in result
        assert "config_file" in result

    @pytest.mark.asyncio
    async def test_download_nonexistent_server(self, downloader):
        """Test downloading a server that doesn't exist."""
        result = await downloader.download_servers(
            server_names=["nonexistent-server-12345"], max_concurrent=1
        )

        assert result["total"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1
        assert len(result["failed_servers"]) == 1

        failed_server = result["failed_servers"][0]
        assert failed_server["server"] == "nonexistent-server-12345"
        assert "error" in failed_server

    @pytest.mark.asyncio
    async def test_download_by_category(self, downloader):
        """Test downloading servers by category."""
        result = await downloader.download_servers(
            categories=["official"], max_concurrent=2
        )

        # Should find official servers to download
        assert result["total"] >= 0  # Might be 0 if no official servers enabled
        assert isinstance(result["successful"], int)
        assert isinstance(result["failed"], int)

    @pytest.mark.asyncio
    async def test_empty_download_request(self, downloader):
        """Test downloading with no servers specified."""
        # Clear servers to ensure no enabled servers
        original_servers = downloader.servers.copy()
        downloader.servers = []

        result = await downloader.download_servers()

        assert result["success"] is False
        assert "No servers selected" in result.get("message", "")

        # Restore servers
        downloader.servers = original_servers

    @pytest.mark.asyncio
    async def test_config_generation(self, downloader, test_install_dir):
        """Test that configuration files are generated properly."""
        # Download a server
        result = await downloader.download_servers(
            server_names=["filesystem"], max_concurrent=1
        )

        if result["successful"] > 0:
            # Check that config file was created
            config_file = Path(result["config_file"])
            assert config_file.exists()

            # Check config file contents
            with open(config_file) as f:
                config = json.load(f)

            assert "mcpServers" in config
            assert "generated_at" in config
            assert "install_dir" in config

            # Should have at least one server configured
            assert len(config["mcpServers"]) > 0

    def test_installer_availability(self, downloader):
        """Test that all expected installers are available."""
        installer_types = [
            type(installer).__name__ for installer in downloader.installers
        ]

        expected_installers = [
            "NPMInstaller",
            "PipInstaller",
            "GitInstaller",
            "DockerInstaller",
        ]

        for expected in expected_installers:
            assert expected in installer_types

    @pytest.mark.asyncio
    async def test_concurrent_downloads(self, downloader):
        """Test concurrent downloading of multiple servers."""
        # Try to download multiple servers concurrently
        servers_to_test = ["filesystem"]  # Add more if available

        if len(downloader.servers) > 1:
            # Add another server if available
            other_servers = [
                s.name
                for s in downloader.servers
                if s.name != "filesystem" and s.enabled
            ]
            if other_servers:
                servers_to_test.append(other_servers[0])

        result = await downloader.download_servers(
            server_names=servers_to_test, max_concurrent=3
        )

        assert result["total"] == len(servers_to_test)
        # At least some should succeed (or all might fail due to missing dependencies)
        assert isinstance(result["successful"], int)
        assert isinstance(result["failed"], int)
        assert result["successful"] + result["failed"] == result["total"]


class TestDownloaderConfiguration:
    """Test downloader configuration and customization."""

    def test_custom_config_file(self, tmp_path):
        """Test creating downloader with custom config file."""
        config_file = tmp_path / "custom_config.yaml"

        # Create minimal config
        config_content = """
templates:
  - name: test_template
    installation_method: npm
    command_pattern: 'test-{service}'

servers:
  - name: test_server
    template: test_template
    source: npm
    variables:
      service: example
    enabled: true
"""

        config_file.write_text(config_content)

        # Create downloader with custom config
        downloader = GeneralMCPDownloader(
            config_file=str(config_file), install_dir=str(tmp_path / "servers")
        )

        # Check that custom config was loaded
        assert "test_template" in downloader.templates
        assert len([s for s in downloader.servers if s.name == "test_server"]) > 0

    def test_custom_install_directory(self, tmp_path):
        """Test creating downloader with custom install directory."""
        custom_dir = tmp_path / "custom_mcp_servers"

        downloader = GeneralMCPDownloader(install_dir=str(custom_dir))

        assert downloader.install_dir == custom_dir
        assert custom_dir.exists()  # Should be created automatically


class TestDownloaderEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_missing_template(self, tmp_path):
        """Test server with missing template."""
        downloader = GeneralMCPDownloader(install_dir=str(tmp_path))

        # Add server with non-existent template
        bad_server = ServerConfig(
            name="bad_server",
            template="nonexistent_template",
            source="test",
            variables={},
            enabled=True,
        )

        downloader.servers.append(bad_server)

        result = await downloader.download_servers(
            server_names=["bad_server"], max_concurrent=1
        )

        assert result["total"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1

        failed_server = result["failed_servers"][0]
        assert (
            "Template" in failed_server["error"]
            or "not found" in failed_server["error"]
        )

    @pytest.mark.asyncio
    async def test_no_suitable_installer(self, tmp_path):
        """Test server with no suitable installer."""
        downloader = GeneralMCPDownloader(install_dir=str(tmp_path))

        # Create template with unknown installation method
        unknown_template = ServerTemplate(
            name="unknown_method",
            installation_method=InstallationMethod.MANUAL,  # Use MANUAL as placeholder
            command_pattern="unknown {command}",
        )

        downloader.templates["unknown_method"] = unknown_template

        # Add server using unknown method
        unknown_server = ServerConfig(
            name="unknown_server",
            template="unknown_method",
            source="test",
            variables={"command": "test"},
            enabled=True,
        )

        downloader.servers.append(unknown_server)

        result = await downloader.download_servers(
            server_names=["unknown_server"], max_concurrent=1
        )

        # Should fail to find installer
        assert result["total"] == 1
        assert result["failed"] == 1


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
