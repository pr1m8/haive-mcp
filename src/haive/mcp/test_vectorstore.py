"""
Test vector store directly to debug retrieval issues
"""

import asyncio
from haive.mcp.mcp_simple_rag_agent import create_mcp_documents
from haive.core.models.embeddings.base import HuggingFaceEmbeddingConfig
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


def test_vector_store():
    """Test vector store creation and search directly."""
    print("📚 Loading documents...")
    documents = create_mcp_documents()
    print(f"✅ Loaded {len(documents)} documents")
    
    # Create embeddings
    print("\n🔧 Creating embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'cuda'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Create vector store
    print("\n📊 Creating FAISS vector store...")
    vectorstore = FAISS.from_documents(documents, embeddings)
    print(f"✅ Vector store created")
    
    # Test searches
    queries = [
        "python database",
        "github integration",
        "file system operations",
        "SQLAlchemy",
        "PostgreSQL"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"🔍 Query: {query}")
        print(f"{'='*60}")
        
        # Search
        results = vectorstore.similarity_search(query, k=5)
        
        print(f"\n📚 Found {len(results)} results:")
        for i, doc in enumerate(results, 1):
            print(f"\n{i}. {doc.metadata.get('server_name', 'Unknown')}")
            print(f"   Category: {doc.metadata.get('category', 'unknown')}")
            print(f"   Language: {doc.metadata.get('language', 'unknown')}")
            print(f"   Stars: {doc.metadata.get('stars', 0)}")
            
            # Extract description
            content_lines = doc.page_content.split('\n')
            for line in content_lines:
                if line.startswith("Description:"):
                    desc = line.replace("Description:", "").strip()
                    if desc:
                        print(f"   Description: {desc}")
                    break


if __name__ == "__main__":
    print("🧪 Testing vector store directly...")
    test_vector_store()