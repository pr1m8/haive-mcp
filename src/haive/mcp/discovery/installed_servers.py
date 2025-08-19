#!/usr/bin/env python3
"""Discover and manage installed MCP servers.

This module provides utilities to find, check, and manage MCP servers
that are already installed on the system.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Set
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPServerDiscovery:
    """Discover installed MCP servers on the system.
    
    This class provides methods to:
    - Find npm-installed MCP servers
    - Check Python-based MCP servers
    - Locate configuration files
    - Verify server functionality
    
    Example:
        >>> discovery = MCPServerDiscovery()
        >>> installed = discovery.find_all_installed()
        >>> print(f"Found {len(installed)} installed servers")
    """
    
    def __init__(self):
        """Initialize the discovery system."""
        self.npm_servers: List[Dict] = []
        self.pip_servers: List[Dict] = []
        self.config_servers: List[Dict] = []
        self.discovered_servers: Set[str] = set()
        
    def find_all_installed(self) -> List[Dict]:
        """Find all installed MCP servers.
        
        Returns:
            List of dicts with server information
        """
        servers = []
        
        # Find npm-based servers
        npm_servers = self.find_npm_servers()
        servers.extend(npm_servers)
        
        # Find pip-based servers
        pip_servers = self.find_pip_servers()
        servers.extend(pip_servers)
        
        # Find servers from config files
        config_servers = self.find_config_servers()
        servers.extend(config_servers)
        
        # Remove duplicates
        unique_servers = {}
        for server in servers:
            name = server.get('name', server.get('package', 'unknown'))
            if name not in unique_servers:
                unique_servers[name] = server
        
        return list(unique_servers.values())
    
    def find_npm_servers(self) -> List[Dict]:
        """Find npm-installed MCP servers.
        
        Returns:
            List of npm MCP servers with metadata
        """
        servers = []
        
        try:
            # Get global npm packages
            result = subprocess.run(
                ["npm", "list", "-g", "--json", "--depth=0"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                npm_data = json.loads(result.stdout)
                dependencies = npm_data.get('dependencies', {})
                
                # Look for MCP servers
                for package, info in dependencies.items():
                    if 'mcp' in package.lower() or '@modelcontextprotocol' in package:
                        server_info = {
                            'name': package,
                            'version': info.get('version', 'unknown'),
                            'type': 'npm',
                            'global': True,
                            'path': info.get('resolved', ''),
                            'discovered_at': datetime.now().isoformat()
                        }
                        servers.append(server_info)
                        self.npm_servers.append(server_info)
            
            # Also check local npm packages if in a project
            if Path("package.json").exists():
                local_result = subprocess.run(
                    ["npm", "list", "--json", "--depth=0"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if local_result.returncode == 0:
                    local_data = json.loads(local_result.stdout)
                    local_deps = local_data.get('dependencies', {})
                    
                    for package, info in local_deps.items():
                        if 'mcp' in package.lower() or '@modelcontextprotocol' in package:
                            server_info = {
                                'name': package,
                                'version': info.get('version', 'unknown'),
                                'type': 'npm',
                                'global': False,
                                'path': info.get('resolved', ''),
                                'discovered_at': datetime.now().isoformat()
                            }
                            servers.append(server_info)
                    
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error finding npm servers: {e}")
        
        return servers
    
    def find_pip_servers(self) -> List[Dict]:
        """Find pip-installed MCP servers.
        
        Returns:
            List of Python MCP servers with metadata
        """
        servers = []
        
        try:
            # Get pip packages
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                
                # Look for MCP-related packages
                for package in packages:
                    name = package.get('name', '')
                    if 'mcp' in name.lower() or 'model-context' in name.lower():
                        server_info = {
                            'name': name,
                            'version': package.get('version', 'unknown'),
                            'type': 'pip',
                            'discovered_at': datetime.now().isoformat()
                        }
                        servers.append(server_info)
                        self.pip_servers.append(server_info)
                        
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error finding pip servers: {e}")
        
        return servers
    
    def find_config_servers(self) -> List[Dict]:
        """Find servers from configuration files.
        
        Returns:
            List of configured servers with metadata
        """
        servers = []
        
        # Common config locations
        config_paths = [
            Path.home() / ".mcp" / "servers.json",
            Path.home() / ".config" / "mcp" / "servers.json",
            Path("/etc/mcp/servers.json"),
            Path("./mcp_config.json"),
            Path("./.mcp/config.json")
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                    
                    # Extract server configurations
                    if 'servers' in config:
                        for server_name, server_config in config['servers'].items():
                            server_info = {
                                'name': server_name,
                                'type': 'config',
                                'config_path': str(config_path),
                                'command': server_config.get('command', ''),
                                'args': server_config.get('args', []),
                                'discovered_at': datetime.now().isoformat()
                            }
                            servers.append(server_info)
                            self.config_servers.append(server_info)
                            
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Error reading config {config_path}: {e}")
        
        return servers
    
    def check_server_availability(self, server_name: str) -> bool:
        """Check if a specific server is available.
        
        Args:
            server_name: Name of the server to check
            
        Returns:
            True if server is installed and available
        """
        # Check npm global
        try:
            result = subprocess.run(
                ["npm", "list", "-g", server_name],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return True
        except:
            pass
        
        # Check pip
        try:
            result = subprocess.run(
                ["pip", "show", server_name],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return True
        except:
            pass
        
        # Check if executable exists
        try:
            result = subprocess.run(
                ["which", server_name],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except:
            pass
        
        return False
    
    def get_server_info(self, server_name: str) -> Optional[Dict]:
        """Get detailed information about an installed server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            Dict with server details or None if not found
        """
        # Try npm first
        try:
            result = subprocess.run(
                ["npm", "list", "-g", server_name, "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                deps = data.get('dependencies', {})
                if server_name in deps:
                    return {
                        'name': server_name,
                        'type': 'npm',
                        'version': deps[server_name].get('version'),
                        'path': deps[server_name].get('resolved'),
                        'info': deps[server_name]
                    }
        except:
            pass
        
        # Try pip
        try:
            result = subprocess.run(
                ["pip", "show", server_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                info = {}
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip().lower()] = value.strip()
                
                return {
                    'name': server_name,
                    'type': 'pip',
                    'version': info.get('version'),
                    'path': info.get('location'),
                    'info': info
                }
        except:
            pass
        
        return None
    
    def export_installed_list(self, filename: str = "installed_mcp_servers.json"):
        """Export list of installed servers to file.
        
        Args:
            filename: Output filename
        """
        installed = self.find_all_installed()
        
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_servers': len(installed),
            'npm_servers': len(self.npm_servers),
            'pip_servers': len(self.pip_servers),
            'config_servers': len(self.config_servers),
            'servers': installed
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(installed)} servers to {filename}")


def main():
    """Main entry point for CLI usage."""
    import argparse
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    parser = argparse.ArgumentParser(description="Discover installed MCP servers")
    parser.add_argument(
        "--export",
        help="Export to JSON file"
    )
    parser.add_argument(
        "--check",
        help="Check if specific server is installed"
    )
    parser.add_argument(
        "--info",
        help="Get info about specific server"
    )
    
    args = parser.parse_args()
    
    discovery = MCPServerDiscovery()
    
    if args.check:
        available = discovery.check_server_availability(args.check)
        if available:
            console.print(f"[green]✓ {args.check} is installed[/green]")
        else:
            console.print(f"[red]✗ {args.check} is not installed[/red]")
        return
    
    if args.info:
        info = discovery.get_server_info(args.info)
        if info:
            console.print(f"\n[bold]Server: {info['name']}[/bold]")
            console.print(f"Type: {info['type']}")
            console.print(f"Version: {info.get('version', 'unknown')}")
            if info.get('path'):
                console.print(f"Path: {info['path']}")
        else:
            console.print(f"[red]Server {args.info} not found[/red]")
        return
    
    # Find all installed servers
    servers = discovery.find_all_installed()
    
    # Display results
    table = Table(title="Installed MCP Servers")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Version", style="green")
    table.add_column("Global", style="yellow")
    
    for server in servers:
        table.add_row(
            server['name'],
            server['type'],
            server.get('version', 'unknown'),
            "Yes" if server.get('global', True) else "No"
        )
    
    console.print(table)
    console.print(f"\n[bold]Total: {len(servers)} servers found[/bold]")
    
    if args.export:
        discovery.export_installed_list(args.export)
        console.print(f"\n[green]Exported to {args.export}[/green]")


if __name__ == "__main__":
    main()