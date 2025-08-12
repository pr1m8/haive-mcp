"""Sphinx configuration for haive-mcp documentation."""

import os
import sys

# Path setup - add the parent of haive to the path
sys.path.insert(0, os.path.abspath("../../src"))

# Import shared Haive configuration from pydevelop-docs package
from pydevelop_docs.config import get_haive_config

# Get package-specific configuration
package_name = "haive-mcp"
# This is the key - point to the haive directory, not src
package_path = "../../src/haive"

config = get_haive_config(
    package_name=package_name, package_path=package_path, is_central_hub=False
)

# Apply configuration to globals
globals().update(config)

# Override the autoapi_dirs to ensure we get the right module paths
# We want autoapi to see haive.mcp, not just mcp
autoapi_dirs = ["../../src/haive"]  # This should pick up mcp under haive

# Configure autoapi to only document haive.mcp modules
autoapi_ignore = config.get("autoapi_ignore", [])
autoapi_ignore.extend(
    [
        "**/__pycache__/**",
        "**/tests/**",
        "**/test_*.py",
    ]
)

# Filter to only include haive.mcp modules
autoapi_options = config.get("autoapi_options", [])
if "imported-members" in autoapi_options:
    autoapi_options.remove("imported-members")

# Add a custom template directory if needed
autoapi_template_dir = "_autoapi_templates"

# Add the project root to Python path so autoapi can find haive package
project_root = os.path.abspath("../../../../")  # Path to haive root
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try to force autoapi to use the full module path
autoapi_python_use_implicit_namespaces = False


# Add autoapi callback to fix module names
def autoapi_skip_member(app, what, name, obj, skip, options):
    """Fix module names to include haive prefix."""
    if hasattr(obj, "name") and obj.name.startswith("mcp"):
        # This won't work for renaming, but we can at least see what's happening
        pass
    return skip


def setup(app):
    """Setup Sphinx app with custom configurations."""
    app.connect("autoapi-skip-member", autoapi_skip_member)
