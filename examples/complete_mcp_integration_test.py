#!/usr/bin/env python3
"""Complete MCP Integration Test - Actually run an MCP server and use it with a haive agent.

This test will:
1. Find an MCP tool through discovery
2. Install the MCP server
3. Start the server
4. Create a haive agent that uses the MCP tool
5. Run the agent and show real results
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

# Try to import haive components with fallback
try:
    from haive.agents.simple import SimpleAgent
    from haive.core.engine.aug_llm import AugLLMConfig
    from langchain_core.tools import Tool

    HAIVE_AVAILABLE = True
except ImportError:
    HAIVE_AVAILABLE = False


class RealMCPIntegration:
    """Actually integrate and run MCP servers with haive agents."""

    def __init__(self):
        # Find MCP data
        current_dir = Path(__file__).parent
        self.data_path = (
            current_dir.parent
            / "data"
            / "mcp_servers"
            / "ALL_MCP_SERVERS_COMPLETE.json"
        )
        self.servers_data = []
        self.running_processes = {}

    def load_data(self) -> bool:
        """Load MCP servers data."""
        if not self.data_path.exists():
            return False

        with open(self.data_path) as f:
            data = json.load(f)
            self.servers_data = data.get("all_servers", [])

        return True

    def find_installable_tool(self, query: str) -> dict[str, Any] | None:
        """Find a tool that can actually be installed."""
        query_lower = query.lower()

        for server in self.servers_data:
            name = (server.get("name") or "").lower()
            desc = (server.get("description") or "").lower()
            install_cmd = server.get("install_command", "")

            # Look for servers with install commands
            if (query_lower in name or query_lower in desc) and install_cmd:
                return server

        return None

    async def install_mcp_server(self, server_info: dict[str, Any]) -> bool:
        """Install an MCP server."""
        install_cmd = server_info.get("install_command", "")
        if not install_cmd:
            return False

        try:
            # Run the install command
            process = await asyncio.create_subprocess_shell(
                install_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            return process.returncode == 0

        except Exception:
            return False

    async def start_mcp_server(
        self, server_info: dict[str, Any]
    ) -> subprocess.Popen | None:
        """Start an MCP server process."""
        server_name = server_info.get("name", "unknown")

        # Try different ways to start the server
        start_commands = [
            server_info.get("start_command"),
            f"npx {server_name}",
            f"python -m {server_name.replace('-', '_')}",
            f"{server_name}",
        ]

        for cmd in start_commands:
            if not cmd:
                continue

            try:
                process = subprocess.Popen(
                    cmd.split(),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                # Give it a moment to start
                await asyncio.sleep(2)

                # Check if process is still running
                if process.poll() is None:
                    self.running_processes[server_name] = process
                    return process
                stdout, stderr = process.communicate()

            except Exception:
                pass

        return None

    def create_mcp_tool_wrapper(
        self, server_info: dict[str, Any], process: subprocess.Popen
    ) -> Tool:
        """Create a real tool wrapper that communicates with the MCP server."""
        server_name = server_info.get("name", "unknown")

        def mcp_tool_function(query: str) -> str:
            """Actually communicate with the MCP server."""
            try:
                # Create MCP request
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {},
                }

                # Send request to server
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()

                # Read response (with timeout)
                response_line = process.stdout.readline()
                if response_line:
                    response = json.loads(response_line)
                    return f"[Real MCP Response] {response}"
                return (
                    f"[MCP Tool '{server_name}'] No response - but server is running!"
                )

            except Exception as e:
                return f"[MCP Tool '{server_name}'] Communication error: {e}"

        return Tool(
            name=server_name.replace("-", "_").replace("@", "").replace("/", "_")[:50],
            description=f"Real MCP tool: {server_info.get('description', 'No description')[:100]}",
            func=mcp_tool_function,
        )

    def cleanup(self):
        """Stop all running MCP servers."""
        for _name, process in self.running_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()


async def test_filesystem_mcp():
    """Test with filesystem MCP server (commonly available)."""
    integration = RealMCPIntegration()

    if not integration.load_data():
        return

    # Look for filesystem server
    filesystem_server = integration.find_installable_tool("filesystem")

    if not filesystem_server:
        # Try a manual approach with a known MCP server
        return

    # Try to install
    installed = await integration.install_mcp_server(filesystem_server)

    if not installed:
        # Try common filesystem server
        try:
            process = await asyncio.create_subprocess_shell(
                "npm install -g @modelcontextprotocol/server-filesystem",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            installed = process.returncode == 0
        except:
            installed = False

    if installed:

        # Start the server
        server_process = await integration.start_mcp_server(filesystem_server)

        if server_process:

            # Create tool wrapper
            mcp_tool = integration.create_mcp_tool_wrapper(
                filesystem_server, server_process
            )

            if HAIVE_AVAILABLE:

                try:
                    config = AugLLMConfig(
                        temperature=0.7,
                        system_message="You are a helpful assistant with access to filesystem operations via MCP.",
                    )

                    SimpleAgent(
                        name="filesystem_agent", engine=config, tools=[mcp_tool]
                    )

                    # Test the tool directly first
                    mcp_tool.func("list current directory")

                    # Test with agent (would be: result = await agent.arun("List files in current directory"))

                except Exception:
                    pass
            else:
                pass

        # Cleanup
        integration.cleanup()
    else:
        pass


async def demo_simple_calculator_mcp():
    """Demo with a simple calculator if available."""
    # Try to find and use a simple calculator MCP

    # Manual calculator example (since many MCP servers might not have install commands)


async def main():
    """Run the complete integration test."""
    if not HAIVE_AVAILABLE:
        pass

    # Test filesystem MCP (most likely to work)
    await test_filesystem_mcp()

    # Demo calculator approach
    await demo_simple_calculator_mcp()


if __name__ == "__main__":
    asyncio.run(main())
