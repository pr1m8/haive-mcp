"""Unit tests for the MCPInstallerService."""

import pytest

from haive.mcp.installer_service import MCPInstallerService, InstallMethod


class TestMCPInstallerService:
    """Test the installer service search, plan, and config generation."""

    @pytest.fixture
    def service(self):
        return MCPInstallerService(require_approval=False)

    def test_server_count(self, service):
        """Service loads the server database."""
        assert service.server_count > 1000

    def test_search_returns_results(self, service):
        """Search finds servers."""
        results = service.search("filesystem")
        assert len(results) > 0

    def test_search_empty(self, service):
        """Empty search returns nothing."""
        results = service.search("")
        assert len(results) == 0

    def test_get_detail_enriches(self, service):
        """Detail returns enriched server info."""
        detail = service.get_detail("21st.dev Magic")
        assert detail is not None
        assert detail["name"] == "21st.dev Magic"
        assert detail.get("install_command")

    @pytest.mark.asyncio
    async def test_plan_install_readme_method(self, service):
        """Plan install uses README extraction as primary method."""
        plan = await service.plan_install("21st.dev Magic")
        assert plan is not None
        assert plan.server_name == "21st.dev Magic"
        assert plan.install_command
        assert plan.method == InstallMethod.README
        assert plan.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_plan_install_not_found(self, service):
        """Plan install returns None for unknown server."""
        plan = await service.plan_install("this-server-does-not-exist-xyz")
        assert plan is None

    @pytest.mark.asyncio
    async def test_plan_install_has_config(self, service):
        """Plan includes a valid config dict."""
        plan = await service.plan_install("Database")
        assert plan is not None
        assert "command" in plan.config
        assert "transport" in plan.config

    @pytest.mark.asyncio
    async def test_approve_auto_when_disabled(self, service):
        """Approval is automatic when require_approval=False."""
        plan = await service.plan_install("Database")
        assert plan is not None
        approved = await service.approve(plan)
        assert approved is True

    @pytest.mark.asyncio
    async def test_approve_with_callback(self):
        """Custom approval callback is called."""
        callback_called = False

        def my_callback(plan):
            nonlocal callback_called
            callback_called = True
            return True

        svc = MCPInstallerService(
            require_approval=True, approval_callback=my_callback
        )
        plan = await svc.plan_install("Database")
        assert plan is not None
        approved = await svc.approve(plan)
        assert approved is True
        assert callback_called is True

    @pytest.mark.asyncio
    async def test_approve_callback_rejects(self):
        """Custom callback can reject installation."""
        svc = MCPInstallerService(
            require_approval=True, approval_callback=lambda p: False
        )
        plan = await svc.plan_install("Database")
        assert plan is not None
        approved = await svc.approve(plan)
        assert approved is False

    def test_generate_langchain_config(self, service):
        """Generates valid langchain-mcp-adapters config."""
        config = service.generate_langchain_config("21st.dev Magic")
        assert config is not None
        assert "21st.dev Magic" in config
        entry = config["21st.dev Magic"]
        assert "command" in entry
        assert "args" in entry
        assert entry["transport"] == "stdio"

    def test_generate_claude_desktop_config(self, service):
        """Generates valid Claude Desktop mcp.json config."""
        config = service.generate_claude_desktop_config("21st.dev Magic")
        assert config is not None
        assert "mcpServers" in config
        assert "21st.dev Magic" in config["mcpServers"]
        entry = config["mcpServers"]["21st.dev Magic"]
        assert "command" in entry
        assert "args" in entry

    def test_generate_mcp_server_config(self, service):
        """Generates valid MCPServerConfig object."""
        config = service.generate_mcp_server_config("21st.dev Magic")
        assert config is not None
        assert config.name == "21st.dev Magic"
        assert config.command is not None
        assert config.transport.value == "stdio"


class TestInstallCommandDerivation:
    """Test install command extraction from READMEs."""

    @pytest.fixture
    def loader(self):
        from haive.mcp.documentation.doc_loader import MCPDocumentationLoader
        return MCPDocumentationLoader()

    def test_derive_npx(self, loader):
        readme = "## Install\n```\nnpx -y @scope/my-server\n```"
        cmd = loader._derive_install_command(readme, "owner", "repo")
        assert cmd == "npx -y @scope/my-server"

    def test_derive_uvx(self, loader):
        readme = "## Install\n```\nuvx mcp-server-fetch\n```"
        cmd = loader._derive_install_command(readme, "owner", "repo")
        assert cmd == "uvx mcp-server-fetch"

    def test_derive_pip(self, loader):
        readme = "## Install\n```\npip install mcp-server-tool\n```"
        cmd = loader._derive_install_command(readme, "owner", "repo")
        assert cmd == "pip install mcp-server-tool"

    def test_derive_skips_inspector(self, loader):
        readme = "## Debug\n```\nnpx @modelcontextprotocol/inspector uv run server\n```\n## Install\n```\npip install my-server\n```"
        cmd = loader._derive_install_command(readme, "owner", "repo")
        assert cmd == "pip install my-server"

    def test_derive_fallback_from_repo(self, loader):
        cmd = loader._derive_install_command("", "owner", "mcp-server-test")
        assert cmd == "npx -y @owner/mcp-server-test"

    def test_derive_fallback_plain_repo(self, loader):
        cmd = loader._derive_install_command("", "owner", "my-tool")
        assert cmd == "npx -y my-tool"

    def test_derive_empty(self, loader):
        cmd = loader._derive_install_command("", "", "")
        assert cmd == ""

    def test_derive_strips_comments(self, loader):
        readme = "## Install\n```\nnpx -y my-server # start the server\n```"
        cmd = loader._derive_install_command(readme, "owner", "repo")
        assert cmd == "npx -y my-server"

    def test_generate_server_config(self, loader):
        """Config generation works for enriched servers."""
        loader.load_all_mcp_documents()
        config = loader.generate_server_config("21st.dev Magic")
        assert config is not None
        assert config["command"] in ("npx", "uvx", "pip", "python")
        assert config["transport"] == "stdio"
