#!/usr/bin/env python3
"""
List and browse all available MCP servers with filtering and export options.

This script provides a comprehensive way to explore the MCP server ecosystem
without needing an agent.
"""

import json
import csv
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()


class MCPServerBrowser:
    """Browse and export MCP server information."""
    
    def __init__(self):
        self.servers_file = Path(__file__).parent / "agent_resources" / "mcp_servers" / "all_mcp_documents.json"
        # Debug output
        print(f"[DEBUG] Looking for file at: {self.servers_file}")
        print(f"[DEBUG] File exists: {self.servers_file.exists()}")
        self.servers = self._load_servers()
        
    def _load_servers(self) -> List[Dict]:
        """Load server information from JSON file."""
        if not self.servers_file.exists():
            console.print(f"[red]Server file not found: {self.servers_file}[/red]")
            return []
            
        try:
            with open(self.servers_file, 'r') as f:
                data = json.load(f)
                # Simply return the data as-is if it loads successfully
                print(f"[DEBUG] Loaded data successfully, type: {type(data).__name__}")
                if hasattr(data, '__len__'):
                    print(f"[DEBUG] Data has {len(data)} items")
                return data
        except Exception as e:
            console.print(f"[red]Failed to load servers: {e}[/red]")
            return []
    
    def list_servers(self, category: Optional[str] = None, 
                    language: Optional[str] = None,
                    limit: Optional[int] = None) -> List[Dict]:
        """List servers with optional filtering."""
        filtered = self.servers
        
        if category:
            filtered = [s for s in filtered 
                       if category.lower() in s.get('metadata', {}).get('category', '').lower()]
        
        if language:
            filtered = [s for s in filtered 
                       if language.lower() in s.get('metadata', {}).get('language', '').lower()]
        
        if limit:
            filtered = filtered[:limit]
            
        return filtered
    
    def search_servers(self, query: str) -> List[Dict]:
        """Search servers by name, description, or metadata."""
        query_lower = query.lower()
        results = []
        
        for server in self.servers:
            # Search in title
            if query_lower in server.get('title', '').lower():
                results.append(server)
                continue
                
            # Search in content
            if query_lower in server.get('page_content', '').lower():
                results.append(server)
                continue
                
            # Search in metadata
            metadata_str = json.dumps(server.get('metadata', {})).lower()
            if query_lower in metadata_str:
                results.append(server)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get statistics about the MCP ecosystem."""
        stats = {
            'total_servers': len(self.servers),
            'by_language': defaultdict(int),
            'by_category': defaultdict(int),
            'official_count': 0,
            'with_npm': 0,
            'with_pip': 0,
            'with_github': 0
        }
        
        for server in self.servers:
            metadata = server.get('metadata', {})
            
            # Language stats
            language = metadata.get('language', 'unknown')
            stats['by_language'][language] += 1
            
            # Category stats
            category = metadata.get('category', 'uncategorized')
            stats['by_category'][category] += 1
            
            # Official servers
            if metadata.get('isOfficial'):
                stats['official_count'] += 1
            
            # Package availability
            if metadata.get('npmPackage'):
                stats['with_npm'] += 1
            if metadata.get('pypiPackage'):
                stats['with_pip'] += 1
            if metadata.get('githubUrl'):
                stats['with_github'] += 1
        
        return stats
    
    def export_to_csv(self, filename: str, servers: Optional[List[Dict]] = None):
        """Export servers to CSV format."""
        servers = servers or self.servers
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title', 'language', 'category', 'github_url', 
                         'npm_package', 'description']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for server in servers:
                metadata = server.get('metadata', {})
                writer.writerow({
                    'title': server.get('title', ''),
                    'language': metadata.get('language', ''),
                    'category': metadata.get('category', ''),
                    'github_url': metadata.get('githubUrl', ''),
                    'npm_package': metadata.get('npmPackage', ''),
                    'description': server.get('page_content', '')[:200]
                })
        
        console.print(f"[green]✓ Exported {len(servers)} servers to {filename}[/green]")
    
    def export_to_json(self, filename: str, servers: Optional[List[Dict]] = None):
        """Export servers to JSON format."""
        servers = servers or self.servers
        
        export_data = []
        for server in servers:
            export_data.append({
                'name': server.get('metadata', {}).get('name', ''),
                'metadata': server.get('metadata', {}),
                'description': server.get('metadata', {}).get('description', '')
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✓ Exported {len(servers)} servers to {filename}[/green]")
    
    def export_to_yaml(self, filename: str, servers: Optional[List[Dict]] = None):
        """Export servers to YAML format."""
        servers = servers or self.servers
        
        export_data = []
        for server in servers:
            export_data.append({
                'name': server.get('metadata', {}).get('name', ''),
                'metadata': server.get('metadata', {}),
                'description': server.get('metadata', {}).get('description', '')
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)
        
        console.print(f"[green]✓ Exported {len(servers)} servers to {filename}[/green]")
    
    def display_server_table(self, servers: List[Dict], title: str = "MCP Servers"):
        """Display servers in a rich table format."""
        table = Table(title=title, show_lines=True)
        
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Language", style="magenta")
        table.add_column("Category", style="yellow")
        table.add_column("Description", style="green")
        
        for server in servers:
            metadata = server.get('metadata', {})
            description = server.get('page_content', '')[:60] + "..."
            
            table.add_row(
                server.get('title', 'Unknown'),
                metadata.get('language', 'Unknown'),
                metadata.get('category', 'Uncategorized'),
                description
            )
        
        console.print(table)
    
    def display_server_details(self, server_name: str):
        """Display detailed information about a specific server."""
        server = None
        for s in self.servers:
            if s.get('title', '').lower() == server_name.lower():
                server = s
                break
        
        if not server:
            console.print(f"[red]Server '{server_name}' not found[/red]")
            return
        
        metadata = server.get('metadata', {})
        
        # Create detail panels
        info = f"""
[bold]Title:[/bold] {server.get('title', 'Unknown')}
[bold]Language:[/bold] {metadata.get('language', 'Unknown')}
[bold]Category:[/bold] {metadata.get('category', 'Uncategorized')}
[bold]Official:[/bold] {'Yes' if metadata.get('isOfficial') else 'No'}
"""
        
        if metadata.get('githubUrl'):
            info += f"[bold]GitHub:[/bold] {metadata.get('githubUrl')}\n"
        
        if metadata.get('npmPackage'):
            info += f"[bold]NPM Package:[/bold] {metadata.get('npmPackage')}\n"
        
        if metadata.get('pypiPackage'):
            info += f"[bold]PyPI Package:[/bold] {metadata.get('pypiPackage')}\n"
        
        console.print(Panel(info, title="Server Information", border_style="blue"))
        
        # Description
        description = server.get('page_content', 'No description available')
        console.print(Panel(description, title="Description", border_style="green"))


@click.group()
def cli():
    """MCP Server Browser - Explore and export MCP server information."""
    pass


@cli.command()
@click.option('--category', help='Filter by category')
@click.option('--language', help='Filter by programming language')
@click.option('--limit', type=int, help='Limit number of results')
def list(category, language, limit):
    """List all MCP servers with optional filtering."""
    browser = MCPServerBrowser()
    servers = browser.list_servers(category=category, language=language, limit=limit)
    
    if servers:
        browser.display_server_table(servers, 
            title=f"MCP Servers ({len(servers)} found)")
    else:
        console.print("[yellow]No servers found matching criteria[/yellow]")


@cli.command()
@click.option('--query', '-q', required=True, help='Search query')
def search(query):
    """Search for MCP servers by name or description."""
    browser = MCPServerBrowser()
    results = browser.search_servers(query)
    
    if results:
        browser.display_server_table(results, 
            title=f"Search Results ({len(results)} found)")
    else:
        console.print(f"[yellow]No servers found matching '{query}'[/yellow]")


@cli.command()
def stats():
    """Show statistics about the MCP ecosystem."""
    browser = MCPServerBrowser()
    stats = browser.get_statistics()
    
    # Overall stats
    overall = f"""
[bold]Total Servers:[/bold] {stats['total_servers']}
[bold]Official Servers:[/bold] {stats['official_count']}
[bold]With NPM Package:[/bold] {stats['with_npm']}
[bold]With PyPI Package:[/bold] {stats['with_pip']}
[bold]With GitHub URL:[/bold] {stats['with_github']}
"""
    console.print(Panel(overall, title="Overall Statistics", border_style="cyan"))
    
    # Language distribution
    lang_table = Table(title="Languages", show_header=True)
    lang_table.add_column("Language", style="cyan")
    lang_table.add_column("Count", style="magenta")
    
    for lang, count in sorted(stats['by_language'].items(), 
                             key=lambda x: x[1], reverse=True)[:10]:
        lang_table.add_row(lang, str(count))
    
    console.print(lang_table)
    
    # Category distribution
    cat_table = Table(title="Categories", show_header=True)
    cat_table.add_column("Category", style="yellow")
    cat_table.add_column("Count", style="green")
    
    for cat, count in sorted(stats['by_category'].items(), 
                            key=lambda x: x[1], reverse=True)[:10]:
        cat_table.add_row(cat, str(count))
    
    console.print(cat_table)


@cli.command()
@click.option('--format', '-f', 
              type=click.Choice(['csv', 'json', 'yaml']), 
              default='json',
              help='Export format')
@click.option('--output', '-o', help='Output filename')
@click.option('--category', help='Filter by category before export')
@click.option('--language', help='Filter by language before export')
def export(format, output, category, language):
    """Export MCP server data to various formats."""
    browser = MCPServerBrowser()
    
    # Filter servers if requested
    servers = browser.list_servers(category=category, language=language)
    
    # Generate filename if not provided
    if not output:
        output = f"mcp_servers.{format}"
    
    # Export based on format
    if format == 'csv':
        browser.export_to_csv(output, servers)
    elif format == 'json':
        browser.export_to_json(output, servers)
    elif format == 'yaml':
        browser.export_to_yaml(output, servers)


@cli.command()
@click.argument('server_name')
def details(server_name):
    """Show detailed information about a specific server."""
    browser = MCPServerBrowser()
    browser.display_server_details(server_name)


@cli.command()
def popular():
    """Show the most popular MCP servers."""
    browser = MCPServerBrowser()
    
    # For now, show official servers as "popular"
    official = [s for s in browser.servers 
                if s.get('metadata', {}).get('isOfficial')]
    
    if official:
        browser.display_server_table(official[:20], 
            title="Popular/Official MCP Servers")
    else:
        # Show servers with npm packages as alternative
        with_npm = [s for s in browser.servers 
                    if s.get('metadata', {}).get('npmPackage')][:20]
        browser.display_server_table(with_npm, 
            title="MCP Servers with NPM Packages")


if __name__ == "__main__":
    cli()