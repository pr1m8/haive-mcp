#!/usr/bin/env python3
"""Non-interactive MCP server manager that avoids EOF errors."""

import subprocess
import json
import time
import sys
import os
from typing import Dict, List, Optional
import signal
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMCPServerManager:
    """Simple manager for MCP servers."""
    
    def __init__(self):
        self.servers: Dict[str, dict] = {}
        self.available_servers = {
            "filesystem": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
                "description": "File system operations"
            },
            "time": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-time"],
                "description": "Date and time utilities"
            },
            "memory": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
                "description": "Persistent memory storage"
            }
        }
    
    def start_server(self, name: str) -> bool:
        """Start an MCP server by name."""
        if name not in self.available_servers:
            logger.error(f"Unknown server: {name}")
            return False
        
        if name in self.servers:
            logger.warning(f"Server {name} is already running")
            return True
        
        server_config = self.available_servers[name]
        
        try:
            logger.info(f"Starting {name} server...")
            logger.info(f"Command: {' '.join(server_config['command'])}")
            
            # Start the server process
            process = subprocess.Popen(
                server_config["command"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                self.servers[name] = {
                    "process": process,
                    "pid": process.pid,
                    "command": server_config["command"]
                }
                logger.info(f"✅ {name} server started successfully (PID: {process.pid})")
                return True
            else:
                # Process died immediately
                stdout, stderr = process.communicate()
                logger.error(f"❌ {name} server failed to start")
                if stdout:
                    logger.error(f"stdout: {stdout}")
                if stderr:
                    logger.error(f"stderr: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start {name} server: {e}")
            return False
    
    def stop_server(self, name: str) -> bool:
        """Stop a server by name."""
        if name not in self.servers:
            logger.warning(f"Server {name} is not running")
            return False
        
        try:
            process = self.servers[name]["process"]
            logger.info(f"Stopping {name} server (PID: {self.servers[name]['pid']})...")
            
            # Try graceful termination first
            process.terminate()
            
            # Wait up to 5 seconds for termination
            try:
                process.wait(timeout=5)
                logger.info(f"✅ {name} server stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if needed
                logger.warning(f"Force killing {name} server...")
                process.kill()
                process.wait()
                logger.info(f"✅ {name} server force stopped")
            
            del self.servers[name]
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop {name} server: {e}")
            return False
    
    def stop_all_servers(self):
        """Stop all running servers."""
        logger.info("Stopping all servers...")
        server_names = list(self.servers.keys())
        for name in server_names:
            self.stop_server(name)
    
    def show_status(self):
        """Show server status."""
        logger.info("\n=== MCP Server Status ===")
        if not self.servers:
            logger.info("No servers running")
        else:
            for name, info in self.servers.items():
                process = info["process"]
                # Check if still running
                if process.poll() is None:
                    logger.info(f"✅ {name}: PID {info['pid']} (running)")
                else:
                    logger.info(f"❌ {name}: PID {info['pid']} (stopped)")
    
    def run_non_interactive(self):
        """Run servers in non-interactive mode."""
        logger.info("Starting MCP Server Manager (non-interactive mode)...")
        logger.info("This will start MCP servers and keep them running.")
        
        # Start default servers
        default_servers = ["filesystem", "time"]
        
        logger.info(f"\nStarting default servers: {', '.join(default_servers)}")
        
        for server_name in default_servers:
            if self.start_server(server_name):
                logger.info(f"✅ {server_name} server started successfully")
            else:
                logger.error(f"❌ Failed to start {server_name} server")
        
        self.show_status()
        
        # Set up signal handlers
        def signal_handler(signum, frame):
            logger.info("\n⚠️  Received interrupt signal")
            self.stop_all_servers()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("\n💡 Servers are running. Press Ctrl+C to stop.")
        logger.info("📊 Status will be updated every 30 seconds.\n")
        
        try:
            # Keep running and show status periodically
            while True:
                time.sleep(30)
                
                # Check server health
                for name, info in list(self.servers.items()):
                    process = info["process"]
                    if process.poll() is not None:
                        logger.warning(f"⚠️  Server {name} has stopped unexpectedly")
                        del self.servers[name]
                
                self.show_status()
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interrupted by user")
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            logger.info("\nShutting down servers...")
            self.stop_all_servers()
            logger.info("All servers stopped. Goodbye!")

if __name__ == "__main__":
    # Check if npx is available
    try:
        subprocess.run(["npx", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("❌ 'npx' command not found. Please install Node.js and npm.")
        sys.exit(1)
    
    manager = SimpleMCPServerManager()
    manager.run_non_interactive()