#!/usr/bin/env python3
"""Comprehensive MCP Discovery Web Interface.

Combines all features:
- CSV data browsing with sorting/filtering
- Self-query RAG search with metadata filtering
- Parent document retrieval for full content
- Enhanced data viewing with README content
"""

import asyncio
import json
from datetime import datetime
from typing import Any

import plotly.express as px
import streamlit as st

from haive.mcp.csv_viewer import create_csv_export, load_mcp_servers_data
from haive.mcp.self_query_mcp_agent import SelfQueryMCPAgent

# Import our custom components


st.set_page_config(
    page_title="MCP Discovery Hub",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "search_agent" not in st.session_state:
    with st.spinner("🚀 Initializing search agents..."):
        st.session_state.search_agent = SelfQueryMCPAgent()

if "servers_data" not in st.session_state:
    st.session_state.servers_data = load_mcp_servers_data()

if "df" not in st.session_state:
    st.session_state.df = create_csv_export()


# Main app
def main():
    """Main.
"""
    st.title("🔍 MCP Discovery Hub")
    st.markdown("**Comprehensive Model Context Protocol Server Discovery & Analysis**")

    # Sidebar navigation
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        [
            "🏠 Dashboard",
            "🔍 Advanced Search",
            "📊 Data Browser",
            "📚 Server Details",
            "📈 Analytics",
            "⚙️ Tools",
        ],
    )

    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🔍 Advanced Search":
        show_advanced_search()
    elif page == "📊 Data Browser":
        show_data_browser()
    elif page == "📚 Server Details":
        show_server_details()
    elif page == "📈 Analytics":
        show_analytics()
    elif page == "⚙️ Tools":
        show_tools()


def show_dashboard():
    """Main dashboard with overview and quick search."""
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    df = st.session_state.df

    with col1:
        st.metric(
            "Total Servers", len(df), help="Total number of MCP servers in database"
        )

    with col2:
        starred_count = (df["stars"] > 0).sum()
        st.metric(
            "With GitHub Stars", starred_count, f"{starred_count / len(df) * 100:.1f}%"
        )

    with col3:
        categories = df["category"].nunique()
        st.metric("Categories", categories, help="Number of unique server categories")

    with col4:
        with_features = (df["total_features"] > 0).sum()
        st.metric(
            "With Features", with_features, f"{with_features / len(df) * 100:.1f}%"
        )

    # Quick search
    st.subheader("🚀 Quick Search")

    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "Search MCP servers",
            placeholder="e.g., 'Python database servers with more than 5 stars'",
            help="Use natural language! Try: 'JavaScript web servers', 'Database tools with high stars', etc.",
        )

    with col2:
        search_method = st.selectbox(
            "Search Method",
            ["Auto", "Self-Query", "Parent Docs", "Similarity"],
            help="Auto: Let the system choose the best method",
        )

    if search_query:
        with st.spinner("🔍 Searching..."):
            results = search_servers(search_query, search_method)
            display_search_results(results, search_query)

    # Top categories
    st.subheader("📊 Popular Categories")

    category_counts = df["category"].value_counts().head(8)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            x=category_counts.values,
            y=category_counts.index,
            orientation="h",
            title="Servers by Category",
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top starred servers
        top_starred = df.nlargest(5, "stars")[["name", "stars", "category"]]
        st.write("⭐ **Top Starred Servers**")
        for _, row in top_starred.iterrows():
            st.write(f"**{row['name']}** ({row['category']}) - {row['stars']} ⭐")


def show_advanced_search():
    """Advanced search with all retrieval methods."""
    st.subheader("🔍 Advanced Search & Retrieval")
    st.write("Compare different search methodologies for finding MCP servers")

    # Search input
    search_query = st.text_area(
        "Search Query",
        placeholder="Examples:\n- Python database servers with more than 10 stars\n- How to install SQLite MCP servers\n- JavaScript web frameworks with resources",
        height=100,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        max_results = st.slider("Max Results", 1, 20, 5)

    with col2:
        search_methods = st.multiselect(
            "Search Methods",
            ["Self-Query", "Parent Docs", "Similarity", "All"],
            default=["All"],
        )

    with col3:
        if st.button("🚀 Search", type="primary") and search_query:
            perform_advanced_search(search_query, search_methods, max_results)


def perform_advanced_search(query: str, methods: list[str], max_results: int):
    """Perform advanced search with multiple methods."""
    if "All" in methods:
        methods = ["Self-Query", "Parent Docs", "Similarity"]

    with st.spinner("🔍 Performing advanced search..."):
        agent = st.session_state.search_agent

        # Perform searches
        results = {}

        if "Self-Query" in methods:
            try:
                results["self_query"] = asyncio.run(
                    agent.search_with_self_query(query, max_results)
                )
            except Exception as e:
                st.error(f"Self-Query error: {e}")
                results["self_query"] = []

        if "Parent Docs" in methods:
            try:
                results["parent_docs"] = asyncio.run(
                    agent.search_with_parent_retriever(query, max_results)
                )
            except Exception as e:
                st.error(f"Parent Docs error: {e}")
                results["parent_docs"] = []

        if "Similarity" in methods:
            try:
                results["similarity"] = asyncio.run(
                    agent.search_similarity(query, max_results)
                )
            except Exception as e:
                st.error(f"Similarity error: {e}")
                results["similarity"] = []

    # Display results in tabs
    if results:
        tabs = st.tabs([f"📊 {method.replace('_', ' ').title()}" for method in results])

        for tab, (method, docs) in zip(tabs, results.items(), strict=False):
            with tab:
                st.write(f"**{len(docs)} results found**")

                for i, doc in enumerate(docs, 1):
                    with st.expander(
                        f"{i}. {doc.metadata.get('server_name', 'Unknown Server')}"
                    ):
                        # Metadata
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(
                                f"**Category:** {doc.metadata.get('category', 'unknown')}"
                            )
                            st.write(
                                f"**Language:** {doc.metadata.get('language', 'unknown')}"
                            )
                        with col2:
                            st.write(f"**Stars:** {doc.metadata.get('stars', 0)} ⭐")
                            st.write(
                                f"**Features:** {doc.metadata.get('total_features', 0)}"
                            )
                        with col3:
                            if doc.metadata.get("repository_url"):
                                st.link_button(
                                    "📂 Repository", doc.metadata["repository_url"]
                                )

                        # Content
                        st.write("**Content:**")
                        if method == "parent_docs" and len(doc.page_content) > 1000:
                            # Show truncated for parent docs
                            content_preview = (
                                doc.page_content[:500]
                                + "\n\n... [Content truncated] ..."
                            )
                            st.text_area(
                                "Document Content",
                                content_preview,
                                height=200,
                                key=f"{method}_{i}_content",
                            )

                            if st.button("Show Full Content", key=f"{method}_{i}_full"):
                                st.text_area(
                                    "Full Content",
                                    doc.page_content,
                                    height=400,
                                    key=f"{method}_{i}_full_content",
                                )
                        else:
                            st.text_area(
                                "Document Content",
                                doc.page_content,
                                height=200,
                                key=f"{method}_{i}_short",
                            )


def show_data_browser():
    """Enhanced data browser with filtering and sorting."""
    st.subheader("📊 MCP Servers Data Browser")

    df = st.session_state.df

    # Filters
    with st.expander("🔧 Filters & Sorting", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            categories = ["All", *sorted(df["category"].unique().tolist())]
            selected_category = st.selectbox("Category", categories)

        with col2:
            languages = ["All", *sorted(df["language"].unique().tolist())]
            selected_language = st.selectbox("Language", languages)

        with col3:
            min_stars = st.number_input("Min Stars", min_value=0, value=0)
            min_features = st.number_input("Min Features", min_value=0, value=0)

        with col4:
            has_install = st.checkbox("Has Install Command")

            sort_by = st.selectbox(
                "Sort By", ["stars", "total_features", "tools_count", "name"]
            )
            sort_desc = st.checkbox("Descending", value=True)

    # Apply filters
    filtered_df = df.copy()

    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]

    if selected_language != "All":
        filtered_df = filtered_df[filtered_df["language"] == selected_language]

    filtered_df = filtered_df[filtered_df["stars"] >= min_stars]
    filtered_df = filtered_df[filtered_df["total_features"] >= min_features]

    if has_install:
        filtered_df = filtered_df[filtered_df["has_install_command"]]

    # Sort
    filtered_df = filtered_df.sort_values(sort_by, ascending=not sort_desc)

    # Search within filtered results
    search_term = st.text_input("🔍 Search within results")
    if search_term:
        mask = (
            filtered_df["name"].str.contains(search_term, case=False, na=False)
            | filtered_df["description"].str.contains(search_term, case=False, na=False)
            | filtered_df["tools"].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]

    # Display results
    st.write(f"📋 Showing {len(filtered_df)} of {len(df)} servers")

    # Enhanced table display
    display_columns = [
        "name",
        "description",
        "category",
        "language",
        "stars",
        "total_features",
        "tools_count",
        "resources_count",
        "prompts_count",
        "repository_url",
    ]

    # Make table interactive
    event = st.dataframe(
        filtered_df[display_columns],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "repository_url": st.column_config.LinkColumn("Repository"),
            "stars": st.column_config.NumberColumn("⭐ Stars"),
            "total_features": st.column_config.NumberColumn("🔧 Features"),
            "tools_count": st.column_config.NumberColumn("🛠️ Tools"),
            "resources_count": st.column_config.NumberColumn("📚 Resources"),
            "prompts_count": st.column_config.NumberColumn("💬 Prompts"),
        },
    )

    # Show selected server details
    if len(event.selection.rows) > 0:  # type: ignore
        selected_idx = event.selection.rows[0]  # type: ignore
        selected_server = filtered_df.iloc[selected_idx]

        st.subheader(f"📋 Details: {selected_server['name']}")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Basic Info:**")
            st.write(f"- **Description:** {selected_server['description']}")
            st.write(f"- **Category:** {selected_server['category']}")
            st.write(f"- **Language:** {selected_server['language']}")
            st.write(f"- **Stars:** {selected_server['stars']} ⭐")

        with col2:
            st.write("**Features:**")
            st.write(f"- **Tools:** {selected_server['tools_count']}")
            st.write(f"- **Resources:** {selected_server['resources_count']}")
            st.write(f"- **Prompts:** {selected_server['prompts_count']}")
            st.write(
                f"- **Install Command:** {'Yes' if selected_server['has_install_command'] else 'No'}"
            )

        if selected_server["tools"]:
            st.write("**Available Tools:**")
            st.write(selected_server["tools"])


def show_server_details():
    """Detailed server information with enhanced data."""
    st.subheader("📚 Server Details & Documentation")

    # Server selector
    servers = st.session_state.servers_data
    server_names = [
        f"{s.get('name', 'Unknown')} ({s.get('category', 'unknown')})" for s in servers
    ]

    selected_name = st.selectbox("Select Server", server_names)

    if selected_name:
        # Find selected server
        server_idx = server_names.index(selected_name)
        server = servers[server_idx]

        # Display comprehensive details
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write(f"# {server.get('name', 'Unknown Server')}")
            st.write(server.get("description", "No description available"))

            if server.get("repository_url"):
                st.link_button("📂 Repository", server["repository_url"])

        with col2:
            st.metric("⭐ Stars", server.get("stars", 0))
            st.metric(
                "🔧 Total Features",
                len(server.get("tools", []))
                + len(server.get("resources", []))
                + len(server.get("prompts", [])),
            )

        # Tabs for different information
        tabs = st.tabs(
            ["📋 Overview", "🛠️ Tools", "📚 Resources", "💬 Prompts", "⚙️ Installation"]
        )

        with tabs[0]:  # Overview
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Server Information:**")
                st.write(f"- **Category:** {server.get('category', 'unknown')}")
                st.write(f"- **Language:** {server.get('language', 'unknown')}")
                st.write(
                    f"- **Repository:** {server.get('repository_url', 'Not provided')}"
                )

            with col2:
                st.write("**Feature Counts:**")
                st.write(f"- **Tools:** {len(server.get('tools', []))}")
                st.write(f"- **Resources:** {len(server.get('resources', []))}")
                st.write(f"- **Prompts:** {len(server.get('prompts', []))}")

        with tabs[1]:  # Tools
            tools = server.get("tools", [])
            if tools:
                st.write(f"**{len(tools)} Available Tools:**")
                for tool in tools:
                    st.write(f"- {tool}")
            else:
                st.info("No tools available for this server")

        with tabs[2]:  # Resources
            resources = server.get("resources", [])
            if resources:
                st.write(f"**{len(resources)} Available Resources:**")
                for resource in resources:
                    st.write(f"- {resource}")
            else:
                st.info("No resources available for this server")

        with tabs[3]:  # Prompts
            prompts = server.get("prompts", [])
            if prompts:
                st.write(f"**{len(prompts)} Available Prompts:**")
                for prompt in prompts:
                    st.write(f"- {prompt}")
            else:
                st.info("No prompts available for this server")

        with tabs[4]:  # Installation
            install_cmd = server.get("install_command", "")
            if install_cmd:
                st.write("**Installation Command:**")
                st.code(install_cmd, language="bash")

            install_notes = server.get("installation_notes", "")
            if install_notes:
                st.write("**Installation Notes:**")
                st.write(install_notes)

            if not install_cmd and not install_notes:
                st.info("No installation instructions available")


def show_analytics():
    """Analytics and visualizations."""
    st.subheader("📈 MCP Servers Analytics")

    df = st.session_state.df

    # Key insights
    col1, col2, col3 = st.columns(3)

    with col1:
        avg_stars = df[df["stars"] > 0]["stars"].mean()
        st.metric("Avg Stars (starred repos)", f"{avg_stars:.1f}")

    with col2:
        avg_features = df["total_features"].mean()
        st.metric("Avg Features per Server", f"{avg_features:.1f}")

    with col3:
        python_servers = (df["language"] == "python").sum()
        st.metric(
            "Python Servers",
            f"{python_servers} ({python_servers / len(df) * 100:.1f}%)",
        )

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        # Stars distribution
        fig = px.histogram(
            df[df["stars"] > 0],
            x="stars",
            title="Distribution of GitHub Stars",
            nbins=20,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Language distribution
        lang_counts = df["language"].value_counts().head(10)
        fig = px.pie(
            values=lang_counts.values,
            names=lang_counts.index,
            title="Programming Languages",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Features vs Stars scatter
        fig = px.scatter(
            df[df["stars"] > 0],
            x="total_features",
            y="stars",
            color="category",
            title="Features vs GitHub Stars",
            hover_data=["name"],
        )
        st.plotly_chart(fig, use_container_width=True)

        # Category vs Features
        category_features = (
            df.groupby("category")["total_features"]
            .mean()
            .sort_values(ascending=False)
            .head(10)
        )
        fig = px.bar(
            x=category_features.values,
            y=category_features.index,
            orientation="h",
            title="Average Features by Category",
        )
        st.plotly_chart(fig, use_container_width=True)


def show_tools():
    """Tools and utilities."""
    st.subheader("⚙️ Tools & Utilities")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Export Tools:**")

        if st.button("📥 Export to CSV"):
            df = st.session_state.df
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"mcp_servers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

        if st.button("📄 Export to JSON"):
            servers = st.session_state.servers_data
            json_data = json.dumps(servers, indent=2)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_data,
                file_name=f"mcp_servers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

    with col2:
        st.write("**Search Tools:**")

        if st.button("🔄 Refresh Search Index"):
            with st.spinner("Rebuilding search index..."):
                # Reinitialize search agent
                st.session_state.search_agent = SelfQueryMCPAgent()
            st.success("Search index refreshed!")

        st.write("**Data Tools:**")
        st.info("Data enhancement tools will be available in the next version")


def search_servers(query: str, method: str) -> dict[str, Any]:
    """Perform search based on selected method."""
    agent = st.session_state.search_agent

    if method == "Auto":
        # Auto-select method based on query
        method = agent.analyze_query_intent(query)

    try:
        if method.lower() == "self-query":
            docs = asyncio.run(agent.search_with_self_query(query, 5))
            return {"method": "Self-Query", "docs": docs}

        if method.lower() == "parent docs":
            docs = asyncio.run(agent.search_with_parent_retriever(query, 5))
            return {"method": "Parent Documents", "docs": docs}

        # Similarity
        docs = asyncio.run(agent.search_similarity(query, 5))
        return {"method": "Similarity", "docs": docs}

    except Exception as e:
        st.error(f"Search error: {e}")
        return {"method": "Error", "docs": []}


def display_search_results(results: dict[str, Any], query: str):
    """Display search results."""
    if not results.get("docs"):
        st.info("No results found")
        return

    st.write(f"**{len(results['docs'])} results found using {results['method']}**")

    for i, doc in enumerate(results["docs"], 1):
        with st.expander(f"{i}. {doc.metadata.get('server_name', 'Unknown')}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Category:** {doc.metadata.get('category', 'unknown')}")
                st.write(f"**Language:** {doc.metadata.get('language', 'unknown')}")

            with col2:
                st.write(f"**Stars:** {doc.metadata.get('stars', 0)} ⭐")
                st.write(f"**Features:** {doc.metadata.get('total_features', 0)}")

            with col3:
                if doc.metadata.get("repository_url"):
                    st.link_button("Repository", doc.metadata["repository_url"])

            # Content preview
            content = doc.page_content
            if len(content) > 300:
                content = content[:300] + "..."

            st.text_area("Description", content, height=100, key=f"result_{i}")


if __name__ == "__main__":
    main()
