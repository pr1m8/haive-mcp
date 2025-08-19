# MCP FastAPI Interface

## Overview

Complete REST API and web interface for managing MCP servers with bulk operations, real-time progress tracking, and category-based organization.

## Features

- **REST API**: 10+ endpoints for complete MCP management
- **WebSocket Support**: Real-time progress updates
- **Web Interface**: Built-in HTML interface with interactive controls
- **Bulk Operations**: Category installation, health monitoring, server management
- **Auto-Documentation**: Swagger UI and ReDoc integration
- **CORS Support**: Cross-origin requests enabled
- **Error Handling**: Comprehensive error responses and logging

## Quick Start

### Start the Server

```bash
# Using the module directly
poetry run python -m haive.mcp.api --port 8001

# Using uvicorn directly
poetry run uvicorn haive.mcp.api:app --reload --port 8001 --host 0.0.0.0

# With custom options
poetry run python -m haive.mcp.api --host 127.0.0.1 --port 8000 --reload --log-level debug
```

### Access the Interface

- **Web Interface**: http://localhost:8001/
- **API Documentation**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **WebSocket**: ws://localhost:8001/ws/progress

## API Endpoints

### System Status
```http
GET /api/mcp/status
```
Returns overall system status including connected servers and tool counts.

### Categories
```http
GET /api/mcp/categories
```
Get all available server categories with descriptions and server lists.

```http
POST /api/mcp/categories/{category_name}/install
Content-Type: application/json

{
    "max_concurrent": 5
}
```
Install all servers in a specific category.

### Server Management
```http
POST /api/mcp/servers/install
Content-Type: application/json

{
    "servers": ["@modelcontextprotocol/server-time", "@modelcontextprotocol/server-memory"],
    "add_to_manager": true,
    "max_concurrent": 3
}
```
Install multiple servers in parallel.

```http
DELETE /api/mcp/servers/remove
Content-Type: application/json

{
    "server_names": ["time", "memory"]
}
```
Remove servers from the manager.

```http
GET /api/mcp/servers
```
List all configured servers and their status.

### Health Monitoring
```http
GET /api/mcp/health/bulk
```
Perform health check on all connected servers.

### Operations Tracking
```http
GET /api/mcp/operations/{operation_id}
```
Get the status of a specific bulk operation.

### Server Updates
```http
PUT /api/mcp/servers/update
```
Update all installed MCP servers to latest versions.

## WebSocket Interface

Connect to `/ws/progress` for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/progress');
ws.onmessage = function(event) {
    console.log('Progress update:', event.data);
};
```

## Usage Examples

### Python Client
```python
import httpx
import asyncio

async def example_usage():
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        # Get system status
        response = await client.get(f"{base_url}/api/mcp/status")
        status = response.json()
        print(f"Connected servers: {status['summary']['connected_servers']}")
        
        # Get categories
        response = await client.get(f"{base_url}/api/mcp/categories")
        categories = response.json()
        print(f"Available categories: {list(categories.keys())}")
        
        # Install development category
        response = await client.post(
            f"{base_url}/api/mcp/categories/development/install",
            json={"max_concurrent": 3}
        )
        operation = response.json()
        operation_id = operation["operation_id"]
        
        # Track progress
        while True:
            response = await client.get(f"{base_url}/api/mcp/operations/{operation_id}")
            op_status = response.json()
            print(f"Progress: {op_status['progress_percentage']:.1f}%")
            
            if op_status["is_complete"]:
                print(f"Completed with {op_status['success_rate']:.1f}% success rate")
                break
            
            await asyncio.sleep(2)

# Run the example
asyncio.run(example_usage())
```

### JavaScript/Browser
```javascript
// Get system status
fetch('/api/mcp/status')
    .then(response => response.json())
    .then(status => {
        console.log('System status:', status);
    });

// Install category with progress tracking
async function installCategory(category) {
    const response = await fetch(`/api/mcp/categories/${category}/install`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_concurrent: 3 })
    });
    
    const operation = await response.json();
    trackOperation(operation.operation_id);
}

async function trackOperation(operationId) {
    const checkProgress = async () => {
        const response = await fetch(`/api/mcp/operations/${operationId}`);
        const operation = await response.json();
        
        console.log(`Progress: ${operation.progress_percentage.toFixed(1)}%`);
        
        if (!operation.is_complete) {
            setTimeout(checkProgress, 2000);
        } else {
            console.log(`Completed: ${operation.success_rate.toFixed(1)}% success`);
        }
    };
    checkProgress();
}
```

### cURL Examples
```bash
# Get system status
curl http://localhost:8001/api/mcp/status

# List categories
curl http://localhost:8001/api/mcp/categories

# Install development category
curl -X POST http://localhost:8001/api/mcp/categories/development/install \
     -H "Content-Type: application/json" \
     -d '{"max_concurrent": 3}'

# Health check
curl http://localhost:8001/api/mcp/health/bulk

# Install specific servers
curl -X POST http://localhost:8001/api/mcp/servers/install \
     -H "Content-Type: application/json" \
     -d '{
       "servers": ["@modelcontextprotocol/server-time"],
       "add_to_manager": true,
       "max_concurrent": 1
     }'
```

## Configuration

### Environment Variables
```bash
# API server configuration
export MCP_API_HOST="0.0.0.0"
export MCP_API_PORT="8001"
export MCP_API_LOG_LEVEL="info"

# CORS configuration
export MCP_API_CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
```

### CLI Arguments
```bash
python -m haive.mcp.api --help

# Available options:
# --host: Host to bind to (default: 0.0.0.0)
# --port: Port to bind to (default: 8000)
# --reload: Enable auto-reload for development
# --log-level: Set logging level (info, debug, warning, error)
```

## Web Interface Features

The built-in web interface provides:

### Dashboard
- System status display
- Connected servers count
- Total tools available
- Health summary

### Categories Browser
- View all available categories
- See server count per category
- One-click category installation
- Progress tracking

### Quick Actions
- Install common categories (development, data, productivity)
- Bulk health check
- System status refresh

### Operations Monitor
- Real-time operation progress
- Success/failure rates
- Operation history
- Error details

## Architecture

### Application Structure
```python
# FastAPI app with lifespan management
app = FastAPI(
    title="MCP Bulk Management API",
    description="REST API for managing MCP servers",
    version="1.0.0",
    lifespan=lifespan
)

# Global manager instance
global_manager: MCPManager = None

# WebSocket connection manager
connection_manager = ConnectionManager()
```

### Lifecycle Management
- **Startup**: Initialize MCPManager
- **Runtime**: Handle requests and WebSocket connections
- **Shutdown**: Gracefully close all MCP connections

### Error Handling
- **HTTP Exceptions**: Proper status codes and error messages
- **Logging**: Comprehensive operation logging
- **Graceful Failures**: Individual server failures don't break operations

## Testing

### Unit Tests
```bash
# Test API endpoints
poetry run pytest tests/test_api.py -v

# Test with running server
poetry run uvicorn haive.mcp.api:app --port 8001 &
poetry run pytest tests/test_api_integration.py -v
```

### Manual Testing
```bash
# Start server
poetry run python -m haive.mcp.api --port 8001 --reload

# Test endpoints
curl http://localhost:8001/api/mcp/status
curl http://localhost:8001/api/mcp/categories

# Test web interface
open http://localhost:8001/
```

## Development

### Adding New Endpoints
```python
@app.get("/api/mcp/custom-endpoint")
async def custom_endpoint():
    """Add your custom endpoint here."""
    if not global_manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")
    
    # Your logic here
    return {"message": "Custom endpoint response"}
```

### WebSocket Updates
```python
# Broadcast progress updates
await connection_manager.broadcast(f"Operation started: {operation_id}")
```

### Request/Response Models
```python
class CustomRequest(BaseModel):
    """Define request models for type safety."""
    parameter: str = Field(description="Parameter description")

class CustomResponse(BaseModel):
    """Define response models for documentation."""
    result: str
    success: bool
```

## Production Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["python", "-m", "haive.mcp.api", "--host", "0.0.0.0", "--port", "8001"]
```

### Nginx Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Known Issues & Future Plans

### Current Status
- ✅ **API fully functional** - All endpoints working
- ✅ **WebSocket support** - Real-time updates working
- ✅ **Web interface** - Interactive controls functional
- 🔄 **Installation method** - Still using git clone (needs Phase 1 fix)

### Next Steps (Per PROJECT_NOTES.md)
1. **Fix installation method**: Replace git clone with package managers
2. **Add authentication**: JWT tokens for production use
3. **Rate limiting**: Prevent API abuse
4. **Metrics**: Prometheus/monitoring integration
5. **Caching**: Redis for operation status caching

## Dependencies

```toml
fastapi = "^0.104"
uvicorn = "^0.24"
websockets = "^12.0"
aiohttp = "^3.9"
pydantic = "^2.0"
```

## Contributing

1. Follow the Master Fix Plan in PROJECT_NOTES.md
2. Test with real MCP servers (no mocks)
3. Update API documentation for any changes
4. Test WebSocket functionality
5. Ensure proper error handling and logging