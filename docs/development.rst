Development
===========

This guide covers developing with and contributing to haive-mcp.

Development Setup
----------------

Setting up the development environment:

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/your-org/haive
    cd haive/backend/haive

    # Install with development dependencies
    poetry install --all-extras --with dev

    # Install pre-commit hooks
    poetry run pre-commit install

    # Verify installation
    poetry run pytest packages/haive-mcp/tests/ -v

Project Structure
----------------

The haive-mcp package is organized as follows:

.. code-block::

    packages/haive-mcp/
    ├── src/haive/mcp/
    │   ├── __init__.py              # Package exports
    │   ├── config.py                # Configuration models
    │   ├── manager.py               # MCP server management
    │   ├── agents/                  # MCP-enabled agents
    │   │   ├── mcp_agent.py         # Main MCP agent
    │   │   ├── documentation_agent.py
    │   │   └── transferable_mcp_agent.py
    │   ├── discovery/               # Server discovery
    │   │   ├── analyzer.py          # Server analysis
    │   │   └── server_discovery.py  # Discovery logic
    │   ├── mixins/                  # Mixin classes
    │   │   └── mcp_mixin.py         # MCP capabilities mixin
    │   ├── servers/                 # Server implementations
    │   │   ├── dataflow_mcp_server.py
    │   │   └── example_server_fastmcp.py
    │   └── tools/                   # Utility tools
    ├── tests/                       # Test suite
    ├── docs/                        # Documentation
    ├── examples/                    # Usage examples
    └── README.md                    # Package documentation

Running Tests
------------

The test suite includes unit tests, integration tests, and examples:

.. code-block:: bash

    # Run all tests
    poetry run pytest packages/haive-mcp/tests/

    # Run with coverage
    poetry run pytest packages/haive-mcp/tests/ --cov=haive.mcp

    # Run specific test file
    poetry run pytest packages/haive-mcp/tests/test_config.py -v

    # Run integration tests (requires MCP servers)
    poetry run pytest packages/haive-mcp/tests/integration/ -v

    # Run examples as tests
    poetry run python packages/haive-mcp/examples/basic_mcp_example.py

Writing Tests
------------

Test Structure
~~~~~~~~~~~~~~

Tests are organized by module:

.. code-block::

    tests/
    ├── unit/                    # Unit tests
    │   ├── test_config.py       # Configuration tests
    │   ├── test_manager.py      # Manager tests
    │   └── test_agents.py       # Agent tests
    ├── integration/             # Integration tests
    │   ├── test_mcp_servers.py  # Server integration
    │   └── test_full_workflow.py
    └── fixtures/                # Test fixtures
        ├── mock_servers.py      # Mock MCP servers
        └── test_configs.py      # Test configurations

Example Test
~~~~~~~~~~~~

.. code-block:: python

    import pytest
    from haive.mcp.config import MCPConfig, MCPServerConfig
    from haive.mcp.manager import MCPManager

    class TestMCPConfig:
        """Test MCP configuration."""

        def test_basic_config_creation(self):
            """Test creating a basic MCP configuration."""
            config = MCPConfig(
                enabled=True,
                servers={
                    "test": MCPServerConfig(
                        name="test",
                        transport="stdio",
                        command="echo",
                        args=["hello"]
                    )
                }
            )
            
            assert config.enabled is True
            assert len(config.servers) == 1
            assert config.servers["test"].name == "test"

        def test_server_validation(self):
            """Test server configuration validation."""
            with pytest.raises(ValidationError):
                MCPServerConfig(
                    name="",  # Invalid empty name
                    transport="invalid_transport"
                )

        @pytest.mark.asyncio
        async def test_manager_integration(self):
            """Test manager with configuration."""
            config = MCPConfig(enabled=True)
            manager = MCPManager(config)
            
            # Test manager initialization
            assert manager.enabled is True
            assert len(manager._servers) == 0

Mock Servers
~~~~~~~~~~~~

For testing without actual MCP servers:

.. code-block:: python

    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    @pytest.fixture
    def mock_mcp_client():
        """Mock MCP client for testing."""
        client = AsyncMock()
        client.connect = AsyncMock(return_value=True)
        client.list_tools = AsyncMock(return_value=[
            {"name": "test_tool", "description": "A test tool"}
        ])
        client.call_tool = AsyncMock(return_value={"result": "success"})
        return client

    @pytest.mark.asyncio
    async def test_with_mock_server(mock_mcp_client):
        """Test agent with mocked MCP server."""
        # Use mock client in test
        pass

Code Style
----------

The project follows strict coding standards:

Python Style
~~~~~~~~~~~~

- **PEP 8** compliance with 88-character line limit
- **Type hints** for all public functions and methods
- **Google-style docstrings** for documentation
- **Black** for code formatting
- **isort** for import sorting
- **mypy** for static type checking

.. code-block:: python

    from typing import Dict, List, Optional

    def process_servers(
        servers: Dict[str, MCPServerConfig],
        categories: Optional[List[str]] = None
    ) -> List[str]:
        """Process MCP server configurations.
        
        Args:
            servers: Dictionary of server configurations
            categories: Optional list of categories to filter by
            
        Returns:
            List of processed server names
            
        Raises:
            ValueError: If server configuration is invalid
        """
        result = []
        for name, config in servers.items():
            if categories and config.category not in categories:
                continue
            result.append(name)
        return result

Documentation Style
~~~~~~~~~~~~~~~~~~

- **Google-style docstrings** for all public APIs
- **Sphinx autodoc** compatible
- **Type annotations** in docstrings
- **Examples** in docstrings where helpful

.. code-block:: python

    class MCPAgent:
        """An agent with MCP capabilities.
        
        This agent extends SimpleAgent with MCP server integration,
        providing access to external tools and resources.
        
        Attributes:
            mcp_config: Optional MCP configuration
            
        Example:
            Basic usage::
            
                agent = MCPAgent(
                    engine=engine,
                    mcp_config=mcp_config
                )
                await agent.setup()
        """

Linting and Formatting
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Format code
    poetry run black packages/haive-mcp/

    # Sort imports
    poetry run isort packages/haive-mcp/

    # Type checking
    poetry run mypy packages/haive-mcp/src/

    # Lint code
    poetry run ruff check packages/haive-mcp/

    # Run all checks
    poetry run pre-commit run --all-files

Contributing Guidelines
----------------------

Pull Request Process
~~~~~~~~~~~~~~~~~~~

1. **Fork** the repository and create a feature branch
2. **Write tests** for new functionality
3. **Update documentation** including docstrings and guides
4. **Run the full test suite** and ensure all tests pass
5. **Submit a pull request** with a clear description

Commit Messages
~~~~~~~~~~~~~~

Use conventional commit format:

.. code-block::

    feat(mcp): add health monitoring for MCP servers
    fix(agents): resolve tool discovery timeout issue
    docs(mcp): improve configuration examples
    test(manager): add integration tests for server lifecycle

Code Review Checklist
~~~~~~~~~~~~~~~~~~~~~

Before submitting, ensure:

- [ ] All tests pass
- [ ] Code coverage is maintained
- [ ] Type hints are included  
- [ ] Docstrings follow Google style
- [ ] Examples are included for new features
- [ ] Documentation is updated
- [ ] No breaking changes (or marked as such)
- [ ] Performance impact is considered

Release Process
--------------

Version Management
~~~~~~~~~~~~~~~~~

The project uses semantic versioning:

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

.. code-block:: bash

    # Update version
    poetry version patch|minor|major

    # Tag release
    git tag v0.2.0
    git push origin v0.2.0

Building Documentation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Install docs dependencies
    poetry install --extras docs

    # Build documentation
    cd packages/haive-mcp/docs
    poetry run sphinx-build -b html . _build/html

    # Serve locally
    poetry run python -m http.server 8000 -d _build/html

Publishing
~~~~~~~~~

.. code-block:: bash

    # Build package
    poetry build

    # Publish to PyPI (with proper credentials)
    poetry publish

Debugging
---------

Common Issues
~~~~~~~~~~~~

**Import Errors**
    - Check that all dependencies are installed
    - Verify PYTHONPATH includes the src directory
    - Use `poetry shell` to activate the virtual environment

**MCP Server Connection Issues**
    - Verify MCP servers are installed and accessible
    - Check server startup logs for errors
    - Enable debug logging for detailed connection info

**Test Failures**
    - Ensure test dependencies are installed
    - Check that mock servers are configured correctly
    - Run tests individually to isolate issues

Debug Configuration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import logging

    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("haive.mcp")
    logger.setLevel(logging.DEBUG)

    # Debug specific components
    logging.getLogger("haive.mcp.manager").setLevel(logging.DEBUG)
    logging.getLogger("haive.mcp.agents").setLevel(logging.DEBUG)

Performance Profiling
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import cProfile
    import pstats

    # Profile MCP operations
    profiler = cProfile.Profile()
    profiler.enable()

    # Run MCP operations
    await agent.setup()
    result = await agent.arun({"messages": [...]})

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(10)

Getting Help
-----------

- **Documentation**: Read the full documentation at https://haive-mcp.readthedocs.io
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Ask questions in GitHub Discussions
- **Discord**: Join the community Discord for real-time help
- **Email**: Contact the maintainers for security issues