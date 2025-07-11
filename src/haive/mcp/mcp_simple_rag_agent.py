"""
MCP Simple RAG Agent - Using Haive's proper patterns

This agent uses BaseRAGAgent and SimpleAgent to create a proper RAG system
for MCP server discovery.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from haive.agents.rag.base.agent import BaseRAGAgent
from haive.core.models.embeddings.base import HuggingFaceEmbeddingConfig
from haive.core.models.llm.base import AzureLLMConfig, LLMConfig
from haive.core.engine.retriever.retriever import VectorStoreRetrieverConfig
from haive.core.engine.vectorstore.vectorstore import VectorStoreConfig
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


def create_mcp_documents() -> List[Document]:
    """Create documents from MCP server data with improved searchability."""
    print("📚 Loading MCP server data...")
    
    # Direct path to the MCP servers data
    all_servers_path = Path(__file__).parent.parent.parent.parent / "data" / "mcp_servers" / "ALL_MCP_SERVERS_COMPLETE.json"
    
    # Load JSON data manually (haive document loader has JSON parsing issues)
    with open(all_servers_path, 'r') as f:
        data = json.load(f)
        servers = data.get('all_servers', [])
    
    print(f"📊 Processing {len(servers)} MCP servers into documents...")
    
    documents = []
    for server in servers:
        # Get server details
        name = server.get('name', 'Unknown')
        description = server.get('description', 'No description available')
        category = server.get('category', 'general')
        language = server.get('language', 'unknown')
        stars = server.get('stars', 0)
        install_command = server.get('install_command', 'npm install')
        repository_url = server.get('repository_url', '')
        tools = server.get('tools', [])
        resources = server.get('resources', [])
        prompts = server.get('prompts', [])
        use_cases = server.get('use_cases', 'General purpose MCP server')
        installation_notes = server.get('installation_notes', 'Standard MCP installation')
        
        # Create rich document content with enhanced searchability
        content = f"""
MCP Server: {name}

Description: {description}

Category: {category}
Language: {language}
Programming Language: {language}
Stars: {stars}
Install Command: {install_command}
Repository: {repository_url}

Available Tools:
{chr(10).join(f"- {tool}" for tool in tools)}

Available Resources:
{chr(10).join(f"- {resource}" for resource in resources)}

Available Prompts:
{chr(10).join(f"- {prompt}" for prompt in prompts)}

Use Cases: {use_cases}

Installation: {installation_notes}

Keywords: {category} {language} MCP server {name.lower().replace('-', ' ')} database python nodejs javascript typescript sql postgresql mysql sqlite github file system web api
Tool Count: {len(tools)}
Resource Count: {len(resources)}
Prompt Count: {len(prompts)}
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
                "prompts_count": len(server.get('prompts', [])),
                "type": "mcp_server",
                "document_id": f"mcp_server_{len(documents)}",
                "source": str(all_servers_path)
            }
        )
        documents.append(doc)
    
    print(f"✅ Created {len(documents)} MCP server documents")
    return documents


def create_mcp_rag_agent(llm_config: Optional[LLMConfig] = None) -> BaseRAGAgent:
    """Create a BaseRAG agent using direct vector store for MCP discovery."""
    
    # Load MCP documents
    documents = create_mcp_documents()
    
    # Use defaults if no config provided
    if not llm_config:
        llm_config = AzureLLMConfig()
    
    print("📊 Creating embeddings with GPU support...")
    # Create embedding config
    embedding_model = HuggingFaceEmbeddingConfig(
        model="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'cuda'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    print("📊 Creating MCP RAG agent with VectorStoreConfig...")
    
    # Create vector store config with documents
    vs_config = VectorStoreConfig(
        provider="FAISS",
        embedding_model=embedding_model,
        documents=documents,  # Pass documents directly
        k=10,  # Return top 10 results
        search_type="similarity",
        score_threshold=0.5
    )
    
    print(f"✅ Creating agent with {len(documents)} documents...")
    
    # Create agent with vector store config as engine
    agent = BaseRAGAgent(
        name="MCP_Discovery_Agent",
        engine=vs_config  # Use VectorStoreConfig as engine
    )
    
    print(f"✅ Agent created successfully")
    return agent


# FastAPI Integration for web interface
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    response: str
    timestamp: str


# Create FastAPI app
app = FastAPI(
    title="MCP Discovery Agent",
    description="Ask questions about MCP servers and get expert recommendations",
    version="1.0.0"
)

# Global agent instance
mcp_agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize the MCP RAG agent."""
    global mcp_agent
    print("🚀 Initializing MCP Discovery Agent...")
    mcp_agent = create_mcp_rag_agent()
    print("✅ Agent ready!")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Web interface for the MCP agent."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>MCP Discovery Agent</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .chat-container {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #eee;
            border-radius: 10px;
            padding: 15px;
            background: #fafafa;
        }
        .message {
            margin: 15px 0;
            padding: 12px 16px;
            border-radius: 10px;
            max-width: 80%;
        }
        .user-message {
            background: #e3f2fd;
            margin-left: auto;
            text-align: right;
        }
        .agent-message {
            background: white;
            border: 1px solid #ddd;
            white-space: pre-wrap;
            line-height: 1.4;
        }
        .input-container {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        input {
            flex: 1;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        input:focus {
            border-color: #667eea;
        }
        button {
            padding: 15px 30px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .examples {
            margin-top: 25px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .examples h3 {
            margin-top: 0;
            color: #555;
        }
        .example {
            display: inline-block;
            margin: 5px;
            padding: 8px 15px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
        }
        .example:hover {
            background: #e3f2fd;
            transform: translateY(-1px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 20px;
            display: none;
        }
        .loading.active {
            display: block;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            background: #28a745;
            color: white;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 MCP Discovery Agent</h1>
        <p class="subtitle">Your intelligent assistant for finding the perfect MCP servers</p>
        
        <div class="chat-container" id="chat"></div>
        
        <div class="loading" id="loading">
            <p>🔍 Searching through 1,960 MCP servers...</p>
        </div>
        
        <div class="input-container">
            <input 
                type="text" 
                id="query" 
                placeholder="Ask about MCP servers... e.g., 'Python servers for databases'"
                onkeypress="handleKeyPress(event)"
            />
            <button onclick="askQuestion()" id="askBtn">Ask</button>
        </div>
        
        <div class="examples">
            <h3>💡 Try these examples:</h3>
            <div class="example" onclick="setExample(this)">
                What Python MCP servers can help with databases?
            </div>
            <div class="example" onclick="setExample(this)">
                Find the most popular GitHub integration servers
            </div>
            <div class="example" onclick="setExample(this)">
                Which MCP server is best for file system operations?
            </div>
            <div class="example" onclick="setExample(this)">
                Compare Slack integration MCP servers
            </div>
            <div class="example" onclick="setExample(this)">
                What tools does the weather MCP server provide?
            </div>
            <div class="example" onclick="setExample(this)">
                Show me TypeScript servers with high star ratings
            </div>
        </div>
    </div>
    
    <script>
        function setExample(element) {
            document.getElementById('query').value = element.textContent.trim();
            document.getElementById('query').focus();
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                askQuestion();
            }
        }
        
        async function askQuestion() {
            const input = document.getElementById('query');
            const query = input.value.trim();
            if (!query) return;
            
            const chatDiv = document.getElementById('chat');
            const loadingDiv = document.getElementById('loading');
            const askBtn = document.getElementById('askBtn');
            
            // Add user message
            chatDiv.innerHTML += `
                <div class="message user-message">
                    <strong>You:</strong> ${query}
                </div>
            `;
            
            // Clear input and show loading
            input.value = '';
            input.disabled = true;
            askBtn.disabled = true;
            loadingDiv.classList.add('active');
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query})
                });
                
                const data = await response.json();
                
                // Add agent response
                chatDiv.innerHTML += `
                    <div class="message agent-message">
                        <strong>🤖 MCP Assistant:</strong>
                        ${data.response}
                    </div>
                `;
                
                // Scroll to bottom
                chatDiv.scrollTop = chatDiv.scrollHeight;
                
            } catch (error) {
                chatDiv.innerHTML += `
                    <div class="message agent-message" style="color: red;">
                        <strong>Error:</strong> ${error.message}
                    </div>
                `;
            } finally {
                input.disabled = false;
                askBtn.disabled = false;
                loadingDiv.classList.remove('active');
                input.focus();
            }
        }
        
        // Focus on load
        window.onload = () => {
            document.getElementById('query').focus();
        };
    </script>
</body>
</html>
"""


@app.post("/ask", response_model=QueryResponse)
async def ask_agent(request: QueryRequest):
    """Ask the MCP agent a question."""
    if not mcp_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        print(f"🔍 Processing query: {request.query}")
        
        # Run the query through the agent with debug
        print(f"🔍 Running agent with debug=True...")
        import sys
        sys.stdout.flush()
        
        result = await mcp_agent.arun(request.query, debug=True)
        
        print(f"✅ Got result type: {type(result)}")
        print(f"✅ Got result: {result}")
        
        # Debug: Print all attributes of the result
        if hasattr(result, '__dict__'):
            print(f"🔍 Result attributes: {result.__dict__}")
        
        # Handle RetrieverOutput object
        response_text = ""
        
        if hasattr(result, 'retrieved_documents'):
            docs = result.retrieved_documents
            query_used = getattr(result, 'query', request.query)
            
            print(f"📚 Retrieved {len(docs)} documents for query: '{query_used}'")
            
            if docs:
                # Format the retrieved documents into a readable response
                response_text = f"Found {len(docs)} relevant MCP servers for '{query_used}':\n\n"
                
                for i, doc in enumerate(docs[:5], 1):
                    server_name = doc.metadata.get('server_name', 'Unknown')
                    category = doc.metadata.get('category', 'general')
                    stars = doc.metadata.get('stars', 0)
                    repo_url = doc.metadata.get('repository_url', '')
                    
                    response_text += f"{i}. **{server_name}** ({category})\n"
                    response_text += f"   ⭐ {stars} stars\n"
                    if repo_url:
                        response_text += f"   🔗 {repo_url}\n"
                    
                    # Extract description from content
                    content_lines = doc.page_content.split('\n')
                    description = ""
                    for line in content_lines:
                        if line.startswith("Description:"):
                            description = line.replace("Description:", "").strip()
                            break
                    
                    if description and description != "No description available":
                        response_text += f"   📝 {description}\n"
                    
                    response_text += "\n"
            else:
                # No documents found - try direct vector store search as fallback
                print(f"⚠️ No documents retrieved. Trying direct vector store search...")
                
                try:
                    # Get the vector store from the agent
                    if hasattr(mcp_agent, '_compiled_app') and hasattr(mcp_agent._compiled_app, 'nodes'):
                        # Try to get the vector store config
                        vector_store_config = mcp_agent.engine
                        if hasattr(vector_store_config, 'create_vectorstore'):
                            print("📊 Creating direct vector store...")
                            vectorstore = vector_store_config.create_vectorstore()
                            direct_results = vectorstore.similarity_search(request.query, k=5)
                            
                            if direct_results:
                                response_text = f"Found {len(direct_results)} MCP servers matching '{request.query}' (via direct search):\n\n"
                                for i, doc in enumerate(direct_results[:5], 1):
                                    server_name = doc.metadata.get('server_name', 'Unknown')
                                    category = doc.metadata.get('category', 'general')
                                    stars = doc.metadata.get('stars', 0)
                                    repo_url = doc.metadata.get('repository_url', '')
                                    
                                    response_text += f"{i}. **{server_name}** ({category})\n"
                                    response_text += f"   ⭐ {stars} stars\n"
                                    if repo_url:
                                        response_text += f"   🔗 {repo_url}\n"
                                    
                                    # Extract description from content
                                    content_lines = doc.page_content.split('\n')
                                    description = ""
                                    for line in content_lines:
                                        if line.startswith("Description:"):
                                            description = line.replace("Description:", "").strip()
                                            break
                                    
                                    if description and description != "No description available":
                                        response_text += f"   📝 {description}\n"
                                    
                                    response_text += "\n"
                            else:
                                response_text = f"No MCP servers found matching '{request.query}'."
                        else:
                            response_text = f"Could not access vector store for '{request.query}'."
                    else:
                        response_text = f"Agent structure not accessible for '{request.query}'."
                        
                except Exception as e:
                    print(f"❌ Direct search failed: {e}")
                    response_text = f"Search failed for '{request.query}'. Error: {str(e)}"
        
        elif hasattr(result, 'content'):
            # Handle string content
            response_text = str(result.content)
        else:
            # Fallback - convert to string
            response_text = str(result)
        
        # Ensure we have a string response
        if not isinstance(response_text, str):
            response_text = str(response_text)
        
        return QueryResponse(
            query=request.query,
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("🚀 Starting MCP Discovery Agent on port 6969")
    print("📍 Open http://localhost:6969 to chat with the agent")
    uvicorn.run(app, host="0.0.0.0", port=6969)