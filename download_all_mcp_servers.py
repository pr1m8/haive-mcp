#!/usr/bin/env python3
"""
Download and install all available MCP servers programmatically.

This script reads MCP server information from the agent_resources directory
and attempts to install all servers using the appropriate package managers.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPServerInstaller:
    """Install MCP servers from various sources."""
    
    def __init__(self, install_dir: Path = None):
        self.install_dir = install_dir or Path.home() / ".mcp" / "servers"
        self.install_dir.mkdir(parents=True, exist_ok=True)
        
        # Load server data
        self.servers_file = Path(__file__).parent / "agent_resources" / "mcp_servers" / "all_mcp_documents.json"
        self.servers = self._load_servers()
        
        # Track installation results
        self.installed = []
        self.failed = []
        self.skipped = []
        
    def _load_servers(self) -> List[Dict]:
        """Load server information from JSON file."""
        if not self.servers_file.exists():
            logger.error(f"Server file not found: {self.servers_file}")
            return []
            
        try:
            with open(self.servers_file, 'r') as f:
                data = json.load(f)
                # The file is a list, not a dict with 'documents' key
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Failed to load servers: {e}")
            return []
    
    def _detect_install_method(self, server: Dict) -> Optional[str]:
        """Detect the installation method for a server."""
        metadata = server.get('metadata', {})
        
        # Check for explicit package info
        if 'npmPackage' in metadata:
            return 'npm'
        elif 'pypiPackage' in metadata:
            return 'pip'
        elif 'cargoPackage' in metadata:
            return 'cargo'
        elif 'goModule' in metadata:
            return 'go'
        
        # Infer from language
        language = metadata.get('language', '').lower()
        if language in ['typescript', 'javascript', 'node', 'nodejs']:
            return 'npm'
        elif language == 'python':
            return 'pip'
        elif language == 'rust':
            return 'cargo'
        elif language == 'go':
            return 'go'
        
        # Default to git clone
        return 'git'
    
    def _install_npm_server(self, server: Dict) -> bool:
        """Install an npm-based MCP server."""
        name = server.get('title', '').strip()
        npm_package = server.get('metadata', {}).get('npmPackage', name)
        
        if not npm_package:
            # Try to construct from repository name
            repo = server.get('metadata', {}).get('githubUrl', '')
            if 'github.com' in repo:
                # Extract owner/repo format
                parts = repo.rstrip('/').split('/')
                if len(parts) >= 2:
                    npm_package = f"@{parts[-2]}/{parts[-1]}"
        
        try:
            logger.info(f"Installing npm package: {npm_package}")
            cmd = ['npm', 'install', '-g', npm_package]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info(f"✓ Successfully installed: {npm_package}")
                return True
            else:
                logger.warning(f"Failed to install {npm_package}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout installing {npm_package}")
            return False
        except Exception as e:
            logger.error(f"Error installing {npm_package}: {e}")
            return False
    
    def _install_pip_server(self, server: Dict) -> bool:
        """Install a pip-based MCP server."""
        name = server.get('title', '').strip()
        pip_package = server.get('metadata', {}).get('pypiPackage', name)
        
        try:
            logger.info(f"Installing pip package: {pip_package}")
            cmd = [sys.executable, '-m', 'pip', 'install', pip_package]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info(f"✓ Successfully installed: {pip_package}")
                return True
            else:
                logger.warning(f"Failed to install {pip_package}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing {pip_package}: {e}")
            return False
    
    def _install_git_server(self, server: Dict) -> bool:
        """Clone and setup a git-based MCP server."""
        repo_url = server.get('metadata', {}).get('githubUrl', '')
        if not repo_url:
            return False
            
        name = repo_url.rstrip('/').split('/')[-1]
        install_path = self.install_dir / name
        
        try:
            if install_path.exists():
                logger.info(f"Server already cloned: {name}")
                return True
                
            logger.info(f"Cloning repository: {repo_url}")
            cmd = ['git', 'clone', repo_url, str(install_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                logger.info(f"✓ Successfully cloned: {name}")
                
                # Try to install dependencies
                if (install_path / 'package.json').exists():
                    subprocess.run(['npm', 'install'], cwd=install_path, capture_output=True)
                elif (install_path / 'requirements.txt').exists():
                    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                                 cwd=install_path, capture_output=True)
                
                return True
            else:
                logger.warning(f"Failed to clone {name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error cloning {name}: {e}")
            return False
    
    def install_server(self, server: Dict) -> bool:
        """Install a single MCP server."""
        name = server.get('title', 'Unknown')
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {name}")
        
        # Skip if marked as not installable
        if server.get('metadata', {}).get('notInstallable'):
            logger.info(f"⊘ Skipping {name} (marked as not installable)")
            self.skipped.append(name)
            return False
        
        # Detect installation method
        method = self._detect_install_method(server)
        logger.info(f"Installation method: {method}")
        
        # Install based on method
        success = False
        if method == 'npm':
            success = self._install_npm_server(server)
        elif method == 'pip':
            success = self._install_pip_server(server)
        elif method == 'git':
            success = self._install_git_server(server)
        else:
            logger.warning(f"⊘ Unsupported installation method: {method}")
            self.skipped.append(name)
            return False
        
        # Track results
        if success:
            self.installed.append(name)
        else:
            self.failed.append(name)
            
        return success
    
    def install_all(self, max_workers: int = 5, limit: Optional[int] = None):
        """Install all MCP servers with parallel execution."""
        servers_to_install = self.servers[:limit] if limit else self.servers
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting installation of {len(servers_to_install)} MCP servers")
        logger.info(f"Install directory: {self.install_dir}")
        logger.info(f"{'='*60}\n")
        
        # Install in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(servers_to_install), batch_size):
            batch = servers_to_install[i:i+batch_size]
            logger.info(f"\nProcessing batch {i//batch_size + 1}/{(len(servers_to_install)-1)//batch_size + 1}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(self.install_server, server): server 
                          for server in batch}
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        server = futures[future]
                        logger.error(f"Exception installing {server.get('title')}: {e}")
            
            # Small delay between batches
            time.sleep(2)
        
        # Print summary
        self._print_summary()
        
        # Generate configuration
        self._generate_config()
    
    def _print_summary(self):
        """Print installation summary."""
        total = len(self.installed) + len(self.failed) + len(self.skipped)
        
        logger.info(f"\n{'='*60}")
        logger.info("INSTALLATION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total servers processed: {total}")
        logger.info(f"✓ Successfully installed: {len(self.installed)}")
        logger.info(f"✗ Failed installations: {len(self.failed)}")
        logger.info(f"⊘ Skipped: {len(self.skipped)}")
        
        if self.failed:
            logger.info("\nFailed servers:")
            for server in self.failed[:10]:
                logger.info(f"  - {server}")
            if len(self.failed) > 10:
                logger.info(f"  ... and {len(self.failed) - 10} more")
    
    def _generate_config(self):
        """Generate MCP configuration for installed servers."""
        config_file = self.install_dir / "mcp_servers_config.json"
        
        config = {"servers": {}}
        
        for server_data in self.servers:
            name = server_data.get('title', '')
            if name in self.installed:
                # Create basic configuration
                server_name = name.replace('/', '_').replace('@', '')
                config["servers"][server_name] = {
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", name],
                    "description": server_data.get('page_content', '')[:200],
                    "repository": server_data.get('metadata', {}).get('githubUrl', '')
                }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"\n✓ Configuration saved to: {config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Install all MCP servers")
    parser.add_argument('--install-dir', type=Path, 
                       help='Installation directory (default: ~/.mcp/servers)')
    parser.add_argument('--workers', type=int, default=5,
                       help='Number of parallel workers (default: 5)')
    parser.add_argument('--limit', type=int,
                       help='Limit number of servers to install (for testing)')
    
    args = parser.parse_args()
    
    installer = MCPServerInstaller(install_dir=args.install_dir)
    
    try:
        installer.install_all(max_workers=args.workers, limit=args.limit)
    except KeyboardInterrupt:
        logger.info("\n\nInstallation interrupted by user")
        installer._print_summary()


if __name__ == "__main__":
    main()