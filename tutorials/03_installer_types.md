# Tutorial 3: Understanding Different Installer Types

## Overview

MCP servers can be distributed and installed through various package managers and methods. Each installer type has its own advantages and use cases.

## NPM Installer

### What is NPM?

NPM (Node Package Manager) is the package manager for JavaScript and Node.js. Many MCP servers are distributed as npm packages.

### How NPM Installation Works

```bash
# Global installation (available system-wide)
npm install -g @modelcontextprotocol/server-filesystem

# Local installation (project-specific)
npm install @modelcontextprotocol/server-filesystem

# Using npx (no installation needed)
npx @modelcontextprotocol/server-filesystem
```

### NPM Server Structure

```
npm-package/
├── package.json          # Package metadata
├── index.js             # Entry point
├── lib/                 # Source code
│   ├── server.js
│   └── tools.js
└── bin/                 # Executable scripts
    └── mcp-server
```

### Testing NPM Installer

```python
# Test script for NPM installer
from src.haive.mcp.downloader.installers import NPMInstaller
from src.haive.mcp.downloader.config import ServerConfig, ServerTemplate

async def test_npm():
    installer = NPMInstaller()
    
    config = ServerConfig(
        name="test-npm",
        template="npm",
        source="npm",
        variables={"package": "@modelcontextprotocol/server-filesystem"}
    )
    
    template = ServerTemplate(
        name="npm",
        installation_method="npm",
        command_pattern="{package}"
    )
    
    # Install
    result = await installer.install(config, template, Path("./test"))
    print(f"Success: {result['success']}")
    print(f"Command: {result.get('command')}")
```

### Common NPM Issues

1. **Permission Errors**
   ```bash
   # Fix: Use npm prefix
   npm config set prefix ~/.npm-global
   export PATH=~/.npm-global/bin:$PATH
   ```

2. **Version Conflicts**
   ```bash
   # Fix: Use specific version
   npm install package@1.2.3
   ```

3. **Dependency Issues**
   ```bash
   # Fix: Clear cache and reinstall
   npm cache clean --force
   npm install
   ```

## Pip Installer

### What is Pip?

Pip is the package installer for Python. Python-based MCP servers are distributed through PyPI (Python Package Index).

### How Pip Installation Works

```bash
# Basic installation
pip install mcp-server-name

# Specific version
pip install mcp-server-name==1.0.0

# From git repository
pip install git+https://github.com/user/mcp-server.git

# Development mode
pip install -e ./local-mcp-server
```

### Python MCP Server Structure

```
python-package/
├── setup.py             # Package configuration
├── pyproject.toml       # Modern Python packaging
├── src/
│   └── mcp_server/
│       ├── __init__.py
│       ├── server.py    # Main server code
│       └── tools.py     # Tool implementations
└── requirements.txt     # Dependencies
```

### Testing Pip Installer

```python
# Test script for Pip installer
from src.haive.mcp.downloader.installers import PipInstaller

async def test_pip():
    installer = PipInstaller()
    
    config = ServerConfig(
        name="test-pip",
        template="pip",
        source="pypi",
        variables={"package": "requests"}  # Test with known package
    )
    
    template = ServerTemplate(
        name="pip",
        installation_method="pip",
        command_pattern="{package}"
    )
    
    # Install
    result = await installer.install(config, template, Path("./test"))
    print(f"Success: {result['success']}")
    
    # Verify
    verified = await installer.verify(config, template, Path("./test"))
    print(f"Verified: {verified}")
```

### Common Pip Issues

1. **Import Errors**
   ```bash
   # Fix: Install in virtual environment
   python -m venv venv
   source venv/bin/activate
   pip install package
   ```

2. **Dependency Conflicts**
   ```bash
   # Fix: Use pip-tools
   pip install pip-tools
   pip-compile requirements.in
   pip-sync requirements.txt
   ```

## Git Installer

### What is Git Installation?

Some MCP servers are distributed as Git repositories that need to be cloned and set up manually.

### How Git Installation Works

```bash
# Clone repository
git clone https://github.com/username/mcp-server.git

# Install dependencies
cd mcp-server
pip install -r requirements.txt
# or
npm install

# Run setup
python setup.py install
```

### Git Repository Structure

```
git-repo/
├── .git/                # Git metadata
├── README.md           # Documentation
├── src/                # Source code
├── requirements.txt    # Python dependencies
├── package.json        # Node dependencies
└── scripts/            # Setup scripts
    └── install.sh
```

### Testing Git Installer

```python
# Test script for Git installer
from src.haive.mcp.downloader.installers import GitInstaller

async def test_git():
    installer = GitInstaller()
    
    config = ServerConfig(
        name="test-git",
        template="git",
        source="https://github.com/octocat/Hello-World.git",
        variables={"owner": "octocat", "repo": "Hello-World"}
    )
    
    template = ServerTemplate(
        name="git",
        installation_method="git",
        command_pattern="echo 'Installed {repo}'",
        post_install=[]  # No post-install for test
    )
    
    # Install
    result = await installer.install(config, template, Path("./test"))
    print(f"Success: {result['success']}")
    print(f"Clone dir: {result.get('clone_dir')}")
```

### Common Git Issues

1. **Authentication**
   ```bash
   # Fix: Use SSH or token
   git clone git@github.com:user/repo.git
   # or
   git clone https://token@github.com/user/repo.git
   ```

2. **Large Repositories**
   ```bash
   # Fix: Shallow clone
   git clone --depth 1 https://github.com/user/repo.git
   ```

## Docker Installer

### What is Docker Installation?

Docker allows MCP servers to run in isolated containers with all dependencies included.

### How Docker Installation Works

```bash
# Pull image
docker pull mcp/server-name:latest

# Run container
docker run -it --rm mcp/server-name

# With volume mounting
docker run -it --rm -v $(pwd):/workspace mcp/server-name
```

### Docker Image Structure

```
Dockerfile
├── FROM base-image
├── RUN install-dependencies
├── COPY server-code /app
├── WORKDIR /app
├── EXPOSE port
└── CMD ["start-server"]
```

### Testing Docker Installer

```python
# Test script for Docker installer
from src.haive.mcp.downloader.installers import DockerInstaller

async def test_docker():
    installer = DockerInstaller()
    
    config = ServerConfig(
        name="test-docker",
        template="docker",
        source="docker",
        variables={"image": "alpine:latest"}  # Small test image
    )
    
    template = ServerTemplate(
        name="docker",
        installation_method="docker",
        command_pattern="{image}"
    )
    
    # Install (pull image)
    result = await installer.install(config, template, Path("./test"))
    print(f"Success: {result['success']}")
    print(f"Image: {result.get('image')}")
```

### Common Docker Issues

1. **Permission Denied**
   ```bash
   # Fix: Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. **Storage Space**
   ```bash
   # Fix: Clean up unused images
   docker system prune -a
   ```

## Comparison Table

| Feature | NPM | Pip | Git | Docker |
|---------|-----|-----|-----|--------|
| **Language** | JavaScript | Python | Any | Any |
| **Dependencies** | Automatic | Automatic | Manual | Included |
| **Isolation** | No | Virtual env | No | Full |
| **Version Control** | Yes | Yes | Yes | Yes |
| **Binary Support** | Limited | Limited | Yes | Yes |
| **Setup Complexity** | Low | Low | Medium | Medium |
| **Resource Usage** | Low | Low | Low | High |

## Choosing the Right Installer

### Use NPM when:
- Server is written in JavaScript/TypeScript
- You want automatic dependency management
- You need wide distribution

### Use Pip when:
- Server is written in Python
- You want PyPI distribution
- You need Python ecosystem integration

### Use Git when:
- Server is in development
- You need latest changes
- You want to contribute

### Use Docker when:
- You need complete isolation
- Server has complex dependencies
- You want consistent environments

## Complete Test Suite

Run all installer tests:

```bash
# Run comprehensive test
python tests/integration/test_each_installer_type.py

# Run specific installer test
pytest tests/integration/test_each_installer_type.py::test_npm_installer_real -v
```

## Summary

Each installer type serves different needs:
- **NPM**: Best for JavaScript-based servers
- **Pip**: Ideal for Python servers
- **Git**: Perfect for development and customization
- **Docker**: Excellent for isolation and complex setups

## Next Steps

- Tutorial 4: Creating Your Own MCP Server
- Tutorial 5: Advanced Configuration
- Explore installer plugins in the codebase