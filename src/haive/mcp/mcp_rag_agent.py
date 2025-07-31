"""MCP RAG Agent - Simplified version that works with our enhanced retriever

This agent helps users find and understand MCP servers using RAG.
"""

from datetime import datetime
from pathlib import Path
import sys


# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from langchain_openai import ChatOpenAI

from haive.agents.rag.base.agent import BaseRAGAgent
from haive.core.engine.aug_llm import AugLLMConfig
from haive.mcp.working_enhanced_retriever import WorkingEnhancedRetriever


async def create_mcp_rag_agent():
    """Create a RAG agent for MCP discovery."""
    # Initialize the enhanced retriever
    print("🔧 Setting up enhanced retriever...")
    retriever = WorkingEnhancedRetriever()
    retriever.setup()

    # Get all documents
    llm = ChatOpenAI(temperature=0)

    # Do a broad query to get documents
    print("📚 Loading MCP server documentation...")
    docs = await retriever.enhanced_query(llm, "MCP servers", k=50)

    print(f"✅ Loaded {len(docs)} documents")

    # Create RAG agent from documents
    agent = BaseRAGAgent.from_documents(
        documents=docs,
        name="mcp_rag_agent",
        llm_config=AugLLMConfig(
            name="mcp_rag_llm", model="gpt-3.5-turbo", temperature=0.3
        ),
        chunk_size=1000,
        chunk_overlap=200,
    )

    # Add custom system message
    agent.system_message = """You are an expert MCP (Model Context Protocol) server assistant.

Your role is to help users:
1. Find MCP servers that match their needs
2. Understand what each server can do (tools, resources, prompts)
3. Compare different servers for similar tasks
4. Explain how to use specific servers
5. Suggest the best servers based on requirements

When answering:
- Be specific about server capabilities
- Mention the programming language (Python/TypeScript/etc)
- Include star ratings when relevant
- Explain what tools/resources/prompts the server provides
- Suggest alternatives if multiple servers could work"""

    return agent


# FastAPI Integration
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
    title="MCP RAG Agent",
    description="Ask questions about MCP servers",
    version="1.0.0",
)

# Global agent instance
rag_agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize the RAG agent on startup."""
    global rag_agent
    print("🚀 Starting MCP RAG Agent...")
    rag_agent = await create_mcp_rag_agent()
    print("✅ Agent ready!")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Web UI for the agent."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>MCP RAG Agent</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .chat-container {
            margin-top: 20px;
        }
        .message {
            margin: 15px 0;
            padding: 15px;
            border-radius: 8px;
        }
        .user-message {
            background: #e3f2fd;
            text-align: right;
        }
        .agent-message {
            background: #f5f5f5;
            white-space: pre-wrap;
        }
        .input-container {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        input {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
        }
        input:focus {
            border-color: #2196F3;
        }
        button {
            padding: 12px 30px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #1976D2;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .examples {
            margin-top: 30px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
        }
        .examples h3 {
            margin-top: 0;
            color: #666;
        }
        .example {
            padding: 8px 12px;
            margin: 5px 0;
            background: white;
            border-radius: 20px;
            display: inline-block;
            cursor: pointer;
            transition: all 0.2s;
        }
        .example:hover {
            background: #e3f2fd;
            transform: translateY(-2px);
        }
        .loading {
            display: none;
            text-align: center;
            color: #666;
        }
        .loading.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 MCP RAG Agent</h1>
        <p style="text-align: center; color: #666;">Ask me anything about MCP servers!</p>
        
        <div class="chat-container" id="chat"></div>
        
        <div class="loading" id="loading">
            <p>🤔 Thinking...</p>
        </div>
        
        <div class="input-container">
            <input 
                type="text" 
                id="query" 
                placeholder="Ask about MCP servers..."
                onkeypress="handleKeyPress(event)"
            />
            <button onclick="askQuestion()" id="askBtn">Ask</button>
        </div>
        
        <div class="examples">
            <h3>Try these examples:</h3>
            <div class="example" onclick="setExample(this)">
                What Python MCP servers can help with databases?
            </div>
            <div class="example" onclick="setExample(this)">
                Find MCP servers for GitHub integration
            </div>
            <div class="example" onclick="setExample(this)">
                Which MCP server has the most stars?
            </div>
            <div class="example" onclick="setExample(this)">
                Compare Slack integration MCP servers
            </div>
            <div class="example" onclick="setExample(this)">
                What tools does the filesystem MCP server provide?
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
                    ${query}
                </div>
            `;
            
            // Clear input and disable
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
                        ${data.response}
                    </div>
                `;
                
                // Scroll to bottom
                chatDiv.scrollTop = chatDiv.scrollHeight;
                
            } catch (error) {
                chatDiv.innerHTML += `
                    <div class="message agent-message" style="color: red;">
                        Error: ${error.message}
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
    """Ask the RAG agent a question."""
    if not rag_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Run the query
        result = await rag_agent.arun(request.query)

        return QueryResponse(
            query=request.query, response=result, timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("🚀 Starting MCP RAG Agent on port 6969")
    print("📍 Open http://localhost:6969 to chat with the agent")
    uvicorn.run(app, host="0.0.0.0", port=6969)
