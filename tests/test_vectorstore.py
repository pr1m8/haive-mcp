"""Test vector store directly to debug retrieval issues."""

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from haive.mcp.mcp_simple_rag_agent import create_mcp_documents


def test_vector_store():
    """Test vector store creation and search directly."""
    documents = create_mcp_documents()

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
        "github integration",
        "file system operations",
        "SQLAlchemy",
        "PostgreSQL",
    ]

    for query in queries:
        # Search
        results = vectorstore.similarity_search(query, k=5)

        for _i, doc in enumerate(results, 1):
            # Extract description
            content_lines = doc.page_content.split("\n")
            for line in content_lines:
                if line.startswith("Description:"):
                    desc = line.replace("Description:", "").strip()
                    if desc:
                        pass
                    break


if __name__ == "__main__":
    test_vector_store()
