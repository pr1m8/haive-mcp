"""Launcher core module.

This module provides launcher functionality for the Haive framework.

Functions:
    run_csv_viewer: Run Csv Viewer functionality.
    run_comprehensive_web: Run Comprehensive Web functionality.
    run_self_query_test: Run Self Query Test functionality.
"""

#!/usr/bin/env python3
"""MCP Discovery Tools Launcher.

Easy launcher for all MCP discovery and analysis tools.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_csv_viewer():
    """Launch CSV viewer."""
    script_path = Path(__file__).parent / "csv_viewer.py"
    subprocess.run([sys.executable, str(script_path), "--web"], check=False)


def run_comprehensive_web():
    """Launch comprehensive web interface."""
    script_path = Path(__file__).parent / "comprehensive_mcp_web.py"
    subprocess.run(["streamlit", "run", str(script_path)], check=False)


def run_self_query_test():
    """Run self-query agent test."""
    script_path = Path(__file__).parent / "self_query_mcp_agent.py"
    subprocess.run([sys.executable, str(script_path)], check=False)


def run_data_enhancement(max_servers=None):
    """Run data enhancement."""
    script_path = Path(__file__).parent / "enhance_mcp_data.py"
    cmd = [sys.executable, str(script_path)]

    if max_servers:
        cmd.extend(["--max-servers", str(max_servers)])

    subprocess.run(cmd, check=False)


def run_original_rag_agent():
    """Run original RAG agent."""
    script_path = Path(__file__).parent / "mcp_simple_rag_agent.py"
    subprocess.run([sys.executable, str(script_path)], check=False)


def main():
    parser = argparse.ArgumentParser(description="MCP Discovery Tools Launcher")
    parser.add_argument(
        "tool",
        choices=["web", "csv", "test", "enhance", "rag", "all"],
        help="Tool to launch",
    )
    parser.add_argument(
        "--max-servers", type=int, help="Max servers for data enhancement (for testing)"
    )

    args = parser.parse_args()

    if args.tool == "web":
        print("🚀 Launching Comprehensive Web Interface...")
        run_comprehensive_web()

    elif args.tool == "csv":
        print("📊 Launching CSV Viewer...")
        run_csv_viewer()

    elif args.tool == "test":
        print("🧪 Running Self-Query Agent Test...")
        run_self_query_test()

    elif args.tool == "enhance":
        print("📈 Running Data Enhancement...")
        run_data_enhancement(args.max_servers)

    elif args.tool == "rag":
        print("🤖 Launching Original RAG Agent...")
        run_original_rag_agent()

    elif args.tool == "all":
        print("🎯 Available Tools:")
        print("=" * 50)
        print("1. web      - Comprehensive web interface (recommended)")
        print("2. csv      - CSV data viewer")
        print("3. test     - Test self-query search")
        print("4. enhance  - Enhance data with GitHub info")
        print("5. rag      - Original RAG agent")
        print()
        print("Usage examples:")
        print("  poetry run python launcher.py web")
        print("  poetry run python launcher.py enhance --max-servers 10")
        print("  poetry run python launcher.py test")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Show help if no arguments
        main()
        sys.argv.append("all")

    main()
