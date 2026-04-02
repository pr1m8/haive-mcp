"""MCP Server Installer Service with LLM fallback and HITL approval.

Provides a complete install pipeline:
1. Search the 1,960 server database for matching servers
2. Extract install command from README (primary)
3. Fall back to LLM to derive install command if extraction fails
4. HITL approval before installation (configurable)
5. Install via npx/uvx/pip and verify connectivity

The service is usable standalone or integrated into IntelligentMCPAgent.

Example:
    .. code-block:: python

        from haive.mcp.installer_service import MCPInstallerService

        service = MCPInstallerService(require_approval=True)
        result = await service.search_and_install("postgres")
        # Searches DB → finds server → derives install → asks approval → installs
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import shutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from haive.mcp.config import MCPServerConfig, MCPTransport
from haive.mcp.documentation.doc_loader import MCPDocumentationLoader
from haive.mcp.self_query import MCPSelfQuery

logger = logging.getLogger(__name__)


class InstallMethod(str, Enum):
    """How the install command was determined."""
    README = "readme"
    LLM = "llm"
    FALLBACK = "fallback"


@dataclass
class InstallPlan:
    """Plan for installing an MCP server."""
    server_name: str
    description: str
    install_command: str
    method: InstallMethod
    config: dict[str, Any]
    repository_url: str = ""
    stars: int | None = None
    confidence: float = 1.0


@dataclass
class InstallResult:
    """Result of an installation attempt."""
    success: bool
    server_name: str
    message: str
    config: dict[str, Any] | None = None
    tools_discovered: list[str] = field(default_factory=list)


class MCPInstallerService:
    """Service for searching, configuring, and installing MCP servers.

    Supports three modes for deriving install commands:
    1. **README extraction** -- parses install commands from server READMEs
    2. **LLM fallback** -- uses an LLM to analyze the repo and suggest install
    3. **Pattern fallback** -- derives from repo name conventions

    HITL approval can be enabled via ``require_approval=True``. The default
    approval handler prints to stdout and waits for input. Override with a
    custom ``approval_callback``.
    """

    def __init__(
        self,
        require_approval: bool = True,
        approval_callback: Callable[[InstallPlan], bool] | None = None,
        llm_callback: Callable[[str, str], str] | None = None,
        auto_verify: bool = True,
    ):
        """Initialize the installer service.

        Args:
            require_approval: Require human approval before install.
            approval_callback: Custom approval function. Receives an
                ``InstallPlan`` and returns ``True`` to approve.
                If ``None``, uses interactive stdin prompt.
            llm_callback: Custom LLM function for install command derivation.
                Receives ``(server_name, readme_content)`` and returns
                an install command string. If ``None``, uses a built-in
                prompt with langchain (if available).
            auto_verify: Verify the command exists before installing.
        """
        self.require_approval = require_approval
        self.approval_callback = approval_callback
        self.llm_callback = llm_callback
        self.auto_verify = auto_verify
        self._query = MCPSelfQuery()
        self._loader = self._query.loader

    @property
    def server_count(self) -> int:
        return self._query.server_count

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search the server database."""
        return self._query.search(query, limit=limit)

    def get_detail(self, name: str) -> dict[str, Any] | None:
        """Get enriched detail for a server."""
        return self._query.get_server_detail(name)

    # ------------------------------------------------------------------
    # Install plan
    # ------------------------------------------------------------------

    async def plan_install(self, server_name: str) -> InstallPlan | None:
        """Create an install plan for a server.

        Tries README extraction first, then LLM fallback.

        Args:
            server_name: Server name (exact or partial match).

        Returns:
            ``InstallPlan`` or ``None`` if server not found.
        """
        enriched = self._loader.get_enriched_server(server_name)
        if enriched is None:
            return None

        install_cmd = enriched.get("install_command", "")
        method = InstallMethod.README
        confidence = 0.9

        # If no install command from README, try LLM fallback
        if not install_cmd:
            readme = enriched.get("readme_content", "")
            install_cmd = await self._llm_derive_install(
                enriched.get("name", server_name), readme
            )
            if install_cmd:
                method = InstallMethod.LLM
                confidence = 0.7
            else:
                # Last resort: pattern-based fallback
                owner = enriched.get("repository_owner", "")
                repo = enriched.get("repository_name", "")
                if repo:
                    install_cmd = f"npx -y {repo}"
                    method = InstallMethod.FALLBACK
                    confidence = 0.4

        if not install_cmd:
            return None

        config = self._loader.generate_server_config(server_name) or {
            "command": install_cmd.split()[0],
            "args": install_cmd.split()[1:],
            "transport": "stdio",
        }

        return InstallPlan(
            server_name=enriched.get("name", server_name),
            description=enriched.get("description", ""),
            install_command=install_cmd,
            method=method,
            config=config,
            repository_url=enriched.get("repository_url", ""),
            stars=enriched.get("stars"),
            confidence=confidence,
        )

    # ------------------------------------------------------------------
    # Approval
    # ------------------------------------------------------------------

    async def approve(self, plan: InstallPlan) -> bool:
        """Request approval for an install plan.

        Uses ``approval_callback`` if set, otherwise prompts on stdin.

        Args:
            plan: The install plan to approve.

        Returns:
            ``True`` if approved.
        """
        if not self.require_approval:
            return True

        if self.approval_callback:
            result = self.approval_callback(plan)
            if asyncio.iscoroutine(result):
                return await result
            return result

        # Default: interactive stdin
        return self._interactive_approve(plan)

    @staticmethod
    def _interactive_approve(plan: InstallPlan) -> bool:
        """Interactive approval via stdin."""
        print(f"\n  Install MCP Server")
        print(f"  {'=' * 40}")
        print(f"  Server:  {plan.server_name}")
        if plan.description:
            print(f"  Desc:    {plan.description[:80]}")
        print(f"  Command: {plan.install_command}")
        print(f"  Method:  {plan.method.value} (confidence: {plan.confidence:.0%})")
        if plan.repository_url:
            print(f"  Repo:    {plan.repository_url}")
        print()
        try:
            answer = input("  Approve? [y/N] ").strip().lower()
            return answer in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    # ------------------------------------------------------------------
    # Install
    # ------------------------------------------------------------------

    async def install(self, plan: InstallPlan) -> InstallResult:
        """Execute an install plan.

        Verifies the command is available, then attempts installation.

        Args:
            plan: Approved install plan.

        Returns:
            ``InstallResult`` with success status.
        """
        cmd_parts = plan.install_command.split()
        binary = cmd_parts[0]

        # Verify binary exists
        if self.auto_verify and not shutil.which(binary):
            return InstallResult(
                success=False,
                server_name=plan.server_name,
                message=f"Command '{binary}' not found. Install it first.",
            )

        # Try connecting with langchain-mcp-adapters
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient

            lc_config = {
                plan.server_name: {
                    "command": plan.config.get("command", binary),
                    "args": plan.config.get("args", cmd_parts[1:]),
                    "transport": "stdio",
                }
            }
            if plan.config.get("env"):
                lc_config[plan.server_name]["env"] = plan.config["env"]

            client = MultiServerMCPClient(lc_config)
            tools = await client.get_tools()
            tool_names = [t.name for t in tools]

            return InstallResult(
                success=True,
                server_name=plan.server_name,
                message=f"Connected! {len(tools)} tools available.",
                config=plan.config,
                tools_discovered=tool_names,
            )

        except Exception as e:
            return InstallResult(
                success=False,
                server_name=plan.server_name,
                message=f"Connection failed: {e}",
                config=plan.config,
            )

    # ------------------------------------------------------------------
    # Combined flow
    # ------------------------------------------------------------------

    async def search_and_install(self, query: str) -> InstallResult | None:
        """Full pipeline: search → plan → approve → install.

        Args:
            query: Search query (e.g., ``"postgres"``, ``"filesystem"``).

        Returns:
            ``InstallResult`` or ``None`` if no server found / rejected.
        """
        # Search
        results = self.search(query)
        if not results:
            logger.info(f"No servers found for '{query}'")
            return None

        # Plan for best match
        plan = await self.plan_install(results[0]["name"])
        if plan is None:
            logger.info(f"Could not create install plan for {results[0]['name']}")
            return None

        # Approve
        approved = await self.approve(plan)
        if not approved:
            return InstallResult(
                success=False,
                server_name=plan.server_name,
                message="Installation rejected by user.",
            )

        # Install
        return await self.install(plan)

    def search_and_install_sync(self, query: str) -> InstallResult | None:
        """Synchronous wrapper for ``search_and_install``."""
        return asyncio.run(self.search_and_install(query))

    # ------------------------------------------------------------------
    # Generate configs (for external use)
    # ------------------------------------------------------------------

    def generate_mcp_server_config(self, server_name: str) -> MCPServerConfig | None:
        """Generate an ``MCPServerConfig`` for a server.

        Args:
            server_name: Server name.

        Returns:
            ``MCPServerConfig`` ready to use with ``MCPManager``.
        """
        config = self._loader.generate_server_config(server_name)
        if config is None:
            return None

        return MCPServerConfig(
            name=server_name,
            transport=MCPTransport.STDIO,
            command=config["command"],
            args=config.get("args", []),
            env=config.get("env", {}),
        )

    def generate_langchain_config(self, server_name: str) -> dict[str, Any] | None:
        """Generate a ``langchain-mcp-adapters`` compatible config.

        Args:
            server_name: Server name.

        Returns:
            Dict suitable for ``MultiServerMCPClient``.
        """
        config = self._loader.generate_server_config(server_name)
        if config is None:
            return None

        lc = {
            server_name: {
                "command": config["command"],
                "args": config.get("args", []),
                "transport": "stdio",
            }
        }
        if config.get("env"):
            lc[server_name]["env"] = config["env"]
        return lc

    def generate_claude_desktop_config(self, server_name: str) -> dict[str, Any] | None:
        """Generate a Claude Desktop ``mcp.json`` config entry.

        Args:
            server_name: Server name.

        Returns:
            Dict in Claude Desktop format.
        """
        config = self._loader.generate_server_config(server_name)
        if config is None:
            return None

        entry: dict[str, Any] = {
            "command": config["command"],
            "args": config.get("args", []),
        }
        if config.get("env"):
            entry["env"] = config["env"]

        return {"mcpServers": {server_name: entry}}

    # ------------------------------------------------------------------
    # LLM fallback
    # ------------------------------------------------------------------

    async def _llm_derive_install(self, server_name: str, readme: str) -> str:
        """Use LLM to derive install command from server name and README.

        Args:
            server_name: Server name.
            readme: README content (may be empty).

        Returns:
            Derived install command, or empty string.
        """
        if self.llm_callback:
            result = self.llm_callback(server_name, readme)
            if asyncio.iscoroutine(result):
                return await result
            return result

        # Try using langchain if available
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            try:
                from langchain_anthropic import ChatAnthropic as ChatOpenAI
            except ImportError:
                logger.debug("No LLM available for install command fallback")
                return ""

        prompt = f"""Given this MCP server, determine the single install/run command.

Server: {server_name}
Repository README (first 2000 chars):
{readme[:2000] if readme else '(no README available)'}

Rules:
- For npm packages: return "npx -y <package-name>"
- For Python packages: return "uvx <package-name>" or "pip install <package-name>"
- Return ONLY the command, nothing else. No explanation.
- If you cannot determine the command, return "UNKNOWN"
"""
        try:
            llm = ChatOpenAI(temperature=0)
            response = await llm.ainvoke(prompt)
            cmd = response.content.strip().strip("`").strip()
            if cmd and cmd != "UNKNOWN" and len(cmd) < 200:
                return cmd
        except Exception as e:
            logger.debug(f"LLM fallback failed: {e}")

        return ""
