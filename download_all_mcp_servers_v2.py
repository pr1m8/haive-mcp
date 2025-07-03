#!/usr/bin/env python3
"""
Download and install all available MCP servers programmatically.
Version 2 - Updated to work with the actual JSON structure.
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
                # The file is a list directly
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Failed to load servers: {e}")
            return []
    
    def _detect_install_method(self, server: Dict) -> Optional[str]:
        """Detect the installation method for a server."""
        metadata = server.get('metadata', {})
        
        # Check for explicit package info
        if metadata.get('npmPackage'):
            return 'npm'
        elif metadata.get('pypiPackage'):
            return 'pip'
        elif metadata.get('cargoPackage'):
            return 'cargo'
        elif metadata.get('goModule'):
            return 'go'
        
        # Infer from languages list
        languages = metadata.get('languages', [])
        if languages:
            language = languages[0].lower()
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
        metadata = server.get('metadata', {})
        name = metadata.get('name', '').strip()
        npm_package = metadata.get('npmPackage', '')
        
        if not npm_package:
            # Try to construct from repository name
            # For modelcontextprotocol servers, they often use @modelcontextprotocol/server-*
            if 'modelcontextprotocol' in name:
                parts = name.split('/')
                if len(parts) >= 2:
                    npm_package = f"@modelcontextprotocol/{parts[-1]}"
            else:
                # General pattern: owner/repo becomes @owner/repo
                npm_package = f"@{name}"
        
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
        metadata = server.get('metadata', {})
        name = metadata.get('name', '').strip()
        pip_package = metadata.get('pypiPackage', name.split('/')[-1])
        
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
        metadata = server.get('metadata', {})
        repo_url = metadata.get('repo_url', '')
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
        metadata = server.get('metadata', {})
        name = metadata.get('name', 'Unknown')
        repo_url = metadata.get('repo_url', '')
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {name}")
        
        # Skip if no repository URL
        if not repo_url:
            logger.info(f"⊘ Skipping {name} (no repository URL)")
            self.skipped.append(name)
            return False
        
        # Skip if it's marked as Other/unknown
        if metadata.get('category') == 'Other' and metadata.get('languages') == ['Other']:
            logger.info(f"⊘ Skipping {name} (unknown language/category)")
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
        # Filter to only servers with known languages
        valid_servers = [s for s in self.servers 
                        if s.get('metadata', {}).get('languages') 
                        and s['metadata']['languages'][0] != 'Other']
        
        servers_to_install = valid_servers[:limit] if limit else valid_servers
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting installation of {len(servers_to_install)} MCP servers")
        logger.info(f"(Filtered from {len(self.servers)} total servers)")
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
                        logger.error(f"Exception installing {server.get('metadata', {}).get('name')}: {e}")
            
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
        
        if self.installed:
            logger.info("\nSuccessfully installed:")
            for server in self.installed[:10]:
                logger.info(f"  ✓ {server}")
            if len(self.installed) > 10:
                logger.info(f"  ... and {len(self.installed) - 10} more")
        
        if self.failed:
            logger.info("\nFailed servers:")
            for server in self.failed[:10]:
                logger.info(f"  ✗ {server}")
            if len(self.failed) > 10:
                logger.info(f"  ... and {len(self.failed) - 10} more")
    
    def _generate_config(self):
        """Generate MCP configuration for installed servers."""
        config_file = self.install_dir / "mcp_servers_config.json"
        
        config = {"servers": {}}
        
        for server_data in self.servers:
            metadata = server_data.get('metadata', {})
            name = metadata.get('name', '')
            if name in self.installed:
                # Create basic configuration
                server_name = name.replace('/', '_').replace('@', '')
                config["servers"][server_name] = {
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", name],
                    "description": metadata.get('description', '')[:200],
                    "repository": metadata.get('repo_url', ''),
                    "category": metadata.get('category', ''),
                    "languages": metadata.get('languages', [])
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