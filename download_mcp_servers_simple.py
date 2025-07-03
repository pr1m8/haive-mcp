#!/usr/bin/env python3
"""
Simple MCP server downloader - downloads official and popular servers.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# List of known official/popular MCP servers to install
OFFICIAL_SERVERS = [
    "@modelcontextprotocol/server-filesystem",
    "@modelcontextprotocol/server-github", 
    "@modelcontextprotocol/server-gitlab",
    "@modelcontextprotocol/server-google-drive",
    "@modelcontextprotocol/server-slack",
    "@modelcontextprotocol/server-postgres",
    "@modelcontextprotocol/server-sqlite",
    "@modelcontextprotocol/server-puppeteer",
    "@modelcontextprotocol/server-brave-search",
    "@modelcontextprotocol/server-google-maps",
]

# Additional popular community servers
COMMUNITY_SERVERS = [
    "mcp-server-fetch",
    "mcp-server-shell",
    "mcp-server-git",
    "mcp-server-docker",
    "mcp-server-kubernetes",
    "mcp-server-aws",
    "mcp-server-azure",
    "mcp-server-gcp",
]


def install_npm_package(package: str) -> bool:
    """Install a single npm package globally."""
    try:
        logger.info(f"Installing: {package}")
        cmd = ["npm", "install", "-g", package]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            logger.info(f"✓ Success: {package}")
            return True
        else:
            # Try with npx if global install fails
            logger.warning(f"Global install failed, trying npx: {package}")
            test_cmd = ["npx", "-y", package, "--help"]
            test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
            if test_result.returncode == 0:
                logger.info(f"✓ Works with npx: {package}")
                return True
            else:
                logger.error(f"✗ Failed: {package}")
                if result.stderr:
                    logger.error(f"  Error: {result.stderr[:200]}")
                return False
    except Exception as e:
        logger.error(f"✗ Exception installing {package}: {e}")
        return False


def generate_config(installed_servers: List[str]):
    """Generate MCP configuration file."""
    config_dir = Path.home() / ".mcp"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "servers_config.json"
    
    config = {"servers": {}}
    
    for server in installed_servers:
        # Create a simple name from the package
        name = server.replace("@", "").replace("/", "_").replace("-", "_")
        
        config["servers"][name] = {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", server],
            "description": f"MCP Server: {server}"
        }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"\n✓ Configuration saved to: {config_file}")
    logger.info(f"  You can use this configuration with your MCP client")


def main():
    """Main installation process."""
    logger.info("MCP Server Installer - Simple Version")
    logger.info("=" * 60)
    
    # Check if npm is available
    try:
        subprocess.run(["npm", "--version"], capture_output=True, check=True)
    except:
        logger.error("npm is not installed. Please install Node.js and npm first.")
        sys.exit(1)
    
    all_servers = OFFICIAL_SERVERS + COMMUNITY_SERVERS
    installed = []
    failed = []
    
    logger.info(f"Will attempt to install {len(all_servers)} MCP servers\n")
    
    for server in all_servers:
        if install_npm_package(server):
            installed.append(server)
        else:
            failed.append(server)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("INSTALLATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✓ Successfully installed: {len(installed)}")
    logger.info(f"✗ Failed: {len(failed)}")
    
    if installed:
        logger.info("\nInstalled servers:")
        for server in installed:
            logger.info(f"  ✓ {server}")
    
    if failed:
        logger.info("\nFailed servers (may not exist or require different installation):")
        for server in failed:
            logger.info(f"  ✗ {server}")
    
    # Generate configuration
    if installed:
        generate_config(installed)
    
    logger.info("\nTo use these servers:")
    logger.info("1. Configure your MCP client with the generated config")
    logger.info("2. Or run directly with: npx -y <server-name>")


if __name__ == "__main__":
    main()