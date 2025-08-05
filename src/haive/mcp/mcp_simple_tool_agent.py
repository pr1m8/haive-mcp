"""MCP Simple Tool Agent - Using SimpleAgent with retrieval tool."""

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from haive.agents.simple.agent import SimpleAgent
from haive.core.models.llm.base import AzureLLMConfig, LLMConfig
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel

from haive.mcp.documentation import MCPDocumentationLoader

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))


# Global vector store
VECTOR_STORE = None


def create_mcp_documents() -> list[Document]:
    """Create documents from MCP server data."""
    doc_loader = MCPDocumentationLoader()
    all_servers_path = doc_loader.mcp_servers_path / "ALL_MCP_SERVERS_COMPLETE.json"

    with open(all_servers_path) as f:
        data = json.load(f)
        servers = data.get("all_servers", [])

    documents = []
    for server in servers:
        # Get server details
        name = server.get("name", "Unknown")
        description = server.get("description", "No description available")
        category = server.get("category", "general")
        language = server.get("language", "unknown")
        stars = server.get("stars", 0)
        install_command = server.get("install_command", "npm install")
        repository_url = server.get("repository_url", "")
        tools = server.get("tools", [])
        resources = server.get("resources", [])
        prompts = server.get("prompts", [])
        use_cases = server.get("use_cases", "General purpose MCP server")
        installation_notes = server.get(
            "installation_notes", "Standard MCP installation"
        )

        # Create rich document content with searchable keywords
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

Keywords: {category} {language} MCP server {name.lower().replace("-", " ")}
Tool Count: {len(tools)}
Resource Count: {len(resources)}
Prompt Count: {len(prompts)}
"""

        doc = Document(
            page_content=content,
            metadata={
                "server_name": server.get("name", "Unknown"),
                "category": server.get("category", "general"),
                "language": server.get("language", "unknown"),
                "stars": server.get("stars", 0),
                "has_install": bool(server.get("install_command")),
                "repository_url": server.get("repository_url", ""),
                "tools_count": len(server.get("tools", [])),
                "resources_count": len(server.get("resources", [])),
                "prompts_count": len(server.get("prompts", [])),
                "type": "mcp_server",
                "document_id": f"mcp_server_{len(documents)}",
                "source": str(all_servers_path),
            },
        )
        documents.append(doc)

    return documents


def initialize_vector_store():
    """Initialize the vector store with MCP documents."""
    global VECTOR_STORE

    # Load documents
    documents = create_mcp_documents()

    # Create embeddings

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Create FAISS vector store
    VECTOR_STORE = FAISS.from_documents(documents, embeddings)


@tool
def search_mcp_servers(query: str, k: int = 5) -> str:
    """Search for MCP servers based on query.

    Args:
        query: Search query (e.g., "python database", "github integration")
        k: Number of results to return (default: 5)

    Returns:
        Formatted string with search results
    """
    if VECTOR_STORE is None:
        return "Vector store not initialized. Please wait for initialization."

    # Perform search
    results = VECTOR_STORE.similarity_search(query, k=k)

    if not results:
        return f"No MCP servers found matching '{query}'"

    # Format results
    output = f"Found {len(results)} MCP servers matching '{query}':\n\n"

    for i, doc in enumerate(results, 1):
        server_name = doc.metadata.get("server_name", "Unknown")
        category = doc.metadata.get("category", "general")
        stars = doc.metadata.get("stars", 0)
        repo_url = doc.metadata.get("repository_url", "")

        # Extract description from content
        content_lines = doc.page_content.split("\n")
        description = ""
        for line in content_lines:
            if line.startswith("Description:"):
                description = line.replace("Description:", "").strip()
                break

        output += f"{i}. **{server_name}** ({category})\n"
        output += f"   ⭐ {stars} stars\n"
        if repo_url:
            output += f"   🔗 {repo_url}\n"
        if description and description != "No description available":
            output += f"   📝 {description}\n"
        output += "\n"

    return output


def create_mcp_tool_agent(llm_config: LLMConfig | None = None) -> SimpleAgent:
    """Create a SimpleAgent with MCP search tool."""
    # Initialize vector store if not already done
    if VECTOR_STORE is None:
        initialize_vector_store()

    # Use defaults if no config provided
    if not llm_config:
        llm_config = AzureLLMConfig()

    # Create SimpleAgent with search tool
    agent = SimpleAgent(
        name="MCP_Tool_Agent",
        engine=llm_config,  # Use engine instead of llm_config
    )

    return agent


# FastAPI Integration


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    response: str
    timestamp: str


# Create FastAPI app
app = FastAPI(
    title="MCP Tool Discovery Agent",
    description="Ask questions about MCP servers using tool-based search",
    version="1.0.0",
)

# Global agent instance
mcp_agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize the MCP tool agent."""
    global mcp_agent
    mcp_agent = create_mcp_tool_agent()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Web interface for the MCP agent."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>MCP Tool Discovery Agent</title>
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
        .loading {
            text-align: center;
            color: #666;
            padding: 20px;
            display: none;
        }
        .loading.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 MCP Tool Discovery Agent</h1>
        <p class="subtitle">Search through 1,960 MCP servers with tool-based intelligence</p>

        <div class="chat-container" id="chat"></div>

        <div class="loading" id="loading">
            <p>🔍 Agent is thinking and searching...</p>
        </div>

        <div class="input-container">
            <input
                type="text"
                id="query"
                placeholder="Ask about MCP servers... e.g., 'Find Python servers for databases'"
                onkeypress="handleKeyPress(event)"
            />
            <button onclick="askQuestion()" id="askBtn">Ask</button>
        </div>
    </div>

    <script>
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

        # Run the query through the agent
        result = await mcp_agent.arun(request.query)

        return QueryResponse(
            query=request.query, response=result, timestamp=datetime.now().isoformat()
        )

    except Exception as e:

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6970)
