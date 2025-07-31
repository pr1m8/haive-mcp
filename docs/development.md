# Development Guide

## Setting Up Development Environment

### Prerequisites

- Python 3.8+
- Poetry for dependency management
- Node.js and npm (for testing npm-based servers)
- Docker (optional, for testing Docker-based servers)
- Git

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd haive/packages/haive-mcp

# Install dependencies with Poetry
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install

# Run tests to verify setup
poetry run pytest
```

## Project Structure

```
haive-mcp/
├── src/haive/mcp/          # Source code
│   ├── downloader/         # General downloader system
│   │   ├── __init__.py
│   │   ├── config.py       # Configuration models
│   │   ├── core.py         # GeneralMCPDownloader
│   │   ├── installers.py   # Installer plugins
│   │   ├── discovery.py    # Server discovery
│   │   └── integration.py  # Agent integration
│   ├── agents/             # MCP-enabled agents
│   ├── mixins/             # MCP mixins
│   └── config.py           # MCP configuration
├── scripts/                # CLI scripts
│   ├── download_servers.py # Download manager
│   └── manage_servers.py   # Server manager
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test fixtures
├── docs/                  # Documentation
├── configs/               # Configuration templates
└── examples/              # Usage examples
```

## Coding Standards

### Python Style Guide

Follow PEP 8 with these additions:

- Line length: 88 characters (Black default)
- Use type hints for all functions
- Google-style docstrings
- Prefer f-strings for formatting

### Docstring Format

```python
def process_server(server_config: ServerConfig, 
                  timeout: int = 30) -> Dict[str, Any]:
    """Process and install an MCP server.
    
    Downloads and configures an MCP server based on the provided
    configuration. Handles retries and error recovery.
    
    Args:
        server_config: Server configuration object
        timeout: Connection timeout in seconds (default: 30)
        
    Returns:
        Dictionary containing:
            - success: Whether installation succeeded
            - command: Command to run the server
            - error: Error message if failed
            
    Raises:
        ValueError: If server_config is invalid
        TimeoutError: If installation times out
        
    Example:
        >>> config = ServerConfig(name="test", template="npm")
        >>> result = process_server(config)
        >>> print(result["success"])
        True
    """
```

### Type Hints

Always use type hints:

```python
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

def find_servers(
    pattern: str,
    sources: List[str],
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Find servers matching pattern."""
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=haive.mcp --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_installers.py

# Run with verbose output
poetry run pytest -v

# Run only unit tests
poetry run pytest tests/unit/

# Run only integration tests
poetry run pytest tests/integration/
```

### Writing Tests

#### Unit Tests

```python
# tests/unit/test_installers.py
import pytest
from haive.mcp.downloader.installers import NPMInstaller
from haive.mcp.downloader.config import ServerConfig, ServerTemplate

class TestNPMInstaller:
    @pytest.fixture
    def installer(self):
        return NPMInstaller()
        
    @pytest.fixture
    def server_config(self):
        return ServerConfig(
            name="test-server",
            template="npm_test",
            source="npm",
            variables={"package": "@test/package"}
        )
        
    async def test_can_handle_npm_template(self, installer, server_config):
        template = ServerTemplate(
            name="npm_test",
            installation_method="npm",
            command_pattern="npx {package}"
        )
        
        result = await installer.can_handle(server_config, template)
        assert result is True
        
    async def test_install_success(self, installer, server_config, tmp_path):
        # Test implementation
        pass
```

#### Integration Tests

```python
# tests/integration/test_downloader.py
import pytest
from haive.mcp.downloader import GeneralMCPDownloader

@pytest.mark.integration
class TestGeneralMCPDownloader:
    @pytest.fixture
    async def downloader(self, tmp_path):
        config_file = tmp_path / "test_config.yaml"
        # Create test configuration
        return GeneralMCPDownloader(
            config_file=str(config_file),
            install_dir=str(tmp_path / "servers")
        )
        
    async def test_download_real_server(self, downloader):
        # This test requires network access
        result = await downloader.download_servers(["filesystem"])
        assert result["successful"] > 0
```

### Test Fixtures

Common fixtures in `tests/conftest.py`:

```python
import pytest
from pathlib import Path

@pytest.fixture
def test_config_path(tmp_path):
    """Create a test configuration file."""
    config = tmp_path / "config.yaml"
    config.write_text("""
    templates:
      - name: test_template
        installation_method: npm
        command_pattern: 'npx {package}'
    servers:
      - name: test_server
        template: test_template
        variables:
          package: test-package
    """)
    return config

@pytest.fixture
def mock_server_response():
    """Mock server discovery response."""
    return [
        {
            "name": "test-mcp-server",
            "description": "Test server",
            "npm": {"name": "@test/mcp-server"}
        }
    ]
```

## Adding New Features

### Adding a New Installer

1. Create installer class:

```python
# src/haive/mcp/downloader/installers.py
class NewMethodInstaller(MCPInstaller):
    """Installer for new method."""
    
    async def can_handle(self, server_config, template):
        return template.installation_method == "new_method"
        
    async def install(self, server_config, template, install_dir):
        # Implementation
        return {"success": True}
        
    async def verify(self, server_config, template, install_dir):
        # Verification logic
        return True
```

2. Register installer:

```python
# src/haive/mcp/downloader/core.py
self.installers = [
    NPMInstaller(),
    PipInstaller(),
    GitInstaller(),
    DockerInstaller(),
    NewMethodInstaller()  # Add here
]
```

3. Add tests:

```python
# tests/unit/test_new_installer.py
class TestNewMethodInstaller:
    # Test implementation
    pass
```

### Adding New Discovery Source

1. Update discovery module:

```python
# src/haive/mcp/downloader/discovery.py
async def discover_from_new_source(self, url: str):
    """Discover servers from new source."""
    # Implementation
    pass
```

2. Add to configuration:

```yaml
patterns:
  discovery_sources:
    - type: new_source
      url: https://example.com/api
      parser: new_source_parser
```

## Debugging

### Enable Debug Logging

```python
import logging

# Set debug level
logging.basicConfig(level=logging.DEBUG)

# Or for specific module
logger = logging.getLogger("haive.mcp.downloader")
logger.setLevel(logging.DEBUG)
```

### Debug Configuration

```yaml
settings:
  log_level: DEBUG
  debug_mode: true
  verbose_errors: true
```

### Using VS Code

`.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Downloader",
            "type": "python",
            "request": "launch",
            "module": "scripts.download_servers",
            "args": ["download", "--servers", "filesystem"],
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

## Performance Optimization

### Async Best Practices

```python
# Good - Concurrent downloads
tasks = [download_server(s) for s in servers]
results = await asyncio.gather(*tasks)

# Bad - Sequential downloads
results = []
for server in servers:
    result = await download_server(server)
    results.append(result)
```

### Connection Pooling

```python
# Reuse aiohttp session
async with aiohttp.ClientSession() as session:
    downloader = GeneralMCPDownloader(session=session)
    # Use downloader with shared session
```

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run tests: `poetry run pytest`
5. Run linting: `poetry run black . && poetry run isort .`
6. Commit with clear message
7. Push and create PR

### Commit Message Format

```
feat: Add support for new installer type

- Implement NewMethodInstaller class
- Add configuration for new method
- Include comprehensive tests
- Update documentation

Closes #123
```

### Code Review Checklist

- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] Type hints added
- [ ] No hardcoded values
- [ ] Error handling implemented
- [ ] Logging added appropriately

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Create git tag: `git tag v1.2.3`
5. Push tag: `git push origin v1.2.3`
6. Poetry will handle the rest

## Troubleshooting Development Issues

### Poetry Lock Issues

```bash
# Remove lock and reinstall
rm poetry.lock
poetry install
```

### Import Errors

```bash
# Ensure package is installed in development mode
poetry install -e .
```

### Test Discovery Issues

```bash
# Verify test structure
pytest --collect-only
```