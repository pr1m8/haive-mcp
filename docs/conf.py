"""Sphinx configuration for haive-mcp documentation.

This file configures Sphinx to generate documentation for the haive-mcp package
using autodoc, autosummary, and Google-style docstrings.
"""

import os
import sys
from datetime import datetime

# Add source to path
sys.path.insert(0, os.path.abspath("../src"))

# Project information
project = "haive-mcp"
copyright = f"{datetime.now().year}, Haive Team"
author = "Haive Team"
version = "0.1.0"
release = "0.1.0"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}

# Autosummary settings
autosummary_generate = True
autosummary_imported_members = True

# Napoleon settings (for Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None

# Type hints settings
typehints_defaults = "comma"
typehints_document_rtype = True

# MyST settings (for Markdown)
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "tasklist",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev", None),
    "langchain": ("https://python.langchain.com/docs", None),
}

# Templates
templates_path = ["_templates"]

# Exclude patterns
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# HTML theme
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "includehidden": True,
}

# Static files
html_static_path = ["_static"]

# Source suffix
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}