#!/usr/bin/env python3
"""Discover what's actually available in langchain-mcp-adapters."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def discover_langchain_mcp():
    """Discover what's in the langchain-mcp-adapters package."""
    print("=== Discovering LangChain MCP Adapters ===\n")
    
    try:
        import langchain_mcp_adapters
        print(f"✅ Package location: {langchain_mcp_adapters.__file__}")
        print(f"✅ Package attributes: {dir(langchain_mcp_adapters)}\n")
    except ImportError as e:
        print(f"❌ Failed to import langchain_mcp_adapters: {e}")
        return
    
    # Check client module
    print("=== langchain_mcp_adapters.client ===")
    try:
        from langchain_mcp_adapters import client
        print(f"✅ Client module attributes: {[attr for attr in dir(client) if not attr.startswith('_')]}\n")
        
        # Check specific imports
        for item in dir(client):
            if not item.startswith('_'):
                try:
                    obj = getattr(client, item)
                    print(f"  - {item}: {type(obj).__name__}")
                    if hasattr(obj, '__doc__') and obj.__doc__:
                        first_line = obj.__doc__.split('\n')[0].strip()
                        if first_line:
                            print(f"    {first_line}")
                except Exception as e:
                    print(f"  - {item}: Error - {e}")
        
    except ImportError as e:
        print(f"❌ Failed to import client: {e}")
    
    # Check if mcp package exists
    print("\n=== mcp package ===")
    try:
        import mcp
        print(f"✅ mcp package found: {mcp.__file__}")
        print(f"✅ mcp attributes: {[attr for attr in dir(mcp) if not attr.startswith('_')]}")
        
        # Check mcp.client.stdio
        print("\n=== mcp.client.stdio ===")
        try:
            from mcp.client import stdio
            print(f"✅ stdio module attributes: {[attr for attr in dir(stdio) if not attr.startswith('_')]}")
            
            # Look for key components
            for item in ['StdioServerParameters', 'stdio_client', 'StdioClient']:
                if hasattr(stdio, item):
                    print(f"  ✓ Found {item}")
                else:
                    print(f"  ✗ Missing {item}")
                    
        except ImportError as e:
            print(f"❌ Failed to import mcp.client.stdio: {e}")
            
    except ImportError as e:
        print(f"❌ mcp package not found: {e}")
        print("  Install with: pip install mcp")
    
    # Check actual usage pattern
    print("\n=== Checking actual usage pattern ===")
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        print("✅ Found MultiServerMCPClient")
        
        # Check its methods
        print(f"   Methods: {[m for m in dir(MultiServerMCPClient) if not m.startswith('_') and callable(getattr(MultiServerMCPClient, m))]}")
        
    except ImportError as e:
        print(f"❌ MultiServerMCPClient not found: {e}")
    
    # Check for tools
    print("\n=== Checking for tool utilities ===")
    try:
        from langchain_mcp_adapters.client import load_mcp_tools
        print("✅ Found load_mcp_tools function")
    except ImportError:
        print("❌ load_mcp_tools not found")
        
    try:
        from langchain_mcp_tools import create_mcp_tools
        print("✅ Found create_mcp_tools from langchain_mcp_tools")
    except ImportError:
        print("❌ langchain_mcp_tools not available")


def check_correct_usage():
    """Check the correct usage pattern based on what we found."""
    print("\n\n=== Correct Usage Pattern ===\n")
    
    try:
        # Import what actually exists
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from mcp.client.stdio import StdioServerParameters, stdio_client
        
        print("✅ Correct imports found!")
        print("\nExample usage:")
        print("""
# 1. Create server parameters
server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem"],
    env=None
)

# 2. Use stdio_client to connect
async with stdio_client(server_params) as (read, write):
    # Use read/write for communication
    pass

# 3. Or use MultiServerMCPClient for multiple servers
client = MultiServerMCPClient({
    "filesystem": filesystem_client,
    "github": github_client
})
""")
        
    except ImportError as e:
        print(f"❌ Failed to import correct components: {e}")


if __name__ == "__main__":
    discover_langchain_mcp()
    check_correct_usage()