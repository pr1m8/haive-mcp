#!/usr/bin/env python3
"""FastAPI server for browsing downloaded MCP servers.

This server provides a web interface to explore the 63+ downloaded MCP servers,
view their READMEs, analyze their tools, and understand their capabilities.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import re
from datetime import datetime
import uvicorn

app = FastAPI(
    title="MCP Servers Browser",
    description="Browse and explore 63+ downloaded MCP servers",
    version="1.0.0"
)

# Configuration
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "scratches/mcp-analysis/mcp_servers_data.csv"
INSTALL_REPORT = BASE_DIR / "mcp_install_report_20250819_133347.json"

class MCPServerBrowser:
    """Browser for downloaded MCP servers."""
    
    def __init__(self):
        self.servers_data = None
        self.installed_servers = set()
        self.load_data()
    
    def load_data(self):
        """Load server data and installation reports."""
        # Load CSV data
        if DATA_FILE.exists():
            self.servers_data = pd.read_csv(DATA_FILE)
        
        # Load installation report
        if INSTALL_REPORT.exists():
            with open(INSTALL_REPORT, 'r') as f:
                report = json.load(f)
                self.installed_servers = set(report.get('installed_servers', []))
    
    def get_server_info(self, server_name: str) -> Dict:
        """Get comprehensive info about a server."""
        if self.servers_data is None:
            return None
        
        # Find server in data
        server_row = self.servers_data[self.servers_data['name'] == server_name]
        if server_row.empty:
            return None
        
        server_info = server_row.iloc[0].to_dict()
        
        # Check if it's installed (downloaded)
        server_info['is_downloaded'] = server_name in self.installed_servers
        
        # Get local directory info if downloaded
        if server_info['is_downloaded']:
            local_info = self.get_local_server_info(server_name)
            server_info.update(local_info)
        
        return server_info
    
    def get_local_server_info(self, server_name: str) -> Dict:
        """Get info about locally downloaded server."""
        # Try to find the directory
        repo_name = server_name.split('/')[-1]  # Get repo name from org/repo
        potential_dirs = [repo_name]
        
        # Some common variations
        if '-' in repo_name:
            potential_dirs.append(repo_name.replace('-', '_'))
        if '_' in repo_name:
            potential_dirs.append(repo_name.replace('_', '-'))
        
        local_dir = None
        for dir_name in potential_dirs:
            if Path(dir_name).exists():
                local_dir = Path(dir_name)
                break
        
        if not local_dir:
            return {'local_dir': None, 'readme': None, 'files': []}
        
        # Read README
        readme_content = None
        for readme_name in ['README.md', 'README.rst', 'README.txt', 'README']:
            readme_path = local_dir / readme_name
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        readme_content = f.read()
                    break
                except:
                    pass
        
        # Get file listing
        files = []
        if local_dir.exists():
            for item in local_dir.iterdir():
                if item.name.startswith('.'):
                    continue
                files.append({
                    'name': item.name,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None
                })
        
        # Look for MCP-specific files
        mcp_files = self.find_mcp_files(local_dir)
        
        return {
            'local_dir': str(local_dir),
            'readme': readme_content,
            'files': files,
            'mcp_files': mcp_files
        }
    
    def find_mcp_files(self, directory: Path) -> List[Dict]:
        """Find MCP-related files in the directory."""
        mcp_files = []
        
        if not directory.exists():
            return mcp_files
        
        # Common MCP file patterns
        patterns = [
            r'.*mcp.*\.py$',
            r'.*mcp.*\.js$',
            r'.*mcp.*\.ts$',
            r'.*server.*\.py$',
            r'.*server.*\.js$',
            r'.*server.*\.ts$',
            r'package\.json$',
            r'pyproject\.toml$',
            r'requirements\.txt$',
            r'setup\.py$'
        ]
        
        for item in directory.rglob('*'):
            if item.is_file():
                for pattern in patterns:
                    if re.match(pattern, item.name, re.IGNORECASE):
                        try:
                            # Try to read file content (first 1000 chars)
                            with open(item, 'r', encoding='utf-8') as f:
                                content = f.read(1000)
                            
                            mcp_files.append({
                                'path': str(item.relative_to(directory)),
                                'name': item.name,
                                'size': item.stat().st_size,
                                'preview': content
                            })
                        except:
                            mcp_files.append({
                                'path': str(item.relative_to(directory)),
                                'name': item.name,
                                'size': item.stat().st_size,
                                'preview': 'Binary file or encoding error'
                            })
                        break
        
        return mcp_files[:20]  # Limit to first 20 files

# Initialize browser
browser = MCPServerBrowser()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with server list."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Servers Browser</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #f0f8ff; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
            .stat {{ background: #e6f3ff; padding: 15px; border-radius: 5px; text-align: center; }}
            .server-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }}
            .server-card {{ border: 1px solid #ddd; padding: 15px; border-radius: 8px; }}
            .server-card.downloaded {{ border-color: #4CAF50; background-color: #f0fff0; }}
            .server-name {{ font-weight: bold; color: #333; }}
            .server-description {{ margin: 10px 0; color: #666; }}
            .server-meta {{ font-size: 0.9em; color: #999; }}
            .button {{ background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔌 MCP Servers Browser</h1>
            <p>Browse and explore {len(browser.installed_servers)} downloaded MCP servers from our database of 1,960+ servers</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>{len(browser.installed_servers)}</h3>
                <p>Downloaded Servers</p>
            </div>
            <div class="stat">
                <h3>{len(browser.servers_data) if browser.servers_data is not None else 0}</h3>
                <p>Total in Database</p>
            </div>
            <div class="stat">
                <h3>98.4%</h3>
                <p>Success Rate</p>
            </div>
        </div>
        
        <h2>📋 Available APIs</h2>
        <ul>
            <li><a href="/servers">List all downloaded servers (JSON)</a></li>
            <li><a href="/servers/browser-tools-mcp">Example: View specific server</a></li>
            <li><a href="/search?q=mcp">Search servers by keyword</a></li>
            <li><a href="/stats">Installation statistics</a></li>
        </ul>
        
        <h2>🚀 Quick Links</h2>
        <div style="margin: 20px 0;">
            <a href="/servers/browser-tools-mcp" class="button">Browser Tools MCP</a>
            <a href="/servers/fastapi_mcp" class="button">FastAPI MCP</a>
            <a href="/servers/mcp-agent" class="button">MCP Agent</a>
            <a href="/servers/awesome-mcp-servers" class="button">Awesome MCP Servers</a>
        </div>
        
        <p style="margin-top: 40px; color: #666; text-align: center;">
            Server running at <a href="http://localhost:8080">http://localhost:8080</a><br>
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </body>
    </html>
    """
    return html

@app.get("/servers")
async def list_servers():
    """List all downloaded servers."""
    if not browser.installed_servers:
        return {"error": "No servers installed"}
    
    servers = []
    for server_name in list(browser.installed_servers)[:50]:  # Limit to first 50
        server_info = browser.get_server_info(server_name)
        if server_info:
            servers.append({
                "name": server_name,
                "description": server_info.get('description', 'No description'),
                "stars": server_info.get('stars', 0),
                "language": server_info.get('language', 'Unknown'),
                "category": server_info.get('category', 'Unknown'),
                "is_downloaded": True,
                "url": f"/servers/{server_name.replace('/', '-')}"
            })
    
    return {"servers": servers, "total": len(servers)}

@app.get("/servers/{server_name}")
async def get_server(server_name: str):
    """Get detailed info about a specific server."""
    # Handle URL encoding
    if '-' in server_name and '/' not in server_name:
        # Try to find the server by repository name
        for installed_name in browser.installed_servers:
            if installed_name.split('/')[-1] == server_name or installed_name.replace('/', '-') == server_name:
                server_name = installed_name
                break
    
    server_info = browser.get_server_info(server_name)
    if not server_info:
        raise HTTPException(status_code=404, detail="Server not found")
    
    return server_info

@app.get("/servers/{server_name}/readme")
async def get_server_readme(server_name: str):
    """Get README content for a server."""
    # Handle URL encoding
    if '-' in server_name and '/' not in server_name:
        for installed_name in browser.installed_servers:
            if installed_name.split('/')[-1] == server_name or installed_name.replace('/', '-') == server_name:
                server_name = installed_name
                break
    
    server_info = browser.get_server_info(server_name)
    if not server_info or not server_info.get('is_downloaded'):
        raise HTTPException(status_code=404, detail="Server not found or not downloaded")
    
    readme = server_info.get('readme')
    if not readme:
        return {"error": "No README found"}
    
    return {"readme": readme, "server": server_name}

@app.get("/search")
async def search_servers(q: str = Query(..., description="Search query")):
    """Search servers by keyword."""
    if not browser.servers_data is not None:
        return {"error": "No server data loaded"}
    
    # Search in name and description
    results = browser.servers_data[
        browser.servers_data['name'].str.contains(q, case=False, na=False) |
        browser.servers_data['description'].str.contains(q, case=False, na=False)
    ]
    
    servers = []
    for _, row in results.head(20).iterrows():
        servers.append({
            "name": row['name'],
            "description": row['description'],
            "stars": row['stars'],
            "language": row.get('language', 'Unknown'),
            "is_downloaded": row['name'] in browser.installed_servers
        })
    
    return {"query": q, "results": servers, "total_found": len(results)}

@app.get("/stats")
async def get_stats():
    """Get installation and server statistics."""
    if browser.servers_data is None:
        return {"error": "No data loaded"}
    
    # Basic stats
    total_servers = len(browser.servers_data)
    downloaded_servers = len(browser.installed_servers)
    
    # Language distribution of downloaded servers
    downloaded_data = browser.servers_data[browser.servers_data['name'].isin(browser.installed_servers)]
    language_counts = downloaded_data['language'].value_counts().to_dict()
    
    # Category distribution
    category_counts = downloaded_data['category'].value_counts().to_dict()
    
    # Star distribution
    star_ranges = {
        "1000+": len(downloaded_data[downloaded_data['stars'] >= 1000]),
        "100-999": len(downloaded_data[(downloaded_data['stars'] >= 100) & (downloaded_data['stars'] < 1000)]),
        "10-99": len(downloaded_data[(downloaded_data['stars'] >= 10) & (downloaded_data['stars'] < 100)]),
        "1-9": len(downloaded_data[(downloaded_data['stars'] >= 1) & (downloaded_data['stars'] < 10)]),
        "0": len(downloaded_data[downloaded_data['stars'] == 0])
    }
    
    return {
        "total_servers_in_db": total_servers,
        "downloaded_servers": downloaded_servers,
        "success_rate": f"{(downloaded_servers / 64 * 100):.1f}%",  # Based on last attempt
        "language_distribution": language_counts,
        "category_distribution": category_counts,
        "star_distribution": star_ranges,
        "top_downloaded_servers": downloaded_data.nlargest(10, 'stars')[['name', 'stars', 'description']].to_dict('records')
    }

if __name__ == "__main__":
    print("🚀 Starting MCP Servers Browser...")
    print("📊 Browse your downloaded MCP servers at: http://localhost:8080")
    print(f"📁 Found {len(browser.installed_servers)} downloaded servers")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)