#!/usr/bin/env python3
"""Simple test of MCP server functionality."""

import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that we can import MCP components."""
    logger.info("Testing MCP imports...")
    
    try:
        from mcp.server import FastMCP
        logger.info("✓ Imported FastMCP from mcp.server")
    except ImportError as e:
        logger.error(f"✗ Failed to import FastMCP: {e}")
        return False
    
    try:
        from mcp import types
        logger.info("✓ Imported mcp.types")
    except ImportError as e:
        logger.error(f"✗ Failed to import mcp.types: {e}")
        return False
    
    try:
        import mcp.server.stdio
        logger.info("✓ Imported mcp.server.stdio")
    except ImportError as e:
        logger.error(f"✗ Failed to import mcp.server.stdio: {e}")
        return False
    
    return True


def test_server_creation():
    """Test creating a FastMCP server."""
    logger.info("\nTesting server creation...")
    
    try:
        from mcp.server import FastMCP
        
        # Create a simple server
        mcp = FastMCP("test-server")
        logger.info("✓ Created FastMCP server instance")
        
        # Add a simple tool
        @mcp.tool()
        async def hello(name: str) -> str:
            """Say hello to someone."""
            return f"Hello, {name}!"
        
        logger.info("✓ Added tool to server")
        
        # Check if tool was registered
        logger.info(f"✓ Server has tools: {hasattr(mcp, '_tools')}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to create server: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_langchain_mcp():
    """Test LangChain MCP adapter imports."""
    logger.info("\nTesting LangChain MCP adapters...")
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        logger.info("✓ Imported MultiServerMCPClient")
        
        from langchain_mcp_adapters.client import load_mcp_tools
        logger.info("✓ Imported load_mcp_tools")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Failed to import LangChain MCP adapters: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("=== MCP Package Tests ===\n")
    
    test1 = test_imports()
    test2 = test_server_creation()
    test3 = test_langchain_mcp()
    
    logger.info("\n=== Test Summary ===")
    logger.info(f"Import Tests: {'✓ PASSED' if test1 else '✗ FAILED'}")
    logger.info(f"Server Creation: {'✓ PASSED' if test2 else '✗ FAILED'}")
    logger.info(f"LangChain Adapters: {'✓ PASSED' if test3 else '✗ FAILED'}")
    
    all_passed = test1 and test2 and test3
    logger.info(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")


if __name__ == "__main__":
    main()