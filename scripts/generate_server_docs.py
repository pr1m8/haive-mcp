#!/usr/bin/env python3
"""Generate RST documentation for MCP servers from JSON data.

This script processes MCP server JSON data and generates:
1. Individual server documentation (index.rst, configuration.rst)
2. Master index file (mcp_servers.rst) organizing servers by category
3. Category index files for navigation

Usage:
    poetry run python scripts/generate_server_docs.py
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MCPDocumentationGenerator:
    """Generate RST documentation for MCP servers."""

    def __init__(self, base_path: Path | None = None):
        """Initialize the documentation generator."""
        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = base_path
        self.data_path = self.base_path / "data" / "mcp_servers"
        self.docs_path = self.base_path / "data" / "documentation" / "servers"
        self.sphinx_docs_path = self.base_path / "docs"

        # Ensure directories exist
        self.docs_path.mkdir(parents=True, exist_ok=True)

    def generate_all_documentation(self) -> None:
        """Generate documentation for all MCP servers."""
        logger.info("Starting MCP documentation generation...")

        # Load server data
        servers = self._load_server_data()
        logger.info(f"Loaded {len(servers)} servers")

        # Organize servers by category
        categorized_servers = self._categorize_servers(servers)

        # Generate individual server docs
        for server_name, server_data in servers.items():
            self._generate_server_documentation(server_name, server_data)

        # Generate category index files
        for category, servers_in_category in categorized_servers.items():
            self._generate_category_index(category, servers_in_category)

        # Generate master index
        self._generate_master_index(categorized_servers)

        logger.info("Documentation generation complete!")

    def _load_server_data(self) -> Dict[str, Any]:
        """Load all server data from JSON files."""
        all_servers = {}

        # Try production database first
        prod_db = self.data_path / "production_mcp_database.json"
        if prod_db.exists():
            with open(prod_db) as f:
                data = json.load(f)
                if "servers" in data:
                    all_servers.update(data["servers"])

        # Load from all_mcp_documents.json as fallback
        all_docs = self.data_path / "all_mcp_documents.json"
        if all_docs.exists() and not all_servers:
            with open(all_docs) as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Convert list to dict
                    for doc in data:
                        if "metadata" in doc and "name" in doc["metadata"]:
                            all_servers[doc["metadata"]["name"]] = doc
                elif "servers" in data:
                    all_servers.update(data["servers"])

        return all_servers

    def _categorize_servers(
        self, servers: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Organize servers by category."""
        categories = {}

        for server_name, server_data in servers.items():
            # Determine category
            category = self._get_server_category(server_data)

            if category not in categories:
                categories[category] = []

            categories[category].append({"name": server_name, "data": server_data})

        # Sort servers within each category by quality score
        for category in categories:
            categories[category].sort(
                key=lambda x: self._calculate_quality_score(x["data"]), reverse=True
            )

        return categories

    def _get_server_category(self, server_data: Dict[str, Any]) -> str:
        """Determine the category for a server."""
        # Check metadata for category
        if "metadata" in server_data:
            category = server_data["metadata"].get("category", "")
        else:
            category = server_data.get("category", "")

        # Map to standard categories
        category_map = {
            "ai": "ai_ml",
            "ml": "ai_ml",
            "database": "database",
            "db": "database",
            "api": "api_integration",
            "file": "filesystem",
            "fs": "filesystem",
            "cloud": "cloud",
            "search": "search",
            "security": "security",
            "monitoring": "monitoring",
            "communication": "communication",
            "productivity": "productivity",
            "media": "media",
            "finance": "finance",
            "version control": "version_control",
            "vcs": "version_control",
        }

        # Normalize category
        category_lower = category.lower()
        for key, mapped in category_map.items():
            if key in category_lower:
                return mapped

        # Default category
        return "utility" if category else "uncategorized"

    def _calculate_quality_score(self, server_data: Dict[str, Any]) -> float:
        """Calculate quality score for a server."""
        score = 0.0

        # Extract metadata
        if "metadata" in server_data:
            meta = server_data["metadata"]
            stars = meta.get("stars", 0) or 0
            has_docs = bool(server_data.get("readme_content"))
        else:
            meta = server_data.get("metadata", {})
            stars = meta.get("stars", 0) or 0
            has_docs = bool(server_data.get("documentation"))

        # Stars contribution (40%)
        if stars > 1000:
            score += 40
        elif stars > 100:
            score += 30
        elif stars > 10:
            score += 20
        elif stars > 0:
            score += 10

        # Documentation quality (30%)
        if has_docs:
            doc_content = server_data.get("readme_content") or server_data.get(
                "documentation", ""
            )
            doc_length = len(doc_content)
            if doc_length > 5000:
                score += 30
            elif doc_length > 1000:
                score += 20
            elif doc_length > 100:
                score += 10

        # Maintenance (20%)
        if meta.get("last_updated"):
            try:
                last_update = datetime.fromisoformat(
                    meta["last_updated"].replace("Z", "+00:00")
                )
                days_ago = (datetime.now().astimezone() - last_update).days
                if days_ago < 30:
                    score += 20
                elif days_ago < 90:
                    score += 15
                elif days_ago < 180:
                    score += 10
                elif days_ago < 365:
                    score += 5
            except:
                pass

        # Completeness (10%)
        if meta.get("npm_package") or meta.get("install_command"):
            score += 5
        if meta.get("transport_types"):
            score += 5

        return score

    def _generate_server_documentation(
        self, server_name: str, server_data: Dict[str, Any]
    ) -> None:
        """Generate documentation for a single server."""
        # Determine category and create directory
        category = self._get_server_category(server_data)
        safe_name = server_name.replace("/", "_").replace("@", "")
        server_dir = self.docs_path / category / safe_name
        server_dir.mkdir(parents=True, exist_ok=True)

        # Generate index.rst
        self._generate_server_index(server_dir, server_name, server_data)

        # Generate configuration.rst
        self._generate_server_configuration(server_dir, server_name, server_data)

    def _generate_server_index(
        self, server_dir: Path, server_name: str, server_data: Dict[str, Any]
    ) -> None:
        """Generate index.rst for a server."""
        quality_score = self._calculate_quality_score(server_data)

        # Extract metadata
        if "metadata" in server_data:
            meta = server_data["metadata"]
            description = meta.get("description", "")
            repo_url = meta.get("repo_url", "")
            category = meta.get("category", "")
        else:
            meta = server_data.get("metadata", {})
            description = server_data.get("description", "")
            repo_url = server_data.get("repository", "")
            category = server_data.get("category", "")

        # Quality badge
        if quality_score >= 70:
            quality_badge = ".. badge:: Quality: Excellent (≥70)"
        elif quality_score >= 50:
            quality_badge = ".. badge:: Quality: Good (≥50)"
        else:
            quality_badge = ".. badge:: Quality: Needs Improvement (<50)"

        content = f"""{server_name}
{'=' * len(server_name)}

{quality_badge}
.. badge:: Category: {category}

.. contents:: Table of Contents
   :depth: 2
   :local:

Overview
--------

{description}

**Quality Score:** {quality_score:.1f}/100

**Category:** {category}

**Installation Method:** {meta.get('install_method', 'npm')}

**Setup Complexity:** {self._estimate_complexity(server_data)}/5

Repository
~~~~~~~~~~

**URL:** {repo_url}

**Source:** {meta.get('source', 'github')}

**Last Updated:** {meta.get('last_updated', 'Unknown')}

Quality Metrics
~~~~~~~~~~~~~~~

* **Documentation Score:** {self._calculate_doc_score(server_data):.1f}/100
* **Popularity Score:** {self._calculate_popularity_score(server_data):.1f}/100  
* **Maintenance Score:** {self._calculate_maintenance_score(server_data):.1f}/100
* **Completeness Score:** {self._calculate_completeness_score(server_data):.1f}/100

Tags
~~~~

{self._generate_tags(server_data)}

Installation
------------

Quick Install
~~~~~~~~~~~~~

.. code-block:: bash

   {self._generate_install_command(server_data)}

{self._generate_detailed_installation(server_data)}

Features
--------

{self._extract_features(server_data)}

API Reference
-------------

{self._extract_api_info(server_data)}

Configuration
-------------

See :doc:`configuration` for detailed configuration options.

Examples
--------

See :doc:`examples` for usage examples and code samples.

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

For installation issues, check:

1. Ensure all dependencies are installed
2. Verify environment variables are set correctly
3. Check network connectivity for remote resources

See Also
--------

* :doc:`../index` - Category overview
* :doc:`../../index` - All MCP servers
* :doc:`configuration` - Configuration reference
* :doc:`examples` - Usage examples

.. note::
   This documentation was automatically generated from the MCP server metadata
   and repository information. For the most up-to-date information, please
   refer to the official repository.
"""

        index_file = server_dir / "index.rst"
        index_file.write_text(content)

    def _generate_server_configuration(
        self, server_dir: Path, server_name: str, server_data: Dict[str, Any]
    ) -> None:
        """Generate configuration.rst for a server."""
        # Extract metadata
        if "metadata" in server_data:
            meta = server_data["metadata"]
        else:
            meta = server_data.get("metadata", {})

        transport_types = meta.get("transport_types", ["stdio"])

        content = f"""Configuration for {server_name}
{'=' * (len(server_name) + 17)}

This page contains configuration information for the {server_name} MCP server.

.. contents:: Table of Contents
   :depth: 2
   :local:

Basic Configuration
-------------------

**Installation Method:** {meta.get('install_method', 'npm')}

**Setup Complexity:** {self._estimate_complexity(server_data)}/5

**Transport Types:** {', '.join(transport_types)}

Environment Variables
---------------------

.. note::
   Environment variables may be required for this server to function properly.
   Check the repository documentation for specific requirements.

{self._extract_env_vars(server_data)}

Transport Configuration
-----------------------

This server supports the following transport types:

{self._generate_transport_examples(server_name, transport_types)}
"""

        config_file = server_dir / "configuration.rst"
        config_file.write_text(content)

    def _generate_category_index(
        self, category: str, servers: List[Dict[str, Any]]
    ) -> None:
        """Generate index.rst for a category."""
        category_dir = self.docs_path / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Format category name
        category_title = category.replace("_", " ").title()

        content = f"""{category_title} MCP Servers
{'=' * (len(category_title) + 12)}

.. contents:: Servers in this category
   :depth: 1
   :local:

Overview
--------

This category contains {len(servers)} MCP servers related to {category_title.lower()}.

Servers
-------

.. toctree::
   :maxdepth: 1
   :titlesonly:

"""

        # Add each server
        for server_info in servers:
            server_name = server_info["name"]
            safe_name = server_name.replace("/", "_").replace("@", "")
            quality = self._calculate_quality_score(server_info["data"])

            content += f"   {safe_name}/index\n"

        content += """

Quick Reference
---------------

.. list-table:: Servers Overview
   :header-rows: 1
   :widths: 30 10 10 50

   * - Server
     - Quality
     - Stars
     - Description
"""

        # Add table rows
        for server_info in servers:
            server_name = server_info["name"]
            server_data = server_info["data"]
            quality = self._calculate_quality_score(server_data)

            if "metadata" in server_data:
                stars = server_data["metadata"].get("stars", 0) or "N/A"
                desc = (server_data["metadata"].get("description") or "")[:80]
            else:
                meta = server_data.get("metadata", {})
                stars = meta.get("stars", 0) or "N/A"
                desc = (server_data.get("description") or "")[:80]

            content += f"   * - :doc:`{server_name.replace('/', '_').replace('@', '')}/index`\n"
            content += f"     - {quality:.0f}%\n"
            content += f"     - {stars}\n"
            content += f"     - {desc}...\n"

        index_file = category_dir / "index.rst"
        index_file.write_text(content)

    def _generate_master_index(
        self, categorized_servers: Dict[str, List[Dict[str, Any]]]
    ) -> None:
        """Generate the master mcp_servers.rst index file."""
        total_servers = sum(len(servers) for servers in categorized_servers.values())

        content = f"""MCP Servers Documentation
=========================

Browse {total_servers} Model Context Protocol servers organized by category.

.. contents:: Categories
   :depth: 2
   :local:

Overview
--------

This comprehensive documentation covers all discovered MCP servers, organized by 
functionality. Each server includes:

* Installation instructions
* Configuration examples
* Quality metrics
* API documentation
* Troubleshooting guides

Quick Stats
~~~~~~~~~~~

* **Total Servers:** {total_servers}
* **Categories:** {len(categorized_servers)}
* **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}

"""

        # Category mapping for better titles
        category_titles = {
            "ai_ml": "AI & Machine Learning",
            "api_integration": "API Integration",
            "cloud": "Cloud Services",
            "communication": "Communication",
            "database": "Databases",
            "filesystem": "File Systems",
            "finance": "Finance",
            "media": "Media & Content",
            "monitoring": "Monitoring & Analytics",
            "productivity": "Productivity Tools",
            "search": "Search & Discovery",
            "security": "Security",
            "utility": "Utilities",
            "version_control": "Version Control",
            "uncategorized": "Other",
        }

        # Add each category
        for category in sorted(categorized_servers.keys()):
            servers = categorized_servers[category]
            if not servers:
                continue

            title = category_titles.get(category, category.replace("_", " ").title())

            content += f"""
{title}
{'-' * len(title)}

{self._get_category_description(category)}

**Servers in this category:** {len(servers)}

.. toctree::
   :maxdepth: 1
   :titlesonly:

   servers/{category}/index
"""

            # Add top 5 servers as highlights
            top_servers = servers[:5]
            if top_servers:
                content += "\nHighlighted Servers:\n\n"
                for server_info in top_servers:
                    server_name = server_info["name"]
                    safe_name = server_name.replace("/", "_").replace("@", "")
                    quality = self._calculate_quality_score(server_info["data"])

                    content += f"* :doc:`servers/{category}/{safe_name}/index` "
                    content += f"(Quality: {quality:.0f}%)\n"

        content += """

Finding Servers
---------------

Use the search functionality or browse by category above. You can also:

* Filter by quality score
* Search by capability
* Find servers by programming language
* Discover servers by transport type

Contributing
------------

To add or update server documentation:

1. Submit a PR to the MCP server repository
2. Update the server metadata
3. Run the documentation generator
4. Review the generated docs

See Also
--------

* :doc:`index` - Main documentation
* :doc:`quickstart` - Getting started guide
* :doc:`configuration` - Configuration guide
* :doc:`api/agents` - Agent API reference
"""

        # Write to docs directory
        servers_file = self.sphinx_docs_path / "mcp_servers.rst"
        servers_file.write_text(content)

        logger.info(f"Generated master index at {servers_file}")

    def _get_category_description(self, category: str) -> str:
        """Get description for a category."""
        descriptions = {
            "ai_ml": "Servers for AI/ML operations, model integration, and intelligent processing.",
            "api_integration": "Connect to external APIs, webhooks, and third-party services.",
            "cloud": "Cloud platform integrations including AWS, Azure, GCP, and more.",
            "communication": "Email, messaging, notifications, and collaboration tools.",
            "database": "Database connectors, query tools, and data management.",
            "filesystem": "File system operations, storage, and document management.",
            "finance": "Financial data, trading, accounting, and payment processing.",
            "media": "Image, video, audio processing and media management.",
            "monitoring": "System monitoring, logging, analytics, and observability.",
            "productivity": "Task management, note-taking, and productivity tools.",
            "search": "Search engines, indexing, and information retrieval.",
            "security": "Security tools, authentication, and vulnerability scanning.",
            "utility": "General purpose utilities and helper tools.",
            "version_control": "Git, version control, and code repository tools.",
            "uncategorized": "Servers that don't fit into other categories.",
        }
        return descriptions.get(
            category, f"Servers related to {category.replace('_', ' ')}."
        )

    # Helper methods for documentation generation
    def _estimate_complexity(self, server_data: Dict[str, Any]) -> int:
        """Estimate setup complexity (1-5)."""
        complexity = 1

        # Check for dependencies
        if "metadata" in server_data:
            meta = server_data["metadata"]
        else:
            meta = server_data.get("metadata", {})

        deps = meta.get("dependencies", [])
        if len(deps) > 5:
            complexity += 2
        elif len(deps) > 2:
            complexity += 1

        # Check for environment variables
        if meta.get("env_vars"):
            complexity += 1

        # Check for additional setup steps
        doc = server_data.get("readme_content") or server_data.get("documentation", "")
        if "docker" in doc.lower():
            complexity += 1
        if "api key" in doc.lower() or "token" in doc.lower():
            complexity += 1

        return min(complexity, 5)

    def _calculate_doc_score(self, server_data: Dict[str, Any]) -> float:
        """Calculate documentation quality score."""
        doc = server_data.get("readme_content") or server_data.get("documentation", "")
        if not doc:
            return 0.0

        score = 0.0
        doc_len = len(doc)

        # Length scoring
        if doc_len > 5000:
            score += 40
        elif doc_len > 2000:
            score += 30
        elif doc_len > 500:
            score += 20
        elif doc_len > 100:
            score += 10

        # Content quality
        if "## installation" in doc.lower():
            score += 15
        if "## usage" in doc.lower() or "## example" in doc.lower():
            score += 15
        if "## configuration" in doc.lower():
            score += 10
        if "```" in doc:  # Has code examples
            score += 10
        if "## api" in doc.lower():
            score += 10

        return min(score, 100)

    def _calculate_popularity_score(self, server_data: Dict[str, Any]) -> float:
        """Calculate popularity score based on stars, forks, etc."""
        if "metadata" in server_data:
            meta = server_data["metadata"]
        else:
            meta = server_data.get("metadata", {})

        stars = meta.get("stars", 0) or 0

        if stars > 5000:
            return 100.0
        elif stars > 1000:
            return 80.0
        elif stars > 100:
            return 60.0
        elif stars > 10:
            return 40.0
        elif stars > 0:
            return 20.0
        return 0.0

    def _calculate_maintenance_score(self, server_data: Dict[str, Any]) -> float:
        """Calculate maintenance score based on last update."""
        if "metadata" in server_data:
            meta = server_data["metadata"]
        else:
            meta = server_data.get("metadata", {})

        if not meta.get("last_updated"):
            return 50.0  # Unknown, assume average

        try:
            last_update = datetime.fromisoformat(
                meta["last_updated"].replace("Z", "+00:00")
            )
            days_ago = (datetime.now().astimezone() - last_update).days

            if days_ago < 30:
                return 100.0
            elif days_ago < 90:
                return 80.0
            elif days_ago < 180:
                return 60.0
            elif days_ago < 365:
                return 40.0
            else:
                return 20.0
        except:
            return 50.0

    def _calculate_completeness_score(self, server_data: Dict[str, Any]) -> float:
        """Calculate completeness score based on available metadata."""
        score = 0.0

        if "metadata" in server_data:
            meta = server_data["metadata"]
            doc = server_data.get("readme_content", "")
        else:
            meta = server_data.get("metadata", {})
            doc = server_data.get("documentation", "")

        # Check for essential fields
        if meta.get("description"):
            score += 10
        if meta.get("repository") or meta.get("repo_url"):
            score += 10
        if meta.get("npm_package") or meta.get("install_command"):
            score += 20
        if meta.get("transport_types"):
            score += 10
        if meta.get("capabilities"):
            score += 10
        if doc:
            score += 20
        if meta.get("env_vars") or "environment" in doc.lower():
            score += 10
        if meta.get("dependencies"):
            score += 10

        return min(score, 100)

    def _generate_tags(self, server_data: Dict[str, Any]) -> str:
        """Generate tags for the server."""
        tags = []

        if "metadata" in server_data:
            meta = server_data["metadata"]
        else:
            meta = server_data.get("metadata", {})

        # Add transport types as tags
        for transport in meta.get("transport_types", []):
            tags.append(f".. badge:: Transport: {transport}")

        # Add language tags
        languages = meta.get("languages", [])
        for lang in languages[:3]:  # Limit to 3
            tags.append(f".. badge:: Language: {lang}")

        # Add capability tags
        capabilities = meta.get("capabilities", [])
        for cap in capabilities[:3]:  # Limit to 3
            tags.append(f".. badge:: {cap}")

        return "\n".join(tags) if tags else "No tags available"

    def _generate_install_command(self, server_data: Dict[str, Any]) -> str:
        """Generate installation command."""
        if "metadata" in server_data:
            meta = server_data["metadata"]
        else:
            meta = server_data.get("metadata", {})

        # Check for npm package
        npm_package = meta.get("npm_package")
        if npm_package:
            return f"npx -y {npm_package}"

        # Check for custom install command
        install_cmd = meta.get("install_command")
        if install_cmd:
            return install_cmd

        # Check for repository
        repo = meta.get("repository") or meta.get("repo_url", "")
        if repo:
            return f"# Installation method: manual\n   # Please refer to the repository for installation instructions\n   git clone {repo}"

        return "# Installation instructions not available"

    def _generate_detailed_installation(self, server_data: Dict[str, Any]) -> str:
        """Generate detailed installation section."""
        content = []

        if "metadata" in server_data:
            meta = server_data["metadata"]
            doc = server_data.get("readme_content", "")
        else:
            meta = server_data.get("metadata", {})
            doc = server_data.get("documentation", "")

        # Check for dependencies
        deps = meta.get("dependencies", [])
        if deps:
            content.append("Dependencies")
            content.append("~~~~~~~~~~~~")
            content.append("")
            content.append("This server requires the following dependencies:")
            content.append("")
            for dep in deps:
                content.append(f"* {dep}")
            content.append("")

        # Check for setup instructions
        setup = meta.get("setup_instructions")
        if setup:
            content.append("Setup Instructions")
            content.append("~~~~~~~~~~~~~~~~~~")
            content.append("")
            if isinstance(setup, list):
                for i, step in enumerate(setup, 1):
                    content.append(f"{i}. {step}")
            else:
                content.append(setup)
            content.append("")

        return "\n".join(content)

    def _extract_features(self, server_data: Dict[str, Any]) -> str:
        """Extract features from documentation."""
        if "metadata" in server_data:
            meta = server_data["metadata"]
            doc = server_data.get("readme_content", "")
        else:
            meta = server_data.get("metadata", {})
            doc = server_data.get("documentation", "")

        features = []

        # Check capabilities
        caps = meta.get("capabilities", [])
        if caps:
            for cap in caps:
                features.append(f"* {cap}")

        # Extract from documentation
        if doc and "## features" in doc.lower():
            # Simple extraction logic
            lines = doc.split("\n")
            in_features = False
            for line in lines:
                if "## features" in line.lower():
                    in_features = True
                    continue
                if in_features and line.startswith("##"):
                    break
                if in_features and line.strip().startswith(("*", "-", "•")):
                    features.append(line.strip())

        if features:
            return "\n".join(features)
        return "Feature list not available. Check the repository for details."

    def _extract_api_info(self, server_data: Dict[str, Any]) -> str:
        """Extract API information."""
        if "metadata" in server_data:
            doc = server_data.get("readme_content", "")
        else:
            doc = server_data.get("documentation", "")

        if doc and "## api" in doc.lower():
            return "API documentation available in the repository README."

        return "API documentation not available in the extracted content."

    def _extract_env_vars(self, server_data: Dict[str, Any]) -> str:
        """Extract environment variables."""
        content = []

        if "metadata" in server_data:
            meta = server_data["metadata"]
            doc = server_data.get("readme_content", "")
        else:
            meta = server_data.get("metadata", {})
            doc = server_data.get("documentation", "")

        # Check metadata for env vars
        env_vars = meta.get("env_vars", {})
        if env_vars:
            for var, desc in env_vars.items():
                content.append(f"**{var}**")
                content.append(f"   {desc}")
                content.append("")

        # Try to extract from documentation
        if doc and not env_vars:
            lines = doc.split("\n")
            for line in lines:
                if "export" in line or "env" in line.lower():
                    if "=" in line and any(
                        var in line for var in ["API", "KEY", "TOKEN", "URL"]
                    ):
                        content.append(f".. code-block:: bash")
                        content.append("")
                        content.append(f"   {line.strip()}")
                        content.append("")

        return "\n".join(content) if content else "No environment variables documented."

    def _generate_transport_examples(
        self, server_name: str, transport_types: List[str]
    ) -> str:
        """Generate transport configuration examples."""
        content = []

        for transport in transport_types:
            content.append(f"* ``{transport}``")

        content.append("")
        content.append("For Claude Desktop configuration:")
        content.append("")
        content.append(".. code-block:: json")
        content.append("")
        content.append("   {")
        content.append('     "mcpServers": {')
        content.append(f'       "{server_name}": {{')
        content.append('         "command": "npx",')
        content.append(f'         "args": ["{server_name}"]')
        content.append("       }")
        content.append("     }")
        content.append("   }")

        return "\n".join(content)


def main():
    """Run the documentation generator."""
    generator = MCPDocumentationGenerator()
    generator.generate_all_documentation()


if __name__ == "__main__":
    main()
