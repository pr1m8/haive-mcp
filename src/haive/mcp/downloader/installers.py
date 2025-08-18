"""Installer plugins for different MCP server types.

This module provides installer implementations for various installation methods
including NPM, pip, Git, Docker, binary downloads, and more.

Examples:
    Using installers directly:

        .. code-block:: python
        installer = NPMInstaller()
        if await installer.can_handle(server_config, template):
            result = await installer.install(server_config, template, install_dir)

Classes:
    MCPInstaller: Abstract base class for installers
    NPMInstaller: Handles NPM package installations
    PipInstaller: Handles Python pip installations
    GitInstaller: Handles Git repository cloning
    DockerInstaller: Handles Docker image pulling
    BinaryInstaller: Handles binary executable downloads
    CurlInstaller: Handles direct HTTP downloads

Version: 1.0.0
Author: Haive MCP Team
"""

import asyncio
import json
import logging
import os
import shlex
import shutil
import stat
import tarfile
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp

from haive.mcp.downloader.config import InstallationMethod, ServerConfig, ServerTemplate

logger = logging.getLogger(__name__)


class MCPInstaller(ABC):
    """Abstract base class for MCP installers.

    All installer implementations must inherit from this class and implement
    the required methods.

    Examples:
        Creating a custom installer:

        .. code-block:: python
            class MyInstaller(MCPInstaller):
                async def can_handle(self, server_config, template):
                    return template.installation_method == "custom"

                async def install(self, server_config, template, install_dir):
                    # Custom installation logic
                    return {"success": True}

                async def verify(self, server_config, template, install_dir):
                    # Verification logic
                    return True
    """

    @abstractmethod
    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        """Check if this installer can handle the given configuration.

        Args:
            server_config: Server configuration
            template: Server template

        Returns:
            True if this installer can handle the installation
        """

    @abstractmethod
    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        """Install the MCP server.

        Args:
            server_config: Server configuration
            template: Server template
            install_dir: Installation directory

        Returns:
            Dict with installation results including success status
        """

    @abstractmethod
    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        """Verify the installation was successful.

        Args:
            server_config: Server configuration
            template: Server template
            install_dir: Installation directory

        Returns:
            True if installation is verified
        """

    async def _run_command(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 300,
    ) -> dict[str, Any]:
        """Run a command and return results.

        Args:
            cmd: Command and arguments
            cwd: Working directory
            env: Environment variables
            timeout: Command timeout in seconds

        Returns:
            Dict with returncode, stdout, and stderr
        """
        # Merge environment variables
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=cmd_env,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }

        except TimeoutError:
            if process:
                process.kill()
                await process.wait()
            return {
                "returncode": -1,
                "error": f"Command timed out after {timeout} seconds",
            }
        except Exception as e:
            return {"returncode": -1, "error": str(e)}


class NPMInstaller(MCPInstaller):
    """Installer for NPM-based MCP servers.

    Handles installation of MCP servers distributed as NPM packages.
    Supports both global and local installations.

    Examples:
        NPM installation:

        .. code-block:: python
            installer = NPMInstaller()
            result = await installer.install(
                server_config,
                template,
                Path("/home/user/.mcp/servers")
            )
    """

    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        """Check if this is an NPM installation.

        Returns:
            True if template uses NPM installation method
        """
        return template.installation_method == InstallationMethod.NPM

    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        """Install NPM package.

        Attempts global installation first, falls back to local if that fails.

        Args:
            server_config: Server configuration
            template: Server template
            install_dir: Installation directory

        Returns:
            Installation result dictionary
        """
        # Format package name
        package = template.command_pattern.format(**server_config.variables)

        # Check for version constraint
        if server_config.version:
            package = f"{package}@{server_config.version}"

        logger.info(f"Installing NPM package: {package}")

        # Try global install first
        cmd = ["npm", "install", "-g", package]
        result = await self._run_command(cmd, timeout=template.timeout)

        if result["returncode"] == 0:
            return {
                "success": True,
                "method": "npm",
                "package": package,
                "install_type": "global",
                "command": f"npx {package}",
                "args": template.args_pattern,
            }

        # Try local install as fallback
        logger.info(f"Global install failed, trying local install for {package}")

        # Create package directory
        package_dir = install_dir / server_config.name
        package_dir.mkdir(parents=True, exist_ok=True)

        # Create minimal package.json
        package_json = {
            "name": f"mcp-{server_config.name}",
            "version": "1.0.0",
            "dependencies": {package.split("@")[0]: server_config.version or "latest"},
        }

        with open(package_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)

        # Install locally
        cmd = ["npm", "install"]
        result = await self._run_command(cmd, cwd=package_dir, timeout=template.timeout)

        if result["returncode"] == 0:
            # Find the executable
            node_modules = package_dir / "node_modules" / ".bin"
            executables = list(node_modules.glob("*")) if node_modules.exists() else []

            command = str(executables[0]) if executables else f"npm run {package}"

            return {
                "success": True,
                "method": "npm",
                "package": package,
                "install_type": "local",
                "install_dir": str(package_dir),
                "command": command,
                "args": template.args_pattern,
            }

        return {
            "success": False,
            "error": f"NPM installation failed: {result.get('stderr', 'Unknown error')}",
        }

    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        """Verify NPM installation.

        Checks if the package is accessible via npx.

        Returns:
            True if package is installed and accessible
        """
        package = template.command_pattern.format(**server_config.variables)

        # Try to run help command
        cmd = ["npx", package, "--help"]
        result = await self._run_command(cmd, timeout=10)

        # Some packages might not have --help, so just check if it runs
        return result["returncode"] in [0, 1]


class PipInstaller(MCPInstaller):
    """Installer for Python pip-based MCP servers.

    Handles installation of MCP servers distributed as Python packages.

    Examples:
        Pip installation:

        .. code-block:: python
            installer = PipInstaller()
            result = await installer.install(
                server_config,
                template,
                install_dir
            )
    """

    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        """Check if this is a pip installation."""
        return template.installation_method == InstallationMethod.PIP

    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        """Install Python package via pip.

        Args:
            server_config: Server configuration
            template: Server template
            install_dir: Installation directory

        Returns:
            Installation result dictionary
        """
        package = template.command_pattern.format(**server_config.variables)

        # Add version if specified
        if server_config.version:
            package = f"{package}=={server_config.version}"

        logger.info(f"Installing pip package: {package}")

        # Install with pip
        cmd = ["pip", "install", package]
        result = await self._run_command(cmd, timeout=template.timeout)

        if result["returncode"] == 0:
            # Determine module name (replace hyphens with underscores)
            module_name = package.split("==")[0].split("[")[0].replace("-", "_")

            return {
                "success": True,
                "method": "pip",
                "package": package,
                "module": module_name,
                "command": f"python -m {module_name}",
                "args": template.args_pattern,
            }

        return {
            "success": False,
            "error": f"Pip installation failed: {result.get('stderr', 'Unknown error')}",
        }

    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        """Verify pip installation.

        Checks if the module can be imported.

        Returns:
            True if module is installed and importable
        """
        package = template.command_pattern.format(**server_config.variables)
        module_name = package.split("==")[0].split("[")[0].replace("-", "_")

        # Try to import the module
        cmd = ["python", "-c", f"import {module_name}"]
        result = await self._run_command(cmd, timeout=10)

        return result["returncode"] == 0


class GitInstaller(MCPInstaller):
    """Installer for Git repository-based MCP servers.

    Handles cloning Git repositories and running post-install commands.

    Examples:
        Git installation:

        .. code-block:: python
            installer = GitInstaller()
            result = await installer.install(
                server_config,
                template,
                install_dir
            )
    """

    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        """Check if this is a Git installation."""
        return template.installation_method == InstallationMethod.GIT

    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        """Clone Git repository and run post-install commands.

        Args:
            server_config: Server configuration
            template: Server template
            install_dir: Installation directory

        Returns:
            Installation result dictionary
        """
        repo_url = server_config.source

        # Parse repository name
        parsed = urlparse(repo_url)
        Path(parsed.path).stem.replace(".git", "")

        # Use server name as directory name
        clone_dir = install_dir / server_config.name

        logger.info(f"Cloning repository: {repo_url} to {clone_dir}")

        # Remove existing directory if it exists
        if clone_dir.exists():
            shutil.rmtree(clone_dir)

        # Clone repository
        cmd = ["git", "clone", repo_url, str(clone_dir)]

        # Add branch/tag if version specified
        if server_config.version:
            cmd.extend(["--branch", server_config.version])

        result = await self._run_command(cmd, timeout=template.timeout)

        if result["returncode"] != 0:
            return {
                "success": False,
                "error": f"Git clone failed: {result.get('stderr', 'Unknown error')}",
            }

        # Run post-install commands
        for post_cmd in template.post_install:
            formatted_cmd = post_cmd.format(**server_config.variables)
            logger.info(f"Running post-install: {formatted_cmd}")

            # Split command properly (handle quoted arguments)

            cmd_parts = shlex.split(formatted_cmd)

            result = await self._run_command(
                cmd_parts,
                cwd=clone_dir,
                env=server_config.env_vars,
                timeout=template.timeout,
            )

            if result["returncode"] != 0:
                logger.warning(f"Post-install command failed: {formatted_cmd}")

        # Format command
        command = template.command_pattern.format(**server_config.variables)

        # Make command absolute path if it's a relative path
        if not command.startswith("/"):
            command = str(clone_dir / command)

        return {
            "success": True,
            "method": "git",
            "repo_url": repo_url,
            "clone_dir": str(clone_dir),
            "command": command,
            "args": template.args_pattern,
            "cwd": str(clone_dir),
        }

    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        """Verify Git installation.

        Checks if the repository was cloned successfully.

        Returns:
            True if repository exists with .git directory
        """
        clone_dir = install_dir / server_config.name
        return clone_dir.exists() and (clone_dir / ".git").exists()


class DockerInstaller(MCPInstaller):
    """Installer for Docker-based MCP servers.

    Handles pulling Docker images for containerized MCP servers.

    Examples:
        Docker installation:

        .. code-block:: python
            installer = DockerInstaller()
            result = await installer.install(
                server_config,
                template,
                install_dir
            )
    """

    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        """Check if this is a Docker installation."""
        return template.installation_method == InstallationMethod.DOCKER

    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        """Pull Docker image.

        Args:
            server_config: Server configuration
            template: Server template
            install_dir: Installation directory

        Returns:
            Installation result dictionary
        """
        image = template.command_pattern.format(**server_config.variables)

        # Add tag if version specified
        if server_config.version and ":" not in image:
            image = f"{image}:{server_config.version}"

        logger.info(f"Pulling Docker image: {image}")

        # Pull the image
        cmd = ["docker", "pull", image]
        result = await self._run_command(cmd, timeout=template.timeout)

        if result["returncode"] == 0:
            # Create run command
            docker_cmd = ["docker", "run", "--rm", "-it"]

            # Add environment variables
            for key, value in server_config.env_vars.items():
                docker_cmd.extend(["-e", f"{key}={value}"])

            # Add image
            docker_cmd.append(image)

            return {
                "success": True,
                "method": "docker",
                "image": image,
                "command": "docker",
                "args": docker_cmd[1:],  # Skip 'docker' itself
                "transport": "docker",
            }

        return {
            "success": False,
            "error": f"Docker pull failed: {result.get('stderr', 'Unknown error')}",
        }

    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        """Verify Docker installation.

        Checks if the Docker image exists locally.

        Returns:
            True if image is available
        """
        image = template.command_pattern.format(**server_config.variables)

        if server_config.version and ":" not in image:
            image = f"{image}:{server_config.version}"

        # Check if image exists
        cmd = ["docker", "image", "inspect", image]
        result = await self._run_command(cmd, timeout=10)

        return result["returncode"] == 0


class BinaryInstaller(MCPInstaller):
    """Installer for binary executable MCP servers.

    Downloads and installs pre-compiled binary executables.

    Examples:
        Binary installation:

        .. code-block:: python
            installer = BinaryInstaller()
            result = await installer.install(
                server_config,
                template,
                install_dir
            )
    """

    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        """Check if this is a binary installation."""
        return template.installation_method == InstallationMethod.BINARY

    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        """Download and install binary executable.

        Args:
            server_config: Server configuration
            template: Server template
            install_dir: Installation directory

        Returns:
            Installation result dictionary
        """
        download_url = server_config.source

        if not download_url:
            return {"success": False, "error": "No download URL provided for binary"}

        # Create server directory
        server_dir = install_dir / server_config.name
        server_dir.mkdir(parents=True, exist_ok=True)

        # Determine binary name
        binary_name = template.command_pattern.format(**server_config.variables)
        if binary_name.startswith("./"):
            binary_name = binary_name[2:]

        binary_path = server_dir / binary_name

        logger.info(f"Downloading binary from: {download_url}")

        try:
            # Download binary
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status != 200:
                        return {
                            "success": False,
                            "error": f"Download failed with status {response.status}",
                        }

                    # Save binary
                    with open(binary_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

            # Make executable
            st = os.stat(binary_path)
            os.chmod(binary_path, st.st_mode | stat.S_IEXEC)

            logger.info(f"Binary downloaded and made executable: {binary_path}")

            # Run post-install commands
            for post_cmd in template.post_install:
                formatted_cmd = post_cmd.format(
                    **server_config.variables, binary_path=str(binary_path)
                )

                cmd_parts = shlex.split(formatted_cmd)

                await self._run_command(
                    cmd_parts, cwd=server_dir, timeout=template.timeout
                )

            return {
                "success": True,
                "method": "binary",
                "binary_path": str(binary_path),
                "command": str(binary_path),
                "args": template.args_pattern,
                "cwd": str(server_dir),
            }

        except Exception as e:
            return {"success": False, "error": f"Binary installation failed: {e!s}"}

    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        """Verify binary installation.

        Checks if the binary exists and is executable.

        Returns:
            True if binary exists and is executable
        """
        server_dir = install_dir / server_config.name
        binary_name = template.command_pattern.format(**server_config.variables)
        if binary_name.startswith("./"):
            binary_name = binary_name[2:]

        binary_path = server_dir / binary_name

        if not binary_path.exists():
            return False

        # Check if executable
        return os.access(binary_path, os.X_OK)


class CurlInstaller(MCPInstaller):
    """Installer for direct HTTP downloads.

    Downloads files directly via HTTP/HTTPS without package managers.

    Examples:
        Curl installation:

        .. code-block:: python
            installer = CurlInstaller()
            result = await installer.install(
                server_config,
                template,
                install_dir
            )
    """

    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        """Check if this is a curl/HTTP download."""
        return template.installation_method == InstallationMethod.CURL

    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        """Download files via HTTP.

        Args:
            server_config: Server configuration
            template: Server template
            install_dir: Installation directory

        Returns:
            Installation result dictionary
        """
        download_url = server_config.source

        if not download_url:
            return {"success": False, "error": "No download URL provided"}

        # Create server directory
        server_dir = install_dir / server_config.name
        server_dir.mkdir(parents=True, exist_ok=True)

        # Determine filename
        filename = server_config.variables.get(
            "filename", Path(urlparse(download_url).path).name or "download"
        )

        file_path = server_dir / filename

        logger.info(f"Downloading from: {download_url} to {file_path}")

        try:
            # Download file
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status != 200:
                        return {
                            "success": False,
                            "error": f"Download failed with status {response.status}",
                        }

                    # Save file
                    with open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

            logger.info(f"File downloaded: {file_path}")

            # Extract if needed
            if filename.endswith((".tar.gz", ".tgz", ".zip")):
                await self._extract_archive(file_path, server_dir)

            # Run post-install commands
            for post_cmd in template.post_install:
                formatted_cmd = post_cmd.format(
                    **server_config.variables, download_dir=str(server_dir)
                )

                cmd_parts = shlex.split(formatted_cmd)

                await self._run_command(
                    cmd_parts, cwd=server_dir, timeout=template.timeout
                )

            # Format command
            command = template.command_pattern.format(
                **server_config.variables, download_dir=str(server_dir)
            )

            if not command.startswith("/"):
                command = str(server_dir / command)

            return {
                "success": True,
                "method": "curl",
                "download_url": download_url,
                "file_path": str(file_path),
                "command": command,
                "args": template.args_pattern,
                "cwd": str(server_dir),
            }

        except Exception as e:
            return {"success": False, "error": f"Download failed: {e!s}"}

    async def _extract_archive(self, archive_path: Path, extract_dir: Path) -> None:
        """Extract compressed archive.

        Args:
            archive_path: Path to archive file
            extract_dir: Directory to extract to
        """
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
        else:
            # Handle tar archives

            with tarfile.open(archive_path, "r:*") as tar_ref:
                tar_ref.extractall(extract_dir)

        logger.info(f"Extracted archive: {archive_path}")

    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        """Verify curl installation.

        Checks if the expected files exist.

        Returns:
            True if installation directory exists with files
        """
        server_dir = install_dir / server_config.name

        if not server_dir.exists():
            return False

        # Check if directory has files
        return any(server_dir.iterdir())
