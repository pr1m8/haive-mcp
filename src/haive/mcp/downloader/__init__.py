"""Module exports."""

from haive.mcp.downloader.config import (
    DiscoveryConfig,
    DownloaderConfig,
    InstallationMethod,
    ServerConfig,
    ServerTemplate,
    load_config,
    save_config,
)
from haive.mcp.downloader.core import (  # add_custom_server,; add_custom_template,; get_all_status,; get_server_status,; save_configuration,; servers,; templates,
    DownloadResult,
    GeneralMCPDownloader,
    ServerStatus,
)
from haive.mcp.downloader.discovery import (  # , determine_template
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
from haive.mcp.downloader.integration import (
    MCPAgentIntegration,
    MCPCapabilityExtractor,
    MCPServerConnection,
)
from haive.mcp.downloader.legacy_core import (
    GeneralMCPDownloader,
)

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
