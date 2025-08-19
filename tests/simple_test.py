#!/usr/bin/env python3
"""Simple test to validate our MCP setup."""

import subprocess
import sys
from pathlib import Path

def test_files_exist():
    """Test that key files exist."""
    files_to_check = [
        'src/haive/mcp/installer/bulk_installer.py',
        'src/haive/mcp/discovery/installed_servers.py', 
        'src/haive/mcp/servers/mcp_server_manager.py',
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")

def test_bulk_installer_help():
    """Test bulk installer help."""
    try:
        result = subprocess.run([
            sys.executable, 'src/haive/mcp/installer/bulk_installer.py', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Bulk installer CLI works")
            return True
        else:
            print(f"❌ Bulk installer failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error testing bulk installer: {e}")
        return False

def test_discovery_help():
    """Test discovery help."""
    try:
        result = subprocess.run([
            sys.executable, 'src/haive/mcp/discovery/installed_servers.py', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Discovery CLI works")
            return True
        else:
            print(f"❌ Discovery failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error testing discovery: {e}")
        return False

def main():
    """Run simple tests."""
    print("🧪 Running Simple MCP Tests")
    print("=" * 40)
    
    test_files_exist()
    print()
    
    bulk_ok = test_bulk_installer_help()
    discovery_ok = test_discovery_help()
    
    print()
    if bulk_ok and discovery_ok:
        print("🎉 All basic tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())