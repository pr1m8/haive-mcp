# Tutorial 2: Setting Up Your First MCP Server

## Prerequisites

Before starting, ensure you have:

- Python 3.8+ installed
- Node.js and npm (for npm-based servers)
- Basic command line knowledge

## Step 1: Understanding Server Types

MCP servers come in different types based on installation method:

### NPM Servers (Most Common)

```bash
# Official servers
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-github

# Community servers
npm install -g mcp-server-weather
npm install -g mcp-server-search
```

### Python/Pip Servers

```bash
# Python-based servers
pip install mcp-server-python
pip install fastmcp
```

### Git Repository Servers

```bash
# Clone and install
git clone https://github.com/username/custom-mcp-server
cd custom-mcp-server
pip install -r requirements.txt
```

### Docker Servers

```bash
# Pull and run
docker pull mcp/server-name
docker run -it mcp/server-name
```

## Step 2: Installing the Filesystem Server

Let's start with the official filesystem server as our first example.

### Manual Installation

```bash
# Install globally via npm
npm install -g @modelcontextprotocol/server-filesystem

# Verify installation
npx @modelcontextprotocol/server-filesystem --help
```

### Using the Downloader

```bash
# Using our download script
python scripts/download_servers.py download --servers filesystem
```

## Step 3: Understanding Server Configuration

Each server needs configuration to work properly:

```yaml
# Basic configuration structure
servers:
  filesystem:
    # Transport method (how client talks to server)
    transport: stdio

    # Command to start the server
    command: npx
    args: ["@modelcontextprotocol/server-filesystem"]

    # Environment variables (if needed)
    env:
      ALLOWED_PATHS: "/home/user/documents"

    # Server capabilities
    capabilities: ["tools", "resources"]
```

## Step 4: Testing Your Server

### Manual Test

```bash
# Start the server manually
npx @modelcontextprotocol/server-filesystem

# You should see:
# Server listening on stdio transport...
```

### Programmatic Test

```python
import asyncio
from haive.mcp.downloader import GeneralMCPDownloader

async def test_server():
    downloader = GeneralMCPDownloader()

    # Download and install
    result = await downloader.download_servers(["filesystem"])

    if result["successful"] > 0:
        print("✓ Server installed successfully!")
        print(f"Configuration saved to: {result['config_file']}")
    else:
        print("✗ Installation failed")
        print(result["failed_servers"])

# Run the test
asyncio.run(test_server())
```

## Step 5: Connecting to Your Server

### Using Haive MCP Agent

```python
from haive.mcp.agents import MCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

# Create agent with MCP
agent = MCPAgent.create_with_mcp_servers(
    engine=AugLLMConfig(),
    server_configs={
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["@modelcontextprotocol/server-filesystem"]
        }
    }
)

# Initialize connection
await agent.setup()

# Use the server
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "List all files in the current directory"
    }]
})
```

## Step 6: Understanding Server Responses

When connected, the server provides:

### 1. Tool Definitions

```json
{
  "tools": [
    {
      "name": "read_file",
      "description": "Read the contents of a file",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Path to the file"
          }
        },
        "required": ["path"]
      }
    }
  ]
}
```

### 2. Tool Execution

```json
// Request
{
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "/home/user/test.txt"
    }
  }
}

// Response
{
  "content": [
    {
      "type": "text",
      "text": "Hello, World!"
    }
  ]
}
```

## Step 7: Common Issues and Solutions

### Issue 1: Command Not Found

```bash
# Error: npx: command not found
# Solution: Install Node.js and npm
sudo apt install nodejs npm  # Ubuntu/Debian
brew install node            # macOS
```

### Issue 2: Permission Denied

```bash
# Error: EACCES: permission denied
# Solution: Configure npm to use a different directory
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Issue 3: Connection Timeout

```yaml
# Solution: Increase timeout in config
servers:
  filesystem:
    transport: stdio
    command: npx
    args: ["@modelcontextprotocol/server-filesystem"]
    timeout: 60 # Increase from default 30
```

## Step 8: Exploring Server Capabilities

The filesystem server provides various tools:

1. **File Operations**
   - `read_file`: Read file contents
   - `write_file`: Write to files
   - `list_directory`: List directory contents

2. **Directory Operations**
   - `create_directory`: Make new directories
   - `remove_directory`: Delete directories
   - `move_file`: Move/rename files

3. **Metadata Operations**
   - `get_file_info`: Get file statistics
   - `check_exists`: Check if path exists

## Practice Exercises

1. **Install Multiple Servers**

   ```bash
   python scripts/download_servers.py download --servers filesystem github sqlite
   ```

2. **Test Each Server**

   ```bash
   python scripts/manage_servers.py test filesystem
   python scripts/manage_servers.py test github
   python scripts/manage_servers.py test sqlite
   ```

3. **View Server Logs**

   ```bash
   python scripts/manage_servers.py logs filesystem -n 50
   ```

4. **Check Health Status**
   ```bash
   python scripts/manage_servers.py health --all
   ```

## Summary

You've learned how to:

- ✓ Understand different MCP server types
- ✓ Install your first MCP server
- ✓ Configure server settings
- ✓ Test server connectivity
- ✓ Connect servers to AI agents
- ✓ Troubleshoot common issues

## Next Steps

- Continue to Tutorial 3: Working with Multiple Servers
- Explore the server registry for more options
- Try creating your own MCP server

## Additional Resources

- [Filesystem Server Docs](https://github.com/modelcontextprotocol/servers/tree/main/filesystem)
- [MCP Client Libraries](https://modelcontextprotocol.io/libraries)
- [Troubleshooting Guide](../docs/troubleshooting.md)
