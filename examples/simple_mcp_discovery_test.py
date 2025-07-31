#!/usr/bin/env python3
"""Simple MCP Tool Discovery Test.

Tests the core discovery functionality without requiring the web interface.
"""

import asyncio
import json

# Direct imports from the MCP components
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "haive" / "mcp"))

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.vectorstores import FAISS


class SimpleMCPDiscovery:
    """Simplified MCP discovery for testing."""

    def __init__(self):
        self.data_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "data"
            / "mcp_servers"
            / "ALL_MCP_SERVERS_COMPLETE.json"
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        self.documents = []
        self.vectorstore = None

    def load_mcp_data(self) -> list[dict[str, Any]]:
        """Load MCP servers data."""
        if not self.data_path.exists():
            return []

        with open(self.data_path) as f:
            data = json.load(f)
            servers = data.get("all_servers", [])

        return servers

    def create_documents(self, servers: list[dict[str, Any]]) -> list[Document]:
        """Create searchable documents from server data."""
        documents = []

        for server in servers:
            # Extract key information
            name = server.get("name", "Unknown")
            description = server.get("description", "No description")
            category = server.get("category", "general")
            language = server.get("language", "unknown")
            stars = server.get("stars", 0) or 0
            tools = server.get("tools", [])

            # Create searchable content
            content = f"""
MCP Server: {name}
Category: {category}
Language: {language}
Stars: {stars}
Description: {description}
Tools: {", ".join(tools) if tools else "No tools listed"}
Keywords: {category} {language} tool server MCP {name.lower().replace("-", " ")}
"""

            doc = Document(
                page_content=content,
                metadata={
                    "server_name": name,
                    "category": category,
                    "language": language,
                    "stars": stars,
                    "tools_count": len(tools),
                    "has_tools": len(tools) > 0,
                    "description": description,
                },
            )
            documents.append(doc)

        return documents

    def setup_search(self):
        """Initialize the search system."""
        servers = self.load_mcp_data()
        if not servers:
            return False

        self.documents = self.create_documents(servers)

        # Create vector store
        self.vectorstore = FAISS.from_documents(self.documents, self.embeddings)

        return True

    async def search_tools(self, query: str, k: int = 5) -> list[Document]:
        """Search for MCP tools."""
        if not self.vectorstore:
            return []

        docs = self.vectorstore.similarity_search(query, k=k)

        return docs


async def test_discovery():
    """Test the discovery system."""
    discovery = SimpleMCPDiscovery()

    # Setup search
    if not discovery.setup_search():
        return

    # Test queries
    test_queries = [
        "calculator tool",
        "Python database tools",
        "web scraping",
        "file system operations",
        "API integration tools",
    ]

    for query in test_queries:
        results = await discovery.search_tools(query, k=3)

        if results:
            for _i, _doc in enumerate(results, 1):
                pass
        else:
            pass


async def show_haive_integration():
    """Show how to integrate with haive agents."""


if __name__ == "__main__":
    asyncio.run(test_discovery())
    asyncio.run(show_haive_integration())
