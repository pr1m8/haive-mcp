"""MCP documentation loader for server discovery and setup extraction.

Loads, searches, and extracts setup information from the pre-indexed
database of 1,960+ MCP servers. Includes lightweight GitHub README
fetching via aiohttp (no external framework dependencies).

Example:
    .. code-block:: python

        from haive.mcp.documentation import MCPDocumentationLoader

        loader = MCPDocumentationLoader()
        all_docs = loader.load_all_mcp_documents()
        print(f"Loaded {len(all_docs)} servers")

        results = loader.search_servers_by_capability("database")
        for server in results:
            info = loader.extract_setup_info(server)
            print(info["name"], info.get("install_command"))
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MCPDocumentationLoader:
    """Loads and processes MCP server documentation from the local database."""

    def __init__(self, resources_path: Path | None = None):
        """Initialize the documentation loader.

        Args:
            resources_path: Path to the data directory containing MCP servers.
                Defaults to the package's ``data/`` directory.
        """
        if resources_path is None:
            resources_path = Path(__file__).parent.parent.parent.parent.parent / "data"

        self.resources_path = resources_path
        self.mcp_servers_path = self.resources_path / "mcp_servers"
        self._loaded_docs: dict[str, Any] = {}

    def load_all_mcp_documents(self) -> dict[str, dict[str, Any]]:
        """Load all MCP server documentation from the stored JSON.

        Tries multiple data files in order of preference:
        1. ALL_MCP_SERVERS_COMPLETE.json (full database)
        2. organized_servers.json (organized version)
        3. all_mcp_documents.json (original)

        Returns:
            Dictionary mapping server names to documentation dictionaries.
        """
        candidates = [
            self.mcp_servers_path / "ALL_MCP_SERVERS_COMPLETE.json",
            self.mcp_servers_path / "organized_servers.json",
            self.mcp_servers_path / "all_mcp_documents.json",
        ]

        all_docs_path = None
        for candidate in candidates:
            if candidate.exists() and candidate.stat().st_size > 200:
                all_docs_path = candidate
                break

        if all_docs_path is None:
            logger.error("No MCP server data files found")
            return {}

        try:
            with open(all_docs_path) as f:
                data = json.load(f)

            if isinstance(data, list):
                docs_dict = {}
                for doc in data:
                    name = doc.get("name") or doc.get("metadata", {}).get("name", "")
                    if name:
                        docs_dict[name] = doc
                        self._loaded_docs[name] = doc
            elif "all_servers" in data:
                docs_dict = {}
                for doc in data["all_servers"]:
                    name = doc.get("name", "")
                    if name:
                        docs_dict[name] = doc
                        self._loaded_docs[name] = doc
            elif "servers" in data:
                docs_dict = data["servers"]
                self._loaded_docs = docs_dict.copy()
            else:
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
            server_name: Server name (e.g., ``"modelcontextprotocol/server-filesystem"``)
        """
        if not self._loaded_docs:
            self.load_all_mcp_documents()
        return self._loaded_docs.get(server_name)

    def search_servers_by_category(self, category: str) -> list[dict[str, Any]]:
        """Search for MCP servers by category.

        Args:
            category: Category to search for (e.g., ``"database"``, ``"filesystem"``)
        """
        if not self._loaded_docs:
            self.load_all_mcp_documents()

        matching = []
        for server_doc in self._loaded_docs.values():
            if "metadata" in server_doc:
                server_category = server_doc.get("metadata", {}).get("category", "")
            else:
                server_category = server_doc.get("category", "")

            if category.lower() in (server_category or "").lower():
                matching.append(server_doc)

        return matching

    def search_servers_by_capability(self, capability: str) -> list[dict[str, Any]]:
        """Search for MCP servers by capability in name or description.

        Args:
            capability: Capability keyword to search for.
        """
        if not self._loaded_docs:
            self.load_all_mcp_documents()

        matching = []
        for server_doc in self._loaded_docs.values():
            if "metadata" in server_doc:
                description = server_doc.get("metadata", {}).get("description", "")
                readme = server_doc.get("readme_content", "")
            else:
                description = server_doc.get("description", "")
                readme = server_doc.get("documentation", "")

            if (
                capability.lower() in (description or "").lower()
                or capability.lower() in (readme or "").lower()
            ):
                matching.append(server_doc)

        return matching

    async def fetch_github_readme(self, repo_url: str) -> str | None:
        """Fetch README from a GitHub repository via the API.

        Uses aiohttp directly -- no external framework dependencies.

        Args:
            repo_url: GitHub repository URL
                (e.g., ``"https://github.com/owner/repo"``)

        Returns:
            README content as a string, or ``None`` on failure.
        """
        try:
            import aiohttp
        except ImportError:
            logger.warning("aiohttp not installed -- cannot fetch README")
            return None

        try:
            parts = repo_url.rstrip("/").replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                return None
            owner, repo = parts[0], parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    api_url,
                    headers={"Accept": "application/vnd.github.raw+json"},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    logger.warning(f"GitHub API returned {resp.status} for {api_url}")
                    return None
        except Exception as e:
            logger.exception(f"Failed to fetch GitHub README: {e}")
            return None

    async def fetch_url_content(self, url: str) -> str | None:
        """Fetch text content from a URL.

        Args:
            url: URL to fetch.

        Returns:
            Response text, or ``None`` on failure.
        """
        try:
            import aiohttp
        except ImportError:
            logger.warning("aiohttp not installed -- cannot fetch URL")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    logger.warning(f"HTTP {resp.status} for {url}")
                    return None
        except Exception as e:
            logger.exception(f"Failed to fetch URL: {e}")
            return None

    def extract_setup_info(self, server_doc: dict[str, Any]) -> dict[str, Any]:
        """Extract setup information from server documentation.

        Args:
            server_doc: Server documentation dictionary.

        Returns:
            Extracted setup information including installation steps,
            configuration, and usage examples.
        """
        if "metadata" in server_doc and "readme_content" in server_doc:
            metadata = server_doc.get("metadata", {})
            readme = server_doc.get("readme_content", "")
            return {
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

        readme = server_doc.get("documentation", "")
        meta = server_doc.get("metadata", {})
        return {
            "name": server_doc.get("name", ""),
            "repo_url": server_doc.get("repository", server_doc.get("repository_url", "")),
            "description": server_doc.get("description", ""),
            "category": server_doc.get("category", ""),
            "stars": meta.get("stars") if isinstance(meta, dict) else None,
            "last_updated": meta.get("last_updated") if isinstance(meta, dict) else None,
            "is_official": meta.get("is_official", False) if isinstance(meta, dict) else False,
            "npm_package": meta.get("npm_package") if isinstance(meta, dict) else None,
            "install_command": (
                server_doc.get("install_command")
                or (meta.get("install_command") if isinstance(meta, dict) else None)
            ),
            "setup_instructions": meta.get("setup_instructions") if isinstance(meta, dict) else None,
            "transport_types": meta.get("transport_types", []) if isinstance(meta, dict) else [],
            "capabilities": meta.get("capabilities", []) if isinstance(meta, dict) else [],
            "dependencies": meta.get("dependencies", []) if isinstance(meta, dict) else [],
            "installation": self._extract_installation_steps(readme),
            "configuration": self._extract_configuration(readme),
            "usage": self._extract_usage_examples(readme),
        }

    # ------------------------------------------------------------------
    # Private helpers for extracting sections from README content
    # ------------------------------------------------------------------

    def _extract_installation_steps(self, readme: str | None) -> list[str]:
        """Extract installation steps from README."""
        if not readme:
            return []

        steps = []
        lines = readme.split("\n")
        in_install_section = False

        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["## install", "# install", "### install"]):
                in_install_section = True
                continue
            if in_install_section and line.startswith("#"):
                break
            if in_install_section and line.strip():
                if any(cmd in line for cmd in ["npm", "npx", "uvx", "pip", "git", "yarn", "pnpm", "cargo", "go", "docker"]):
                    steps.append(line.strip())
                elif line.strip().startswith(("$", ">", "```")):
                    clean = line.strip().lstrip("$>").strip()
                    if clean and not clean.startswith("```"):
                        steps.append(clean)

        return steps

    def _extract_configuration(self, readme: str | None) -> dict[str, Any]:
        """Extract configuration / env vars from README."""
        if not readme:
            return {}

        config: dict[str, Any] = {}
        lines = readme.split("\n")
        in_config = False

        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["## config", "# config", "### config", "## setup", "### setup"]):
                in_config = True
                continue
            if in_config and line.startswith("#"):
                break
            if ("export" in line or "=" in line) and any(
                v in line for v in ["API_KEY", "TOKEN", "URL", "PORT", "HOST", "SECRET"]
            ):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip().replace("export ", "")
                    value = parts[1].strip().strip("\"'")
                    config[key] = value

        return config

    def _extract_usage_examples(self, readme: str | None) -> list[str]:
        """Extract usage examples from README."""
        if not readme:
            return []

        examples: list[str] = []
        lines = readme.split("\n")
        in_usage = False
        in_code = False
        current: list[str] = []

        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["## usage", "# usage", "### usage", "## example", "### example"]):
                in_usage = True
                continue
            if in_usage and line.startswith("#") and not line.startswith("###"):
                break
            if "```" in line:
                if in_code:
                    if current:
                        examples.append("\n".join(current))
                        current = []
                    in_code = False
                else:
                    in_code = True
                continue
            if in_usage and in_code:
                current.append(line)

        return examples

    def _extract_dependencies(self, readme: str | None) -> list[str]:
        """Extract dependencies from README."""
        if not readme:
            return []

        deps: list[str] = []
        for line in readme.split("\n"):
            if "require" in line.lower() or "depend" in line.lower():
                if "npm install" in line:
                    parts = line.split("npm install")[-1].strip().split()
                    deps.extend(p for p in parts if not p.startswith("-"))
                elif "pip install" in line:
                    parts = line.split("pip install")[-1].strip().split()
                    deps.extend(p for p in parts if not p.startswith("-"))

        return list(set(deps))
