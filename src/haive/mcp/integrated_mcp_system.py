#!/usr/bin/env python3
"""Integrated MCP Discovery & Management System.

A complete end-to-end solution that combines:
1. MCP server discovery with enhanced RAG search
2. One-click installation from discovery results
3. FastMCP server management (like Claude's 'claude mcp add')
4. Live server monitoring and access

This creates a seamless workflow from discovery to deployment.
"""

import asyncio
import json
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from csv_viewer import load_mcp_servers_data
from self_query_mcp_agent import SelfQueryMCPAgent

# Import our components


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServerInstallation:
    """Track server installation status."""

    server_name: str
    status: str  # pending, installing, installed, failed
    message: str
    installed_at: str | None = None
    install_command: str | None = None
    pid: int | None = None


class MCPServerInstaller:
    """Handles server installation and setup."""

    def __init__(self, manager_config_path: Path | None = None):
        self.manager_config_path = (
            manager_config_path or Path.home() / ".fastmcp" / "servers.json"
        )
        self.installations: dict[str, ServerInstallation] = {}

    async def detect_package_manager(
        self, server_data: dict[str, Any]
    ) -> tuple[str, str]:
        """Detect appropriate package manager and command."""
        language = server_data.get("language", "").lower()
        install_cmd = server_data.get("install_command", "")
        repo_url = server_data.get("repository_url", "")

        # Check for explicit install command
        if install_cmd:
            if "npm" in install_cmd:
                return "npm", install_cmd
            if "pip" in install_cmd:
                return "pip", install_cmd
            if "cargo" in install_cmd:
                return "cargo", install_cmd
            if "go" in install_cmd:
                return "go", install_cmd

        # Infer from language
        if language in ["javascript", "typescript", "nodejs", "js", "ts"]:
            # Check if it's an npx package
            if "@" in server_data.get("name", ""):
                return "npx", f"npx -y {server_data['name']}"
            return "npm", f"npm install -g {server_data['name']}"

        if language in ["python", "py"]:
            # Try to extract package name from repo
            if "github.com" in repo_url:
                return "pip", f"pip install git+{repo_url}"
            return "pip", f"pip install {server_data['name']}"

        if language == "rust":
            return "cargo", f"cargo install {server_data['name']}"

        if language == "go":
            return "go", f"go install {repo_url}"

        # Default to cloning if we have a repo URL
        if repo_url:
            return "git", f"git clone {repo_url}"

        return "unknown", ""

    async def install_server(self, server_data: dict[str, Any]) -> ServerInstallation:
        """Install an MCP server."""
        server_name = server_data.get("name", "unknown")

        try:
            # Detect package manager
            pkg_manager, install_cmd = await self.detect_package_manager(server_data)

            if pkg_manager == "unknown":
                return ServerInstallation(
                    server_name=server_name,
                    status="failed",
                    message="Could not determine installation method",
                )

            # Create installation record
            installation = ServerInstallation(
                server_name=server_name,
                status="installing",
                message=f"Installing via {pkg_manager}...",
                install_command=install_cmd,
            )
            self.installations[server_name] = installation

            # Execute installation
            logger.info(f"Installing {server_name}: {install_cmd}")

            if pkg_manager == "git":
                # Clone to a specific directory
                install_dir = Path.home() / ".mcp-servers" / server_name
                install_dir.parent.mkdir(parents=True, exist_ok=True)

                if install_dir.exists():
                    shutil.rmtree(install_dir)

                install_cmd = f"{install_cmd} {install_dir}"

            # Run installation command
            process = await asyncio.create_subprocess_shell(
                install_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                installation.status = "installed"
                installation.message = f"Successfully installed via {pkg_manager}"
                installation.installed_at = datetime.now().isoformat()

                # Add to FastMCP manager
                await self.add_to_fastmcp_manager(server_data, pkg_manager)

            else:
                installation.status = "failed"
                installation.message = f"Installation failed: {stderr.decode()}"

        except Exception as e:
            installation = ServerInstallation(
                server_name=server_name,
                status="failed",
                message=f"Installation error: {e!s}",
            )
            self.installations[server_name] = installation

        return installation

    async def add_to_fastmcp_manager(
        self, server_data: dict[str, Any], pkg_manager: str
    ):
        """Add installed server to FastMCP manager configuration."""
        # Load existing config
        servers = {}
        if self.manager_config_path.exists():
            with open(self.manager_config_path) as f:
                data = json.load(f)
                servers = data.get("servers", {})

        server_name = server_data.get("name", "unknown")

        # Create server configuration
        server_config = {
            "name": server_name,
            "transport": "stdio",  # Default to stdio
            "scope": "local",
            "active": True,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "metadata": {
                "installed_via": pkg_manager,
                "category": server_data.get("category", "unknown"),
                "language": server_data.get("language", "unknown"),
                "repository": server_data.get("repository_url", ""),
                "description": server_data.get("description", ""),
            },
        }

        # Determine command based on package manager and language
        if pkg_manager == "npx":
            server_config["command"] = "npx"
            server_config["args"] = ["-y", server_name]
        elif pkg_manager == "npm":
            # Try to find the installed command
            server_config["command"] = server_name
            server_config["args"] = []
        elif pkg_manager == "pip":
            # Python servers usually run as modules
            server_config["command"] = "python"
            server_config["args"] = ["-m", server_name.replace("-", "_")]
        elif pkg_manager == "git":
            # For git clones, look for common entry points
            install_dir = Path.home() / ".mcp-servers" / server_name
            if (install_dir / "server.py").exists():
                server_config["command"] = "python"
                server_config["args"] = [str(install_dir / "server.py")]
            elif (install_dir / "index.js").exists():
                server_config["command"] = "node"
                server_config["args"] = [str(install_dir / "index.js")]
            else:
                # Generic fallback
                server_config["command"] = str(install_dir / "run.sh")
                server_config["args"] = []

        # Add to servers config
        servers[server_name] = server_config

        # Save updated config
        self.manager_config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "servers": servers,
            "metadata": {
                "version": "1.0.0",
                "last_modified": datetime.now().isoformat(),
            },
        }

        with open(self.manager_config_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Added {server_name} to FastMCP manager")


class IntegratedMCPSystem:
    """Main integrated system combining discovery and management."""

    def __init__(self):
        self.discovery_agent = SelfQueryMCPAgent()
        self.installer = MCPServerInstaller()
        self.fastmcp_manager = None  # Will be initialized when needed
        self.servers_data = load_mcp_servers_data()

    async def search_servers(self, query: str, method: str = "auto") -> dict[str, Any]:
        """Search for MCP servers."""
        if method == "auto":
            method = self.discovery_agent.analyze_query_intent(query)

        if method == "self_query":
            docs = await self.discovery_agent.search_with_self_query(query)
        elif method == "parent_docs":
            docs = await self.discovery_agent.search_with_parent_retriever(query)
        else:
            docs = await self.discovery_agent.search_similarity(query)

        return {"method": method, "documents": docs}

    async def install_and_configure(self, server_name: str) -> ServerInstallation:
        """Install a server and configure it in FastMCP."""
        # Find server data
        server_data = None
        for server in self.servers_data:
            if server.get("name") == server_name:
                server_data = server
                break

        if not server_data:
            return ServerInstallation(
                server_name=server_name,
                status="failed",
                message="Server not found in database",
            )

        # Install the server
        installation = await self.installer.install_server(server_data)

        return installation

    def get_fastmcp_servers(self) -> dict[str, Any]:
        """Get all FastMCP managed servers."""
        if not self.installer.manager_config_path.exists():
            return {}

        with open(self.installer.manager_config_path) as f:
            data = json.load(f)
            return data.get("servers", {})

    async def start_server(self, server_name: str) -> dict[str, Any]:
        """Start a FastMCP server."""
        servers = self.get_fastmcp_servers()
        if server_name not in servers:
            return {"success": False, "error": f"Server {server_name} not found"}

        server_config = servers[server_name]

        try:
            # Build command
            cmd = [server_config["command"], *server_config.get("args", [])]

            # Start process
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            return {
                "success": True,
                "message": f"Started {server_name}",
                "pid": process.pid,
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to start server: {e!s}"}

    async def stop_server(self, server_name: str, pid: int) -> dict[str, Any]:
        """Stop a running server."""
        try:
            # Send terminate signal
            os.kill(pid, 15)  # SIGTERM
            return {"success": True, "message": f"Stopped {server_name}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to stop server: {e!s}"}


# Streamlit Web Interface
def create_web_interface():
    """Create the integrated web interface."""
    st.set_page_config(
        page_title="MCP Integrated System", page_icon="🚀", layout="wide"
    )

    # Initialize system
    if "system" not in st.session_state:
        with st.spinner("Initializing MCP system..."):
            st.session_state.system = IntegratedMCPSystem()

    if "running_servers" not in st.session_state:
        st.session_state.running_servers = {}

    system = st.session_state.system

    # Header
    st.title("🚀 MCP Integrated Discovery & Management")
    st.markdown("**End-to-end MCP server discovery, installation, and management**")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔍 Discover", "📦 Installed", "🎮 Running", "📊 Analytics"]
    )

    with tab1:
        show_discovery_tab(system)

    with tab2:
        show_installed_tab(system)

    with tab3:
        show_running_tab(system)

    with tab4:
        show_analytics_tab(system)


def show_discovery_tab(system):
    """Discovery and installation tab."""
    st.subheader("🔍 Discover MCP Servers")

    # Search interface
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "Search for MCP servers",
            placeholder="e.g., 'Python database servers with more than 5 stars'",
            help="Use natural language to search",
        )

    with col2:
        search_method = st.selectbox(
            "Method", ["auto", "self_query", "parent_docs", "similarity"]
        )

    if search_query:
        with st.spinner("Searching..."):
            results = asyncio.run(system.search_servers(search_query, search_method))

        st.write(
            f"**Found {len(results['documents'])} servers using {results['method']}**"
        )

        # Display results with install buttons
        for i, doc in enumerate(results["documents"]):
            metadata = doc.metadata
            server_name = metadata.get("server_name", "Unknown")

            with st.expander(
                f"**{server_name}** - {metadata.get('category', 'unknown')}"
            ):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**Language:** {metadata.get('language', 'unknown')}")
                    st.write(f"**Stars:** {metadata.get('stars', 0)} ⭐")
                    st.write(f"**Features:** {metadata.get('total_features', 0)}")

                with col2:
                    if metadata.get("repository_url"):
                        st.link_button("📂 Repository", metadata["repository_url"])

                with col3:
                    install_key = f"install_{server_name}_{i}"
                    if st.button("📦 Install", key=install_key, type="primary"):
                        with st.spinner(f"Installing {server_name}..."):
                            installation = asyncio.run(
                                system.install_and_configure(server_name)
                            )

                        if installation.status == "installed":
                            st.success(f"✅ {installation.message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {installation.message}")

                # Show description
                st.write("**Description:**")
                content = doc.page_content
                if len(content) > 500:
                    content = content[:500] + "..."
                st.text(content)


def show_installed_tab(system):
    """Show installed servers."""
    st.subheader("📦 Installed MCP Servers")

    servers = system.get_fastmcp_servers()

    if not servers:
        st.info(
            "No servers installed yet. Use the Discover tab to find and install servers."
        )
        return

    # Display as table
    server_data = []
    for name, config in servers.items():
        server_data.append(
            {
                "Name": name,
                "Transport": config.get("transport", "stdio"),
                "Command": config.get("command", "N/A"),
                "Status": "Active" if config.get("active", True) else "Inactive",
                "Installed": config.get("created", "Unknown")[:10],
                "Category": config.get("metadata", {}).get("category", "unknown"),
                "Language": config.get("metadata", {}).get("language", "unknown"),
            }
        )

    df = pd.DataFrame(server_data)

    # Add actions column
    selected = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    # Show selected server details
    if len(selected.selection.rows) > 0:
        idx = selected.selection.rows[0]
        server_name = df.iloc[idx]["Name"]
        server_config = servers[server_name]

        st.subheader(f"📋 Server: {server_name}")

        col1, col2 = st.columns(2)

        with col1:
            st.json(server_config)

        with col2:
            st.write("**Actions:**")

            # Start server button
            if st.button(f"▶️ Start {server_name}", key=f"start_{server_name}"):
                with st.spinner(f"Starting {server_name}..."):
                    result = asyncio.run(system.start_server(server_name))

                if result["success"]:
                    st.success(result["message"])
                    st.session_state.running_servers[server_name] = result["pid"]
                    st.rerun()
                else:
                    st.error(result["error"])

            # Remove server button
            if st.button(f"🗑️ Remove {server_name}", key=f"remove_{server_name}"):
                # Remove from config
                del servers[server_name]
                data = {
                    "servers": servers,
                    "metadata": {
                        "version": "1.0.0",
                        "last_modified": datetime.now().isoformat(),
                    },
                }
                with open(system.installer.manager_config_path, "w") as f:
                    json.dump(data, f, indent=2)

                st.success(f"Removed {server_name}")
                st.rerun()


def show_running_tab(system):
    """Show running servers."""
    st.subheader("🎮 Running MCP Servers")

    running = st.session_state.running_servers

    if not running:
        st.info("No servers currently running. Start servers from the Installed tab.")
        return

    # Display running servers
    for server_name, pid in list(running.items()):
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.write(f"**{server_name}** (PID: {pid})")

        with col2:
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Check if process exists
                st.success("🟢 Running")
            except:
                st.error("🔴 Stopped")
                del running[server_name]

        with col3:
            if st.button("⏹️ Stop", key=f"stop_{server_name}_{pid}"):
                result = asyncio.run(system.stop_server(server_name, pid))

                if result["success"]:
                    st.success(result["message"])
                    del running[server_name]
                    st.rerun()
                else:
                    st.error(result["error"])


def show_analytics_tab(system):
    """Show analytics and statistics."""
    st.subheader("📊 MCP System Analytics")

    # Get statistics
    servers = system.get_fastmcp_servers()
    running = st.session_state.running_servers
    all_servers = system.servers_data

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Available", len(all_servers))

    with col2:
        st.metric("Installed", len(servers))

    with col3:
        st.metric("Running", len(running))

    with col4:
        install_rate = (len(servers) / len(all_servers) * 100) if all_servers else 0
        st.metric("Install Rate", f"{install_rate:.1f}%")

    # Category breakdown of installed servers
    if servers:
        st.subheader("📊 Installed Servers by Category")

        categories = {}
        for server_config in servers.values():
            category = server_config.get("metadata", {}).get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1

        # Create bar chart

        df = pd.DataFrame(list(categories.items()), columns=["Category", "Count"])

        fig = px.bar(df, x="Category", y="Count", title="Installed Servers by Category")
        st.plotly_chart(fig, use_container_width=True)

    # Installation history
    if system.installer.installations:
        st.subheader("📜 Installation History")

        install_data = []
        for server_name, installation in system.installer.installations.items():
            install_data.append(
                {
                    "Server": server_name,
                    "Status": installation.status,
                    "Message": installation.message,
                    "Installed At": installation.installed_at or "N/A",
                    "Command": installation.install_command or "N/A",
                }
            )

        df = pd.DataFrame(install_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    create_web_interface()
