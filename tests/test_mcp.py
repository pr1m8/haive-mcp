"""Tests for the MCP module."""


def test_mcp_import() -> None:
    """Test that the MCP module can be imported."""
    import haive.mcp

    assert haive.mcp.__version__ == "0.1.0"
