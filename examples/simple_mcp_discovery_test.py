#!/usr/bin/env python3
"""Simple MCP Tool Discovery Test

Tests the core discovery functionality without requiring the web interface.
"""

import asyncio
import json

# Direct imports from the MCP components
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "haive" / "mcp"))

from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


class SimpleMCPDiscovery:
    """Simplified MCP discovery for testing"""

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
        """Load MCP servers data"""
        print(f"📚 Loading MCP data from: {self.data_path}")

        if not self.data_path.exists():
            print(f"❌ Data file not found at: {self.data_path}")
            return []

        with open(self.data_path) as f:
            data = json.load(f)
            servers = data.get("all_servers", [])

        print(f"✅ Loaded {len(servers)} MCP servers")
        return servers

    def create_documents(self, servers: list[dict[str, Any]]) -> list[Document]:
        """Create searchable documents from server data"""
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
        """Initialize the search system"""
        servers = self.load_mcp_data()
        if not servers:
            return False

        self.documents = self.create_documents(servers)
        print(f"📄 Created {len(self.documents)} searchable documents")

        # Create vector store
        print("🔍 Creating search index...")
        self.vectorstore = FAISS.from_documents(self.documents, self.embeddings)
        print("✅ Search index ready")

        return True

    async def search_tools(self, query: str, k: int = 5) -> list[Document]:
        """Search for MCP tools"""
        if not self.vectorstore:
            print("❌ Search index not initialized")
            return []

        print(f"\n🔍 Searching for: {query}")
        docs = self.vectorstore.similarity_search(query, k=k)

        return docs


async def test_discovery():
    """Test the discovery system"""
    print("🚀 Testing MCP Tool Discovery")
    print("=" * 60)

    discovery = SimpleMCPDiscovery()

    # Setup search
    if not discovery.setup_search():
        print("❌ Failed to setup search system")
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

        print(f"\nQuery: '{query}'")
        print("-" * 50)

        if results:
            for i, doc in enumerate(results, 1):
                metadata = doc.metadata
                print(f"\n{i}. {metadata.get('server_name', 'Unknown')}")
                print(f"   Category: {metadata.get('category', 'unknown')}")
                print(f"   Language: {metadata.get('language', 'unknown')}")
                print(f"   Stars: {metadata.get('stars', 0)} ⭐")
                print(f"   Has Tools: {'✅' if metadata.get('has_tools') else '❌'}")
                print(f"   Description: {metadata.get('description', 'N/A')[:80]}...")
        else:
            print("No results found")


async def show_haive_integration():
    """Show how to integrate with haive agents"""
    print("\n\n🤖 Haive Agent Integration")
    print("=" * 60)

    print(
        """
After discovering a tool, here's how to integrate it with a haive agent:

1. Install the MCP server:
   pip install <mcp-server-name>
   # or
   npm install -g <mcp-server-name>

2. Create a tool wrapper:

```python
from haive.agents.react import ReactAgent
from haive.core.engine.aug_llm import AugLLMConfig
from langchain_core.tools import tool

@tool
def mcp_calculator(expression: str) -> str:
    \"\"\"Use MCP calculator to evaluate expressions\"\"\"
    # Here you would connect to the MCP server
    # For now, a simple example:
    try:
        result = eval(expression)
        return f"Result: {result}"
    except:
        return "Error: Invalid expression"

# Create agent with the tool
agent = ReactAgent(
    name="math_agent",
    engine=AugLLMConfig(),
    tools=[mcp_calculator]
)

# Use the agent
result = await agent.arun("Calculate 25 * 4")
```

3. Or use the integrated system:
   python integrated_launcher.py web
   - Search for tools
   - Click install
   - Tools are automatically configured!
"""
    )


if __name__ == "__main__":
    asyncio.run(test_discovery())
    asyncio.run(show_haive_integration())
