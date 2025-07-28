"""Integrated_Launcher core module.

This module provides integrated launcher functionality for the Haive framework.

Functions:
    print_banner: Print Banner functionality.
    check_dependencies: Check Dependencies functionality.
    run_integrated_web: Run Integrated Web functionality.
"""

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
    print(
        """
╔══════════════════════════════════════════════════════════════════╗
║       🚀 MCP Integrated Discovery & Management System 🚀         ║
║                                                                  ║
║  Seamlessly discover, install, and manage MCP servers           ║
╚══════════════════════════════════════════════════════════════════╝
    """
    )


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

    if missing:
        print("❌ Missing dependencies:")
        print(f"   Run: pip install {' '.join(missing)}")
        return False

    return True


def run_integrated_web():
    """Launch the integrated web interface."""
    print("🌐 Launching Integrated MCP Web Interface...")
    script_path = Path(__file__).parent / "integrated_mcp_system.py"
    subprocess.run(["streamlit", "run", str(script_path)], check=False)


def run_discovery_test():
    """Test the discovery system."""
    print("🔍 Testing MCP Discovery System...")
    script_path = Path(__file__).parent / "self_query_mcp_agent.py"
    subprocess.run([sys.executable, str(script_path)], check=False)


def run_fastmcp_manager(args):
    """Run FastMCP server management commands."""
    script_path = Path(__file__).parent / "fastmcp_runner.py"
    cmd = [sys.executable, str(script_path)] + args
    subprocess.run(cmd, check=False)


def show_status():
    """Show system status."""
    print("\n📊 System Status")
    print("=" * 50)

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
            print(f"✅ MCP Database: {len(servers)} servers available")
    else:
        print("❌ MCP Database: Not found")

    # Check for FastMCP config
    fastmcp_config = Path.home() / ".fastmcp" / "servers.json"

    if fastmcp_config.exists():
        with open(fastmcp_config) as f:
            data = json.load(f)
            servers = data.get("servers", {})
            print(f"✅ Installed Servers: {len(servers)} servers configured")

            # List installed servers
            if servers:
                print("\n   Installed servers:")
                for name, config in servers.items():
                    active = "✅" if config.get("active", True) else "❌"
                    print(f"   {active} {name} ({config.get('transport', 'stdio')})")
    else:
        print("❌ Installed Servers: None")

    # Check for vector store
    vector_store_path = Path(__file__).parent / "vector_store"
    if vector_store_path.exists():
        print("✅ Search Index: Initialized")
    else:
        print("⚠️  Search Index: Not initialized (will be created on first search)")


def run_csv_viewer():
    """Launch CSV data viewer."""
    print("📊 Launching CSV Data Viewer...")
    script_path = Path(__file__).parent / "csv_viewer.py"
    subprocess.run([sys.executable, str(script_path), "--web"], check=False)


def install_server_interactive():
    """Interactive server installation."""
    print("\n📦 Interactive Server Installation")
    print("=" * 50)

    # Load available servers
    data_path = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "mcp_servers"
        / "ALL_MCP_SERVERS_COMPLETE.json"
    )

    if not data_path.exists():
        print("❌ MCP database not found")
        return

    with open(data_path) as f:
        data = json.load(f)
        servers = data.get("all_servers", [])

    # Filter servers with install commands
    installable = [
        s for s in servers if s.get("install_command") or s.get("repository_url")
    ]

    print(f"Found {len(installable)} installable servers")

    # Show categories
    categories = {}
    for server in installable:
        cat = server.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCategories:")
    for i, (cat, count) in enumerate(sorted(categories.items()), 1):
        print(f"  {i}. {cat} ({count} servers)")

    try:
        cat_choice = int(input("\nSelect category (number): ")) - 1
        selected_category = sorted(categories.keys())[cat_choice]
    except:
        print("Invalid selection")
        return

    # Show servers in category
    cat_servers = [s for s in installable if s.get("category") == selected_category]

    print(f"\nServers in '{selected_category}':")
    for i, server in enumerate(cat_servers[:20], 1):  # Limit to 20
        name = server.get("name", "Unknown")
        stars = server.get("stars", 0)
        desc = server.get("description", "No description")[:50] + "..."
        print(f"  {i}. {name} ({stars}⭐) - {desc}")

    try:
        server_choice = int(input("\nSelect server to install (number): ")) - 1
        selected_server = cat_servers[server_choice]
    except:
        print("Invalid selection")
        return

    # Show server details
    print(f"\n📋 Server: {selected_server.get('name')}")
    print(f"Description: {selected_server.get('description', 'N/A')}")
    print(f"Language: {selected_server.get('language', 'unknown')}")
    print(
        f"Install: {selected_server.get('install_command', 'Manual installation required')}"
    )

    if input("\nProceed with installation? (y/n): ").lower() == "y":
        print("Please use the web interface for automated installation")
        print("Run: python integrated_launcher.py web")


def main():
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
            print("Error: Server command required (start, stop, status, list, monitor)")
            sys.exit(1)
        run_fastmcp_manager(args.args)

    elif args.command == "install":
        install_server_interactive()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
