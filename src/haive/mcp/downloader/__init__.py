"""MCP Server Downloader - Download, install, and manage MCP servers."""

from haive.mcp.downloader.config import (
    DiscoveryConfig,
    DownloaderConfig,
    InstallationMethod,
    ServerConfig,
    ServerTemplate,
    load_config,
    save_config,
)
from haive.mcp.downloader.core import (
    DownloadResult,
    GeneralMCPDownloader,
    ServerStatus,
)
from haive.mcp.downloader.discovery import (
    DiscoveredServer,
    ServerDiscovery,
)
from haive.mcp.downloader.github_mass_downloader import (
    GitHubMCPDownloader,
)
from haive.mcp.downloader.installers import (
    BinaryInstaller,
    CurlInstaller,
    DockerInstaller,
    GitInstaller,
    MCPInstaller,
    NPMInstaller,
    PipInstaller,
)

# Integration module depends on haive.core - import lazily
try:
    from haive.mcp.downloader.integration import (
        MCPAgentIntegration,
        MCPCapabilityExtractor,
        MCPServerConnection,
    )
except ImportError:
    MCPAgentIntegration = None
    MCPCapabilityExtractor = None
    MCPServerConnection = None

__all__ = [
    "BinaryInstaller",
    "CurlInstaller",
    "DiscoveredServer",
    "DiscoveryConfig",
    "DockerInstaller",
    "DownloadResult",
    "DownloaderConfig",
    "GeneralMCPDownloader",
    "GitHubMCPDownloader",
    "GitInstaller",
    "InstallationMethod",
    "MCPAgentIntegration",
    "MCPCapabilityExtractor",
    "MCPInstaller",
    "MCPServerConnection",
    "NPMInstaller",
    "PipInstaller",
    "ServerConfig",
    "ServerDiscovery",
    "ServerStatus",
    "ServerTemplate",
    "load_config",
    "save_config",
]
