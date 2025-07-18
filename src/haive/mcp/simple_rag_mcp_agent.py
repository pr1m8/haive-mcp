"""SimpleRAG Agent for MCP Server Discovery

This agent uses the enhanced retriever to help users find and understand MCP servers.
It can answer questions about server capabilities, suggest servers based on needs,
and provide detailed information about specific servers.
"""

import asyncio
from datetime import datetime
from pathlib import Path
import sys
from typing import Any


# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_openai import ChatOpenAI

from haive.agents.rag.simple.agent import SimpleRAGAgent
from haive.core.engine.aug_llm import AugLLMConfig
from haive.mcp.working_enhanced_retriever import WorkingEnhancedRetriever


class MCPSimpleRAGAgent(SimpleRAGAgent):
    """SimpleRAG agent specialized for MCP server discovery."""

    def __init__(self, name: str = "mcp_rag_agent", **kwargs):
        # Initialize the enhanced retriever
        self.mcp_retriever = WorkingEnhancedRetriever()
        self.mcp_retriever.setup()

        # Create a wrapper that makes our retriever compatible with SimpleRAG
        retriever_config = {"retriever": MCPRetrieverWrapper(self.mcp_retriever)}

        # Initialize parent with our retriever
        super().__init__(name=name, retriever_config=retriever_config, **kwargs)

    def get_system_prompt(self) -> str:
        """Custom system prompt for MCP assistance."""
        return """You are an expert MCP (Model Context Protocol) server assistant.
        
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
- Suggest alternatives if multiple servers could work

Use the retrieved documents to provide accurate, helpful information about MCP servers."""


class MCPRetrieverWrapper(BaseRetriever):
    """Wrapper to make our enhanced retriever compatible with LangChain."""

    def __init__(self, enhanced_retriever: WorkingEnhancedRetriever):
        super().__init__()
        self.enhanced_retriever = enhanced_retriever
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOpenAI(temperature=0.3)
        return self._llm

    async def _aget_relevant_documents(
        self, query: str, *, run_manager=None
    ) -> list[Document]:
        """Async retrieval using our enhanced retriever."""
        docs = await self.enhanced_retriever.enhanced_query(self.llm, query, k=5)
        return docs

    def _get_relevant_documents(
        self, query: str, *, run_manager=None
    ) -> list[Document]:
        """Sync retrieval (runs async in event loop)."""
        return asyncio.run(self._aget_relevant_documents(query))


async def create_mcp_rag_agent(model: str = "gpt-3.5-turbo") -> MCPSimpleRAGAgent:
    """Factory function to create configured MCP RAG agent."""
    # Create engine config
    engine_config = AugLLMConfig(
        name="mcp_rag_engine", model=model, temperature=0.3, streaming=True
    )

    # Create agent
    agent = MCPSimpleRAGAgent(
        name="mcp_assistant", engine=engine_config, max_documents=5
    )

    return agent


async def demo_mcp_rag_agent():
    """Demonstrate the MCP RAG agent."""
    print("🚀 Starting MCP SimpleRAG Agent Demo\n")

    # Create agent
    agent = await create_mcp_rag_agent()

    # Example queries
    queries = [
        "What Python MCP servers are available for database operations?",
        "Find me MCP servers that can help with file system operations",
        "What's the most popular MCP server for GitHub integration?",
        "Compare MCP servers for weather data - which has the most features?",
        "I need an MCP server for Slack integration, what are my options?",
    ]

    for query in queries:
        print(f"\n{'=' * 60}")
        print(f"📝 Query: {query}")
        print(f"{'=' * 60}\n")

        # Get response
        response = await agent.arun(query)
        print(f"🤖 Response:\n{response}\n")

        # Small delay between queries
        await asyncio.sleep(1)


# FastAPI Integration
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    max_documents: int = 5


class QueryResponse(BaseModel):
    query: str
    response: str
    retrieved_servers: list[dict[str, Any]]
    timestamp: str


# Create FastAPI app for the RAG agent
app = FastAPI(
    title="MCP SimpleRAG Agent API",
    description="Ask questions about MCP servers and get intelligent responses",
    version="1.0.0",
)

# Global agent instance
rag_agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize the RAG agent on startup."""
    global rag_agent
    print("🔧 Initializing MCP SimpleRAG Agent...")
    rag_agent = await create_mcp_rag_agent()
    print("✅ Agent ready!")


@app.get("/")
async def root():
    """Simple web UI for testing the agent."""
    return HTMLResponse(
        """
<!DOCTYPE html>
<html>
<head>
    <title>MCP SimpleRAG Agent</title>
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
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        textarea {
            width: 100%;
            min-height: 100px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        button {
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover {
            background: #0056b3;
        }
        .response {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
            white-space: pre-wrap;
        }
        .example-queries {
            margin-top: 20px;
            padding: 15px;
            background: #e9ecef;
            border-radius: 4px;
        }
        .example-queries h3 {
            margin-top: 0;
        }
        .example-queries li {
            margin: 5px 0;
            cursor: pointer;
            color: #007bff;
        }
        .example-queries li:hover {
            text-decoration: underline;
        }
        .loading {
            display: none;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>🤖 MCP SimpleRAG Agent</h1>
    <div class="container">
        <h2>Ask about MCP Servers</h2>
        <textarea id="query" placeholder="e.g., What Python MCP servers are available for database operations?"></textarea>
        <br>
        <button onclick="askAgent()">Ask Agent</button>
        <span class="loading" id="loading">Thinking...</span>
        
        <div id="response" class="response" style="display: none;"></div>
        
        <div class="example-queries">
            <h3>Example Queries:</h3>
            <ul>
                <li onclick="setQuery(this.textContent)">What Python MCP servers are available for database operations?</li>
                <li onclick="setQuery(this.textContent)">Find MCP servers for file system operations with high star ratings</li>
                <li onclick="setQuery(this.textContent)">Compare GitHub integration MCP servers - which is best?</li>
                <li onclick="setQuery(this.textContent)">I need an MCP server for Slack, what are my options?</li>
                <li onclick="setQuery(this.textContent)">What MCP servers can help with AI/LLM tasks?</li>
                <li onclick="setQuery(this.textContent)">Show me the most popular TypeScript MCP servers</li>
            </ul>
        </div>
    </div>
    
    <script>
        function setQuery(text) {
            document.getElementById('query').value = text;
        }
        
        async function askAgent() {
            const query = document.getElementById('query').value;
            if (!query) return;
            
            const loading = document.getElementById('loading');
            const responseDiv = document.getElementById('response');
            
            loading.style.display = 'inline';
            responseDiv.style.display = 'none';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query})
                });
                
                const data = await response.json();
                
                responseDiv.textContent = data.response;
                responseDiv.style.display = 'block';
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
                responseDiv.style.display = 'block';
            } finally {
                loading.style.display = 'none';
            }
        }
        
        // Allow Enter key to submit
        document.getElementById('query').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askAgent();
            }
        });
    </script>
</body>
</html>
"""
    )


@app.post("/ask", response_model=QueryResponse)
async def ask_agent(request: QueryRequest):
    """Ask the RAG agent a question about MCP servers."""
    if not rag_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Get response from agent
        response = await rag_agent.arun(request.query)

        # Get the retrieved documents (for transparency)
        retriever_wrapper = rag_agent.retriever_config["retriever"]
        docs = await retriever_wrapper._aget_relevant_documents(request.query)

        retrieved_servers = [
            {
                "name": doc.metadata.get("server_name", "Unknown"),
                "category": doc.metadata.get("category", "general"),
                "stars": doc.metadata.get("stars", 0),
                "language": doc.metadata.get("language", "unknown"),
            }
            for doc in docs
        ]

        return QueryResponse(
            query=request.query,
            response=response,
            retrieved_servers=retrieved_servers,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Check if running as script
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Run demo
        asyncio.run(demo_mcp_rag_agent())
    else:
        # Run FastAPI server
        import uvicorn

        print("🚀 Starting MCP SimpleRAG Agent API on port 6969")
        print("📍 Open http://localhost:6969 to use the agent")
        uvicorn.run(app, host="0.0.0.0", port=6969)
