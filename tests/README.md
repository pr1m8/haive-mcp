# MCP Tests

This directory contains comprehensive tests for the MCP (Model Context Protocol) functionality in the haive-mcp package.

## Test Structure

### Test Files

1. **test_mcp_server_setup.py**
   - Tests for MCP server setup and management
   - Server lifecycle (start, stop, status)
   - Simple, filesystem, and time server functionality
   - Non-interactive mode testing

2. **test_bulk_download.py**
   - Tests for bulk installation of MCP servers
   - Star-based filtering and installation
   - Category-based installation
   - Top N server installation
   - Installation report generation

3. **test_specific_download.py**
   - Tests for specific installer types (NPM, pip, Git, Docker, Binary, Curl)
   - Individual server installation
   - Installation verification
   - Error handling for failed installations

4. **test_viewing_installed.py**
   - Tests for discovering installed MCP servers
   - NPM and pip server discovery
   - Configuration file discovery
   - Server availability checking
   - Export functionality

## Running Tests

### Run All Tests
```bash
poetry run pytest tests/ -v
```

### Run Specific Test File
```bash
poetry run pytest tests/test_mcp_server_setup.py -v
```

### Run with Coverage
```bash
poetry run pytest tests/ --cov=haive.mcp --cov-report=html
```

### Run Only Unit Tests (Fast)
```bash
poetry run pytest tests/ -v -m "not integration and not slow"
```

### Run Integration Tests
```bash
poetry run pytest tests/ -v -m integration
```

## Test Categories

Tests are marked with the following categories:

- **integration**: Tests that require external resources or take longer
- **slow**: Tests that take significant time to complete
- **requires_network**: Tests that need network access

## Fixtures

Common fixtures are provided in `conftest.py`:

- `temp_test_dir`: Temporary directory for test files
- `event_loop`: Event loop for async tests
- `mock_subprocess_run`: Mock for subprocess.run calls
- `sample_mcp_servers`: Sample server data for testing

## Writing New Tests

When adding new tests:

1. Use appropriate fixtures from conftest.py
2. Mock external dependencies (subprocess, network calls)
3. Test both success and failure cases
4. Add appropriate markers (@pytest.mark.integration, etc.)
5. Follow the existing test structure

Example:
```python
def test_new_functionality(temp_test_dir, mock_subprocess_run):
    """Test description here."""
    # Setup
    mock_subprocess_run.return_value.returncode = 0
    
    # Execute
    result = your_function()
    
    # Assert
    assert result is not None
    mock_subprocess_run.assert_called_once()
```

## Coverage Goals

We aim for:
- 80%+ overall coverage
- 90%+ coverage for critical functionality
- 100% coverage for error handling paths
