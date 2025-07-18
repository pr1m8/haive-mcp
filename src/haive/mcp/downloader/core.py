"""Core MCP Downloader implementation.

This module provides the main GeneralMCPDownloader class that orchestrates
the downloading, installation, and configuration of MCP servers from various sources.

Example:
    Basic usage::

        downloader = GeneralMCPDownloader()
        result = await downloader.download_servers(["filesystem", "github"])

    Auto-discovery::

        result = await downloader.auto_discover_and_download(limit=10)

    Custom configuration::

        downloader = GeneralMCPDownloader(
            config_file="my_config.yaml",
            install_dir="/custom/path"
        )

Classes:
    GeneralMCPDownloader: Main downloader orchestrator
    DownloadResult: Result of download operations
    ServerStatus: Status tracking for servers

Version: 1.0.0
Author: Haive MCP Team
"""

import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import time
from typing import Any

from pydantic import BaseModel, Field

from haive.mcp.downloader.config import (
    DownloaderConfig,
    InstallationMethod,
    ServerConfig,
    ServerTemplate,
    load_config,
    save_config,
)
from haive.mcp.downloader.discovery import ServerDiscovery
from haive.mcp.downloader.installers import (
    BinaryInstaller,
    CurlInstaller,
    DockerInstaller,
    GitInstaller,
    MCPInstaller,
    NPMInstaller,
    PipInstaller,
)


logger = logging.getLogger(__name__)


class ServerStatus(BaseModel):
    """Status information for an MCP server.

    Attributes:
        name: Server name
        status: Current status (installed, failed, pending)
        last_check: Timestamp of last status check
        last_success: Timestamp of last successful operation
        install_result: Result of installation attempt
        health_status: Health check status
        error: Error message if failed

    Example:
        Creating status::

            status = ServerStatus(
                name="filesystem",
                status="installed",
                last_check=datetime.now(),
                last_success=datetime.now()
            )
    """

    name: str = Field(..., description="Server name")
    status: str = Field(default="pending", description="Current status")
    last_check: datetime | None = Field(None, description="Last check time")
    last_success: datetime | None = Field(None, description="Last success time")
    install_result: dict[str, Any] | None = Field(None, description="Install result")
    health_status: str | None = Field(None, description="Health status")
    error: str | None = Field(None, description="Error message")


class DownloadResult(BaseModel):
    """Result of a download operation.

    Attributes:
        total: Total servers attempted
        successful: Number of successful installations
        failed: Number of failed installations
        success_rate: Percentage success rate
        successful_servers: List of successful server details
        failed_servers: List of failed server details
        config_file: Path to generated configuration
        duration: Operation duration in seconds

    Example:
        Checking results::

            if result.success_rate > 80:
                print(f"Good success rate: {result.success_rate}%")
    """

    total: int = Field(..., description="Total servers")
    successful: int = Field(..., description="Successful installs")
    failed: int = Field(..., description="Failed installs")
    success_rate: float = Field(..., description="Success percentage")
    successful_servers: list[dict[str, Any]] = Field(default_factory=list)
    failed_servers: list[dict[str, Any]] = Field(default_factory=list)
    config_file: str | None = Field(None, description="Config file path")
    duration: float | None = Field(None, description="Duration in seconds")


class GeneralMCPDownloader:
    """General MCP Server Downloader with configurable patterns and installers.

    This is the main orchestrator class that manages the downloading, installation,
    and configuration of MCP servers from various sources using a plugin-based
    architecture.

    Attributes:
        config: Downloader configuration
        installers: List of available installers
        discovery: Server discovery instance
        status_tracker: Server status tracking

    Example:
        Creating and using downloader::

            downloader = GeneralMCPDownloader()

            # Download specific servers
            result = await downloader.download_servers(["filesystem", "github"])

            # Auto-discover and install
            result = await downloader.auto_discover_and_download(limit=10)

            # Check server health
            health = await downloader.check_server_health()

    Note:
        The downloader automatically creates necessary directories and
        default configuration if not provided.
    """

    def __init__(self, config_file: str | None = None, install_dir: str | None = None):
        """Initialize the General MCP Downloader.

        Args:
            config_file: Path to YAML configuration file. If not provided,
                creates a default configuration.
            install_dir: Directory for server installations. Defaults to
                ~/.mcp/servers if not specified.

        Example:
            Initialization::

                # Use defaults
                downloader = GeneralMCPDownloader()

                # Custom paths
                downloader = GeneralMCPDownloader(
                    config_file="/path/to/config.yaml",
                    install_dir="/custom/install/dir"
                )
        """
        # Load or create configuration
        if config_file and Path(config_file).exists():
            self.config = load_config(Path(config_file))
            logger.info(f"Loaded configuration from {config_file}")
        else:
            self.config = self._create_default_config()
            if config_file:
                save_config(self.config, Path(config_file))
                logger.info(f"Created default configuration at {config_file}")

        # Override install directory if provided
        if install_dir:
            self.config.install_dir = Path(install_dir)

        # Ensure directories exist
        self._ensure_directories()

        # Initialize components
        self.installers = self._initialize_installers()
        self.discovery = ServerDiscovery(self.config.discovery)
        self.status_tracker: dict[str, ServerStatus] = {}

        # Load existing status
        self._load_status()

        logger.info(
            f"Initialized downloader with {len(self.config.templates)} templates "
            f"and {len(self.config.servers)} servers"
        )

    def _create_default_config(self) -> DownloaderConfig:
        """Create default configuration with common templates.

        Returns:
            Default DownloaderConfig instance

        Note:
            This creates a sensible default configuration that covers
            the most common MCP server patterns.
        """
        from haive.mcp.downloader.config import (
            DiscoveryConfig,
            ServerConfig,
            ServerTemplate,
        )

        # Default templates
        templates = [
            ServerTemplate(
                name="npm_official",
                installation_method=InstallationMethod.NPM,
                command_pattern="@modelcontextprotocol/server-{service}",
                capabilities=["tools"],
                category="official",
                prerequisites=["node", "npm"],
            ),
            ServerTemplate(
                name="npm_community",
                installation_method=InstallationMethod.NPM,
                command_pattern="{package}",
                capabilities=["tools"],
                category="community",
                prerequisites=["node", "npm"],
            ),
            ServerTemplate(
                name="git_repo",
                installation_method=InstallationMethod.GIT,
                command_pattern="python server.py",
                post_install=["pip install -r requirements.txt"],
                capabilities=["tools"],
                category="development",
                prerequisites=["git", "python"],
            ),
            ServerTemplate(
                name="docker_image",
                installation_method=InstallationMethod.DOCKER,
                command_pattern="{image}",
                capabilities=["tools"],
                category="containerized",
                prerequisites=["docker"],
            ),
            ServerTemplate(
                name="pypi_package",
                installation_method=InstallationMethod.PIP,
                command_pattern="{package}",
                capabilities=["tools"],
                category="python",
                prerequisites=["python", "pip"],
            ),
        ]

        # Default servers
        servers = [
            ServerConfig(
                name="filesystem",
                template="npm_official",
                source="npm",
                variables={"service": "filesystem"},
                tags={"official", "file-operations", "core"},
            ),
            ServerConfig(
                name="github",
                template="npm_official",
                source="npm",
                variables={"service": "github"},
                tags={"official", "git", "development"},
            ),
            ServerConfig(
                name="sqlite",
                template="npm_official",
                source="npm",
                variables={"service": "sqlite"},
                tags={"official", "database", "sql"},
            ),
        ]

        # Discovery configuration
        discovery = DiscoveryConfig(
            sources=[
                "https://raw.githubusercontent.com/modelcontextprotocol/servers/main/README.md",
                "https://api.github.com/search/repositories?q=mcp+server+in:name&sort=stars",
                "https://registry.npmjs.org/-/v1/search?text=mcp+server",
            ],
            patterns={
                "npm": [
                    "@modelcontextprotocol/server-*",
                    "mcp-server-*",
                    "*-mcp-server",
                ],
                "pypi": ["mcp-*", "*-mcp", "mcp-server-*"],
                "docker": ["mcp/*", "modelcontextprotocol/*"],
                "github": ["*mcp*server*", "mcp-*"],
            },
        )

        return DownloaderConfig(
            templates=templates, servers=servers, discovery=discovery
        )

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist.

        Creates:
            - Installation directory
            - Configuration directory
            - Log directory
            - Backup directory (if enabled)
        """
        directories = [
            self.config.install_dir,
            self.config.config_dir,
            self.config.log_dir,
        ]

        if self.config.backup_enabled:
            directories.append(self.config.backup_dir)

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    def _initialize_installers(self) -> list[MCPInstaller]:
        """Initialize all available installers.

        Returns:
            List of installer instances

        Note:
            New installers can be added here as they are developed.
        """
        return [
            NPMInstaller(),
            PipInstaller(),
            GitInstaller(),
            DockerInstaller(),
            BinaryInstaller(),
            CurlInstaller(),
        ]

    def _load_status(self) -> None:
        """Load server status from persistent storage.

        Loads the status tracking information from the status file
        if it exists.
        """
        status_file = self.config.config_dir / "server_status.json"

        if status_file.exists():
            try:
                with open(status_file) as f:
                    data = json.load(f)

                for name, status_data in data.items():
                    # Convert timestamps
                    if status_data.get("last_check"):
                        status_data["last_check"] = datetime.fromisoformat(
                            status_data["last_check"]
                        )
                    if status_data.get("last_success"):
                        status_data["last_success"] = datetime.fromisoformat(
                            status_data["last_success"]
                        )

                    self.status_tracker[name] = ServerStatus(**status_data)

                logger.info(f"Loaded status for {len(self.status_tracker)} servers")

            except Exception as e:
                logger.error(f"Error loading status: {e}")

    def _save_status(self) -> None:
        """Save server status to persistent storage.

        Saves the current status tracking information to a JSON file
        for persistence across runs.
        """
        status_file = self.config.config_dir / "server_status.json"

        try:
            data = {}
            for name, status in self.status_tracker.items():
                status_dict = status.model_dump(mode="json")
                # Convert timestamps to ISO format
                if status.last_check:
                    status_dict["last_check"] = status.last_check.isoformat()
                if status.last_success:
                    status_dict["last_success"] = status.last_success.isoformat()
                data[name] = status_dict

            with open(status_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved status for {len(data)} servers")

        except Exception as e:
            logger.error(f"Error saving status: {e}")

    @property
    def templates(self) -> dict[str, ServerTemplate]:
        """Get templates as a dictionary.

        Returns:
            Dict mapping template names to ServerTemplate objects

        Example:
            Accessing templates::

                npm_template = downloader.templates["npm_official"]
                print(f"Command: {npm_template.command_pattern}")
        """
        return {t.name: t for t in self.config.templates}

    @property
    def servers(self) -> list[ServerConfig]:
        """Get list of server configurations.

        Returns:
            List of ServerConfig objects

        Example:
            Listing servers::

                for server in downloader.servers:
                    print(f"{server.name}: {server.template}")
        """
        return self.config.servers

    async def download_servers(
        self,
        server_names: list[str] | None = None,
        categories: list[str] | None = None,
        tags: set[str] | None = None,
        max_concurrent: int | None = None,
    ) -> DownloadResult:
        """Download and install MCP servers.

        This is the main method for downloading servers. It supports filtering
        by name, category, or tags, and handles concurrent downloads with
        retry logic.

        Args:
            server_names: Specific server names to download. If None,
                downloads all enabled servers.
            categories: Filter servers by category (e.g., "official", "community")
            tags: Filter servers by tags (e.g., {"database", "file-operations"})
            max_concurrent: Maximum concurrent downloads. Uses config default if None.

        Returns:
            DownloadResult with details of the operation

        Example:
            Download specific servers::

                result = await downloader.download_servers(["filesystem", "github"])
                print(f"Success rate: {result.success_rate}%")

            Download by category::

                result = await downloader.download_servers(categories=["official"])

            Download by tags::

                result = await downloader.download_servers(tags={"database", "sql"})

        Raises:
            ValueError: If no servers match the criteria
        """
        start_time = time.time()

        # Filter servers to download
        servers_to_download = self._filter_servers(server_names, categories, tags)

        if not servers_to_download:
            raise ValueError("No servers match the download criteria")

        logger.info(f"Downloading {len(servers_to_download)} servers...")

        # Use configured max concurrent if not specified
        if max_concurrent is None:
            max_concurrent = self.config.max_concurrent

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
        successful_servers = []
        failed_servers = []

        for i, result in enumerate(results):
            server = servers_to_download[i]

            if isinstance(result, Exception):
                failed_servers.append({"server": server.name, "error": str(result)})
                self._update_server_status(server.name, "failed", error=str(result))
            elif isinstance(result, dict) and result.get("success"):
                successful_servers.append({"server": server.name, "result": result})
                self._update_server_status(server.name, "installed", result=result)
            else:
                error = (
                    result.get("error", "Unknown error")
                    if isinstance(result, dict)
                    else "Unknown error"
                )
                failed_servers.append({"server": server.name, "error": error})
                self._update_server_status(server.name, "failed", error=error)

        # Save configuration
        config_file = await self._save_server_config(successful_servers)

        # Save status
        self._save_status()

        # Create result
        total = len(servers_to_download)
        successful = len(successful_servers)
        failed = len(failed_servers)

        result = DownloadResult(
            total=total,
            successful=successful,
            failed=failed,
            success_rate=(successful / total * 100) if total > 0 else 0,
            successful_servers=successful_servers,
            failed_servers=failed_servers,
            config_file=str(config_file),
            duration=time.time() - start_time,
        )

        logger.info(
            f"Download complete: {successful}/{total} successful ({result.success_rate:.1f}%)"
        )

        return result

    def _filter_servers(
        self,
        server_names: list[str] | None = None,
        categories: list[str] | None = None,
        tags: set[str] | None = None,
    ) -> list[ServerConfig]:
        """Filter servers based on criteria.

        Args:
            server_names: Specific server names
            categories: Categories to include
            tags: Tags to filter by

        Returns:
            List of filtered ServerConfig objects
        """
        filtered = []

        for server in self.config.servers:
            # Skip disabled servers
            if not server.enabled:
                continue

            # Filter by name
            if server_names and server.name not in server_names:
                continue

            # Filter by category
            if categories:
                template = self.templates.get(server.template)
                if not template or template.category not in categories:
                    continue

            # Filter by tags
            if tags and not server.tags.intersection(tags):
                continue

            filtered.append(server)

        return filtered

    async def _download_server_with_semaphore(
        self, semaphore: asyncio.Semaphore, server: ServerConfig
    ) -> dict[str, Any]:
        """Download a server with concurrency control.

        Args:
            semaphore: Asyncio semaphore for concurrency control
            server: Server configuration

        Returns:
            Download result dictionary
        """
        async with semaphore:
            return await self._download_server(server)

    async def _download_server(self, server: ServerConfig) -> dict[str, Any]:
        """Download and install a single MCP server.

        Args:
            server: Server configuration

        Returns:
            Result dictionary with success status and details
        """
        template = self.templates.get(server.template)
        if not template:
            return {"success": False, "error": f"Template {server.template} not found"}

        logger.info(f"Installing {server.name} using template {server.template}")

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

        # Attempt installation with retries
        last_error = None
        for attempt in range(self.config.retry_attempts):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt + 1} for {server.name}")
                await asyncio.sleep(self.config.retry_delay)

            try:
                result = await installer.install(
                    server, template, self.config.install_dir
                )

                if result.get("success"):
                    # Verify installation if health check enabled
                    if self.config.health_check_enabled:
                        verified = await self._verify_installation(
                            server, template, installer
                        )
                        result["verified"] = verified

                    return result
                last_error = result.get("error", "Installation failed")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Error installing {server.name}: {e}")

        return {"success": False, "error": last_error}

    async def _verify_installation(
        self, server: ServerConfig, template: ServerTemplate, installer: MCPInstaller
    ) -> bool:
        """Verify server installation with health check.

        Args:
            server: Server configuration
            template: Server template
            installer: Installer that was used

        Returns:
            True if verification successful
        """
        try:
            # Use installer's verify method
            verified = await asyncio.wait_for(
                installer.verify(server, template, self.config.install_dir),
                timeout=self.config.health_check_timeout,
            )

            if verified:
                logger.info(f"✓ Verified installation of {server.name}")
            else:
                logger.warning(f"⚠ Verification failed for {server.name}")

            return verified

        except TimeoutError:
            logger.warning(f"Health check timed out for {server.name}")
            return False
        except Exception as e:
            logger.error(f"Error verifying {server.name}: {e}")
            return False

    def _update_server_status(
        self,
        name: str,
        status: str,
        result: dict | None = None,
        error: str | None = None,
    ) -> None:
        """Update server status in tracker.

        Args:
            name: Server name
            status: New status
            result: Installation result if applicable
            error: Error message if failed
        """
        if name not in self.status_tracker:
            self.status_tracker[name] = ServerStatus(name=name)

        server_status = self.status_tracker[name]
        server_status.status = status
        server_status.last_check = datetime.now()

        if status == "installed" and result:
            server_status.last_success = datetime.now()
            server_status.install_result = result
            server_status.error = None
        elif error:
            server_status.error = error

    async def _save_server_config(
        self, successful_servers: list[dict[str, Any]]
    ) -> Path:
        """Save successful server configurations.

        Args:
            successful_servers: List of successfully installed servers

        Returns:
            Path to saved configuration file
        """
        config = {
            "mcpServers": {},
            "generated_at": datetime.now().isoformat(),
            "install_dir": str(self.config.install_dir),
            "downloader_version": "1.0.0",
        }

        for server_info in successful_servers:
            server_name = server_info["server"]
            server_result = server_info["result"]

            # Find server config
            server_config = next(
                (s for s in self.config.servers if s.name == server_name), None
            )
            if not server_config:
                continue

            # Find template
            template = self.templates.get(server_config.template)
            if not template:
                continue

            # Create MCP server configuration
            mcp_config = {
                "command": server_result.get("command", template.command_pattern),
                "args": template.args_pattern,
                "env": {**template.env_vars, **server_config.env_vars},
            }

            # Add transport-specific fields
            if server_result.get("method") == "docker":
                mcp_config["transport"] = "docker"
            else:
                mcp_config["transport"] = "stdio"

            config["mcpServers"][server_name] = mcp_config

        # Save configuration
        config_path = self.config.config_dir / "mcp_servers_config.json"

        # Backup existing config if enabled
        if self.config.backup_enabled and config_path.exists():
            backup_path = (
                self.config.backup_dir / f"mcp_servers_config_{int(time.time())}.json"
            )
            import shutil

            shutil.copy2(config_path, backup_path)
            logger.debug(f"Backed up config to {backup_path}")

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved configuration to {config_path}")
        return config_path

    async def auto_discover_and_download(
        self, limit: int | None = None, auto_install: bool = True
    ) -> DownloadResult:
        """Auto-discover servers from registries and optionally download them.

        This method discovers MCP servers from configured sources and can
        automatically install them.

        Args:
            limit: Maximum number of servers to discover per source
            auto_install: Whether to automatically install discovered servers

        Returns:
            DownloadResult with discovery and installation details

        Example:
            Auto-discover and install::

                result = await downloader.auto_discover_and_download(limit=20)
                print(f"Discovered and installed {result.successful} servers")

            Discover only::

                result = await downloader.auto_discover_and_download(
                    limit=50,
                    auto_install=False
                )
        """
        logger.info("Starting auto-discovery of MCP servers...")

        # Discover servers
        discovered_servers = await self.discovery.discover_all(limit_per_source=limit)

        logger.info(f"Discovered {len(discovered_servers)} unique servers")

        # Convert discovered servers to ServerConfig
        new_servers = []
        for server_data in discovered_servers:
            # Skip if already configured
            if any(s.name == server_data["name"] for s in self.config.servers):
                continue

            # Determine template based on source/type
            template_name = self.discovery.determine_template(server_data)
            if template_name not in self.templates:
                logger.warning(f"No template for {server_data['name']}, skipping")
                continue

            server = ServerConfig(
                name=server_data["name"],
                template=template_name,
                source=server_data.get("source", ""),
                variables=server_data.get("variables", {}),
                tags=set(server_data.get("tags", [])),
                enabled=True,
            )

            new_servers.append(server)
            self.config.servers.append(server)

        logger.info(f"Added {len(new_servers)} new servers to configuration")

        if auto_install and new_servers:
            # Download newly discovered servers
            server_names = [s.name for s in new_servers]
            return await self.download_servers(server_names)
        # Return discovery-only result
        return DownloadResult(
            total=len(new_servers),
            successful=len(new_servers),
            failed=0,
            success_rate=100.0,
            successful_servers=[{"server": s.name} for s in new_servers],
            failed_servers=[],
            duration=0,
        )

    async def check_server_health(
        self, server_names: list[str] | None = None
    ) -> dict[str, Any]:
        """Check health status of installed servers.

        Args:
            server_names: Specific servers to check. If None, checks all installed.

        Returns:
            Dict with health check results

        Example:
            Checking health::

                health = await downloader.check_server_health()
                for server, status in health["servers"].items():
                    print(f"{server}: {status}")
        """
        servers_to_check = []

        if server_names:
            servers_to_check = [
                s for s in self.config.servers if s.name in server_names
            ]
        else:
            # Check all installed servers
            servers_to_check = [
                s
                for s in self.config.servers
                if self.status_tracker.get(s.name, ServerStatus(name=s.name)).status
                == "installed"
            ]

        health_results = {}

        for server in servers_to_check:
            template = self.templates.get(server.template)
            if not template:
                continue

            # Find installer
            installer = None
            for inst in self.installers:
                if await inst.can_handle(server, template):
                    installer = inst
                    break

            if installer:
                try:
                    is_healthy = await installer.verify(
                        server, template, self.config.install_dir
                    )
                    health_results[server.name] = (
                        "healthy" if is_healthy else "unhealthy"
                    )

                    # Update status
                    if server.name in self.status_tracker:
                        self.status_tracker[server.name].health_status = health_results[
                            server.name
                        ]
                        self.status_tracker[server.name].last_check = datetime.now()

                except Exception as e:
                    health_results[server.name] = f"error: {e!s}"
                    logger.error(f"Health check failed for {server.name}: {e}")
            else:
                health_results[server.name] = "no_installer"

        # Save updated status
        self._save_status()

        # Calculate summary
        healthy = sum(1 for status in health_results.values() if status == "healthy")
        total = len(health_results)

        return {
            "servers": health_results,
            "summary": {
                "total_checked": total,
                "healthy": healthy,
                "unhealthy": total - healthy,
                "health_rate": (healthy / total * 100) if total > 0 else 0,
            },
        }

    def add_custom_server(self, server: ServerConfig) -> None:
        """Add a custom server configuration.

        Args:
            server: ServerConfig to add

        Example:
            Adding custom server::

                custom = ServerConfig(
                    name="my-custom-mcp",
                    template="git_repo",
                    source="https://github.com/user/my-mcp.git",
                    variables={"owner": "user", "repo": "my-mcp"}
                )
                downloader.add_custom_server(custom)
        """
        # Check for duplicates
        if any(s.name == server.name for s in self.config.servers):
            logger.warning(f"Server {server.name} already exists, updating")
            self.config.servers = [
                s if s.name != server.name else server for s in self.config.servers
            ]
        else:
            self.config.servers.append(server)
            logger.info(f"Added custom server: {server.name}")

    def add_custom_template(self, template: ServerTemplate) -> None:
        """Add a custom template.

        Args:
            template: ServerTemplate to add

        Example:
            Adding custom template::

                template = ServerTemplate(
                    name="rust_binary",
                    installation_method=InstallationMethod.BINARY,
                    command_pattern="./{service}-mcp",
                    category="rust"
                )
                downloader.add_custom_template(template)
        """
        # Check for duplicates
        existing_names = [t.name for t in self.config.templates]
        if template.name in existing_names:
            logger.warning(f"Template {template.name} already exists, updating")
            self.config.templates = [
                t if t.name != template.name else template
                for t in self.config.templates
            ]
        else:
            self.config.templates.append(template)
            logger.info(f"Added custom template: {template.name}")

    def get_server_status(self, server_name: str) -> ServerStatus | None:
        """Get status for a specific server.

        Args:
            server_name: Name of the server

        Returns:
            ServerStatus if found, None otherwise

        Example:
            Checking status::

                status = downloader.get_server_status("filesystem")
                if status and status.status == "installed":
                    print(f"Last success: {status.last_success}")
        """
        return self.status_tracker.get(server_name)

    def get_all_status(self) -> dict[str, ServerStatus]:
        """Get status for all servers.

        Returns:
            Dict mapping server names to ServerStatus objects
        """
        return self.status_tracker.copy()

    def save_configuration(self, config_file: Path) -> None:
        """Save current configuration to file.

        Args:
            config_file: Path to save configuration

        Example:
            Saving config::

                downloader.save_configuration(Path("my_config.yaml"))
        """
        save_config(self.config, config_file)
        logger.info(f"Saved configuration to {config_file}")
