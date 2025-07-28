"""Enhanced MCP Retriever combining Parent Document Retriever with Self-Query.

This implementation combines:
1. Parent-child document retrieval for context preservation
2. Self-query metadata filtering for natural language queries
3. Metadata propagation from parent to child chunks

The key insight: Store metadata on BOTH parent docs AND child chunks,
enabling self-query filtering on chunks while returning full parents.
"""

import asyncio
import json

# Haive imports
from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.engine.vectorstore.providers.ChromaVectorStoreConfig import (
    ChromaVectorStoreConfig,
)
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers import ParentDocumentRetriever
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

# LangChain imports
from langchain_core.documents import Document

from haive.mcp.documentation import MCPDocumentationLoader


class EnhancedMCPRetriever:
    """Enhanced retriever that combines parent-child documents with self-query.

    The trick: Create a custom retriever that:
    1. Uses self-query to filter child chunks by metadata
    2. Returns parent documents for matching chunks
    3. Maintains all metadata relationships
    """

    def __init__(self, engine: AugLLMConfig):
        self.engine = engine
        self.doc_loader = MCPDocumentationLoader()
        self.parent_retriever = None
        self.child_vectorstore = None
        self.parent_store = InMemoryStore()
        self.metadata_fields = []

    def _create_metadata_schema(self) -> list[AttributeInfo]:
        """Define metadata schema for self-query."""
        return [
            AttributeInfo(
                name="category",
                description="Server category like database, filesystem, api, etc.",
                type="string",
            ),
            AttributeInfo(
                name="stars", description="Number of GitHub stars", type="integer"
            ),
            AttributeInfo(
                name="has_capabilities",
                description="Whether server has listed capabilities",
                type="boolean",
            ),
            AttributeInfo(
                name="language",
                description="Primary programming language (python, javascript, etc.)",
                type="string",
            ),
            AttributeInfo(
                name="transport",
                description="Transport type (stdio, http, websocket)",
                type="string",
            ),
        ]

    async def setup_enhanced_retriever(self) -> None:
        """Set up the enhanced parent-child retriever with self-query."""
        print("🔧 Setting up Enhanced Parent-Child + Self-Query Retriever...")

        # Load server data
        all_servers_path = (
            self.doc_loader.mcp_servers_path / "ALL_MCP_SERVERS_COMPLETE.json"
        )
        with open(all_servers_path) as f:
            data = json.load(f)
            servers = data.get("all_servers", [])[:300]  # Limit for demo

        print(f"📚 Processing {len(servers)} MCP servers...")

        # Create enhanced parent documents with rich metadata
        parent_documents = []
        for server_data in servers:
            # Extract language from repository URL or other indicators
            repo_url = server_data.get("repository_url", "").lower()
            language = "unknown"
            if "python" in repo_url or ".py" in str(
                server_data.get("install_command", "")
            ):
                language = "python"
            elif "node" in repo_url or "npm" in str(
                server_data.get("install_command", "")
            ):
                language = "javascript"
            elif "rust" in repo_url:
                language = "rust"
            elif "go" in repo_url:
                language = "go"

            # Create comprehensive parent document
            parent_content = f"""
# {server_data.get("name", "Unknown")} MCP Server

**Repository**: {server_data.get("repository_url", "No URL")}
**Category**: {server_data.get("category", "general")}
**Stars**: {server_data.get("stars", 0)}
**Language**: {language}

## Description
{server_data.get("description", "No description available")}

## Capabilities
The server provides the following capabilities:
{chr(10).join("- " + cap for cap in server_data.get("capabilities", [])) or "No specific capabilities listed"}

## Installation
```bash
{server_data.get("install_command", "No installation command available")}
```

## Setup Instructions
{server_data.get("setup_instructions", "Follow repository README for setup")}

## Transport Configuration
Supported transport types: {", ".join(server_data.get("transport_types", ["stdio"]))}

## Additional Details
- Last updated: {server_data.get("last_updated", "Unknown")}
- Documentation available: {server_data.get("has_documentation", False)}
- Official server: {server_data.get("is_official", False)}
"""

            # Rich metadata for BOTH parent and child documents
            metadata = {
                # Identity
                "doc_id": f"mcp_server_{server_data.get('name', 'unknown').replace('/', '_')}",
                "server_name": server_data.get("name", "unknown"),
                # Self-query fields
                "category": server_data.get("category", "general").lower(),
                "stars": int(server_data.get("stars", 0) or 0),
                "has_capabilities": len(server_data.get("capabilities", [])) > 0,
                "language": language,
                "transport": (
                    server_data.get("transport_types", ["stdio"])[0]
                    if server_data.get("transport_types")
                    else "stdio"
                ),
                # Additional metadata
                "repository_url": server_data.get("repository_url", ""),
                "capability_count": len(server_data.get("capabilities", [])),
                "install_command": server_data.get("install_command", ""),
            }

            parent_doc = Document(page_content=parent_content, metadata=metadata)
            parent_documents.append(parent_doc)

        # Set up vector store for child chunks
        child_vs_config = ChromaVectorStoreConfig(
            name="mcp_enhanced_chunks",
            collection_name="mcp_child_chunks_enhanced",
            persist_directory="/tmp/mcp_enhanced_chunks",
        )
        self.child_vectorstore = child_vs_config.instantiate()

        # Create text splitter for child chunks
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,  # Larger chunks for better context
            chunk_overlap=50,
            separators=["\n## ", "\n### ", "\n\n", "\n", " "],
        )

        # Set up parent document retriever
        self.parent_retriever = ParentDocumentRetriever(
            vectorstore=self.child_vectorstore,
            docstore=self.parent_store,
            child_splitter=child_splitter,
            id_key="doc_id",  # Use our custom doc_id
        )

        # Add documents - this creates child chunks with parent metadata
        print("📥 Creating child chunks with parent metadata...")
        self.parent_retriever.add_documents(parent_documents)

        # Store metadata schema
        self.metadata_fields = self._create_metadata_schema()

        print("✅ Enhanced retriever ready!")

    def create_self_query_retriever(self, k: int = 5) -> SelfQueryRetriever:
        """Create a self-query retriever that works with parent documents."""
        # Create self-query retriever on the child vectorstore
        # but we'll modify it to return parent documents

        llm = self.engine.instantiate()

        return SelfQueryRetriever.from_llm(
            llm=llm,
            vectorstore=self.child_vectorstore,
            document_contents="MCP server documentation including setup, capabilities, and configuration",
            metadata_field_info=self.metadata_fields,
            search_kwargs={"k": k * 2},  # Get more chunks, we'll dedupe parents
        )

    async def query_with_parent_context(self, query: str, k: int = 5) -> list[Document]:
        """Query using self-query on chunks but return full parent documents.

        This is the key method that combines both approaches!
        """
        print(f"\n🔍 Enhanced Query: '{query}'")

        # Step 1: Use self-query to find relevant child chunks
        self_query_retriever = self.create_self_query_retriever(k=k * 2)
        child_chunks = await self_query_retriever.aget_relevant_documents(query)

        print(f"   Found {len(child_chunks)} relevant chunks")

        # Step 2: Get unique parent document IDs
        parent_ids = set()
        for chunk in child_chunks:
            if "doc_id" in chunk.metadata:
                parent_ids.add(chunk.metadata["doc_id"])

        print(f"   Mapping to {len(parent_ids)} unique parent documents")

        # Step 3: Retrieve full parent documents
        parent_docs = []
        for parent_id in list(parent_ids)[:k]:  # Limit to k parents
            parent_doc = self.parent_store.mget([parent_id])[0]
            if parent_doc:
                parent_docs.append(parent_doc)

        # Step 4: Sort by relevance (using stars as a proxy)
        parent_docs.sort(key=lambda d: d.metadata.get("stars", 0), reverse=True)

        return parent_docs

    async def demonstrate_queries(self) -> None:
        """Demonstrate various query patterns."""
        print("\n📊 Demonstrating Enhanced Retrieval Patterns...")

        queries = [
            # Natural language with metadata filters
            "Python database servers with more than 50 stars",
            "JavaScript servers for API integration",
            "Filesystem tools that support HTTP transport",
            "High-quality GitHub integration servers",
            "Rust-based MCP servers with capabilities",
            # Pure semantic search that still benefits from metadata
            "PostgreSQL connection management",
            "Real-time data synchronization tools",
            "Authentication and security servers",
        ]

        for query in queries[:3]:  # Demo first 3
            docs = await self.query_with_parent_context(query, k=3)

            print(f"\n📍 Query: '{query}'")
            print(f"   Results: {len(docs)} parent documents")

            for i, doc in enumerate(docs):
                print(f"\n   {i + 1}. {doc.metadata.get('server_name', 'Unknown')}")
                print(f"      Category: {doc.metadata.get('category', 'Unknown')}")
                print(f"      Language: {doc.metadata.get('language', 'Unknown')}")
                print(f"      Stars: {doc.metadata.get('stars', 0)}")
                print(f"      Transport: {doc.metadata.get('transport', 'Unknown')}")
                print(
                    f"      Has Capabilities: {doc.metadata.get('has_capabilities', False)}"
                )

    async def find_and_analyze_best_server(self, requirements: str) -> Document | None:
        """Find the best server matching requirements using enhanced retrieval."""
        print(f"\n🎯 Finding best server for: '{requirements}'")

        # Use enhanced retrieval
        docs = await self.query_with_parent_context(requirements, k=10)

        if not docs:
            print("❌ No servers found")
            return None

        # Analyze and rank results
        print(f"\n📈 Analyzing {len(docs)} candidates...")

        # Score based on multiple factors
        scored_docs = []
        for doc in docs:
            score = 0

            # Stars weight
            stars = doc.metadata.get("stars", 0)
            score += min(stars / 10, 50)  # Cap at 50 points

            # Has capabilities
            if doc.metadata.get("has_capabilities", False):
                score += 20

            # Has install command
            if doc.metadata.get("install_command"):
                score += 15

            # Language match (if Python mentioned in requirements)
            if (
                "python" in requirements.lower()
                and doc.metadata.get("language") == "python"
            ):
                score += 15

            scored_docs.append((score, doc))

        # Sort by score
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        best_doc = scored_docs[0][1]
        best_score = scored_docs[0][0]

        print(f"\n🏆 Best Match: {best_doc.metadata.get('server_name', 'Unknown')}")
        print(f"   Score: {best_score:.1f}/100")
        print(f"   Category: {best_doc.metadata.get('category', 'Unknown')}")
        print(f"   Language: {best_doc.metadata.get('language', 'Unknown')}")
        print(f"   Stars: {best_doc.metadata.get('stars', 0)}")

        return best_doc


# === EXAMPLE USAGE ===


async def main():
    """Run the enhanced retriever example."""
    print("🚀 Enhanced Parent-Child + Self-Query Retriever for MCP Servers")
    print("=" * 70)

    # Initialize
    engine = AugLLMConfig(
        name="mcp_enhanced_engine",
        model="gpt-4",
        temperature=0.3,  # Lower for more consistent parsing
    )

    retriever = EnhancedMCPRetriever(engine)

    # Setup
    await retriever.setup_enhanced_retriever()

    # Demonstrate queries
    await retriever.demonstrate_queries()

    # Find best server for specific requirements
    requirements = "Python database server with high stars for PostgreSQL integration"
    best_server = await retriever.find_and_analyze_best_server(requirements)

    if best_server:
        print("\n\n📄 Full Documentation:")
        print("-" * 70)
        print(best_server.page_content[:1000] + "...")

    print("\n\n✅ Enhanced retrieval demonstration complete!")
    print("\n🔑 Key Features Demonstrated:")
    print("   1. Self-query parsing of natural language")
    print("   2. Metadata filtering on child chunks")
    print("   3. Parent document retrieval for full context")
    print("   4. Rich metadata schema (category, stars, language, etc.)")
    print("   5. Intelligent ranking based on multiple factors")


if __name__ == "__main__":
    asyncio.run(main())
