#!/usr/bin/env python3
"""Simple Discovery Demo.

Shows how to use existing haive-mcp components to discover and analyze
MCP servers and other ecosystem resources.

Usage:
    poetry run python examples/simple_discovery_demo.py
"""

import asyncio
import contextlib
from typing import Any

from haive.core.engine import AugLLMConfig

# Import what we actually have available
from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.documentation import MCPDocumentationLoader


class SimpleDiscoveryAgent:
    """Simple agent for discovering and analyzing MCP resources."""

    def __init__(self):
        self.loader = MCPDocumentationLoader()

        # Create an MCP agent that can use GitHub and filesystem tools for discovery
        self.mcp_config = MCPConfig(
            enabled=True,
            servers={
                "github": MCPServerConfig(
                    name="github",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-github"],
                    # Note: In real usage, you'd need GITHUB_TOKEN env var
                ),
                "filesystem": MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem"],
                ),
            },
        )

        self.engine = AugLLMConfig(name="discovery_engine")
        self.agent = MCPAgent(
            engine=self.engine, mcp_config=self.mcp_config, name="discovery_agent"
        )

    async def setup(self):
        """Initialize the discovery agent."""
        with contextlib.suppress(Exception):
            await self.agent.setup()

    async def analyze_current_database(self) -> dict[str, Any]:
        """Analyze our current 992-server database."""
        try:
            # Load our comprehensive database
            all_servers = self.loader.load_all_mcp_documents()

            # Analyze the database
            analysis = {
                "total_servers": len(all_servers),
                "categories": {},
                "popular_patterns": [],
                "installation_methods": {},
                "transport_types": {},
            }

            for server_name, server_doc in all_servers.items():
                # Categorize by common patterns
                if "filesystem" in server_name.lower():
                    analysis["categories"]["filesystem"] = (
                        analysis["categories"].get("filesystem", 0) + 1
                    )
                elif "github" in server_name.lower():
                    analysis["categories"]["github"] = (
                        analysis["categories"].get("github", 0) + 1
                    )
                elif "database" in server_name.lower() or "sql" in server_name.lower():
                    analysis["categories"]["database"] = (
                        analysis["categories"].get("database", 0) + 1
                    )
                elif "search" in server_name.lower():
                    analysis["categories"]["search"] = (
                        analysis["categories"].get("search", 0) + 1
                    )
                else:
                    analysis["categories"]["other"] = (
                        analysis["categories"].get("other", 0) + 1
                    )

                # Look for installation patterns in content
                content = server_doc.get("content", "").lower()
                if "npm install" in content:
                    analysis["installation_methods"]["npm"] = (
                        analysis["installation_methods"].get("npm", 0) + 1
                    )
                if "pip install" in content:
                    analysis["installation_methods"]["pip"] = (
                        analysis["installation_methods"].get("pip", 0) + 1
                    )
                if "docker" in content:
                    analysis["installation_methods"]["docker"] = (
                        analysis["installation_methods"].get("docker", 0) + 1
                    )

            return analysis

        except Exception as e:
            return {"error": str(e)}

    async def find_capability_gaps(self) -> list[str]:
        """Identify capability gaps in our current database."""
        # Use our agent to analyze what capabilities might be missing
        gap_analysis_prompt = """
        Based on the current MCP server ecosystem, what types of capabilities
        or integrations might be missing that would be valuable for AI agents?

        Consider:
        1. Popular APIs that don't have MCP servers yet
        2. Common developer tools lacking MCP integration
        3. Emerging technologies that could benefit from MCP
        4. Workflow automation opportunities

        Provide a prioritized list of missing capabilities.
        """

        try:
            result = await self.agent.arun(
                {"messages": [{"role": "user", "content": gap_analysis_prompt}]}
            )

            # Parse the result to extract gaps
            return self._parse_capability_gaps(result)

        except Exception:
            # Return some common gaps we know about
            return [
                "Microsoft Office integration",
                "Slack/Discord bots",
                "CI/CD pipeline tools",
                "Cloud cost monitoring",
                "Kubernetes management",
                "Social media APIs",
                "E-commerce platforms",
            ]

    def _parse_capability_gaps(self, result) -> list[str]:
        """Parse LLM result to extract capability gaps."""
        # Handle different result types from agent
        if hasattr(result, "content"):
            content = result.content
        elif hasattr(result, "messages") and result.messages:
            content = (
                result.messages[-1].content
                if result.messages[-1].content
                else str(result.messages[-1])
            )
        else:
            content = str(result)

        # Simple parsing - in real implementation would be more sophisticated
        lines = content.split("\n")
        gaps = []

        for line in lines:
            line = line.strip()
            if line and (line.startswith(("-", "*")) or line[0].isdigit()):
                # Clean up the line
                clean_line = line.lstrip("-*0123456789. ").strip()
                if clean_line:
                    gaps.append(clean_line)

        return gaps[:10]  # Return top 10

    async def suggest_ecosystem_expansions(self) -> dict[str, list[str]]:
        """Suggest other ecosystems we could apply this pattern to."""
        ecosystems = {
            "langchain_tools": [
                "Document loaders",
                "Text splitters",
                "Vector stores",
                "Retrieval methods",
                "Custom tools",
            ],
            "huggingface_models": [
                "Text generation models",
                "Code generation models",
                "Embedding models",
                "Specialized domain models",
                "Multimodal models",
            ],
            "docker_images": [
                "Development environments",
                "Database containers",
                "Web servers",
                "ML frameworks",
                "Microservices",
            ],
            "github_actions": [
                "CI/CD workflows",
                "Testing frameworks",
                "Deployment actions",
                "Code quality tools",
                "Security scanning",
            ],
            "vscode_extensions": [
                "Language support",
                "Debugging tools",
                "Productivity extensions",
                "Theme and UI enhancements",
                "Integration tools",
            ],
        }

        return ecosystems


async def main():
    """Run the simple discovery demo."""
    # Create discovery agent
    agent = SimpleDiscoveryAgent()
    await agent.setup()

    # 1. Analyze current database
    analysis = await agent.analyze_current_database()

    if "error" not in analysis:
        for _category, _count in analysis["categories"].items():
            pass

        for _method, _count in analysis["installation_methods"].items():
            pass

    # 2. Find capability gaps
    gaps = await agent.find_capability_gaps()
    for _i, _gap in enumerate(gaps, 1):
        pass

    # 3. Suggest ecosystem expansions
    ecosystems = await agent.suggest_ecosystem_expansions()
    for _ecosystem, examples in ecosystems.items():
        for _example in examples[:3]:  # Show first 3 examples
            pass


if __name__ == "__main__":
    asyncio.run(main())
