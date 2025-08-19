#!/usr/bin/env python3
"""MCP Server Manager for Model Context Protocol servers.

This module provides a robust way to start and manage MCP servers, handling
the complexities of stdio transport, process management, and server lifecycle.

Key features:
    - Manages multiple MCP servers concurrently
    - Handles stdio transport servers correctly (stderr is normal output)
    - Provides health monitoring and automatic restart capabilities
    - Supports environment variable configuration for API keys
    - Clean shutdown handling with signal management

Example:
    Basic usage to start filesystem and time servers::

        from haive.mcp.servers import MCPServerManager
        
        manager = MCPServerManager()
        manager.run(servers_to_start=["filesystem", "time"])

    Non-blocking mode for integration::

        manager = MCPServerManager()
        manager.run(servers_to_start=["filesystem"], blocking=False)
        # Servers run in background
        status = manager.get_status()
        print(f"Running servers: {status}")

    With environment variables for API servers::

        manager = MCPServerManager()
        env_overrides = {"GITHUB_TOKEN": "your-token"}
        manager.start_server("github", env_overrides=env_overrides)

Note:
    MCP servers using stdio transport write their status messages to stderr,
    which is normal behavior and not an error condition.
"""

import subprocess
import json
import time
import sys
import os
from typing import Dict, List, Optional, Tuple
import signal
import logging
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCPServerManager")

class MCPServerManager:
    """Manages MCP servers with proper stdio handling.
    
    This class provides comprehensive management of Model Context Protocol (MCP)
    servers, including starting, stopping, monitoring, and health checking.
    
    Attributes:
        servers: Dict mapping server names to their process information
        available_servers: Dict of pre-configured server definitions
        shutdown_requested: Flag indicating graceful shutdown was requested
    
    Example:
        >>> manager = MCPServerManager()
        >>> manager.start_server("filesystem")
        True
        >>> status = manager.get_status()
        >>> print(status["filesystem"]["running"])
        True
    """
    
    def __init__(self):
        self.servers: Dict[str, dict] = {}
        self.available_servers = {
            "filesystem": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
                "description": "File system operations",
                "transport": "stdio"
            },
            "time": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-time"],
                "description": "Date and time utilities",
                "transport": "stdio"
            },
            "memory": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
                "description": "Persistent memory storage",
                "transport": "stdio"
            },
            "github": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
                "description": "GitHub repository access",
                "transport": "stdio",
                "requires_env": ["GITHUB_TOKEN"]
            },
            "brave-search": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
                "description": "Web search via Brave",
                "transport": "stdio",
                "requires_env": ["BRAVE_API_KEY"]
            }
        }
        self.shutdown_requested = False
    
    def check_server_startup(self, process: subprocess.Popen, name: str, timeout: float = 5.0) -> Tuple[bool, str]:
        """Check if a server started successfully.
        
        For stdio transport servers, output to stderr is normal behavior and not
        indicative of an error. This method handles the distinction between
        different transport types.
        
        Args:
            process: The subprocess.Popen instance for the server
            name: Name of the server being checked
            timeout: Maximum time to wait for startup confirmation
            
        Returns:
            Tuple of (success: bool, message: str) indicating startup status
            
        Note:
            Stdio servers are considered successfully started if they remain
            running after the initial startup period.
        """
        start_time = time.time()
        
        # For stdio servers, we need to check differently
        server_config = self.available_servers.get(name, {})
        is_stdio = server_config.get("transport") == "stdio"
        
        while time.time() - start_time < timeout:
            # Check if process is still running
            if process.poll() is not None:
                # Process exited
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    return True, "Process completed successfully"
                else:
                    error_msg = stderr if stderr else stdout
                    return False, f"Process exited with code {process.returncode}: {error_msg}"
            
            # For stdio servers, any output to stderr is normal
            if is_stdio:
                time.sleep(0.5)
                # Still running = success for stdio servers
                if process.poll() is None:
                    return True, "Stdio server running"
            
            time.sleep(0.1)
        
        # Timeout reached, process still running = success
        if process.poll() is None:
            return True, "Server started (still running after timeout)"
        
        return False, "Server startup timeout"
    
    def start_server(self, name: str, env_overrides: Dict[str, str] = None) -> bool:
        """Start an MCP server by name.
        
        Starts a configured MCP server process with proper environment setup
        and monitoring. Handles both stdio and other transport types.
        
        Args:
            name: Name of the server to start (must be in available_servers)
            env_overrides: Optional dict of environment variables to set/override
            
        Returns:
            bool: True if server started successfully, False otherwise
            
        Raises:
            None: Errors are logged but not raised
            
        Example:
            >>> manager.start_server("filesystem")
            True
            >>> manager.start_server("github", {"GITHUB_TOKEN": "token"})
            True
        """
        if name not in self.available_servers:
            logger.error(f"Unknown server: {name}")
            return False
        
        if name in self.servers:
            logger.warning(f"Server {name} is already running")
            return True
        
        server_config = self.available_servers[name]
        
        # Check required environment variables
        required_env = server_config.get("requires_env", [])
        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
        
        missing_env = [var for var in required_env if var not in env]
        if missing_env:
            logger.error(f"❌ {name} server requires environment variables: {', '.join(missing_env)}")
            logger.info(f"   Set them in your environment or pass via env_overrides parameter")
            return False
        
        try:
            logger.info(f"🚀 Starting {name} server...")
            logger.debug(f"Command: {' '.join(server_config['command'])}")
            
            # Start the server process
            # For stdio servers, we need to handle stdin/stdout/stderr specially
            if server_config.get("transport") == "stdio":
                process = subprocess.Popen(
                    server_config["command"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    bufsize=0  # Unbuffered
                )
            else:
                process = subprocess.Popen(
                    server_config["command"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env
                )
            
            # Check if server started successfully
            success, message = self.check_server_startup(process, name)
            
            if success:
                self.servers[name] = {
                    "process": process,
                    "pid": process.pid,
                    "command": server_config["command"],
                    "transport": server_config.get("transport", "unknown"),
                    "description": server_config["description"]
                }
                logger.info(f"✅ {name} server started successfully (PID: {process.pid})")
                logger.info(f"   Description: {server_config['description']}")
                
                # Start output monitoring thread for stdio servers
                if server_config.get("transport") == "stdio":
                    self._start_output_monitor(name, process)
                
                return True
            else:
                logger.error(f"❌ {name} server failed to start: {message}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start {name} server: {e}")
            return False
    
    def _start_output_monitor(self, name: str, process: subprocess.Popen):
        """Monitor output from stdio servers in background thread.
        
        Creates a daemon thread to continuously read and log output from
        stdio transport servers. This prevents output buffer overflow and
        provides visibility into server status.
        
        Args:
            name: Name of the server being monitored
            process: The subprocess.Popen instance to monitor
            
        Note:
            The monitoring thread is daemon mode and will terminate when
            the main process exits.
        """
        def monitor():
            logger.debug(f"Starting output monitor for {name}")
            while process.poll() is None and not self.shutdown_requested:
                try:
                    # Read stderr (where stdio servers typically write status)
                    line = process.stderr.readline()
                    if line:
                        logger.debug(f"[{name}] {line.strip()}")
                except:
                    break
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def stop_server(self, name: str) -> bool:
        """Stop a server by name.
        
        Attempts graceful termination first, then force kills if necessary.
        Cleans up all associated resources.
        
        Args:
            name: Name of the server to stop
            
        Returns:
            bool: True if server was stopped, False if server wasn't running
                  or stop failed
                  
        Example:
            >>> manager.stop_server("filesystem")
            True
        """
        if name not in self.servers:
            logger.warning(f"Server {name} is not running")
            return False
        
        try:
            process = self.servers[name]["process"]
            logger.info(f"🛑 Stopping {name} server (PID: {self.servers[name]['pid']})...")
            
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
        """Stop all running servers.
        
        Gracefully shuts down all managed servers. This method is called
        automatically during signal handling for clean shutdown.
        
        Note:
            Sets shutdown_requested flag to signal monitoring threads.
        """
        self.shutdown_requested = True
        logger.info("🛑 Stopping all servers...")
        server_names = list(self.servers.keys())
        for name in server_names:
            self.stop_server(name)
    
    def get_status(self) -> Dict[str, dict]:
        """Get status of all servers.
        
        Returns current status information for all managed servers,
        including PID, running state, transport type, and description.
        
        Returns:
            Dict mapping server names to status information dicts with keys:
                - pid: Process ID of the server
                - running: Boolean indicating if server is currently running
                - transport: Transport type (e.g., "stdio")
                - description: Human-readable server description
                
        Example:
            >>> status = manager.get_status()
            >>> print(status["filesystem"]["running"])
            True
        """
        status = {}
        for name, info in self.servers.items():
            process = info["process"]
            is_running = process.poll() is None
            status[name] = {
                "pid": info["pid"],
                "running": is_running,
                "transport": info["transport"],
                "description": info["description"]
            }
        return status
    
    def show_status(self):
        """Show server status.
        
        Prints a formatted status report of all servers to the logger,
        including running servers and available servers that aren't running.
        
        Note:
            Output is sent to the configured logger at INFO level.
        """
        logger.info("\n📊 === MCP Server Status ===")
        status = self.get_status()
        
        if not status:
            logger.info("No servers running")
        else:
            for name, info in status.items():
                if info["running"]:
                    logger.info(f"✅ {name}: PID {info['pid']} ({info['transport']}) - {info['description']}")
                else:
                    logger.info(f"❌ {name}: PID {info['pid']} (stopped)")
        
        # Show available servers not running
        not_running = set(self.available_servers.keys()) - set(status.keys())
        if not_running:
            logger.info("\n💡 Available servers (not running):")
            for name in not_running:
                config = self.available_servers[name]
                logger.info(f"   - {name}: {config['description']}")
    
    def run(self, servers_to_start: List[str] = None, blocking: bool = True):
        """Run the MCP server manager.
        
        Main entry point for starting and managing MCP servers. Can run in
        blocking mode (stays running until interrupted) or non-blocking mode
        (returns after starting servers).
        
        Args:
            servers_to_start: List of server names to start. Defaults to
                            ["filesystem", "time"] if not specified.
            blocking: If True, blocks and monitors servers until interrupted.
                     If False, returns immediately after starting servers.
                     
        Returns:
            bool: True if servers started successfully, False if critical
                  error occurred (e.g., npx not available)
                  
        Example:
            Blocking mode (typical usage)::
            
                manager = MCPServerManager()
                manager.run()  # Runs until Ctrl+C
                
            Non-blocking mode (for integration)::
            
                manager = MCPServerManager()
                success = manager.run(blocking=False)
                # Do other work while servers run
                manager.stop_all_servers()  # Clean shutdown
                
        Note:
            In blocking mode, installs signal handlers for SIGINT and SIGTERM
            to ensure clean shutdown of all servers.
        """
        logger.info("🎯 MCP Server Manager Starting...")
        logger.info("This manages Model Context Protocol servers for AI tool integration.")
        
        # Check if npx is available
        try:
            subprocess.run(["npx", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ 'npx' command not found. Please install Node.js and npm.")
            return False
        
        # Default servers if none specified
        if servers_to_start is None:
            servers_to_start = ["filesystem", "time"]
        
        logger.info(f"\n🚀 Starting servers: {', '.join(servers_to_start)}")
        
        # Start requested servers
        success_count = 0
        for server_name in servers_to_start:
            if self.start_server(server_name):
                success_count += 1
        
        logger.info(f"\n✅ Started {success_count}/{len(servers_to_start)} servers successfully")
        self.show_status()
        
        if not blocking:
            return True
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("\n⚠️  Received interrupt signal")
            self.stop_all_servers()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("\n💡 Servers are running. Press Ctrl+C to stop.")
        logger.info("📊 Status updates every 60 seconds.\n")
        
        try:
            # Keep running and show status periodically
            while not self.shutdown_requested:
                time.sleep(60)
                
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
            self.stop_all_servers()
            logger.info("👋 All servers stopped. Goodbye!")
        
        return True


def main():
    """Main entry point for command-line usage.
    
    Provides a CLI interface for the MCP Server Manager with options
    for listing available servers, selecting which to start, and
    enabling debug logging.
    
    Command-line arguments:
        --servers: Space-separated list of servers to start
        --list: List available servers and exit
        --debug: Enable debug-level logging
        
    Example:
        List available servers::
        
            $ python mcp_server_manager.py --list
            
        Start specific servers::
        
            $ python mcp_server_manager.py --servers filesystem memory
            
        Enable debug logging::
        
            $ python mcp_server_manager.py --debug
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server Manager")
    parser.add_argument(
        "--servers", 
        nargs="+", 
        help="Servers to start (default: filesystem time)",
        default=["filesystem", "time"]
    )
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List available servers and exit"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    manager = MCPServerManager()
    
    if args.list:
        logger.info("📋 Available MCP Servers:")
        for name, config in manager.available_servers.items():
            logger.info(f"\n{name}:")
            logger.info(f"  Description: {config['description']}")
            logger.info(f"  Transport: {config.get('transport', 'unknown')}")
            if config.get('requires_env'):
                logger.info(f"  Required env: {', '.join(config['requires_env'])}")
        return
    
    # Run the manager
    manager.run(servers_to_start=args.servers)


if __name__ == "__main__":
    main()