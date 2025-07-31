#!/usr/bin/env python3
"""Proper MCP Integration - Using correct langchain tool patterns.

This demonstrates the RIGHT way to create MCP tools:
1. Using @tool decorator
2. Using StructuredTool.from_function
3. Proper state management outside the tool class
4. Real MCP server integration
"""

import asyncio
import json
import os
import subprocess
from typing import Any

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field


class MCPServerManager:
    """Manages MCP server processes and state - OUTSIDE of tool classes."""

    def __init__(self):
        self.servers: dict[str, subprocess.Popen] = {}
        self.initialized_servers: dict[str, bool] = {}
        self.request_ids: dict[str, int] = {}

    async def start_filesystem_server(self) -> bool:
        """Start MCP filesystem server."""
        try:
            # Create test files
            test_dir = "/tmp/mcp_demo"
            os.makedirs(test_dir, exist_ok=True)

            with open(f"{test_dir}/demo.txt", "w") as f:
                f.write(
                    "Hello from real MCP filesystem server!\nThis file was read using proper tool integration."
                )

            with open(f"{test_dir}/info.json", "w") as f:
                json.dump(
                    {
                        "server": "MCP Filesystem",
                        "status": "running",
                        "capabilities": ["read_file", "write_file", "list_directory"],
                    },
                    f,
                    indent=2,
                )

            # Start server
            process = subprocess.Popen(
                ["npx", "@modelcontextprotocol/server-filesystem", test_dir],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="/home/will/Projects/haive/backend/haive",
            )

            await asyncio.sleep(2)

            if process.poll() is None:
                self.servers["filesystem"] = process
                self.request_ids["filesystem"] = 1

                # Initialize the server
                if await self._initialize_server("filesystem"):
                    return True

        except Exception:
            pass

        return False

    async def _initialize_server(self, server_name: str) -> bool:
        """Initialize MCP server connection."""
        try:
            process = self.servers[server_name]

            init_request = {
                "jsonrpc": "2.0",
                "id": self.request_ids[server_name],
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "haive-mcp", "version": "1.0.0"},
                },
            }

            process.stdin.write(json.dumps(init_request) + "\n")
            process.stdin.flush()
            self.request_ids[server_name] += 1

            response = process.stdout.readline()
            if response.strip():
                result = json.loads(response)
                if "result" in result:
                    # Send initialized notification
                    initialized = {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                    }
                    process.stdin.write(json.dumps(initialized) + "\n")
                    process.stdin.flush()

                    self.initialized_servers[server_name] = True
                    return True

        except Exception:
            pass

        return False

    def call_mcp_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> str:
        """Call an MCP tool on a server."""
        if server_name not in self.servers or not self.initialized_servers.get(
            server_name
        ):
            return f"❌ Server {server_name} not available"

        try:
            process = self.servers[server_name]
            request = {
                "jsonrpc": "2.0",
                "id": self.request_ids[server_name],
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }

            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            self.request_ids[server_name] += 1

            response = process.stdout.readline()
            if response.strip():
                result = json.loads(response)

                if "result" in result:
                    content = result["result"].get("content", [])
                    if content and content[0].get("type") == "text":
                        return content[0].get("text", str(result["result"]))
                    return str(result["result"])
                if "error" in result:
                    return f"❌ MCP Error: {result['error']['message']}"

        except Exception as e:
            return f"❌ Communication error: {e}"

        return "❌ No response from server"

    def stop_all_servers(self):
        """Stop all MCP servers."""
        for _name, process in self.servers.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

        self.servers.clear()
        self.initialized_servers.clear()


# Global server manager instance
mcp_manager = MCPServerManager()


# Method 1: Using @tool decorator (simplest)
@tool
def mcp_read_file(filename: str) -> str:
    """Read a file using MCP filesystem server.

    Args:
        filename: Name of the file to read (e.g., 'demo.txt', 'info.json')
    """
    return mcp_manager.call_mcp_tool("filesystem", "read_file", {"path": filename})


@tool
def mcp_list_directory(path: str = ".") -> str:
    """List directory contents using MCP filesystem server.

    Args:
        path: Directory path to list (default: current directory)
    """
    return mcp_manager.call_mcp_tool("filesystem", "list_directory", {"path": path})


# Method 2: Using StructuredTool with input schema
class FileOperationInput(BaseModel):
    """Input schema for file operations."""

    operation: str = Field(description="Operation: 'read' or 'list'")
    path: str = Field(description="File or directory path")


def mcp_file_operations(operation: str, path: str) -> str:
    """Perform file operations via MCP filesystem server."""
    if operation == "read":
        return mcp_manager.call_mcp_tool("filesystem", "read_file", {"path": path})
    if operation == "list":
        return mcp_manager.call_mcp_tool("filesystem", "list_directory", {"path": path})
    return f"❌ Unknown operation: {operation}"


mcp_structured_tool = StructuredTool.from_function(
    func=mcp_file_operations,
    name="mcp_filesystem_operations",
    description="Perform file and directory operations via MCP filesystem server",
    args_schema=FileOperationInput,
)


async def test_tool_decorator_approach():
    """Test the @tool decorator approach."""
    mcp_read_file.run("demo.txt")

    mcp_list_directory.run(".")

    mcp_read_file.run("info.json")


async def test_structured_tool_approach():
    """Test the StructuredTool approach."""
    mcp_structured_tool.run({"operation": "read", "path": "demo.txt"})

    mcp_structured_tool.run({"operation": "list", "path": "."})


async def demonstrate_haive_integration():
    """Show how these tools integrate with haive agents."""


async def main():
    """Run the complete proper MCP integration test."""
    try:
        # Start MCP server
        if not await mcp_manager.start_filesystem_server():
            return

        # Test both approaches
        await test_tool_decorator_approach()
        await test_structured_tool_approach()

        # Show haive integration
        await demonstrate_haive_integration()

    finally:
        # Always cleanup
        mcp_manager.stop_all_servers()


if __name__ == "__main__":
    asyncio.run(main())
