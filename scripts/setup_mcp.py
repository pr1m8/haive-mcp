#!/usr/bin/env python3
"""Setup script for the General MCP Downloader

This script sets up the general MCP downloader system and handles dependencies.
"""

import asyncio
import logging
from pathlib import Path
import subprocess
import sys


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")

    required_packages = ["aiohttp", "click", "pyyaml"]

    for package in required_packages:
        try:
            print(f"  Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"  ✅ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install {package}: {e}")
            return False

    return True


def setup_directories():
    """Create necessary directories"""
    print("📁 Setting up directories...")

    dirs = [
        Path.home() / ".mcp",
        Path.home() / ".mcp" / "servers",
        Path.home() / ".mcp" / "configs",
        Path.home() / ".mcp" / "logs",
        Path.home() / ".mcp" / "backups",
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created: {dir_path}")


def make_executable():
    """Make scripts executable"""
    print("🔧 Making scripts executable...")

    scripts = [
        "general_mcp_downloader.py",
        "mcp_manager.py",
        "test_general_downloader.py",
    ]

    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            script_path.chmod(0o755)
            print(f"  ✅ Made executable: {script}")
        else:
            print(f"  ⚠️  Script not found: {script}")


async def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")

    try:
        from general_mcp_downloader import GeneralMCPDownloader

        # Create a test downloader
        downloader = GeneralMCPDownloader()

        print("  ✅ Downloader created successfully")
        print(f"  📋 Templates loaded: {len(downloader.templates)}")
        print(f"  🎯 Servers configured: {len(downloader.servers)}")
        print(f"  📁 Install directory: {downloader.install_dir}")

        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False


def create_aliases():
    """Create convenient command aliases"""
    print("🔗 Creating command aliases...")

    current_dir = Path.cwd()

    # Create shell aliases
    aliases = f"""
# MCP Manager Aliases
alias mcp-discover='python "{current_dir}/mcp_manager.py" discover'
alias mcp-install='python "{current_dir}/mcp_manager.py" install'
alias mcp-list='python "{current_dir}/mcp_manager.py" list-servers'
alias mcp-health='python "{current_dir}/mcp_manager.py" health-check'
alias mcp-update='python "{current_dir}/mcp_manager.py" update'
alias mcp-config='python "{current_dir}/mcp_manager.py" config'

# Quick commands
alias mcp-install-core='python "{current_dir}/mcp_manager.py" install --categories official core'
alias mcp-install-all='python "{current_dir}/mcp_manager.py" install --all'
alias mcp-discover-install='python "{current_dir}/mcp_manager.py" discover --auto-install --limit 10'
"""

    # Save to aliases file
    aliases_file = Path.home() / ".mcp" / "aliases.sh"
    with open(aliases_file, "w") as f:
        f.write(aliases)

    print(f"  ✅ Aliases saved to: {aliases_file}")
    print(f"  💡 Run 'source {aliases_file}' to use aliases")


def show_usage_examples():
    """Show usage examples"""
    print("\n🎯 Usage Examples:")
    print("=" * 50)

    examples = [
        (
            "Discover servers",
            "python mcp_manager.py discover --auto-install --limit 10",
        ),
        (
            "Install specific servers",
            "python mcp_manager.py install --servers filesystem github postgres",
        ),
        ("Install by category", "python mcp_manager.py install --categories official"),
        ("List all servers", "python mcp_manager.py list-servers"),
        ("Health check", "python mcp_manager.py health-check"),
        ("Update servers", "python mcp_manager.py update --all"),
        ("Test the system", "python test_general_downloader.py"),
    ]

    for description, command in examples:
        print(f"  {description}:")
        print(f"    {command}")
        print()


async def main():
    """Main setup function"""
    print("🚀 General MCP Downloader Setup")
    print("=" * 50)
    print("Setting up the flexible, general MCP server management system...")
    print()

    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed!")
        return False

    print()

    # Setup directories
    setup_directories()
    print()

    # Make scripts executable
    make_executable()
    print()

    # Test installation
    test_success = await test_installation()
    print()

    if test_success:
        # Create aliases
        create_aliases()
        print()

        # Show usage examples
        show_usage_examples()

        print("🎉 Setup completed successfully!")
        print("\n📋 What was created:")
        print("  ✅ General MCP Downloader - Flexible, configurable server installer")
        print("  ✅ MCP Manager - Complete CLI management interface")
        print("  ✅ Configuration templates - Reusable installation patterns")
        print("  ✅ Plugin architecture - Extensible installation methods")
        print("  ✅ Auto-discovery system - Find servers from multiple sources")
        print("  ✅ Health monitoring - Track server status over time")

        print("\n🌟 Key advantages over previous implementations:")
        print("  🔧 Configuration-driven instead of hardcoded patterns")
        print("  🔌 Plugin architecture for easy extension")
        print("  📊 Comprehensive status tracking and monitoring")
        print("  🔍 Multi-source discovery system")
        print("  ⚡ Concurrent processing for better performance")
        print("  🛡️ Better error handling and recovery")
        print("  📋 Standardized configuration output")

        return True
    print("❌ Setup failed during testing!")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
