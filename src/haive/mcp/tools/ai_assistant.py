r"""AI-friendly MCP server selection and configuration assistant.

This module provides tools specifically designed for AI agents to automatically
select, configure, and use MCP servers based on task analysis and intelligent
recommendations. It minimizes the need for manual configuration while maximizing
the effectiveness of server selection.

The assistant provides:
    - Automatic server selection based on task analysis
    - Smart configuration generation with minimal setup
    - Performance-aware server combinations
    - Fallback strategies for failed servers
    - Context-aware capability matching

Classes:
    MCPAssistant: Main AI-friendly server selection assistant
    SmartConfig: Intelligent configuration generator
    TaskMatcher: Advanced task-to-server matching system

Example:
    AI agent usage::\n
        from haive.mcp.tools import MCPAssistant

        # Create assistant
        assistant = MCPAssistant()

        # Automatically select servers for a task
        task = "I need to analyze Python code in a GitHub repo for security issues"
        config = await assistant.auto_configure_for_task(task)

        # Create agent with optimal configuration
        agent = MCPAgent(
            engine=engine,
            mcp_config=config,
            name="security_analysis_agent"
        )

        # Assistant provides reasoning
        reasoning = assistant.get_selection_reasoning()
        print(f"Selected servers because: {reasoning}")

Note:
    Designed to work seamlessly with AI agents that need to dynamically
    adapt their capabilities based on task requirements.
"""

import logging
from dataclasses import dataclass
from typing import Any

from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.documentation.doc_loader import MCPDocumentationLoader
from haive.mcp.tools.server_selector import MCPServerSelector, TaskAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class ServerRecommendation:
    """A server recommendation with detailed reasoning."""

    server_name: str
    confidence: float  # 0.0 to 1.0
    reasoning: str
    capabilities: list[str]
    estimated_setup_time: int  # seconds
    fallback_servers: list[str]
    required_env_vars: list[str]


@dataclass
class SmartConfiguration:
    """A complete MCP configuration with metadata."""

    config: MCPConfig
    primary_servers: list[str]
    fallback_servers: list[str]
    estimated_capabilities: list[str]
    setup_complexity: str  # "simple", "moderate", "complex"
    reasoning: str
    warnings: list[str]


class TaskMatcher:
    """Advanced task-to-server matching with learning capabilities."""

    def __init__(self):
        """Initialize task matcher."""
        self.task_patterns = self._load_task_patterns()
        self.server_profiles = self._load_server_profiles()
        self.success_history = {}  # Track successful combinations

    def _load_task_patterns(self) -> dict[str, Any]:
        """Load predefined task patterns for better matching."""
        return {
            "code_analysis": {
                "keywords": [
                    "analyze",
                    "code",
                    "review",
                    "audit",
                    "security",
                    "quality",
                ],
                "required_servers": ["github", "filesystem"],
                "optional_servers": ["brave-search", "arxiv"],
                "complexity": "moderate",
            },
            "research": {
                "keywords": ["research", "paper", "study", "academic", "literature"],
                "required_servers": ["brave-search", "arxiv"],
                "optional_servers": ["wikipedia", "github"],
                "complexity": "simple",
            },
            "data_analysis": {
                "keywords": ["data", "analyze", "database", "query", "statistics"],
                "required_servers": ["postgres", "sqlite"],
                "optional_servers": ["filesystem", "fetch"],
                "complexity": "moderate",
            },
            "content_generation": {
                "keywords": ["generate", "create", "write", "image", "art"],
                "required_servers": ["everart", "fetch"],
                "optional_servers": ["filesystem"],
                "complexity": "simple",
            },
            "system_administration": {
                "keywords": ["server", "deploy", "configure", "system", "admin"],
                "required_servers": ["filesystem", "github"],
                "optional_servers": ["time", "fetch"],
                "complexity": "complex",
            },
            "communication": {
                "keywords": ["email", "send", "message", "calendar", "schedule"],
                "required_servers": ["gmail", "google-calendar"],
                "optional_servers": ["notion"],
                "complexity": "simple",
            },
        }

    def _load_server_profiles(self) -> dict[str, Any]:
        """Load detailed server profiles for better recommendations."""
        return {
            "github": {
                "reliability": 0.9,
                "setup_difficulty": "easy",
                "common_issues": ["API rate limits", "token expiration"],
                "best_for": ["code analysis", "repository management"],
                "requires_auth": True,
            },
            "filesystem": {
                "reliability": 0.95,
                "setup_difficulty": "easy",
                "common_issues": ["permission errors"],
                "best_for": ["file operations", "local data"],
                "requires_auth": False,
            },
            "postgres": {
                "reliability": 0.85,
                "setup_difficulty": "moderate",
                "common_issues": ["connection setup", "credentials"],
                "best_for": ["structured data", "complex queries"],
                "requires_auth": True,
            },
            "brave-search": {
                "reliability": 0.8,
                "setup_difficulty": "moderate",
                "common_issues": ["rate limits", "API changes"],
                "best_for": ["web research", "current information"],
                "requires_auth": True,
            },
            "fetch": {
                "reliability": 0.9,
                "setup_difficulty": "easy",
                "common_issues": ["network connectivity", "CORS"],
                "best_for": ["HTTP requests", "API calls"],
                "requires_auth": False,
            },
        }

    def match_task_to_pattern(self, task_description: str) -> str | None:
        """Match a task description to a known pattern.

        Args:
            task_description: Natural language task description

        Returns:
            Pattern name if matched, None otherwise
        """
        task_lower = task_description.lower()

        best_match = None
        best_score = 0

        for pattern_name, pattern in self.task_patterns.items():
            score = 0
            keyword_matches = 0

            for keyword in pattern["keywords"]:
                if keyword in task_lower:
                    keyword_matches += 1
                    score += 1

            # Bonus for multiple keyword matches
            if keyword_matches > 1:
                score += keyword_matches * 0.5

            if score > best_score:
                best_score = score
                best_match = pattern_name

        return best_match if best_score > 1 else None

    def get_server_recommendation_score(
        self, server_name: str, task_pattern: str | None, task_description: str
    ) -> float:
        """Calculate recommendation score for a server.

        Args:
            server_name: Name of the server
            task_pattern: Matched task pattern
            task_description: Original task description

        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.0

        # Base score from server profile
        if server_name in self.server_profiles:
            profile = self.server_profiles[server_name]
            score += profile["reliability"] * 0.3

            # Bonus for easy setup
            if profile["setup_difficulty"] == "easy":
                score += 0.2
            elif profile["setup_difficulty"] == "moderate":
                score += 0.1

        # Score from task pattern match
        if task_pattern and task_pattern in self.task_patterns:
            pattern = self.task_patterns[task_pattern]
            if server_name in pattern["required_servers"]:
                score += 0.4
            elif server_name in pattern["optional_servers"]:
                score += 0.2

        # Score from task description keywords
        task_lower = task_description.lower()
        if server_name in self.server_profiles:
            profile = self.server_profiles[server_name]
            for use_case in profile["best_for"]:
                if use_case in task_lower:
                    score += 0.1

        # Historical success bonus
        history_key = f"{task_pattern or 'unknown'}:{server_name}"
        if history_key in self.success_history:
            success_rate = self.success_history[history_key]
            score += success_rate * 0.2

        return min(score, 1.0)


class MCPAssistant:
    """AI-friendly MCP server selection and configuration assistant."""

    def __init__(self, cache_enabled: bool = True):
        """Initialize MCP assistant.

        Args:
            cache_enabled: Whether to cache server information
        """
        self.selector = MCPServerSelector()
        self.matcher = TaskMatcher()
        self.analyzer = TaskAnalyzer()
        self.cache_enabled = cache_enabled
        self.cached_configs = {}
        self.last_reasoning = ""

    async def auto_configure_for_task(
        self,
        task_description: str,
        prefer_simple_setup: bool = True,
        max_servers: int = 3,
        include_fallbacks: bool = True,
    ) -> SmartConfiguration:
        """Automatically configure MCP servers for a task.

        Args:
            task_description: Natural language description of the task
            prefer_simple_setup: Prefer servers with easier setup
            max_servers: Maximum number of servers to include
            include_fallbacks: Whether to include fallback servers

        Returns:
            SmartConfiguration with optimized setup
        """
        # Check cache first
        cache_key = f"{task_description}:{prefer_simple_setup}:{max_servers}"
        if self.cache_enabled and cache_key in self.cached_configs:
            return self.cached_configs[cache_key]

        # Analyze the task
        requirements = self.analyzer.analyze_task(task_description)
        task_pattern = self.matcher.match_task_to_pattern(task_description)

        # Get server recommendations
        recommendations = self._get_smart_recommendations(
            task_description,
            requirements,
            task_pattern,
            max_servers,
            prefer_simple_setup,
        )

        # Generate configuration
        config = self._create_smart_config(recommendations, include_fallbacks)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            task_description, task_pattern, recommendations, requirements
        )

        # Determine complexity
        complexity = self._assess_setup_complexity(recommendations)

        # Generate warnings
        warnings = self._generate_warnings(recommendations)

        smart_config = SmartConfiguration(
            config=config,
            primary_servers=[r.server_name for r in recommendations],
            fallback_servers=self._get_fallback_servers(recommendations),
            estimated_capabilities=requirements.required_capabilities,
            setup_complexity=complexity,
            reasoning=reasoning,
            warnings=warnings,
        )

        # Cache the result
        if self.cache_enabled:
            self.cached_configs[cache_key] = smart_config

        self.last_reasoning = reasoning
        return smart_config

    def _get_smart_recommendations(
        self,
        task_description: str,
        requirements: Any,
        task_pattern: str | None,
        max_servers: int,
        prefer_simple_setup: bool,
    ) -> list[ServerRecommendation]:
        """Get intelligent server recommendations."""
        # Get base recommendations from selector
        base_scores = self.selector.recommend_for_task(
            task_description, max_servers * 2
        )

        recommendations = []

        for score in base_scores:
            # Calculate enhanced confidence using task matcher
            confidence = self.matcher.get_server_recommendation_score(
                score.server_name, task_pattern, task_description
            )

            # Adjust for setup preference
            if prefer_simple_setup:
                server_name = score.server_name.split("/")[-1]  # Get short name
                if server_name in self.matcher.server_profiles:
                    profile = self.matcher.server_profiles[server_name]
                    if profile["setup_difficulty"] == "easy":
                        confidence += 0.1
                    elif profile["setup_difficulty"] == "complex":
                        confidence -= 0.1

            # Generate reasoning
            reasoning_parts = []
            if task_pattern:
                reasoning_parts.append(f"Matches {task_pattern} pattern")
            reasoning_parts.extend(score.reasons)

            # Estimate setup time
            setup_time = self._estimate_setup_time(score.server_name)

            # Get required environment variables
            env_vars = self._get_required_env_vars(score.server_name)

            # Get fallback servers
            fallbacks = self._suggest_fallbacks(score.server_name, requirements)

            recommendation = ServerRecommendation(
                server_name=score.server_name,
                confidence=confidence,
                reasoning="; ".join(reasoning_parts),
                capabilities=score.capabilities_match,
                estimated_setup_time=setup_time,
                fallback_servers=fallbacks,
                required_env_vars=env_vars,
            )

            recommendations.append(recommendation)

        # Sort by confidence and return top results
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        return recommendations[:max_servers]

    def _create_smart_config(
        self, recommendations: list[ServerRecommendation], include_fallbacks: bool
    ) -> MCPConfig:
        """Create optimized MCP configuration."""
        servers = {}

        # Add primary servers
        for rec in recommendations:
            server_config = self._create_optimized_server_config(rec)
            if server_config:
                servers[server_config.name] = server_config

        # Add fallback servers if requested
        if include_fallbacks:
            fallback_names = set()
            for rec in recommendations:
                fallback_names.update(rec.fallback_servers)

            # Add fallback configs (disabled by default)
            for name in fallback_names:
                if name not in servers:
                    fallback_config = self._create_fallback_server_config(name)
                    if fallback_config:
                        fallback_config.enabled = False  # Disabled by default
                        servers[fallback_config.name] = fallback_config

        return MCPConfig(
            enabled=True,
            servers=servers,
            lazy_init=True,  # Always use lazy init for flexibility
            auto_discover=False,  # We've done the discovery
            max_concurrent_servers=min(len(servers), 5),  # Reasonable limit
        )

    def _create_optimized_server_config(
        self, recommendation: ServerRecommendation
    ) -> MCPServerConfig | None:
        """Create optimized server config from recommendation."""
        try:
            # Get server documentation
            if recommendation.server_name in self.selector.server_map:
                server_doc = self.selector.server_map[recommendation.server_name]
                loader = MCPDocumentationLoader()
                setup_info = loader.extract_setup_info(server_doc)

                # Create base config
                config = self.selector._create_server_config_from_setup(setup_info)
                if not config:
                    return None

                # Apply optimizations
                config.timeout = 60  # Generous timeout for AI agents
                config.retry_attempts = 3  # Reasonable retry count
                config.auto_start = True  # Auto-start for convenience

                # Set health check for critical servers
                if recommendation.confidence > 0.8:
                    config.health_check_interval = 300  # 5 minutes

                return config

        except Exception as e:
            logger.exception(
                f"Failed to create config for {recommendation.server_name}: {e}"
            )

        return None

    def _create_fallback_server_config(
        self, server_name: str
    ) -> MCPServerConfig | None:
        """Create fallback server configuration."""
        # Simplified configs for common fallback servers
        fallback_configs = {
            "fetch": MCPServerConfig(
                name="fetch_fallback",
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-fetch"],
                enabled=False,
                description="HTTP fetch fallback",
            ),
            "filesystem": MCPServerConfig(
                name="filesystem_fallback",
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"],
                enabled=False,
                description="Local filesystem fallback",
            ),
        }

        return fallback_configs.get(server_name)

    def _estimate_setup_time(self, server_name: str) -> int:
        """Estimate setup time in seconds."""
        short_name = server_name.split("/")[-1]

        if short_name in self.matcher.server_profiles:
            profile = self.matcher.server_profiles[short_name]
            difficulty = profile["setup_difficulty"]
            requires_auth = profile["requires_auth"]

            base_time = {"easy": 30, "moderate": 120, "complex": 300}.get(
                difficulty, 60
            )

            if requires_auth:
                base_time += 60  # Extra time for auth setup

            return base_time

        return 60  # Default estimate

    def _get_required_env_vars(self, server_name: str) -> list[str]:
        """Get required environment variables for a server."""
        # Common patterns for environment variables
        env_patterns = {
            "github": ["GITHUB_TOKEN"],
            "gmail": ["GMAIL_CREDENTIALS", "GMAIL_TOKEN"],
            "google-calendar": ["GOOGLE_CALENDAR_CREDENTIALS"],
            "notion": ["NOTION_TOKEN"],
            "brave-search": ["BRAVE_API_KEY"],
            "postgres": ["POSTGRES_URL", "POSTGRES_USER", "POSTGRES_PASSWORD"],
            "openai": ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
        }

        short_name = server_name.split("/")[-1]
        return env_patterns.get(short_name, [])

    def _suggest_fallbacks(self, server_name: str, requirements: Any) -> list[str]:
        """Suggest fallback servers for a primary server."""
        fallback_map = {
            "brave-search": ["fetch", "filesystem"],
            "github": ["filesystem", "fetch"],
            "postgres": ["sqlite", "filesystem"],
            "gmail": ["filesystem"],
            "notion": ["filesystem"],
            "arxiv": ["fetch", "filesystem"],
        }

        short_name = server_name.split("/")[-1]
        return fallback_map.get(short_name, ["filesystem", "fetch"])

    def _generate_reasoning(
        self,
        task_description: str,
        task_pattern: str | None,
        recommendations: list[ServerRecommendation],
        requirements: Any,
    ) -> str:
        """Generate human-readable reasoning for the selection."""
        parts = []

        if task_pattern:
            parts.append(f"Detected task type: {task_pattern}")

        parts.append(
            f"Required capabilities: {', '.join(requirements.required_capabilities)}"
        )

        if recommendations:
            top_server = recommendations[0]
            parts.append(
                f"Primary server: {top_server.server_name} (confidence: {
                    top_server.confidence:.1%
                })"
            )

            if len(recommendations) > 1:
                others = [r.server_name for r in recommendations[1:]]
                parts.append(f"Supporting servers: {', '.join(others)}")

        return ". ".join(parts)

    def _assess_setup_complexity(
        self, recommendations: list[ServerRecommendation]
    ) -> str:
        """Assess overall setup complexity."""
        if not recommendations:
            return "simple"

        max_setup_time = max(r.estimated_setup_time for r in recommendations)
        total_env_vars = sum(len(r.required_env_vars) for r in recommendations)

        if max_setup_time > 240 or total_env_vars > 3:
            return "complex"
        if max_setup_time > 90 or total_env_vars > 1:
            return "moderate"
        return "simple"

    def _generate_warnings(
        self, recommendations: list[ServerRecommendation]
    ) -> list[str]:
        """Generate warnings about potential issues."""
        warnings = []

        # Check for authentication requirements
        auth_servers = [r.server_name for r in recommendations if r.required_env_vars]
        if auth_servers:
            warnings.append(f"Authentication required for: {', '.join(auth_servers)}")

        # Check for complex setup
        complex_servers = [
            r.server_name for r in recommendations if r.estimated_setup_time > 180
        ]
        if complex_servers:
            warnings.append(f"Complex setup required for: {', '.join(complex_servers)}")

        # Check for reliability concerns
        low_confidence = [r.server_name for r in recommendations if r.confidence < 0.6]
        if low_confidence:
            warnings.append(f"Lower confidence servers: {', '.join(low_confidence)}")

        return warnings

    def _get_fallback_servers(
        self, recommendations: list[ServerRecommendation]
    ) -> list[str]:
        """Get all fallback servers from recommendations."""
        fallbacks = set()
        for rec in recommendations:
            fallbacks.update(rec.fallback_servers)
        return list(fallbacks)

    def get_selection_reasoning(self) -> str:
        """Get the reasoning for the last selection."""
        return self.last_reasoning

    def explain_recommendation(self, server_name: str) -> dict[str, Any]:
        """Get detailed explanation for a server recommendation.

        Args:
            server_name: Name of the server to explain

        Returns:
            Dictionary with detailed explanation
        """
        short_name = server_name.split("/")[-1]

        explanation = {
            "server_name": server_name,
            "short_name": short_name,
            "profile": self.matcher.server_profiles.get(short_name, {}),
            "common_use_cases": [],
            "setup_requirements": self._get_required_env_vars(server_name),
            "estimated_setup_time": self._estimate_setup_time(server_name),
            "fallback_options": self._suggest_fallbacks(server_name, None),
        }

        # Add common use cases from task patterns
        for pattern_name, pattern in self.matcher.task_patterns.items():
            if short_name in pattern.get("required_servers", []) + pattern.get(
                "optional_servers", []
            ):
                explanation["common_use_cases"].append(pattern_name)

        return explanation

    async def validate_configuration(self, config: MCPConfig) -> dict[str, Any]:
        """Validate a configuration and provide feedback.

        Args:
            config: MCP configuration to validate

        Returns:
            Validation results with issues and suggestions
        """
        results = {
            "valid": True,
            "issues": [],
            "suggestions": [],
            "estimated_setup_time": 0,
            "required_env_vars": [],
        }

        for server_name, server_config in config.servers.items():
            # Check for missing environment variables
            required_vars = self._get_required_env_vars(server_name)
            missing_vars = [
                var for var in required_vars if var not in server_config.env
            ]

            if missing_vars:
                results["issues"].append(
                    f"{server_name}: Missing environment variables: {', '.join(missing_vars)}"
                )
                results["valid"] = False

            results["required_env_vars"].extend(required_vars)
            results["estimated_setup_time"] += self._estimate_setup_time(server_name)

        # Check for conflicting servers
        server_names = [name.split("/")[-1] for name in config.servers]
        if len(server_names) != len(set(server_names)):
            results["issues"].append("Conflicting server names detected")

        # Suggestions for optimization
        if len(config.servers) > 5:
            results["suggestions"].append(
                "Consider reducing the number of servers for better performance"
            )

        if results["estimated_setup_time"] > 300:
            results["suggestions"].append(
                "Setup may take over 5 minutes - consider simpler alternatives"
            )

        return results
