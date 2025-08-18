#!/usr/bin/env python3
"""Integrated MCP System Launcher.

Provides easy access to all components of the integrated MCP discovery and management system.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def print_banner():
    """Print system banner."""


def check_dependencies():
    """Check required dependencies."""
    missing = []

    try:
        import streamlit
    except ImportError:
        missing.append("streamlit")

    try:
        import plotly
    except ImportError:
        missing.append("plotly")

    try:
        import pandas
    except ImportError:
        missing.append("pandas")

    try:
        import aiohttp
    except ImportError:
        missing.append("aiohttp")

    try:
        import psutil
    except ImportError:
        missing.append("psutil")

    return not missing


def run_integrated_web():
    """Launch the integrated web interface."""
    script_path = Path(__file__).parent / "integrated_mcp_system.py"
    subprocess.run(["streamlit", "run", str(script_path)], check=False)


def run_discovery_test():
    """Test the discovery system."""
    script_path = Path(__file__).parent / "self_query_mcp_agent.py"
    subprocess.run([sys.executable, str(script_path)], check=False)


def run_fastmcp_manager(args):
    """Run FastMCP server management commands."""
    script_path = Path(__file__).parent / "fastmcp_runner.py"
    cmd = [sys.executable, str(script_path), *args]
    subprocess.run(cmd, check=False)


def show_status():
    """Show system status."""
    # Check for MCP servers data
    data_path = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "mcp_servers"
        / "ALL_MCP_SERVERS_COMPLETE.json"
    )

    if data_path.exists():
        with open(data_path) as f:
            data = json.load(f)
            servers = data.get("all_servers", [])
    else:
        pass

    # Check for FastMCP config
    fastmcp_config = Path.home() / ".fastmcp" / "servers.json"

    if fastmcp_config.exists():
        with open(fastmcp_config) as f:
            data = json.load(f)
            servers = data.get("servers", {})

            # List installed servers
            if servers:
                for _name, config in servers.items():
                    "✅" if config.get("active", True) else "❌"
    else:
        pass

    # Check for vector store
    vector_store_path = Path(__file__).parent / "vector_store"
    if vector_store_path.exists():
        pass
    else:
        pass


def run_csv_viewer():
    """Launch CSV data viewer."""
    script_path = Path(__file__).parent / "csv_viewer.py"
    subprocess.run([sys.executable, str(script_path), "--web"], check=False)


def install_server_interactive():
    """Interactive server installation."""
    # Load available servers
    data_path = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "mcp_servers"
        / "ALL_MCP_SERVERS_COMPLETE.json"
    )

    if not data_path.exists():
        return

    with open(data_path) as f:
        data = json.load(f)
        servers = data.get("all_servers", [])

    # Filter servers with install commands
    installable = [
        s for s in servers if s.get("install_command") or s.get("repository_url")
    ]

    # Show categories
    categories = {}
    for server in installable:
        cat = server.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    for _i, (cat, _count) in enumerate(sorted(categories.items()), 1):
        pass

    try:
        cat_choice = int(input("\nSelect category (number): ")) - 1
        selected_category = sorted(categories.keys())[cat_choice]
    except (ValueError, IndexError):
        return

    # Show servers in category
    cat_servers = [s for s in installable if s.get("category") == selected_category]

    for _i, server in enumerate(cat_servers[:20], 1):  # Limit to 20
        server.get("name", "Unknown")
        server.get("stars", 0)
        server.get("description", "No description")[:50] + "..."

    try:
        server_choice = int(input("\nSelect server to install (number): ")) - 1
        cat_servers[server_choice]
    except (ValueError, IndexError):
        return

    # Show server details

    if input("\nProceed with installation? (y/n): ").lower() == "y":
        pass


def main():
    """Main.
"""
    parser = argparse.ArgumentParser(
        description="MCP Integrated System Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s web              # Launch integrated web interface (recommended)
  %(prog)s status           # Show system status
  %(prog)s discover         # Test discovery system
  %(prog)s csv              # Launch CSV data viewer
  %(prog)s server start weather    # Start a server
  %(prog)s server stop weather     # Stop a server
  %(prog)s server status           # Show running servers
  %(prog)s install          # Interactive server installation
        """,
    )

    parser.add_argument(
        "command",
        choices=["web", "status", "discover", "csv", "server", "install"],
        help="Command to execute",
    )

    parser.add_argument("args", nargs="*", help="Additional arguments for the command")

    args = parser.parse_args()

    print_banner()

    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)

    if args.command == "web":
        run_integrated_web()

    elif args.command == "status":
        show_status()

    elif args.command == "discover":
        run_discovery_test()

    elif args.command == "csv":
        run_csv_viewer()

    elif args.command == "server":
        if not args.args:
            sys.exit(1)
        run_fastmcp_manager(args.args)

    elif args.command == "install":
        install_server_interactive()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
