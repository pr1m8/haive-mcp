#!/usr/bin/env python3
"""Self Query MCP Discovery Agent - Proper Haive Implementation.

This agent uses Haive's configuration system properly by extending BaseRAGAgent
and using SelfQueryRetrieverConfig instead of manually creating retrievers.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from haive.agents.rag.base.agent import BaseRAGAgent
from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.engine.embedding.providers.HuggingFaceEmbeddingConfig import (
    HuggingFaceEmbeddingConfig,
)
from haive.core.engine.retriever.providers.SelfQueryRetrieverConfig import (
    SelfQueryRetrieverConfig,
)
from haive.core.engine.vectorstore.providers.FAISSVectorStoreConfig import (
    FAISSVectorStoreConfig,
)
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
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


class MCPDocumentLoader:
    """Load and process MCP server documents."""

    @staticmethod
    def create_mcp_documents() -> List[Document]:
        """Create documents from MCP servers data."""
        # Load the data
        data_path = (
            Path(__file__).parent.parent.parent.parent
            / "data"
            / "mcp_servers"
            / "ALL_MCP_SERVERS_COMPLETE.json"
        )

        if not data_path.exists():
            # Fallback to a simple example document if data file doesn't exist
            return [
                Document(
                    page_content="Sample MCP server for testing",
                    metadata={
                        "server_name": "sample-server",
                        "category": "test",
                        "language": "python",
                        "stars": 0,
                        "tools_count": 1,
                        "resources_count": 0,
                        "prompts_count": 0,
                        "total_features": 1,
                        "has_install": True,
                        "type": "mcp_server",
                        "document_id": "mcp_server_0",
                    },
                )
            ]

        with open(data_path) as f:
            data = json.load(f)
            servers = data.get("all_servers", [])

        documents = []

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

            # Create document content
            content = f"""# MCP Server: {name}

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

            document = Document(page_content=content, metadata=metadata)
            documents.append(document)

        return documents


class SelfQueryMCPAgent(BaseRAGAgent):
    """Enhanced MCP Discovery Agent using proper Haive configuration system."""

    def __init__(self, name: str = "mcp_self_query_agent"):
        """Initialize with proper Haive configuration system."""

        # Create embedding config
        embedding_config = HuggingFaceEmbeddingConfig(
            model="sentence-transformers/all-mpnet-base-v2"
        )

        # Create vector store config
        vectorstore_config = FAISSVectorStoreConfig(
            name="mcp_vectorstore", embedding_config=embedding_config
        )

        # Create LLM config for self-query
        llm_config = AugLLMConfig(temperature=0.0, model="gpt-4")

        # Define metadata fields for self-query
        metadata_field_info = [
            {
                "name": "category",
                "description": "The category of the MCP server (database, web, file, utility, etc.)",
                "type": "string",
            },
            {
                "name": "language",
                "description": "The programming language of the server (python, javascript, typescript, etc.)",
                "type": "string",
            },
            {
                "name": "stars",
                "description": "The number of GitHub stars the repository has",
                "type": "integer",
            },
            {
                "name": "tools_count",
                "description": "The number of tools provided by the server",
                "type": "integer",
            },
            {
                "name": "resources_count",
                "description": "The number of resources provided by the server",
                "type": "integer",
            },
            {
                "name": "prompts_count",
                "description": "The number of prompts provided by the server",
                "type": "integer",
            },
            {
                "name": "total_features",
                "description": "The total number of features (tools + resources + prompts)",
                "type": "integer",
            },
            {
                "name": "has_install",
                "description": "Whether the server has installation instructions",
                "type": "boolean",
            },
        ]

        # Create self-query retriever config
        self_query_config = SelfQueryRetrieverConfig(
            name="mcp_self_query_retriever",
            vectorstore_config=vectorstore_config,
            llm_config=llm_config,
            document_content_description="MCP (Model Context Protocol) server information including name, description, tools, resources, prompts, and installation details",
            metadata_field_info=metadata_field_info,
            k=5,
        )

        # Initialize BaseRAGAgent with self-query retriever
        super().__init__(name=name, engine=self_query_config)

        # Load MCP documents into the vector store
        self._load_mcp_documents()

    def _load_mcp_documents(self):
        """Load MCP documents into the vector store."""
        try:
            # Create documents
            documents = MCPDocumentLoader.create_mcp_documents()

            # Get the vector store from our retriever config
            vectorstore = self.engine.vectorstore_config.instantiate()

            # Add documents to vector store
            vectorstore.add_documents(documents)

            print(f"✅ Loaded {len(documents)} MCP server documents into vector store")

        except Exception as e:
            print(f"⚠️ Warning: Could not load MCP documents: {e}")

    def analyze_query_intent(self, query: str) -> str:
        """Analyze query to determine if it's suitable for self-query."""
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

        if any(indicator in query_lower for indicator in structured_indicators):
            return "self_query"

        return "semantic"

    async def search_mcp_servers(self, query: str, k: int = 5) -> List[Document]:
        """Search for MCP servers using the configured retriever."""
        try:
            # Use the retriever from our BaseRAGAgent
            retriever = self.engine.instantiate()

            # Perform the search
            documents = await retriever.aget_relevant_documents(query)

            return documents[:k]

        except Exception as e:
            print(f"Error during search: {e}")
            return []


# Example usage and testing
async def test_mcp_agent():
    """Test the MCP agent."""
    print("🚀 Initializing MCP Self-Query Agent...")

    agent = SelfQueryMCPAgent()

    test_queries = [
        "Python database servers with more than 5 stars",
        "JavaScript web servers",
        "Servers in the database category with tools",
        "MCP servers for file system operations",
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print(f"Intent: {agent.analyze_query_intent(query)}")

        results = await agent.search_mcp_servers(query, k=3)

        print(f"Found {len(results)} results:")
        for i, doc in enumerate(results, 1):
            metadata = doc.metadata
            server_name = metadata.get("server_name", "Unknown")
            category = metadata.get("category", "unknown")
            language = metadata.get("language", "unknown")
            stars = metadata.get("stars", 0)

            print(f"  {i}. {server_name} ({category}, {language}, {stars} ⭐)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_mcp_agent())
