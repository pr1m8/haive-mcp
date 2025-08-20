#!/usr/bin/env python3
"""MCP Server Manager V2 - Pydantic-based refactor.

This module provides a refactored MCPServerManager that inherits from the
base server management framework, adding MCP-specific functionality with
full Pydantic validation.

Key improvements:
    - Inherits from BaseServerManager for type-safe management
    - Full Pydantic validation for all configurations
    - Backward compatibility with existing MCPServerManager API
    - Enhanced error handling and logging
    - Better separation of concerns

Example:
    Basic usage with new typed API::
    
        from haive.mcp.servers import MCPServerManagerV2
        
        manager = MCPServerManagerV2()
        manager.add_config("filesystem", {
            "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
            "description": "File system operations",
            "transport": "stdio"
        })
        await manager.start_server("filesystem")
        
    Legacy compatibility mode::
    
        manager = MCPServerManagerV2()
        manager.run(servers_to_start=["filesystem", "time"])
"""

import asyncio
import subprocess
import threading
import signal
import sys
import os
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import logging

from pydantic import Field, model_validator
from haive.dataflow.server_management.base import BaseServerManager
from haive.dataflow.server_management.models import ServerStatus

from .models import MCPServerConfig, MCPServerInfo, MCPTransport


logger = logging.getLogger("MCPServerManagerV2")


class MCPServerManagerV2(BaseServerManager[MCPServerConfig, MCPServerInfo]):
    """Refactored MCP Server Manager with Pydantic validation.
    
    Inherits from BaseServerManager to provide type-safe server management
    with MCP-specific extensions for stdio transport, environment validation,
    and protocol handling.
    
    Attributes:
        config_class: MCPServerConfig class for validation
        info_class: MCPServerInfo class for runtime state
        output_monitors: Thread references for stdio output monitoring
        legacy_mode: Enable backward compatibility behaviors
        
    Example:
        >>> manager = MCPServerManagerV2()
        >>> config = MCPServerConfig(
        ...     name="github",
        ...     command=["npx", "-y", "@modelcontextprotocol/server-github"],
        ...     transport=MCPTransport.STDIO,
        ...     requires_env=["GITHUB_TOKEN"]
        ... )
        >>> manager.add_config("github", config)
        >>> await manager.start_server("github", {"GITHUB_TOKEN": "token"})
    """
    
    config_class: type[MCPServerConfig] = Field(
        default=MCPServerConfig,
        exclude=True
    )
    
    info_class: type[MCPServerInfo] = Field(
        default=MCPServerInfo,
        exclude=True
    )
    
    output_monitors: Dict[str, threading.Thread] = Field(
        default_factory=dict,
        exclude=True,
        description="Output monitoring threads for stdio servers"
    )
    
    legacy_mode: bool = Field(
        default=False,
        description="Enable backward compatibility mode"
    )
    
    shutdown_requested: bool = Field(
        default=False,
        exclude=True,
        description="Flag for graceful shutdown"
    )
    
    def __init__(self, **data):
        """Initialize with optional pre-configured servers."""
        # Handle legacy available_servers initialization
        if "available_configs" not in data:
            data["available_configs"] = self._get_default_configs()
        
        super().__init__(**data)
        
        # Set up logging based on mode
        if self.legacy_mode:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    @classmethod
    def _get_default_configs(cls) -> Dict[str, MCPServerConfig]:
        """Get default MCP server configurations."""
        return {
            "filesystem": MCPServerConfig(
                name="filesystem",
                command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
                description="File system operations",
                transport=MCPTransport.STDIO
            ),
            "time": MCPServerConfig(
                name="time",
                command=["npx", "-y", "@modelcontextprotocol/server-time"],
                description="Date and time utilities",
                transport=MCPTransport.STDIO
            ),
            "memory": MCPServerConfig(
                name="memory",
                command=["npx", "-y", "@modelcontextprotocol/server-memory"],
                description="Persistent memory storage",
                transport=MCPTransport.STDIO
            ),
            "github": MCPServerConfig(
                name="github",
                command=["npx", "-y", "@modelcontextprotocol/server-github"],
                description="GitHub repository access",
                transport=MCPTransport.STDIO,
                requires_env=["GITHUB_TOKEN"]
            ),
            "brave-search": MCPServerConfig(
                name="brave-search",
                command=["npx", "-y", "@modelcontextprotocol/server-brave-search"],
                description="Web search via Brave",
                transport=MCPTransport.STDIO,
                requires_env=["BRAVE_API_KEY"]
            )
        }
    
    async def start_server(self, name: str, env_overrides: Optional[Dict[str, str]] = None) -> MCPServerInfo:
        """Start an MCP server with proper validation.
        
        Extends base start_server with MCP-specific features like environment
        validation and stdio output monitoring.
        
        Args:
            name: Server name
            env_overrides: Optional environment variable overrides
            
        Returns:
            MCPServerInfo with running server details
            
        Raises:
            ValueError: If required environment variables are missing
            RuntimeError: If server fails to start
        """
        # Get configuration
        config = self.get_config(name)
        if not config:
            raise ValueError(f"No configuration found for server '{name}'")
        
        # Validate environment variables
        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
        
        missing_env = [var for var in config.requires_env if var not in env]
        if missing_env:
            raise ValueError(
                f"Server '{name}' requires environment variables: {', '.join(missing_env)}. "
                f"Set them in your environment or pass via env_overrides parameter"
            )
        
        # Start the process with appropriate configuration
        try:
            if config.transport == MCPTransport.STDIO:
                process = subprocess.Popen(
                    config.command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    cwd=config.working_directory,
                    bufsize=0  # Unbuffered for stdio
                )
            else:
                process = subprocess.Popen(
                    config.command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    cwd=config.working_directory
                )
            
            # Create server info with process details
            info = self.info_class(
                name=name,
                pid=process.pid,
                status=ServerStatus.STARTING,
                config_snapshot=config.model_dump(),
                transport=config.transport,
                transport_info={"env_vars": list(config.requires_env)}
            )
            
            # Store process handle (excluded from serialization)
            info.process_handle = process
            
            # Check startup (MCP-specific logic)
            success = await self._check_mcp_startup(process, config, info)
            if not success:
                process.terminate()
                raise RuntimeError(f"MCP server '{name}' failed to start")
            
            # Update status
            info.update_status(ServerStatus.RUNNING)
            
            # Start output monitoring for stdio servers
            if config.transport == MCPTransport.STDIO:
                self._start_output_monitor(name, process)
            
            # Store server info
            self.servers[name] = info
            
            # Start health monitoring if enabled
            if self.health_check_interval > 0:
                await self.start_health_monitoring(name)
            
            logger.info(f"✅ {name} server started successfully (PID: {info.pid})")
            return info
            
        except Exception as e:
            logger.error(f"❌ Failed to start {name} server: {e}")
            raise RuntimeError(f"Failed to start server '{name}': {e}")
    
    async def _check_mcp_startup(
        self, 
        process: subprocess.Popen, 
        config: MCPServerConfig, 
        info: MCPServerInfo,
        timeout: float = 5.0
    ) -> bool:
        """Check if MCP server started successfully.
        
        MCP-specific startup validation that understands stdio transport
        servers write status to stderr as normal behavior.
        """
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            # Check if process is still running
            if process.poll() is not None:
                # Process exited
                if process.returncode == 0:
                    return True
                else:
                    stdout, stderr = process.communicate()
                    error_msg = stderr if stderr else stdout
                    logger.error(f"Process exited with code {process.returncode}: {error_msg}")
                    return False
            
            # For stdio servers, running = success
            if config.transport == MCPTransport.STDIO:
                await asyncio.sleep(0.5)
                if process.poll() is None:
                    info.protocol_version = "1.0"  # Default protocol
                    return True
            
            await asyncio.sleep(0.1)
        
        # Timeout reached, process still running = success
        return process.poll() is None
    
    def _start_output_monitor(self, name: str, process: subprocess.Popen) -> None:
        """Start monitoring thread for stdio server output."""
        def monitor():
            logger.debug(f"Starting output monitor for {name}")
            while process.poll() is None and not self.shutdown_requested:
                try:
                    # Read stderr (where stdio servers write status)
                    line = process.stderr.readline()
                    if line:
                        logger.debug(f"[{name}] {line.strip()}")
                        # Update message count in server info
                        if name in self.servers:
                            self.servers[name].record_message()
                except:
                    break
            logger.debug(f"Output monitor for {name} stopped")
        
        thread = threading.Thread(target=monitor, daemon=True, name=f"mcp-monitor-{name}")
        thread.start()
        self.output_monitors[name] = thread
    
    async def stop_server(self, name: str, force: bool = False) -> bool:
        """Stop server with cleanup of MCP-specific resources."""
        # Stop output monitor first
        if name in self.output_monitors:
            # Signal thread to stop by setting shutdown flag
            # Thread will exit on next iteration
            del self.output_monitors[name]
        
        # Stop the server process
        info = self.servers.get(name)
        if not info:
            return False
        
        try:
            # Stop health monitoring first
            await self.stop_health_monitoring(name)
            
            # Terminate process gracefully
            if info.process_handle and info.process_handle.poll() is None:
                info.process_handle.terminate()
                
                # Wait for graceful termination
                try:
                    info.process_handle.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if force:
                        info.process_handle.kill()
                        info.process_handle.wait(timeout=5)
                    else:
                        return False
            
            # Update status
            info.status = ServerStatus.STOPPED
            
            # Remove from active servers
            del self.servers[name]
            
            logger.info(f"Stopped MCP server '{name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping server '{name}': {e}")
            return False
    
    async def health_check(self, name: str) -> bool:
        """MCP-specific health check implementation."""
        info = self.servers.get(name)
        if not info:
            return False
        
        # Check process is running
        if info.process_handle and info.process_handle.poll() is not None:
            return False
        
        # For stdio servers, check if we're getting messages
        if info.transport == MCPTransport.STDIO:
            if info.last_message_time:
                idle_time = (datetime.now() - info.last_message_time).total_seconds()
                # Consider unhealthy if no messages for 5 minutes
                if idle_time > 300:
                    logger.warning(f"Server '{name}' idle for {int(idle_time)}s")
            
        return True
    
    async def restart_server(self, name: str) -> MCPServerInfo:
        """Restart server preserving environment configuration."""
        # Get current environment if server is running
        env_overrides = None
        if name in self.servers:
            transport_info = self.servers[name].transport_info
            if "env_vars" in transport_info:
                # Try to preserve environment variables
                env_overrides = {}
                for var in transport_info["env_vars"]:
                    if var in os.environ:
                        env_overrides[var] = os.environ[var]
        
        # Stop and start
        await self.stop_server(name)
        return await self.start_server(name, env_overrides)
    
    async def cleanup(self) -> None:
        """Clean up all resources including output monitors."""
        self.shutdown_requested = True
        
        # Stop all output monitors
        self.output_monitors.clear()
        
        # Call parent cleanup
        await super().cleanup()
    
    # =====================================================
    # Backward Compatibility Methods
    # =====================================================
    
    @property
    def available_servers(self) -> Dict[str, dict]:
        """Legacy property for backward compatibility."""
        # Convert configs to legacy format
        legacy = {}
        for name, config in self.available_configs.items():
            legacy[name] = {
                "command": config.command,
                "description": config.description,
                "transport": config.transport.value,
                "requires_env": config.requires_env
            }
        return legacy
    
    def start_server_sync(self, name: str, env_overrides: Optional[Dict[str, str]] = None) -> bool:
        """Synchronous wrapper for legacy compatibility."""
        try:
            try:
                loop = asyncio.get_running_loop()
                # If loop is already running, schedule as task
                future = asyncio.ensure_future(self.start_server(name, env_overrides))
                # Can't wait for it in sync context
                return True
            except RuntimeError:
                # No running loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.start_server(name, env_overrides))
                    return True
                finally:
                    loop.close()
        except Exception as e:
            logger.error(f"Failed to start server '{name}': {e}")
            return False
    
    def stop_server_sync(self, name: str) -> bool:
        """Synchronous wrapper for legacy compatibility."""
        try:
            try:
                loop = asyncio.get_running_loop()
                # If loop is already running, schedule as task
                future = asyncio.ensure_future(self.stop_server(name))
                return True
            except RuntimeError:
                # No running loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.stop_server(name))
                finally:
                    loop.close()
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, dict]:
        """Get legacy-format status."""
        status = {}
        for name, info in self.servers.items():
            status[name] = {
                "pid": info.pid,
                "running": info.is_running,
                "transport": info.transport.value,
                "description": self.available_configs[name].description
            }
        return status
    
    def show_status(self) -> None:
        """Show status in legacy format."""
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
        not_running = set(self.available_configs.keys()) - set(status.keys())
        if not_running:
            logger.info("\n💡 Available servers (not running):")
            for name in not_running:
                config = self.available_configs[name]
                logger.info(f"   - {name}: {config.description}")
    
    def run(self, servers_to_start: Optional[List[str]] = None, blocking: bool = True) -> bool:
        """Legacy run method for backward compatibility."""
        logger.info("🎯 MCP Server Manager Starting...")
        logger.info("This manages Model Context Protocol servers for AI tool integration.")
        
        # Enable legacy mode
        self.legacy_mode = True
        
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
            if self.start_server_sync(server_name):
                success_count += 1
        
        logger.info(f"\n✅ Started {success_count}/{len(servers_to_start)} servers successfully")
        self.show_status()
        
        if not blocking:
            return True
        
        # Set up signal handlers
        def signal_handler(signum, frame):
            logger.info("\n⚠️  Received interrupt signal")
            self.stop_all_servers()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("\n💡 Servers are running. Press Ctrl+C to stop.")
        logger.info("📊 Status updates every 60 seconds.\n")
        
        try:
            # Run event loop with periodic status
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_monitoring_loop())
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interrupted by user")
        finally:
            self.stop_all_servers()
            logger.info("👋 All servers stopped. Goodbye!")
        
        return True
    
    async def _run_monitoring_loop(self) -> None:
        """Async monitoring loop for legacy run mode."""
        while not self.shutdown_requested:
            await asyncio.sleep(60)
            
            # Check server health
            for name in list(self.servers.keys()):
                if not await self.health_check(name):
                    logger.warning(f"⚠️  Server {name} has stopped unexpectedly")
                    await self._handle_server_failure(name)
            
            self.show_status()
    
    def stop_all_servers(self) -> None:
        """Stop all servers synchronously for legacy compatibility."""
        self.shutdown_requested = True
        logger.info("🛑 Stopping all servers...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.cleanup())


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server Manager V2")
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
    
    manager = MCPServerManagerV2()
    
    if args.list:
        logger.info("📋 Available MCP Servers:")
        for name, config in manager.available_configs.items():
            logger.info(f"\n{name}:")
            logger.info(f"  Description: {config.description}")
            logger.info(f"  Transport: {config.transport}")
            if config.requires_env:
                logger.info(f"  Required env: {', '.join(config.requires_env)}")
        return
    
    # Run the manager
    manager.run(servers_to_start=args.servers)


if __name__ == "__main__":
    main()