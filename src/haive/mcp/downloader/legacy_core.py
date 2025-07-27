#!/usr/bin/env python3
"""General MCP Server Downloader - A flexible, configuration-driven approach

This script provides a general, extensible system for downloading and configuring
MCP servers from various sources using configurable installation strategies.

Key features:
- Plugin architecture for different installation methods
- Configuration-driven patterns and templates
- Support for multiple server registries and sources
- Flexible metadata handling
- Batch processing with retry logic
- Progress tracking and logging
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import yaml
except ImportError:
    yaml = None

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class InstallationMethod(Enum):
    """Supported installation methods"""

    NPM = "npm"
    PIP = "pip"
    GIT = "git"
    DOCKER = "docker"
    BINARY = "binary"
    CURL = "curl"
    MANUAL = "manual"
    SCRIPT = "script"


@dataclass
class ServerTemplate:
    """Template for MCP server configuration"""

    name: str
    installation_method: InstallationMethod
    command_pattern: str
    args_pattern: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    category: str = "general"
    health_check: str | None = None
    prerequisites: list[str] = field(default_factory=list)
    post_install: list[str] = field(default_factory=list)


@dataclass
class ServerConfig:
    """Configuration for a specific MCP server"""

    name: str
    template: str
    source: str
    variables: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    tags: set[str] = field(default_factory=set)


class MCPInstaller(ABC):
    """Abstract base class for MCP installers"""

    @abstractmethod
    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        """Check if this installer can handle the given configuration"""

    @abstractmethod
    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        """Install the MCP server"""

    @abstractmethod
    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        """Verify the installation was successful"""


class NPMInstaller(MCPInstaller):
    """Installer for NPM-based MCP servers"""

    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        return template.installation_method == InstallationMethod.NPM

    async def _run_command(
        self, cmd: list[str], cwd: Path | None = None, timeout: int = 300
    ) -> dict[str, Any]:
        """Run a command and return results"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
        except TimeoutError:
            process.kill()
            return {"returncode": -1, "error": "Command timed out"}

    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        package = template.command_pattern.format(**server_config.variables)

        # Try global install first, fallback to local
        for install_type in ["global", "local"]:
            try:
                cmd = ["npm", "install"]
                if install_type == "global":
                    cmd.append("-g")
                cmd.append(package)

                logger.info(f"Installing NPM package: {package} ({install_type})")
                result = await self._run_command(
                    cmd, cwd=install_dir if install_type == "local" else None
                )

                if result["returncode"] == 0:
                    return {
                        "method": "npm",
                        "package": package,
                        "install_type": install_type,
                        "command": (
                            f"npx {package}"
                            if install_type == "global"
                            else f"npm run {package}"
                        ),
                        "success": True,
                    }
            except Exception as e:
                logger.warning(f"NPM {install_type} install failed for {package}: {e}")
                continue

        return {"success": False, "error": "All NPM installation methods failed"}

    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        package = template.command_pattern.format(**server_config.variables)
        try:
            # Check if package is available
            result = await self._run_command(["npx", package, "--help"], timeout=10)
            return result["returncode"] == 0
        except:
            return False

    async def _run_command(
        self, cmd: list[str], cwd: Path | None = None, timeout: int = 300
    ) -> dict[str, Any]:
        """Run a command and return results"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
        except TimeoutError:
            process.kill()
            return {"returncode": -1, "error": "Command timed out"}


class PipInstaller(MCPInstaller):
    """Installer for Python/pip-based MCP servers"""

    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        return template.installation_method == InstallationMethod.PIP

    async def _run_command(self, cmd: list[str], timeout: int = 300) -> dict[str, Any]:
        """Run a command and return results"""
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
        except TimeoutError:
            process.kill()
            return {"returncode": -1, "error": "Command timed out"}

    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        package = template.command_pattern.format(**server_config.variables)

        try:
            cmd = ["pip", "install", package]
            logger.info(f"Installing pip package: {package}")
            result = await self._run_command(cmd)

            if result["returncode"] == 0:
                return {
                    "method": "pip",
                    "package": package,
                    "command": f"python -m {package.replace('-', '_')}",
                    "success": True,
                }
            return {"success": False, "error": result.get("stderr", "Unknown error")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        package = template.command_pattern.format(**server_config.variables)
        try:
            import importlib

            module_name = package.replace("-", "_")
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    async def _run_command(self, cmd: list[str], timeout: int = 300) -> dict[str, Any]:
        """Run a command and return results"""
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
        except TimeoutError:
            process.kill()
            return {"returncode": -1, "error": "Command timed out"}


class GitInstaller(MCPInstaller):
    """Installer for Git-based MCP servers"""

    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        return template.installation_method == InstallationMethod.GIT

    async def _run_command(
        self, cmd: list[str], cwd: Path | None = None, timeout: int = 300
    ) -> dict[str, Any]:
        """Run a command and return results"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
        except TimeoutError:
            process.kill()
            return {"returncode": -1, "error": "Command timed out"}

    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        repo_url = server_config.source
        repo_name = Path(urlparse(repo_url).path).stem
        clone_dir = install_dir / repo_name

        try:
            # Clone repository
            cmd = ["git", "clone", repo_url, str(clone_dir)]
            logger.info(f"Cloning repository: {repo_url}")
            result = await self._run_command(cmd)

            if result["returncode"] != 0:
                return {
                    "success": False,
                    "error": result.get("stderr", "Git clone failed"),
                }

            # Run post-install commands
            for post_cmd in template.post_install:
                formatted_cmd = post_cmd.format(**server_config.variables).split()
                await self._run_command(formatted_cmd, cwd=clone_dir)

            return {
                "method": "git",
                "repo_url": repo_url,
                "clone_dir": str(clone_dir),
                "command": template.command_pattern.format(**server_config.variables),
                "success": True,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        repo_url = server_config.source
        repo_name = Path(urlparse(repo_url).path).stem
        clone_dir = install_dir / repo_name
        return clone_dir.exists() and (clone_dir / ".git").exists()

    async def _run_command(
        self, cmd: list[str], cwd: Path | None = None, timeout: int = 300
    ) -> dict[str, Any]:
        """Run a command and return results"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
        except TimeoutError:
            process.kill()
            return {"returncode": -1, "error": "Command timed out"}


class DockerInstaller(MCPInstaller):
    """Installer for Docker-based MCP servers"""

    async def can_handle(
        self, server_config: ServerConfig, template: ServerTemplate
    ) -> bool:
        return template.installation_method == InstallationMethod.DOCKER

    async def _run_command(self, cmd: list[str], timeout: int = 300) -> dict[str, Any]:
        """Run a command and return results"""
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
        except TimeoutError:
            process.kill()
            return {"returncode": -1, "error": "Command timed out"}

    async def install(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> dict[str, Any]:
        image = template.command_pattern.format(**server_config.variables)

        try:
            # Pull Docker image
            cmd = ["docker", "pull", image]
            logger.info(f"Pulling Docker image: {image}")
            result = await self._run_command(cmd)

            if result["returncode"] == 0:
                return {
                    "method": "docker",
                    "image": image,
                    "command": f"docker run -it --rm {image}",
                    "success": True,
                }
            return {
                "success": False,
                "error": result.get("stderr", "Docker pull failed"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def verify(
        self, server_config: ServerConfig, template: ServerTemplate, install_dir: Path
    ) -> bool:
        image = template.command_pattern.format(**server_config.variables)
        try:
            result = await self._run_command(["docker", "image", "inspect", image])
            return result["returncode"] == 0
        except:
            return False

    async def _run_command(self, cmd: list[str], timeout: int = 300) -> dict[str, Any]:
        """Run a command and return results"""
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
        except TimeoutError:
            process.kill()
            return {"returncode": -1, "error": "Command timed out"}


class GeneralMCPDownloader:
    """General MCP Server Downloader with configurable patterns and installers"""

    def __init__(self, config_file: str | None = None, install_dir: str | None = None):
        self.config_file = config_file or "mcp_downloader_config.yaml"
        self.install_dir = Path(install_dir or Path.home() / ".mcp" / "servers")
        self.install_dir.mkdir(parents=True, exist_ok=True)

        # Initialize installers
        self.installers: list[MCPInstaller] = [
            NPMInstaller(),
            PipInstaller(),
            GitInstaller(),
            DockerInstaller(),
        ]

        # Load configuration
        self.templates: dict[str, ServerTemplate] = {}
        self.servers: list[ServerConfig] = []
        self.patterns: dict[str, Any] = {}

        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        config_path = Path(self.config_file)

        if not config_path.exists():
            logger.info(
                f"Config file {self.config_file} not found, creating default config"
            )
            self.create_default_config()
            return

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)

            # Load templates
            for template_data in config.get("templates", []):
                # Convert installation_method string to enum
                if "installation_method" in template_data and isinstance(
                    template_data["installation_method"], str
                ):
                    template_data["installation_method"] = InstallationMethod(
                        template_data["installation_method"]
                    )
                template = ServerTemplate(**template_data)
                self.templates[template.name] = template

            # Load server configurations
            for server_data in config.get("servers", []):
                server = ServerConfig(**server_data)
                self.servers.append(server)

            # Load patterns
            self.patterns = config.get("patterns", {})

            logger.info(
                f"Loaded {len(self.templates)} templates and {len(self.servers)} servers"
            )

        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.create_default_config()

    def create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            "templates": [
                {
                    "name": "npm_official",
                    "installation_method": "npm",
                    "command_pattern": "@modelcontextprotocol/server-{service}",
                    "capabilities": ["tools"],
                    "category": "official",
                },
                {
                    "name": "npm_community",
                    "installation_method": "npm",
                    "command_pattern": "{package}",
                    "capabilities": ["tools"],
                    "category": "community",
                },
                {
                    "name": "git_repo",
                    "installation_method": "git",
                    "command_pattern": "python server.py",
                    "post_install": ["pip install -r requirements.txt"],
                    "capabilities": ["tools"],
                    "category": "development",
                },
                {
                    "name": "docker_image",
                    "installation_method": "docker",
                    "command_pattern": "{image}",
                    "capabilities": ["tools"],
                    "category": "containerized",
                },
            ],
            "servers": [
                {
                    "name": "filesystem",
                    "template": "npm_official",
                    "source": "npm",
                    "variables": {"service": "filesystem"},
                    "enabled": True,
                    "tags": ["file", "official"],
                }
            ],
            "patterns": {
                "discovery_sources": [
                    "https://github.com/modelcontextprotocol/servers",
                    "https://raw.githubusercontent.com/modelcontextprotocol/servers/main/README.md",
                ],
                "package_patterns": {
                    "npm": [
                        "@modelcontextprotocol/server-*",
                        "mcp-server-*",
                        "*-mcp-server",
                    ],
                    "pypi": ["mcp-*", "*-mcp", "mcp-server-*"],
                },
            },
        }

        with open(self.config_file, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created default config file: {self.config_file}")
        self.load_config()

    async def discover_servers_from_registry(
        self, registry_url: str
    ) -> list[dict[str, Any]]:
        """Discover MCP servers from a registry or documentation source"""
        discovered = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(registry_url) as response:
                    if response.status == 200:
                        content = await response.text()

                        # Parse different registry formats
                        if registry_url.endswith(".json"):
                            data = json.loads(content)
                            discovered.extend(self._parse_json_registry(data))
                        elif registry_url.endswith(".md"):
                            discovered.extend(self._parse_markdown_registry(content))
                        else:
                            # Try to parse as GitHub API
                            discovered.extend(self._parse_github_api(content))

        except Exception as e:
            logger.error(f"Error discovering servers from {registry_url}: {e}")

        return discovered

    def _parse_json_registry(self, data: list | dict) -> list[dict[str, Any]]:
        """Parse JSON registry format"""
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "servers" in data:
            return data["servers"]
        return []

    def _parse_markdown_registry(self, content: str) -> list[dict[str, Any]]:
        """Parse markdown format with server links"""
        import re

        servers = []

        # Look for npm package patterns
        npm_pattern = r"npm\s+install\s+([^\s]+)"
        for match in re.finditer(npm_pattern, content):
            package = match.group(1)
            servers.append(
                {
                    "name": package.split("/")[-1].replace("server-", ""),
                    "template": "npm_community",
                    "source": "npm",
                    "variables": {"package": package},
                    "tags": ["npm", "discovered"],
                }
            )

        # Look for GitHub repository links
        github_pattern = r"https://github\.com/([^/]+)/([^/\s\)]+)"
        for match in re.finditer(github_pattern, content):
            owner, repo = match.groups()
            servers.append(
                {
                    "name": repo,
                    "template": "git_repo",
                    "source": f"https://github.com/{owner}/{repo}.git",
                    "variables": {"owner": owner, "repo": repo},
                    "tags": ["git", "github", "discovered"],
                }
            )

        return servers

    def _parse_github_api(self, content: str) -> list[dict[str, Any]]:
        """Parse GitHub API response"""
        try:
            data = json.loads(content)
            servers = []

            if isinstance(data, list):
                for repo in data:
                    if "mcp" in repo.get("name", "").lower():
                        servers.append(
                            {
                                "name": repo["name"],
                                "template": "git_repo",
                                "source": repo["clone_url"],
                                "variables": {
                                    "owner": repo["owner"]["login"],
                                    "repo": repo["name"],
                                },
                                "tags": ["git", "github", "discovered"],
                            }
                        )

            return servers
        except:
            return []

    async def download_servers(
        self,
        server_names: list[str] | None = None,
        categories: list[str] | None = None,
        max_concurrent: int = 5,
    ) -> dict[str, Any]:
        """Download and install MCP servers"""
        # Filter servers to download
        servers_to_download = []
        for server in self.servers:
            if not server.enabled:
                continue

            if server_names and server.name not in server_names:
                continue

            if categories:
                template = self.templates.get(server.template)
                if not template or template.category not in categories:
                    continue

            servers_to_download.append(server)

        if not servers_to_download:
            logger.warning("No servers selected for download")
            return {"success": False, "message": "No servers selected"}

        logger.info(f"Downloading {len(servers_to_download)} servers...")

        # Create semaphore for concurrent downloads
        semaphore = asyncio.Semaphore(max_concurrent)

        # Download servers concurrently
        tasks = []
        for server in servers_to_download:
            task = asyncio.create_task(
                self._download_server_with_semaphore(semaphore, server)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful = []
        failed = []

        for i, result in enumerate(results):
            server = servers_to_download[i]
            if isinstance(result, Exception):
                failed.append({"server": server.name, "error": str(result)})
            elif result.get("success"):
                successful.append({"server": server.name, "result": result})
            else:
                failed.append(
                    {
                        "server": server.name,
                        "error": result.get("error", "Unknown error"),
                    }
                )

        # Generate summary
        summary = {
            "total": len(servers_to_download),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(servers_to_download) * 100,
            "successful_servers": successful,
            "failed_servers": failed,
            "config_file": str(self.install_dir / "mcp_servers_config.json"),
        }

        # Save configuration
        await self._save_server_config(successful)

        return summary

    async def _download_server_with_semaphore(
        self, semaphore: asyncio.Semaphore, server: ServerConfig
    ) -> dict[str, Any]:
        """Download a server with concurrency control"""
        async with semaphore:
            return await self._download_server(server)

    async def _download_server(self, server: ServerConfig) -> dict[str, Any]:
        """Download and install a single MCP server"""
        template = self.templates.get(server.template)
        if not template:
            return {"success": False, "error": f"Template {server.template} not found"}

        logger.info(
            f"Installing server: {server.name} using template: {server.template}"
        )

        # Find appropriate installer
        installer = None
        for inst in self.installers:
            if await inst.can_handle(server, template):
                installer = inst
                break

        if not installer:
            return {
                "success": False,
                "error": f"No installer found for {template.installation_method}",
            }

        # Install the server
        result = await installer.install(server, template, self.install_dir)

        if result.get("success"):
            # Verify installation
            if await installer.verify(server, template, self.install_dir):
                logger.info(f"Successfully installed and verified: {server.name}")
                result["verified"] = True
            else:
                logger.warning(
                    f"Installation succeeded but verification failed: {server.name}"
                )
                result["verified"] = False

        return result

    async def _save_server_config(self, successful_servers: list[dict[str, Any]]):
        """Save successful server configurations to a file"""
        config = {
            "mcpServers": {},
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "install_dir": str(self.install_dir),
        }

        for server_info in successful_servers:
            server_name = server_info["server"]
            server_result = server_info["result"]

            # Find the original server config
            server_config = next(
                (s for s in self.servers if s.name == server_name), None
            )
            if not server_config:
                continue

            template = self.templates.get(server_config.template)
            if not template:
                continue

            # Create MCP server configuration
            mcp_config = {
                "command": server_result.get("command", template.command_pattern),
                "args": template.args_pattern,
                "env": template.env_vars.copy(),
            }

            # Add any environment variables from server config
            if hasattr(server_config, "env_vars"):
                mcp_config["env"].update(server_config.env_vars)

            config["mcpServers"][server_name] = mcp_config

        # Save configuration
        config_path = self.install_dir / "mcp_servers_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved server configuration to: {config_path}")

    async def auto_discover_and_download(
        self, limit: int | None = None
    ) -> dict[str, Any]:
        """Auto-discover servers from registries and download them"""
        logger.info("Starting auto-discovery of MCP servers...")

        discovered_servers = []

        # Discover from configured sources
        for source in self.patterns.get("discovery_sources", []):
            servers = await self.discover_servers_from_registry(source)
            discovered_servers.extend(servers)

        # Remove duplicates and limit
        unique_servers = {}
        for server in discovered_servers:
            name = server.get("name")
            if name and name not in unique_servers:
                unique_servers[name] = server

        discovered_list = list(unique_servers.values())
        if limit:
            discovered_list = discovered_list[:limit]

        logger.info(f"Discovered {len(discovered_list)} unique servers")

        # Add discovered servers to configuration
        for server_data in discovered_list:
            server = ServerConfig(**server_data)
            if server.name not in [s.name for s in self.servers]:
                self.servers.append(server)

        # Download discovered servers
        return await self.download_servers()


async def main():
    """Main function for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description="General MCP Server Downloader")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--install-dir", help="Installation directory")
    parser.add_argument("--servers", nargs="+", help="Specific servers to download")
    parser.add_argument("--categories", nargs="+", help="Server categories to download")
    parser.add_argument(
        "--auto-discover", action="store_true", help="Auto-discover servers"
    )
    parser.add_argument("--limit", type=int, help="Limit number of servers to download")
    parser.add_argument(
        "--max-concurrent", type=int, default=5, help="Max concurrent downloads"
    )

    args = parser.parse_args()

    # Create downloader
    downloader = GeneralMCPDownloader(
        config_file=args.config, install_dir=args.install_dir
    )

    # Run download process
    if args.auto_discover:
        result = await downloader.auto_discover_and_download(limit=args.limit)
    else:
        result = await downloader.download_servers(
            server_names=args.servers,
            categories=args.categories,
            max_concurrent=args.max_concurrent,
        )

    # Print results
    print("\n" + "=" * 60)
    print("📦 MCP SERVER DOWNLOAD RESULTS")
    print("=" * 60)
    print(f"Total servers: {result['total']}")
    print(f"Successful: {result['successful']} ({result['success_rate']:.1f}%)")
    print(f"Failed: {result['failed']}")

    if result["successful_servers"]:
        print("\n✅ Successful installations:")
        for server in result["successful_servers"]:
            print(f"  - {server['server']}")

    if result["failed_servers"]:
        print("\n❌ Failed installations:")
        for server in result["failed_servers"]:
            print(f"  - {server['server']}: {server['error']}")

    print(f"\n📋 Configuration saved to: {result['config_file']}")


if __name__ == "__main__":
    asyncio.run(main())
