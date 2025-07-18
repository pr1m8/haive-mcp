"""MCP Downloader Package.

This package provides a general, extensible system for downloading and managing
Model Context Protocol (MCP) servers from any source.

Example:
    Basic usage::

        from haive.mcp.downloader import GeneralMCPDownloader

        downloader = GeneralMCPDownloader()
        result = await downloader.download_servers(["filesystem", "github"])

    Auto-discovery::

        result = await downloader.auto_discover_and_download(limit=10)

Modules:
    core: Core downloader with plugin architecture
    installers: Plugin installers for different methods
    config: Configuration models and validation
    discovery: Server discovery from multiple sources
    integration: Agent integration utilities

Version: 1.0.0
Author: Haive MCP Team
"""

from haive.mcp.downloader.config import (
    DownloaderConfig,
    InstallationMethod,
    ServerConfig,
    ServerTemplate,
)
from haive.mcp.downloader.core import GeneralMCPDownloader
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
from haive.mcp.downloader.integration import MCPAgentIntegration


__version__ = "1.0.0"
__all__ = [
    "BinaryInstaller",
    "CurlInstaller",
    "DockerInstaller",
    "DownloaderConfig",
    "GeneralMCPDownloader",
    "GitInstaller",
    "InstallationMethod",
    "MCPAgentIntegration",
    "MCPInstaller",
    "NPMInstaller",
    "PipInstaller",
    "ServerConfig",
    "ServerDiscovery",
    "ServerTemplate",
]
