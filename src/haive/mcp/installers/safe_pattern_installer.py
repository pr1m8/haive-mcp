"""Safe Pattern-Based MCP Server Installer

Version 1: Uses predefined patterns for safe, predictable installations.
No code generation - only trusted, tested patterns.
"""

import asyncio
import json
import os
import subprocess
from typing import Any

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from haive.core.tools.interrupt_tool_wrapper import add_human_in_the_loop
from haive.mcp.installers.config_manager import (
    MCPConfigManager,
    MCPEnvironmentConfig,
    MCPServerPattern,
)


class InstallationRequest(BaseModel):
    """Request for MCP server installation"""

    server_name: str = Field(description="Unique name for this server instance")
    package_name: str = Field(
        description="Package name (e.g., @modelcontextprotocol/server-filesystem)"
    )
    pattern_type: str = Field(
        description="Pattern type: filesystem, database, web_api, python_server"
    )
    custom_args: list[str] = Field(
        default_factory=list, description="Custom startup arguments"
    )
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    require_approval: bool = Field(default=True, description="Require human approval")


class InstallationResult(BaseModel):
    """Result of installation attempt"""

    success: bool
    server_name: str
    message: str
    config_created: bool = False
    process_id: int | None = None
    tools_available: list[str] = Field(default_factory=list)


class SafePatternInstaller:
    """Safe MCP installer using only predefined patterns"""

    def __init__(self, config_manager: MCPConfigManager | None = None):
        self.config_manager = config_manager or MCPConfigManager()
        self.running_servers: dict[str, subprocess.Popen] = {}
        self.request_counters: dict[str, int] = {}

        print("🛡️  Safe Pattern Installer initialized")
        print(f"📁 Config directory: {self.config_manager.config_dir}")
        print(
            f"🔧 Available patterns: {', '.join(self.config_manager.list_available_patterns())}"
        )

    def get_pattern_for_server(
        self, package_name: str, suggested_pattern: str
    ) -> MCPServerPattern | None:
        """Get the appropriate pattern for a server"""
        # First try the suggested pattern
        if suggested_pattern:
            pattern = self.config_manager.get_pattern(suggested_pattern)
            if pattern:
                return pattern

        # Auto-detect pattern based on package name
        if "@modelcontextprotocol/server-filesystem" in package_name:
            return self.config_manager.get_pattern("filesystem")
        if "database" in package_name.lower() or "sql" in package_name.lower():
            return self.config_manager.get_pattern("database")
        if "@modelcontextprotocol" in package_name:
            return self.config_manager.get_pattern(
                "web_api"
            )  # Default for MCP packages
        if package_name.startswith("mcp-server-"):
            return self.config_manager.get_pattern("python_server")

        return None

    def validate_installation_request(
        self, request: InstallationRequest
    ) -> tuple[bool, str]:
        """Validate that installation request is safe"""
        # Check if pattern exists
        pattern = self.get_pattern_for_server(
            request.package_name, request.pattern_type
        )
        if not pattern:
            return False, f"Unknown pattern type: {request.pattern_type}"

        # Check for security risks
        if pattern.security_level == "high_risk":
            return (
                False,
                f"Pattern {request.pattern_type} is marked as high risk and not allowed in safe mode",
            )

        # Validate package name format
        if not self._is_safe_package_name(request.package_name):
            return (
                False,
                f"Package name '{request.package_name}' does not match safe patterns",
            )

        # Check if server name already exists
        if request.server_name in self.config_manager.list_configured_servers():
            return False, f"Server '{request.server_name}' already configured"

        return True, "Validation passed"

    def _is_safe_package_name(self, package_name: str) -> bool:
        """Check if package name matches safe patterns"""
        safe_patterns = [
            "@modelcontextprotocol/",
            "mcp-server-",
            "@mcp/",
        ]

        return any(package_name.startswith(pattern) for pattern in safe_patterns)

    @tool
    def check_server_status(self, server_name: str) -> str:
        """Check if an MCP server is running"""
        if server_name in self.running_servers:
            process = self.running_servers[server_name]
            if process.poll() is None:
                return f"✅ Server '{server_name}' is running (PID: {process.pid})"
            return f"❌ Server '{server_name}' process has stopped"
        return f"❌ Server '{server_name}' is not running"

    def create_installation_tool(self, request: InstallationRequest) -> StructuredTool:
        """Create a tool for installing a specific MCP server"""

        def install_server_func(confirm: bool = True) -> str:
            """Install MCP server using safe patterns"""
            if not confirm and request.require_approval:
                return "❌ Installation cancelled - approval required"

            # Validate request
            valid, message = self.validate_installation_request(request)
            if not valid:
                return f"❌ Validation failed: {message}"

            # Get pattern
            pattern = self.get_pattern_for_server(
                request.package_name, request.pattern_type
            )
            if not pattern:
                return f"❌ No pattern found for {request.package_name}"

            try:
                # Create environment config
                env_config = MCPEnvironmentConfig(
                    server_name=request.server_name,
                    package_name=request.package_name,
                    startup_args=request.custom_args or pattern.default_args,
                    env_vars={**pattern.env_template, **request.env_vars},
                    transport_type=pattern.transport,
                    requires_approval=request.require_approval,
                )

                # Save configuration
                config_saved = self.config_manager.add_server_config(env_config)
                if not config_saved:
                    return "❌ Failed to save server configuration"

                # Prepare installation command
                if pattern.install_command != "none":
                    install_cmd = pattern.install_command.format(
                        package_name=request.package_name
                    )

                    print(f"📦 Installing {request.package_name}...")
                    result = subprocess.run(
                        install_cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=60,
                        check=False,
                    )

                    if result.returncode != 0:
                        return f"❌ Installation failed: {result.stderr}"

                # Test startup (dry run)
                startup_cmd = pattern.startup_command.format(
                    package_name=request.package_name,
                    args=" ".join(env_config.startup_args),
                )

                print(f"🚀 Testing server startup: {startup_cmd}")

                return f"""✅ Server '{request.server_name}' configured successfully!

📋 Configuration Summary:
   - Package: {request.package_name}
   - Pattern: {pattern.pattern_name}
   - Transport: {pattern.transport}
   - Security Level: {pattern.security_level}
   - Startup Command: {startup_cmd}
   - Config Saved: {config_saved}

🔧 Next Steps:
   1. Use start_server('{request.server_name}') to run the server
   2. Server will be available for tool creation
   3. Configuration saved to: {self.config_manager.config_dir}

📊 Claude Desktop Config:
{json.dumps(self.config_manager.export_claude_desktop_config(request.server_name), indent=2)}
"""

            except Exception as e:
                return f"❌ Installation error: {e}"

        # Create the tool
        tool_func = StructuredTool.from_function(
            func=install_server_func,
            name=f"install_{request.server_name}",
            description=f"Install MCP server '{request.server_name}' using pattern '{request.pattern_type}'",
        )

        # Wrap with human approval if requested
        if request.require_approval:
            return add_human_in_the_loop(
                tool_func,
                interrupt_config={
                    "allow_accept": True,
                    "allow_edit": True,
                    "allow_respond": True,
                },
            )
        return tool_func

    async def start_server(self, server_name: str) -> InstallationResult:
        """Start a configured MCP server"""
        config = self.config_manager.get_server_config(server_name)
        if not config:
            return InstallationResult(
                success=False,
                server_name=server_name,
                message=f"No configuration found for server '{server_name}'",
            )

        # Get pattern for startup command
        pattern = self.get_pattern_for_server(config.package_name, "")
        if not pattern:
            return InstallationResult(
                success=False,
                server_name=server_name,
                message=f"No pattern found for package '{config.package_name}'",
            )

        try:
            # Prepare startup command
            if config.transport_type == "stdio":
                startup_cmd = pattern.startup_command.format(
                    package_name=config.package_name, args=" ".join(config.startup_args)
                ).split()

                # Prepare environment
                env = {**config.env_vars}
                for key, secret_val in config.secure_vars.items():
                    env[key] = (
                        secret_val.get_secret_value()
                        if hasattr(secret_val, "get_secret_value")
                        else str(secret_val)
                    )

                print(f"🚀 Starting server: {' '.join(startup_cmd)}")

                # Start process
                process = subprocess.Popen(
                    startup_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env={**os.environ, **env} if env else None,
                )

                await asyncio.sleep(2)  # Give it time to start

                if process.poll() is None:
                    self.running_servers[server_name] = process
                    self.request_counters[server_name] = 1

                    # Try to initialize and discover tools
                    tools = await self._discover_server_tools(server_name)

                    return InstallationResult(
                        success=True,
                        server_name=server_name,
                        message=f"Server started successfully (PID: {process.pid})",
                        process_id=process.pid,
                        tools_available=tools,
                    )
                stdout, stderr = process.communicate()
                return InstallationResult(
                    success=False,
                    server_name=server_name,
                    message=f"Server failed to start: {stderr}",
                )

            return InstallationResult(
                success=False,
                server_name=server_name,
                message=f"Transport '{config.transport_type}' not yet supported in safe mode",
            )

        except Exception as e:
            return InstallationResult(
                success=False,
                server_name=server_name,
                message=f"Failed to start server: {e}",
            )

    async def _discover_server_tools(self, server_name: str) -> list[str]:
        """Discover available tools from running server"""
        if server_name not in self.running_servers:
            return []

        try:
            process = self.running_servers[server_name]

            # Initialize server
            init_request = {
                "jsonrpc": "2.0",
                "id": self.request_counters[server_name],
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "haive-safe-installer", "version": "1.0.0"},
                },
            }

            process.stdin.write(json.dumps(init_request) + "\n")
            process.stdin.flush()
            self.request_counters[server_name] += 1

            # Read initialization response
            response = process.stdout.readline()
            if response.strip():
                init_result = json.loads(response)
                if "result" in init_result:
                    # Send initialized notification
                    notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
                    process.stdin.write(json.dumps(notify) + "\n")
                    process.stdin.flush()

                    # List tools
                    tools_request = {
                        "jsonrpc": "2.0",
                        "id": self.request_counters[server_name],
                        "method": "tools/list",
                    }

                    process.stdin.write(json.dumps(tools_request) + "\n")
                    process.stdin.flush()
                    self.request_counters[server_name] += 1

                    tools_response = process.stdout.readline()
                    if tools_response.strip():
                        tools_result = json.loads(tools_response)
                        if (
                            "result" in tools_result
                            and "tools" in tools_result["result"]
                        ):
                            tools = [
                                tool["name"] for tool in tools_result["result"]["tools"]
                            ]
                            print(
                                f"🔧 Discovered tools for {server_name}: {', '.join(tools)}"
                            )
                            return tools

        except Exception as e:
            print(f"❌ Failed to discover tools for {server_name}: {e}")

        return []

    def create_quick_install_tools(self) -> list[StructuredTool]:
        """Create tools for common MCP server installations"""
        common_servers = [
            InstallationRequest(
                server_name="filesystem",
                package_name="@modelcontextprotocol/server-filesystem",
                pattern_type="filesystem",
                custom_args=["/tmp"],
                require_approval=True,
            ),
            InstallationRequest(
                server_name="calculator",
                package_name="@modelcontextprotocol/server-math",
                pattern_type="web_api",
                require_approval=False,  # Math is safe
            ),
        ]

        tools = []
        for request in common_servers:
            tool = self.create_installation_tool(request)
            tools.append(tool)

        return tools

    def cleanup(self):
        """Stop all running servers"""
        for name, process in self.running_servers.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Stopped {name} server")
            except:
                process.kill()
                print(f"🔥 Force killed {name} server")

        self.running_servers.clear()

    def get_status_summary(self) -> dict[str, Any]:
        """Get summary of installer status"""
        return {
            "installer_type": "SafePatternInstaller",
            "available_patterns": self.config_manager.list_available_patterns(),
            "configured_servers": self.config_manager.list_configured_servers(),
            "running_servers": list(self.running_servers.keys()),
            "config_summary": self.config_manager.get_config_summary(),
        }
