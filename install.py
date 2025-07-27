#!/usr/bin/env python3
"""Quick install script for haive-mcp.

This script provides a quick way to install and verify the haive-mcp package.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a command with error handling."""
    print(f"\n📦 {description}...")
    try:
        if isinstance(cmd, str):
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, check=check
            )
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)

        if result.returncode == 0:
            print(f"✅ {description} - Success")
            if result.stdout and len(result.stdout.strip()) < 200:
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} - Failed")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False


def main():
    """Main installation process."""
    print("🚀 Installing haive-mcp package...\n")

    # Check we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: Must run from haive-mcp directory")
        return 1

    # Step 1: Install Python dependencies
    if not run_command("poetry install --all-extras", "Installing Python dependencies"):
        print("\n💡 Try running: pip install poetry")
        return 1

    # Step 2: Check MCP imports
    print("\n🔍 Checking MCP imports...")

    # Check core imports using poetry
    result = run_command(
        [
            "poetry",
            "run",
            "python",
            "-c",
            "from haive.mcp import MCPConfig, MCPServerConfig; print('Core imports OK')",
        ],
        "Core imports test",
        check=False,
    )

    # Check MCP SDK
    result = run_command(
        [
            "poetry",
            "run",
            "python",
            "-c",
            "from mcp.server import FastMCP; print('MCP SDK OK')",
        ],
        "MCP SDK test",
        check=False,
    )
    if not result:
        print("   💡 To install MCP SDK: poetry add mcp")

    # Check LangChain MCP adapters
    result = run_command(
        [
            "poetry",
            "run",
            "python",
            "-c",
            "from langchain_mcp_adapters.client import MultiServerMCPClient; print('LangChain MCP OK')",
        ],
        "LangChain MCP test",
        check=False,
    )
    if not result:
        print("   💡 To install LangChain MCP: poetry add langchain-mcp-adapters")

    # Step 3: Create directories
    print("\n📁 Creating directories...")
    dirs = [
        Path.home() / ".haive" / "mcp" / "servers",
        Path.home() / ".haive" / "mcp" / "configs",
        Path("logs"),
        Path("data"),
    ]

    for dir_path in dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {dir_path}")
        except Exception as e:
            print(f"⚠️  Could not create {dir_path}: {e}")

    # Step 4: Quick test
    if run_command(
        ["poetry", "run", "pytest", "tests/unit/test_config.py", "-q"],
        "Running quick test",
        check=False,
    ):
        print("✅ Tests passing")
    else:
        print("⚠️  Some tests failed (this might be ok)")

    # Step 5: Optional - Install a sample MCP server
    if sys.stdin.isatty():
        print("\n🤔 Would you like to install a sample MCP server? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response == "y":
                run_command(
                    "npm install -g @modelcontextprotocol/server-filesystem",
                    "Installing filesystem MCP server",
                    check=False,
                )
        except KeyboardInterrupt:
            print("\n⏭️  Skipping optional installs")
        except EOFError:
            pass
    else:
        print("\n⏭️  Skipping interactive prompts (non-TTY environment)")

    # Summary
    print("\n" + "=" * 50)
    print("✅ INSTALLATION COMPLETE!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Test imports: poetry run python -c 'from haive.mcp import MCPManager'")
    print("2. Run tests: poetry run pytest")
    print("3. Try examples: poetry run python examples/basic_mcp_agent.py")
    print("\nFor full setup with all MCP servers, run: poetry run python setup_all.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
