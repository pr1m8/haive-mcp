# Documentation Tests

This directory contains tests related to documentation functionality, particularly for testing Sphinx extensions and build processes.

## Files

- `test_viewcode.py` - Simple test module to verify sphinx.ext.viewcode functionality with regular autodoc directives
- `__init__.py` - Package initialization

## Purpose

These test files help us understand and debug documentation generation issues, particularly:

1. **ViewCode Testing**: Verifying that sphinx.ext.viewcode generates proper [source] links with regular autodoc
2. **AutoAPI Comparison**: Understanding why AutoAPI doesn't integrate with viewcode extension
3. **Documentation Build Testing**: Ensuring documentation builds correctly with various configurations

## Usage

The test files can be referenced in documentation RST files for testing purposes without contaminating the main package directory structure.
