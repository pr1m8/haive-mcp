# MCP Server Installation Guide

## Prerequisites

- Python 3.8+
- Node.js and npm (for npm-based servers)
- Docker (for containerized servers)
- Git (for repository-based servers)

## Installation Methods

### Using Poetry (Recommended)

```bash
# Install the haive-mcp package with all dependencies
poetry install --all-extras

# Install development dependencies  
poetry install --with dev
```

### Manual Installation

```bash
# Install core dependencies
pip install pydantic langchain-mcp-adapters

# Install optional dependencies
pip install fastmcp mcp
```

## MCP Server Installation

### Official npm Servers

```bash
# Install filesystem server
npx -y @modelcontextprotocol/server-filesystem

# Install GitHub server
npx -y @modelcontextprotocol/server-github
```

### Using the Download Manager

```bash
# Download and install servers
python scripts/download_servers.py download --all

# Install specific servers
python scripts/download_servers.py download --servers filesystem github

# Install by category
python scripts/download_servers.py download --category official
```

## Configuration

Create a configuration file at `~/.mcp/config.yaml`:

```yaml
servers:
  filesystem:
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem"]
    
  github:
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
```

## Verification

```bash
# Test server connection
python scripts/manage_servers.py test filesystem

# Check all server health
python scripts/manage_servers.py health --all
```

## Troubleshooting

### npm Command Not Found

Install Node.js from [nodejs.org](https://nodejs.org/) or using your package manager:

```bash
# Ubuntu/Debian
sudo apt install nodejs npm

# macOS with Homebrew
brew install node

# Verify installation
npm --version
```

### Permission Errors

If you encounter permission errors with global npm installs:

```bash
# Configure npm to use a different directory
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Connection Timeouts

Increase timeout in configuration:

```yaml
servers:
  slow-server:
    transport: stdio
    command: ...
    timeout: 60  # seconds
    retry_attempts: 3
```