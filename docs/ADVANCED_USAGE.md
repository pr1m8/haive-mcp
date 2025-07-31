# Advanced Usage Guide for haive-mcp

This guide covers advanced patterns and techniques for using haive-mcp in production environments.

## Table of Contents

1. [Production Deployment](#production-deployment)
2. [Custom Discovery Logic](#custom-discovery-logic)
3. [Advanced HITL Workflows](#advanced-hitl-workflows)
4. [Performance Optimization](#performance-optimization)
5. [Multi-Agent Orchestration](#multi-agent-orchestration)
6. [Custom MCP Servers](#custom-mcp-servers)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Security Considerations](#security-considerations)

## Production Deployment

### Configuration Management

Use environment-specific configurations:

```python
import os
from haive.mcp.config import MCPConfig, MCPServerConfig

class MCPConfigManager:
    """Manage MCP configurations for different environments."""

    @staticmethod
    def get_config(environment: str = None) -> MCPConfig:
        env = environment or os.getenv("ENVIRONMENT", "development")

        if env == "production":
            return MCPConfigManager._get_production_config()
        elif env == "staging":
            return MCPConfigManager._get_staging_config()
        else:
            return MCPConfigManager._get_development_config()

    @staticmethod
    def _get_production_config() -> MCPConfig:
        """Production configuration with strict controls."""
        return MCPConfig(
            enabled=True,
            auto_discover=False,  # No auto-discovery in production
            servers={
                "postgres": MCPServerConfig(
                    name="postgres",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-postgres"],
                    env={
                        "DATABASE_URL": os.getenv("PROD_DATABASE_URL"),
                        "SSL_MODE": "require"
                    }
                ),
                "redis": MCPServerConfig(
                    name="redis",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-redis"],
                    env={
                        "REDIS_URL": os.getenv("PROD_REDIS_URL")
                    }
                )
            },
            retry_attempts=5,
            timeout=60
        )
```

### Graceful Startup and Shutdown

```python
import asyncio
import signal
from contextlib import asynccontextmanager

class MCPApplication:
    """Production MCP application with lifecycle management."""

    def __init__(self):
        self.agent = None
        self.manager = None
        self.health_monitor_task = None
        self.shutdown_event = asyncio.Event()

    @asynccontextmanager
    async def lifespan(self):
        """Manage application lifecycle."""
        try:
            # Startup
            await self.startup()
            yield
        finally:
            # Shutdown
            await self.shutdown()

    async def startup(self):
        """Initialize MCP components."""
        logger.info("Starting MCP application...")

        # Create manager
        self.manager = MCPManager(
            auto_health_check=True,
            health_check_interval=60.0,
            max_retry_attempts=3
        )

        # Create agent
        config = MCPConfigManager.get_config()
        self.agent = MCPAgent(
            engine=AugLLMConfig(),
            mcp_config=config
        )

        # Setup agent
        await self.agent.setup()

        # Start health monitoring
        self.health_monitor_task = asyncio.create_task(
            self.monitor_health()
        )

        logger.info("MCP application started successfully")

    async def shutdown(self):
        """Cleanup MCP components."""
        logger.info("Shutting down MCP application...")

        # Signal shutdown
        self.shutdown_event.set()

        # Cancel health monitoring
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass

        # Shutdown manager
        if self.manager:
            await self.manager.shutdown()

        logger.info("MCP application shutdown complete")

    async def monitor_health(self):
        """Monitor server health continuously."""
        while not self.shutdown_event.is_set():
            try:
                status = self.manager.get_all_server_status()

                # Log health metrics
                logger.info(
                    f"MCP Health: Connected={status['summary']['connected_servers']}, "
                    f"Failed={status['summary']['failed_servers']}, "
                    f"Tools={status['summary']['total_tools']}"
                )

                # Alert on failures
                if status['summary']['failed_servers'] > 0:
                    await self.alert_on_failure(status)

                # Wait for next check
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
```

## Custom Discovery Logic

### Capability Mapping System

Create sophisticated capability detection:

```python
from typing import List, Dict, Set
import re

class CapabilityAnalyzer:
    """Advanced capability analysis for MCP server discovery."""

    def __init__(self):
        # Define capability patterns
        self.patterns = {
            "database": [
                r"\b(database|db|sql|query|table|postgres|mysql|sqlite)\b",
                r"\b(select|insert|update|delete)\s+\b",
                r"\bconnect\s+to\s+\w+\s+database\b"
            ],
            "filesystem": [
                r"\b(file|folder|directory|path|read|write|save)\b",
                r"\b(create|delete|modify)\s+\w+\.(txt|json|md|csv)\b",
                r"\bsave\s+.+\s+to\s+file\b"
            ],
            "web_search": [
                r"\b(search|google|bing|web|internet|find|look up)\b",
                r"\bsearch\s+(for|about)\s+\w+\b",
                r"\bfind\s+.+\s+online\b"
            ],
            "github": [
                r"\b(github|repo|repository|pr|pull request|issue)\b",
                r"\b(clone|push|pull|commit)\s+\w+\b",
                r"\bgit\s+\w+\b"
            ],
            "api": [
                r"\b(api|rest|endpoint|webhook|http)\b",
                r"\b(get|post|put|delete)\s+request\b",
                r"\bcall\s+\w+\s+api\b"
            ]
        }

        # Define capability relationships
        self.relationships = {
            "database": ["data_analysis", "reporting"],
            "filesystem": ["data_export", "logging"],
            "web_search": ["research", "information_gathering"],
            "github": ["code_management", "collaboration"],
            "api": ["integration", "data_sync"]
        }

    def analyze_message(self, message: str) -> Set[str]:
        """Analyze message to detect needed capabilities."""
        message_lower = message.lower()
        detected = set()

        # Check patterns
        for capability, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    detected.add(capability)
                    break

        # Add related capabilities
        related = set()
        for cap in detected:
            if cap in self.relationships:
                related.update(self.relationships[cap])

        return detected.union(related)

    def get_server_recommendations(self, capabilities: Set[str]) -> List[Dict]:
        """Get server recommendations for capabilities."""
        # Map capabilities to servers
        capability_to_servers = {
            "database": [
                "modelcontextprotocol/server-postgres",
                "modelcontextprotocol/server-sqlite",
                "modelcontextprotocol/server-mysql"
            ],
            "filesystem": [
                "modelcontextprotocol/server-filesystem"
            ],
            "web_search": [
                "modelcontextprotocol/server-brave-search",
                "modelcontextprotocol/server-google-search"
            ],
            "github": [
                "modelcontextprotocol/server-github"
            ]
        }

        recommendations = []
        for cap in capabilities:
            if cap in capability_to_servers:
                for server in capability_to_servers[cap]:
                    recommendations.append({
                        "server": server,
                        "capability": cap,
                        "priority": self._calculate_priority(server, cap)
                    })

        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        return recommendations

    def _calculate_priority(self, server: str, capability: str) -> float:
        """Calculate server priority based on various factors."""
        # Example priority calculation
        base_priority = 1.0

        # Prefer official servers
        if server.startswith("modelcontextprotocol/"):
            base_priority += 0.5

        # Prefer well-known capabilities
        if capability in ["database", "filesystem", "web_search"]:
            base_priority += 0.3

        return base_priority
```

### Custom Discovery Agent

```python
class AdvancedDiscoveryAgent(IntelligentMCPAgent):
    """Agent with advanced discovery capabilities."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capability_analyzer = CapabilityAnalyzer()
        self.discovery_cache = {}

    async def _analyze_capability_needs(self, user_message: str) -> List[str]:
        """Enhanced capability analysis with caching."""
        # Check cache
        cache_key = hash(user_message.lower())
        if cache_key in self.discovery_cache:
            return self.discovery_cache[cache_key]

        # Analyze with custom analyzer
        capabilities = self.capability_analyzer.analyze_message(user_message)

        # Get LLM analysis for complex cases
        if not capabilities or len(user_message) > 200:
            llm_capabilities = await super()._analyze_capability_needs(user_message)
            capabilities.update(llm_capabilities)

        # Cache result
        result = list(capabilities)
        self.discovery_cache[cache_key] = result

        return result

    async def _get_server_recommendations(
        self,
        capabilities: List[str]
    ) -> List[ServerRecommendation]:
        """Get prioritized server recommendations."""
        recommendations = self.capability_analyzer.get_server_recommendations(
            set(capabilities)
        )

        # Convert to ServerRecommendation objects
        server_recs = []
        for rec in recommendations[:5]:  # Top 5
            config = await self._generate_server_config(rec["server"])
            server_recs.append(
                ServerRecommendation(
                    server_name=rec["server"],
                    reason=f"Provides {rec['capability']} capability",
                    capabilities=[rec["capability"]],
                    confidence=rec["priority"],
                    config=config,
                    alternative_servers=[]
                )
            )

        return server_recs
```

## Advanced HITL Workflows

### Multi-Stage Approval System

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

class ApprovalLevel(Enum):
    AUTO_APPROVE = "auto"
    TEAM_LEAD = "team_lead"
    SECURITY_REVIEW = "security"
    EXECUTIVE = "executive"

@dataclass
class ApprovalPolicy:
    """Define approval policies for different scenarios."""
    server_pattern: str
    required_level: ApprovalLevel
    timeout_minutes: int
    auto_approve_list: List[str]
    block_list: List[str]

class EnterpriseApprovalSystem:
    """Enterprise-grade approval system for MCP installations."""

    def __init__(self):
        self.policies = [
            ApprovalPolicy(
                server_pattern=".*filesystem.*",
                required_level=ApprovalLevel.TEAM_LEAD,
                timeout_minutes=30,
                auto_approve_list=["read_file"],
                block_list=["delete_file", "write_sensitive"]
            ),
            ApprovalPolicy(
                server_pattern=".*database.*",
                required_level=ApprovalLevel.SECURITY_REVIEW,
                timeout_minutes=60,
                auto_approve_list=[],
                block_list=["drop_table", "delete_all"]
            ),
            ApprovalPolicy(
                server_pattern=".*production.*",
                required_level=ApprovalLevel.EXECUTIVE,
                timeout_minutes=120,
                auto_approve_list=[],
                block_list=[]
            )
        ]

        self.approval_queue = asyncio.Queue()
        self.approval_handlers = {}

    async def request_approval(
        self,
        request: HITLApprovalRequest
    ) -> bool:
        """Process approval request through policy system."""
        server_name = request.recommendation.server_name

        # Find matching policy
        policy = self._find_policy(server_name)
        if not policy:
            # Default deny for unknown servers
            logger.warning(f"No policy for server: {server_name}")
            return False

        # Check block list
        if self._is_blocked(request, policy):
            logger.warning(f"Server blocked by policy: {server_name}")
            return False

        # Check auto-approve
        if self._can_auto_approve(request, policy):
            logger.info(f"Auto-approved: {server_name}")
            return True

        # Route to appropriate approval handler
        return await self._route_approval(request, policy)

    def _find_policy(self, server_name: str) -> Optional[ApprovalPolicy]:
        """Find matching policy for server."""
        for policy in self.policies:
            if re.match(policy.server_pattern, server_name):
                return policy
        return None

    def _is_blocked(
        self,
        request: HITLApprovalRequest,
        policy: ApprovalPolicy
    ) -> bool:
        """Check if server or capabilities are blocked."""
        capabilities = request.recommendation.capabilities
        return any(cap in policy.block_list for cap in capabilities)

    def _can_auto_approve(
        self,
        request: HITLApprovalRequest,
        policy: ApprovalPolicy
    ) -> bool:
        """Check if can auto-approve based on policy."""
        if policy.required_level == ApprovalLevel.AUTO_APPROVE:
            return True

        capabilities = request.recommendation.capabilities
        return all(cap in policy.auto_approve_list for cap in capabilities)

    async def _route_approval(
        self,
        request: HITLApprovalRequest,
        policy: ApprovalPolicy
    ) -> bool:
        """Route to appropriate approval handler."""
        handler = self.approval_handlers.get(policy.required_level)
        if not handler:
            logger.error(f"No handler for level: {policy.required_level}")
            return False

        # Set timeout
        request.response_deadline = datetime.now() + timedelta(
            minutes=policy.timeout_minutes
        )

        # Send to handler
        return await handler(request)
```

### Slack Integration for Approvals

```python
import aiohttp
from typing import Dict

class SlackApprovalHandler:
    """Handle approvals through Slack."""

    def __init__(self, webhook_url: str, channel: str = "#mcp-approvals"):
        self.webhook_url = webhook_url
        self.channel = channel
        self.pending_approvals: Dict[str, HITLApprovalRequest] = {}

    async def handle_approval(self, request: HITLApprovalRequest) -> bool:
        """Send approval request to Slack and wait for response."""
        # Create Slack message
        message = self._create_approval_message(request)

        # Send to Slack
        async with aiohttp.ClientSession() as session:
            await session.post(self.webhook_url, json=message)

        # Store pending approval
        self.pending_approvals[request.request_id] = request

        # Wait for response (simplified - in production use webhooks)
        return await self._wait_for_response(request)

    def _create_approval_message(self, request: HITLApprovalRequest) -> Dict:
        """Create Slack message with approval buttons."""
        return {
            "channel": self.channel,
            "text": f"MCP Server Approval Request: {request.recommendation.server_name}",
            "attachments": [{
                "color": "warning",
                "fields": [
                    {
                        "title": "Server",
                        "value": request.recommendation.server_name,
                        "short": True
                    },
                    {
                        "title": "Reason",
                        "value": request.recommendation.reason,
                        "short": True
                    },
                    {
                        "title": "Capabilities",
                        "value": ", ".join(request.recommendation.capabilities),
                        "short": False
                    }
                ],
                "actions": [
                    {
                        "name": "approval",
                        "text": "Approve",
                        "type": "button",
                        "value": f"approve:{request.request_id}",
                        "style": "primary"
                    },
                    {
                        "name": "approval",
                        "text": "Reject",
                        "type": "button",
                        "value": f"reject:{request.request_id}",
                        "style": "danger"
                    }
                ]
            }]
        }
```

## Performance Optimization

### Connection Pooling

```python
class MCPConnectionPool:
    """Connection pool for MCP servers."""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.pools: Dict[str, List[Any]] = {}
        self.locks: Dict[str, asyncio.Lock] = {}

    async def get_connection(self, server_name: str, config: MCPServerConfig):
        """Get connection from pool or create new one."""
        if server_name not in self.locks:
            self.locks[server_name] = asyncio.Lock()
            self.pools[server_name] = []

        async with self.locks[server_name]:
            # Try to get from pool
            if self.pools[server_name]:
                return self.pools[server_name].pop()

            # Create new connection
            return await self._create_connection(config)

    async def return_connection(self, server_name: str, connection: Any):
        """Return connection to pool."""
        async with self.locks[server_name]:
            if len(self.pools[server_name]) < self.max_connections:
                self.pools[server_name].append(connection)
            else:
                await self._close_connection(connection)
```

### Lazy Loading and Caching

```python
class CachedMCPManager(MCPManager):
    """MCP Manager with caching capabilities."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tool_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_update = {}

    async def get_all_tools(self, refresh: bool = False) -> List[Any]:
        """Get tools with caching."""
        cache_key = "all_tools"
        now = time.time()

        # Check cache validity
        if (not refresh and
            cache_key in self.tool_cache and
            now - self.last_cache_update.get(cache_key, 0) < self.cache_ttl):
            return self.tool_cache[cache_key]

        # Refresh and cache
        tools = await super().get_all_tools(refresh=True)
        self.tool_cache[cache_key] = tools
        self.last_cache_update[cache_key] = now

        return tools
```

### Batch Operations

```python
class BatchMCPOperations:
    """Batch operations for efficiency."""

    @staticmethod
    async def add_servers_batch(
        manager: MCPManager,
        configs: List[Tuple[str, MCPServerConfig]],
        max_concurrent: int = 5
    ) -> List[MCPRegistrationResult]:
        """Add multiple servers concurrently with limit."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def add_with_limit(name: str, config: MCPServerConfig):
            async with semaphore:
                return await manager.add_server(name, config)

        tasks = [
            add_with_limit(name, config)
            for name, config in configs
        ]

        return await asyncio.gather(*tasks)
```

## Multi-Agent Orchestration

### Coordinator Pattern

```python
class MCPCoordinator:
    """Coordinate multiple agents with shared MCP resources."""

    def __init__(self):
        self.agents: Dict[str, MCPAgent] = {}
        self.shared_manager = MCPManager()
        self.resource_locks: Dict[str, asyncio.Lock] = {}

    async def register_agent(
        self,
        name: str,
        agent: MCPAgent,
        shared_servers: List[str] = None
    ):
        """Register agent with coordinator."""
        self.agents[name] = agent

        # Setup shared servers
        if shared_servers:
            for server in shared_servers:
                if server not in self.resource_locks:
                    self.resource_locks[server] = asyncio.Lock()

    async def execute_with_shared_resource(
        self,
        agent_name: str,
        server_name: str,
        operation: Callable
    ):
        """Execute operation with exclusive access to resource."""
        if server_name not in self.resource_locks:
            raise ValueError(f"Server {server_name} not registered as shared")

        async with self.resource_locks[server_name]:
            agent = self.agents[agent_name]
            return await operation(agent)
```

### Pipeline Pattern

```python
class MCPPipeline:
    """Pipeline for multi-agent workflows."""

    def __init__(self):
        self.stages: List[Dict[str, Any]] = []

    def add_stage(
        self,
        name: str,
        agent: MCPAgent,
        transform: Optional[Callable] = None
    ):
        """Add processing stage to pipeline."""
        self.stages.append({
            "name": name,
            "agent": agent,
            "transform": transform or (lambda x: x)
        })
        return self

    async def execute(self, initial_input: Any) -> Any:
        """Execute pipeline stages sequentially."""
        result = initial_input

        for stage in self.stages:
            logger.info(f"Executing stage: {stage['name']}")

            # Process with agent
            agent_result = await stage["agent"].arun({
                "messages": [{"role": "user", "content": str(result)}]
            })

            # Transform for next stage
            result = stage["transform"](agent_result)

        return result

# Example usage
pipeline = MCPPipeline()
pipeline.add_stage("research", research_agent)
pipeline.add_stage("analysis", analysis_agent, transform=extract_data)
pipeline.add_stage("report", report_agent, transform=format_report)

result = await pipeline.execute("Analyze market trends")
```

## Custom MCP Servers

### Creating Your Own Server

```python
# Example custom MCP server for proprietary tools
class CustomMCPServer:
    """Template for custom MCP server."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Callable]:
        """Register available tools."""
        return {
            "custom_analysis": self.custom_analysis,
            "proprietary_search": self.proprietary_search
        }

    async def custom_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Custom analysis tool."""
        # Your proprietary logic here
        return {"result": "analysis complete"}

    async def proprietary_search(self, query: str) -> List[Dict[str, Any]]:
        """Search proprietary database."""
        # Your search logic here
        return [{"title": "Result 1", "content": "..."}]
```

## Monitoring and Observability

### Metrics Collection

```python
from dataclasses import dataclass
from datetime import datetime
import prometheus_client as prom

@dataclass
class MCPMetrics:
    """Metrics for MCP operations."""

    # Counters
    servers_added = prom.Counter(
        'mcp_servers_added_total',
        'Total MCP servers added'
    )

    servers_failed = prom.Counter(
        'mcp_servers_failed_total',
        'Total MCP server failures'
    )

    tools_called = prom.Counter(
        'mcp_tools_called_total',
        'Total MCP tool calls',
        ['server', 'tool']
    )

    # Gauges
    active_servers = prom.Gauge(
        'mcp_active_servers',
        'Number of active MCP servers'
    )

    available_tools = prom.Gauge(
        'mcp_available_tools',
        'Number of available tools'
    )

    # Histograms
    connection_duration = prom.Histogram(
        'mcp_connection_duration_seconds',
        'MCP server connection duration'
    )

    tool_duration = prom.Histogram(
        'mcp_tool_duration_seconds',
        'MCP tool execution duration',
        ['server', 'tool']
    )

class MonitoredMCPManager(MCPManager):
    """MCP Manager with metrics collection."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics = MCPMetrics()

    async def add_server(
        self,
        server_name: str,
        config: MCPServerConfig,
        **kwargs
    ) -> MCPRegistrationResult:
        """Add server with metrics."""
        start_time = time.time()

        try:
            result = await super().add_server(server_name, config, **kwargs)

            if result.success:
                self.metrics.servers_added.inc()
                self.metrics.active_servers.inc()
            else:
                self.metrics.servers_failed.inc()

            return result

        finally:
            duration = time.time() - start_time
            self.metrics.connection_duration.observe(duration)
```

### Logging Best Practices

```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

class LoggedMCPAgent(IntelligentMCPAgent):
    """Agent with structured logging."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = structlog.get_logger().bind(
            agent_name=self.name,
            agent_type="IntelligentMCPAgent"
        )

    async def arun(self, inputs: Dict[str, Any]) -> Any:
        """Run with detailed logging."""
        request_id = str(uuid.uuid4())
        logger = self.logger.bind(request_id=request_id)

        logger.info(
            "agent_execution_started",
            input_length=len(str(inputs))
        )

        try:
            result = await super().arun(inputs)

            logger.info(
                "agent_execution_completed",
                output_length=len(str(result)),
                servers_used=list(self.mcp_manager._servers.keys())
            )

            return result

        except Exception as e:
            logger.error(
                "agent_execution_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
```

## Security Considerations

### Server Allowlisting

```python
class SecureMCPManager(MCPManager):
    """MCP Manager with security controls."""

    def __init__(self, allowed_servers: List[str], **kwargs):
        super().__init__(**kwargs)
        self.allowed_servers = set(allowed_servers)
        self.blocked_commands = ["rm", "del", "format"]

    async def add_server(
        self,
        server_name: str,
        config: MCPServerConfig,
        **kwargs
    ) -> MCPRegistrationResult:
        """Add server with security checks."""
        # Check allowlist
        if not self._is_allowed_server(config):
            return MCPRegistrationResult(
                server_name=server_name,
                success=False,
                status=MCPServerStatus.FAILED,
                error_message="Server not in allowlist"
            )

        # Check for dangerous commands
        if self._has_dangerous_commands(config):
            return MCPRegistrationResult(
                server_name=server_name,
                success=False,
                status=MCPServerStatus.FAILED,
                error_message="Dangerous commands detected"
            )

        return await super().add_server(server_name, config, **kwargs)

    def _is_allowed_server(self, config: MCPServerConfig) -> bool:
        """Check if server is allowed."""
        # Check by package name in args
        if config.args:
            for arg in config.args:
                if any(allowed in arg for allowed in self.allowed_servers):
                    return True
        return False

    def _has_dangerous_commands(self, config: MCPServerConfig) -> bool:
        """Check for dangerous commands."""
        if config.command in self.blocked_commands:
            return True

        if config.args:
            return any(
                cmd in arg
                for cmd in self.blocked_commands
                for arg in config.args
            )

        return False
```

### Environment Isolation

```python
class IsolatedMCPEnvironment:
    """Run MCP servers in isolated environments."""

    @staticmethod
    def get_sandboxed_config(config: MCPServerConfig) -> MCPServerConfig:
        """Add sandboxing to server config."""
        sandboxed = config.model_copy()

        # Add isolation environment variables
        sandboxed.env = sandboxed.env or {}
        sandboxed.env.update({
            "MCP_SANDBOX": "true",
            "MCP_READ_ONLY": "true",
            "MCP_ALLOWED_PATHS": "/tmp/mcp-sandbox",
            "MCP_NETWORK_DISABLED": "true"
        })

        # Wrap command in sandbox
        if sandboxed.command == "npx":
            sandboxed.args = [
                "--no-install",  # Prevent new installations
                "--ignore-scripts",  # Ignore package scripts
                *sandboxed.args
            ]

        return sandboxed
```

## Summary

These advanced patterns enable:

1. **Production-ready deployments** with proper lifecycle management
2. **Sophisticated discovery** with custom analyzers
3. **Enterprise approvals** with multi-stage workflows
4. **High performance** through caching and pooling
5. **Complex orchestration** with multi-agent patterns
6. **Full observability** with metrics and logging
7. **Security controls** with allowlisting and sandboxing

Choose the patterns that match your requirements and adapt them to your specific use case.
