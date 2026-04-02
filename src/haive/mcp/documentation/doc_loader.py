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
        self._documents_path = self.mcp_servers_path / "documents"
        self._loaded_docs: dict[str, Any] = {}
        self._enriched: dict[str, dict[str, Any]] = {}

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

    def get_enriched_server(self, server_name: str) -> dict[str, Any] | None:
        """Get a server enriched with data from its individual document file.

        The individual document files in ``data/mcp_servers/documents/`` contain
        full README content, descriptions, stars, and other metadata not present
        in the lightweight index.

        Args:
            server_name: Server name (exact or partial match).

        Returns:
            Enriched server dict with ``readme_content``, ``description``,
            ``install_command`` etc., or ``None`` if not found.
        """
        if not self._loaded_docs:
            self.load_all_mcp_documents()

        # Find the server in the index
        server = self._loaded_docs.get(server_name)
        if server is None:
            # Try partial match
            for name, doc in self._loaded_docs.items():
                if server_name.lower() in name.lower():
                    server = doc
                    server_name = name
                    break
        if server is None:
            return None

        # Check cache
        if server_name in self._enriched:
            return self._enriched[server_name]

        # Try to find the document file
        owner = server.get("repository_owner", "")
        repo_name = server.get("repository_name", "")
        if owner and repo_name:
            doc_file = self._documents_path / f"{owner}_{repo_name}.json"
            if doc_file.exists():
                try:
                    with open(doc_file) as f:
                        doc_data = json.load(f)
                    # Merge enriched data into a copy
                    enriched = {**server}
                    meta = doc_data.get("metadata", {})
                    enriched["description"] = meta.get("description") or enriched.get("description", "")
                    enriched["readme_content"] = doc_data.get("readme_content", "")
                    enriched["stars"] = meta.get("stars")
                    enriched["last_updated"] = meta.get("last_updated")
                    enriched["license"] = meta.get("license")
                    enriched["languages"] = meta.get("languages", [])
                    enriched["platforms"] = meta.get("platforms", [])
                    # Derive install command from README if not already set
                    if not enriched.get("install_command"):
                        enriched["install_command"] = self._derive_install_command(
                            enriched.get("readme_content", ""),
                            owner, repo_name,
                        )
                    self._enriched[server_name] = enriched
                    return enriched
                except Exception as e:
                    logger.debug(f"Failed to load document for {server_name}: {e}")

        # No doc file found -- derive install command from repo info
        enriched = {**server}
        enriched["install_command"] = self._derive_install_command("", owner, repo_name)
        self._enriched[server_name] = enriched
        return enriched

    @staticmethod
    def _derive_install_command(readme: str, owner: str, repo_name: str) -> str:
        """Derive an install command from README content or repo info.

        Scans the README for npx/uvx/pip/npm install patterns first,
        then falls back to a sensible default based on repo name.
        """
        if readme:
            candidates: list[tuple[int, str]] = []
            for line in readme.split("\n"):
                stripped = line.strip().lstrip("$> ").strip()
                if not stripped or stripped.startswith("```"):
                    continue
                cmd = stripped.split("#")[0].strip()  # trim inline comments

                # Skip debug/inspector commands
                if "inspector" in cmd.lower():
                    continue

                # pip install (high priority - simple, reliable)
                if cmd.startswith("pip install ") and len(cmd.split()) <= 4:
                    candidates.append((100, cmd))
                # uvx (high priority - Python MCP servers)
                elif cmd.startswith("uvx ") and len(cmd.split()) <= 4:
                    candidates.append((90, cmd))
                # npx -y @scope/package (standard MCP install)
                elif cmd.startswith("npx -y @") and len(cmd.split()) <= 4:
                    candidates.append((80, cmd))
                # npx -y package
                elif cmd.startswith("npx -y ") and len(cmd.split()) <= 4:
                    candidates.append((70, cmd))
                # npm install -g
                elif cmd.startswith("npm install -g ") and len(cmd.split()) <= 5:
                    candidates.append((60, cmd))
                # npx @scope/package (without -y)
                elif cmd.startswith("npx @") and len(cmd.split()) <= 3:
                    candidates.append((50, cmd.replace("npx ", "npx -y ")))

            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                return candidates[0][1]

        # Fallback: guess from repo name
        if repo_name:
            if any(repo_name.startswith(p) for p in ["mcp-server-", "server-"]):
                return f"npx -y @{owner}/{repo_name}"
            return f"npx -y {repo_name}"

        return ""

    def generate_server_config(self, server_name: str) -> dict[str, Any] | None:
        """Generate an MCP server configuration from a server in the database.

        Returns a config dict that can be used with:
        - haive-mcp ``MCPServerConfig``
        - Claude Desktop ``mcp.json``
        - ``langchain-mcp-adapters`` ``MultiServerMCPClient``

        Args:
            server_name: Server name (exact or partial match).

        Returns:
            Config dict with ``command``, ``args``, ``transport``, ``env``
            fields, or ``None`` if server not found.
        """
        enriched = self.get_enriched_server(server_name)
        if enriched is None:
            return None

        install_cmd = enriched.get("install_command", "")
        if not install_cmd:
            return None

        parts = install_cmd.split()
        config: dict[str, Any] = {"transport": "stdio"}

        if parts[0] == "npx":
            config["command"] = "npx"
            config["args"] = [p for p in parts[1:] if p]
            if "-y" not in config["args"]:
                config["args"].insert(0, "-y")
        elif parts[0] == "uvx":
            config["command"] = "uvx"
            config["args"] = parts[1:]
        elif parts[0] == "pip":
            # pip install → run as python -m
            pkg = parts[-1] if len(parts) > 2 else parts[1]
            module = pkg.replace("-", "_")
            config["command"] = "python"
            config["args"] = ["-m", module]
        elif parts[0] == "npm":
            # npm install -g → npx
            pkg = parts[-1]
            config["command"] = "npx"
            config["args"] = ["-y", pkg]
        else:
            config["command"] = parts[0]
            config["args"] = parts[1:]

        # Extract env vars from README config section
        readme = enriched.get("readme_content", "")
        env_vars = self._extract_configuration(readme)
        if env_vars:
            config["env"] = env_vars

        return config

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
