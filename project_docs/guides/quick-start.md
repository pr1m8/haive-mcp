# Quick Start Guide

**Get up and running with dynamic MCP integration in 5 minutes**

## 🚀 5-Minute Setup

### Prerequisites

- Python 3.12+
- Node.js 18+ (for MCP servers)
- OpenAI API key (or other LLM provider)

### Step 1: Install

```bash
# Install Haive MCP package
pip install haive-mcp

# Install Node.js MCP servers
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-calculator
```

### Step 2: Environment Setup

```bash
# Create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### Step 3: Your First Dynamic Agent

Create `quick_start.py`:

```python
"""Quick start example - Dynamic MCP agent in 5 minutes."""

import asyncio
from haive.mcp.agents import IntelligentMCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

async def main():
    # Create intelligent agent with auto-discovery
    agent = IntelligentMCPAgent(
        name="quick_start_agent",
        engine=AugLLMConfig(),
        auto_discover=True,
        require_approval=False  # Auto-approve for demo
    )

    # Setup agent
    await agent.setup()
    print("🤖 Agent ready! Asking about files...")

    # Agent automatically discovers filesystem tools
    result1 = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "List the files in the current directory"
        }]
    })
    print(f"📁 Files: {result1}")

    # Agent automatically discovers calculator tools
    result2 = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Calculate 15 * 23 + 47"
        }]
    })
    print(f"🧮 Calculation: {result2}")

    # Cleanup
    await agent.cleanup()
    print("✅ Done!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Run It!

```bash
python quick_start.py
```

**Output**:

```
🤖 Agent ready! Asking about files...
📁 Files: I found 3 files: quick_start.py, .env, README.md
🧮 Calculation: The result is 392
✅ Done!
```

**🎉 Congratulations!** Your agent just automatically discovered and used filesystem and calculator tools without any manual configuration.

## 🎯 What Just Happened?

1. **Agent Analyzed Requests**: Used AI to understand what capabilities were needed
2. **Discovered Tools**: Found appropriate MCP servers from the database
3. **Installed Automatically**: Added filesystem and calculator servers on-demand
4. **Executed Tasks**: Used the new tools to complete user requests
5. **Maintained Context**: All happened in a single conversation flow

## 🔧 Customization Options

### Add Human Approval

```python
async def approval_callback(request):
    print(f"Install {request.recommendation.server_name}? (y/n)")
    return input() == 'y'

agent = IntelligentMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True,
    require_approval=True,
    approval_callback=approval_callback
)
```

### Use Static Configuration

```python
from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig

config = MCPConfig(
    servers={
        "filesystem": MCPServerConfig(
            name="filesystem",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
        )
    }
)

agent = MCPAgent(engine=AugLLMConfig(), mcp_config=config)
```

### Add More Capabilities

```bash
# Install more MCP servers
npm install -g @modelcontextprotocol/server-brave-search
npm install -g @modelcontextprotocol/server-postgres

# Set API keys
export BRAVE_API_KEY=your-brave-key
export DATABASE_URL=postgresql://localhost/mydb
```

## 🌟 Try More Examples

### Web Search + File Operations

```python
async def web_search_example():
    agent = IntelligentMCPAgent(
        engine=AugLLMConfig(),
        auto_discover=True,
        require_approval=False
    )

    await agent.setup()

    # Agent will auto-discover web search and filesystem tools
    result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Search for Python async programming tutorials and save the top 3 results to a file"
        }]
    })

    print(f"Result: {result}")
    await agent.cleanup()
```

### Database Analysis

```python
async def database_example():
    agent = IntelligentMCPAgent(
        engine=AugLLMConfig(),
        auto_discover=True,
        require_approval=False
    )

    await agent.setup()

    # Agent will auto-discover database tools
    result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Connect to the sales database and show me the top 10 customers by revenue"
        }]
    })

    print(f"Database analysis: {result}")
    await agent.cleanup()
```

## 🎨 Interactive Demo

Want to see it in action? Try this interactive demo:

```python
"""Interactive demo - chat with your agent."""

import asyncio
from haive.mcp.agents import IntelligentMCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

async def interactive_demo():
    agent = IntelligentMCPAgent(
        name="demo_agent",
        engine=AugLLMConfig(temperature=0.7),
        auto_discover=True,
        require_approval=True  # You'll approve tool installations
    )

    await agent.setup()
    print("🤖 Hi! I'm your dynamic MCP agent. I can discover and use tools as needed.")
    print("💡 Try asking me to:")
    print("   - Work with files: 'List my files'")
    print("   - Do calculations: 'What's 123 * 456?'")
    print("   - Search the web: 'Find Python tutorials'")
    print("   - Analyze data: 'Process the sales.csv file'")
    print("   - Or anything else!")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            break

        try:
            result = await agent.arun({
                "messages": [{"role": "user", "content": user_input}]
            })
            print(f"Agent: {result}\n")

        except Exception as e:
            print(f"Error: {e}\n")

    await agent.cleanup()
    print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(interactive_demo())
```

## 🚨 Troubleshooting

### Common Issues

**1. Import Errors**

```bash
# Make sure haive-mcp is installed
pip install haive-mcp

# Check Python version
python --version  # Should be 3.12+
```

**2. MCP Server Not Found**

```bash
# Install MCP servers globally
npm install -g @modelcontextprotocol/server-filesystem

# Check Node.js version
node --version  # Should be 18+
```

**3. API Key Issues**

```bash
# Set environment variable
export OPENAI_API_KEY=your-key

# Or create .env file
echo "OPENAI_API_KEY=your-key" > .env
```

**4. Permission Errors**

```bash
# Fix npm permissions (Linux/Mac)
sudo npm install -g @modelcontextprotocol/server-filesystem

# Or use npx (slower but no permissions needed)
# Agent will use npx automatically if global install fails
```

### Debug Mode

Enable debug logging to see what's happening:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your agent code here
```

## 🔗 Next Steps

Now that you have a working dynamic agent:

1. **[Integration Guide](../integration/README.md)** - Add MCP to existing agents
2. **[Usage Patterns](usage-patterns.md)** - Common scenarios and patterns
3. **[Examples](../examples/README.md)** - More complex working examples
4. **[Architecture](../architecture/README.md)** - Understand how it works
5. **[Implementation](../implementation/README.md)** - Production deployment

## 💡 Pro Tips

- **Start simple**: Use auto-discovery without approval for experimentation
- **Add approval later**: Enable `require_approval=True` for production
- **Check available servers**: Browse the [MCP Server Database](https://github.com/modelcontextprotocol/servers)
- **Monitor usage**: Use debug logging to understand what tools are being discovered
- **Share tools**: Use `TransferableMCPAgent` for multi-agent scenarios

---

**🎉 Welcome to the world of dynamic AI agents!** Your agents can now adapt to any task by automatically discovering and using the right tools.
