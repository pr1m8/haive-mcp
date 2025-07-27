#!/usr/bin/env python3
"""Self Query MCP Discovery Agent

Enhanced RAG agent that uses Self Query methodology for structured querying
with metadata filtering and parent document retrieval.
"""

import asyncio
import json
from pathlib import Path

from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers import ParentDocumentRetriever
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.schema import Document
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class MCPServerMetadata(BaseModel):
    """Metadata schema for MCP servers."""

    server_name: str = Field(description="Name of the MCP server")
    category: str = Field(description="Server category (database, web, file, etc.)")
    language: str = Field(description="Programming language")
    stars: int = Field(description="GitHub stars count")
    tools_count: int = Field(description="Number of available tools")
    resources_count: int = Field(description="Number of available resources")
    prompts_count: int = Field(description="Number of available prompts")
    has_install: bool = Field(description="Whether server has install command")
    total_features: int = Field(description="Total tools + resources + prompts")


class EnhancedMCPDocument:
    """Enhanced document creation with chunking for parent retrieval."""

    @staticmethod
    def create_mcp_documents_with_chunks() -> tuple[list[Document], list[Document]]:
        """Create both parent documents and child chunks for retrieval."""
        # Load the data
        data_path = (
            Path(__file__).parent.parent.parent.parent
            / "data"
            / "mcp_servers"
            / "ALL_MCP_SERVERS_COMPLETE.json"
        )

        with open(data_path) as f:
            data = json.load(f)
            servers = data.get("all_servers", [])

        print(f"📚 Processing {len(servers)} MCP servers for enhanced retrieval...")

        parent_docs = []
        child_docs = []

        # Text splitter for creating chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", " ", ""]
        )

        for i, server in enumerate(servers):
            # Extract server details
            name = server.get("name", "Unknown")
            description = server.get("description", "No description available")
            category = server.get("category", "general")
            language = server.get("language", "unknown")
            stars = server.get("stars", 0) or 0
            install_command = server.get("install_command", "")
            repository_url = server.get("repository_url", "")
            tools = server.get("tools", [])
            resources = server.get("resources", [])
            prompts = server.get("prompts", [])
            use_cases = server.get("use_cases", "General purpose MCP server")
            installation_notes = server.get(
                "installation_notes", "Standard MCP installation"
            )

            # Create comprehensive metadata
            metadata = {
                "server_name": name,
                "category": category,
                "language": language,
                "stars": stars,
                "has_install": bool(install_command),
                "repository_url": repository_url,
                "tools_count": len(tools),
                "resources_count": len(resources),
                "prompts_count": len(prompts),
                "total_features": len(tools) + len(resources) + len(prompts),
                "type": "mcp_server",
                "document_id": f"mcp_server_{i}",
                "source": str(data_path),
            }

            # Create detailed parent document content
            parent_content = f"""
# MCP Server: {name}

## Description
{description}

## Server Information
- **Category**: {category}
- **Language**: {language}
- **GitHub Stars**: {stars}
- **Repository**: {repository_url}
- **Install Command**: {install_command}

## Available Features

### Tools ({len(tools)})
{chr(10).join(f"- {tool}" for tool in tools) if tools else "No tools available"}

### Resources ({len(resources)})
{chr(10).join(f"- {resource}" for resource in resources) if resources else "No resources available"}

### Prompts ({len(prompts)})
{chr(10).join(f"- {prompt}" for prompt in prompts) if prompts else "No prompts available"}

## Use Cases
{use_cases}

## Installation Instructions
{installation_notes}

## Technical Details
- Total Features: {len(tools) + len(resources) + len(prompts)}
- Has Install Command: {"Yes" if install_command else "No"}
- Repository Available: {"Yes" if repository_url else "No"}

## Keywords
{category} {language} MCP server {name.lower().replace("-", " ")} database python nodejs javascript typescript sql postgresql mysql sqlite github file system web api tools resources prompts
            """.strip()

            # Create parent document
            parent_doc = Document(page_content=parent_content, metadata=metadata.copy())
            parent_docs.append(parent_doc)

            # Create child chunks
            chunks = text_splitter.split_text(parent_content)
            for j, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update(
                    {
                        "chunk_id": f"{i}_{j}",
                        "parent_id": f"mcp_server_{i}",
                        "chunk_index": j,
                    }
                )

                child_doc = Document(page_content=chunk, metadata=chunk_metadata)
                child_docs.append(child_doc)

        print(
            f"✅ Created {len(parent_docs)} parent documents and {len(child_docs)} child chunks"
        )
        return parent_docs, child_docs


class SelfQueryMCPAgent:
    """Enhanced MCP Discovery Agent with Self Query and Parent Document Retrieval."""

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        self.llm = ChatOpenAI(temperature=0, model="gpt-4")
        self.setup_retrievers()

    def setup_retrievers(self):
        """Set up both self-query and parent document retrievers."""
        # Create documents
        parent_docs, child_docs = EnhancedMCPDocument.create_mcp_documents_with_chunks()

        # 1. Standard vector store for self-query
        self.vectorstore = FAISS.from_documents(child_docs, self.embeddings)

        # 2. Parent document retriever setup
        self.docstore = InMemoryStore()
        self.parent_retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            child_splitter=RecursiveCharacterTextSplitter(
                chunk_size=500, chunk_overlap=50
            ),
            parent_splitter=RecursiveCharacterTextSplitter(
                chunk_size=2000, chunk_overlap=100
            ),
        )

        # Add parent documents to the docstore
        for doc in parent_docs:
            self.docstore.mset([(doc.metadata["document_id"], doc)])

        # 3. Self-query retriever with metadata attributes
        self.metadata_field_info = [
            AttributeInfo(
                name="category",
                description="The category of the MCP server (database, web, file, utility, etc.)",
                type="string",
            ),
            AttributeInfo(
                name="language",
                description="The programming language of the server (python, javascript, typescript, etc.)",
                type="string",
            ),
            AttributeInfo(
                name="stars",
                description="The number of GitHub stars the repository has",
                type="integer",
            ),
            AttributeInfo(
                name="tools_count",
                description="The number of tools provided by the server",
                type="integer",
            ),
            AttributeInfo(
                name="resources_count",
                description="The number of resources provided by the server",
                type="integer",
            ),
            AttributeInfo(
                name="prompts_count",
                description="The number of prompts provided by the server",
                type="integer",
            ),
            AttributeInfo(
                name="total_features",
                description="The total number of features (tools + resources + prompts)",
                type="integer",
            ),
            AttributeInfo(
                name="has_install",
                description="Whether the server has installation instructions",
                type="boolean",
            ),
        ]

        document_content_description = "MCP (Model Context Protocol) server information including name, description, tools, resources, prompts, and installation details"

        self.self_query_retriever = SelfQueryRetriever.from_llm(
            self.llm,
            self.vectorstore,
            document_content_description,
            self.metadata_field_info,
            verbose=True,
        )

    async def search_with_self_query(self, query: str, k: int = 5) -> list[Document]:
        """Search using self-query retriever for structured queries."""
        print(f"🔍 Self-query search: {query}")

        try:
            docs = await asyncio.to_thread(
                self.self_query_retriever.get_relevant_documents, query
            )

            print(f"📚 Self-query found {len(docs)} documents")
            return docs[:k]

        except Exception as e:
            print(f"❌ Self-query error: {e}")
            # Fallback to standard similarity search
            return await self.search_similarity(query, k)

    async def search_with_parent_retriever(
        self, query: str, k: int = 5
    ) -> list[Document]:
        """Search using parent document retriever for full content."""
        print(f"🔍 Parent document search: {query}")

        try:
            docs = await asyncio.to_thread(
                self.parent_retriever.get_relevant_documents, query
            )

            print(f"📚 Parent retriever found {len(docs)} full documents")
            return docs[:k]

        except Exception as e:
            print(f"❌ Parent retriever error: {e}")
            return await self.search_similarity(query, k)

    async def search_similarity(self, query: str, k: int = 5) -> list[Document]:
        """Fallback similarity search."""
        print(f"🔍 Similarity search: {query}")

        docs = await asyncio.to_thread(self.vectorstore.similarity_search, query, k=k)

        print(f"📚 Similarity search found {len(docs)} documents")
        return docs

    async def hybrid_search(self, query: str, k: int = 5) -> dict[str, list[Document]]:
        """Perform all search methods and return results."""
        print(f"🚀 Hybrid search for: {query}")

        results = {}

        # Self-query search (best for structured queries)
        results["self_query"] = await self.search_with_self_query(query, k)

        # Parent document search (best for full content)
        results["parent_docs"] = await self.search_with_parent_retriever(query, k)

        # Standard similarity search (fallback)
        results["similarity"] = await self.search_similarity(query, k)

        return results

    def analyze_query_intent(self, query: str) -> str:
        """Analyze query to determine best search method."""
        query_lower = query.lower()

        # Structured query indicators
        structured_indicators = [
            "with",
            "having",
            "stars",
            "category",
            "language",
            "tools",
            "resources",
            "prompts",
            "features",
        ]

        # Content query indicators
        content_indicators = [
            "how to",
            "install",
            "setup",
            "configure",
            "example",
            "documentation",
            "readme",
            "instructions",
        ]

        if any(indicator in query_lower for indicator in structured_indicators):
            return "self_query"
        if any(indicator in query_lower for indicator in content_indicators):
            return "parent_docs"
        return "similarity"


async def test_enhanced_agent():
    """Test the enhanced MCP agent."""
    agent = SelfQueryMCPAgent()

    test_queries = [
        "Python database servers with more than 5 stars",
        "JavaScript web servers",
        "Servers in the database category with tools",
        "How to install PostgreSQL MCP servers",
        "MCP servers for file system operations",
        "TypeScript servers with resources and prompts",
    ]

    for query in test_queries:
        print(f"\n{'=' * 80}")
        print(f"🔍 Query: {query}")
        print(f"{'=' * 80}")

        # Determine best search method
        method = agent.analyze_query_intent(query)
        print(f"🎯 Recommended method: {method}")

        # Perform hybrid search
        results = await agent.hybrid_search(query, k=3)

        for search_type, docs in results.items():
            print(f"\n📊 {search_type.upper()} Results ({len(docs)} found):")
            print("-" * 50)

            for i, doc in enumerate(docs, 1):
                metadata = doc.metadata
                content_preview = (
                    doc.page_content[:200] + "..."
                    if len(doc.page_content) > 200
                    else doc.page_content
                )

                print(f"{i}. {metadata.get('server_name', 'Unknown')}")
                print(f"   Category: {metadata.get('category', 'unknown')}")
                print(f"   Language: {metadata.get('language', 'unknown')}")
                print(f"   Stars: {metadata.get('stars', 0)}")
                print(f"   Features: {metadata.get('total_features', 0)}")
                print(f"   Preview: {content_preview}")
                print()


if __name__ == "__main__":
    print("🚀 Enhanced MCP Discovery Agent with Self Query & Parent Retrieval")
    print("=" * 80)

    asyncio.run(test_enhanced_agent())
