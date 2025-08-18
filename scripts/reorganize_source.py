#!/usr/bin/env python3
"""Script to reorganize MCP source files into proper structure.

This script moves files from the root MCP directory into appropriate
subdirectories based on their functionality.
"""

import os
import shutil
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent / "src" / "haive" / "mcp"

# File movements mapping
FILE_MOVEMENTS = {
    "retrieval": [
        "simple_faiss_retriever.py",
        "enhanced_parent_self_query_retriever.py",
        "working_enhanced_retriever.py",
        "complete_mcp_with_parent_retriever.py",
    ],
    "examples": [
        "simple_rag_mcp_agent.py",
        "mcp_simple_rag_agent.py",
        "mcp_simple_tool_agent.py",
        "self_query_mcp_agent.py",
        "self_query_mcp_agent_v2.py",
        "mcp_rag_agent.py",
    ],
    "integration": [
        "haive_agent_mcp_integration.py",
        "fastapi_mcp_server.py",
        "integrated_mcp_system.py",
        "integrated_launcher.py",
    ],
    "archive": [
        "comprehensive_mcp_web.py",
        "csv_viewer.py",
        "dynamic_activation_mcp.py",
        "dynamic_mcp_tool.py",
        "enhance_mcp_data.py",
        "fastmcp_runner.py",
        "launcher.py",
        "production_mcp_tool.py",
    ],
}


def move_files(dry_run=True):
    """Move files to their appropriate directories.

    Args:
        dry_run: If True, only print what would be done without moving files.
    """
    for target_dir, files in FILE_MOVEMENTS.items():
        target_path = BASE_DIR / target_dir

        # Ensure target directory exists
        if not dry_run:
            target_path.mkdir(exist_ok=True)

        for filename in files:
            source = BASE_DIR / filename
            destination = target_path / filename

            if source.exists():
                if dry_run:
                    print(f"Would move: {filename} -> {target_dir}/{filename}")
                else:
                    shutil.move(str(source), str(destination))
                    print(f"Moved: {filename} -> {target_dir}/{filename}")
            else:
                print(f"File not found: {filename}")


def create_readme_files(dry_run=True):
    """Create README files for new directories.

    Args:
        dry_run: If True, only print what would be done.
    """
    readme_contents = {
        "retrieval": """# MCP Retrieval Components

This directory contains retrieval and RAG-related components for MCP.

## Components

- `simple_faiss_retriever.py` - FAISS-based vector retriever
- `enhanced_parent_self_query_retriever.py` - Advanced retriever with parent document support
- `working_enhanced_retriever.py` - Production-ready enhanced retriever
- `complete_mcp_with_parent_retriever.py` - Complete retriever implementation
""",
        "examples": """# MCP Examples

This directory contains example implementations showing how to use MCP components.

## Examples

- `simple_rag_mcp_agent.py` - Basic RAG agent with MCP
- `mcp_simple_rag_agent.py` - Alternative RAG implementation
- `mcp_simple_tool_agent.py` - Tool-focused MCP agent
- `self_query_mcp_agent.py` - Self-querying agent example
- `self_query_mcp_agent_v2.py` - Improved self-querying agent
""",
        "archive": """# Archived MCP Components

This directory contains experimental or deprecated components that are no longer
actively maintained but kept for reference.

## Contents

Various experimental implementations and older versions of components.
""",
    }

    for dir_name, content in readme_contents.items():
        readme_path = BASE_DIR / dir_name / "README.md"

        if dry_run:
            print(f"Would create: {dir_name}/README.md")
        else:
            readme_path.parent.mkdir(exist_ok=True)
            readme_path.write_text(content)
            print(f"Created: {dir_name}/README.md")


def main():
    """Main function to run the reorganization."""
    import sys

    print("MCP Source Reorganization Script")
    print("=" * 50)

    # Check for command line argument
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("\nDRY RUN - Showing what would be done:")
        print("-" * 50)
        move_files(dry_run=True)
        print("\nREADME files to create:")
        create_readme_files(dry_run=True)
    else:
        print("\nExecuting reorganization...")
        move_files(dry_run=False)
        create_readme_files(dry_run=False)
        print("\nReorganization complete!")


if __name__ == "__main__":
    main()
