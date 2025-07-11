"""
Direct test of vector store functionality without haive imports
"""
import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


def test_vector_store():
    """Test vector store creation and search directly."""
    print("📚 Loading documents...")
    
    # Load MCP data
    data_path = Path("data/mcp_servers/ALL_MCP_SERVERS_COMPLETE.json")
    with open(data_path, 'r') as f:
        data = json.load(f)
        servers = data.get('all_servers', [])
    
    print(f"📊 Found {len(servers)} servers")
    
    # Create documents focusing on database-related servers
    documents = []
    for server in servers[:500]:  # Test with first 500
        name = server.get('name', 'Unknown')
        description = server.get('description', '')
        category = server.get('category', 'general')
        
        # Create searchable content
        content = f"""
MCP Server: {name}
Description: {description}
Category: {category}
Keywords: {category} {name.lower().replace('-', ' ')} MCP server
"""
        
        # Add extra keywords for database servers
        if any(word in name.lower() or word in description.lower() 
               for word in ['database', 'sql', 'postgres', 'mysql', 'sqlite', 'db']):
            content += "\nDatabase Keywords: database SQL query python"
        
        doc = Document(
            page_content=content,
            metadata={
                'server_name': name,
                'category': category,
                'description': description
            }
        )
        documents.append(doc)
    
    print(f"✅ Created {len(documents)} documents")
    
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
        "SQLAlchemy",
        "PostgreSQL",
        "database connections",
        "SQL server"
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
            if doc.metadata.get('description'):
                print(f"   Description: {doc.metadata.get('description')[:100]}...")


if __name__ == "__main__":
    print("🧪 Testing vector store directly...")
    test_vector_store()