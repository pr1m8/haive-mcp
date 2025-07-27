# API Reference

## Core Classes

### GeneralMCPDownloader

Main class for downloading and managing MCP servers.

```python
class GeneralMCPDownloader:
    """General MCP Server Downloader with configurable patterns and installers.

    This class provides a flexible, configuration-driven approach to downloading
    and installing MCP servers from various sources.

    Args:
        config_file: Path to configuration file (default: 'mcp_downloader_config.yaml')
        install_dir: Directory for installations (default: ~/.mcp/servers)

    Attributes:
        templates: Dictionary of server templates
        servers: List of configured servers
        patterns: Discovery patterns and sources
        installers: List of available installer plugins
    """
```

#### Methods

##### `__init__(config_file: Optional[str] = None, install_dir: Optional[str] = None)`

Initialize the downloader with configuration.

##### `async download_servers(server_names: Optional[List[str]] = None, categories: Optional[List[str]] = None, max_concurrent: int = 5) -> Dict[str, Any]`

Download and install MCP servers.

```python
# Download specific servers
result = await downloader.download_servers(["filesystem", "github"])

# Download by category
result = await downloader.download_servers(categories=["official"])

# Download all enabled servers
result = await downloader.download_servers()
```

**Returns:**

```python
{
    "total": 10,
    "successful": 8,
    "failed": 2,
    "success_rate": 80.0,
    "successful_servers": [...],
    "failed_servers": [...],
    "config_file": "/path/to/config.json"
}
```

##### `async discover_servers_from_registry(registry_url: str) -> List[Dict[str, Any]]`

Discover servers from a registry or documentation source.

```python
servers = await downloader.discover_servers_from_registry(
    "https://registry.npmjs.org/-/v1/search?text=mcp-server"
)
```

##### `async auto_discover_and_download(limit: Optional[int] = None) -> Dict[str, Any]`

Automatically discover and download servers.

```python
# Discover and download up to 50 servers
result = await downloader.auto_discover_and_download(limit=50)
```

### ServerConfig

Configuration for individual MCP servers.

```python
@dataclass
class ServerConfig:
    """Configuration for a specific MCP server.

    Attributes:
        name: Unique server identifier
        template: Template name to use
        source: Source URL or package name
        variables: Template variables
        enabled: Whether server is enabled
        priority: Priority for installation order
        tags: Set of tags for categorization
    """
    name: str
    template: str
    source: str
    variables: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    tags: Set[str] = field(default_factory=set)
```

### ServerTemplate

Reusable template for server configurations.

```python
@dataclass
class ServerTemplate:
    """Template for MCP server configuration.

    Attributes:
        name: Template identifier
        installation_method: Method to use (npm, pip, git, docker, etc.)
        command_pattern: Command pattern with {variables}
        args_pattern: Argument pattern list
        env_vars: Environment variables
        capabilities: Server capabilities
        category: Server category
        health_check: Health check command
        prerequisites: Required dependencies
        post_install: Post-installation commands
    """
    name: str
    installation_method: InstallationMethod
    command_pattern: str
    args_pattern: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    category: str = "general"
    health_check: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    post_install: List[str] = field(default_factory=list)
```

## Installer Plugins

### MCPInstaller (Abstract Base)

Base class for all installer plugins.

```python
class MCPInstaller(ABC):
    """Abstract base class for MCP installers."""

    @abstractmethod
    async def can_handle(self, server_config: ServerConfig,
                        template: ServerTemplate) -> bool:
        """Check if this installer can handle the given configuration."""

    @abstractmethod
    async def install(self, server_config: ServerConfig,
                     template: ServerTemplate,
                     install_dir: Path) -> Dict[str, Any]:
        """Install the MCP server."""

    @abstractmethod
    async def verify(self, server_config: ServerConfig,
                    template: ServerTemplate,
                    install_dir: Path) -> bool:
        """Verify the installation was successful."""
```

### NPMInstaller

Installer for npm-based MCP servers.

```python
class NPMInstaller(MCPInstaller):
    """Installer for NPM-based MCP servers.

    Handles installation of MCP servers distributed via npm.
    Supports both global and local installation methods.
    """
```

### PipInstaller

Installer for Python/pip-based servers.

```python
class PipInstaller(MCPInstaller):
    """Installer for Python/pip-based MCP servers.

    Handles installation of MCP servers distributed via PyPI.
    """
```

### GitInstaller

Installer for Git repository-based servers.

```python
class GitInstaller(MCPInstaller):
    """Installer for Git-based MCP servers.

    Clones repositories and runs post-installation commands.
    """
```

### DockerInstaller

Installer for Docker-based servers.

```python
class DockerInstaller(MCPInstaller):
    """Installer for Docker-based MCP servers.

    Pulls Docker images for containerized MCP servers.
    """
```

## CLI Interface

### Main Commands

#### download

Download and install MCP servers.

```bash
python scripts/download_servers.py download [OPTIONS]

Options:
  -c, --config TEXT           Configuration file path
  -s, --servers TEXT          Specific servers to download (multiple)
  -cat, --category TEXT       Server categories to download (multiple)
  --all                       Download all configured servers
  -m, --max-concurrent INT    Maximum concurrent downloads
  -o, --output-dir TEXT       Output directory for installations
```

#### discover

Discover MCP servers from registries.

```bash
python scripts/download_servers.py discover [OPTIONS]

Options:
  -s, --source TEXT    Discovery source URL or registry
  -l, --limit INT      Limit number of servers to discover
  -o, --output TEXT    Output file for discovered servers
```

#### list

List available MCP servers.

```bash
python scripts/download_servers.py list [OPTIONS]

Options:
  --npm         List npm packages
  --pypi        List PyPI packages
  --github      List GitHub repositories
  --installed   List installed servers
```

#### status

Show status of installed servers.

```bash
python scripts/download_servers.py status [OPTIONS]

Options:
  --json    Output as JSON
```

### Management Commands

#### test

Test connection to an MCP server.

```bash
python scripts/manage_servers.py test SERVER_NAME [OPTIONS]

Options:
  -t, --timeout INT    Connection timeout in seconds
```

#### logs

View logs for an MCP server.

```bash
python scripts/manage_servers.py logs SERVER_NAME [OPTIONS]

Options:
  -n, --lines INT    Number of log lines to show
  -f, --follow       Follow log output
```

#### health

Check health status of servers.

```bash
python scripts/manage_servers.py health [OPTIONS]

Options:
  --all    Test all servers
```

## Async/Await Usage

All download and discovery operations are asynchronous:

```python
import asyncio
from general_mcp_downloader import GeneralMCPDownloader

async def main():
    downloader = GeneralMCPDownloader()

    # Download servers
    result = await downloader.download_servers(["filesystem"])

    # Discover servers
    servers = await downloader.discover_servers_from_registry(
        "https://registry.npmjs.org/-/v1/search?text=mcp"
    )

    # Auto-discover and download
    result = await downloader.auto_discover_and_download(limit=10)

# Run async function
asyncio.run(main())
```

## Error Handling

```python
try:
    result = await downloader.download_servers(["my-server"])
except Exception as e:
    logger.error(f"Download failed: {e}")

# Check results
if result["failed"] > 0:
    for failure in result["failed_servers"]:
        print(f"Failed: {failure['server']} - {failure['error']}")
```

## Extending with Custom Installers

Create custom installer plugins:

```python
from general_mcp_downloader import MCPInstaller

class CustomInstaller(MCPInstaller):
    async def can_handle(self, server_config, template):
        return template.installation_method == "custom"

    async def install(self, server_config, template, install_dir):
        # Custom installation logic
        return {"success": True, "method": "custom"}

    async def verify(self, server_config, template, install_dir):
        # Verification logic
        return True

# Register installer
downloader = GeneralMCPDownloader()
downloader.installers.append(CustomInstaller())
```
