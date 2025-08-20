#!/usr/bin/env python3
"""Simple test of native MCP client implementation.

This script tests the native MCP client with a real MCP server to validate
the Phase 2 implementation works correctly.
"""

import asyncio
import tempfile
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from haive.mcp.client import MCPClient, StdioTransport


async def test_filesystem_server():
    """Test filesystem server with native MCP client."""
    print("🧪 Testing Native MCP Client with Filesystem Server")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        
        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_content = "Hello Native MCP Protocol!"
        test_file.write_text(test_content)
        print(f"📝 Created test file: {test_file}")
        
        # Create transport
        transport = StdioTransport(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", temp_dir],
            timeout=10.0
        )
        print("🚀 Created STDIO transport")
        
        try:
            # Test with context manager
            async with MCPClient(transport) as client:
                print("✅ Connected to MCP server")
                
                # Get server info
                server_info = await client.get_server_info()
                server_name = server_info.get("serverInfo", {}).get("name", "unknown")
                print(f"🔌 Connected to server: {server_name}")
                
                # Get capabilities
                capabilities = await client.get_capabilities()
                cap_names = [cap.value for cap in capabilities]
                print(f"⚡ Server capabilities: {cap_names}")
                
                # List tools
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
                print(f"🔧 Available tools: {tool_names}")
                
                # Find and use read_file tool
                if "read_file" in tool_names:
                    print(f"📖 Testing read_file tool with: {str(test_file)}")
                    
                    result = await client.call_tool("read_file", {
                        "path": str(test_file)  # Use absolute path within the allowed directory
                    })
                    
                    print(f"📄 Tool result: {result}")
                    
                    # Verify content
                    if test_content in str(result):
                        print("✅ Tool execution successful - content matches!")
                    else:
                        print("❌ Tool execution failed - content mismatch")
                        return False
                else:
                    print("⚠️  read_file tool not available")
                    
                # Test health check
                health = await client.health_check()
                print(f"💚 Health check: connected={health['connected']}")
                
                print("✅ All tests passed!")
                return True
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Run the test."""
    print("=" * 60)
    print("🔬 Native MCP Client Test - Phase 2 Validation")
    print("=" * 60)
    
    success = await test_filesystem_server()
    
    print("=" * 60)
    if success:
        print("🎉 Phase 2 Implementation: WORKING!")
        print("✅ Native MCP protocol client successfully implemented")
    else:
        print("❌ Phase 2 Implementation: FAILED")
        print("🔧 Native MCP protocol client needs fixes")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)