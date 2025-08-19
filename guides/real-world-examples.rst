Real-World Examples
===================

Production-ready examples and patterns for using Haive MCP in real applications.

MCP Server Dashboard
--------------------

Complete web dashboard for managing MCP servers:

Project Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

   mcp-dashboard/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py              # FastAPI app
   │   ├── models.py            # Additional Pydantic models
   │   ├── services/
   │   │   ├── __init__.py
   │   │   ├── mcp_service.py   # MCP business logic
   │   │   └── auth_service.py  # Authentication
   │   └── static/
   │       ├── dashboard.html
   │       ├── style.css
   │       └── app.js
   ├── docker-compose.yml
   ├── Dockerfile
   └── pyproject.toml

Main Application
~~~~~~~~~~~~~~~~

.. code-block:: python

   # app/main.py
   from fastapi import FastAPI, Request, Depends
   from fastapi.staticfiles import StaticFiles
   from fastapi.templating import Jinja2Templates
   from fastapi.responses import HTMLResponse
   from pathlib import Path
   import os

   from haive.mcp.plugins import MCPBrowserPlugin
   from .services.mcp_service import MCPService
   from .services.auth_service import AuthService

   # Configuration
   MCP_SERVERS_PATH = Path(os.getenv("MCP_SERVERS_PATH", "/data/mcp_servers"))
   CACHE_TTL = int(os.getenv("MCP_CACHE_TTL", "3600"))

   # Create FastAPI app
   app = FastAPI(
       title="MCP Server Dashboard",
       description="Production MCP server management dashboard",
       version="2.0.0"
   )

   # Static files and templates
   app.mount("/static", StaticFiles(directory="app/static"), name="static")
   templates = Jinja2Templates(directory="app/static")

   # Services
   auth_service = AuthService()
   mcp_service = MCPService(
       server_directory=MCP_SERVERS_PATH,
       cache_ttl=CACHE_TTL
   )

   # Dashboard UI
   @app.get("/", response_class=HTMLResponse)
   async def dashboard(request: Request):
       """Main dashboard page"""
       return templates.TemplateResponse("dashboard.html", {"request": request})

   # API Routes
   app.include_router(
       mcp_service.get_router(),
       prefix="/api/v1/mcp",
       tags=["MCP Management"],
       dependencies=[Depends(auth_service.verify_token)]
   )

   # Health and metrics
   @app.get("/health")
   async def health():
       servers = await mcp_service.load_servers()
       return {
           "status": "healthy",
           "timestamp": datetime.now().isoformat(),
           "servers": {
               "total": len(servers),
               "verified": sum(1 for s in servers if s.is_verified),
               "categories": len(set().union(*(s.capabilities for s in servers)))
           }
       }

   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(
           "app.main:app",
           host="0.0.0.0",
           port=8000,
           reload=os.getenv("ENVIRONMENT") == "development"
       )

Enhanced MCP Service
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # app/services/mcp_service.py
   from typing import List, Dict, Optional
   from pathlib import Path
   from datetime import datetime, timedelta
   from fastapi import APIRouter, HTTPException, BackgroundTasks
   import asyncio
   import logging

   from haive.mcp.plugins import MCPBrowserPlugin
   from haive.mcp.models import DownloadedServerInfo
   from ..models import ServerHealth, DashboardStats, ServerUpdate

   logger = logging.getLogger(__name__)

   class MCPService(MCPBrowserPlugin):
       """Enhanced MCP service for production dashboard"""
       
       def __init__(self, **kwargs):
           super().__init__(**kwargs)
           self._health_cache = {}
           self._last_health_check = None
       
       def get_router(self) -> APIRouter:
           """Enhanced router with dashboard-specific endpoints"""
           router = super().get_router()
           
           # Dashboard-specific endpoints
           @router.get("/dashboard/stats", response_model=DashboardStats)
           async def get_dashboard_stats():
               """Get comprehensive dashboard statistics"""
               servers = await self.load_servers()
               
               # Calculate statistics
               total_size = sum(s.file_size for s in servers)
               verified_count = sum(1 for s in servers if s.is_verified)
               
               # Capability distribution
               capability_counts = {}
               for server in servers:
                   for cap in server.capabilities:
                       capability_counts[cap] = capability_counts.get(cap, 0) + 1
               
               # Recent installations (last 30 days)
               recent_cutoff = datetime.now() - timedelta(days=30)
               recent_installs = [
                   s for s in servers 
                   if s.installed_date > recent_cutoff
               ]
               
               return DashboardStats(
                   total_servers=len(servers),
                   verified_servers=verified_count,
                   total_size_mb=round(total_size / (1024*1024), 2),
                   capability_distribution=capability_counts,
                   recent_installs=len(recent_installs),
                   health_score=await self._calculate_health_score(servers)
               )
           
           @router.get("/dashboard/health", response_model=List[ServerHealth])
           async def get_server_health():
               """Get health status of all servers"""
               return await self._check_all_server_health()
           
           @router.post("/dashboard/health/refresh")
           async def refresh_health_check(background_tasks: BackgroundTasks):
               """Trigger health check refresh"""
               background_tasks.add_task(self._refresh_health_cache)
               return {"message": "Health check refresh initiated"}
           
           @router.post("/servers/{server_name}/update")
           async def update_server(server_name: str, update: ServerUpdate):
               """Update server metadata"""
               servers = await self.load_servers()
               server = next((s for s in servers if s.name == server_name), None)
               
               if not server:
                   raise HTTPException(404, f"Server not found: {server_name}")
               
               # Update server metadata (simplified)
               if update.description:
                   # In real implementation, persist to database
                   logger.info(f"Updated {server_name} description: {update.description}")
               
               return {"message": f"Server {server_name} updated successfully"}
           
           return router
       
       async def _calculate_health_score(self, servers: List[DownloadedServerInfo]) -> float:
           """Calculate overall health score (0-100)"""
           if not servers:
               return 0.0
           
           health_factors = []
           
           # File existence check
           existing_count = sum(1 for s in servers if s.local_path.exists())
           health_factors.append(existing_count / len(servers) * 100)
           
           # Verification status
           verified_count = sum(1 for s in servers if s.is_verified)
           health_factors.append(verified_count / len(servers) * 100)
           
           # File size consistency
           consistent_count = 0
           for server in servers:
               if server.local_path.exists():
                   actual_size = server.local_path.stat().st_size
                   if actual_size == server.file_size:
                       consistent_count += 1
           health_factors.append(consistent_count / len(servers) * 100)
           
           return round(sum(health_factors) / len(health_factors), 1)
       
       async def _check_all_server_health(self) -> List[ServerHealth]:
           """Check health of all servers"""
           # Use cached results if recent
           if (self._last_health_check and 
               datetime.now() - self._last_health_check < timedelta(minutes=5)):
               return list(self._health_cache.values())
           
           servers = await self.load_servers()
           health_results = []
           
           # Check each server in parallel
           tasks = [
               self._check_server_health(server)
               for server in servers
           ]
           
           health_statuses = await asyncio.gather(*tasks, return_exceptions=True)
           
           for server, health in zip(servers, health_statuses):
               if isinstance(health, ServerHealth):
                   health_results.append(health)
                   self._health_cache[server.name] = health
               else:
                   # Handle exceptions
                   error_health = ServerHealth(
                       server_name=server.name,
                       status="error",
                       checks=[],
                       overall_health=0.0,
                       last_checked=datetime.now(),
                       error_message=str(health)
                   )
                   health_results.append(error_health)
           
           self._last_health_check = datetime.now()
           return health_results
       
       async def _check_server_health(self, server: DownloadedServerInfo) -> ServerHealth:
           """Check individual server health"""
           checks = []
           
           # File existence
           file_exists = server.local_path.exists()
           checks.append({
               "name": "file_exists",
               "status": "pass" if file_exists else "fail",
               "message": "Server files exist" if file_exists else "Server files missing"
           })
           
           # File size consistency
           size_consistent = False
           if file_exists:
               actual_size = server.local_path.stat().st_size
               size_consistent = actual_size == server.file_size
           
           checks.append({
               "name": "size_consistent",
               "status": "pass" if size_consistent else "fail",
               "message": "File size matches" if size_consistent else "File size mismatch"
           })
           
           # Package.json validation (for npm packages)
           package_valid = True
           if server.download_source == "npm" and file_exists:
               package_json = server.local_path / "package.json"
               package_valid = package_json.exists()
           
           checks.append({
               "name": "package_structure",
               "status": "pass" if package_valid else "warn",
               "message": "Package structure valid" if package_valid else "Missing package.json"
           })
           
           # Calculate overall health
           passed_checks = sum(1 for c in checks if c["status"] == "pass")
           overall_health = (passed_checks / len(checks)) * 100
           
           # Determine overall status
           if overall_health >= 90:
               status = "healthy"
           elif overall_health >= 70:
               status = "warning"
           else:
               status = "error"
           
           return ServerHealth(
               server_name=server.name,
               status=status,
               checks=checks,
               overall_health=round(overall_health, 1),
               last_checked=datetime.now()
           )

Additional Models
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # app/models.py
   from pydantic import BaseModel, Field
   from typing import List, Dict, Optional
   from datetime import datetime

   class ServerHealth(BaseModel):
       """Server health check results"""
       server_name: str
       status: str = Field(..., pattern="^(healthy|warning|error)$")
       checks: List[Dict[str, str]]
       overall_health: float = Field(..., ge=0.0, le=100.0)
       last_checked: datetime
       error_message: Optional[str] = None

   class DashboardStats(BaseModel):
       """Dashboard statistics"""
       total_servers: int
       verified_servers: int
       total_size_mb: float
       capability_distribution: Dict[str, int]
       recent_installs: int
       health_score: float

   class ServerUpdate(BaseModel):
       """Server update request"""
       description: Optional[str] = None
       capabilities: Optional[List[str]] = None
       verified: Optional[bool] = None

Frontend Dashboard
~~~~~~~~~~~~~~~~~~

.. code-block:: html

   <!-- app/static/dashboard.html -->
   <!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>MCP Server Dashboard</title>
       <link rel="stylesheet" href="/static/style.css">
       <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   </head>
   <body>
       <div class="container">
           <header>
               <h1>🔧 MCP Server Dashboard</h1>
               <div class="header-stats">
                   <div class="stat-card">
                       <span id="total-servers">-</span>
                       <label>Total Servers</label>
                   </div>
                   <div class="stat-card">
                       <span id="health-score">-</span>
                       <label>Health Score</label>
                   </div>
                   <div class="stat-card">
                       <span id="total-size">-</span>
                       <label>Total Size</label>
                   </div>
               </div>
           </header>

           <main>
               <section class="dashboard-section">
                   <h2>📊 Server Statistics</h2>
                   <div class="charts">
                       <canvas id="capabilities-chart"></canvas>
                   </div>
               </section>

               <section class="dashboard-section">
                   <h2>📋 Server List</h2>
                   <div class="controls">
                       <input type="search" id="search-input" placeholder="Search servers...">
                       <select id="category-filter">
                           <option value="">All Categories</option>
                       </select>
                       <button id="refresh-btn">🔄 Refresh</button>
                   </div>
                   <div id="servers-grid" class="servers-grid">
                       <!-- Server cards populated by JavaScript -->
                   </div>
               </section>

               <section class="dashboard-section">
                   <h2>🏥 Health Status</h2>
                   <div id="health-grid" class="health-grid">
                       <!-- Health cards populated by JavaScript -->
                   </div>
               </section>
           </main>
       </div>

       <script src="/static/app.js"></script>
   </body>
   </html>

MCP Plugin Marketplace
-----------------------

A marketplace for discovering and installing MCP plugins:

Marketplace Service
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # marketplace/service.py
   from typing import List, Dict, Optional
   from pathlib import Path
   from fastapi import APIRouter, HTTPException, BackgroundTasks
   import httpx
   import asyncio
   import subprocess
   import logging

   from haive.mcp.plugins import MCPBrowserPlugin
   from haive.mcp.models import MCPServerInfo, DownloadedServerInfo
   from .models import MarketplaceServer, InstallationResult

   logger = logging.getLogger(__name__)

   class MCPMarketplaceService(MCPBrowserPlugin):
       """MCP plugin marketplace service"""
       
       def __init__(self, **kwargs):
           super().__init__(**kwargs)
           self._marketplace_cache = None
           self._npm_client = httpx.AsyncClient()
       
       def get_router(self) -> APIRouter:
           router = super().get_router()
           
           @router.get("/marketplace/available", response_model=List[MarketplaceServer])
           async def get_available_servers():
               """Get all available MCP servers from marketplace"""
               return await self._fetch_marketplace_servers()
           
           @router.get("/marketplace/search")
           async def search_marketplace(q: str):
               """Search marketplace servers"""
               available = await self._fetch_marketplace_servers()
               return [
                   server for server in available
                   if q.lower() in server.name.lower() or 
                      q.lower() in server.description.lower() or
                      any(q.lower() in cap.lower() for cap in server.capabilities)
               ]
           
           @router.post("/marketplace/install/{package_name}")
           async def install_server(
               package_name: str, 
               background_tasks: BackgroundTasks
           ):
               """Install server from marketplace"""
               # Validate package exists
               available = await self._fetch_marketplace_servers()
               server_info = next(
                   (s for s in available if s.package_name == package_name), 
                   None
               )
               
               if not server_info:
                   raise HTTPException(404, f"Package not found: {package_name}")
               
               # Start installation in background
               background_tasks.add_task(
                   self._install_server_background,
                   server_info
               )
               
               return {
                   "message": f"Installation started for {package_name}",
                   "package_name": package_name,
                   "status": "installing"
               }
           
           @router.get("/marketplace/installation-status/{package_name}")
           async def get_installation_status(package_name: str):
               """Get installation status for a package"""
               # Check if already installed
               installed = await self.load_servers()
               installed_server = next(
                   (s for s in installed if package_name in str(s.local_path)),
                   None
               )
               
               if installed_server:
                   return {
                       "package_name": package_name,
                       "status": "installed",
                       "server": installed_server.model_dump()
                   }
               
               return {
                   "package_name": package_name,
                   "status": "not_installed"
               }
           
           return router
       
       async def _fetch_marketplace_servers(self) -> List[MarketplaceServer]:
           """Fetch available servers from NPM registry"""
           if self._marketplace_cache:
               return self._marketplace_cache
           
           # Search NPM for MCP packages
           search_url = "https://registry.npmjs.org/-/v1/search"
           params = {
               "text": "keywords:mcp model-context-protocol",
               "size": 100
           }
           
           try:
               response = await self._npm_client.get(search_url, params=params)
               response.raise_for_status()
               data = response.json()
               
               marketplace_servers = []
               for package in data.get("objects", []):
                   pkg_data = package.get("package", {})
                   
                   # Extract server information
                   server = MarketplaceServer(
                       package_name=pkg_data.get("name", ""),
                       name=self._clean_package_name(pkg_data.get("name", "")),
                       description=pkg_data.get("description", ""),
                       version=pkg_data.get("version", "1.0.0"),
                       capabilities=self._extract_capabilities(pkg_data),
                       npm_downloads=pkg_data.get("downloads", {}).get("monthly", 0),
                       github_stars=self._extract_github_stars(pkg_data),
                       last_updated=pkg_data.get("date", ""),
                       homepage=pkg_data.get("links", {}).get("homepage", ""),
                       repository=pkg_data.get("links", {}).get("repository", "")
                   )
                   
                   marketplace_servers.append(server)
               
               self._marketplace_cache = marketplace_servers
               return marketplace_servers
               
           except Exception as e:
               logger.error(f"Error fetching marketplace data: {e}")
               return []
       
       async def _install_server_background(self, server_info: MarketplaceServer):
           """Install server in background"""
           try:
               logger.info(f"Installing {server_info.package_name}")
               
               # Create installation directory
               install_dir = self.server_directory / server_info.name
               install_dir.mkdir(parents=True, exist_ok=True)
               
               # Run npm install
               process = await asyncio.create_subprocess_exec(
                   "npm", "install", server_info.package_name,
                   cwd=install_dir,
                   stdout=asyncio.subprocess.PIPE,
                   stderr=asyncio.subprocess.PIPE
               )
               
               stdout, stderr = await process.communicate()
               
               if process.returncode == 0:
                   logger.info(f"Successfully installed {server_info.package_name}")
                   # Clear cache to pick up new server
                   self.clear_cache()
               else:
                   logger.error(f"Failed to install {server_info.package_name}: {stderr.decode()}")
                   
           except Exception as e:
               logger.error(f"Installation error for {server_info.package_name}: {e}")

CI/CD MCP Server Manager
------------------------

Automated MCP server management in CI/CD pipelines:

GitHub Actions Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # .github/workflows/mcp-management.yml
   name: MCP Server Management
   
   on:
     schedule:
       - cron: '0 6 * * *'  # Daily at 6 AM
     workflow_dispatch:
       inputs:
         action:
           description: 'Action to perform'
           required: true
           default: 'health-check'
           type: choice
           options:
             - health-check
             - update-servers
             - generate-report
   
   jobs:
     mcp-management:
       runs-on: ubuntu-latest
       
       steps:
       - name: Checkout code
         uses: actions/checkout@v3
       
       - name: Set up Python
         uses: actions/setup-python@v4
         with:
           python-version: '3.11'
       
       - name: Install dependencies
         run: |
           pip install poetry
           poetry install
       
       - name: Run MCP Health Check
         if: github.event.inputs.action == 'health-check' || github.event_name == 'schedule'
         run: poetry run python scripts/mcp_health_check.py
         env:
           MCP_SERVERS_PATH: ${{ secrets.MCP_SERVERS_PATH }}
       
       - name: Update MCP Servers
         if: github.event.inputs.action == 'update-servers'
         run: poetry run python scripts/mcp_update.py
       
       - name: Generate MCP Report
         if: github.event.inputs.action == 'generate-report'
         run: poetry run python scripts/mcp_report.py
       
       - name: Upload Report
         if: always()
         uses: actions/upload-artifact@v3
         with:
           name: mcp-report
           path: reports/

Health Check Script
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # scripts/mcp_health_check.py
   import asyncio
   import os
   import json
   from pathlib import Path
   from datetime import datetime
   from typing import Dict, List

   from haive.mcp.plugins import MCPBrowserPlugin

   async def main():
       """Run comprehensive MCP health check"""
       server_path = Path(os.getenv("MCP_SERVERS_PATH", "/data/mcp_servers"))
       
       print(f"🏥 MCP Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
       print(f"📁 Server Directory: {server_path}")
       print("=" * 60)
       
       # Initialize plugin
       plugin = MCPBrowserPlugin(server_directory=server_path)
       
       # Load servers
       servers = await plugin.load_servers()
       print(f"📦 Found {len(servers)} MCP servers")
       
       # Health checks
       health_results = {
           "timestamp": datetime.now().isoformat(),
           "total_servers": len(servers),
           "healthy_servers": 0,
           "warning_servers": 0,
           "error_servers": 0,
           "checks": []
       }
       
       for server in servers:
           print(f"\\n🔍 Checking {server.name}...")
           
           check_result = {
               "server_name": server.name,
               "version": server.version,
               "status": "healthy",
               "issues": []
           }
           
           # File existence check
           if not server.local_path.exists():
               check_result["issues"].append("Server files missing")
               check_result["status"] = "error"
           else:
               print(f"  ✅ Files exist at {server.local_path}")
           
           # Size consistency check
           if server.local_path.exists():
               actual_size = get_directory_size(server.local_path)
               if abs(actual_size - server.file_size) > 1024:  # 1KB tolerance
                   check_result["issues"].append(f"Size mismatch: expected {server.file_size}, got {actual_size}")
                   check_result["status"] = "warning" if check_result["status"] == "healthy" else check_result["status"]
               else:
                   print(f"  ✅ Size consistent: {actual_size} bytes")
           
           # Package structure check (for npm packages)
           if server.download_source == "npm" and server.local_path.exists():
               package_json = server.local_path / "package.json"
               if not package_json.exists():
                   check_result["issues"].append("Missing package.json")
                   check_result["status"] = "warning" if check_result["status"] == "healthy" else check_result["status"]
               else:
                   print(f"  ✅ Package structure valid")
           
           # Update counters
           if check_result["status"] == "healthy":
               health_results["healthy_servers"] += 1
               print(f"  🟢 {server.name}: HEALTHY")
           elif check_result["status"] == "warning":
               health_results["warning_servers"] += 1
               print(f"  🟡 {server.name}: WARNING - {', '.join(check_result['issues'])}")
           else:
               health_results["error_servers"] += 1
               print(f"  🔴 {server.name}: ERROR - {', '.join(check_result['issues'])}")
           
           health_results["checks"].append(check_result)
       
       # Summary
       print(f"\\n📊 Health Check Summary:")
       print(f"  🟢 Healthy: {health_results['healthy_servers']}")
       print(f"  🟡 Warning: {health_results['warning_servers']}")
       print(f"  🔴 Error: {health_results['error_servers']}")
       
       # Calculate health score
       total = len(servers)
       if total > 0:
           health_score = (
               health_results['healthy_servers'] + 
               health_results['warning_servers'] * 0.5
           ) / total * 100
           print(f"  📈 Overall Health Score: {health_score:.1f}%")
           health_results["health_score"] = health_score
       
       # Save results
       reports_dir = Path("reports")
       reports_dir.mkdir(exist_ok=True)
       
       report_file = reports_dir / f"mcp_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
       with open(report_file, 'w') as f:
           json.dump(health_results, f, indent=2)
       
       print(f"\\n📄 Report saved to: {report_file}")
       
       # Exit with appropriate code
       if health_results["error_servers"] > 0:
           exit(1)
       elif health_results["warning_servers"] > 0:
           exit(2)
       else:
           exit(0)

   def get_directory_size(directory: Path) -> int:
       """Calculate total size of directory"""
       total = 0
       for path in directory.rglob('*'):
           if path.is_file():
               total += path.stat().st_size
       return total

   if __name__ == "__main__":
       asyncio.run(main())

Microservices Architecture
--------------------------

Distributed MCP management across microservices:

Service Architecture
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   mcp-microservices/
   ├── services/
   │   ├── mcp-discovery/       # Server discovery service
   │   │   ├── Dockerfile
   │   │   └── app.py
   │   ├── mcp-installer/       # Installation service
   │   │   ├── Dockerfile
   │   │   └── app.py
   │   ├── mcp-health/          # Health monitoring
   │   │   ├── Dockerfile
   │   │   └── app.py
   │   └── mcp-gateway/         # API gateway
   │       ├── Dockerfile
   │       └── app.py
   ├── docker-compose.yml
   ├── k8s/                     # Kubernetes manifests
   └── shared/
       ├── models.py
       └── utils.py

Discovery Service
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # services/mcp-discovery/app.py
   from fastapi import FastAPI
   from typing import List, Dict
   import asyncio
   import httpx
   from datetime import datetime, timedelta

   from haive.mcp.plugins import MCPBrowserPlugin
   from shared.models import DiscoveryResult, ServerRegistry

   app = FastAPI(title="MCP Discovery Service", version="1.0.0")

   class MCPDiscoveryService:
       """Service for discovering available MCP servers"""
       
       def __init__(self):
           self.registry = ServerRegistry()
           self.last_scan = None
       
       async def discover_npm_packages(self) -> List[Dict]:
           """Discover MCP packages from NPM"""
           async with httpx.AsyncClient() as client:
               # Search for MCP packages
               response = await client.get(
                   "https://registry.npmjs.org/-/v1/search",
                   params={
                       "text": "keywords:mcp model-context-protocol",
                       "size": 250
                   }
               )
               return response.json().get("objects", [])
       
       async def discover_github_repos(self) -> List[Dict]:
           """Discover MCP repositories from GitHub"""
           async with httpx.AsyncClient() as client:
               response = await client.get(
                   "https://api.github.com/search/repositories",
                   params={
                       "q": "model-context-protocol OR mcp-server",
                       "sort": "stars",
                       "per_page": 100
                   }
               )
               return response.json().get("items", [])
       
       async def run_discovery(self) -> DiscoveryResult:
           """Run complete discovery scan"""
           print(f"🔍 Starting MCP discovery scan at {datetime.now()}")
           
           # Run discovery tasks in parallel
           npm_task = asyncio.create_task(self.discover_npm_packages())
           github_task = asyncio.create_task(self.discover_github_repos())
           
           npm_packages, github_repos = await asyncio.gather(
               npm_task, github_task, return_exceptions=True
           )
           
           # Process results
           discovered_servers = []
           
           # Process NPM packages
           if not isinstance(npm_packages, Exception):
               for pkg in npm_packages:
                   server_info = self._process_npm_package(pkg)
                   if server_info:
                       discovered_servers.append(server_info)
           
           # Process GitHub repositories
           if not isinstance(github_repos, Exception):
               for repo in github_repos:
                   server_info = self._process_github_repo(repo)
                   if server_info:
                       discovered_servers.append(server_info)
           
           # Update registry
           self.registry.update_servers(discovered_servers)
           self.last_scan = datetime.now()
           
           return DiscoveryResult(
               timestamp=self.last_scan,
               npm_packages_found=len(npm_packages) if not isinstance(npm_packages, Exception) else 0,
               github_repos_found=len(github_repos) if not isinstance(github_repos, Exception) else 0,
               total_servers=len(discovered_servers)
           )

   # Service instance
   discovery_service = MCPDiscoveryService()

   # API endpoints
   @app.get("/discover")
   async def run_discovery():
       """Trigger discovery scan"""
       result = await discovery_service.run_discovery()
       return result

   @app.get("/registry")
   async def get_registry():
       """Get current server registry"""
       return discovery_service.registry.get_all_servers()

   @app.get("/health")
   async def health():
       return {
           "status": "healthy",
           "last_scan": discovery_service.last_scan.isoformat() if discovery_service.last_scan else None
       }

Docker Compose Setup
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'
   
   services:
     mcp-discovery:
       build: ./services/mcp-discovery
       ports:
         - "8001:8000"
       environment:
         - SERVICE_NAME=mcp-discovery
         - REDIS_URL=redis://redis:6379
       depends_on:
         - redis
       restart: unless-stopped
     
     mcp-installer:
       build: ./services/mcp-installer
       ports:
         - "8002:8000"
       environment:
         - SERVICE_NAME=mcp-installer
         - MCP_SERVERS_PATH=/data/mcp_servers
       volumes:
         - mcp_servers:/data/mcp_servers
       restart: unless-stopped
     
     mcp-health:
       build: ./services/mcp-health
       ports:
         - "8003:8000"
       environment:
         - SERVICE_NAME=mcp-health
         - MCP_SERVERS_PATH=/data/mcp_servers
       volumes:
         - mcp_servers:/data/mcp_servers:ro
       restart: unless-stopped
     
     mcp-gateway:
       build: ./services/mcp-gateway
       ports:
         - "8000:8000"
       environment:
         - DISCOVERY_URL=http://mcp-discovery:8000
         - INSTALLER_URL=http://mcp-installer:8000
         - HEALTH_URL=http://mcp-health:8000
       depends_on:
         - mcp-discovery
         - mcp-installer
         - mcp-health
       restart: unless-stopped
     
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
       restart: unless-stopped
   
   volumes:
     mcp_servers:
     redis_data:

Performance Testing
-------------------

Load testing MCP services:

Locust Load Test
~~~~~~~~~~~~~~~~

.. code-block:: python

   # tests/load_test.py
   from locust import HttpUser, task, between
   import random
   import json

   class MCPServiceUser(HttpUser):
       """Load test user for MCP services"""
       
       wait_time = between(1, 3)
       
       def on_start(self):
           """Setup user session"""
           # Get list of available servers for testing
           response = self.client.get("/api/v1/mcp/servers")
           if response.status_code == 200:
               self.servers = response.json()
               self.server_names = [s["name"] for s in self.servers]
           else:
               self.servers = []
               self.server_names = []
       
       @task(3)
       def list_servers(self):
           """Test server listing endpoint"""
           self.client.get("/api/v1/mcp/servers")
       
       @task(2)
       def get_server_details(self):
           """Test getting specific server details"""
           if self.server_names:
               server_name = random.choice(self.server_names)
               self.client.get(f"/api/v1/mcp/servers/{server_name}")
       
       @task(1)
       def search_servers(self):
           """Test server search functionality"""
           search_terms = ["database", "ai", "web", "tool", "search"]
           term = random.choice(search_terms)
           self.client.get(f"/api/v1/mcp/search?q={term}")
       
       @task(1)
       def get_categories(self):
           """Test categories endpoint"""
           self.client.get("/api/v1/mcp/categories")
       
       @task(1)
       def get_dashboard_stats(self):
           """Test dashboard statistics"""
           self.client.get("/api/v1/mcp/dashboard/stats")

   # Run with: locust -f tests/load_test.py --host=http://localhost:8000

Monitoring Integration
----------------------

Production monitoring with Prometheus and Grafana:

Metrics Collection
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # monitoring/metrics.py
   from prometheus_client import Counter, Histogram, Gauge, generate_latest
   from fastapi import Response
   import time

   # Metrics
   REQUEST_COUNT = Counter(
       'mcp_requests_total',
       'Total MCP API requests',
       ['method', 'endpoint', 'status']
   )

   REQUEST_DURATION = Histogram(
       'mcp_request_duration_seconds',
       'MCP API request duration'
   )

   SERVERS_TOTAL = Gauge(
       'mcp_servers_total',
       'Total number of MCP servers'
   )

   SERVERS_HEALTHY = Gauge(
       'mcp_servers_healthy',
       'Number of healthy MCP servers'
   )

   class MetricsMiddleware:
       """Middleware to collect metrics"""
       
       def __init__(self, app):
           self.app = app
       
       async def __call__(self, scope, receive, send):
           if scope["type"] == "http":
               start_time = time.time()
               
               # Process request
               response = await self.app(scope, receive, send)
               
               # Record metrics
               duration = time.time() - start_time
               REQUEST_DURATION.observe(duration)
               
               REQUEST_COUNT.labels(
                   method=scope["method"],
                   endpoint=scope["path"],
                   status="200"  # Simplified
               ).inc()
           
           return response

   # Metrics endpoint
   @app.get("/metrics")
   async def get_metrics():
       """Prometheus metrics endpoint"""
       return Response(generate_latest(), media_type="text/plain")

These real-world examples demonstrate production-ready patterns for using Haive MCP in various scenarios, from simple dashboards to complex microservices architectures. Each example follows our Pydantic-first design principles and provides comprehensive error handling, monitoring, and testing patterns.

Next Steps
----------

- :doc:`performance-optimization` - Scaling and optimization
- :doc:`troubleshooting` - Common issues and solutions