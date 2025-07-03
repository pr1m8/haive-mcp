#!/usr/bin/env python3
"""Simple background downloader that doesn't depend on broken modules."""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return result."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=cwd,
            timeout=300
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def download_npm_servers():
    """Download NPM-based MCP servers."""
    print("📦 Downloading NPM MCP servers...")
    
    npm_servers = [
        "@modelcontextprotocol/server-filesystem",
        "@modelcontextprotocol/server-github", 
        "@modelcontextprotocol/server-sqlite",
        "@modelcontextprotocol/server-postgres",
        "@modelcontextprotocol/server-fetch",
        "@modelcontextprotocol/server-time"
    ]
    
    results = []
    for server in npm_servers:
        print(f"  Installing {server}...")
        
        # Try global install
        result = run_command(f"npm install -g {server}")
        if result["success"]:
            print(f"    ✅ {server} installed globally")
            results.append({"server": server, "method": "npm-global", "success": True})
        else:
            # Try local install
            result = run_command(f"npm install {server}", cwd="downloads/npm_local")
            if result["success"]:
                print(f"    ✅ {server} installed locally")
                results.append({"server": server, "method": "npm-local", "success": True})
            else:
                print(f"    ❌ {server} failed: {result.get('error', 'Unknown error')}")
                results.append({"server": server, "success": False, "error": result.get("error")})
    
    return results

def download_community_servers():
    """Download community MCP servers."""
    print("🌍 Downloading community MCP servers...")
    
    # Create download directory
    Path("downloads/community").mkdir(parents=True, exist_ok=True)
    
    # Common community servers (examples)
    community_repos = [
        "https://github.com/octocat/Hello-World.git",  # Test repo
        # Add more community repos as discovered
    ]
    
    results = []
    for repo in community_repos:
        repo_name = Path(repo).stem.replace(".git", "")
        print(f"  Cloning {repo_name}...")
        
        result = run_command(f"git clone {repo}", cwd="downloads/community")
        if result["success"]:
            print(f"    ✅ {repo_name} cloned")
            results.append({"repo": repo, "success": True})
        else:
            print(f"    ❌ {repo_name} failed: {result.get('error', 'Unknown error')}")
            results.append({"repo": repo, "success": False, "error": result.get("error")})
    
    return results

def create_master_config(npm_results, community_results):
    """Create master configuration file."""
    print("📋 Creating master configuration...")
    
    config = {
        "generated_at": datetime.now().isoformat(),
        "mcpServers": {},
        "download_summary": {
            "npm_servers": len([r for r in npm_results if r["success"]]),
            "community_repos": len([r for r in community_results if r["success"]]),
            "total_successful": len([r for r in npm_results + community_results if r["success"]])
        }
    }
    
    # Add successful NPM servers
    for result in npm_results:
        if result["success"]:
            server_name = result["server"].split("/")[-1].replace("server-", "")
            
            if result["method"] == "npm-global":
                command = f"npx {result['server']}"
            else:
                command = f"npm run {result['server']}"
            
            config["mcpServers"][server_name] = {
                "command": command,
                "args": [],
                "env": {},
                "source": result["server"],
                "method": result["method"]
            }
    
    # Save config
    config_path = Path("downloads/master_mcp_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Master config saved: {config_path}")
    return config_path

def main():
    """Main download function."""
    print("🚀 Starting Simple Background MCP Download")
    print("=" * 60)
    
    start_time = time.time()
    
    # Create downloads directory
    Path("downloads").mkdir(exist_ok=True)
    Path("downloads/npm_local").mkdir(exist_ok=True)
    
    # Download NPM servers
    npm_results = download_npm_servers()
    
    # Download community servers  
    community_results = download_community_servers()
    
    # Create master config
    config_path = create_master_config(npm_results, community_results)
    
    # Summary
    total_time = time.time() - start_time
    successful = len([r for r in npm_results + community_results if r["success"]])
    total = len(npm_results + community_results)
    
    print("\n" + "=" * 60)
    print("🎉 Download Complete!")
    print(f"📊 Results: {successful}/{total} successful ({successful/total*100:.1f}%)")
    print(f"⏱️  Time: {total_time:.1f} seconds")
    print(f"📋 Config: {config_path}")
    print("=" * 60)
    
    # Save final status
    status = {
        "completed_at": datetime.now().isoformat(),
        "runtime_seconds": total_time,
        "npm_results": npm_results,
        "community_results": community_results,
        "config_file": str(config_path),
        "summary": {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful/total*100 if total > 0 else 0
        }
    }
    
    with open("downloads/download_status.json", 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"📊 Status saved: downloads/download_status.json")

if __name__ == "__main__":
    main()