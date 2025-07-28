"""Github_Mass_Downloader core module.

This module provides github mass downloader functionality for the Haive framework.

Classes:
    GitHubMCPDownloader: GitHubMCPDownloader implementation.

Functions:
    load_all_servers: Load All Servers functionality.
    categorize_servers: Categorize Servers functionality.
"""

#!/usr/bin/env python3
"""Download ALL MCP servers from the GitHub resources.

This script reads all MCP server information from agent_resources/mcp_servers/
and downloads/installs every single one in an organized manner.
"""

import asyncio
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from general_mcp_downloader import GeneralMCPDownloader, ServerConfig
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.tree import Tree

console = Console()


class GitHubMCPDownloader:
    """Download all MCP servers from GitHub resources."""

    def __init__(self, resources_dir: str = "agent_resources/mcp_servers"):
        self.resources_dir = Path(resources_dir)
        self.all_servers_file = self.resources_dir / "all_mcp_documents.json"
        self.documents_dir = self.resources_dir / "documents"
        self.output_dir = Path("all_mcp_downloads")
        self.output_dir.mkdir(exist_ok=True)

        # Create organized subdirectories
        self.dirs = {
            "official": self.output_dir / "official",
            "npm": self.output_dir / "npm",
            "python": self.output_dir / "python",
            "github": self.output_dir / "github",
            "docker": self.output_dir / "docker",
            "other": self.output_dir / "other",
        }

        for dir_path in self.dirs.values():
            dir_path.mkdir(exist_ok=True)

    def load_all_servers(self):
        """Load all server information from resources."""
        if not self.all_servers_file.exists():
            console.print(f"[red]Error: {self.all_servers_file} not found![/red]")
            return []

        with open(self.all_servers_file) as f:
            return json.load(f)

    def categorize_servers(self, servers):
        """Categorize servers by type."""
        categorized = defaultdict(list)

        for server in servers:
            metadata = server.get("metadata", {})
            name = metadata.get("name", "")
            repo_url = metadata.get("repo_url", "")
            languages = metadata.get("languages", [])

            # Determine category
            if "@modelcontextprotocol" in name:
                category = "official"
            elif (
                any(lang.lower() == "javascript" for lang in languages)
                or "npm" in name.lower()
            ):
                category = "npm"
            elif any(lang.lower() == "python" for lang in languages):
                category = "python"
            elif repo_url and "github.com" in repo_url:
                category = "github"
            else:
                category = "other"

            categorized[category].append(server)

        return categorized

    def create_server_config(self, server_data):
        """Create ServerConfig from server data."""
        metadata = server_data.get("metadata", {})
        name = metadata.get("name", "").split("/")[-1]
        repo_url = metadata.get("repo_url", "")
        languages = metadata.get("languages", [])

        # Clean up name
        name = (
            name.replace("mcp-server-", "")
            .replace("-mcp-server", "")
            .replace("mcp-", "")
        )
        if not name:
            name = "unknown"

        # Determine installation method
        if "@modelcontextprotocol" in metadata.get("name", ""):
            template = "npm_official"
            source = "npm"
            variables = {"service": name}
        elif "npm" in metadata.get("name", "").lower() or any(
            lang.lower() == "javascript" for lang in languages
        ):
            template = "npm_community"
            source = "npm"
            variables = {"package": metadata.get("name", "")}
        elif any(lang.lower() == "python" for lang in languages):
            template = "pypi_package"
            source = "pypi"
            variables = {"package": name}
        elif repo_url:
            template = "git_repo"
            source = repo_url
            # Parse owner and repo
            parts = (
                repo_url.replace("https://github.com/", "")
                .replace(".git", "")
                .split("/")
            )
            owner = parts[0] if len(parts) > 0 else "unknown"
            repo = parts[1] if len(parts) > 1 else name
            variables = {"owner": owner, "repo": repo}
        else:
            return None

        return ServerConfig(
            name=name[:50],  # Limit name length
            template=template,
            source=source,
            variables=variables,
            tags={cat.lower() for cat in metadata.get("category", "").split() if cat},
        )

    async def download_all_servers(self):
        """Download all servers from GitHub resources."""
        console.print(
            Panel.fit(
                "[bold cyan]🚀 GitHub MCP Server Mass Downloader[/bold cyan]\n"
                "Downloading ALL MCP servers from agent_resources",
                title="MCP Mass Download",
            )
        )

        # Load servers
        console.print("\n[yellow]Loading server information...[/yellow]")
        servers = self.load_all_servers()
        console.print(f"Found [green]{len(servers)}[/green] total servers")

        # Categorize
        categorized = self.categorize_servers(servers)

        # Show categories
        tree = Tree("📁 Server Categories")
        for category, servers_list in categorized.items():
            tree.add(f"{category}: {len(servers_list)} servers")
        console.print(tree)

        # Create downloaders for each category
        results = {}

        for category, servers_list in categorized.items():
            console.print(f"\n[bold cyan]Processing {category} servers...[/bold cyan]")

            # Create downloader for this category
            downloader = GeneralMCPDownloader(install_dir=str(self.dirs[category]))

            # Add servers
            valid_servers = []
            for server_data in servers_list:
                config = self.create_server_config(server_data)
                if config:
                    # Check if already exists
                    if not any(s.name == config.name for s in downloader.servers):
                        downloader.servers.append(config)
                        valid_servers.append(config.name)

            console.print(f"Added {len(valid_servers)} valid {category} servers")

            # Download with progress
            if valid_servers:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        f"Downloading {category} servers...", total=len(valid_servers)
                    )

                    # Download in batches
                    batch_size = 5
                    successful = 0
                    failed = 0

                    for i in range(0, len(valid_servers), batch_size):
                        batch = valid_servers[i : i + batch_size]

                        try:
                            result = await downloader.download_servers(
                                server_names=batch, max_concurrent=3
                            )

                            successful += result.get("successful", 0)
                            failed += result.get("failed", 0)

                            progress.update(task, advance=len(batch))

                        except Exception as e:
                            console.print(f"[red]Error in batch: {e}[/red]")
                            failed += len(batch)
                            progress.update(task, advance=len(batch))

                    results[category] = {
                        "total": len(valid_servers),
                        "successful": successful,
                        "failed": failed,
                    }

        # Show results
        self.show_results(results)

        # Create master config
        self.create_master_config(categorized)

    def show_results(self, results):
        """Display download results."""
        console.print("\n")

        table = Table(title="Download Results", box=box.ROUNDED)
        table.add_column("Category", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Success", justify="right", style="green")
        table.add_column("Failed", justify="right", style="red")
        table.add_column("Success Rate", justify="right")

        total_all = 0
        success_all = 0
        failed_all = 0

        for category, stats in results.items():
            total = stats["total"]
            successful = stats["successful"]
            failed = stats["failed"]
            rate = (successful / total * 100) if total > 0 else 0

            table.add_row(
                category.title(),
                str(total),
                str(successful),
                str(failed),
                f"{rate:.1f}%",
            )

            total_all += total
            success_all += successful
            failed_all += failed

        # Add total row
        table.add_section()
        total_rate = (success_all / total_all * 100) if total_all > 0 else 0
        table.add_row(
            "TOTAL",
            str(total_all),
            str(success_all),
            str(failed_all),
            f"{total_rate:.1f}%",
            style="bold",
        )

        console.print(table)

    def create_master_config(self, categorized):
        """Create a master configuration file."""
        master_config = {
            "generated_at": datetime.now().isoformat(),
            "categories": {},
            "total_servers": sum(len(servers) for servers in categorized.values()),
        }

        for category, servers_list in categorized.items():
            config_file = (
                self.dirs[category] / ".mcp" / "configs" / "mcp_servers_config.json"
            )
            if config_file.exists():
                with open(config_file) as f:
                    cat_config = json.load(f)

                master_config["categories"][category] = {
                    "count": len(servers_list),
                    "config_file": str(config_file),
                    "servers": list(cat_config.get("mcpServers", {}).keys()),
                }

        master_file = self.output_dir / "master_mcp_config.json"
        with open(master_file, "w") as f:
            json.dump(master_config, f, indent=2)

        console.print(
            f"\n[green]✅ Master configuration saved to:[/green] {master_file}"
        )

        # Show organized structure
        console.print("\n[bold]📁 Organized Structure:[/bold]")
        tree = Tree(f"📁 {self.output_dir}")

        for category, dir_path in self.dirs.items():
            if dir_path.exists():
                cat_tree = tree.add(f"📁 {category}/")
                # Count actual directories
                subdirs = [
                    d for d in dir_path.iterdir() if d.is_dir() and d.name != ".mcp"
                ]
                if subdirs:
                    for subdir in subdirs[:5]:  # Show first 5
                        cat_tree.add(f"📦 {subdir.name}")
                    if len(subdirs) > 5:
                        cat_tree.add(f"... and {len(subdirs) - 5} more")

        console.print(tree)


async def main():
    """Main function."""
    downloader = GitHubMCPDownloader()

    try:
        await downloader.download_all_servers()

        console.print("\n[bold green]🎉 Mass download complete![/bold green]")
        console.print("\n[yellow]What was accomplished:[/yellow]")
        console.print("✅ Loaded all MCP servers from GitHub resources")
        console.print("✅ Categorized servers by type (official, npm, python, etc.)")
        console.print("✅ Downloaded and organized servers into directories")
        console.print("✅ Created configuration files for each category")
        console.print("✅ Generated master configuration file")

    except KeyboardInterrupt:
        console.print("\n[yellow]Download interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
