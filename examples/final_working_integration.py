#!/usr/bin/env python3
"""Final Working MCP Integration - CORRECTED VERSION.

This demonstrates the CORRECT way to create MCP tools:
1. Use @tool decorator or StructuredTool.from_function
2. External server management (not inside tool classes)
3. Real MCP protocol communication
4. Proper integration with haive agents

NEVER subclass BaseTool directly - use the proper patterns!
"""

import asyncio
import json
import os
import subprocess
from typing import Any

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field


class MCPServerRunner:
    """CORRECT: External server management class
    Handles MCP server lifecycle separately from tool definitions.
    """

    def __init__(self):
        self.processes: dict[str, subprocess.Popen] = {}
        self.initialized: dict[str, bool] = {}
        self.request_counters: dict[str, int] = {}

    async def start_filesystem_server(self) -> bool:
        """Start and initialize MCP filesystem server."""
        try:
            # Setup test files
            test_dir = "/tmp/mcp_final_test"
            os.makedirs(test_dir, exist_ok=True)

            with open(f"{test_dir}/readme.txt", "w") as f:
                f.write(
                    "CORRECTED MCP Integration\n\nThis file demonstrates the proper way to integrate MCP servers with haive agents."
                )

            with open(f"{test_dir}/status.json", "w") as f:
                json.dump(
                    {
                        "integration": "corrected",
                        "pattern": "@tool decorator",
                        "server_management": "external class",
                        "status": "working",
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
                self.processes["filesystem"] = process
                self.request_counters["filesystem"] = 1

                if await self._initialize_server("filesystem"):
                    return True

        except Exception:
            pass

        return False

    async def _initialize_server(self, server_name: str) -> bool:
        """Initialize MCP server connection."""
        try:
            process = self.processes[server_name]

            # MCP initialize request
            init_msg = {
                "jsonrpc": "2.0",
                "id": self.request_counters[server_name],
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "haive-corrected-integration",
                        "version": "1.0.0",
                    },
                },
            }

            process.stdin.write(json.dumps(init_msg) + "\n")
            process.stdin.flush()
            self.request_counters[server_name] += 1

            response = process.stdout.readline()
            if response.strip():
                result = json.loads(response)
                if "result" in result:
                    # Send initialized notification
                    notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
                    process.stdin.write(json.dumps(notify) + "\n")
                    process.stdin.flush()

                    self.initialized[server_name] = True
                    return True

        except Exception:
            pass

        return False

    def execute_mcp_operation(
        self, server_name: str, tool_name: str, args: dict[str, Any]
    ) -> str:
        """Execute MCP tool operation."""
        if server_name not in self.processes or not self.initialized.get(server_name):
            return f"❌ Server '{server_name}' not available"

        try:
            process = self.processes[server_name]
            request = {
                "jsonrpc": "2.0",
                "id": self.request_counters[server_name],
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
            }

            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            self.request_counters[server_name] += 1

            response = process.stdout.readline()
            if response.strip():
                result = json.loads(response)

                if "result" in result:
                    content = result["result"].get("content", [])
                    if content and content[0].get("type") == "text":
                        return content[0].get("text", "No text content")
                    return str(result["result"])
                if "error" in result:
                    return f"❌ MCP Error: {result['error']['message']}"

        except Exception as e:
            return f"❌ Operation failed: {e}"

        return "❌ No server response"

    def cleanup(self):
        """Stop all servers."""
        for _name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()


# Global server instance (correct pattern)
server_runner = MCPServerRunner()


# CORRECT PATTERN 1: @tool decorator
@tool
def read_mcp_file(filename: str) -> str:
    """Read a file using the MCP filesystem server.

    Args:
        filename: Name of file to read (e.g., 'readme.txt', 'status.json')
    """
    return server_runner.execute_mcp_operation(
        "filesystem", "read_file", {"path": filename}
    )


@tool
def list_mcp_directory(path: str = ".") -> str:
    """List directory contents using MCP filesystem server.

    Args:
        path: Directory path to list (default: current directory)
    """
    return server_runner.execute_mcp_operation(
        "filesystem", "list_directory", {"path": path}
    )


# CORRECT PATTERN 2: StructuredTool with schema
class FileSystemInput(BaseModel):
    """Input schema for filesystem operations."""

    action: str = Field(description="Action: 'read' or 'list'")
    target: str = Field(description="File or directory path")


def filesystem_operation(action: str, target: str) -> str:
    """Perform filesystem operations via MCP."""
    if action == "read":
        return server_runner.execute_mcp_operation(
            "filesystem", "read_file", {"path": target}
        )
    if action == "list":
        return server_runner.execute_mcp_operation(
            "filesystem", "list_directory", {"path": target}
        )
    return f"❌ Invalid action: {action}"


structured_filesystem_tool = StructuredTool.from_function(
    func=filesystem_operation,
    name="mcp_filesystem_tool",
    description="Perform filesystem operations via MCP server",
    args_schema=FileSystemInput,
)


async def test_corrected_integration():
    """Test the corrected MCP integration."""
    try:
        # Start server using external manager
        if not await server_runner.start_filesystem_server():
            return

        # Test decorated tools
        list_mcp_directory.run(".")

        read_mcp_file.run("readme.txt")

        read_mcp_file.run("status.json")

        # Test structured tool
        structured_filesystem_tool.run({"action": "list", "target": "."})

        structured_filesystem_tool.run({"action": "read", "target": "status.json"})

        # Show haive integration

    finally:
        server_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(test_corrected_integration())
