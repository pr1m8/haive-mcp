#!/usr/bin/env python3
"""Minimal MCP test - direct connection to verify setup"""

import asyncio
from langchain_mcp_adapters.client import stdio_client
from mcp.client.stdio import StdioServerParameters

async def minimal_test():
    """Minimal test with direct MCP connection"""
    
    print("🔧 MINIMAL MCP TEST")
    print("=" * 30)
    
    try:
        # Test filesystem server
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            env={},
        )
        
        print("📁 Connecting to filesystem server...")
        
        # Try connection with timeout
        async with asyncio.timeout(10):
            async with stdio_client(server_params) as session:
                print("✅ Connected!")
                
                # Try to list tools
                try:
                    from langchain_mcp_adapters.client import load_mcp_tools
                    tools = await load_mcp_tools(session)
                    print(f"🔧 Found {len(tools)} tools")
                    for tool in tools[:3]:
                        print(f"   • {tool.name}")
                except Exception as e:
                    print(f"⚠️  Could not load tools: {e}")
                
                print("🎉 TEST PASSED!")
                return True
                
    except asyncio.TimeoutError:
        print("⏰ Connection timed out")
        return False
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(minimal_test())
    if success:
        print("\n✅ MCP connection works!")
    else:
        print("\n❌ MCP connection failed")