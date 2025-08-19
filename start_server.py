#!/usr/bin/env python3
"""Simple script to start the Haive MCP server and manage additional servers."""

import asyncio
import logging
from haive.mcp.manager import MCPManager
from haive.mcp.config import MCPServerConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_basic_server():
    """Start the basic MCP server with filesystem support."""
    logger.info("🚀 Starting Haive MCP Server...")
    
    # Create MCP manager
    manager = MCPManager()
    
    # Add filesystem server (basic file operations)
    filesystem_config = MCPServerConfig(
        name="filesystem",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "."]
    )
    
    try:
        # Add filesystem server
        logger.info("📁 Adding filesystem server...")
        result = await manager.add_server("filesystem", filesystem_config)
        if result.success:
            logger.info("✅ Filesystem server added successfully!")
        else:
            logger.error(f"❌ Failed to add filesystem server: {result.error_message}")
        
        # Get available tools
        tools = await manager.get_all_tools()
        logger.info(f"🛠️  Available tools: {len(tools)}")
        for tool in tools[:5]:  # Show first 5 tools
            logger.info(f"   - {tool.name}: {tool.description}")
        
        # Show server status
        status = manager.get_all_server_status()
        logger.info("📊 Server Status:")
        logger.info(f"   Connected: {status['summary']['connected_servers']}")
        logger.info(f"   Failed: {status['summary']['failed_servers']}")
        logger.info(f"   Total tools: {status['summary']['total_tools']}")
        
        return manager
        
    except Exception as e:
        logger.error(f"❌ Error starting server: {e}")
        return None

async def add_additional_servers(manager: MCPManager):
    """Add additional servers to the running manager."""
    logger.info("\n🔧 Adding additional servers...")
    
    # Example: Add more servers
    additional_servers = {
        "time": MCPServerConfig(
            name="time",
            transport="stdio", 
            command="npx",
            args=["-y", "@modelcontextprotocol/server-time"]
        ),
        # Uncomment to add GitHub server (requires GITHUB_TOKEN)
        # "github": MCPServerConfig(
        #     name="github",
        #     transport="stdio",
        #     command="npx", 
        #     args=["-y", "@modelcontextprotocol/server-github"],
        #     env={"GITHUB_TOKEN": "your_token_here"}
        # )
    }
    
    for server_name, config in additional_servers.items():
        try:
            logger.info(f"➕ Adding {server_name} server...")
            result = await manager.add_server(server_name, config)
            if result.success:
                logger.info(f"✅ {server_name} server added!")
            else:
                logger.info(f"⚠️  {server_name} server failed: {result.error_message}")
        except Exception as e:
            logger.info(f"⚠️  {server_name} server error: {e}")

async def interactive_server_manager(manager: MCPManager):
    """Interactive prompt to add more servers."""
    logger.info("\n🎮 Interactive Server Manager")
    logger.info("Available commands:")
    logger.info("  'status' - Show server status")
    logger.info("  'tools' - List available tools") 
    logger.info("  'add [server_name]' - Add a server")
    logger.info("  'reload [server_name]' - Reload a server")
    logger.info("  'quit' - Exit")
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == "quit":
                break
            elif command == "status":
                status = manager.get_all_server_status()
                print(f"Connected servers: {status['summary']['connected_servers']}")
                print(f"Failed servers: {status['summary']['failed_servers']}")
                print(f"Total tools: {status['summary']['total_tools']}")
                
            elif command == "tools":
                tools = await manager.get_all_tools()
                print(f"Available tools ({len(tools)}):")
                for tool in tools:
                    print(f"  - {tool.name}: {tool.description}")
                    
            elif command.startswith("add "):
                server_name = command.replace("add ", "").strip()
                print(f"Adding server: {server_name}")
                # You can add logic here to configure and add specific servers
                
            elif command.startswith("reload "):
                server_name = command.replace("reload ", "").strip()
                try:
                    await manager.reload_server(server_name)
                    print(f"✅ Reloaded {server_name}")
                except Exception as e:
                    print(f"❌ Failed to reload {server_name}: {e}")
                    
            else:
                print("Unknown command. Type 'quit' to exit.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

async def main():
    """Main function."""
    logger.info("🎯 Haive MCP Server Startup Script")
    
    # Start basic server
    manager = await start_basic_server()
    if not manager:
        logger.error("Failed to start basic server")
        return
    
    # Add additional servers
    await add_additional_servers(manager)
    
    # Show final status
    tools = await manager.get_all_tools()
    logger.info(f"\n🎉 Server ready with {len(tools)} tools available!")
    
    # Interactive management
    await interactive_server_manager(manager)
    
    logger.info("👋 Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())