"""MCP server testing and validation tools.

This module provides tools for testing MCP server configurations, validating
connections, and ensuring servers are working correctly before use in production.

The testing system provides:
    - Connection testing for individual servers
    - Batch testing for multiple servers
    - Health monitoring and diagnostics
    - Performance benchmarking
    - Configuration validation

Classes:
    MCPServerTester: Main testing interface
    TestResult: Results from server testing
    HealthMonitor: Continuous health monitoring

Example:
    Testing server configurations::\n
        from haive.mcp.tools import MCPServerTester
        from haive.mcp.config import MCPServerConfig

        # Test individual server
        tester = MCPServerTester()

        server_config = MCPServerConfig(
            name="test_server",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"]
        )

        result = await tester.test_server(server_config)
        if result.success:
            print(f"✅ {server_config.name} is working")
        else:
            print(f"❌ {server_config.name} failed: {result.error}")

        # Test multiple servers
        results = await tester.test_multiple_servers([server_config])

        # Monitor health
        monitor = tester.create_health_monitor()
        await monitor.start_monitoring([server_config])

Note:
    Server testing requires the actual MCP packages to be installed
    and may need appropriate environment variables.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from haive.mcp.config import MCPConfig, MCPServerConfig

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result from testing an MCP server."""

    server_name: str
    success: bool
    response_time: float  # seconds
    error: str | None = None
    tools_discovered: int = 0
    capabilities_found: list[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.capabilities_found is None:
            self.capabilities_found = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class HealthStatus:
    """Health status for a server."""

    server_name: str
    healthy: bool
    last_check: float
    consecutive_failures: int = 0
    average_response_time: float = 0.0
    uptime_percentage: float = 100.0


class HealthMonitor:
    """Continuous health monitoring for MCP servers."""

    def __init__(self, check_interval: int = 60):
        """Initialize health monitor.

        Args:
            check_interval: Seconds between health checks
        """
        self.check_interval = check_interval
        self.monitoring = False
        self.health_status: dict[str, HealthStatus] = {}
        self.monitor_task = None

    async def start_monitoring(self, servers: list[MCPServerConfig]):
        """Start monitoring the specified servers.

        Args:
            servers: List of server configurations to monitor
        """
        self.monitoring = True

        # Initialize health status
        for server in servers:
            self.health_status[server.name] = HealthStatus(
                server_name=server.name, healthy=True, last_check=time.time()
            )

        # Start monitoring task
        self.monitor_task = asyncio.create_task(self._monitor_loop(servers))

        logger.info(f"Started monitoring {len(servers)} servers")

    async def stop_monitoring(self):
        """Stop health monitoring."""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped health monitoring")

    async def _monitor_loop(self, servers: list[MCPServerConfig]):
        """Main monitoring loop."""
        tester = MCPServerTester()

        while self.monitoring:
            try:
                # Test all servers
                results = await tester.test_multiple_servers(servers, timeout=30)

                # Update health status
                for result in results:
                    if result.server_name in self.health_status:
                        status = self.health_status[result.server_name]
                        status.last_check = time.time()

                        if result.success:
                            status.healthy = True
                            status.consecutive_failures = 0
                            # Update average response time
                            if status.average_response_time == 0:
                                status.average_response_time = result.response_time
                            else:
                                status.average_response_time = (
                                    status.average_response_time * 0.8
                                    + result.response_time * 0.2
                                )
                        else:
                            status.consecutive_failures += 1
                            if status.consecutive_failures >= 3:
                                status.healthy = False

                # Wait before next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    def get_health_report(self) -> dict[str, HealthStatus]:
        """Get current health status for all monitored servers."""
        return self.health_status.copy()

    def get_unhealthy_servers(self) -> list[str]:
        """Get list of unhealthy server names."""
        return [
            name for name, status in self.health_status.items() if not status.healthy
        ]


class MCPServerTester:
    """Main testing interface for MCP servers."""

    def __init__(self):
        """Initialize server tester."""
        self.test_history: list[TestResult] = []

    async def test_server(
        self, server_config: MCPServerConfig, timeout: int = 60
    ) -> TestResult:
        """Test a single MCP server configuration.

        Args:
            server_config: Server configuration to test
            timeout: Timeout in seconds for the test

        Returns:
            TestResult with test outcome
        """
        start_time = time.time()

        try:
            # Import MCP client dependencies
            try:
                from langchain_mcp_adapters import MCPClient
            except ImportError:
                return TestResult(
                    server_name=server_config.name,
                    success=False,
                    response_time=0.0,
                    error="MCP client dependencies not available (install langchain-mcp-adapters)",
                )

            # Create test configuration
            test_config = {
                server_config.name: self._create_client_config(server_config)
            }

            # Test connection
            client = None
            try:
                client = MultiServerMCPClient(test_config)

                # Try to get tools as a connection test
                tools = await asyncio.wait_for(
                    client.get_tools(server_name=server_config.name), timeout=timeout
                )

                response_time = time.time() - start_time

                # Analyze discovered tools
                tools_count = len(tools) if tools else 0
                capabilities = self._analyze_capabilities(tools, server_config)
                warnings = self._check_for_warnings(server_config, tools)

                result = TestResult(
                    server_name=server_config.name,
                    success=True,
                    response_time=response_time,
                    tools_discovered=tools_count,
                    capabilities_found=capabilities,
                    warnings=warnings,
                )

            finally:
                # Clean up client
                if client and hasattr(client, "close"):
                    try:
                        await client.close()
                    except Exception:
                        pass

        except TimeoutError:
            result = TestResult(
                server_name=server_config.name,
                success=False,
                response_time=timeout,
                error=f"Server did not respond within {timeout}s",
            )

        except Exception as e:
            result = TestResult(
                server_name=server_config.name,
                success=False,
                response_time=time.time() - start_time,
                error=str(e),
            )

        # Store result in history
        self.test_history.append(result)

        return result

    async def test_multiple_servers(
        self, servers: list[MCPServerConfig], timeout: int = 60, parallel: bool = True
    ) -> list[TestResult]:
        """Test multiple servers.

        Args:
            servers: List of server configurations to test
            timeout: Timeout per server in seconds
            parallel: Whether to test servers in parallel

        Returns:
            List of TestResult objects
        """
        if parallel:
            # Test in parallel for speed
            tasks = [self.test_server(server, timeout) for server in servers]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    final_results.append(
                        TestResult(
                            server_name=servers[i].name,
                            success=False,
                            response_time=0.0,
                            error=f"Test failed with exception: {result}",
                        )
                    )
                else:
                    final_results.append(result)

            return final_results

        # Test sequentially
        results = []
        for server in servers:
            result = await self.test_server(server, timeout)
            results.append(result)

        return results

    async def test_config(self, config: MCPConfig) -> dict[str, TestResult]:
        """Test an entire MCP configuration.

        Args:
            config: MCP configuration to test

        Returns:
            Dictionary mapping server names to test results
        """
        servers = list(config.servers.values())
        results = await self.test_multiple_servers(servers)

        return {result.server_name: result for result in results}

    def _create_client_config(self, server_config: MCPServerConfig) -> dict[str, Any]:
        """Create client configuration from server config."""
        config = {}

        if server_config.transport == "stdio":
            config["command"] = server_config.command
            config["args"] = server_config.args
            config["transport"] = "stdio"
        elif server_config.transport in ["sse", "streamable_http"]:
            config["url"] = server_config.url
            config["transport"] = server_config.transport

        # Add environment variables
        if server_config.env:
            config["env"] = server_config.env

        return config

    def _analyze_capabilities(
        self, tools: list[Any], server_config: MCPServerConfig
    ) -> list[str]:
        """Analyze discovered tools to determine capabilities."""
        capabilities = set()

        if not tools:
            return list(capabilities)

        # Analyze tool names for capability hints
        for tool in tools:
            tool_name = getattr(tool, "name", str(tool)).lower()

            # File system capabilities
            if any(
                keyword in tool_name
                for keyword in ["file", "read", "write", "directory"]
            ):
                capabilities.add("filesystem")

            # Database capabilities
            if any(
                keyword in tool_name
                for keyword in ["query", "sql", "database", "table"]
            ):
                capabilities.add("database")

            # Web capabilities
            if any(keyword in tool_name for keyword in ["http", "fetch", "web", "api"]):
                capabilities.add("web")

            # Git capabilities
            if any(
                keyword in tool_name for keyword in ["git", "repo", "commit", "branch"]
            ):
                capabilities.add("git")

            # Search capabilities
            if any(keyword in tool_name for keyword in ["search", "find", "lookup"]):
                capabilities.add("search")

        return list(capabilities)

    def _check_for_warnings(
        self, server_config: MCPServerConfig, tools: list[Any]
    ) -> list[str]:
        """Check for potential issues and generate warnings."""
        warnings = []

        # Check if no tools were discovered
        if not tools:
            warnings.append("No tools discovered - server may not be fully configured")

        # Check for missing environment variables
        if server_config.env:

            missing_vars = [
                var for var in server_config.env.keys() if var not in os.environ
            ]
            if missing_vars:
                warnings.append(
                    f"Environment variables not set: {', '.join(missing_vars)}"
                )

        # Check for common authentication requirements
        server_name = server_config.name.lower()
        if any(
            service in server_name
            for service in ["github", "gmail", "notion", "calendar"]
        ):
            if not server_config.env:
                warnings.append(
                    "Server likely requires authentication but no env vars configured"
                )

        return warnings

    def create_health_monitor(self, check_interval: int = 60) -> HealthMonitor:
        """Create a health monitor instance.

        Args:
            check_interval: Seconds between health checks

        Returns:
            HealthMonitor instance
        """
        return HealthMonitor(check_interval)

    def get_test_history(self) -> list[TestResult]:
        """Get history of all test results."""
        return self.test_history.copy()

    def get_success_rate(self, server_name: str | None = None) -> float:
        """Get success rate for a server or overall.

        Args:
            server_name: Specific server name, or None for overall

        Returns:
            Success rate as percentage (0.0 to 100.0)
        """
        if server_name:
            relevant_tests = [
                test for test in self.test_history if test.server_name == server_name
            ]
        else:
            relevant_tests = self.test_history

        if not relevant_tests:
            return 0.0

        successful = sum(1 for test in relevant_tests if test.success)
        return (successful / len(relevant_tests)) * 100.0

    def generate_test_report(self) -> dict[str, Any]:
        """Generate a comprehensive test report.

        Returns:
            Dictionary with test statistics and details
        """
        if not self.test_history:
            return {"error": "No tests performed yet"}

        # Group by server
        by_server = {}
        for test in self.test_history:
            if test.server_name not in by_server:
                by_server[test.server_name] = []
            by_server[test.server_name].append(test)

        # Calculate statistics
        total_tests = len(self.test_history)
        successful_tests = sum(1 for test in self.test_history if test.success)

        server_stats = {}
        for server_name, tests in by_server.items():
            successful = sum(1 for test in tests if test.success)
            avg_response_time = sum(test.response_time for test in tests) / len(tests)

            server_stats[server_name] = {
                "total_tests": len(tests),
                "successful": successful,
                "success_rate": (successful / len(tests)) * 100.0,
                "average_response_time": avg_response_time,
                "last_test": tests[-1].success if tests else False,
            }

        return {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "overall_success_rate": (successful_tests / total_tests) * 100.0,
                "servers_tested": len(by_server),
            },
            "server_statistics": server_stats,
            "recommendations": self._generate_recommendations(by_server),
        }

    def _generate_recommendations(
        self, by_server: dict[str, list[TestResult]]
    ) -> list[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        for server_name, tests in by_server.items():
            latest_test = tests[-1]
            success_rate = sum(1 for test in tests if test.success) / len(tests)

            if success_rate < 0.5:
                recommendations.append(
                    f"Server '{server_name}' has low success rate ({
                        success_rate:.1%}) - check configuration"
                )

            if latest_test.response_time > 30:
                recommendations.append(
                    f"Server '{server_name}' has slow response time ({
                        latest_test.response_time:.1f}s)"
                )

            if latest_test.warnings:
                recommendations.append(
                    f"Server '{server_name}' has warnings: {
                        '; '.join(
                            latest_test.warnings)}"
                )

        return recommendations
