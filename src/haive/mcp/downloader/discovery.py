"""Server discovery module for finding MCP servers from various sources.

This module provides functionality to discover MCP servers from multiple
registries and sources including npm, PyPI, GitHub, and custom registries.

Example:
    Basic discovery::

        discovery = ServerDiscovery(config)
        servers = await discovery.discover_all(limit_per_source=10)

    Discover from specific source::

        servers = await discovery.discover_from_npm(query="mcp server", limit=20)

Classes:
    ServerDiscovery: Main discovery class
    DiscoveredServer: Information about a discovered server

Version: 1.0.0
Author: Haive MCP Team
"""

import asyncio
import logging
import re
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import aiohttp
from pydantic import BaseModel, Field

from haive.mcp.downloader.config import DiscoveryConfig

logger = logging.getLogger(__name__)


class DiscoveredServer(BaseModel):
    """Information about a discovered MCP server.

    Attributes:
        name: Server name
        source: Where it was discovered (npm, github, etc.)
        source_url: URL where it was found
        description: Server description
        package_name: Package name (for npm/pypi)
        repo_url: Repository URL (for git)
        author: Author/owner name
        version: Latest version
        stars: GitHub stars or similar metric
        tags: Extracted tags
        metadata: Additional metadata

    Example:
        Discovered server info::

            server = DiscoveredServer(
                name="filesystem",
                source="npm",
                package_name="@modelcontextprotocol/server-filesystem",
                description="MCP server for filesystem operations"
            )
    """

    name: str = Field(..., description="Server name")
    source: str = Field(..., description="Discovery source")
    source_url: str | None = Field(None, description="Source URL")
    description: str | None = Field(None, description="Description")
    package_name: str | None = Field(None, description="Package name")
    repo_url: str | None = Field(None, description="Repository URL")
    author: str | None = Field(None, description="Author/owner")
    version: str | None = Field(None, description="Latest version")
    stars: int | None = Field(None, description="Popularity metric")
    tags: set[str] = Field(default_factory=set, description="Tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra metadata")


class ServerDiscovery:
    """Discovers MCP servers from various sources.

    This class provides methods to discover MCP servers from multiple
    registries and sources, with support for various search patterns
    and filtering options.

    Attributes:
        config: Discovery configuration
        discovered_cache: Cache of discovered servers
        session: Aiohttp session for HTTP requests

    Example:
        Using discovery::

            discovery = ServerDiscovery(config)

            # Discover from all sources
            all_servers = await discovery.discover_all()

            # Discover from specific source
            npm_servers = await discovery.discover_from_npm("mcp-server")

            # Determine template for discovered server
            template = discovery.determine_template(server_data)
    """

    def __init__(self, config: DiscoveryConfig):
        """Initialize server discovery.

        Args:
            config: Discovery configuration with sources and patterns
        """
        self.config = config
        self.discovered_cache: dict[str, DiscoveredServer] = {}
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session.

        Returns:
            Active aiohttp session
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def discover_all(
        self, limit_per_source: int | None = None
    ) -> list[dict[str, Any]]:
        """Discover servers from all configured sources.

        Args:
            limit_per_source: Maximum servers to discover per source.
                Uses config default if not specified.

        Returns:
            List of discovered server dictionaries

        Example:
            Discovering from all sources::

                servers = await discovery.discover_all(limit_per_source=50)
                print(f"Found {len(servers)} unique servers")
        """
        if limit_per_source is None:
            limit_per_source = self.config.max_servers

        all_servers = []
        tasks = []

        # Create discovery tasks for each source
        for source_url in self.config.sources:
            if "npmjs.org" in source_url:
                task = self.discover_from_npm_registry(source_url, limit_per_source)
            elif "pypi.org" in source_url:
                task = self.discover_from_pypi(source_url, limit_per_source)
            elif "github.com" in source_url or "api.github.com" in source_url:
                task = self.discover_from_github(source_url, limit_per_source)
            else:
                task = self.discover_from_url(source_url, limit_per_source)

            tasks.append(task)

        # Run all discoveries concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            source_url = self.config.sources[i]

            if isinstance(result, Exception):
                logger.error(f"Discovery failed for {source_url}: {result}")
                continue

            if isinstance(result, list):
                all_servers.extend(result)
                logger.info(f"Discovered {len(result)} servers from {source_url}")

        # Deduplicate by name
        unique_servers = {}
        for server in all_servers:
            name = server.get("name", "")
            if name and name not in unique_servers:
                unique_servers[name] = server

        return list(unique_servers.values())

    async def discover_from_npm_registry(
        self, registry_url: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Discover servers from npm registry.

        Args:
            registry_url: NPM registry search URL
            limit: Maximum results to return

        Returns:
            List of discovered servers

        Example:
            NPM discovery::

                servers = await discovery.discover_from_npm_registry(
                    "https://registry.npmjs.org/-/v1/search?text=mcp+server",
                    limit=50
                )
        """
        discovered = []

        try:
            session = await self._get_session()

            # Parse base URL and query
            parsed = urlparse(registry_url)
            query_params = parse_qs(parsed.query)

            # Add size parameter
            query_params["size"] = [str(min(limit, 250))]  # NPM max is 250

            # Rebuild URL

            url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(query_params, doseq=True)}"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    for obj in data.get("objects", []):
                        package = obj.get("package", {})
                        name = package.get("name", "")

                        # Check if it matches our patterns
                        if self._matches_npm_pattern(name):
                            server_name = self._extract_server_name(name)

                            discovered.append(
                                {
                                    "name": server_name,
                                    "source": "npm",
                                    "source_url": registry_url,
                                    "package_name": name,
                                    "description": package.get("description"),
                                    "author": package.get("author", {}).get("name"),
                                    "version": package.get("version"),
                                    "tags": self._extract_tags(
                                        name, package.get("keywords", [])
                                    ),
                                    "variables": {"package": name},
                                }
                            )

        except Exception as e:
            logger.exception(f"NPM discovery error: {e}")

        return discovered[:limit]

    async def discover_from_pypi(
        self, search_url: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Discover servers from PyPI.

        Args:
            search_url: PyPI search URL
            limit: Maximum results

        Returns:
            List of discovered servers
        """
        discovered = []

        try:
            await self._get_session()

            # PyPI JSON API endpoint
            if "search" in search_url:
                # Convert search URL to API URL

                # Search for packages matching patterns
                for pattern in self.config.patterns.get("pypi", []):
                    search_pattern = pattern.replace("*", "")
                    search_url = f"https://pypi.org/search/?q={search_pattern}"

                    # Note: PyPI doesn't have a great search API, so we'd need to
                    # scrape or use a different approach. For now, we'll use
                    # a simplified approach
                    logger.info(f"PyPI discovery would search for: {search_pattern}")

                    # Add some common known packages as examples
                    if "mcp" in search_pattern:
                        known_packages = ["mcp-server-example", "fastmcp", "mcp"]

                        for pkg in known_packages:
                            if self._matches_pypi_pattern(pkg):
                                discovered.append(
                                    {
                                        "name": self._extract_server_name(pkg),
                                        "source": "pypi",
                                        "source_url": search_url,
                                        "package_name": pkg,
                                        "tags": {"python", "pip"},
                                        "variables": {"package": pkg},
                                    }
                                )

        except Exception as e:
            logger.exception(f"PyPI discovery error: {e}")

        return discovered[:limit]

    async def discover_from_github(
        self, api_url: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Discover servers from GitHub.

        Args:
            api_url: GitHub API search URL
            limit: Maximum results

        Returns:
            List of discovered servers

        Example:
            GitHub discovery::

                servers = await discovery.discover_from_github(
                    "https://api.github.com/search/repositories?q=mcp+server",
                    limit=30
                )
        """
        discovered = []

        try:
            session = await self._get_session()

            # Add per_page parameter
            if "?" in api_url:
                api_url += f"&per_page={min(limit, 100)}"
            else:
                api_url += f"?per_page={min(limit, 100)}"

            headers = {
                "Accept": "application/vnd.github.v3+json",
                # Add token if available in environment
                # "Authorization": f"token {os.getenv('GITHUB_TOKEN')}"
            }

            async with session.get(api_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()

                    for repo in data.get("items", []):
                        name = repo.get("name", "")
                        repo.get("full_name", "")

                        # Check if it matches our patterns
                        if self._matches_github_pattern(name):
                            server_name = self._extract_server_name(name)

                            discovered.append(
                                {
                                    "name": server_name,
                                    "source": "github",
                                    "source_url": api_url,
                                    "repo_url": repo.get("clone_url"),
                                    "description": repo.get("description"),
                                    "author": repo.get("owner", {}).get("login"),
                                    "stars": repo.get("stargazers_count"),
                                    "tags": self._extract_tags(
                                        name,
                                        repo.get("topics", [])
                                        + (
                                            repo.get("language", "").lower().split()
                                            if repo.get("language")
                                            else []
                                        ),
                                    ),
                                    "variables": {
                                        "owner": repo.get("owner", {}).get("login"),
                                        "repo": name,
                                    },
                                }
                            )

                else:
                    logger.warning(f"GitHub API returned status {response.status}")

        except Exception as e:
            logger.exception(f"GitHub discovery error: {e}")

        return discovered[:limit]

    async def discover_from_url(
        self, url: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Discover servers from a generic URL (e.g., README).

        Args:
            url: URL to parse for server information
            limit: Maximum results

        Returns:
            List of discovered servers
        """
        discovered = []

        try:
            session = await self._get_session()

            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()

                    # Look for npm install commands
                    npm_pattern = r"npm install (?:-g )?([^\s]+)"
                    for match in re.finditer(npm_pattern, content):
                        package = match.group(1)
                        if self._matches_npm_pattern(package):
                            discovered.append(
                                {
                                    "name": self._extract_server_name(package),
                                    "source": "readme",
                                    "source_url": url,
                                    "package_name": package,
                                    "tags": {"npm", "discovered"},
                                    "variables": {"package": package},
                                }
                            )

                    # Look for GitHub repository links
                    github_pattern = r"https://github\.com/([^/]+)/([^/\s\)]+)"
                    for match in re.finditer(github_pattern, content):
                        owner, repo = match.groups()
                        repo = repo.rstrip(".git")

                        if self._matches_github_pattern(repo):
                            discovered.append(
                                {
                                    "name": self._extract_server_name(repo),
                                    "source": "readme",
                                    "source_url": url,
                                    "repo_url": f"https://github.com/{owner}/{repo}.git",
                                    "author": owner,
                                    "tags": {"git", "github", "discovered"},
                                    "variables": {"owner": owner, "repo": repo},
                                }
                            )

        except Exception as e:
            logger.exception(f"URL discovery error for {url}: {e}")

        return discovered[:limit]

    def _matches_npm_pattern(self, package_name: str) -> bool:
        """Check if package name matches NPM patterns.

        Args:
            package_name: NPM package name

        Returns:
            True if matches any configured pattern
        """
        patterns = self.config.patterns.get("npm", [])

        for pattern in patterns:
            # Convert glob pattern to regex
            regex_pattern = pattern.replace("*", ".*")
            if re.match(f"^{regex_pattern}$", package_name):
                return True

        return False

    def _matches_pypi_pattern(self, package_name: str) -> bool:
        """Check if package name matches PyPI patterns."""
        patterns = self.config.patterns.get("pypi", [])

        for pattern in patterns:
            regex_pattern = pattern.replace("*", ".*")
            if re.match(f"^{regex_pattern}$", package_name):
                return True

        return False

    def _matches_github_pattern(self, repo_name: str) -> bool:
        """Check if repository name matches GitHub patterns."""
        patterns = self.config.patterns.get("github", [])

        for pattern in patterns:
            regex_pattern = pattern.replace("*", ".*")
            if re.match(f"^{regex_pattern}$", repo_name, re.IGNORECASE):
                return True

        return False

    def _extract_server_name(self, full_name: str) -> str:
        """Extract clean server name from package/repo name.

        Args:
            full_name: Full package or repository name

        Returns:
            Clean server name

        Example:
            Extracting names::

                name = _extract_server_name("@modelcontextprotocol/server-filesystem")
                # Returns: "filesystem"

                name = _extract_server_name("mcp-server-github")
                # Returns: "github"
        """
        # Remove common prefixes
        name = full_name

        # Remove scope if present
        if "/" in name:
            name = name.split("/")[-1]

        # Remove common prefixes
        prefixes = ["server-", "mcp-server-", "mcp-", "-mcp-server", "-mcp"]
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix) :]
            elif name.endswith(prefix):
                name = name[: -len(prefix)]

        return name

    def _extract_tags(self, name: str, keywords: list[str]) -> set[str]:
        """Extract tags from name and keywords.

        Args:
            name: Package/repo name
            keywords: List of keywords

        Returns:
            Set of extracted tags
        """
        tags = set()

        # Add keywords
        tags.update(k.lower() for k in keywords if k)

        # Extract from name
        name_parts = re.split(r"[-_]", name.lower())
        common_tags = {
            "mcp",
            "server",
            "ai",
            "llm",
            "tool",
            "api",
            "database",
            "file",
            "git",
            "web",
            "search",
        }

        for part in name_parts:
            if part in common_tags:
                tags.add(part)

        return tags

    def determine_template(self, server_data: dict[str, Any]) -> str:
        """Determine the appropriate template for a discovered server.

        Args:
            server_data: Discovered server information

        Returns:
            Template name to use

        Example:
            Determining template::

                template = discovery.determine_template({
                    "source": "npm",
                    "package_name": "@modelcontextprotocol/server-example"
                })
                # Returns: "npm_official"
        """
        source = server_data.get("source", "")

        if source == "npm":
            package_name = server_data.get("package_name", "")

            if package_name.startswith("@modelcontextprotocol/"):
                return "npm_official"
            if "/" in package_name:
                return "npm_scoped"
            if package_name.startswith("mcp-server-"):
                return "npm_mcp_pattern"
            return "npm_community"

        if source == "pypi":
            package_name = server_data.get("package_name", "")

            if package_name.startswith("mcp-"):
                return "pypi_mcp_pattern"
            return "pypi_package"

        if source in ["github", "readme"]:
            if server_data.get("repo_url"):
                # Guess language from tags or metadata
                tags = server_data.get("tags", set())

                if "python" in tags:
                    return "git_repo"
                if "node" in tags or "npm" in tags:
                    return "git_node_repo"
                if "go" in tags:
                    return "git_go_repo"
                return "git_repo"  # Default
            return "git_repo"  # Return default instead of None

        if source == "docker":
            return "docker_image"

        return "npm_community"  # Default fallback

    async def search_servers(
        self, query: str, sources: list[str] | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Search for servers across sources with a specific query.

        Args:
            query: Search query
            sources: Specific sources to search (npm, pypi, github)
            limit: Maximum results

        Returns:
            List of matching servers

        Example:
            Searching for servers::

                results = await discovery.search_servers(
                    "database",
                    sources=["npm", "github"],
                    limit=20
                )
        """
        if sources is None:
            sources = ["npm", "github", "pypi"]

        all_results = []

        if "npm" in sources:
            npm_url = f"https://registry.npmjs.org/-/v1/search?text={query}+mcp+server"
            results = await self.discover_from_npm_registry(npm_url, limit)
            all_results.extend(results)

        if "github" in sources:
            github_url = (
                f"https://api.github.com/search/repositories?q={query}+mcp+server"
            )
            results = await self.discover_from_github(github_url, limit)
            all_results.extend(results)

        if "pypi" in sources:
            pypi_url = f"https://pypi.org/search/?q={query}+mcp"
            results = await self.discover_from_pypi(pypi_url, limit)
            all_results.extend(results)

        # Deduplicate and limit
        seen = set()
        unique_results = []

        for result in all_results:
            name = result.get("name")
            if name and name not in seen:
                seen.add(name)
                unique_results.append(result)

                if len(unique_results) >= limit:
                    break

        return unique_results
