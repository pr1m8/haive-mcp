"""Complete End-to-End MCP Example with Parent Document Retriever.

This example demonstrates:
1. Parent-child document retrieval for MCP servers
2. Self-query capabilities with metadata filtering
3. HITL approval for server installation
4. Live server testing with tools, resources, and prompts
5. Hierarchical categorization with AutoTree

The parent-child pattern allows:
- Small chunks for precise similarity search (capabilities, keywords)
- Full server documentation returned for context
- Metadata filtering (stars, category, etc.) via self-query
"""

import asyncio
import json
import subprocess
import sys
import tempfile
from typing import Any

from haive.agents.rag.base.agent import BaseRAGAgent
from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.engine.retriever.providers.ParentDocumentRetrieverConfig import (
    ParentDocumentRetrieverConfig,
)
from haive.core.engine.retriever.providers.SelfQueryRetrieverConfig import (
    SelfQueryRetrieverConfig,
)
from haive.core.engine.vectorstore.providers.ChromaVectorStoreConfig import (
    ChromaVectorStoreConfig,
)
from langchain_core.documents import Document
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel, Field

from haive.mcp.documentation import MCPDocumentationLoader

# For running the actual test


# Haive imports

# LangChain imports

# Pydantic models


# === MODELS ===


class MCPServerInfo(BaseModel):
    """Complete MCP server information."""

    name: str
    repository_url: str
    description: str
    category: str
    stars: int = 0
    install_command: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    setup_instructions: str | None = None
    transport_types: list[str] = Field(default_factory=list)


class HITLRequest(BaseModel):
    """HITL approval request."""

    action: str
    server_name: str
    risk_level: str = "medium"
    details: dict[str, Any] = Field(default_factory=dict)


# === COMPLETE SYSTEM ===


class MCPSystemWithParentRetriever:
    """MCP system using parent-child document retrieval."""

    def __init__(self, engine: AugLLMConfig):
        self.engine = engine
        self.doc_loader = MCPDocumentationLoader()
        self.parent_retriever = None
        self.self_query_retriever = None
        self.rag_agent = None
        self.installed_servers: dict[str, dict] = {}

    async def setup_retrievers(self) -> None:
        """Set up both parent-child and self-query retrievers."""
        # Load all server documents
        all_servers_path = (
            self.doc_loader.mcp_servers_path / "ALL_MCP_SERVERS_COMPLETE.json"
        )
        with open(all_servers_path) as f:
            data = json.load(f)
            servers = data.get("all_servers", [])

        # Create parent documents (full server info)
        parent_documents = []
        for server_data in servers[:500]:  # Limit for demo
            # Create comprehensive parent document
            parent_content = f"""
# {server_data.get("name", "Unknown")}

**Repository**: {server_data.get("repository_url", "No URL")}
**Category**: {server_data.get("category", "general")}
**Stars**: {server_data.get("stars", 0)}

## Description
{server_data.get("description", "No description available")}

## Capabilities
{", ".join(server_data.get("capabilities", [])) or "No capabilities listed"}

## Installation
{server_data.get("install_command", "No installation command available")}

## Setup Instructions
{server_data.get("setup_instructions", "No setup instructions available")}

## Transport Types
{", ".join(server_data.get("transport_types", ["stdio"]))}
"""

            # Metadata for both parent and child docs
            metadata = {
                "server_id": server_data.get("name", "unknown"),
                "category": server_data.get("category", "general"),
                "stars": server_data.get("stars", 0) or 0,
                "has_install": bool(server_data.get("install_command")),
                "capability_count": len(server_data.get("capabilities", [])),
                "repository_url": server_data.get("repository_url", ""),
            }

            parent_doc = Document(page_content=parent_content, metadata=metadata)
            parent_documents.append(parent_doc)

        # === SETUP PARENT-CHILD RETRIEVER ===

        # Vector store for child chunks
        child_vs_config = ChromaVectorStoreConfig(
            name="mcp_child_chunks",
            collection_name="mcp_server_chunks",
            persist_directory="/tmp/mcp_child_chunks",
        )

        # Parent document retriever config
        parent_retriever_config = ParentDocumentRetrieverConfig(
            name="mcp_parent_retriever",
            vectorstore_config=child_vs_config,
            child_chunk_size=200,  # Small chunks for precise search
            child_chunk_overlap=20,
            k=5,  # Return top 5 parent documents
        )

        # Instantiate parent retriever
        self.parent_retriever = parent_retriever_config.instantiate()

        # Add documents to parent retriever
        self.parent_retriever.add_documents(parent_documents)

        # === SETUP SELF-QUERY RETRIEVER (for metadata filtering) ===

        # Separate vector store for self-query
        self_query_vs_config = ChromaVectorStoreConfig(
            name="mcp_self_query",
            collection_name="mcp_self_query_docs",
            persist_directory="/tmp/mcp_self_query",
        )

        # Add documents to self-query vector store
        vs = self_query_vs_config.instantiate()
        vs.add_documents(parent_documents)

        # Define metadata fields
        metadata_fields = [
            {
                "name": "category",
                "description": "Server category (filesystem, database, etc.)",
                "type": "string",
            },
            {"name": "stars", "description": "GitHub stars", "type": "integer"},
            {
                "name": "has_install",
                "description": "Has installation command",
                "type": "boolean",
            },
            {
                "name": "capability_count",
                "description": "Number of capabilities",
                "type": "integer",
            },
        ]

        # Self-query retriever config
        self_query_config = SelfQueryRetrieverConfig(
            name="mcp_self_query",
            vectorstore_config=self_query_vs_config,
            llm_config=self.engine,
            document_content_description="MCP server documentation with setup instructions and capabilities",
            metadata_field_info=metadata_fields,
            k=10,
        )

        self.self_query_retriever = self_query_config.instantiate()

        # === CREATE RAG AGENT ===

        # Create a RAG agent using the parent retriever
        self.rag_agent = BaseRAGAgent(
            name="MCP_RAG_Agent",
            engine=parent_retriever_config,  # Use parent retriever as engine
        )

    async def demonstrate_retrieval(self) -> None:
        """Demonstrate different retrieval patterns."""
        # 1. Parent-child retrieval (semantic search)
        parent_docs = await self.parent_retriever.aget_relevant_documents(
            "database integration PostgreSQL"
        )

        for _i, _doc in enumerate(parent_docs[:3]):
            pass

        # 2. Self-query retrieval (metadata filtering)
        self_query_docs = await self.self_query_retriever.aget_relevant_documents(
            "database servers with more than 50 stars"
        )

        for _i, _doc in enumerate(self_query_docs[:3]):
            pass

        # 3. RAG agent query
        rag_result = await self.rag_agent.arun(
            {"query": "Find MCP servers for GitHub integration with good documentation"}
        )

        if rag_result and "documents" in rag_result:
            for _doc in rag_result["documents"][:2]:
                pass

    async def install_top_server_with_hitl(self) -> str | None:
        """Find and install top server with HITL approval."""
        # Use self-query to find high-quality servers
        query = "GitHub or database servers with more than 100 stars"
        docs = await self.self_query_retriever.aget_relevant_documents(query)

        if not docs:
            return None

        # Sort by stars and pick top
        sorted_docs = sorted(
            docs, key=lambda d: d.metadata.get("stars", 0), reverse=True
        )
        top_doc = sorted_docs[0]

        server_info = MCPServerInfo(
            name=top_doc.metadata.get("server_id", "unknown"),
            repository_url=top_doc.metadata.get("repository_url", ""),
            description=top_doc.page_content[:200],
            category=top_doc.metadata.get("category", "general"),
            stars=top_doc.metadata.get("stars", 0),
        )

        # HITL Approval

        response = input("\nApprove installation? (y/n): ").lower().strip()

        if response != "y":
            return None

        # Install server (simplified for demo)
        return await self._install_server(server_info)

    async def _install_server(self, server_info: MCPServerInfo) -> str | None:
        """Install MCP server with FastMCP."""
        # Generate FastMCP server
        server_code = f'''"""
MCP Server: {server_info.name}
Category: {server_info.category}
Generated from haive-mcp database
"""


mcp = FastMCP("{server_info.name}")

# Tool example
@mcp.tool()
async def get_server_info() -> dict:
    """Get information about this MCP server."""
    return {{
        "name": "{server_info.name}",
        "category": "{server_info.category}",
        "stars": {server_info.stars},
        "repository": "{server_info.repository_url}"
    }}

# Tool based on category
@mcp.tool()
async def process_data(input_text: str) -> str:
    """Process data using {server_info.category} capabilities."""
    return f"Processed using {server_info.name}: {{input_text}}"

# Resource example
@mcp.resource("server://metadata")
async def server_metadata() -> str:
    """Server metadata resource."""
    return """{server_info.name} - Category: {server_info.category}, Stars: {server_info.stars}"""

# Prompt example
@mcp.prompt()
async def analysis_prompt(topic: str) -> list:
    """Generate analysis prompt for {server_info.category}."""
    return [{{
        "role": "user",
        "content": f"Analyze {{topic}} using {server_info.category} best practices"
    }}]

if __name__ == "__main__":
    mcp.run(transport="stdio")
'''

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(server_code)
            server_path = f.name

        self.installed_servers[server_info.name] = {
            "path": server_path,
            "info": server_info,
        }

        return server_path

    async def test_installed_server(self, server_name: str) -> None:
        """Test installed server with all MCP capabilities."""
        if server_name not in self.installed_servers:
            return

        server_data = self.installed_servers[server_name]
        server_path = server_data["path"]

        # Create MCP client
        client_config = {
            server_name: {
                "command": "python",
                "args": [server_path],
                "transport": "stdio",
            }
        }

        client = MultiServerMCPClient(client_config)

        try:
            async with client.session(server_name) as session:
                # 1. Test Tools
                tools_result = await session.list_tools()
                tools = tools_result.tools if hasattr(tools_result, "tools") else []

                for _tool in tools:
                    pass

                # Call a tool
                if tools:
                    await session.call_tool(tools[0].name, arguments={})

                # 2. Test Resources
                resources_result = await session.list_resources()
                resources = (
                    resources_result.resources
                    if hasattr(resources_result, "resources")
                    else []
                )

                for _resource in resources:
                    pass

                # Read a resource
                if resources:
                    content = await session.read_resource(resources[0].uri)
                    if content.contents:
                        pass

                # 3. Test Prompts
                prompts_result = await session.list_prompts()
                prompts = (
                    prompts_result.prompts if hasattr(prompts_result, "prompts") else []
                )

                for _prompt in prompts:
                    pass

                # Generate a prompt
                if prompts:
                    prompt_result = await session.get_prompt(
                        prompts[0].name, arguments={"topic": "MCP integration patterns"}
                    )
                    if prompt_result.messages:
                        prompt_result.messages[0]

        except Exception:
            import traceback

            traceback.print_exc()


# === MAIN EXECUTION ===


async def main():
    """Run the complete end-to-end example."""
    # Initialize
    engine = AugLLMConfig(name="mcp_engine", model="gpt-4", temperature=0.7)

    system = MCPSystemWithParentRetriever(engine)

    # Step 1: Setup retrievers
    await system.setup_retrievers()

    # Step 2: Demonstrate retrieval patterns
    await system.demonstrate_retrieval()

    # Step 3: Install top server with HITL
    server_path = await system.install_top_server_with_hitl()

    if server_path:
        # Step 4: Test the installed server
        server_name = next(iter(system.installed_servers.keys()))
        await system.test_installed_server(server_name)


if __name__ == "__main__":
    # Ensure we have FastMCP available
    try:
        pass
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "fastmcp"], check=True)

    # Run the example
    asyncio.run(main())
