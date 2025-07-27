# haive-mcp API Reference

Complete API documentation for the haive-mcp package.

## Table of Contents

- [Agents](#agents)
  - [IntelligentMCPAgent](#intelligentmcpagent)
  - [MCPAgent](#mcpagent)
  - [TransferableMCPAgent](#transferablemcpagent)
- [Manager](#manager)
  - [MCPManager](#mcpmanager)
- [Configuration](#configuration)
  - [MCPConfig](#mcpconfig)
  - [MCPServerConfig](#mcpserverconfig)
- [Models](#models)
  - [HITLApprovalRequest](#hitlapprovalrequest)
  - [ServerRecommendation](#serverrecommendation)
  - [MCPRegistrationResult](#mcpregistrationresult)
- [Tools](#tools)
- [Enums](#enums)

## Agents

### IntelligentMCPAgent

Dynamic MCP agent with auto-discovery and HITL approval capabilities.

```python
from haive.mcp.agents import IntelligentMCPAgent
```

#### Constructor

```python
IntelligentMCPAgent(
    engine: AugLLMConfig,
    name: str = "intelligent_mcp_agent",
    auto_discover: bool = True,
    require_approval: bool = True,
    approval_timeout: float = 30.0,
    approval_callback: Optional[Callable[[HITLApprovalRequest], bool]] = None,
    **kwargs
)
```

**Parameters:**

- `engine` (AugLLMConfig): LLM engine configuration
- `name` (str): Agent name
- `auto_discover` (bool): Enable automatic server discovery based on user needs
- `require_approval` (bool): Require HITL approval for installations
- `approval_timeout` (float): Timeout for approval requests in seconds
- `approval_callback` (Optional[Callable]): Custom approval callback function
- `**kwargs`: Additional ReactAgent parameters

#### Methods

##### `async setup() -> None`

Initialize the agent and documentation components.

##### `async arun(inputs: dict[str, Any]) -> Any`

Run the agent with automatic discovery if enabled.

**Parameters:**

- `inputs` (dict): Agent inputs with messages

**Returns:**

- Agent response after processing

##### `get_recommendation_history() -> list[ServerRecommendation]`

Get history of server recommendations made.

##### `get_pending_approvals() -> list[HITLApprovalRequest]`

Get list of pending approval requests.

##### `async approve_request(request_id: str) -> bool`

Approve a pending request.

##### `async reject_request(request_id: str) -> bool`

Reject a pending request.

#### Built-in Tools

The agent includes these tools:

- `discover_mcp_servers(capability: str) -> str` - Find servers by capability
- `install_mcp_server(server_name: str, require_approval: bool = True) -> str` - Install server
- `list_mcp_status() -> str` - Get current status
- `reload_mcp_server(server_name: str) -> str` - Reload server

#### Example

```python
agent = IntelligentMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True,
    require_approval=True,
    approval_callback=my_approval_handler
)

await agent.setup()
result = await agent.arun({
    "messages": [{"role": "user", "content": "Search the web"}]
})
```

### MCPAgent

Standard MCP agent for production use with static configurations.

```python
from haive.mcp.agents import MCPAgent
```

#### Constructor

```python
MCPAgent(
    engine: AugLLMConfig,
    mcp_config: Optional[MCPConfig] = None,
    name: str = "mcp_agent",
    **kwargs
)
```

**Parameters:**

- `engine` (AugLLMConfig): LLM engine configuration
- `mcp_config` (Optional[MCPConfig]): MCP configuration with servers
- `name` (str): Agent name
- `**kwargs`: Additional SimpleAgent parameters

#### Methods

##### `async setup() -> None`

Initialize MCP connections and discover tools.

##### `get_available_capabilities() -> list[str]`

Get all available capabilities from connected servers.

##### `async discover_tools_by_capability(capability: str) -> list[Any]`

Find tools that provide a specific capability.

##### `async call_tool_with_retry(tool_name: str, arguments: dict, max_retries: int = 3) -> Any`

Call a tool with automatic retry logic.

#### Class Methods

##### `create_with_mcp_servers(engine, server_configs, name=None, **kwargs) -> MCPAgent`

Factory method to create agent with server configurations.

**Parameters:**

- `engine` (AugLLMConfig): LLM engine
- `server_configs` (dict[str, dict]): Server configurations
- `name` (Optional[str]): Agent name
- `**kwargs`: Additional parameters

**Example:**

```python
agent = MCPAgent.create_with_mcp_servers(
    engine=engine,
    server_configs={
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"]
        }
    }
)
```

### TransferableMCPAgent

MCP agent that can transfer tools to other agents.

```python
from haive.mcp.agents import TransferableMCPAgent
```

#### Constructor

Same as MCPAgent.

#### Additional Methods

##### `async transfer_tools_to_agent(target_agent: Agent, tool_names: list[str]) -> bool`

Transfer specific tools to another agent.

##### `async transfer_all_tools_to_agent(target_agent: Agent) -> bool`

Transfer all tools to another agent.

##### `async receive_tools_from_agent(source_agent: Agent, tools: list[Any]) -> bool`

Receive tools from another agent.

#### Example

```python
agent1 = TransferableMCPAgent(engine=engine, mcp_config=config1)
agent2 = TransferableMCPAgent(engine=engine, mcp_config=config2)

await agent1.setup()
await agent2.setup()

# Transfer specific tools
await agent1.transfer_tools_to_agent(agent2, ["file_read", "file_write"])
```

## Manager

### MCPManager

Dynamic MCP server lifecycle manager with hot-reload support.

```python
from haive.mcp.manager import MCPManager
```

#### Constructor

```python
MCPManager(
    enabled: bool = True,
    auto_health_check: bool = True,
    health_check_interval: float = 30.0,
    max_retry_attempts: int = 3,
    connection_timeout: float = 10.0
)
```

**Parameters:**

- `enabled` (bool): Whether MCP management is enabled
- `auto_health_check` (bool): Enable automatic health monitoring
- `health_check_interval` (float): Interval between health checks in seconds
- `max_retry_attempts` (int): Maximum retry attempts for failed connections
- `connection_timeout` (float): Timeout for server connections in seconds

#### Methods

##### `async add_server(server_name: str, config: MCPServerConfig, connect_immediately: bool = True) -> MCPRegistrationResult`

Add a new MCP server dynamically.

**Parameters:**

- `server_name` (str): Unique name for the server
- `config` (MCPServerConfig): Server configuration
- `connect_immediately` (bool): Whether to connect immediately

**Returns:**

- MCPRegistrationResult with success status and details

##### `async remove_server(server_name: str) -> bool`

Remove an MCP server.

##### `async get_all_tools(refresh: bool = False) -> list[Any]`

Get all tools from connected servers.

**Parameters:**

- `refresh` (bool): Whether to refresh the tool list

##### `async refresh_tools() -> None`

Refresh the tool list from all connected servers.

##### `async get_resources(server_name: Optional[str] = None) -> list[Any]`

Get available resources from MCP servers.

##### `async get_prompts(server_name: Optional[str] = None) -> list[Any]`

Get available prompts from MCP servers.

##### `async reload_server(server_name: str) -> MCPRegistrationResult`

Reload a specific MCP server.

##### `async call_tool(tool_name: str, arguments: dict[str, Any]) -> Any`

Call a tool from any connected server.

##### `get_server_status(server_name: str) -> Optional[MCPServerStatus]`

Get the status of a specific server.

##### `get_all_server_status() -> dict[str, dict[str, Any]]`

Get status information for all servers.

##### `async retry_failed_servers() -> list[MCPRegistrationResult]`

Retry connection to all failed servers.

##### `async shutdown() -> None`

Shutdown the manager and close all connections.

#### Example

```python
manager = MCPManager(auto_health_check=True)

# Add server
result = await manager.add_server("filesystem", MCPServerConfig(
    name="filesystem",
    transport="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem"]
))

# Get tools with refresh
tools = await manager.get_all_tools(refresh=True)

# Check status
status = manager.get_all_server_status()
print(f"Connected servers: {status['summary']['connected_servers']}")
```

## Configuration

### MCPConfig

Main configuration for MCP integration.

```python
from haive.mcp.config import MCPConfig
```

#### Fields

- `enabled` (bool): Whether MCP is enabled
- `servers` (dict[str, MCPServerConfig]): Server configurations
- `auto_discover` (bool): Enable automatic server discovery
- `lazy_init` (bool): Delay initialization until first use
- `retry_attempts` (int): Connection retry attempts
- `timeout` (int): Connection timeout in seconds

#### Example

```python
config = MCPConfig(
    enabled=True,
    servers={
        "postgres": postgres_server_config,
        "github": github_server_config
    },
    auto_discover=False,
    retry_attempts=3,
    timeout=30
)
```

### MCPServerConfig

Configuration for individual MCP servers.

```python
from haive.mcp.config import MCPServerConfig
```

#### Fields

- `name` (str): Server name
- `transport` (TransportType): Transport type ("stdio" or "sse")
- `command` (Optional[str]): Command for stdio transport
- `args` (Optional[list[str]]): Command arguments
- `url` (Optional[str]): URL for SSE transport
- `env` (Optional[dict[str, str]]): Environment variables
- `capabilities` (list[str]): Server capabilities
- `category` (str): Server category
- `description` (str): Server description

#### Example

```python
config = MCPServerConfig(
    name="postgres",
    transport="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-postgres"],
    env={"DATABASE_URL": "postgresql://localhost/mydb"},
    capabilities=["database", "sql"],
    category="database",
    description="PostgreSQL database access"
)
```

## Models

### HITLApprovalRequest

Request for human-in-the-loop approval.

```python
from haive.mcp.agents.intelligent_mcp_agent import HITLApprovalRequest
```

#### Fields

- `request_id` (str): Unique request ID
- `timestamp` (datetime): Request timestamp
- `request_type` (str): Type of approval needed
- `recommendation` (ServerRecommendation): Server recommendation
- `context` (dict[str, Any]): Additional context
- `status` (ApprovalStatus): Current status
- `response_deadline` (Optional[datetime]): Deadline for response

### ServerRecommendation

Recommendation for MCP server installation.

```python
from haive.mcp.agents.intelligent_mcp_agent import ServerRecommendation
```

#### Fields

- `server_name` (str): Full server name
- `reason` (str): Why this server is recommended
- `capabilities` (list[str]): Capabilities provided
- `confidence` (float): Confidence score 0-1
- `config` (MCPServerConfig): Proposed configuration
- `alternative_servers` (list[str]): Alternative options

### MCPRegistrationResult

Result of MCP server registration.

```python
from haive.mcp.manager import MCPRegistrationResult
```

#### Fields

- `server_name` (str): Name of the server
- `success` (bool): Whether registration succeeded
- `status` (MCPServerStatus): Current server status
- `tools_count` (int): Number of tools discovered
- `tools` (list[str]): List of tool names
- `error_message` (Optional[str]): Error message if failed
- `connection_time` (Optional[float]): Connection time in seconds

### MCPHealthStatus

Health status information for an MCP server.

```python
from haive.mcp.manager import MCPHealthStatus
```

#### Fields

- `server_name` (str): Name of the server
- `status` (MCPServerStatus): Current status
- `last_check` (datetime): Last health check time
- `response_time` (Optional[float]): Response time in seconds
- `consecutive_failures` (int): Number of consecutive failures
- `total_requests` (int): Total requests made
- `successful_requests` (int): Successful requests
- `error_details` (Optional[str]): Latest error details

## Tools

### Built-in Discovery Tools

These tools are automatically included in IntelligentMCPAgent:

#### discover_mcp_servers

```python
@tool
async def discover_mcp_servers(capability: str) -> str:
    """Discover MCP servers that provide a specific capability."""
```

**Parameters:**

- `capability` (str): The capability needed (e.g., 'database', 'web_search')

**Returns:**

- JSON string with discovered servers and recommendations

#### install_mcp_server

```python
@tool
async def install_mcp_server(server_name: str, require_approval: bool = True) -> str:
    """Install and configure an MCP server."""
```

**Parameters:**

- `server_name` (str): Full name of the server to install
- `require_approval` (bool): Whether to require HITL approval

**Returns:**

- JSON string with installation result

#### list_mcp_status

```python
@tool
async def list_mcp_status() -> str:
    """Get status of all MCP servers and available tools."""
```

**Returns:**

- JSON string with current MCP status

#### reload_mcp_server

```python
@tool
async def reload_mcp_server(server_name: str) -> str:
    """Reload a specific MCP server to refresh its capabilities."""
```

**Parameters:**

- `server_name` (str): Name of the server to reload

**Returns:**

- JSON string with reload result

## Enums

### MCPServerStatus

Status of an MCP server.

```python
from haive.mcp.manager import MCPServerStatus
```

**Values:**

- `PENDING` - Not yet attempted to connect
- `CONNECTING` - Connection in progress
- `CONNECTED` - Successfully connected and operational
- `FAILED` - Connection failed with error
- `DISCONNECTED` - Intentionally disconnected by user
- `UNHEALTHY` - Connected but health check failed

### ApprovalStatus

Status of HITL approval request.

```python
from haive.mcp.agents.intelligent_mcp_agent import ApprovalStatus
```

**Values:**

- `PENDING` - Awaiting approval
- `APPROVED` - Approved by user
- `REJECTED` - Rejected by user
- `TIMEOUT` - Approval timeout exceeded

### TransportType

MCP transport types.

```python
from haive.mcp.config import TransportType
```

**Values:**

- `stdio` - Standard I/O transport (for local processes)
- `sse` - Server-Sent Events transport (for HTTP endpoints)

## Error Handling

All async methods may raise these exceptions:

- `ValueError` - Invalid configuration or parameters
- `ConnectionError` - Failed to connect to MCP server
- `TimeoutError` - Connection or operation timeout
- `RuntimeError` - General runtime errors

Example error handling:

```python
try:
    result = await manager.add_server("test", config)
    if not result.success:
        print(f"Failed to add server: {result.error_message}")
except Exception as e:
    logger.error(f"Error adding server: {e}")
```

## Best Practices

1. **Always call setup()** on agents before use
2. **Use async/await** for all operations
3. **Handle approval callbacks** properly in production
4. **Monitor server health** with status checks
5. **Use environment variables** for sensitive configuration
6. **Implement proper error handling** for all operations
7. **Clean shutdown** with manager.shutdown()

## Migration Guide

### From Static to Dynamic

```python
# Old static approach
agent = MCPAgent(
    engine=engine,
    mcp_config=static_config
)

# New dynamic approach
agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True
)
```

### Adding Hot-Reload

```python
# Old: Restart required
# Stop agent, update config, restart

# New: Hot-reload
await manager.add_server("new_server", config)
tools = await manager.get_all_tools(refresh=True)
# Use immediately!
```
