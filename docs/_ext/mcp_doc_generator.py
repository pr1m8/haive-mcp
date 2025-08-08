"""Sphinx extension to generate MCP server documentation during build.

This extension automatically generates RST documentation for MCP servers
from JSON data before the Sphinx build process.
"""

import logging
import sys
from pathlib import Path

from sphinx.application import Sphinx

# Add the scripts directory to path
docs_dir = Path(__file__).parent.parent
package_dir = docs_dir.parent
scripts_dir = package_dir / "scripts"
sys.path.insert(0, str(scripts_dir))

logger = logging.getLogger(__name__)


def generate_mcp_docs(app: Sphinx, config):
    """Generate MCP server documentation before build."""
    logger.info("Generating MCP server documentation...")

    try:
        # Import the generator
        from generate_server_docs import MCPDocumentationGenerator

        # Create generator instance
        generator = MCPDocumentationGenerator(base_path=package_dir)

        # Generate all documentation
        generator.generate_all_documentation()

        logger.info("MCP server documentation generated successfully!")

    except Exception as e:
        logger.error(f"Failed to generate MCP documentation: {e}")
        # Don't fail the build, just log the error
        import traceback

        traceback.print_exc()


def setup(app: Sphinx):
    """Setup the extension."""
    app.connect("config-inited", generate_mcp_docs)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
