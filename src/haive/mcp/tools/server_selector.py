r"""Intelligent MCP server selection and filtering tools for AI agents.

This module provides sophisticated tools for filtering, selecting, and recommending
MCP servers based on various criteria including prefixes, capabilities, task analysis,
and performance metrics. Designed to help AI agents make intelligent decisions about
which servers to use for specific tasks.

The server selector provides:
    - Namespace/prefix-based filtering for organized server groups
    - Capability-based server recommendations
    - Task analysis for automatic server selection
    - Performance-aware server ranking
    - Interactive selection interfaces
    - Smart server combinations and workflows

Classes:
    MCPServerSelector: Main class for intelligent server selection
    ServerFilter: Flexible filtering system for servers
    TaskAnalyzer: Analyzes tasks to recommend appropriate servers
    ServerRecommender: Provides smart server recommendations

Example:
    Basic server selection::\n
        from haive.mcp.tools import MCPServerSelector
        from haive.mcp.documentation import MCPDocumentationLoader

        # Create selector with all available servers
        loader = MCPDocumentationLoader()
        all_servers = loader.load_all_mcp_documents()

        selector = MCPServerSelector(all_servers)

        # Filter by prefix (organization/namespace)
        anthropic_servers = selector.filter_by_prefix("anthropic/")
        openai_servers = selector.filter_by_prefix("openai/")

        # Get recommendations for a task
        task = "I need to analyze a GitHub repository for security issues"
        recommendations = selector.recommend_for_task(task)

        # Interactive selection
        chosen_servers = await selector.interactive_select(
            "Choose servers for code analysis",
            categories=["development", "security"]
        )

Note:
    This system is designed to make server selection intelligent and context-aware,
    reducing the need for manual server configuration.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.documentation.doc_loader import MCPDocumentationLoader

logger = logging.getLogger(__name__)


@dataclass
class ServerScore:
    """Score and metadata for a server recommendation."""

    server_name: str
    score: float
    reasons: list[str]
    capabilities_match: list[str]
    category_match: bool
    prefix_match: bool


@dataclass
class TaskRequirements:
    """Analyzed requirements from a task description."""

    keywords: list[str]
    required_capabilities: list[str]
    preferred_categories: list[str]
    suggested_servers: list[str]
    complexity_score: float


class ServerFilter:
    """Flexible filtering system for MCP servers."""

    def __init__(self, servers: list[dict[str, Any]]):
        """Initialize filter with server list.

        Args:
            servers: List of server documentation dictionaries
        """
        self.servers = servers
        self._build_indices()

    def _build_indices(self):
        """Build search indices for efficient filtering."""
        self.by_prefix = {}
        self.by_category = {}
        self.by_capability = {}

        for server in self.servers:
            metadata = server.get("metadata", {})
            name = metadata.get("name", "")
            category = metadata.get("category", "")

            # Build prefix index
            if "/" in name:
                prefix = name.split("/")[0] + "/"
                if prefix not in self.by_prefix:
                    self.by_prefix[prefix] = []
                self.by_prefix[prefix].append(server)

            # Build category index
            if category:
                if category not in self.by_category:
                    self.by_category[category] = []
                self.by_category[category].append(server)

            # Build capability index (from description)
            description = metadata.get("description", "").lower()
            for word in description.split():
                if len(word) > 3:  # Skip short words
                    if word not in self.by_capability:
                        self.by_capability[word] = []
                    self.by_capability[word].append(server)

    def filter_by_prefix(self, prefix: str) -> list[dict[str, Any]]:
        """Filter servers by name prefix (namespace).

        Args:
            prefix: Prefix to filter by (e.g., "anthropic/", "openai/")

        Returns:
            List of servers matching the prefix
        """
        if not prefix.endswith("/"):
            prefix += "/"

        return self.by_prefix.get(prefix, [])

    def filter_by_category(self, category: str) -> list[dict[str, Any]]:
        """Filter servers by category.

        Args:
            category: Category to filter by

        Returns:
            List of servers in the category
        """
        return self.by_category.get(category, [])

    def filter_by_capability_key(self, key: str) -> list[dict[str, Any]]:
        """Filter servers by capability key in description.

        Args:
            key: Key to search for

        Returns:
            List of servers mentioning the key
        """
        key = key.lower()
        matching = []

        for server in self.servers:
            metadata = server.get("metadata", {})
            description = metadata.get("description", "").lower()
            readme = server.get("readme_content", "").lower()

            if key in description or key in readme:
                matching.append(server)

        return matching

    def filter_by_multiple_criteria(
        self,
        prefixes: list[str] | None = None,
        categories: list[str] | None = None,
        keywords: list[str] | None = None,
        exclude_prefixes: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Filter servers by multiple criteria.

        Args:
            prefixes: List of prefixes to include
            categories: List of categories to include
            keywords: List of capability keywords
            exclude_prefixes: List of prefixes to exclude

        Returns:
            List of servers matching all criteria
        """

        # Start with all servers
        candidates = set(range(len(self.servers)))

        # Apply prefix filters
        if prefixes:
            prefix_matches = set()
            for prefix in prefixes:
                for server in self.filter_by_prefix(prefix):
                    prefix_matches.add(self.servers.index(server))
            candidates &= prefix_matches

        # Apply category filters
        if categories:
            category_matches = set()
            for category in categories:
                for server in self.filter_by_category(category):
                    category_matches.add(self.servers.index(server))
            candidates &= category_matches

        # Apply key filters
        if keywords:
            keyword_matches = set()
            for key in keywords:
                for server in self.filter_by_capability_key(key):
                    keyword_matches.add(self.servers.index(server))
            candidates &= keyword_matches

        # Apply exclusions
        if exclude_prefixes:
            for prefix in exclude_prefixes:
                excluded = set()
                for server in self.filter_by_prefix(prefix):
                    excluded.add(self.servers.index(server))
                candidates -= excluded

        return [self.servers[i] for i in candidates]


class TaskAnalyzer:
    """Analyzes task descriptions to determine server requirements."""

    def __init__(self):
        """Initialize task analyzer."""
        self.capability_patterns = {
            "filesystem": ["file", "directory", "read", "write", "path", "folder"],
            "database": [
                "database",
                "sql",
                "query",
                "table",
                "postgres",
                "mysql",
                "sqlite",
            ],
            "git": [
                "git",
                "github",
                "repository",
                "repo",
                "commit",
                "branch",
                "pull request",
            ],
            "web": ["http", "web", "api", "fetch", "download", "scrape", "url"],
            "search": ["search", "find", "lookup", "query", "index"],
            "calendar": ["calendar", "schedule", "appointment", "meeting", "event"],
            "email": ["email", "mail", "send", "inbox", "message"],
            "image": ["image", "picture", "photo", "generate", "edit", "vision"],
            "security": ["security", "vulnerability", "scan", "audit", "penetration"],
            "development": ["code", "programming", "debug", "test", "ci/cd", "deploy"],
            "documentation": ["docs", "documentation", "readme", "wiki", "help"],
            "time": ["time", "date", "timestamp", "timezone", "duration"],
            "ai": ["ai", "ml", "model", "predict", "train", "inference"],
        }

        self.server_patterns = {
            "github": ["github", "git", "repository", "repo", "issue", "pr"],
            "filesystem": ["file", "directory", "path", "folder", "local"],
            "postgres": ["postgres", "postgresql", "database", "sql"],
            "brave-search": ["search", "web search", "internet", "lookup"],
            "fetch": ["http", "download", "web", "api", "url"],
            "sqlite": ["sqlite", "database", "local database"],
            "time": ["time", "date", "timezone", "timestamp"],
            "memory": ["memory", "cache", "store", "remember"],
            "arxiv": ["arxiv", "research", "papers", "academic"],
            "everart": ["image", "art", "generate", "picture"],
            "gmail": ["gmail", "email", "mail", "send"],
            "google-calendar": ["calendar", "schedule", "appointment"],
            "notion": ["notion", "notes", "wiki", "knowledge"],
        }

    def analyze_task(self, task_description: str) -> TaskRequirements:
        """Analyze a task description to determine requirements.

        Args:
            task_description: Natural language task description

        Returns:
            TaskRequirements with analyzed needs
        """
        task_lower = task_description.lower()

        # Extract keywords
        keywords = re.findall(r"\b\w+\b", task_lower)
        keywords = [w for w in keywords if len(w) > 2]

        # Determine required capabilities
        required_capabilities = []
        for capability, patterns in self.capability_patterns.items():
            if any(pattern in task_lower for pattern in patterns):
                required_capabilities.append(capability)

        # Determine preferred categories
        category_scores = {}
        for capability in required_capabilities:
            if capability in ["filesystem", "database", "git"]:
                category_scores["development"] = (
                    category_scores.get("development", 0) + 1
                )
            elif capability in ["web", "search", "ai"]:
                category_scores["utilities"] = category_scores.get("utilities", 0) + 1
            elif capability in ["calendar", "email"]:
                category_scores["productivity"] = (
                    category_scores.get("productivity", 0) + 1
                )

        preferred_categories = sorted(
            category_scores.keys(), key=lambda x: category_scores[x], reverse=True
        )

        # Suggest specific servers
        suggested_servers = []
        for server, patterns in self.server_patterns.items():
            score = sum(1 for pattern in patterns if pattern in task_lower)
            if score > 0:
                suggested_servers.append((server, score))

        suggested_servers.sort(key=lambda x: x[1], reverse=True)
        suggested_servers = [s[0] for s in suggested_servers[:5]]

        # Calculate complexity
        complexity_score = len(required_capabilities) + len(suggested_servers) * 0.5

        return TaskRequirements(
            keywords=keywords[:10],  # Top 10 keywords
            required_capabilities=required_capabilities,
            preferred_categories=preferred_categories,
            suggested_servers=suggested_servers,
            complexity_score=min(complexity_score, 10.0),
        )


class MCPServerSelector:
    """Intelligent MCP server selection and recommendation system."""

    def __init__(self, servers: list[dict[str, Any]] | None = None):
        """Initialize server selector.

        Args:
            servers: List of server documentation. If None, loads all available.
        """
        if servers is None:
            loader = MCPDocumentationLoader()
            servers = loader.load_all_mcp_documents()

        self.servers = servers
        self.filter = ServerFilter(servers)
        self.analyzer = TaskAnalyzer()

        # Build name to server mapping
        self.server_map = {}
        for server in servers:
            metadata = server.get("metadata", {})
            name = metadata.get("name", "")
            if name:
                self.server_map[name] = server

    def get_available_prefixes(self) -> list[str]:
        """Get all available server prefixes/namespaces.

        Returns:
            List of unique prefixes found in server names
        """
        return sorted(self.filter.by_prefix.keys())

    def get_available_categories(self) -> list[str]:
        """Get all available server categories.

        Returns:
            List of unique categories
        """
        return sorted(self.filter.by_category.keys())

    def filter_by_prefix(self, prefix: str) -> list[dict[str, Any]]:
        """Filter servers by prefix/namespace.

        Args:
            prefix: Prefix to filter by (e.g., "modelcontextprotocol/")

        Returns:
            List of servers with matching prefix
        """
        return self.filter.filter_by_prefix(prefix)

    def recommend_for_task(
        self,
        task_description: str,
        max_servers: int = 5,
        include_experimental: bool = False,
    ) -> list[ServerScore]:
        """Recommend servers for a specific task.

        Args:
            task_description: Natural language description of the task
            max_servers: Maximum number of servers to recommend
            include_experimental: Whether to include experimental servers

        Returns:
            List of ServerScore objects ranked by relevance
        """
        requirements = self.analyzer.analyze_task(task_description)
        scores = []

        for server in self.servers:
            metadata = server.get("metadata", {})
            name = metadata.get("name", "")
            description = metadata.get("description", "").lower()
            category = metadata.get("category", "")

            # Skip experimental servers if not requested
            if not include_experimental and "experimental" in name.lower():
                continue

            score = 0.0
            reasons = []
            capabilities_match = []
            category_match = False
            prefix_match = False

            # Score based on suggested servers
            if any(suggested in name for suggested in requirements.suggested_servers):
                score += 5.0
                reasons.append("Directly mentioned in task analysis")

            # Score based on capability keywords
            for capability in requirements.required_capabilities:
                if capability in description:
                    score += 2.0
                    capabilities_match.append(capability)
                    reasons.append(f"Provides {capability} capability")

            # Score based on category match
            if category in requirements.preferred_categories:
                score += 1.0
                category_match = True
                reasons.append(f"Matches preferred category: {category}")

            # Score based on key overlap
            task_keywords = set(requirements.keywords)
            desc_keywords = set(description.split())
            overlap = len(task_keywords & desc_keywords)
            if overlap > 0:
                score += overlap * 0.5
                reasons.append(f"Key overlap: {overlap} matches")

            # Bonus for well-known/stable servers
            if name.startswith("modelcontextprotocol/"):
                score += 0.5
                prefix_match = True
                reasons.append("Official ModelContextProtocol server")

            if score > 0:
                scores.append(
                    ServerScore(
                        server_name=name,
                        score=score,
                        reasons=reasons,
                        capabilities_match=capabilities_match,
                        category_match=category_match,
                        prefix_match=prefix_match,
                    )
                )

        # Sort by score and return top results
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:max_servers]

    async def interactive_select(
        self,
        prompt: str = "Select MCP servers to use:",
        categories: list[str] | None = None,
        prefixes: list[str] | None = None,
        max_selections: int | None = None,
    ) -> list[str]:
        """Interactive server selection interface.

        Args:
            prompt: Prompt to display to user
            categories: Filter by categories
            prefixes: Filter by prefixes
            max_selections: Maximum number of selections allowed

        Returns:
            List of selected server names
        """
        # Filter servers based on criteria
        if categories or prefixes:
            candidates = self.filter.filter_by_multiple_criteria(
                prefixes=prefixes, categories=categories
            )
        else:
            candidates = self.servers

        if not candidates:
            print("No servers match the specified criteria.")
            return []

        print(f"\n{prompt}")
        print("=" * len(prompt))

        # Display available servers
        for i, server in enumerate(candidates, 1):
            metadata = server.get("metadata", {})
            name = metadata.get("name", "Unknown")
            description = metadata.get("description", "No description")
            category = metadata.get("category", "Uncategorized")

            print(f"{i:2d}. {name}")
            print(f"    Category: {category}")
            print(
                f"    Description: {description[:80]}{'...' if len(description) > 80 else ''}"
            )
            print()

        # Get user selections
        selections = []
        while True:
            try:
                user_input = input(
                    f"\nEnter server numbers (1-{len(candidates)}) separated by commas, or 'done': "
                ).strip()

                if user_input.lower() == "done":
                    break

                if user_input.lower() == "all":
                    selections = list(range(len(candidates)))
                    break

                # Parse selections
                numbers = [int(x.strip()) for x in user_input.split(",") if x.strip()]
                valid_numbers = [n for n in numbers if 1 <= n <= len(candidates)]

                if valid_numbers:
                    selections.extend(
                        [n - 1 for n in valid_numbers]
                    )  # Convert to 0-based
                    selections = list(set(selections))  # Remove duplicates

                    if max_selections and len(selections) >= max_selections:
                        selections = selections[:max_selections]
                        print(f"Maximum of {max_selections} selections reached.")
                        break

                print(f"Selected {len(selections)} servers. Current selections:")
                for idx in selections:
                    name = candidates[idx].get("metadata", {}).get("name", "Unknown")
                    print(f"  - {name}")

            except (ValueError, IndexError):
                print("Invalid input. Please enter valid server numbers.")
            except KeyboardInterrupt:
                print("\nSelection cancelled.")
                return []

        # Return selected server names
        selected_names = []
        for idx in selections:
            name = candidates[idx].get("metadata", {}).get("name")
            if name:
                selected_names.append(name)

        return selected_names

    def create_config_for_selection(
        self, selected_servers: list[str], lazy_init: bool = True
    ) -> MCPConfig:
        """Create MCPConfig for selected servers.

        Args:
            selected_servers: List of server names to include
            lazy_init: Whether to use lazy initialization

        Returns:
            MCPConfig with selected servers
        """
        # Use documentation loader to get setup info and create configs
        loader = MCPDocumentationLoader()
        servers = {}

        for server_name in selected_servers:
            if server_name in self.server_map:
                server_doc = self.server_map[server_name]
                setup_info = loader.extract_setup_info(server_doc)

                # Create MCPServerConfig
                config = self._create_server_config_from_setup(setup_info)
                if config:
                    servers[config.name] = config

        return MCPConfig(
            enabled=True, servers=servers, lazy_init=lazy_init, auto_discover=False
        )

    def _create_server_config_from_setup(
        self, setup_info: dict[str, Any]
    ) -> MCPServerConfig | None:
        """Create MCPServerConfig from setup information."""
        try:
            # Determine transport and connection info
            transport = "stdio"  # Default
            command = None
            args = []
            url = None

            # Extract from installation steps
            for step in setup_info.get("installation", []):
                if "npx" in step:
                    command = "npx"
                    # Extract package name
                    parts = step.split()
                    idx = parts.index("npx") if "npx" in parts else -1
                    if idx >= 0 and idx + 1 < len(parts):
                        args = parts[idx + 1 :]
                elif "http" in step:
                    # URL-based server
                    transport = "sse"
                    url = step

            return MCPServerConfig(
                name=setup_info.get("name", "unknown").replace("/", "_"),
                transport=transport,
                command=command,
                args=args,
                url=url,
                capabilities=setup_info.get("capabilities", []),
                category=setup_info.get("category", ""),
                description=setup_info.get("description", ""),
                env=setup_info.get("configuration", {}),
            )
        except Exception as e:
            logger.error(f"Failed to create server config: {e}")
            return None

    def get_selection_summary(self, selected_servers: list[str]) -> dict[str, Any]:
        """Get summary of selected servers.

        Args:
            selected_servers: List of selected server names

        Returns:
            Summary dictionary with statistics and details
        """
        categories = {}
        total_capabilities = set()
        prefixes = set()

        server_details = []

        for name in selected_servers:
            if name in self.server_map:
                server = self.server_map[name]
                metadata = server.get("metadata", {})

                category = metadata.get("category", "Uncategorized")
                categories[category] = categories.get(category, 0) + 1

                # Extract capabilities from description (simple heuristic)
                description = metadata.get("description", "").lower()
                if "file" in description:
                    total_capabilities.add("filesystem")
                if "database" in description or "sql" in description:
                    total_capabilities.add("database")
                if "web" in description or "http" in description:
                    total_capabilities.add("web")
                if "git" in description:
                    total_capabilities.add("git")

                if "/" in name:
                    prefixes.add(name.split("/")[0])

                server_details.append(
                    {
                        "name": name,
                        "category": category,
                        "description": metadata.get("description", ""),
                    }
                )

        return {
            "total_servers": len(selected_servers),
            "categories": categories,
            "capabilities": list(total_capabilities),
            "prefixes": list(prefixes),
            "servers": server_details,
        }
