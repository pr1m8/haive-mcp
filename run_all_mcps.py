#!/usr/bin/env python3
"""RUN ALL MCPs - Complete setup with resources, prompts, tools, and reliability"""

import asyncio
import sys
from pathlib import Path

# Import our modules
from production_mcp_runner import production_mcp_runner
from ensure_reliability import MCPReliabilityMonitor

async def run_all_mcps():
    """Complete MCP setup with all features"""
    
    print("🚀 COMPLETE MCP ECOSYSTEM SETUP")
    print("=" * 60)
    print("Setting up ALL MCP servers with:")
    print("   🛠️  Tool discovery")
    print("   📚 Resource prompts") 
    print("   🛡️  Reliability monitoring")
    print("   🔄 Auto-recovery")
    print("   📊 Health tracking")
    print()
    
    # Step 1: Production setup
    print("STEP 1: Production MCP Setup")
    print("-" * 30)
    manager, results = await production_mcp_runner()
    
    # Step 2: Start reliability monitoring
    print("\nSTEP 2: Reliability Monitoring")
    print("-" * 30)
    monitor = MCPReliabilityMonitor(manager, check_interval=60.0)  # Check every minute
    
    # Step 3: Interactive mode
    print("\nSTEP 3: Interactive MCP System")
    print("-" * 30)
    print("🎯 MCP Ecosystem is now running!")
    print()
    print("Available commands:")
    print("   'status' - Show server status")
    print("   'tools' - List all available tools")
    print("   'resources' - Show resource templates")
    print("   'stats' - Show reliability statistics")
    print("   'quit' - Shutdown system")
    print()
    
    # Start monitoring in background
    monitor_task = asyncio.create_task(monitor.start_monitoring())
    
    try:
        while True:
            command = input("MCP> ").strip().lower()
            
            if command == 'quit':
                break
            elif command == 'status':
                await show_status(manager)
            elif command == 'tools':
                await show_tools(manager, results)
            elif command == 'resources':
                await show_resources(results)
            elif command == 'stats':
                show_reliability_stats(monitor)
            elif command == 'help':
                print("Commands: status, tools, resources, stats, quit")
            else:
                print("Unknown command. Type 'help' for available commands.")
                
    except KeyboardInterrupt:
        print("\n⚠️  Shutting down...")
    
    finally:
        # Cleanup
        monitor.stop_monitoring()
        monitor_task.cancel()
        await manager.shutdown()
        print("✅ MCP ecosystem shutdown complete")

async def show_status(manager):
    """Show current server status"""
    status = manager.get_all_server_status()
    
    print(f"\n📊 MCP SERVER STATUS:")
    print(f"   📈 Total servers: {status['summary']['total_servers']}")
    print(f"   ✅ Connected: {status['summary']['connected_servers']}")
    print(f"   ❌ Failed: {status['summary']['failed_servers']}")
    print(f"   🔧 Total tools: {status['summary']['total_tools']}")
    
    print(f"\n📋 Server Details:")
    for name, info in status['servers'].items():
        status_icon = "✅" if info['status'] == 'connected' else "❌"
        print(f"   {status_icon} {name}: {len(info['tools'])} tools ({info['status']})")

async def show_tools(manager, results):
    """Show all available tools"""
    print(f"\n🛠️  AVAILABLE TOOLS:")
    
    total_tools = 0
    for server_name, tools in results['tools_discovered'].items():
        print(f"\n📂 {server_name} ({len(tools)} tools):")
        for tool in tools[:10]:  # Show first 10 tools
            print(f"   • {tool}")
        if len(tools) > 10:
            print(f"   • ... and {len(tools) - 10} more")
        total_tools += len(tools)
    
    print(f"\n📊 Total: {total_tools} tools across all servers")

async def show_resources(results):
    """Show resource templates"""
    print(f"\n📚 RESOURCE TEMPLATES:")
    
    # This would be loaded from the production config
    from production_mcp_runner import production_mcp_runner
    # Show resource templates from successful servers
    resource_examples = {
        "filesystem": ["file:///tmp/example.txt", "directory:///home/user"],
        "github": ["github://repo/owner/name", "github://issue/owner/repo/123"],
        "brave_search": ["search://python tutorials", "web://https://example.com"],
        "puppeteer": ["webpage://https://example.com", "screenshot://https://example.com"],
        "memory": ["memory://entity/user123", "memory://graph/knowledge"]
    }
    
    for server, examples in resource_examples.items():
        if server in results['successful']:
            print(f"\n📂 {server}:")
            for example in examples:
                print(f"   • {example}")

def show_reliability_stats(monitor):
    """Show reliability statistics"""
    stats = monitor.get_reliability_stats()
    
    print(f"\n🛡️  RELIABILITY STATISTICS:")
    print(f"   ⏱️  Uptime: {stats['uptime_minutes']:.1f} minutes")
    print(f"   🔍 Health checks: {stats['total_checks']}")
    print(f"   ❌ Failures detected: {stats['failures_detected']}")
    print(f"   🔄 Auto-recoveries: {stats['auto_recoveries']}")
    print(f"   📈 Failure rate: {stats['failure_rate']*100:.2f}%")
    print(f"   🎯 Recovery rate: {stats['recovery_rate']*100:.2f}%")

if __name__ == "__main__":
    print("🚀 STARTING COMPLETE MCP ECOSYSTEM")
    print("This will set up all MCP servers with full reliability monitoring")
    print()
    
    try:
        asyncio.run(run_all_mcps())
    except KeyboardInterrupt:
        print("\n⚠️  Startup interrupted")
    except Exception as e:
        print(f"\n💥 Startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)