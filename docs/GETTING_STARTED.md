# Getting Started with haive-mcp

This guide will walk you through setting up and using haive-mcp for dynamic MCP server management in your Haive agents.

## Table of Contents

1. [Installation](#installation)
2. [Understanding MCP](#understanding-mcp)
3. [Your First Dynamic Agent](#your-first-dynamic-agent)
4. [Key Features Explained](#key-features-explained)
5. [Common Use Cases](#common-use-cases)
6. [Best Practices](#best-practices)

## Installation

### Prerequisites

- Python 3.12+
- Poetry (for dependency management)
- Node.js (for MCP servers that use npm)

### Install haive-mcp

```bash
# If you're in the haive project
cd packages/haive-mcp
poetry install

# Or add to your project
poetry add haive-mcp
```

### Verify Installation

```python
# Test that imports work
from haive.mcp.agents import IntelligentMCPAgent
from haive.mcp.manager import MCPManager
print("✅ haive-mcp installed successfully!")
```

## Understanding MCP

Model Context Protocol (MCP) enables AI models to access external tools and data sources. Think of it as a standardized way to give your agents superpowers:

- **Tools**: Functions the agent can call (e.g., search web, query database)
- **Resources**: Data sources the agent can read (e.g., files, APIs)
- **Prompts**: Pre-defined templates for common tasks

### MCP Servers

MCP servers are programs that provide tools/resources/prompts. Examples:

- `filesystem` - Read/write files
- `postgres` - Database operations
- `github` - Repository management
- `brave-search` - Web searching

## Your First Dynamic Agent

Let's create an agent that automatically installs what it needs:

```python
import asyncio
from haive.mcp.agents import IntelligentMCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

async def main():
    # Create an intelligent agent
    agent = IntelligentMCPAgent(
        engine=AugLLMConfig(),       # Your LLM configuration
        auto_discover=True,          # Auto-find needed servers
        require_approval=True        # Ask before installing
    )

    # Initialize the agent
    await agent.setup()

    # Ask it to do something that needs tools
    result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Search for Python decorators tutorial and save it to decorators.md"
        }]
    })

    print(result)

    # What happened behind the scenes:
    # 1. Agent analyzed your request
    # 2. Detected need for: web search + file writing
    # 3. Found brave-search and filesystem servers
    # 4. Asked for approval to install
    # 5. Installed servers and got tools
    # 6. Completed your task!

asyncio.run(main())
```

## Key Features Explained

### 1. Auto-Discovery

The agent analyzes what you're asking and figures out what tools it needs:

```python
# Agent detects different needs automatically
await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Query the user table in PostgreSQL"
    }]
})
# Detects: Need database access → Installs postgres server

await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Check the latest issues in my GitHub repo"
    }]
})
# Detects: Need GitHub access → Installs github server
```

### 2. HITL Approval

Control what gets installed with custom approval logic:

```python
async def my_approval(request):
    """Custom approval logic"""
    print(f"\n🔔 APPROVAL REQUEST")
    print(f"Server: {request.recommendation.server_name}")
    print(f"Reason: {request.recommendation.reason}")

    # You could:
    # - Check against allowlist
    # - Log to audit system
    # - Send to Slack for approval
    # - Auto-approve trusted servers

    if "postgres" in request.recommendation.server_name:
        print("⚠️  Database access requested!")
        return False  # Deny database servers

    return True  # Approve others

agent = IntelligentMCPAgent(
    engine=engine,
    approval_callback=my_approval
)
```

### 3. Hot-Reload

Add servers and refresh tools without restarting:

```python
# Access the manager
manager = agent.mcp_manager

# Add a new server while running
await manager.add_server("calculator", MCPServerConfig(
    name="calculator",
    transport="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-calculator"]
))

# Refresh tools - no restart needed!
tools = await manager.get_all_tools(refresh=True)
print(f"Now have {len(tools)} tools available")

# Use the new tools immediately
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Calculate 15% tip on $47.82"
    }]
})
```

### 4. Manual Discovery

Take control of the discovery process:

```python
# Create agent without auto-discovery
agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=False  # Manual mode
)

# Discover servers yourself
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Use discover_mcp_servers tool to find all database servers"
    }]
})

# Review the options, then install specific one
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Install the modelcontextprotocol/server-sqlite server"
    }]
})
```

## Common Use Cases

### 1. Research Assistant

```python
# Agent that can search and save research
research_agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True
)

await research_agent.arun({
    "messages": [{
        "role": "user",
        "content": """
        Research the latest developments in quantum computing.
        Search multiple sources and create a summary report.
        Save it as quantum_computing_2024.md
        """
    }]
})
# Auto-installs: brave-search, filesystem
```

### 2. Data Analyst

```python
# Agent that works with databases
analyst_agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True
)

await analyst_agent.arun({
    "messages": [{
        "role": "user",
        "content": """
        Connect to PostgreSQL and analyze the sales data.
        Create visualizations and export to Excel.
        """
    }]
})
# Auto-installs: postgres, excel, matplotlib servers
```

### 3. DevOps Assistant

```python
# Agent for development tasks
devops_agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True
)

await devops_agent.arun({
    "messages": [{
        "role": "user",
        "content": """
        Check my GitHub repos for open PRs.
        Run tests on the latest changes.
        Update the deployment status.
        """
    }]
})
# Auto-installs: github, docker, kubernetes servers
```

### 4. Multi-Agent Collaboration

```python
# Multiple agents sharing tools
from haive.mcp.agents import TransferableMCPAgent

# Research agent finds information
researcher = TransferableMCPAgent(engine=engine, mcp_config=research_config)
await researcher.setup()

# Writer agent creates content
writer = TransferableMCPAgent(engine=engine, mcp_config=writer_config)
await writer.setup()

# Share research tools with writer
await researcher.transfer_tools_to_agent(
    writer,
    tool_names=["web_search", "arxiv_search"]
)

# Now writer can also search!
```

## Best Practices

### 1. Start with Auto-Discovery

Let the agent figure out what it needs first:

```python
# Good for exploration and prototyping
agent = IntelligentMCPAgent(
    engine=engine,
    auto_discover=True,
    require_approval=True  # Stay in control
)
```

### 2. Move to Static Config for Production

Once you know what servers you need:

```python
from haive.mcp.config import MCPConfig, MCPServerConfig

# Production configuration
production_config = MCPConfig(
    servers={
        "postgres": MCPServerConfig(...),
        "redis": MCPServerConfig(...),
        "github": MCPServerConfig(...)
    }
)

# Faster startup, predictable behavior
agent = MCPAgent(
    engine=engine,
    mcp_config=production_config
)
```

### 3. Implement Proper Approval Logic

```python
# Production approval system
async def production_approval(request):
    # Check allowlist
    allowed_servers = ["filesystem", "postgres", "github"]
    server_name = request.recommendation.server_name

    if any(allowed in server_name for allowed in allowed_servers):
        # Log approval
        logger.info(f"Auto-approved: {server_name}")
        return True

    # Send to human for review
    await send_slack_message(
        f"MCP Server approval needed: {server_name}\n"
        f"Reason: {request.recommendation.reason}"
    )

    # Wait for human response (simplified)
    return await wait_for_human_approval(request.request_id)
```

### 4. Monitor Server Health

```python
# Regular health checks
async def monitor_servers(agent):
    while True:
        status = agent.mcp_manager.get_all_server_status()

        # Check for failures
        if status['summary']['failed_servers'] > 0:
            logger.warning(f"Failed servers: {status['summary']['failed_servers']}")

            # Try to recover
            for server_name, info in status['servers'].items():
                if info['status'] == 'failed':
                    await agent.mcp_manager.reload_server(server_name)

        await asyncio.sleep(60)  # Check every minute
```

### 5. Use Environment Variables

```python
# Don't hardcode sensitive data
import os

github_config = MCPServerConfig(
    name="github",
    transport="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"],
    env={
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
        "GITHUB_OWNER": os.getenv("GITHUB_OWNER", "default-org")
    }
)
```

## Next Steps

1. **Explore Available Servers**: Check the [MCP Server Directory](https://github.com/modelcontextprotocol/servers)
2. **Build Custom Servers**: Create your own MCP servers for proprietary tools
3. **Advanced Patterns**: See [ADVANCED_USAGE.md](ADVANCED_USAGE.md)
4. **Contributing**: Help us expand the server database!

## Troubleshooting

### Agent won't install servers?

- Check `require_approval` setting
- Verify npm/npx is installed
- Look at logs for connection errors

### Tools not showing up?

- Use `refresh=True` when getting tools
- Check server status with `list_mcp_status` tool
- Verify server installed successfully

### Performance issues?

- Disable auto-discovery for production
- Use static configurations
- Limit health check frequency

## Summary

haive-mcp makes it easy to give your agents access to external tools and data:

1. **Start simple** with auto-discovery
2. **Stay in control** with HITL approval
3. **Scale up** with static configs
4. **Keep running** with hot-reload

The key is that your agents can now adapt to any task by finding and installing the right tools automatically!
