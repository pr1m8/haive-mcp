"""Working Enhanced MCP Retriever - Parent-Child + Self-Query Combined

This demonstrates the key pattern: metadata on child chunks enables
self-query filtering while returning full parent documents.
"""

import asyncio
import json
import sys

from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers import ParentDocumentRetriever
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from haive.core.engine.aug_llm import AugLLMConfig
from haive.mcp.documentation import MCPDocumentationLoader


# Core imports - using direct imports to avoid issues


sys.path.insert(0, "/home/will/Projects/haive/backend/haive/packages/haive-core/src")
sys.path.insert(0, "/home/will/Projects/haive/backend/haive/packages/haive-mcp/src")


# LangChain imports


class WorkingEnhancedRetriever:
    """Working implementation of combined parent-child + self-query retriever."""

    def __init__(self):
        self.doc_loader = MCPDocumentationLoader()
        self.embeddings = HuggingFaceEmbeddings()
        self.parent_store = InMemoryStore()
        self.child_vectorstore = None
        self.parent_retriever = None

    def setup(self):
        """Set up the enhanced retriever."""
        print("🔧 Setting up Enhanced Retriever...")

        # Load MCP servers
        all_servers_path = (
            self.doc_loader.mcp_servers_path / "ALL_MCP_SERVERS_COMPLETE.json"
        )
        with open(all_servers_path) as f:
            data = json.load(f)
            servers = data.get("all_servers", [])[:100]  # Limited for demo

        print(f"📚 Processing {len(servers)} MCP servers...")

        # Create parent documents with rich metadata
        parent_documents = []
        for server_data in servers:
            # Determine language
            repo_url = server_data.get("repository_url", "").lower()
            install_cmd = str(server_data.get("install_command", "")).lower()

            language = "unknown"
            if "python" in repo_url or "pip" in install_cmd or ".py" in install_cmd:
                language = "python"
            elif "javascript" in repo_url or "npm" in install_cmd or "node" in repo_url:
                language = "javascript"
            elif "rust" in repo_url:
                language = "rust"
            elif "go" in repo_url:
                language = "go"

            # Parent document content
            content = f"""
# {server_data.get("name", "Unknown")} MCP Server

**Category**: {server_data.get("category", "general")}
**Language**: {language}
**Stars**: {server_data.get("stars", 0)}

## Description
{server_data.get("description", "No description")}

## Capabilities
{", ".join(server_data.get("capabilities", [])) or "No capabilities listed"}

## Installation
{server_data.get("install_command", "No install command")}
"""

            # Metadata for BOTH parent and chunks
            metadata = {
                "doc_id": f"mcp_{server_data.get('name', '').replace('/', '_')}",
                "server_name": server_data.get("name", "unknown"),
                "category": server_data.get("category", "general").lower(),
                "stars": int(server_data.get("stars", 0) or 0),
                "language": language,
                "has_install": bool(server_data.get("install_command")),
            }

            doc = Document(page_content=content, metadata=metadata)
            parent_documents.append(doc)

        # Create vector store for child chunks
        self.child_vectorstore = Chroma(
            collection_name="mcp_chunks",
            embedding_function=self.embeddings,
            persist_directory="/tmp/mcp_enhanced_demo",
        )

        # Create parent document retriever
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=200, chunk_overlap=20
        )

        self.parent_retriever = ParentDocumentRetriever(
            vectorstore=self.child_vectorstore,
            docstore=self.parent_store,
            child_splitter=child_splitter,
            id_key="doc_id",
        )

        # Add documents
        print("📥 Adding documents with parent-child structure...")
        self.parent_retriever.add_documents(parent_documents)

        print("✅ Enhanced retriever ready!")

    def create_self_query_on_chunks(self, llm, query: str, k: int = 5):
        """Create self-query retriever that operates on child chunks."""
        # Metadata schema
        metadata_info = [
            AttributeInfo(
                name="category", description="Server category", type="string"
            ),
            AttributeInfo(name="stars", description="GitHub stars", type="integer"),
            AttributeInfo(
                name="language", description="Programming language", type="string"
            ),
            AttributeInfo(
                name="has_install",
                description="Has installation command",
                type="boolean",
            ),
        ]

        # Self-query retriever on child vectorstore
        retriever = SelfQueryRetriever.from_llm(
            llm=llm,
            vectorstore=self.child_vectorstore,
            document_contents="MCP server documentation",
            metadata_field_info=metadata_info,
            verbose=True,
        )

        return retriever

    async def enhanced_query(self, llm, query: str, k: int = 5):
        """The magic: Use self-query on chunks, return parent documents."""
        print(f"\n🔍 Enhanced Query: '{query}'")

        # Step 1: Self-query on child chunks
        self_query_retriever = self.create_self_query_on_chunks(llm, query, k * 2)
        chunks = await self_query_retriever.aget_relevant_documents(query)

        print(f"   Found {len(chunks)} matching chunks")

        # Step 2: Get unique parent IDs
        parent_ids = set()
        for chunk in chunks:
            if "doc_id" in chunk.metadata:
                parent_ids.add(chunk.metadata["doc_id"])

        print(f"   Mapping to {len(parent_ids)} parent documents")

        # Step 3: Retrieve full parents
        parents = []
        for pid in list(parent_ids)[:k]:
            parent = self.parent_store.mget([pid])[0]
            if parent:
                parents.append(parent)

        return parents


async def main():
    """Run working example."""
    print("🚀 Working Enhanced Retriever Demo")
    print("=" * 50)

    # Setup
    retriever = WorkingEnhancedRetriever()
    retriever.setup()

    # Create LLM for self-query
    engine = AugLLMConfig(name="query_engine", model="gpt-3.5-turbo", temperature=0)
    llm = engine.instantiate()

    # Test queries
    queries = [
        "Python MCP servers with more than 50 stars",
        "JavaScript database servers",
        "High quality servers with installation commands",
    ]

    for query in queries:
        docs = await retriever.enhanced_query(llm, query, k=3)

        print(f"\n📊 Results for: '{query}'")
        for i, doc in enumerate(docs):
            print(f"\n{i + 1}. {doc.metadata.get('server_name', 'Unknown')}")
            print(f"   Category: {doc.metadata.get('category')}")
            print(f"   Language: {doc.metadata.get('language')}")
            print(f"   Stars: {doc.metadata.get('stars')}")
            print(f"   Content preview: {doc.page_content[:100]}...")

    print("\n✅ Demo complete!")
    print("\n🔑 Key Pattern:")
    print("1. Metadata stored on BOTH parent docs AND child chunks")
    print("2. Self-query filters child chunks by metadata")
    print("3. Return full parent documents for context")
    print("4. Natural language queries with metadata filtering!")


if __name__ == "__main__":
    # Run it!
    asyncio.run(main())
