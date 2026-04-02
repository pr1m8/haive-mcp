"""CLI entry point for haive-mcp.

Usage:
    python -m haive.mcp [command] [options]
    haive-mcp [command] [options]
"""

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="haive-mcp")
def cli():
    """haive-mcp - Dynamic MCP integration for Haive agents."""


@cli.command()
def status():
    """Show status of configured MCP servers."""
    from haive.mcp.config import MCPConfig

    config = MCPConfig()
    click.echo(f"MCP enabled: {config.enabled}")
    click.echo(f"Servers configured: {len(config.servers)}")
    click.echo(f"Auto-discover: {config.auto_discover}")
    click.echo(f"Health checks: {config.enable_health_checks}")


@cli.command()
@click.argument("capability", required=False, default=None)
def discover(capability: str | None):
    """Discover MCP servers by capability.

    If no capability is specified, lists all available categories.
    """
    from haive.mcp.self_query import MCPSelfQuery

    engine = MCPSelfQuery()
    click.echo(f"MCP Server Database: {engine.server_count} servers\n")

    if capability:
        results = engine.search(capability)
        click.echo(f"Found {len(results)} servers matching '{capability}':\n")
        for s in results[:15]:
            name = s.get("name", "?")
            desc = (s.get("description") or "")[:60]
            click.echo(f"  {name}")
            if desc:
                click.echo(f"    {desc}")
    else:
        cats = engine.get_categories()
        click.echo("Categories:\n")
        for cat, count in cats.items():
            click.echo(f"  {cat:<30} ({count} servers)")


@cli.command("self-query")
def self_query_cmd():
    """Interactive self-query interface for MCP server discovery."""
    from haive.mcp.self_query import run_interactive

    run_interactive()


@cli.command()
def transports():
    """List supported transport types."""
    from haive.mcp.config import MCPTransport

    click.echo("Supported MCP transport types:\n")
    for transport in MCPTransport:
        descriptions = {
            "stdio": "Standard I/O (subprocess) - most common, works with npx/uvx",
            "sse": "Server-Sent Events (HTTP streaming)",
            "streamable_http": "HTTP streaming for continuous data",
            "docker": "Docker container (isolated execution)",
        }
        desc = descriptions.get(transport.value, "")
        click.echo(f"  {transport.value:<20} {desc}")


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
