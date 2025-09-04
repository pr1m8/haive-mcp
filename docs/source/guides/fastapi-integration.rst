FastAPI Integration Guide
========================

Complete guide to integrating Haive MCP with FastAPI for web APIs and microservices.

Overview
--------

The Haive MCP platform provides built-in FastAPI integration through:

* **Auto-generated routers** - Platforms automatically create FastAPI routers
* **Pydantic serialization** - Seamless JSON API responses
* **Async support** - Full async/await patterns
* **Type safety** - Complete type hints and validation
* **OpenAPI docs** - Automatic API documentation

Basic Integration
-----------------

Simple FastAPI App
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import FastAPI
   from pathlib import Path
   from haive.mcp.plugins import MCPBrowserPlugin

   # Create FastAPI app
   app = FastAPI(
       title="MCP Server Manager",
       description="Manage and browse MCP servers",
       version="1.0.0"
   )

   # Create MCP plugin
   mcp_plugin = MCPBrowserPlugin(
       server_directory=Path("/home/will/Downloads/mcp_servers"),
       cache_ttl=3600
   )

   # Mount plugin router
   app.include_router(
       mcp_plugin.get_router(),
       prefix="/mcp",
       tags=["MCP Servers"]
   )

   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=8000)

Multiple Plugin Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import FastAPI
   from pathlib import Path
   from haive.mcp.plugins import MCPBrowserPlugin

   app = FastAPI(title="Multi-Plugin MCP Manager")

   # Development servers
   dev_plugin = MCPBrowserPlugin(
       server_directory=Path("/dev/mcp_servers"),
       name="dev-browser"
   )
   app.include_router(
       dev_plugin.get_router(),
       prefix="/dev/mcp",
       tags=["Development MCP"]
   )

   # Production servers  
   prod_plugin = MCPBrowserPlugin(
       server_directory=Path("/prod/mcp_servers"),
       name="prod-browser"
   )
   app.include_router(
       prod_plugin.get_router(),
       prefix="/prod/mcp",
       tags=["Production MCP"]
   )

   # Health check
   @app.get("/health")
   async def health():
       return {
           "status": "healthy",
           "plugins": {
               "dev": dev_plugin.enabled,
               "prod": prod_plugin.enabled
           }
       }

Available Endpoints
-------------------

Default Plugin Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~

Each MCPBrowserPlugin provides these endpoints:

.. code-block:: text

   GET    /servers                    # List all servers
   GET    /servers/{server_name}      # Get specific server
   GET    /categories                 # List unique capabilities
   GET    /search                     # Search servers (query param: q)
   GET    /stats                      # Server statistics
   POST   /cache/refresh              # Refresh server cache
   DELETE /cache                      # Clear cache

Endpoint Details
~~~~~~~~~~~~~~~~

**List Servers** - ``GET /servers``

.. code-block:: python

   # Example response
   [
       {
           "name": "postgresql-server",
           "description": "PostgreSQL MCP server",
           "version": "1.2.0",
           "capabilities": ["database", "sql"],
           "mcp_version": "0.1.0",
           "transport_types": ["stdio"],
           "local_path": "/servers/postgresql-server",
           "file_size": 1024000,
           "installed_date": "2025-01-15T10:30:00",
           "download_source": "npm",
           "is_verified": true
       }
   ]

**Get Server** - ``GET /servers/{server_name}``

.. code-block:: python

   # Example: GET /servers/postgresql-server
   {
       "name": "postgresql-server",
       "description": "PostgreSQL MCP server",
       "version": "1.2.0",
       "capabilities": ["database", "sql"],
       "mcp_version": "0.1.0",
       "transport_types": ["stdio"],
       "command_template": "npx -y @modelcontextprotocol/server-postgres {connection_string}",
       "local_path": "/servers/postgresql-server",
       "file_size": 1024000,
       "installed_date": "2025-01-15T10:30:00",
       "download_source": "npm",
       "is_verified": true
   }

**Search Servers** - ``GET /search?q={query}``

.. code-block:: python

   # Example: GET /search?q=database
   [
       {
           "name": "postgresql-server",
           "description": "PostgreSQL MCP server",
           "version": "1.2.0",
           "capabilities": ["database", "sql"]
       },
       {
           "name": "mysql-server", 
           "description": "MySQL MCP server",
           "version": "1.0.0",
           "capabilities": ["database", "sql"]
       }
   ]

Custom Router Extensions
------------------------

Extending Plugin Routers
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import APIRouter, HTTPException, Query
   from typing import Optional, List
   from haive.mcp.plugins import MCPBrowserPlugin
   from haive.mcp.models import DownloadedServerInfo

   class ExtendedMCPPlugin(MCPBrowserPlugin):
       """Plugin with custom endpoints"""
       
       def get_router(self) -> APIRouter:
           # Start with base router
           router = super().get_router()
           
           @router.get("/servers/by-capability/{capability}")
           async def get_servers_by_capability(capability: str):
               """Get all servers with specific capability"""
               servers = await self.filter_by_category(capability)
               return [s.model_dump() for s in servers]
           
           @router.get("/servers/large")
           async def get_large_servers(
               min_size: int = Query(default=1000000, description="Minimum size in bytes")
           ):
               """Get servers larger than specified size"""
               servers = await self.load_servers()
               large_servers = [s for s in servers if s.file_size >= min_size]
               return [
                   {
                       "name": s.name,
                       "size": s.file_size,
                       "size_mb": round(s.file_size / (1024*1024), 2)
                   }
                   for s in large_servers
               ]
           
           @router.post("/servers/{server_name}/verify")
           async def verify_server(server_name: str):
               """Verify server installation"""
               servers = await self.load_servers()
               server = next((s for s in servers if s.name == server_name), None)
               
               if not server:
                   raise HTTPException(404, f"Server not found: {server_name}")
               
               # Verification logic
               exists = server.local_path.exists()
               correct_size = False
               if exists:
                   actual_size = server.local_path.stat().st_size
                   correct_size = actual_size == server.file_size
               
               return {
                   "server": server_name,
                   "exists": exists,
                   "correct_size": correct_size,
                   "verified": exists and correct_size
               }
           
           @router.get("/analytics/capabilities")
           async def get_capability_analytics():
               """Get capability distribution analytics"""
               servers = await self.load_servers()
               
               capability_counts = {}
               for server in servers:
                   for cap in server.capabilities:
                       capability_counts[cap] = capability_counts.get(cap, 0) + 1
               
               total_servers = len(servers)
               return {
                   "total_servers": total_servers,
                   "capability_distribution": [
                       {
                           "capability": cap,
                           "count": count,
                           "percentage": round(count / total_servers * 100, 1)
                       }
                       for cap, count in sorted(
                           capability_counts.items(),
                           key=lambda x: x[1],
                           reverse=True
                       )
                   ]
               }
           
           return router

Request/Response Models
-----------------------

Custom Pydantic Models
~~~~~~~~~~~~~~~~~~~~~~

Create custom request/response models:

.. code-block:: python

   from pydantic import BaseModel, Field
   from typing import List, Optional
   from datetime import datetime

   class ServerFilter(BaseModel):
       """Request model for server filtering"""
       capabilities: Optional[List[str]] = Field(default=None)
       min_version: Optional[str] = Field(default=None)
       max_size: Optional[int] = Field(default=None)
       verified_only: bool = Field(default=False)

   class ServerSummary(BaseModel):
       """Response model for server summary"""
       name: str
       version: str
       capabilities: List[str]
       size_mb: float
       last_updated: datetime

   class AnalyticsResponse(BaseModel):
       """Response model for analytics"""
       total_servers: int
       total_size_mb: float
       verified_count: int
       capability_distribution: List[dict]

   # Usage in endpoints
   @router.post("/servers/filter", response_model=List[ServerSummary])
   async def filter_servers(filter_params: ServerFilter):
       """Filter servers with custom criteria"""
       servers = await plugin.load_servers()
       
       # Apply filters
       filtered = servers
       if filter_params.capabilities:
           filtered = [
               s for s in filtered
               if any(cap in s.capabilities for cap in filter_params.capabilities)
           ]
       
       if filter_params.verified_only:
           filtered = [s for s in filtered if s.is_verified]
       
       # Convert to response model
       return [
           ServerSummary(
               name=s.name,
               version=s.version,
               capabilities=s.capabilities,
               size_mb=round(s.file_size / (1024*1024), 2),
               last_updated=s.installed_date
           )
           for s in filtered
       ]

Authentication & Authorization
------------------------------

API Key Authentication
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import FastAPI, Depends, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   import os

   security = HTTPBearer()

   def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
       """Verify API key from environment"""
       expected_key = os.getenv("MCP_API_KEY")
       if not expected_key or credentials.credentials != expected_key:
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Invalid API key"
           )
       return credentials

   # Protect specific endpoints
   @router.get("/servers/admin", dependencies=[Depends(verify_api_key)])
   async def admin_servers():
       """Admin-only server listing"""
       servers = await plugin.load_servers()
       return {
           "servers": len(servers),
           "total_size": sum(s.file_size for s in servers),
           "unverified": sum(1 for s in servers if not s.is_verified)
       }

Role-Based Access
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from enum import Enum
   from typing import List

   class UserRole(str, Enum):
       ADMIN = "admin"
       USER = "user"
       READONLY = "readonly"

   class User(BaseModel):
       username: str
       roles: List[UserRole]

   def require_roles(allowed_roles: List[UserRole]):
       """Decorator for role-based access"""
       def decorator(func):
           async def wrapper(*args, **kwargs):
               # In real app, get user from token/session
               current_user = get_current_user()  # Implement this
               
               if not any(role in current_user.roles for role in allowed_roles):
                   raise HTTPException(403, "Insufficient permissions")
               
               return await func(*args, **kwargs)
           return wrapper
       return decorator

   # Usage
   @router.delete("/servers/{server_name}")
   @require_roles([UserRole.ADMIN])
   async def delete_server(server_name: str):
       """Admin-only server deletion"""
       # Implementation here

Error Handling
--------------

Custom Exception Handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import HTTPException, Request
   from fastapi.responses import JSONResponse
   from pydantic import ValidationError
   import logging

   logger = logging.getLogger(__name__)

   @app.exception_handler(ValidationError)
   async def validation_exception_handler(request: Request, exc: ValidationError):
       """Handle Pydantic validation errors"""
       logger.error(f"Validation error: {exc}")
       return JSONResponse(
           status_code=422,
           content={
               "error": "Validation Error",
               "details": exc.errors(),
               "message": "Invalid input data"
           }
       )

   @app.exception_handler(FileNotFoundError)
   async def file_not_found_handler(request: Request, exc: FileNotFoundError):
       """Handle file not found errors"""
       logger.error(f"File not found: {exc}")
       return JSONResponse(
           status_code=404,
           content={
               "error": "File Not Found",
               "message": str(exc)
           }
       )

   class MCPException(Exception):
       """Custom MCP exception"""
       def __init__(self, message: str, status_code: int = 500):
           self.message = message
           self.status_code = status_code
           super().__init__(message)

   @app.exception_handler(MCPException)
   async def mcp_exception_handler(request: Request, exc: MCPException):
       """Handle custom MCP exceptions"""
       logger.error(f"MCP error: {exc.message}")
       return JSONResponse(
           status_code=exc.status_code,
           content={
               "error": "MCP Error",
               "message": exc.message
           }
       )

Graceful Error Responses
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import HTTPException

   class ExtendedMCPPlugin(MCPBrowserPlugin):
       def get_router(self) -> APIRouter:
           router = super().get_router()
           
           @router.get("/servers/{server_name}")
           async def get_server_safe(server_name: str):
               """Get server with proper error handling"""
               try:
                   servers = await self.load_servers()
                   server = next((s for s in servers if s.name == server_name), None)
                   
                   if not server:
                       raise HTTPException(
                           status_code=404,
                           detail={
                               "error": "Server not found",
                               "server_name": server_name,
                               "available_servers": [s.name for s in servers[:5]]
                           }
                       )
                   
                   return server.model_dump()
                   
               except Exception as e:
                   logger.error(f"Error loading server {server_name}: {e}")
                   raise HTTPException(
                       status_code=500,
                       detail={
                           "error": "Internal server error",
                           "message": "Failed to load server information"
                       }
                   )

Middleware & CORS
-----------------

CORS Configuration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000", "https://myapp.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

Custom Middleware
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import Request
   from starlette.middleware.base import BaseHTTPMiddleware
   import time
   import logging

   class LoggingMiddleware(BaseHTTPMiddleware):
       """Log all API requests"""
       
       async def dispatch(self, request: Request, call_next):
           start_time = time.time()
           
           # Log request
           logger.info(f"Request: {request.method} {request.url}")
           
           response = await call_next(request)
           
           # Log response
           process_time = time.time() - start_time
           logger.info(
               f"Response: {response.status_code} "
               f"({process_time:.3f}s)"
           )
           
           return response

   app.add_middleware(LoggingMiddleware)

   class CacheMiddleware(BaseHTTPMiddleware):
       """Add cache headers to responses"""
       
       async def dispatch(self, request: Request, call_next):
           response = await call_next(request)
           
           # Add cache headers for GET requests
           if request.method == "GET":
               response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
           
           return response

   app.add_middleware(CacheMiddleware)

Testing
-------

FastAPI Test Client
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi.testclient import TestClient
   import pytest
   from pathlib import Path
   import tempfile
   import json

   @pytest.fixture
   def test_app():
       """Create test FastAPI app"""
       app = FastAPI()
       
       # Create temporary server directory
       with tempfile.TemporaryDirectory() as temp_dir:
           temp_path = Path(temp_dir)
           
           # Create mock server files
           mock_server_dir = temp_path / "postgresql-server"
           mock_server_dir.mkdir()
           (mock_server_dir / "package.json").write_text(
               json.dumps({
                   "name": "@modelcontextprotocol/server-postgres",
                   "version": "1.2.0",
                   "description": "PostgreSQL MCP server"
               })
           )
           
           plugin = MCPBrowserPlugin(server_directory=temp_path)
           app.include_router(plugin.get_router(), prefix="/mcp")
           
           yield app

   def test_list_servers(test_app):
       """Test server listing endpoint"""
       client = TestClient(test_app)
       response = client.get("/mcp/servers")
       
       assert response.status_code == 200
       servers = response.json()
       assert isinstance(servers, list)
       assert len(servers) >= 1
       
       server = servers[0]
       assert "name" in server
       assert "version" in server
       assert "capabilities" in server

   def test_get_specific_server(test_app):
       """Test getting specific server"""
       client = TestClient(test_app)
       
       # First get list to find a server name
       servers_response = client.get("/mcp/servers")
       servers = servers_response.json()
       
       if servers:
           server_name = servers[0]["name"]
           response = client.get(f"/mcp/servers/{server_name}")
           
           assert response.status_code == 200
           server = response.json()
           assert server["name"] == server_name

   def test_server_not_found(test_app):
       """Test 404 for non-existent server"""
       client = TestClient(test_app)
       response = client.get("/mcp/servers/nonexistent")
       
       assert response.status_code == 404

Async Testing
~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   import asyncio
   from httpx import AsyncClient

   @pytest.mark.asyncio
   async def test_async_endpoints():
       """Test async endpoints"""
       app = create_test_app()  # Your app factory
       
       async with AsyncClient(app=app, base_url="http://test") as client:
           # Test server loading
           response = await client.get("/mcp/servers")
           assert response.status_code == 200
           
           # Test search
           response = await client.get("/mcp/search?q=database")
           assert response.status_code == 200
           results = response.json()
           
           # Verify search results
           for server in results:
               assert "database" in server["name"].lower() or \
                      "database" in server["description"].lower() or \
                      "database" in server["capabilities"]

Production Deployment
---------------------

Docker Deployment
~~~~~~~~~~~~~~~~~

.. code-block:: dockerfile

   FROM python:3.11-slim

   WORKDIR /app

   # Install dependencies
   COPY pyproject.toml poetry.lock ./
   RUN pip install poetry && \
       poetry config virtualenvs.create false && \
       poetry install --only=main

   # Copy application
   COPY . .

   # Expose port
   EXPOSE 8000

   # Run with uvicorn
   CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

Docker Compose
~~~~~~~~~~~~~~

.. code-block:: yaml

   version: '3.8'
   
   services:
     mcp-api:
       build: .
       ports:
         - "8000:8000"
       environment:
         - MCP_SERVER_DIR=/data/mcp_servers
         - MCP_CACHE_TTL=3600
         - MCP_API_KEY=${MCP_API_KEY}
       volumes:
         - ./mcp_servers:/data/mcp_servers:ro
       restart: unless-stopped
     
     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf:ro
         - ./ssl:/etc/nginx/ssl:ro
       depends_on:
         - mcp-api
       restart: unless-stopped

Production Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import os
   from fastapi import FastAPI
   from pathlib import Path

   def create_production_app():
       """Create production-ready FastAPI app"""
       app = FastAPI(
           title="MCP Server Manager",
           description="Production MCP server management API",
           version="1.0.0",
           docs_url="/docs" if os.getenv("ENABLE_DOCS") else None,
           redoc_url="/redoc" if os.getenv("ENABLE_DOCS") else None
       )
       
       # Production plugin configuration
       plugin = MCPBrowserPlugin(
           server_directory=Path(os.getenv("MCP_SERVER_DIR", "/data/mcp_servers")),
           cache_ttl=int(os.getenv("MCP_CACHE_TTL", "3600"))
       )
       
       app.include_router(
           plugin.get_router(),
           prefix="/api/v1/mcp",
           tags=["MCP Servers"]
       )
       
       # Health check
       @app.get("/health")
       async def health():
           return {"status": "healthy", "version": "1.0.0"}
       
       return app

   app = create_production_app()

Performance Optimization
------------------------

Response Caching
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from functools import lru_cache
   from typing import Dict, Any
   import json
   import hashlib

   class CachedMCPPlugin(MCPBrowserPlugin):
       """Plugin with response caching"""
       
       def __init__(self, **kwargs):
           super().__init__(**kwargs)
           self._response_cache = {}
       
       def _cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
           """Generate cache key for endpoint and parameters"""
           key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
           return hashlib.md5(key_data.encode()).hexdigest()
       
       @lru_cache(maxsize=100)
       def _get_cached_response(self, cache_key: str, timestamp: float):
           """LRU cached response getter"""
           return self._response_cache.get(cache_key)
       
       def get_router(self) -> APIRouter:
           router = super().get_router()
           
           @router.get("/servers/cached")
           async def get_servers_cached():
               """Cached server listing"""
               cache_key = self._cache_key("servers", {})
               timestamp = time.time()
               
               # Check cache first
               cached = self._get_cached_response(cache_key, int(timestamp / 60))  # 1-minute buckets
               if cached:
                   return cached
               
               # Load fresh data
               servers = await self.load_servers()
               response = [s.model_dump() for s in servers]
               
               # Cache response
               self._response_cache[cache_key] = response
               
               return response

Async Optimization
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   from concurrent.futures import ThreadPoolExecutor

   class OptimizedMCPPlugin(MCPBrowserPlugin):
       """Optimized plugin with async improvements"""
       
       def __init__(self, **kwargs):
           super().__init__(**kwargs)
           self._executor = ThreadPoolExecutor(max_workers=4)
       
       async def load_servers_parallel(self) -> List[DownloadedServerInfo]:
           """Load servers in parallel"""
           server_dirs = [
               d for d in self.server_directory.iterdir()
               if d.is_dir()
           ]
           
           # Process servers in parallel
           tasks = [
               asyncio.create_task(self._load_single_server(server_dir))
               for server_dir in server_dirs
           ]
           
           results = await asyncio.gather(*tasks, return_exceptions=True)
           
           # Filter successful results
           servers = [
               result for result in results
               if isinstance(result, DownloadedServerInfo)
           ]
           
           return servers
       
       async def _load_single_server(self, server_dir: Path) -> DownloadedServerInfo:
           """Load single server info asynchronously"""
           loop = asyncio.get_event_loop()
           
           # Run CPU-intensive operations in thread pool
           server_info = await loop.run_in_executor(
               self._executor,
               self._extract_server_info,
               server_dir
           )
           
           return server_info

Next Steps
----------

- :doc:`real-world-examples` - Production usage patterns
- :doc:`performance-optimization` - Scaling and optimization
- :doc:`troubleshooting` - Common issues and solutions