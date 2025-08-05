#!/usr/bin/env python3
"""Comprehensive MCP Server Manager.

This script provides a complete management interface for MCP servers including:
- Discovery from multiple sources
- Installation using various methods
- Configuration management
- Health monitoring
- Updates and maintenance

Usage:
    python mcp_manager.py discover --auto-install
    python mcp_manager.py install --servers filesystem github postgres
    python mcp_manager.py install --categories official core
    python mcp_manager.py list --status all
    python mcp_manager.py health-check
    python mcp_manager.py update --all
"""

import asyncio
import json
import logging
import time

import click

from haive.mcp.downloader.core import GeneralMCPDownloader, ServerConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MCPServerManager:
    """Comprehensive MCP Server Manager."""

    def __init__(self, config_file: str | None = None, install_dir: str | None = None):
        self.downloader = GeneralMCPDownloader(config_file, install_dir)
        self.install_dir = self.downloader.install_dir
        self.status_file = self.install_dir / "server_status.json"

    async def discover_all_sources(
        self, auto_install: bool = False, limit: int | None = None
    ) -> dict:
        """Discover MCP servers from all configured sources."""
        click.echo("🔍 Discovering MCP servers from all sources...")

        discovered = {}

        # Use the downloader's discovery method
        for source in self.downloader.patterns.get("discovery_sources", []):
            click.echo(f"  Checking: {source}")
            try:
                servers = await self.downloader.discover_servers_from_registry(source)
                discovered[source] = servers
                click.echo(f"    Found: {len(servers)} servers")
            except Exception as e:
                click.echo(f"    Error: {e}")

        # Flatten and deduplicate
        all_servers = []
        seen_names = set()

        for source, servers in discovered.items():
            for server in servers:
                name = server.get("name", "")
                if name and name not in seen_names:
                    server["discovered_from"] = source
                    all_servers.append(server)
                    seen_names.add(name)

        if limit:
            all_servers = all_servers[:limit]

        click.echo("\n📊 Discovery Summary:")
        click.echo(f"  Sources checked: {len(discovered)}")
        click.echo(f"  Unique servers found: {len(all_servers)}")

        # Save discovery results
        discovery_file = self.install_dir / "discovered_servers.json"
        with open(discovery_file, "w") as f:
            json.dump(
                {
                    "discovered_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "sources": list(discovered.keys()),
                    "servers": all_servers,
                },
                f,
                indent=2,
            )

        click.echo(f"  Discovery results saved to: {discovery_file}")

        if auto_install:
            click.echo("\n🚀 Auto-installing discovered servers...")
            return await self.install_discovered_servers(all_servers)

        return {"discovered": all_servers, "discovery_file": str(discovery_file)}

    async def install_discovered_servers(self, servers: list[dict]) -> dict:
        """Install servers from discovery results."""
        # Add discovered servers to downloader config
        for server_data in servers:
            # Determine appropriate template based on server info
            template = self._determine_template(server_data)

            server = ServerConfig(
                name=server_data.get("name", ""),
                template=template,
                source=server_data.get("source", ""),
                variables=server_data.get("variables", {}),
                tags=set(server_data.get("tags", [])),
            )

            # Check if server already exists
            existing_names = [s.name for s in self.downloader.servers]
            if server.name not in existing_names:
                self.downloader.servers.append(server)

        # Install all servers
        return await self.downloader.download_servers()

    def _determine_template(self, server_data: dict) -> str:
        """Determine the best template for a discovered server."""
        source = server_data.get("source", "")
        tags = server_data.get("tags", [])

        if "npm" in tags or "npm" in source:
            if "@modelcontextprotocol" in server_data.get("variables", {}).get(
                "package", ""
            ):
                return "npm_official"
            if "@" in server_data.get("variables", {}).get("package", ""):
                return "npm_scoped"
            return "npm_community"
        if "git" in tags or "github" in tags:
            return "git_repo"
        if "docker" in tags:
            return "docker_image"
        if "pip" in tags or "python" in tags:
            return "pypi_package"
        return "npm_community"  # Default fallback

    async def install_servers(
        self, server_names: list[str] | None = None, categories: list[str] | None = None
    ) -> dict:
        """Install specific servers or categories."""
        if server_names:
            click.echo(f"📦 Installing servers: {', '.join(server_names)}")
        elif categories:
            click.echo(f"📦 Installing categories: {', '.join(categories)}")
        else:
            click.echo("📦 Installing all enabled servers")

        result = await self.downloader.download_servers(
            server_names=server_names, categories=categories
        )

        # Update status tracking
        await self._update_server_status(result.model_dump())

        return result

    async def list_servers(self, status_filter: str = "all") -> dict:
        """List servers with their status."""
        servers_info = []
        status_data = self._load_server_status()

        for server in self.downloader.servers:
            template = self.downloader.templates.get(server.template, {})
            server_status = status_data.get(server.name, {})

            info = {
                "name": server.name,
                "template": server.template,
                "category": getattr(template, "category", "unknown"),
                "enabled": server.enabled,
                "tags": list(server.tags) if hasattr(server, "tags") else [],
                "installation_method": getattr(
                    template, "installation_method", "unknown"
                ),
                "status": server_status.get("status", "unknown"),
                "last_check": server_status.get("last_check"),
                "last_success": server_status.get("last_success"),
            }

            # Filter by status
            if status_filter != "all":
                if status_filter == "installed" and info["status"] != "installed":
                    continue
                if (
                    (status_filter == "failed" and info["status"] != "failed")
                    or (status_filter == "enabled" and not info["enabled"])
                    or (status_filter == "disabled" and info["enabled"])
                ):
                    continue

            servers_info.append(info)

        return {"servers": servers_info, "total": len(servers_info)}

    async def health_check(self, server_names: list[str] | None = None) -> dict:
        """Perform health checks on servers."""
        click.echo("🏥 Performing health checks...")

        servers_to_check = []
        if server_names:
            servers_to_check = [
                s for s in self.downloader.servers if s.name in server_names
            ]
        else:
            servers_to_check = [s for s in self.downloader.servers if s.enabled]

        results = []

        for server in servers_to_check:
            template = self.downloader.templates.get(server.template)
            if not template:
                continue

            click.echo(f"  Checking: {server.name}")

            # Find appropriate installer for verification
            installer = None
            for inst in self.downloader.installers:
                if await inst.can_handle(server, template):
                    installer = inst
                    break

            if installer:
                try:
                    is_healthy = await installer.verify(
                        server, template, self.install_dir
                    )
                    status = "healthy" if is_healthy else "unhealthy"
                except Exception as e:
                    status = "error"
                    click.echo(f"    Error: {e}")
            else:
                status = "no_installer"

            results.append(
                {
                    "server": server.name,
                    "status": status,
                    "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            click.echo(f"    Status: {status}")

        # Update status file
        await self._update_health_status(results)

        # Summary
        healthy = len([r for r in results if r["status"] == "healthy"])
        total = len(results)

        click.echo("\n📊 Health Check Summary:")
        click.echo(f"  Healthy: {healthy}/{total}")
        click.echo(
            f"  Health rate: {healthy / total * 100:.1f}%"
            if total > 0
            else "  No servers checked"
        )

        return {"results": results, "healthy": healthy, "total": total}

    async def update_servers(
        self, server_names: list[str] | None = None, force: bool = False
    ) -> dict:
        """Update servers to latest versions."""
        click.echo("🔄 Updating servers...")

        # For now, this re-installs servers (future: implement proper update logic)
        return await self.install_servers(server_names)

    def _load_server_status(self) -> dict:
        """Load server status from file."""
        if self.status_file.exists():
            try:
                with open(self.status_file) as f:
                    return json.load(f)
            except BaseException:
                pass
        return {}

    async def _update_server_status(self, install_result: dict):
        """Update server status after installation."""
        status_data = self._load_server_status()

        # Update successful installations
        for server_info in install_result.get("successful_servers", []):
            server_name = server_info["server"]
            status_data[server_name] = {
                "status": "installed",
                "last_success": time.strftime("%Y-%m-%d %H:%M:%S"),
                "last_check": time.strftime("%Y-%m-%d %H:%M:%S"),
                "install_result": server_info["result"],
            }

        # Update failed installations
        for server_info in install_result.get("failed_servers", []):
            server_name = server_info["server"]
            status_data[server_name] = {
                "status": "failed",
                "last_check": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": server_info["error"],
            }

        # Save status
        with open(self.status_file, "w") as f:
            json.dump(status_data, f, indent=2)

    async def _update_health_status(self, health_results: list[dict]):
        """Update health check results."""
        status_data = self._load_server_status()

        for result in health_results:
            server_name = result["server"]
            if server_name not in status_data:
                status_data[server_name] = {}

            status_data[server_name]["health_status"] = result["status"]
            status_data[server_name]["last_health_check"] = result["checked_at"]

        # Save status
        with open(self.status_file, "w") as f:
            json.dump(status_data, f, indent=2)


# CLI Interface
@click.group()
@click.option("--config", help="Configuration file path")
@click.option("--install-dir", help="Installation directory")
@click.pass_context
def cli(ctx, config, install_dir):
    """MCP Server Manager - Comprehensive management for Model Context Protocol servers."""
    ctx.ensure_object(dict)
    ctx.obj["manager"] = MCPServerManager(config, install_dir)


@cli.command()
@click.option(
    "--auto-install", is_flag=True, help="Automatically install discovered servers"
)
@click.option("--limit", type=int, help="Limit number of servers to discover")
@click.pass_context
def discover(ctx, auto_install, limit):
    """Discover MCP servers from all configured sources."""
    manager = ctx.obj["manager"]
    result = asyncio.run(manager.discover_all_sources(auto_install, limit))

    if not auto_install:
        click.echo(f"\n📋 Discovered {len(result['discovered'])} servers")
        click.echo(f"💾 Results saved to: {result['discovery_file']}")
        click.echo("\nUse 'mcp_manager.py install' to install discovered servers")


@cli.command()
@click.option("--servers", multiple=True, help="Specific servers to install")
@click.option("--categories", multiple=True, help="Server categories to install")
@click.option("--all", "install_all", is_flag=True, help="Install all enabled servers")
@click.pass_context
def install(ctx, servers, categories, install_all):
    """Install MCP servers."""
    manager = ctx.obj["manager"]

    server_names = list(servers) if servers else None
    category_list = list(categories) if categories else None

    if not server_names and not category_list and not install_all:
        click.echo("Please specify --servers, --categories, or --all")
        return

    result = asyncio.run(manager.install_servers(server_names, category_list))

    click.echo("\n📊 Installation Results:")
    click.echo(f"  Total: {result['total']}")
    click.echo(f"  Successful: {result['successful']} ({result['success_rate']:.1f}%)")
    click.echo(f"  Failed: {result['failed']}")


@cli.command()
@click.option(
    "--status",
    type=click.Choice(["all", "installed", "failed", "enabled", "disabled"]),
    default="all",
    help="Filter servers by status",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list_servers(ctx, status, output_format):
    """List MCP servers and their status."""
    manager = ctx.obj["manager"]
    result = asyncio.run(manager.list_servers(status))

    if output_format == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        # Table format
        servers = result["servers"]
        if not servers:
            click.echo("No servers found")
            return

        click.echo(f"\n📋 MCP Servers ({result['total']} total)")
        click.echo("=" * 80)

        for server in servers:
            status_emoji = {"installed": "✅", "failed": "❌", "unknown": "❓"}.get(
                server["status"], "⚪"
            )

            enabled_emoji = "🟢" if server["enabled"] else "🔴"

            click.echo(
                f"{status_emoji} {enabled_emoji} {server['name']:<25} {server['category']:<15} {
                    server['installation_method']
                }"
            )


@cli.command()
@click.option("--servers", multiple=True, help="Specific servers to check")
@click.pass_context
def health_check(ctx, servers):
    """Perform health checks on MCP servers."""
    manager = ctx.obj["manager"]
    server_names = list(servers) if servers else None
    asyncio.run(manager.health_check(server_names))


@cli.command()
@click.option("--servers", multiple=True, help="Specific servers to update")
@click.option("--all", "update_all", is_flag=True, help="Update all servers")
@click.option("--force", is_flag=True, help="Force update even if current")
@click.pass_context
def update(ctx, servers, update_all, force):
    """Update MCP servers to latest versions."""
    manager = ctx.obj["manager"]

    server_names = list(servers) if servers else None

    if not server_names and not update_all:
        click.echo("Please specify --servers or --all")
        return

    result = asyncio.run(manager.update_servers(server_names, force))

    click.echo("\n📊 Update Results:")
    click.echo(f"  Updated: {result['successful']}")
    click.echo(f"  Failed: {result['failed']}")


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    manager = ctx.obj["manager"]

    click.echo("📋 Current Configuration")
    click.echo("=" * 50)
    click.echo(f"Install Directory: {manager.install_dir}")
    click.echo(f"Templates: {len(manager.downloader.templates)}")
    click.echo(f"Servers: {len(manager.downloader.servers)}")
    click.echo(
        f"Discovery Sources: {len(manager.downloader.patterns.get('discovery_sources', []))}"
    )


if __name__ == "__main__":
    cli()
