#!/usr/bin/env python3
"""Bulk installer for MCP servers.

This module provides utilities to install multiple MCP servers based on
various criteria like star count, category, or specific lists.
"""

import subprocess
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Callable
from datetime import datetime
import logging
import asyncio
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)


class MCPBulkInstaller:
    """Install multiple MCP servers systematically.
    
    This class provides methods to:
    - Install servers by star count threshold
    - Install servers by category
    - Track installation success/failure
    - Generate installation reports
    
    Attributes:
        data_path: Path to the CSV file with server data
        install_log: List of installation attempts and results
        installed_servers: Set of successfully installed server names
    
    Example:
        >>> installer = MCPBulkInstaller()
        >>> installer.install_by_stars(min_stars=1000)
        >>> installer.save_install_report()
    """
    
    def __init__(self, data_path: str = "mcp_servers_data.csv", dry_run: bool = False):
        """Initialize the bulk installer.
        
        Args:
            data_path: Path to CSV file containing MCP server data
            dry_run: If True, only simulate installations without executing commands
        """
        self.data_path = Path(data_path)
        self.dry_run = dry_run
        self.install_log: List[Dict] = []
        self.installed_servers: set = set()
        
        # Load server data
        if self.data_path.exists():
            self.df = pd.read_csv(self.data_path)
            self.servers_with_stars = self.df[self.df['stars'] > 0]
            console.print(f"[green]Loaded {len(self.df)} servers, {len(self.servers_with_stars)} with stars[/green]")
        else:
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
    
    def install_by_stars(self, min_stars: int = 100, max_servers: Optional[int] = None) -> Dict:
        """Install servers with minimum star count.
        
        Args:
            min_stars: Minimum number of stars required
            max_servers: Maximum number of servers to install (None for all)
            
        Returns:
            Summary dict with installation statistics
        """
        # Filter servers by star count
        eligible_servers = self.servers_with_stars[
            self.servers_with_stars['stars'] >= min_stars
        ].sort_values('stars', ascending=False)
        
        if max_servers:
            eligible_servers = eligible_servers.head(max_servers)
        
        console.print(f"\n[bold]Installing {len(eligible_servers)} servers with {min_stars}+ stars[/bold]")
        
        # Install servers with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Installing servers...", total=len(eligible_servers))
            
            for _, server in eligible_servers.iterrows():
                self._install_server(server)
                progress.update(task, advance=1)
        
        return self._get_summary()
    
    def install_by_category(self, category: str) -> Dict:
        """Install all servers in a specific category.
        
        Args:
            category: Category name (e.g., 'ai_ml', 'database', 'utility')
            
        Returns:
            Summary dict with installation statistics
        """
        category_servers = self.servers_with_stars[
            self.servers_with_stars['category'] == category
        ].sort_values('stars', ascending=False)
        
        console.print(f"\n[bold]Installing {len(category_servers)} servers in category: {category}[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"Installing {category} servers...", total=len(category_servers))
            
            for _, server in category_servers.iterrows():
                self._install_server(server)
                progress.update(task, advance=1)
        
        return self._get_summary()
    
    def install_top_n(self, n: int = 10) -> Dict:
        """Install top N servers by star count.
        
        Args:
            n: Number of top servers to install
            
        Returns:
            Summary dict with installation statistics
        """
        top_servers = self.servers_with_stars.nlargest(n, 'stars')
        
        console.print(f"\n[bold]Installing top {n} servers by stars[/bold]")
        
        # Display table of servers to install
        table = Table(title=f"Top {n} MCP Servers")
        table.add_column("Rank", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Stars", style="green")
        table.add_column("Category", style="yellow")
        
        for i, (_, server) in enumerate(top_servers.iterrows(), 1):
            table.add_row(
                str(i),
                server['name'][:50],
                f"{int(server['stars']):,}",
                server['category']
            )
        
        console.print(table)
        
        # Install with confirmation
        if console.input("\n[yellow]Proceed with installation? (y/n): [/yellow]").lower() == 'y':
            for _, server in top_servers.iterrows():
                self._install_server(server)
        
        return self._get_summary()
    
    def _generate_install_command(self, server: pd.Series) -> Optional[str]:
        """Generate installation command based on server metadata.
        
        Args:
            server: Server data from dataframe
            
        Returns:
            Installation command string or None if not possible
        """
        name = server['name']
        repository_url = server.get('repository_url', '')
        repository_owner = server.get('repository_owner', '')
        repository_name = server.get('repository_name', '')
        language = server.get('language', '')
        
        # Check for existing install_command (handle NaN properly)
        install_cmd = server.get('install_command')
        if pd.notna(install_cmd) and install_cmd.strip():
            return install_cmd.strip()
        
        # Check for npm_package (handle NaN properly)
        npm_package = server.get('npm_package')
        if pd.notna(npm_package) and npm_package.strip():
            return f"npm install -g {npm_package.strip()}"
        
        # Try to infer installation method from repository info
        if repository_url and 'github.com' in repository_url:
            # Official MCP servers pattern
            if repository_owner == 'modelcontextprotocol' and repository_name.startswith('server-'):
                # Official MCP server - use npx
                return f"npx -y @modelcontextprotocol/{repository_name} --help"
            
            # Check if it's a known MCP server pattern
            if 'mcp-server' in repository_name or 'server-' in repository_name:
                # Try npm first for JavaScript/TypeScript projects
                if language in ['JavaScript', 'TypeScript']:
                    # Assume it might be published to npm
                    if '/' in name:  # org/repo format
                        return f"npx -y {name}"
                    else:
                        return f"npx -y {repository_name}"
                
                # For Python projects, try git clone
                elif language == 'Python':
                    return f"git clone {repository_url} && cd {repository_name} && pip install -e ."
                
                # For Go projects
                elif language == 'Go':
                    return f"go install {repository_url.replace('https://github.com/', '')}@latest"
            
            # Generic git clone fallback for any repository
            return f"git clone {repository_url}"
        
        # No installation method found
        return None
    
    def _install_server(self, server: pd.Series) -> bool:
        """Install a single server.
        
        Args:
            server: Server data from dataframe
            
        Returns:
            True if installation succeeded, False otherwise
        """
        name = server['name']
        
        # Skip if already installed
        if name in self.installed_servers:
            console.print(f"[dim]Skipping {name} (already installed)[/dim]")
            return True
        
        # Generate installation command
        cmd = self._generate_install_command(server)
        if not cmd:
            console.print(f"[red]No installation method available for {name}[/red]")
            self._log_install(name, 'error', error='No installation method available')
            return False
        
        # Execute installation
        if self.dry_run:
            console.print(f"[yellow][DRY RUN] Would install {name}[/yellow]")
            console.print(f"[dim]Command: {cmd}[/dim]")
            self.installed_servers.add(name)
            self._log_install(name, 'success', command=cmd)
            return True
        
        console.print(f"[cyan]Installing {name}...[/cyan]")
        console.print(f"[dim]Command: {cmd}[/dim]")
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                console.print(f"[green]✓ Successfully installed {name}[/green]")
                self.installed_servers.add(name)
                self._log_install(name, 'success', command=cmd)
                return True
            else:
                console.print(f"[red]✗ Failed to install {name}[/red]")
                console.print(f"[dim]Error: {result.stderr}[/dim]")
                self._log_install(name, 'failed', command=cmd, error=result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            console.print(f"[red]✗ Installation timeout for {name}[/red]")
            self._log_install(name, 'timeout', command=cmd)
            return False
        except Exception as e:
            console.print(f"[red]✗ Error installing {name}: {e}[/red]")
            self._log_install(name, 'error', command=cmd, error=str(e))
            return False
    
    def _log_install(self, name: str, status: str, command: str = '', error: str = ''):
        """Log installation attempt.
        
        Args:
            name: Server name
            status: Installation status (success, failed, timeout, error)
            command: Installation command used
            error: Error message if failed
        """
        self.install_log.append({
            'timestamp': datetime.now().isoformat(),
            'name': name,
            'status': status,
            'command': command,
            'error': error
        })
    
    def _get_summary(self) -> Dict:
        """Get installation summary statistics.
        
        Returns:
            Dict with success/failure counts and details
        """
        total = len(self.install_log)
        success = len([l for l in self.install_log if l['status'] == 'success'])
        failed = len([l for l in self.install_log if l['status'] == 'failed'])
        timeout = len([l for l in self.install_log if l['status'] == 'timeout'])
        error = len([l for l in self.install_log if l['status'] == 'error'])
        
        return {
            'total_attempts': total,
            'successful': success,
            'failed': failed,
            'timeout': timeout,
            'error': error,
            'success_rate': (success / total * 100) if total > 0 else 0
        }
    
    def save_install_report(self, filename: str = None):
        """Save detailed installation report.
        
        Args:
            filename: Output filename (defaults to timestamp)
        """
        if not filename:
            filename = f"mcp_install_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'summary': self._get_summary(),
            'installed_servers': list(self.installed_servers),
            'install_log': self.install_log,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        console.print(f"\n[green]Installation report saved to: {filename}[/green]")
    
    def show_summary(self):
        """Display installation summary in console."""
        summary = self._get_summary()
        
        table = Table(title="Installation Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Attempts", str(summary['total_attempts']))
        table.add_row("Successful", str(summary['successful']))
        table.add_row("Failed", str(summary['failed']))
        table.add_row("Timeout", str(summary['timeout']))
        table.add_row("Errors", str(summary['error']))
        table.add_row("Success Rate", f"{summary['success_rate']:.1f}%")
        
        console.print(table)
        
        # Show failed servers
        if summary['failed'] > 0 or summary['timeout'] > 0 or summary['error'] > 0:
            console.print("\n[red]Failed installations:[/red]")
            for log in self.install_log:
                if log['status'] != 'success':
                    console.print(f"  - {log['name']}: {log['status']}")
                    if log['error']:
                        console.print(f"    [dim]{log['error'][:100]}...[/dim]")


def main():
    """Main entry point for bulk installer CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk install MCP servers")
    parser.add_argument(
        "--min-stars",
        type=int,
        default=100,
        help="Minimum star count (default: 100)"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        help="Install top N servers by stars"
    )
    parser.add_argument(
        "--category",
        help="Install all servers in category"
    )
    parser.add_argument(
        "--data-file",
        default="mcp_servers_data.csv",
        help="Path to CSV data file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be installed without installing"
    )
    
    args = parser.parse_args()
    
    try:
        installer = MCPBulkInstaller(args.data_file, dry_run=args.dry_run)
        
        if args.top_n:
            installer.install_top_n(args.top_n)
        elif args.category:
            installer.install_by_category(args.category)
        else:
            installer.install_by_stars(min_stars=args.min_stars)
        
        installer.show_summary()
        installer.save_install_report()
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())