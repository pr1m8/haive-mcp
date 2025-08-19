"""
Main entry point for haive-mcp CLI.

Usage:
    python -m haive.mcp [options]
"""

from haive.mcp.servers.mcp_server_manager import main

if __name__ == "__main__":
    main()