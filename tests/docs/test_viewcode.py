"""Simple test module to check if viewcode works.

This test module is used to verify that sphinx.ext.viewcode works correctly
with regular autodoc directives. It serves as a comparison point to understand
why AutoAPI doesn't generate [source] links.
"""


class TestClass:
    """A simple test class."""

    def test_method(self):
        """A test method."""
        return "Hello, World!"


def test_function():
    """A test function."""
    return 42


def another_function(param: str) -> str:
    """Another function with parameters.

    Args:
        param: A string parameter

    Returns:
        The input parameter with a prefix
    """
    return f"Processed: {param}"
