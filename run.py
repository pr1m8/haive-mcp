#!/usr/bin/env python3
"""Simple runner script that demonstrates proper Poetry usage.

Usage:
    poetry run python run.py setup      - Run full setup
    poetry run python run.py install    - Quick install
    poetry run python run.py check      - Health check
    poetry run python run.py validate   - Validate setup
    poetry run python run.py test       - Run tests
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command with Poetry."""
    print(f"\n🚀 {description}...")
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main runner."""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
        
    command = sys.argv[1]
    
    # Ensure we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: Must run from haive-mcp directory")
        return 1
    
    if command == "setup":
        return 0 if run_command(
            ["poetry", "run", "python", "setup_all.py"],
            "Running full setup"
        ) else 1
        
    elif command == "install":
        return 0 if run_command(
            ["poetry", "run", "python", "install.py"],
            "Running quick install"
        ) else 1
        
    elif command == "check":
        return 0 if run_command(
            ["poetry", "run", "python", "check_health.py"],
            "Running health check"
        ) else 1
        
    elif command == "validate":
        return 0 if run_command(
            ["poetry", "run", "python", "validate_setup.py"],
            "Running validation"
        ) else 1
        
    elif command == "test":
        return 0 if run_command(
            ["poetry", "run", "pytest", "-v"],
            "Running tests"
        ) else 1
        
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())