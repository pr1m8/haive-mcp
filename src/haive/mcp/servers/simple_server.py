#!/usr/bin/env python3
"""Simple MCP server that you can easily start and add servers to."""

import asyncio
import json
import logging
import subprocess
import sys
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMCPServerManager:
    """Simple manager for MCP servers."""
    
    def __init__(self):
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
    
    async def add_server(self, name: str, command: List[str], env: Dict[str, str] = None):
        """Add a new MCP server."""
        logger.info(f"🔧 Adding server: {name}")
        logger.info(f"   Command: {' '.join(command)}")
        
        try:
            # Start the server process
            process = subprocess.Popen(
                command,
                env={**subprocess.os.environ, **(env or {})},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store the server info
            self.servers[name] = {
                "command": command,
                "env": env or {},
                "status": "running",
                "pid": process.pid
            }
            self.processes[name] = process
            
            logger.info(f"✅ Server {name} started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start server {name}: {e}")
            return False
    
    def list_servers(self):
        """List all registered servers."""
        logger.info(f"📋 Registered servers ({len(self.servers)}):")
        for name, info in self.servers.items():
            status = "🟢 running" if self.is_server_running(name) else "🔴 stopped"
            logger.info(f"   {name}: {status} (PID: {info.get('pid', 'N/A')})")
    
    def is_server_running(self, name: str) -> bool:
        """Check if a server is still running."""
        if name not in self.processes:
            return False
        return self.processes[name].poll() is None
    
    def stop_server(self, name: str):
        """Stop a specific server."""
        if name in self.processes:
            logger.info(f"🛑 Stopping server: {name}")
            self.processes[name].terminate()
            del self.processes[name]
            if name in self.servers:
                self.servers[name]["status"] = "stopped"
    
    def stop_all_servers(self):
        """Stop all servers."""
        logger.info("🛑 Stopping all servers...")
        for name in list(self.processes.keys()):
            self.stop_server(name)

async def setup_basic_servers(manager: SimpleMCPServerManager):
    """Set up some basic MCP servers."""
    
    # Basic servers that should work out of the box
    basic_servers = {
        "filesystem": {
            "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
            "description": "File system operations"
        },
        "time": {
            "command": ["npx", "-y", "@modelcontextprotocol/server-time"],
            "description": "Date and time utilities"
        },
        # Uncomment if you have a GitHub token
        # "github": {
        #     "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
        #     "env": {"GITHUB_TOKEN": "your_token_here"},
        #     "description": "GitHub repository access"
        # }
    }
    
    logger.info("🚀 Setting up basic MCP servers...")
    
    for name, config in basic_servers.items():
        success = await manager.add_server(
            name, 
            config["command"], 
            config.get("env")
        )
        if success:
            logger.info(f"   ✅ {name}: {config['description']}")
        else:
            logger.info(f"   ❌ {name}: Failed to start")

async def interactive_menu(manager: SimpleMCPServerManager):
    """Interactive menu for managing servers."""
    logger.info("\n🎮 Interactive MCP Server Manager")
    logger.info("Commands:")
    logger.info("  'list' - Show all servers")
    logger.info("  'add' - Add a new server")
    logger.info("  'stop [name]' - Stop a server")
    logger.info("  'restart [name]' - Restart a server")
    logger.info("  'status' - Show system status")
    logger.info("  'help' - Show this help")
    logger.info("  'quit' - Exit")
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == "quit":
                break
            elif command == "list":
                manager.list_servers()
            elif command == "status":
                print(f"Total servers: {len(manager.servers)}")
                running = sum(1 for name in manager.servers if manager.is_server_running(name))
                print(f"Running servers: {running}")
                print(f"Stopped servers: {len(manager.servers) - running}")
            elif command == "help":
                logger.info("Available commands: list, add, stop [name], restart [name], status, help, quit")
            elif command == "add":
                print("Add a new MCP server:")
                name = input("Server name: ").strip()
                if not name:
                    print("Invalid name")
                    continue
                    
                print("Choose a preset or enter custom command:")
                print("1. Brave Search (requires API key)")
                print("2. Memory server")  
                print("3. Custom command")
                
                choice = input("Choice (1-3): ").strip()
                
                if choice == "1":
                    api_key = input("Brave API key: ").strip()
                    if api_key:
                        await manager.add_server(
                            name,
                            ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
                            {"BRAVE_API_KEY": api_key}
                        )
                elif choice == "2":
                    await manager.add_server(
                        name,
                        ["npx", "-y", "@modelcontextprotocol/server-memory"]
                    )
                elif choice == "3":
                    command = input("Command (space-separated): ").strip().split()
                    if command:
                        await manager.add_server(name, command)
                        
            elif command.startswith("stop "):
                server_name = command.replace("stop ", "").strip()
                manager.stop_server(server_name)
            elif command.startswith("restart "):
                server_name = command.replace("restart ", "").strip()
                if server_name in manager.servers:
                    # Stop the server
                    manager.stop_server(server_name)
                    # Wait a moment
                    await asyncio.sleep(1)
                    # Restart it
                    server_info = manager.servers[server_name]
                    await manager.add_server(
                        server_name, 
                        server_info["command"], 
                        server_info["env"]
                    )
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

async def main():
    """Main function."""
    logger.info("🎯 Simple MCP Server Manager")
    logger.info("This will start basic MCP servers and let you add more")
    
    # Create manager
    manager = SimpleMCPServerManager()
    
    try:
        # Set up basic servers
        await setup_basic_servers(manager)
        
        # Show status
        logger.info("\n📊 Initial Status:")
        manager.list_servers()
        
        # Start interactive menu
        await interactive_menu(manager)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    finally:
        # Clean up
        manager.stop_all_servers()
        logger.info("👋 All servers stopped. Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())