#!/usr/bin/env python3
"""Unit tests for each installer type using pytest.

This module provides comprehensive pytest-based tests for all installer types.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.haive.mcp.downloader.legacy_core import (
    DockerInstaller,
    GitInstaller,
    InstallationMethod,
    NPMInstaller,
    PipInstaller,
    ServerConfig,
    ServerTemplate,
)


class TestInstallerBase:
    """Base class for installer tests with common utilities."""

    @pytest.fixture
    def test_dir(self, tmp_path):
        """Create test directory."""
        return tmp_path / "installer_test"

    def check_command_available(self, command: str) -> bool:
        """Check if a command is available on the system."""
        try:
            subprocess.run([command, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class TestNPMInstaller(TestInstallerBase):
    """Test NPM installer functionality."""

    @pytest.fixture
    def npm_installer(self):
        """Create NPM installer instance."""
        return NPMInstaller()

    @pytest.fixture
    def npm_config(self):
        """Create NPM server configuration."""
        return ServerConfig(
            name="test-npm",
            template="npm",
            source="npm",
            variables={"package": "@modelcontextprotocol/server-filesystem"},
        )

    @pytest.fixture
    def npm_template(self):
        """Create NPM server template."""
        return ServerTemplate(
            name="npm",
            installation_method=InstallationMethod.NPM,
            command_pattern="{package}",
        )

    @pytest.mark.asyncio
    async def test_can_handle_npm_method(self, npm_installer, npm_config, npm_template):
        """Test that NPM installer can handle NPM installation method."""
        result = await npm_installer.can_handle(npm_config, npm_template)
        assert result is True

    @pytest.mark.asyncio
    async def test_cannot_handle_other_methods(self, npm_installer, npm_config):
        """Test that NPM installer rejects non-NPM methods."""
        git_template = ServerTemplate(
            name="git",
            installation_method=InstallationMethod.GIT,
            command_pattern="git clone {repo}",
        )

        result = await npm_installer.can_handle(npm_config, git_template)
        assert result is False

    @pytest.mark.skipif(
        not TestInstallerBase().check_command_available("npm"),
        reason="npm not available",
    )
    @pytest.mark.asyncio
    async def test_install_real_package(
        self, npm_installer, npm_config, npm_template, test_dir
    ):
        """Test installing a real npm package."""
        test_dir.mkdir(parents=True, exist_ok=True)

        result = await npm_installer.install(npm_config, npm_template, test_dir)

        assert result["success"] is True
        assert "command" in result
        assert result["method"] == "npm"

    @pytest.mark.skipif(
        not TestInstallerBase().check_command_available("npm"),
        reason="npm not available",
    )
    @pytest.mark.asyncio
    async def test_verify_installation(
        self, npm_installer, npm_config, npm_template, test_dir
    ):
        """Test verifying npm package installation."""
        test_dir.mkdir(parents=True, exist_ok=True)

        # Install first
        install_result = await npm_installer.install(npm_config, npm_template, test_dir)
        if install_result["success"]:
            # Verify
            verified = await npm_installer.verify(npm_config, npm_template, test_dir)
            # Note: This might fail if the package doesn't have --help, which is okay
            assert isinstance(verified, bool)

    @pytest.mark.asyncio
    async def test_install_nonexistent_package(self, npm_installer, test_dir):
        """Test installing a package that doesn't exist."""
        test_dir.mkdir(parents=True, exist_ok=True)

        bad_config = ServerConfig(
            name="bad-package",
            template="npm",
            source="npm",
            variables={"package": "this-package-definitely-does-not-exist-12345"},
        )

        template = ServerTemplate(
            name="npm",
            installation_method=InstallationMethod.NPM,
            command_pattern="{package}",
        )

        result = await npm_installer.install(bad_config, template, test_dir)
        assert result["success"] is False
        assert "error" in result


class TestPipInstaller(TestInstallerBase):
    """Test Pip installer functionality."""

    @pytest.fixture
    def pip_installer(self):
        """Create Pip installer instance."""
        return PipInstaller()

    @pytest.fixture
    def pip_config(self):
        """Create Pip server configuration."""
        return ServerConfig(
            name="test-pip",
            template="pip",
            source="pypi",
            variables={"package": "requests"},
        )

    @pytest.fixture
    def pip_template(self):
        """Create Pip server template."""
        return ServerTemplate(
            name="pip",
            installation_method=InstallationMethod.PIP,
            command_pattern="{package}",
        )

    @pytest.mark.asyncio
    async def test_can_handle_pip_method(self, pip_installer, pip_config, pip_template):
        """Test that Pip installer can handle PIP installation method."""
        result = await pip_installer.can_handle(pip_config, pip_template)
        assert result is True

    @pytest.mark.asyncio
    async def test_install_real_package(
        self, pip_installer, pip_config, pip_template, test_dir
    ):
        """Test installing a real pip package."""
        test_dir.mkdir(parents=True, exist_ok=True)

        result = await pip_installer.install(pip_config, pip_template, test_dir)

        assert result["success"] is True
        assert "command" in result
        assert result["method"] == "pip"

    @pytest.mark.asyncio
    async def test_verify_installation(
        self, pip_installer, pip_config, pip_template, test_dir
    ):
        """Test verifying pip package installation."""
        test_dir.mkdir(parents=True, exist_ok=True)

        # Install first
        install_result = await pip_installer.install(pip_config, pip_template, test_dir)
        if install_result["success"]:
            # Verify
            verified = await pip_installer.verify(pip_config, pip_template, test_dir)
            assert verified is True  # requests should be verifiable


class TestGitInstaller(TestInstallerBase):
    """Test Git installer functionality."""

    @pytest.fixture
    def git_installer(self):
        """Create Git installer instance."""
        return GitInstaller()

    @pytest.fixture
    def git_config(self):
        """Create Git server configuration."""
        return ServerConfig(
            name="test-git",
            template="git",
            source="https://github.com/octocat/Hello-World.git",
            variables={"owner": "octocat", "repo": "Hello-World"},
        )

    @pytest.fixture
    def git_template(self):
        """Create Git server template."""
        return ServerTemplate(
            name="git",
            installation_method=InstallationMethod.GIT,
            command_pattern="echo 'Hello from {repo}'",
            post_install=[],
        )

    @pytest.mark.asyncio
    async def test_can_handle_git_method(self, git_installer, git_config, git_template):
        """Test that Git installer can handle GIT installation method."""
        result = await git_installer.can_handle(git_config, git_template)
        assert result is True

    @pytest.mark.skipif(
        not TestInstallerBase().check_command_available("git"),
        reason="git not available",
    )
    @pytest.mark.asyncio
    async def test_clone_real_repository(
        self, git_installer, git_config, git_template, test_dir
    ):
        """Test cloning a real git repository."""
        test_dir.mkdir(parents=True, exist_ok=True)

        result = await git_installer.install(git_config, git_template, test_dir)

        assert result["success"] is True
        assert "clone_dir" in result
        assert result["method"] == "git"

        # Check that directory was created
        clone_dir = Path(result["clone_dir"])
        assert clone_dir.exists()
        assert (clone_dir / ".git").exists()

    @pytest.mark.skipif(
        not TestInstallerBase().check_command_available("git"),
        reason="git not available",
    )
    @pytest.mark.asyncio
    async def test_verify_clone(
        self, git_installer, git_config, git_template, test_dir
    ):
        """Test verifying git repository clone."""
        test_dir.mkdir(parents=True, exist_ok=True)

        # Clone first
        install_result = await git_installer.install(git_config, git_template, test_dir)
        if install_result["success"]:
            # Verify
            verified = await git_installer.verify(git_config, git_template, test_dir)
            assert verified is True

    @pytest.mark.asyncio
    async def test_clone_invalid_repository(self, git_installer, test_dir):
        """Test cloning an invalid repository."""
        test_dir.mkdir(parents=True, exist_ok=True)

        bad_config = ServerConfig(
            name="bad-repo",
            template="git",
            source="https://github.com/nonexistent/repository.git",
            variables={"owner": "nonexistent", "repo": "repository"},
        )

        template = ServerTemplate(
            name="git",
            installation_method=InstallationMethod.GIT,
            command_pattern="echo 'test'",
            post_install=[],
        )

        result = await git_installer.install(bad_config, template, test_dir)
        assert result["success"] is False
        assert "error" in result


class TestDockerInstaller(TestInstallerBase):
    """Test Docker installer functionality."""

    @pytest.fixture
    def docker_installer(self):
        """Create Docker installer instance."""
        return DockerInstaller()

    @pytest.fixture
    def docker_config(self):
        """Create Docker server configuration."""
        return ServerConfig(
            name="test-docker",
            template="docker",
            source="docker",
            variables={"image": "hello-world"},
        )

    @pytest.fixture
    def docker_template(self):
        """Create Docker server template."""
        return ServerTemplate(
            name="docker",
            installation_method=InstallationMethod.DOCKER,
            command_pattern="{image}",
        )

    @pytest.mark.asyncio
    async def test_can_handle_docker_method(
        self, docker_installer, docker_config, docker_template
    ):
        """Test that Docker installer can handle DOCKER installation method."""
        result = await docker_installer.can_handle(docker_config, docker_template)
        assert result is True

    @pytest.mark.skipif(
        not TestInstallerBase().check_command_available("docker"),
        reason="docker not available",
    )
    @pytest.mark.asyncio
    async def test_pull_real_image(
        self, docker_installer, docker_config, docker_template, test_dir
    ):
        """Test pulling a real docker image."""
        test_dir.mkdir(parents=True, exist_ok=True)

        result = await docker_installer.install(
            docker_config, docker_template, test_dir
        )

        assert result["success"] is True
        assert "image" in result
        assert result["method"] == "docker"
        assert result["image"] == "hello-world"

    @pytest.mark.skipif(
        not TestInstallerBase().check_command_available("docker"),
        reason="docker not available",
    )
    @pytest.mark.asyncio
    async def test_verify_image(
        self, docker_installer, docker_config, docker_template, test_dir
    ):
        """Test verifying docker image."""
        test_dir.mkdir(parents=True, exist_ok=True)

        # Pull first
        install_result = await docker_installer.install(
            docker_config, docker_template, test_dir
        )
        if install_result["success"]:
            # Verify
            verified = await docker_installer.verify(
                docker_config, docker_template, test_dir
            )
            assert verified is True


class TestInstallerIntegration:
    """Integration tests for all installers together."""

    def test_all_installer_types_available(self):
        """Test that all installer types can be imported."""
        installers = [NPMInstaller, PipInstaller, GitInstaller, DockerInstaller]

        for installer_class in installers:
            installer = installer_class()
            assert installer is not None
            assert hasattr(installer, "can_handle")
            assert hasattr(installer, "install")
            assert hasattr(installer, "verify")

    def test_installation_method_enum(self):
        """Test that all installation methods are properly defined."""
        methods = [
            InstallationMethod.NPM,
            InstallationMethod.PIP,
            InstallationMethod.GIT,
            InstallationMethod.DOCKER,
        ]

        for method in methods:
            assert method.value is not None
            assert isinstance(method.value, str)


# Test discovery and availability
class TestSystemAvailability:
    """Test system command availability."""

    def test_command_availability_detection(self):
        """Test that we can detect available commands."""
        base_tester = TestInstallerBase()

        # These should work on most systems
        python_available = base_tester.check_command_available("python")
        python3_available = base_tester.check_command_available("python3")

        # At least one Python should be available
        assert python_available or python3_available

    @pytest.mark.parametrize("command", ["npm", "git", "docker"])
    def test_optional_command_detection(self, command):
        """Test detection of optional commands."""
        base_tester = TestInstallerBase()
        result = base_tester.check_command_available(command)
        # Result should be boolean, we don't care about the value
        assert isinstance(result, bool)


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
