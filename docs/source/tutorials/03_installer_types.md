# Tutorial 3: Automatic Installation Behind the Scenes

## Overview

While MCPAgent handles all installation automatically, understanding how different MCP servers are installed helps you troubleshoot issues and optimize performance. Haive MCP supports **all major installation methods** transparently.

## Automatic Installation in Action

```python
import asyncio
from haive.mcp.agents import MCPAgent
from haive.core.engine.aug_llm import AugLLMConfig

async def see_automatic_installation():
    """Watch automatic installation across different package types."""
    
    agent = MCPAgent(
        name="installer_demo",
        engine=AugLLMConfig(),
        mcp_categories=["core"],  # Contains NPM, Git, and Python servers
        auto_install=True
    )
    
    print("🔄 Starting automatic installation...")
    await agent.initialize_mcp()
    
    # Check what was installed and how
    manager = agent.mcp_manager
    status = await manager.get_all_server_status()
    
    print("\n📦 Installation Results:")
    for server_name, server_status in status.items():
        print(f"  {server_name}: {server_status}")
        
        # Show installation method used
        if server_name in manager.registry.servers:
            server_info = manager.registry.servers[server_name]
            print(f"    Method: {server_info.installation_method}")
            print(f"    Package: {server_info.package_name}")
    
    print(f"\n✅ Total servers installed: {len(status)}")

# See installation in action
asyncio.run(see_automatic_installation())
```

Expected Output:
```
🔄 Starting automatic installation...

📦 Installation Results:
  filesystem: healthy
    Method: npm
    Package: @modelcontextprotocol/server-filesystem
  postgres: healthy  
    Method: npm
    Package: @modelcontextprotocol/server-postgres
  github: healthy
    Method: npm
    Package: @modelcontextprotocol/server-github
  brave_search: healthy
    Method: npm
    Package: @modelcontextprotocol/server-brave-search

✅ Total servers installed: 4
```

## How Different Installation Types Work

The agent automatically determines the best installation method for each server:

## NPM Installer (Most Common)

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

### How Haive Handles NPM Installation

Behind the scenes, when you create an MCPAgent, here's what happens with NPM servers:

```python
# This is what the agent does automatically
async def behind_the_scenes_npm():
    """Show how NPM installation works automatically."""
    
    # When you specify mcp_categories=["core"], the agent:
    # 1. Looks up servers in the "core" category
    # 2. Finds NPM packages like @modelcontextprotocol/server-filesystem
    # 3. Installs them using npx (no global installation needed)
    # 4. Connects via STDIO transport
    # 5. Discovers available tools
    
    agent = MCPAgent(
        name="npm_demo",
        engine=AugLLMConfig(),
        mcp_categories=["core"],  # Contains many NPM servers
        auto_install=True
    )
    
    await agent.initialize_mcp()
    
    # Check what NPM servers were installed
    tools = agent.list_mcp_tools()
    filesystem_tools = [t for t in tools if 'file' in t['name'].lower()]
    
    print("📁 Filesystem tools from NPM server:")
    for tool in filesystem_tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Test NPM server functionality
    result = await agent.arun("List all Python files in the current directory")
    print(f"\n📝 NPM server result: {result}")

asyncio.run(behind_the_scenes_npm())
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

| Feature              | NPM        | Pip         | Git    | Docker   |
| -------------------- | ---------- | ----------- | ------ | -------- |
| **Language**         | JavaScript | Python      | Any    | Any      |
| **Dependencies**     | Automatic  | Automatic   | Manual | Included |
| **Isolation**        | No         | Virtual env | No     | Full     |
| **Version Control**  | Yes        | Yes         | Yes    | Yes      |
| **Binary Support**   | Limited    | Limited     | Yes    | Yes      |
| **Setup Complexity** | Low        | Low         | Medium | Medium   |
| **Resource Usage**   | Low        | Low         | Low    | High     |

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

## Troubleshooting Installation Issues

When automatic installation fails, you can debug specific installer types:

```python
async def debug_installation_issues():
    """Debug installation problems by installer type."""
    
    agent = MCPAgent(
        name="debug_installer",
        engine=AugLLMConfig(),
        mcp_categories=["core"],
        auto_install=True
    )
    
    try:
        await agent.initialize_mcp()
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        
        # Check system requirements
        import subprocess
        
        # Check NPM
        try:
            subprocess.run(["npx", "--version"], check=True, capture_output=True)
            print("✅ NPM available")
        except:
            print("❌ NPM not available - install Node.js")
            
        # Check Python
        try:
            subprocess.run(["pip", "--version"], check=True, capture_output=True)
            print("✅ Python pip available")
        except:
            print("❌ Python pip not available")
            
        # Check Git
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            print("✅ Git available")
        except:
            print("❌ Git not available")

asyncio.run(debug_installation_issues())
```

## Summary

**With MCPAgent, you don't need to worry about installer types!** The agent:

- ✅ **Automatically detects** the best installation method for each server
- ✅ **Handles all package managers** (NPM, Pip, Git, Docker) transparently  
- ✅ **Manages dependencies** and environment setup
- ✅ **Provides debugging tools** when issues occur
- ✅ **Works with 1900+ servers** across all installation types

### Key Takeaways

1. **Zero Manual Setup**: No need to know package managers or installation commands
2. **Universal Support**: Works with NPM, Pip, Git, and Docker automatically
3. **Error Recovery**: Built-in debugging and retry mechanisms
4. **Performance Optimized**: Uses npx for NPM (no global installs needed)

## Next Steps

- **Advanced Patterns**: Multi-agent workflows with different tool categories
- **Custom Categories**: Create your own server categories
- **Performance Tuning**: Optimize installation and connection performance
- **Production Deployment**: Scale MCP integration to production systems
