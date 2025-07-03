#!/usr/bin/env python3
"""Simple MCP connection test - just establish connections"""

import asyncio
import logging
from haive.mcp.config import MCPServerConfig, MCPTransport
from haive.mcp.manager import MCPManager

logging.basicConfig(level=logging.INFO)

async def simple_connection_test():
    """Simple test to establish MCP connections"""
    
    print("🔧 SIMPLE MCP CONNECTION TEST")
    print("=" * 50)
    print("Testing basic MCP server connections...")
    print()
    
    manager = MCPManager(
        auto_health_check=False,
        connection_timeout=10.0
    )
    
    # Simple server config
    config = MCPServerConfig(
        name="filesystem",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        capabilities=["filesystem"],
        category="official"
    )
    
    print("📁 Testing filesystem server connection...")
    
    try:
        result = await manager.add_server("filesystem", config, connect_immediately=True)
        
        if result.success:
            print(f"✅ SUCCESS! Connected to filesystem server")
            print(f"   🔧 Tools count: {result.tools_count}")
            if result.tools:
                print(f"   📋 Tools: {result.tools[:3]}...")
        else:
            print(f"❌ FAILED: {result.error_message}")
            
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
    
    # Get status
    status = manager.get_all_server_status()
    print(f"\n📊 STATUS:")
    print(f"   Connected: {status['summary']['connected_servers']}")
    print(f"   Total tools: {status['summary']['total_tools']}")
    
    await manager.shutdown()
    
    if status['summary']['connected_servers'] > 0:
        print(f"\n🎉 CONNECTION TEST: SUCCESS!")
        return True
    else:
        print(f"\n⚠️  CONNECTION TEST: FAILED")
        return False

if __name__ == "__main__":
    success = asyncio.run(simple_connection_test())
    if success:
        print("✅ MCP system is working!")
    else:
        print("❌ MCP system needs debugging")