#!/usr/bin/env python3
"""Simple test runner for MCP tests."""

import subprocess
import sys
from pathlib import Path

def run_tests(test_type="all"):
    """Run MCP tests.
    
    Args:
        test_type: Type of tests to run (all, unit, integration, specific)
    """
    base_cmd = ["poetry", "run", "pytest", "tests/", "-v"]
    
    if test_type == "unit":
        # Run only unit tests (fast)
        cmd = base_cmd + ["-m", "not integration and not slow"]
        print("Running unit tests only...")
    elif test_type == "integration":
        # Run integration tests
        cmd = base_cmd + ["-m", "integration"]
        print("Running integration tests...")
    elif test_type == "coverage":
        # Run with coverage
        cmd = base_cmd + ["--cov=haive.mcp", "--cov-report=html", "--cov-report=term"]
        print("Running tests with coverage...")
    elif test_type == "specific":
        # Run specific test file
        if len(sys.argv) < 3:
            print("Please specify test file: python run_tests.py specific test_bulk_download")
            return 1
        test_file = f"tests/test_{sys.argv[2]}.py"
        if not Path(test_file).exists():
            print(f"Test file {test_file} not found!")
            return 1
        cmd = ["poetry", "run", "pytest", test_file, "-v"]
        print(f"Running {test_file}...")
    else:
        # Run all tests
        print("Running all tests...")
    
    # Execute tests
    result = subprocess.run(cmd)
    return result.returncode

def main():
    """Main entry point."""
    print("MCP Test Runner")
    print("=" * 50)
    
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    valid_types = ["all", "unit", "integration", "coverage", "specific"]
    if test_type not in valid_types:
        print(f"Invalid test type: {test_type}")
        print(f"Valid options: {', '.join(valid_types)}")
        return 1
    
    return run_tests(test_type)

if __name__ == "__main__":
    sys.exit(main())