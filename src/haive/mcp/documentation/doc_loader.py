"""MCP documentation loader using haive document loaders.

This module provides functionality to load, process, and extract information from
MCP server documentation. It includes methods to parse README files, extract setup
instructions, and generate configurations from documentation.

The loader processes documentation from:
    - Stored JSON files containing 992+ MCP server docs
    - GitHub repositories (via GitHubLoader)
    - Web documentation (via WebScraper)
    - Local documentation files

Classes:
    MCPDocumentationLoader: Main class for loading and processing MCP documentation

Example:
    Loading and using MCP documentation::

        from haive.mcp.documentation import MCPDocumentationLoader
from haive import agents


        # Initialize loader
        loader = MCPDocumentationLoader()

        # Load all documentation
        all_docs = loader.load_all_mcp_documents()
        print(f"Loaded {len(all_docs)} server documentations")

        # Get specific server documentation
        fs_doc = loader.get_server_documentation("modelcontextprotocol/server-filesystem")

        # Extract setup information
        setup_info = loader.extract_setup_info(fs_doc)
        print("Installation:", setup_info["installation"])
        print("Configuration:", setup_info["configuration"])

        # Search by capability
        search_servers = loader.search_servers_by_capability("search")
        print(f"Found {len(search_servers)} servers with search capability")

Note:
    The loader gracefully handles missing dependencies for document loaders.
"""

import json
import logging
from pathlib import Path
from typing import Any

from haive.agents.research.open_perplexity.structured_tools import (
    GitHubLoader,
    WebScraper,
)
from langchain_core.documents import Document

# Try to import haive document loaders
try:
    LOADERS_AVAILABLE = True
except ImportError:
    LOADERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MCPDocumentationLoader:
    """Loads and processes MCP server documentation from various sources."""

    def __init__(self, resources_path: Path | None = None):
        """Initialize the documentation loader.

        Args:
            resources_path: Path to the data directory containing MCP servers
        """
        if resources_path is None:
            # Default to the package's data directory
            resources_path = Path(__file__).parent.parent.parent.parent.parent / "data"

        self.resources_path = resources_path
        self.mcp_servers_path = self.resources_path / "mcp_servers"
        self._loaded_docs: dict[str, Any] = {}

    def load_all_mcp_documents(self) -> dict[str, dict[str, Any]]:
        """Load all MCP server documentation from the stored JSON.

        Returns:
            Dictionary mapping server names to documentation dictionaries
        """
        all_docs_path = self.mcp_servers_path / "all_mcp_documents.json"

        if not all_docs_path.exists():
            logger.error(f"MCP documents file not found: {all_docs_path}")
            return {}

        try:
            with open(all_docs_path) as f:
                data = json.load(f)

            # Handle both old list format and new structured format
            if isinstance(data, list):
                # Old format: list of documents
                docs_dict = {}
                for doc in data:
                    if doc.get("metadata", {}).get("name"):
                        name = doc["metadata"]["name"]
                        docs_dict[name] = doc
                        self._loaded_docs[name] = doc
            # New format: {metadata: {...}, servers: {...}}
            elif "servers" in data:
                docs_dict = data["servers"]
                self._loaded_docs = docs_dict.copy()
            else:
                # Fallback: treat as direct dictionary
                docs_dict = data
                self._loaded_docs = docs_dict.copy()

            logger.info(f"Loaded {len(docs_dict)} MCP server documents")
            return docs_dict
        except Exception as e:
            logger.exception(f"Failed to load MCP documents: {e}")
            return {}

    def get_server_documentation(self, server_name: str) -> dict[str, Any] | None:
        """Get documentation for a specific MCP server.

        Args:
            server_name: Name of the MCP server (e.g., "modelcontextprotocol/server-filesystem")

        Returns:
            Server documentation or None if not found
        """
        # Load all docs if not already cached
        if not self._loaded_docs:
            self.load_all_mcp_documents()

        return self._loaded_docs.get(server_name)

    def search_servers_by_category(self, category: str) -> list[dict[str, Any]]:
        """Search for MCP servers by category.

        Args:
            category: Category to search for (e.g., "Databases", "File Systems")

        Returns:
            List of matching server documentation
        """
        if not self._loaded_docs:
            self.load_all_mcp_documents()

        matching = []
        for server_doc in self._loaded_docs.values():
            # Handle both old and new format
            if "metadata" in server_doc:
                # Old format
                server_category = server_doc.get("metadata", {}).get("category", "")
            else:
                # New format
                server_category = server_doc.get("category", "")

            if category.lower() in server_category.lower():
                matching.append(server_doc)

        return matching

    def search_servers_by_capability(self, capability: str) -> list[dict[str, Any]]:
        """Search for MCP servers by capability mentioned in description.

        Args:
            capability: Capability to search for

        Returns:
            List of matching server documentation
        """
        if not self._loaded_docs:
            self.load_all_mcp_documents()

        matching = []
        for server_doc in self._loaded_docs.values():
            # Handle both old and new format
            if "metadata" in server_doc:
                # Old format
                description = server_doc.get("metadata", {}).get("description", "")
                readme = server_doc.get("readme_content", "")
            else:
                # New format
                description = server_doc.get("description", "")
                readme = server_doc.get("documentation", "")

            if (
                capability.lower() in description.lower()
                or capability.lower() in (readme or "").lower()
            ):
                matching.append(server_doc)

        return matching

    async def fetch_github_readme(self, repo_url: str) -> Document | None:
        """Fetch README from GitHub repository.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Document containing README content
        """
        if not LOADERS_AVAILABLE:
            logger.warning("Haive document loaders not available")
            return None

        try:
            loader = GitHubLoader()
            # Extract owner and repo from URL
            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                docs = await loader.load(repo=f"{owner}/{repo}", content_type="readme")
                return docs[0] if docs else None
        except Exception as e:
            logger.exception(f"Failed to fetch GitHub README: {e}")
            return None

    async def fetch_server_website(self, url: str) -> Document | None:
        """Fetch documentation from server website.

        Args:
            url: Website URL

        Returns:
            Document containing website content
        """
        if not LOADERS_AVAILABLE:
            logger.warning("Haive document loaders not available")
            return None

        try:
            scraper = WebScraper()
            docs = await scraper.load(url=url)
            return docs[0] if docs else None
        except Exception as e:
            logger.exception(f"Failed to fetch website: {e}")
            return None

    def extract_setup_info(self, server_doc: dict[str, Any]) -> dict[str, Any]:
        """Extract setup information from server documentation.

        Args:
            server_doc: Server documentation dictionary

        Returns:
            Extracted setup information
        """
        # Handle both old and new format
        if "metadata" in server_doc:
            # Old format
            metadata = server_doc.get("metadata", {})
            readme = server_doc.get("readme_content", "")
            setup_info = {
                "name": metadata.get("name", ""),
                "repo_url": metadata.get("repo_url", ""),
                "description": metadata.get("description", ""),
                "category": metadata.get("category", ""),
                "platforms": metadata.get("platforms", []),
                "languages": metadata.get("languages", []),
                "license": metadata.get("license", ""),
                "installation": self._extract_installation_steps(readme),
                "configuration": self._extract_configuration(readme),
                "usage": self._extract_usage_examples(readme),
                "dependencies": self._extract_dependencies(readme),
            }
        else:
            # New format
            readme = server_doc.get("documentation", "")
            meta = server_doc.get("metadata", {})
            setup_info = {
                "name": server_doc.get("name", ""),
                "repo_url": server_doc.get("repository", ""),
                "description": server_doc.get("description", ""),
                "category": server_doc.get("category", ""),
                "platforms": [],
                "languages": [],
                "license": "",
                "stars": meta.get("stars"),
                "last_updated": meta.get("last_updated"),
                "is_official": meta.get("is_official", False),
                "npm_package": meta.get("npm_package"),
                "install_command": meta.get("install_command"),
                "setup_instructions": meta.get("setup_instructions"),
                "transport_types": meta.get("transport_types", []),
                "capabilities": meta.get("capabilities", []),
                "dependencies": meta.get("dependencies", []),
                "installation": self._extract_installation_steps(readme),
                "configuration": self._extract_configuration(readme),
                "usage": self._extract_usage_examples(readme),
            }

        return setup_info

    def _extract_installation_steps(self, readme: str | None) -> list[str]:
        """Extract installation steps from README."""
        if not readme:
            return []

        steps = []
        lines = readme.split("\n")
        in_install_section = False

        for line in lines:
            lower_line = line.lower()

            # Look for installation section
            if any(
                keyword in lower_line
                for keyword in ["## install", "# install", "### install"]
            ):
                in_install_section = True
                continue

            # End of installation section
            if in_install_section and line.startswith("#"):
                break

            # Collect installation steps
            if in_install_section and line.strip():
                # Look for commands (lines with npm, pip, git, etc.)
                if any(
                    cmd in line
                    for cmd in ["npm", "pip", "git", "yarn", "pnpm", "cargo", "go"]
                ):
                    steps.append(line.strip())
                elif line.strip().startswith(("$", ">", "```")):
                    # Command line indicators
                    clean_line = line.strip().lstrip("$>").strip()
                    if clean_line and not clean_line.startswith("```"):
                        steps.append(clean_line)

        return steps

    def _extract_configuration(self, readme: str | None) -> dict[str, Any]:
        """Extract configuration information from README."""
        if not readme:
            return {}

        config = {}
        lines = readme.split("\n")
        in_config_section = False

        for _i, line in enumerate(lines):
            lower_line = line.lower()

            # Look for configuration section
            if any(
                keyword in lower_line
                for keyword in [
                    "## config",
                    "# config",
                    "### config",
                    "## setup",
                    "### setup",
                ]
            ):
                in_config_section = True
                continue

            # End of configuration section
            if in_config_section and line.startswith("#"):
                break

            # Look for environment variables
            if ("export" in line or "=" in line) and any(
                var in line for var in ["API_KEY", "TOKEN", "URL", "PORT", "HOST"]
            ):
                parts = line.split("=")
                if len(parts) == 2:
                    key = parts[0].strip().replace("export ", "")
                    value = parts[1].strip().strip("\"'")
                    config[key] = value

        return config

    def _extract_usage_examples(self, readme: str | None) -> list[str]:
        """Extract usage examples from README."""
        if not readme:
            return []

        examples = []
        lines = readme.split("\n")
        in_usage_section = False
        in_code_block = False
        current_example = []

        for line in lines:
            lower_line = line.lower()

            # Look for usage section
            if any(
                keyword in lower_line
                for keyword in [
                    "## usage",
                    "# usage",
                    "### usage",
                    "## example",
                    "### example",
                ]
            ):
                in_usage_section = True
                continue

            # End of usage section
            if in_usage_section and line.startswith("#") and not line.startswith("###"):
                break

            # Track code blocks
            if "```" in line:
                if in_code_block:
                    # End of code block
                    if current_example:
                        examples.append("\n".join(current_example))
                        current_example = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                continue

            # Collect code examples
            if in_usage_section and in_code_block:
                current_example.append(line)

        return examples

    def _extract_dependencies(self, readme: str | None) -> list[str]:
        """Extract dependencies from README."""
        if not readme:
            return []

        dependencies = []
        lines = readme.split("\n")

        for line in lines:
            # Look for requirement patterns
            if "require" in line.lower() or "depend" in line.lower():
                # Extract package names from common patterns
                if "npm install" in line:
                    parts = line.split("npm install")[-1].strip().split()
                    dependencies.extend([p for p in parts if not p.startswith("-")])
                elif "pip install" in line:
                    parts = line.split("pip install")[-1].strip().split()
                    dependencies.extend([p for p in parts if not p.startswith("-")])

        return list(set(dependencies))  # Remove duplicates
