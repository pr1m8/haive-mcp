#!/usr/bin/env python3
"""FastMCP Server Runner.

Manages the lifecycle of FastMCP servers registered in the system.
Provides process management, monitoring, and integration with the discovery system.
"""

import argparse
import asyncio
import contextlib
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPProcessManager:
    """Manages MCP server processes with monitoring and auto-restart."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or Path.home() / ".fastmcp" / "servers.json"
        self.processes: dict[str, subprocess.Popen] = {}
        self.process_info: dict[str, dict[str, Any]] = {}
        self.monitor_task = None
        self._running = False

    def load_servers(self) -> dict[str, Any]:
        """Load server configurations."""
        if not self.config_path.exists():
            return {}

        with open(self.config_path) as f:
            data = json.load(f)
            return data.get("servers", {})

    async def start_server(self, server_name: str) -> dict[str, Any]:
        """Start a specific server."""
        servers = self.load_servers()

        if server_name not in servers:
            return {"success": False, "error": f"Server '{server_name}' not found"}

        if server_name in self.processes:
            # Check if process is still running
            if self.processes[server_name].poll() is None:
                return {
                    "success": False,
                    "error": f"Server '{server_name}' is already running",
                }
            # Clean up dead process
            del self.processes[server_name]

        server_config = servers[server_name]

        if not server_config.get("active", True):
            return {"success": False, "error": f"Server '{server_name}' is disabled"}

        try:
            # Build command
            cmd = [server_config["command"], *server_config.get("args", [])]

            # Set environment
            env = os.environ.copy()
            env.update(server_config.get("env", {}))

            # Handle different transports
            if server_config.get("transport", "stdio") == "stdio":
                # Start process with pipes for stdio
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffered
                    universal_newlines=True,
                )
            else:
                # For SSE/HTTP, just start the process
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

            self.processes[server_name] = process
            self.process_info[server_name] = {
                "pid": process.pid,
                "started_at": datetime.now().isoformat(),
                "command": " ".join(cmd),
                "transport": server_config.get("transport", "stdio"),
                "auto_restart": server_config.get("auto_restart", False),
            }

            logger.info(f"Started server '{server_name}' with PID {process.pid}")

            return {
                "success": True,
                "message": f"Started server '{server_name}'",
                "pid": process.pid,
            }

        except Exception as e:
            logger.exception(f"Failed to start server '{server_name}': {e}")
            return {"success": False, "error": f"Failed to start server: {e!s}"}

    async def stop_server(self, server_name: str) -> dict[str, Any]:
        """Stop a specific server."""
        if server_name not in self.processes:
            return {"success": False, "error": f"Server '{server_name}' is not running"}

        process = self.processes[server_name]

        try:
            # Try graceful termination first
            process.terminate()

            # Wait for process to end
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                logger.warning(
                    f"Server '{server_name}' didn't stop gracefully, forcing..."
                )
                process.kill()
                process.wait()

            # Clean up
            del self.processes[server_name]
            if server_name in self.process_info:
                del self.process_info[server_name]

            logger.info(f"Stopped server '{server_name}'")

            return {"success": True, "message": f"Stopped server '{server_name}'"}

        except Exception as e:
            logger.exception(f"Failed to stop server '{server_name}': {e}")
            return {"success": False, "error": f"Failed to stop server: {e!s}"}

    async def restart_server(self, server_name: str) -> dict[str, Any]:
        """Restart a server."""
        # Stop if running
        if server_name in self.processes:
            stop_result = await self.stop_server(server_name)
            if not stop_result["success"]:
                return stop_result

            # Brief pause
            await asyncio.sleep(1)

        # Start again
        return await self.start_server(server_name)

    def get_server_status(self, server_name: str) -> dict[str, Any]:
        """Get detailed status of a server."""
        status = {
            "name": server_name,
            "running": False,
            "pid": None,
            "uptime": None,
            "memory_usage": None,
            "cpu_usage": None,
        }

        if server_name in self.processes:
            process = self.processes[server_name]

            # Check if still running
            if process.poll() is None:
                status["running"] = True
                status["pid"] = process.pid

                # Get process info
                if server_name in self.process_info:
                    info = self.process_info[server_name]
                    started = datetime.fromisoformat(info["started_at"])
                    uptime = datetime.now() - started
                    status["uptime"] = str(uptime).split(".")[0]  # Remove microseconds

                # Get resource usage
                try:
                    ps_process = psutil.Process(process.pid)
                    status["memory_usage"] = (
                        f"{ps_process.memory_info().rss / 1024 / 1024:.1f} MB"
                    )
                    status["cpu_usage"] = f"{ps_process.cpu_percent(interval=0.1):.1f}%"
                except:
                    pass
            else:
                # Process died
                del self.processes[server_name]
                if server_name in self.process_info:
                    del self.process_info[server_name]

        return status

    async def monitor_servers(self):
        """Monitor running servers and restart if needed."""
        self._running = True

        while self._running:
            # Check each running server
            for server_name in list(self.processes.keys()):
                process = self.processes[server_name]

                # Check if process is still running
                if process.poll() is not None:
                    logger.warning(
                        f"Server '{server_name}' has stopped (exit code: {process.returncode})"
                    )

                    # Clean up
                    del self.processes[server_name]

                    # Check if auto-restart is enabled
                    if server_name in self.process_info:
                        info = self.process_info[server_name]
                        if info.get("auto_restart", False):
                            logger.info(f"Auto-restarting server '{server_name}'...")
                            await self.start_server(server_name)

            # Wait before next check
            await asyncio.sleep(5)

    async def start_monitoring(self):
        """Start the monitoring task."""
        if not self.monitor_task:
            self.monitor_task = asyncio.create_task(self.monitor_servers())

    async def stop_monitoring(self):
        """Stop the monitoring task."""
        self._running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitor_task

    async def stop_all_servers(self):
        """Stop all running servers."""
        for server_name in list(self.processes.keys()):
            await self.stop_server(server_name)

    def list_running_servers(self) -> list[dict[str, Any]]:
        """List all running servers with their status."""
        servers = []

        for server_name in self.processes:
            status = self.get_server_status(server_name)
            servers.append(status)

        return servers


class FastMCPCLI:
    """Command-line interface for FastMCP server management."""

    def __init__(self):
        self.manager = MCPProcessManager()

    async def run_command(self, command: str, args: list[str]):
        """Execute a CLI command."""
        if command == "start":
            if not args:
                return

            result = await self.manager.start_server(args[0])
            if result["success"]:
                pass
            else:
                pass

        elif command == "stop":
            if not args:
                return

            result = await self.manager.stop_server(args[0])
            if result["success"]:
                pass
            else:
                pass

        elif command == "restart":
            if not args:
                return

            result = await self.manager.restart_server(args[0])
            if result["success"]:
                pass
            else:
                pass

        elif command == "status":
            if args:
                # Status for specific server
                status = self.manager.get_server_status(args[0])
                if status["running"]:
                    pass
            else:
                # List all running servers
                servers = self.manager.list_running_servers()
                if not servers:
                    pass
                else:
                    for _server in servers:
                        pass

        elif command == "list":
            # List all configured servers
            servers = self.manager.load_servers()
            if not servers:
                pass
            else:
                for _name, config in servers.items():
                    config.get("command", "N/A")
                    config.get("transport", "stdio")
                    "Yes" if config.get("active", True) else "No"

        elif command == "monitor":
            # Start monitoring mode
            try:
                await self.manager.start_monitoring()

                # Keep running until interrupted
                while True:
                    await asyncio.sleep(1)

            except KeyboardInterrupt:
                await self.manager.stop_monitoring()
                await self.manager.stop_all_servers()

        else:
            pass


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="FastMCP Server Runner")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("args", nargs="*", help="Command arguments")

    args = parser.parse_args()

    cli = FastMCPCLI()
    await cli.run_command(args.command, args.args)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Error: {e}")
        sys.exit(1)
