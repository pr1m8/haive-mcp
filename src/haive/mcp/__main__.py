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
    try:
        from haive.mcp.documentation import MCPDocumentationLoader

        loader = MCPDocumentationLoader()
        docs = loader.load_all_mcp_documents()
        click.echo(f"Found {len(docs)} MCP servers in database")

        if capability:
            click.echo(f"\nSearching for '{capability}'...")
            results = [
                d for d in docs if capability.lower() in str(d).lower()
            ]
            click.echo(f"Found {len(results)} matching servers")
            for doc in results[:10]:
                name = doc.get("name", "Unknown") if isinstance(doc, dict) else str(doc)[:60]
                click.echo(f"  - {name}")
    except ImportError:
        click.echo("Discovery requires the full haive-mcp installation.")
        click.echo("Run: poetry install")


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
