"""FastAPI web interface for MCP bulk management.

This module provides a complete REST API for managing MCP servers with bulk operations,
real-time progress tracking, and a clean web interface for browsing and managing
the 1900+ available MCP servers.

Features:
    - Bulk server installation and management
    - Real-time progress tracking via WebSockets
    - Category-based server organization
    - Health monitoring and status reporting
    - Server browser and search interface
    - Operation history and logging

Examples:
    Running the FastAPI server:
    
    .. code-block:: bash
    
        # Start the server
        poetry run python -m haive.mcp.api
        
        # Or with uvicorn directly
        poetry run uvicorn haive.mcp.api:app --reload --host 0.0.0.0 --port 8000

    Using the API programmatically:
    
    .. code-block:: python
    
        import httpx
        
        # Get available categories
        response = httpx.get("http://localhost:8000/api/mcp/categories")
        categories = response.json()
        
        # Install a category
        response = httpx.post("http://localhost:8000/api/mcp/categories/development/install")
        operation = response.json()
        
        # Track progress
        operation_id = operation["operation_id"]
        progress = httpx.get(f"http://localhost:8000/api/mcp/operations/{operation_id}")
"""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from haive.mcp.manager import MCPManager, MCPBulkOperation, MCPServerCategory, MCPRegistrationResult
from haive.mcp.config import MCPServerConfig, MCPTransport

logger = logging.getLogger(__name__)

# Global manager instance
global_manager: Optional[MCPManager] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.disconnect(connection)

connection_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the FastAPI app."""
    global global_manager
    
    # Startup
    logger.info("🚀 Starting MCP Bulk Management API")
    global_manager = MCPManager()
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down MCP Bulk Management API")
    if global_manager:
        await global_manager.shutdown()


# Create FastAPI app
app = FastAPI(
    title="MCP Bulk Management API",
    description="REST API for managing MCP servers with bulk operations and real-time tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== REQUEST/RESPONSE MODELS =====

class ServerInstallRequest(BaseModel):
    """Request to install MCP servers."""
    servers: List[str] = Field(description="List of server package names to install")
    add_to_manager: bool = Field(default=True, description="Add installed servers to manager")
    max_concurrent: int = Field(default=5, description="Maximum concurrent installations", ge=1, le=10)


class CategoryInstallRequest(BaseModel):
    """Request to install servers from a category."""
    category_name: str = Field(description="Name of the category to install")
    max_concurrent: int = Field(default=5, description="Maximum concurrent installations", ge=1, le=10)


class ServerRemoveRequest(BaseModel):
    """Request to remove servers."""
    server_names: List[str] = Field(description="List of server names to remove")


class BulkOperationResponse(BaseModel):
    """Response for bulk operations."""
    operation_id: str
    operation_type: str
    total_count: int
    status: str
    progress_percentage: float
    success_rate: float
    started_at: datetime
    is_complete: bool


class ServerStatusResponse(BaseModel):
    """Response for server status."""
    server_name: str
    status: str
    tools_count: int
    health: Optional[Dict[str, Any]] = None


# ===== API ENDPOINTS =====

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Bulk Management</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; margin-bottom: 30px; }
            .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .section h2 { color: #555; margin-top: 0; }
            .btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #0056b3; }
            .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .info { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
            pre { background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 MCP Bulk Management</h1>
            <p style="text-align: center; color: #666; margin-bottom: 40px;">
                Manage and install MCP servers with bulk operations, real-time tracking, and health monitoring.
            </p>
            
            <div class="grid">
                <div class="section">
                    <h2>📊 API Status</h2>
                    <div id="api-status" class="status info">Loading...</div>
                    <button class="btn" onclick="checkStatus()">Refresh Status</button>
                </div>
                
                <div class="section">
                    <h2>📁 Categories</h2>
                    <div id="categories">Loading...</div>
                    <button class="btn" onclick="loadCategories()">Refresh Categories</button>
                </div>
            </div>
            
            <div class="section">
                <h2>🛠️ Quick Actions</h2>
                <button class="btn" onclick="installCategory('development')">Install Development Tools</button>
                <button class="btn" onclick="installCategory('data')">Install Data Tools</button>
                <button class="btn" onclick="installCategory('productivity')">Install Productivity Tools</button>
                <button class="btn" onclick="healthCheck()">Health Check All</button>
            </div>
            
            <div class="section">
                <h2>📈 Operations</h2>
                <div id="operations">No active operations</div>
            </div>
            
            <div class="section">
                <h2>🔧 API Documentation</h2>
                <p>Interactive API documentation available at:</p>
                <ul>
                    <li><a href="/docs" target="_blank">Swagger UI</a></li>
                    <li><a href="/redoc" target="_blank">ReDoc</a></li>
                </ul>
            </div>
        </div>
        
        <script>
            const API_BASE = '';
            
            async function checkStatus() {
                try {
                    const response = await fetch(`${API_BASE}/api/mcp/status`);
                    const status = await response.json();
                    document.getElementById('api-status').innerHTML = `
                        <strong>Status:</strong> Running<br>
                        <strong>Connected Servers:</strong> ${status.summary.connected_servers}<br>
                        <strong>Total Tools:</strong> ${status.summary.total_tools}
                    `;
                    document.getElementById('api-status').className = 'status success';
                } catch (error) {
                    document.getElementById('api-status').innerHTML = `<strong>Error:</strong> ${error.message}`;
                    document.getElementById('api-status').className = 'status error';
                }
            }
            
            async function loadCategories() {
                try {
                    const response = await fetch(`${API_BASE}/api/mcp/categories`);
                    const categories = await response.json();
                    const html = Object.entries(categories).map(([name, cat]) => 
                        `<div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <strong>${name}</strong>: ${cat.description}<br>
                            <small>${cat.servers.length} servers</small>
                        </div>`
                    ).join('');
                    document.getElementById('categories').innerHTML = html;
                } catch (error) {
                    document.getElementById('categories').innerHTML = `Error: ${error.message}`;
                }
            }
            
            async function installCategory(category) {
                try {
                    const response = await fetch(`${API_BASE}/api/mcp/categories/${category}/install`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ max_concurrent: 3 })
                    });
                    const operation = await response.json();
                    updateOperations(`Started installing ${category} category (Operation: ${operation.operation_id})`);
                    trackOperation(operation.operation_id);
                } catch (error) {
                    updateOperations(`Error installing ${category}: ${error.message}`);
                }
            }
            
            async function healthCheck() {
                try {
                    const response = await fetch(`${API_BASE}/api/mcp/health/bulk`);
                    const health = await response.json();
                    updateOperations(`Health check complete: ${health.summary.healthy_servers}/${health.summary.total_servers} healthy`);
                } catch (error) {
                    updateOperations(`Health check error: ${error.message}`);
                }
            }
            
            async function trackOperation(operationId) {
                const checkProgress = async () => {
                    try {
                        const response = await fetch(`${API_BASE}/api/mcp/operations/${operationId}`);
                        const operation = await response.json();
                        updateOperations(`Operation ${operationId}: ${operation.progress_percentage.toFixed(1)}% complete (${operation.success_rate.toFixed(1)}% success rate)`);
                        
                        if (!operation.is_complete) {
                            setTimeout(checkProgress, 2000);
                        } else {
                            updateOperations(`Operation ${operationId} completed: ${operation.success_rate.toFixed(1)}% success rate`);
                        }
                    } catch (error) {
                        updateOperations(`Error tracking operation ${operationId}: ${error.message}`);
                    }
                };
                checkProgress();
            }
            
            function updateOperations(message) {
                const timestamp = new Date().toLocaleTimeString();
                const current = document.getElementById('operations').innerHTML;
                document.getElementById('operations').innerHTML = `[${timestamp}] ${message}<br>${current}`;
            }
            
            // Initialize page
            checkStatus();
            loadCategories();
        </script>
    </body>
    </html>
    """


@app.get("/api/mcp/status")
async def get_status():
    """Get overall MCP system status."""
    if not global_manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")
    
    return global_manager.get_all_server_status()


@app.get("/api/mcp/categories")
async def get_categories():
    """Get all available server categories."""
    if not global_manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")
    
    categories = global_manager.get_available_categories()
    return {name: {
        "name": cat.name,
        "description": cat.description,
        "servers": cat.servers,
        "tags": cat.tags,
        "server_count": len(cat.servers)
    } for name, cat in categories.items()}


@app.post("/api/mcp/categories/{category_name}/install")
async def install_category(
    category_name: str, 
    request: CategoryInstallRequest = CategoryInstallRequest(category_name="", max_concurrent=5),
    background_tasks: BackgroundTasks = None
):
    """Install all servers in a category."""
    if not global_manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")
    
    try:
        # Update request with path parameter
        request.category_name = category_name
        
        operation = await global_manager.bulk_install_category(
            category_name=request.category_name,
            max_concurrent=request.max_concurrent
        )
        
        # Broadcast progress via WebSocket
        await connection_manager.broadcast(f"Started category installation: {category_name}")
        
        return BulkOperationResponse(
            operation_id=operation.operation_id,
            operation_type=operation.operation_type,
            total_count=operation.total_count,
            status="running" if not operation.is_complete else "completed",
            progress_percentage=operation.progress_percentage,
            success_rate=operation.success_rate,
            started_at=operation.started_at,
            is_complete=operation.is_complete
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to install category {category_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Installation failed: {e}")


@app.post("/api/mcp/servers/install")
async def install_servers(request: ServerInstallRequest):
    """Install multiple MCP servers."""
    if not global_manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")
    
    try:
        operation = await global_manager.bulk_install_servers(
            server_packages=request.servers,
            add_to_manager=request.add_to_manager,
            max_concurrent=request.max_concurrent
        )
        
        await connection_manager.broadcast(f"Started bulk installation: {len(request.servers)} servers")
        
        return BulkOperationResponse(
            operation_id=operation.operation_id,
            operation_type=operation.operation_type,
            total_count=operation.total_count,
            status="running" if not operation.is_complete else "completed",
            progress_percentage=operation.progress_percentage,
            success_rate=operation.success_rate,
            started_at=operation.started_at,
            is_complete=operation.is_complete
        )
        
    except Exception as e:
        logger.exception(f"Failed to install servers: {e}")
        raise HTTPException(status_code=500, detail=f"Installation failed: {e}")


@app.delete("/api/mcp/servers/remove")
async def remove_servers(request: ServerRemoveRequest):
    """Remove multiple servers from the manager."""
    if not global_manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")
    
    try:
        operation = await global_manager.bulk_remove_servers(request.server_names)
        
        await connection_manager.broadcast(f"Started bulk removal: {len(request.server_names)} servers")
        
        return BulkOperationResponse(
            operation_id=operation.operation_id,
            operation_type=operation.operation_type,
            total_count=operation.total_count,
            status="completed",  # Removal is synchronous
            progress_percentage=operation.progress_percentage,
            success_rate=operation.success_rate,
            started_at=operation.started_at,
            is_complete=operation.is_complete
        )
        
    except Exception as e:
        logger.exception(f"Failed to remove servers: {e}")
        raise HTTPException(status_code=500, detail=f"Removal failed: {e}")


@app.get("/api/mcp/operations/{operation_id}")
async def get_operation_status(operation_id: str):
    """Get the status of a bulk operation."""
    if not global_manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")
    
    operation = global_manager.get_bulk_operation_status(operation_id)
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    return BulkOperationResponse(
        operation_id=operation.operation_id,
        operation_type=operation.operation_type,
        total_count=operation.total_count,
        status="running" if not operation.is_complete else "completed",
        progress_percentage=operation.progress_percentage,
        success_rate=operation.success_rate,
        started_at=operation.started_at,
        is_complete=operation.is_complete
    )


@app.get("/api/mcp/servers")
async def list_servers():
    """List all configured servers and their status."""
    if not global_manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")
    
    status = global_manager.get_all_server_status()
    servers = []
    
    for server_name, server_info in status["servers"].items():
        servers.append(ServerStatusResponse(
            server_name=server_name,
            status=server_info["status"],
            tools_count=len(server_info["tools"]),
            health=server_info["health"]
        ))
    
    return servers


@app.get("/api/mcp/health/bulk")
async def bulk_health_check():
    """Perform health check on all connected servers."""
    if not global_manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")
    
    try:
        health_results = await global_manager.bulk_health_check()
        await connection_manager.broadcast("Bulk health check completed")
        return health_results
    except Exception as e:
        logger.exception(f"Bulk health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


@app.put("/api/mcp/servers/update")
async def update_all_servers():
    """Update all installed MCP servers to latest versions."""
    if not global_manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")
    
    try:
        operation = await global_manager.bulk_update_servers()
        
        await connection_manager.broadcast("Started bulk server updates")
        
        return BulkOperationResponse(
            operation_id=operation.operation_id,
            operation_type=operation.operation_type,
            total_count=operation.total_count,
            status="running" if not operation.is_complete else "completed",
            progress_percentage=operation.progress_percentage,
            success_rate=operation.success_rate,
            started_at=operation.started_at,
            is_complete=operation.is_complete
        )
        
    except Exception as e:
        logger.exception(f"Failed to update servers: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {e}")


@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for messages
            message = await websocket.receive_text()
            await connection_manager.send_personal_message(f"Echo: {message}", websocket)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


# ===== CLI ENTRY POINT =====

def main():
    """Run the FastAPI server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Bulk Management API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    print(f"""
🚀 Starting MCP Bulk Management API
📡 Server: http://{args.host}:{args.port}
📖 Docs: http://{args.host}:{args.port}/docs
🔄 WebSocket: ws://{args.host}:{args.port}/ws/progress
""")
    
    uvicorn.run(
        "haive.mcp.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()