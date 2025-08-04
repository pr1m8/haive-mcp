# Poetry Usage Best Practices for haive-mcp

This document explains the proper way to use Poetry with the haive-mcp package, avoiding sys.path manipulation.

## Key Principles

1. **Always use `poetry run`** - This ensures the virtual environment is active
2. **Never manipulate sys.path** - Poetry handles Python paths correctly
3. **Install in editable mode** - Use `poetry install` to install the package

## Common Commands

### Running Scripts

```bash
# Always prefix with poetry run
poetry run python script.py

# Or activate the shell
poetry shell
python script.py
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific tests
poetry run pytest tests/unit/test_config.py
```

### Checking Imports

```bash
# Test imports properly
poetry run python -c "from haive.mcp import MCPManager; print('Success')"

# NOT like this (wrong)
python -c "import sys; sys.path.insert(0, 'src'); from haive.mcp import MCPManager"
```

### Installing Dependencies

```bash
# Install all dependencies
poetry install --all-extras

# Add new dependencies
poetry add package-name

# Add optional dependencies
poetry add package-name --optional
```

## Setup Scripts

All setup scripts have been updated to use Poetry properly:

1. **setup_all.py** - Uses `poetry run` for all Python execution
2. **install.py** - Uses `poetry run` for import checks
3. **check_health.py** - Uses subprocess with `poetry run`
4. **validate_setup.py** - Uses subprocess with `poetry run`

## Example: Running MCP Code

```python
# script.py
from haive.mcp import MCPManager, MCPConfig

manager = MCPManager()
print("MCP Manager created successfully!")
```

```bash
# Run it properly
poetry run python script.py
```

## Troubleshooting

### Import Errors

If you get import errors:

1. Ensure you're in the package directory
2. Run `poetry install --all-extras`
3. Use `poetry run` prefix

### Path Issues

Never do this:

```python
import sys
sys.path.insert(0, "src")  # Wrong!
```

Instead, ensure proper installation:

```bash
poetry install
poetry run python your_script.py
```

## Integration with IDEs

### VS Code

1. Select the Poetry interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
2. Choose the one in `.venv` directory

### PyCharm

1. Settings → Project → Python Interpreter
2. Add interpreter → Poetry Environment

## Summary

- Always use `poetry run` or activate the Poetry shell
- Never manipulate `sys.path`
- Install packages with `poetry add`
- Run tests with `poetry run pytest`
- Scripts should import normally without path hacks
