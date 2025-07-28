# 🚀 Integrated MCP Discovery & Management System

A complete end-to-end solution for discovering, installing, and managing Model Context Protocol (MCP) servers. This system seamlessly combines our enhanced discovery capabilities with FastMCP-style server management.

## 🌟 Key Features

### 1. **Unified Discovery & Installation**

- 🔍 Natural language search with Self-Query RAG
- 📦 One-click installation from search results
- 🔧 Automatic FastMCP configuration
- ✅ Instant server availability

### 2. **FastMCP-Compatible Management**

- 💻 CLI commands similar to `claude mcp add`
- 🎮 Process lifecycle management
- 📊 Real-time monitoring
- 🔄 Auto-restart capabilities

### 3. **Comprehensive Web Interface**

- 🌐 Single interface for all operations
- 📈 Analytics and usage statistics
- 🔴 Live server status monitoring
- 📋 Installation history tracking

## 🚀 Quick Start

### Prerequisites

```bash
# Install required dependencies
pip install streamlit plotly pandas aiohttp psutil

# Ensure you have the MCP data
# The system expects: packages/haive-mcp/data/mcp_servers/ALL_MCP_SERVERS_COMPLETE.json
```

### Launch the System

```bash
# Recommended: Launch the integrated web interface
poetry run python packages/haive-mcp/src/haive/mcp/integrated_launcher.py web

# Or use the launcher directly
cd packages/haive-mcp/src/haive/mcp
python integrated_launcher.py web
```

## 📋 System Components

### 1. **Integrated Launcher** (`integrated_launcher.py`)

Central entry point for all system features:

```bash
# Launch web interface
python integrated_launcher.py web

# Check system status
python integrated_launcher.py status

# Server management
python integrated_launcher.py server start weather
python integrated_launcher.py server stop weather
python integrated_launcher.py server status

# Interactive installation
python integrated_launcher.py install
```

### 2. **Integrated MCP System** (`integrated_mcp_system.py`)

Core system combining discovery and management:

- Enhanced search with multiple retrieval methods
- Automated installation pipeline
- FastMCP configuration management
- Streamlit web interface

### 3. **FastMCP Runner** (`fastmcp_runner.py`)

Process management for MCP servers:

- Start/stop/restart servers
- Monitor server health
- Auto-restart failed servers
- Resource usage tracking

## 🔍 Discovery Features

### Natural Language Search

```
Examples:
- "Python database servers with more than 10 stars"
- "JavaScript web servers with tools"
- "How to install PostgreSQL MCP servers"
- "TypeScript servers with resources and prompts"
```

### Search Methods

1. **Self-Query**: Structured queries with metadata filtering
2. **Parent Docs**: Full documentation retrieval
3. **Similarity**: Semantic similarity search
4. **Auto**: Intelligent method selection

## 📦 Installation Workflow

### From Discovery to Running Server

1. **Search**: Find servers using natural language
2. **Review**: See detailed information, stars, features
3. **Install**: One-click installation with progress tracking
4. **Configure**: Automatic FastMCP registration
5. **Start**: Launch server immediately
6. **Monitor**: Track status and resource usage

### Supported Installation Methods

- **NPM/NPX**: JavaScript/TypeScript servers
- **Pip**: Python servers
- **Git Clone**: Direct repository cloning
- **Cargo**: Rust servers
- **Go**: Go servers

## 🎮 Server Management

### CLI Commands (FastMCP Compatible)

```bash
# Add a server (manual)
# Servers are automatically added during installation

# Start a server
python fastmcp_runner.py start weather

# Stop a server
python fastmcp_runner.py stop weather

# Restart a server
python fastmcp_runner.py restart weather

# Check status
python fastmcp_runner.py status

# List all servers
python fastmcp_runner.py list

# Monitor all servers
python fastmcp_runner.py monitor
```

### Configuration Storage

Servers are stored in `~/.fastmcp/servers.json`:

```json
{
  "servers": {
    "weather": {
      "name": "weather",
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "weather_mcp"],
      "env": {},
      "active": true,
      "metadata": {
        "installed_via": "pip",
        "category": "utility",
        "language": "python"
      }
    }
  }
}
```

## 🌐 Web Interface Features

### Tabs Overview

1. **🔍 Discover**
   - Search MCP servers
   - View detailed information
   - One-click installation
   - Multiple search methods

2. **📦 Installed**
   - View all installed servers
   - Server configuration details
   - Start/stop controls
   - Remove servers

3. **🎮 Running**
   - Live server status
   - Process monitoring
   - Stop running servers
   - Resource usage

4. **📊 Analytics**
   - Installation statistics
   - Category breakdowns
   - Installation history
   - Usage metrics

## 🔧 Advanced Features

### Auto-Restart Configuration

Enable auto-restart for critical servers:

```json
{
  "servers": {
    "critical-server": {
      "auto_restart": true
      // ... other config
    }
  }
}
```

### Environment Variables

Configure server environment:

```json
{
  "servers": {
    "api-server": {
      "env": {
        "API_KEY": "your-key",
        "DEBUG": "true"
      }
    }
  }
}
```

### Transport Types

- **stdio**: Standard input/output (default)
- **sse**: Server-Sent Events
- **http**: HTTP transport

## 📊 System Architecture

```
┌─────────────────────────────────────────────┐
│          Integrated Web Interface           │
│         (Streamlit + Discovery)             │
└─────────────┬──────────────────────────────┘
              │
┌─────────────┴──────────────────────────────┐
│         Integrated MCP System               │
│  ┌──────────────┐  ┌──────────────────┐   │
│  │  Discovery   │  │   Installation    │   │
│  │   Agent      │  │    Pipeline       │   │
│  └──────────────┘  └──────────────────┘   │
└─────────────┬──────────────────────────────┘
              │
┌─────────────┴──────────────────────────────┐
│          FastMCP Runner                     │
│  ┌──────────────┐  ┌──────────────────┐   │
│  │   Process    │  │    Server         │   │
│  │  Management  │  │  Configuration    │   │
│  └──────────────┘  └──────────────────┘   │
└────────────────────────────────────────────┘
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**

   ```bash
   # Always use poetry run
   poetry run python integrated_launcher.py web
   ```

2. **Server Won't Start**
   - Check the command in `~/.fastmcp/servers.json`
   - Verify the server is properly installed
   - Check logs for error messages

3. **Installation Fails**
   - Ensure you have the required package manager (npm, pip, etc.)
   - Check internet connectivity
   - Try manual installation first

4. **Search Returns No Results**
   - Vector store will be created on first search
   - Ensure MCP data file exists
   - Try different search queries

### Debug Mode

View detailed logs:

```bash
# Set logging level
export LOG_LEVEL=DEBUG
python integrated_launcher.py web
```

## 🔮 Future Enhancements

### Planned Features

- [ ] Server health checks and endpoints
- [ ] Automatic dependency resolution
- [ ] Server marketplace integration
- [ ] Cloud deployment support
- [ ] Multi-user management
- [ ] API access to all features
- [ ] Docker containerization
- [ ] Kubernetes operators

### Community Features

- [ ] Server ratings and reviews
- [ ] Usage statistics sharing
- [ ] Community server repository
- [ ] Server templates and presets

## 📞 Support & Contributing

### Getting Help

1. Check this README first
2. View system status: `python integrated_launcher.py status`
3. Check logs in the web interface
4. Verify dependencies are installed

### Contributing

- Add new installation methods
- Improve search algorithms
- Add server templates
- Enhance monitoring capabilities

## 🎯 Example Workflows

### Workflow 1: Find and Install a Database Server

1. Launch web interface
2. Search: "Python PostgreSQL server with high stars"
3. Review results, check features
4. Click "Install" on preferred server
5. Wait for installation
6. Start server from "Installed" tab
7. Monitor in "Running" tab

### Workflow 2: Manage Multiple Servers

1. Install several servers via discovery
2. Use CLI for batch operations:
   ```bash
   python fastmcp_runner.py monitor
   ```
3. Enable auto-restart for critical servers
4. Monitor resource usage in web interface

### Workflow 3: Development Setup

1. Search for development tools (linters, formatters)
2. Install required servers
3. Configure with environment variables
4. Start all servers
5. Use integrated monitoring

---

**🚀 Ready to revolutionize your MCP server management? Start with:**

```bash
poetry run python packages/haive-mcp/src/haive/mcp/integrated_launcher.py web
```

This integrated system transforms MCP server discovery into immediate usability!
