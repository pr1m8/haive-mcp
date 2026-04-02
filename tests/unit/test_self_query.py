"""Unit tests for the self-query engine."""

import pytest

from haive.mcp.self_query import MCPSelfQuery


class TestMCPSelfQuery:
    """Test the MCP self-query engine against the real server database."""

    @pytest.fixture
    def engine(self):
        return MCPSelfQuery()

    def test_loads_servers(self, engine):
        """Server database loads with expected count."""
        assert engine.server_count > 1000

    def test_search_returns_results(self, engine):
        """Search finds relevant servers."""
        results = engine.search("postgres")
        assert len(results) > 0
        # At least one result should have postgres in the name
        names = [r.get("name", "").lower() for r in results]
        assert any("postgres" in n for n in names)

    def test_search_by_filesystem(self, engine):
        """Search finds filesystem servers."""
        results = engine.search("filesystem")
        assert len(results) > 0

    def test_search_empty_query(self, engine):
        """Empty search returns no results."""
        results = engine.search("")
        assert len(results) == 0

    def test_search_limit(self, engine):
        """Search respects the limit parameter."""
        results = engine.search("server", limit=5)
        assert len(results) <= 5

    def test_get_categories(self, engine):
        """Categories are retrieved with counts."""
        cats = engine.get_categories()
        assert len(cats) > 5
        # Each category should have at least 1 server
        for count in cats.values():
            assert count >= 1

    def test_get_server_detail_exact(self, engine):
        """Server detail works with exact name match."""
        # Search first to find a real server name
        results = engine.search("filesystem")
        if results:
            name = results[0]["name"]
            detail = engine.get_server_detail(name)
            assert detail is not None
            assert detail["name"] == name

    def test_get_server_detail_partial(self, engine):
        """Server detail works with partial name match."""
        detail = engine.get_server_detail("postgres")
        assert detail is not None

    def test_get_server_detail_not_found(self, engine):
        """Server detail returns None for unknown server."""
        detail = engine.get_server_detail("this-server-definitely-does-not-exist-xyz")
        assert detail is None

    def test_search_scores_name_higher(self, engine):
        """Servers with query in name rank higher than description-only matches."""
        results = engine.search("github")
        if len(results) >= 2:
            # First result should have github in the name
            first_name = (results[0].get("name") or "").lower()
            assert "github" in first_name or len(results) == 1
