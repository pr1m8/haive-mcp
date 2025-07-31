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
    Config,
    MCPAgentIntegration,
    MCPCapabilityExtractor,
    MCPServerConnection,
    get_all_prompts,
    get_all_resources,
    get_all_tools,
    get_capability_summary,
    get_tools_by_capability,
    get_tools_by_server,
)
from haive.mcp.downloader.legacy_core import (
    DockerInstaller,
    GeneralMCPDownloader,
    GitInstaller,
    InstallationMethod,
    MCPInstaller,
    NPMInstaller,
    PipInstaller,
    ServerConfig,
    ServerTemplate,
    create_default_config,
    load_config,
)

__all__ = [
    "BinaryInstaller",
    "Config",
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
    "create_default_config",
    "get_all_prompts",
    "get_all_resources",
    "get_all_tools",
    "get_capability_summary",
    "get_tools_by_capability",
    "get_tools_by_server",
    "load_config",
    "save_config",
]
