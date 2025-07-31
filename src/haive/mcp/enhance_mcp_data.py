#!/usr/bin/env python3
"""Enhanced MCP Data Collector

Collects comprehensive information about MCP servers including:
- Full README content
- Detailed documentation
- Installation instructions
- Code examples
- Dependencies
"""

import argparse
import asyncio
import base64
import json
import logging
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubDataEnhancer:
    """Enhanced data collection from GitHub repositories."""

    def __init__(self, github_token: str | None = None):
        self.github_token = github_token
        self.session = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0

    async def __aenter__(self):
        headers = {"User-Agent": "MCP-Data-Enhancer/1.0"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        self.session = aiohttp.ClientSession(headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def extract_github_info(self, url: str) -> dict[str, str] | None:
        """Extract owner and repo from GitHub URL."""
        try:
            parsed = urlparse(url)
            if "github.com" not in parsed.netloc:
                return None

            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 2:
                return {"owner": path_parts[0], "repo": path_parts[1]}
        except Exception as e:
            logger.error(f"Error parsing GitHub URL {url}: {e}")

        return None

    async def check_rate_limit(self):
        """Check and respect GitHub rate limits."""
        if self.rate_limit_remaining <= 10:
            wait_time = max(0, self.rate_limit_reset - time.time())
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.0f} seconds...")
                await asyncio.sleep(wait_time)

    async def fetch_github_api(self, url: str) -> dict[str, Any] | None:
        """Fetch data from GitHub API with rate limiting."""
        await self.check_rate_limit()

        try:
            async with self.session.get(url) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(
                    response.headers.get(
                        "X-RateLimit-Remaining", self.rate_limit_remaining
                    )
                )
                self.rate_limit_reset = int(
                    response.headers.get("X-RateLimit-Reset", self.rate_limit_reset)
                )

                if response.status == 200:
                    return await response.json()
                if response.status == 403:
                    logger.warning(f"Rate limited or forbidden: {url}")
                    return None
                logger.warning(f"GitHub API error {response.status}: {url}")
                return None

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def get_repository_info(self, repo_url: str) -> dict[str, Any]:
        """Get comprehensive repository information."""
        github_info = self.extract_github_info(repo_url)
        if not github_info:
            return {"error": "Not a GitHub repository"}

        owner, repo = github_info["owner"], github_info["repo"]

        # Fetch basic repo info
        repo_data = await self.fetch_github_api(
            f"https://api.github.com/repos/{owner}/{repo}"
        )
        if not repo_data:
            return {"error": "Could not fetch repository data"}

        # Fetch README
        readme_data = await self.fetch_github_api(
            f"https://api.github.com/repos/{owner}/{repo}/readme"
        )
        readme_content = ""
        if readme_data and "content" in readme_data:
            try:
                readme_content = base64.b64decode(readme_data["content"]).decode(
                    "utf-8"
                )
            except Exception as e:
                logger.error(f"Error decoding README for {repo_url}: {e}")

        # Fetch package.json or pyproject.toml for dependencies
        dependencies = await self.get_dependencies(owner, repo)

        # Fetch latest releases
        releases = await self.fetch_github_api(
            f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=3"
        )

        # Fetch topics/tags
        topics = repo_data.get("topics", [])

        return {
            "name": repo_data.get("name"),
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description", ""),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "language": repo_data.get("language"),
            "topics": topics,
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "size": repo_data.get("size", 0),
            "open_issues": repo_data.get("open_issues_count", 0),
            "license": (
                repo_data.get("license", {}).get("name")
                if repo_data.get("license")
                else None
            ),
            "readme_content": readme_content,
            "dependencies": dependencies,
            "releases": releases[:3] if releases else [],
            "homepage": repo_data.get("homepage"),
            "has_wiki": repo_data.get("has_wiki", False),
            "has_projects": repo_data.get("has_projects", False),
            "has_issues": repo_data.get("has_issues", False),
            "archived": repo_data.get("archived", False),
            "disabled": repo_data.get("disabled", False),
        }

    async def get_dependencies(self, owner: str, repo: str) -> dict[str, Any]:
        """Extract dependencies from package files."""
        dependencies = {"npm": {}, "python": {}, "other": {}}

        # Check for package.json
        package_json = await self.fetch_github_api(
            f"https://api.github.com/repos/{owner}/{repo}/contents/package.json"
        )
        if package_json and "content" in package_json:
            try:
                content = base64.b64decode(package_json["content"]).decode("utf-8")
                package_data = json.loads(content)
                dependencies["npm"] = {
                    "dependencies": package_data.get("dependencies", {}),
                    "devDependencies": package_data.get("devDependencies", {}),
                    "peerDependencies": package_data.get("peerDependencies", {}),
                }
            except Exception as e:
                logger.error(f"Error parsing package.json for {owner}/{repo}: {e}")

        # Check for pyproject.toml
        pyproject = await self.fetch_github_api(
            f"https://api.github.com/repos/{owner}/{repo}/contents/pyproject.toml"
        )
        if pyproject and "content" in pyproject:
            try:
                content = base64.b64decode(pyproject["content"]).decode("utf-8")
                # Basic TOML parsing for dependencies
                if "[tool.poetry.dependencies]" in content:
                    dependencies["python"]["poetry"] = "Found poetry dependencies"
                if "dependencies" in content:
                    dependencies["python"]["general"] = "Found Python dependencies"
            except Exception as e:
                logger.error(f"Error parsing pyproject.toml for {owner}/{repo}: {e}")

        # Check for requirements.txt
        requirements = await self.fetch_github_api(
            f"https://api.github.com/repos/{owner}/{repo}/contents/requirements.txt"
        )
        if requirements and "content" in requirements:
            try:
                content = base64.b64decode(requirements["content"]).decode("utf-8")
                deps = [
                    line.strip()
                    for line in content.split("\n")
                    if line.strip() and not line.startswith("#")
                ]
                dependencies["python"]["requirements"] = deps
            except Exception as e:
                logger.error(f"Error parsing requirements.txt for {owner}/{repo}: {e}")

        return dependencies


class MCPDataEnhancer:
    """Main class for enhancing MCP server data."""

    def __init__(self, github_token: str | None = None):
        self.github_token = github_token
        self.data_path = (
            Path(__file__).parent.parent.parent.parent / "data" / "mcp_servers"
        )

    async def load_existing_data(self) -> list[dict[str, Any]]:
        """Load existing MCP servers data."""
        file_path = self.data_path / "ALL_MCP_SERVERS_COMPLETE.json"

        with open(file_path) as f:
            data = json.load(f)
            return data.get("all_servers", [])

    async def enhance_single_server(
        self, server: dict[str, Any], enhancer: GitHubDataEnhancer
    ) -> dict[str, Any]:
        """Enhance data for a single MCP server."""
        enhanced_server = server.copy()

        repo_url = server.get("repository_url", "")
        if not repo_url or "github.com" not in repo_url:
            enhanced_server["enhancement_status"] = "no_github_repo"
            return enhanced_server

        try:
            logger.info(f"Enhancing {server.get('name', 'Unknown')}...")

            # Get comprehensive GitHub data
            github_data = await enhancer.get_repository_info(repo_url)

            if "error" in github_data:
                enhanced_server["enhancement_status"] = f"error: {github_data['error']}"
                return enhanced_server

            # Merge enhanced data
            enhanced_server.update(
                {
                    "enhancement_status": "enhanced",
                    "enhanced_at": time.time(),
                    "github_data": github_data,
                    "full_description": github_data.get("description", ""),
                    "readme_content": github_data.get("readme_content", ""),
                    "dependencies": github_data.get("dependencies", {}),
                    "topics": github_data.get("topics", []),
                    "license": github_data.get("license"),
                    "latest_releases": github_data.get("releases", []),
                    "repo_stats": {
                        "stars": github_data.get("stars", 0),
                        "forks": github_data.get("forks", 0),
                        "open_issues": github_data.get("open_issues", 0),
                        "size_kb": github_data.get("size", 0),
                        "created_at": github_data.get("created_at"),
                        "updated_at": github_data.get("updated_at"),
                    },
                    "features": {
                        "has_wiki": github_data.get("has_wiki", False),
                        "has_issues": github_data.get("has_issues", False),
                        "has_projects": github_data.get("has_projects", False),
                        "archived": github_data.get("archived", False),
                    },
                }
            )

            # Update stars with actual count
            enhanced_server["stars"] = github_data.get("stars", server.get("stars", 0))

            # Add install instructions extraction
            if github_data.get("readme_content"):
                install_instructions = self.extract_install_instructions(
                    github_data["readme_content"]
                )
                enhanced_server["extracted_install_instructions"] = install_instructions

            return enhanced_server

        except Exception as e:
            logger.error(f"Error enhancing {server.get('name', 'Unknown')}: {e}")
            enhanced_server["enhancement_status"] = f"error: {e!s}"
            return enhanced_server

    def extract_install_instructions(self, readme_content: str) -> dict[str, str]:
        """Extract installation instructions from README content."""
        instructions = {}

        # Look for common installation patterns
        lines = readme_content.split("\n")

        current_section = None
        current_content = []

        for line in lines:
            line_lower = line.lower().strip()

            # Detect installation sections
            if any(
                keyword in line_lower
                for keyword in ["install", "setup", "getting started", "quick start"]
            ):
                if line.startswith("#"):
                    if current_section and current_content:
                        instructions[current_section] = "\n".join(current_content)
                    current_section = line.strip("# ").strip()
                    current_content = []
                    continue

            # Collect content
            if current_section:
                current_content.append(line)

        # Add last section
        if current_section and current_content:
            instructions[current_section] = "\n".join(current_content)

        return instructions

    async def enhance_all_servers(self, max_servers: int | None = None) -> None:
        """Enhance data for all MCP servers."""
        servers = await self.load_existing_data()

        if max_servers:
            servers = servers[:max_servers]

        logger.info(f"Starting enhancement of {len(servers)} MCP servers...")

        enhanced_servers = []

        async with GitHubDataEnhancer(self.github_token) as enhancer:
            for i, server in enumerate(servers, 1):
                logger.info(
                    f"Processing {i}/{len(servers)}: {server.get('name', 'Unknown')}"
                )

                enhanced_server = await self.enhance_single_server(server, enhancer)
                enhanced_servers.append(enhanced_server)

                # Small delay to be respectful
                await asyncio.sleep(0.5)

        # Save enhanced data
        output_data = {
            "metadata": {
                "enhanced_at": time.time(),
                "total_servers": len(enhanced_servers),
                "enhanced_count": sum(
                    1
                    for s in enhanced_servers
                    if s.get("enhancement_status") == "enhanced"
                ),
                "error_count": sum(
                    1
                    for s in enhanced_servers
                    if "error" in s.get("enhancement_status", "")
                ),
            },
            "all_servers": enhanced_servers,
        }

        # Save to new file
        output_path = (
            self.data_path / f"ALL_MCP_SERVERS_ENHANCED_{int(time.time())}.json"
        )
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"✅ Enhanced data saved to: {output_path}")
        logger.info(f"📊 Summary: {output_data['metadata']}")


async def main():
    """Main execution function."""

    parser = argparse.ArgumentParser(description="Enhance MCP servers data")
    parser.add_argument(
        "--github-token", help="GitHub API token for higher rate limits"
    )
    parser.add_argument(
        "--max-servers",
        type=int,
        help="Maximum number of servers to process (for testing)",
    )
    parser.add_argument(
        "--test", action="store_true", help="Test mode - process only 5 servers"
    )

    args = parser.parse_args()

    max_servers = args.max_servers
    if args.test:
        max_servers = 5

    enhancer = MCPDataEnhancer(github_token=args.github_token)
    await enhancer.enhance_all_servers(max_servers=max_servers)


if __name__ == "__main__":
    print("🚀 MCP Data Enhancement Tool")
    print("=" * 50)
    print("This tool will:")
    print("- Fetch full README content from GitHub")
    print("- Extract installation instructions")
    print("- Get comprehensive repository metadata")
    print("- Update star counts and other stats")
    print("- Collect dependency information")
    print()

    asyncio.run(main())
