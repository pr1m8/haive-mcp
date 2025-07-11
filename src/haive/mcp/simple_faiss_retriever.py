"""
Simple FAISS-based MCP Retriever with Auto-Loading

Uses FAISS for vector storage and auto-loads MCP server documentation.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import pickle
import os

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from haive.mcp.documentation import MCPDocumentationLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter


class SimpleFAISSRetriever:
    """Simple FAISS-based retriever for MCP servers."""
    
    def __init__(self, cache_dir: str = "/tmp/mcp_faiss_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.doc_loader = MCPDocumentationLoader()
        self.embeddings = HuggingFaceEmbeddings()
        self.vectorstore = None
        self.documents = []
        
    def setup(self):
        """Set up the retriever with auto-loading."""
        print("🔧 Setting up Simple FAISS Retriever...")
        
        # Check if cache exists
        cache_path = self.cache_dir / "faiss_index"
        docs_cache_path = self.cache_dir / "documents.pkl"
        
        if cache_path.exists() and docs_cache_path.exists():
            print("📂 Loading from cache...")
            self.vectorstore = FAISS.load_local(
                str(cache_path), 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            with open(docs_cache_path, 'rb') as f:
                self.documents = pickle.load(f)
            print(f"✅ Loaded {len(self.documents)} documents from cache")
        else:
            print("📚 Building new index...")
            self._build_index()
            
    def _build_index(self):
        """Build the FAISS index from MCP server data."""
        # Load MCP servers
        all_servers_path = self.doc_loader.mcp_servers_path / "ALL_MCP_SERVERS_COMPLETE.json"
        with open(all_servers_path, 'r') as f:
            data = json.load(f)
            servers = data.get('all_servers', [])
            
        print(f"📊 Processing {len(servers)} MCP servers...")
        
        # Create documents
        documents = []
        for server in servers:
            # Main document
            content = f"""
Server: {server.get('name', 'Unknown')}
Description: {server.get('description', 'No description')}
Category: {server.get('category', 'general')}
Language: {server.get('language', 'unknown')}
Stars: {server.get('stars', 0)}
Install Command: {server.get('install_command', 'npm install')}
Repository: {server.get('repository_url', '')}

Tools: {', '.join(server.get('tools', []))}
Resources: {', '.join(server.get('resources', []))}
Prompts: {', '.join(server.get('prompts', []))}

Full Details: {json.dumps(server, indent=2)}
"""
            
            doc = Document(
                page_content=content,
                metadata={
                    "server_name": server.get('name', 'Unknown'),
                    "category": server.get('category', 'general'),
                    "language": server.get('language', 'unknown'),
                    "stars": server.get('stars', 0),
                    "has_install": bool(server.get('install_command')),
                    "repository_url": server.get('repository_url', ''),
                    "tools_count": len(server.get('tools', [])),
                    "resources_count": len(server.get('resources', [])),
                    "prompts_count": len(server.get('prompts', []))
                }
            )
            documents.append(doc)
            
        # Split documents for better retrieval
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", ", ", " "]
        )
        
        split_docs = text_splitter.split_documents(documents)
        print(f"📝 Created {len(split_docs)} chunks from {len(documents)} documents")
        
        # Create FAISS index
        self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
        self.documents = documents
        
        # Save to cache
        cache_path = self.cache_dir / "faiss_index"
        self.vectorstore.save_local(str(cache_path))
        
        docs_cache_path = self.cache_dir / "documents.pkl"
        with open(docs_cache_path, 'wb') as f:
            pickle.dump(self.documents, f)
            
        print("💾 Saved index to cache")
        
    def search(self, query: str, k: int = 5) -> List[Document]:
        """Search for relevant documents."""
        if not self.vectorstore:
            raise ValueError("Retriever not set up. Call setup() first.")
            
        results = self.vectorstore.similarity_search(query, k=k)
        return results
        
    async def asearch(self, query: str, k: int = 5) -> List[Document]:
        """Async search for relevant documents."""
        return self.search(query, k)
        
    def get_server_by_name(self, name: str) -> Dict[str, Any]:
        """Get a specific server by name."""
        for doc in self.documents:
            if doc.metadata.get('server_name', '').lower() == name.lower():
                return doc.metadata
        return {}
        
    def get_servers_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get servers by category."""
        results = []
        for doc in self.documents:
            if doc.metadata.get('category', '').lower() == category.lower():
                results.append(doc.metadata)
        return results
        
    def get_top_servers(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N servers by stars."""
        servers = [doc.metadata for doc in self.documents]
        return sorted(servers, key=lambda x: x.get('stars', 0), reverse=True)[:n]


# Test the retriever
if __name__ == "__main__":
    retriever = SimpleFAISSRetriever()
    retriever.setup()
    
    # Test queries
    test_queries = [
        "Python database servers",
        "GitHub integration",
        "file system operations",
        "weather data"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = retriever.search(query, k=3)
        for i, doc in enumerate(results, 1):
            print(f"  {i}. {doc.metadata.get('server_name')} ({doc.metadata.get('stars')} stars)")