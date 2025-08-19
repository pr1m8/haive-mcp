# MCP Server Manager Guide

## Overview

The MCP Server Manager provides a robust way to start and manage Model Context Protocol (MCP) servers. These servers enable AI agents to interact with various tools and services through a standardized protocol.

## Quick Start

### Command Line Usage

```bash
# List available servers
poetry run python src/haive/mcp/servers/mcp_server_manager.py --list

# Start default servers (filesystem and time)
poetry run python src/haive/mcp/servers/mcp_server_manager.py

# Start specific servers
poetry run python src/haive/mcp/servers/mcp_server_manager.py --servers filesystem memory

# Enable debug logging
poetry run python src/haive/mcp/servers/mcp_server_manager.py --debug
```

### Python API Usage

```python
from haive.mcp.servers import MCPServerManager

# Create manager
manager = MCPServerManager()

# Start servers (blocking mode - runs until Ctrl+C)
manager.run(servers_to_start=["filesystem", "time"])

# Non-blocking mode for integration
manager.run(servers_to_start=["filesystem"], blocking=False)
# ... do other work ...
manager.stop_all_servers()  # Clean shutdown

# Start server with environment variables
manager.start_server("github", env_overrides={"GITHUB_TOKEN": "your-token"})

# Check status
status = manager.get_status()
for name, info in status.items():
    print(f"{name}: {'running' if info['running'] else 'stopped'}")
```

## Available Servers

### Built-in Servers (No API Key Required)

1. **filesystem** - File system operations
   - Read, write, and manage files
   - Secure access limited to current directory

2. **time** - Date and time utilities
   - Get current time, format dates
   - Time zone conversions

3. **memory** - Persistent memory storage
   - Store and retrieve data across sessions
   - Key-value storage

### API-Key Servers

4. **github** - GitHub repository access
   - Requires: `GITHUB_TOKEN` environment variable
   - Access repos, issues, PRs, etc.

5. **brave-search** - Web search via Brave
   - Requires: `BRAVE_API_KEY` environment variable
   - Search the web programmatically

## Understanding Stdio Transport

MCP servers typically use "stdio" transport, which means:
- They communicate via standard input/output
- Status messages appear on stderr (this is normal, not an error)
- The manager handles this correctly - don't be alarmed by stderr output

## Integration with Haive Agents

### Basic Integration

```python
from haive.mcp.servers import MCPServerManager
from haive.mcp.agents import MCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

# Start MCP servers
manager = MCPServerManager()
manager.run(servers_to_start=["filesystem", "time"], blocking=False)

# Create MCP-enabled agent
agent = MCPAgent(
    engine=AugLLMConfig(),
    mcp_servers=["filesystem", "time"]
)

# Agent can now use filesystem and time tools
result = await agent.arun("What time is it? Save it to current_time.txt")

# Cleanup
manager.stop_all_servers()
```

### Advanced Integration with Auto-Discovery

```python
from haive.mcp.agents import IntelligentMCPAgent

# Agent automatically discovers and starts needed servers
agent = IntelligentMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True,
    server_manager=manager  # Optional: provide existing manager
)

# Agent analyzes task and starts appropriate servers
result = await agent.arun("Search for Python tutorials and save results")
# Agent will auto-start web search and filesystem servers
```

## Troubleshooting

### Common Issues

1. **"npx command not found"**
   - Install Node.js and npm: `curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs`

2. **Server fails to start**
   - Check if required environment variables are set
   - Enable debug logging: `--debug`
   - Check if port is already in use (for HTTP servers)

3. **"EOF when reading a line"**
   - This happens with interactive input in non-TTY environments
   - Use the MCPServerManager which handles this correctly

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.getLogger("MCPServerManager").setLevel(logging.DEBUG)

# Or from command line
poetry run python src/haive/mcp/servers/mcp_server_manager.py --debug
```

## Best Practices

1. **Always clean up**: Call `stop_all_servers()` when done
2. **Use environment variables**: Don't hardcode API keys
3. **Monitor server health**: Check `get_status()` periodically
4. **Handle failures gracefully**: Servers may fail to start
5. **Use appropriate servers**: Only start servers you need

## Example: Complete Workflow

```python
#!/usr/bin/env python3
"""Example of using MCP Server Manager in a complete workflow."""

import asyncio
import os
from haive.mcp.servers import MCPServerManager
from haive.mcp.agents import MCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

async def main():
    # Initialize manager
    manager = MCPServerManager()
    
    try:
        # Start servers
        manager.run(servers_to_start=["filesystem", "time"], blocking=False)
        
        # Create agent
        agent = MCPAgent(
            engine=AugLLMConfig(),
            mcp_servers=["filesystem", "time"]
        )
        
        # Use the agent
        result = await agent.arun("What files are in the current directory?")
        print(f"Agent response: {result}")
        
        # Check server status
        status = manager.get_status()
        manager.show_status()
        
    finally:
        # Always cleanup
        manager.stop_all_servers()

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

- Explore the 1900+ available MCP servers from the community
- Create custom MCP servers for your specific needs
- Integrate with the Haive agent framework for powerful AI capabilities
- Use the CLI tool for interactive server discovery and configuration