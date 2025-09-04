# Tutorial 2: Your First MCP-Enhanced Agent

## Prerequisites

Before starting, ensure you have:

- Python 3.8+ installed
- Node.js and npm (for automatic server installation)
- Haive framework installed

With Haive MCP, **servers are installed automatically** - no manual setup required!

## Step 1: Create Your First MCP-Enhanced Agent

Skip all the manual server installation! With Haive MCP, agents automatically discover and install the tools they need:

```python
import asyncio
from haive.mcp.agents.enhanced_mcp_agent import EnhancedMCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

async def create_first_agent():
    """Create an agent that automatically gets filesystem tools."""
    
    # Create agent with automatic tool discovery
    agent = EnhancedMCPAgent(
        name="file_assistant",
        engine=AugLLMConfig(
            temperature=0.7,
            model="gpt-4"
        ),
        mcp_categories=["core"],  # Auto-install filesystem, database, search tools
        auto_install=True
    )
    
    # Initialize - this automatically installs needed servers
    print("🔄 Initializing MCP servers...")
    await agent.initialize_mcp()
    
    # Check what tools were discovered
    stats = agent.get_mcp_stats()
    print(f"✅ Ready! Connected to {stats.servers_connected} servers")
    print(f"📚 Discovered {stats.tools_registered} tools")
    
    # List some tools
    tools = agent.list_mcp_tools()
    print(f"\n🔧 Available tools:")
    for tool in tools[:5]:  # Show first 5
        print(f"  - {tool['name']}: {tool['description'][:60]}...")
    
    return agent

# Run the setup
agent = asyncio.run(create_first_agent())
```

Expected output:
```
🔄 Initializing MCP servers...
✅ Ready! Connected to 4 servers
📚 Discovered 12 tools

🔧 Available tools:
  - read_file: Read the contents of a file
  - write_file: Write content to a file
  - list_directory: List the contents of a directory
  - create_directory: Create a new directory
  - search_files: Search for files matching a pattern
```

## Step 2: Using Your Agent with File Operations

Now let's use the agent to perform file operations:

```python
async def use_file_agent():
    """Use the agent for file operations."""
    
    # Use the agent we created (agent variable from Step 1)
    # Or create a new one:
    agent = EnhancedMCPAgent(
        name="file_worker",
        engine=AugLLMConfig(temperature=0.7),
        mcp_categories=["core"],
        auto_install=True
    )
    await agent.initialize_mcp()
    
    # Task 1: List current directory
    print("\n📂 Listing current directory...")
    result1 = await agent.arun("Please list all files in the current directory")
    print(f"Result: {result1}")
    
    # Task 2: Create a test file
    print("\n📝 Creating a test file...")
    result2 = await agent.arun(
        "Create a file called 'hello.txt' with the content 'Hello from MCP!'"
    )
    print(f"Result: {result2}")
    
    # Task 3: Read the file back
    print("\n📖 Reading the file...")
    result3 = await agent.arun("Read the contents of 'hello.txt'")
    print(f"Result: {result3}")
    
    # Health check
    health = await agent.health_check_mcp()
    print(f"\n💚 MCP Health: {health}")

# Run file operations
asyncio.run(use_file_agent())
```

Expected output:
```
📂 Listing current directory...
Result: I can see the following files in the current directory:
- hello.txt
- pyproject.toml
- README.md
- src/

📝 Creating a test file...
Result: I've successfully created the file 'hello.txt' with the content 'Hello from MCP!'

📖 Reading the file...
Result: The contents of 'hello.txt' are: Hello from MCP!

💚 MCP Health: {'filesystem': 'healthy', 'postgres': 'healthy'}
```

## Step 3: Exploring Different Server Categories

MCP servers are organized into categories for easy discovery:

```python
async def explore_categories():
    """Explore different MCP server categories."""
    
    # Create agents with different tool sets
    
    # 1. Core tools (filesystem, database, web search)
    core_agent = EnhancedMCPAgent(
        name="core_agent",
        engine=AugLLMConfig(),
        mcp_categories=["core"],
        auto_install=True
    )
    
    # 2. Enhanced filesystem tools
    fs_agent = EnhancedMCPAgent(
        name="filesystem_agent", 
        engine=AugLLMConfig(),
        mcp_categories=["enhanced_filesystem"],
        auto_install=True
    )
    
    # 3. Multiple categories
    multi_agent = EnhancedMCPAgent(
        name="multi_agent",
        engine=AugLLMConfig(), 
        mcp_categories=["core", "ai_enhanced", "time_utilities"],
        auto_install=True
    )
    
    # Initialize all agents
    await core_agent.initialize_mcp()
    await fs_agent.initialize_mcp()
    await multi_agent.initialize_mcp()
    
    # Compare capabilities
    print("🔧 Core agent tools:", len(core_agent.list_mcp_tools()))
    print("📁 Filesystem agent tools:", len(fs_agent.list_mcp_tools())) 
    print("🎯 Multi-category agent tools:", len(multi_agent.list_mcp_tools()))
    
    # Use multi-agent for complex task
    result = await multi_agent.arun(
        "Get current time, list files, and search for Python projects online"
    )
    print(f"\n🎯 Multi-tool result: {result}")

# Explore different capabilities
asyncio.run(explore_categories())
```

## Step 4: Debugging and Monitoring

Monitor your MCP integration with built-in debugging tools:

```python
async def debug_mcp_agent():
    """Debug and monitor MCP agent performance."""
    
    agent = EnhancedMCPAgent(
        name="debug_agent",
        engine=AugLLMConfig(),
        mcp_categories=["core"],
        auto_install=True
    )
    
    await agent.initialize_mcp()
    
    # 1. Check server status
    print("🔍 Server Status:")
    status = await agent.mcp_manager.get_all_server_status()
    for server_name, server_status in status.items():
        print(f"  {server_name}: {server_status}")
    
    # 2. Health check all servers
    print("\n💚 Health Check:")
    health = await agent.health_check_mcp()
    print(f"  Overall health: {health}")
    
    # 3. Get detailed statistics
    print("\n📊 Statistics:")
    stats = agent.get_mcp_stats()
    print(f"  Servers connected: {stats.servers_connected}")
    print(f"  Tools registered: {stats.tools_registered}")
    print(f"  Categories active: {stats.categories_active}")
    
    # 4. List all tools with details
    print("\n🔧 All Available Tools:")
    tools = agent.list_mcp_tools()
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description'][:80]}...")
    
    # 5. Test a simple operation
    print("\n🧪 Test Operation:")
    try:
        result = await agent.arun("List the current directory")
        print(f"  ✅ Success: Operation completed")
    except Exception as e:
        print(f"  ❌ Error: {e}")

# Run debugging
asyncio.run(debug_mcp_agent())
```

## Step 5: Common Issues and Solutions

### Issue 1: No Servers Connected

```python
# Check if npm is available
import subprocess
try:
    subprocess.run(["npx", "--version"], check=True, capture_output=True)
    print("✅ npx is available")
except:
    print("❌ npx not found - install Node.js")
    # Solution: Install Node.js from https://nodejs.org/
```

### Issue 2: Slow Initialization

```python
# Increase timeout for slow networks
agent = EnhancedMCPAgent(
    name="patient_agent",
    engine=AugLLMConfig(),
    mcp_categories=["core"],
    auto_install=True,
    initialization_timeout=120  # 2 minutes instead of default
)
```

### Issue 3: Tool Not Working

```python
# Debug specific tool issues
async def debug_tool_issue():
    agent = EnhancedMCPAgent(name="debug", engine=AugLLMConfig(), 
                           mcp_categories=["core"], auto_install=True)
    await agent.initialize_mcp()
    
    # Check if tool exists
    tools = agent.list_mcp_tools()
    tool_names = [t['name'] for t in tools]
    print(f"Available tools: {tool_names}")
    
    # Test specific server health
    health = await agent.mcp_manager.bulk_health_check()
    for result in health:
        if not result.is_healthy:
            print(f"Unhealthy server: {result.server_name} - {result.error}")

asyncio.run(debug_tool_issue())
```

## Practice Exercises

1. **Create a File Manager Agent**

   ```python
   async def file_manager():
       agent = EnhancedMCPAgent(name="fm", engine=AugLLMConfig(), 
                              mcp_categories=["enhanced_filesystem"], auto_install=True)
       await agent.initialize_mcp()
       
       # Organize files by extension
       await agent.arun("List all files and organize them by file extension")
   ```

2. **Multi-Tool Workflow Agent**

   ```python
   async def workflow_agent():
       agent = EnhancedMCPAgent(name="workflow", engine=AugLLMConfig(),
                              mcp_categories=["core", "ai_enhanced"], auto_install=True)
       await agent.initialize_mcp()
       
       # Complex workflow
       await agent.arun("Search for Python files, analyze their imports, and create a dependency report")
   ```

3. **Health Monitoring**

   ```python
   async def monitor_health():
       agent = EnhancedMCPAgent(name="monitor", engine=AugLLMConfig(),
                              mcp_categories=["core"], auto_install=True)
       await agent.initialize_mcp()
       
       # Regular health checks
       import time
       for i in range(3):
           health = await agent.health_check_mcp()
           print(f"Health check {i+1}: {health}")
           time.sleep(10)
   ```

## Summary

You've learned how to:

- ✅ **Create MCP-enhanced agents** with automatic tool discovery
- ✅ **Use dynamic tool integration** without manual server setup
- ✅ **Monitor and debug** MCP connections and performance
- ✅ **Handle common issues** with built-in diagnostics
- ✅ **Explore different categories** of MCP servers and tools
- ✅ **Build complex workflows** using multiple tool categories

## Key Takeaways

1. **No Manual Setup**: Agents automatically discover and install needed tools
2. **1900+ Servers Available**: Massive ecosystem of tools and capabilities
3. **Real-time Integration**: Tools are ready immediately after initialization
4. **Built-in Monitoring**: Health checks and debugging tools included
5. **Category-based Discovery**: Organize tools by functionality for easy use

## Next Steps

- **Tutorial 3**: Advanced MCP patterns and multi-agent workflows
- **Explore Categories**: Try different `mcp_categories` combinations
- **Build Custom Workflows**: Combine multiple tool categories for complex tasks
- **Monitor Performance**: Use health checks and statistics for production

## Available Categories

- `"core"`: Filesystem, database, web search, GitHub tools
- `"ai_enhanced"`: Advanced AI tools and sequential thinking
- `"enhanced_filesystem"`: Extended file operations and management
- `"time_utilities"`: Date, time, and scheduling tools
- `"crypto_finance"`: Cryptocurrency and financial tools
- `"browser_automation"`: Web browser control and testing
- `"github_enhanced"`: Advanced GitHub code analysis
- `"notifications"`: Alert and notification systems

## Additional Resources

- [EnhancedMCPAgent API Reference](../docs/source/agents.rst)
- [MCP Categories Guide](../guides/platform-architecture.rst)
- [Real-world Examples](../guides/real-world-examples.rst)
