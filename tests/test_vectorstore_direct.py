"""Direct test of vector store functionality without haive imports."""

import json
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


def test_vector_store():
    """Test vector store creation and search directly."""
    # Load MCP data
    data_path = Path("data/mcp_servers/ALL_MCP_SERVERS_COMPLETE.json")
    with open(data_path) as f:
        data = json.load(f)
        servers = data.get("all_servers", [])

    # Create documents focusing on database-related servers
    documents = []
    for server in servers[:500]:  # Test with first 500
        name = server.get("name", "Unknown")
        description = server.get("description", "")
        category = server.get("category", "general")

        # Create searchable content
        content = f"""
MCP Server: {name}
Description: {description}
Category: {category}
Keywords: {category} {name.lower().replace("-", " ")} MCP server
"""

        # Add extra keywords for database servers
        if any(
            word in name.lower() or word in description.lower()
            for word in ["database", "sql", "postgres", "mysql", "sqlite", "db"]
        ):
            content += "\nDatabase Keywords: database SQL query python"

        doc = Document(
            page_content=content,
            metadata={
                "server_name": name,
                "category": category,
                "description": description,
            },
        )
        documents.append(doc)

    # Create embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Create vector store
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Test searches
    queries = [
        "python database",
        "SQLAlchemy",
        "PostgreSQL",
        "database connections",
        "SQL server",
    ]

    for query in queries:
        # Search
        results = vectorstore.similarity_search(query, k=5)

        for _i, doc in enumerate(results, 1):
            if doc.metadata.get("description"):
                pass


if __name__ == "__main__":
    test_vector_store()
