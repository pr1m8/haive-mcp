#!/usr/bin/env python3
"""CSV Viewer and Exporter for MCP Servers Data

Creates a browsable CSV export with sorting and filtering capabilities.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


def load_mcp_servers_data() -> list[dict[str, Any]]:
    """Load MCP servers data from JSON file."""
    data_path = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "mcp_servers"
        / "ALL_MCP_SERVERS_COMPLETE.json"
    )

    with open(data_path) as f:
        data = json.load(f)
        return data.get("all_servers", [])


def create_csv_export() -> pd.DataFrame:
    """Create pandas DataFrame for CSV export."""
    servers = load_mcp_servers_data()

    # Flatten the data for CSV
    flattened_data = []
    for server in servers:
        row = {
            "name": server.get("name", "Unknown"),
            "description": server.get("description", "No description"),
            "category": server.get("category", "general"),
            "language": server.get("language", "unknown"),
            "stars": server.get("stars", 0) or 0,
            "install_command": server.get("install_command", ""),
            "repository_url": server.get("repository_url", ""),
            "tools_count": len(server.get("tools", [])),
            "resources_count": len(server.get("resources", [])),
            "prompts_count": len(server.get("prompts", [])),
            "use_cases": server.get("use_cases", "General purpose"),
            "installation_notes": server.get(
                "installation_notes", "Standard installation"
            ),
            "tools": ", ".join(server.get("tools", [])),
            "resources": ", ".join(server.get("resources", [])),
            "prompts": ", ".join(server.get("prompts", [])),
            "has_install_command": bool(server.get("install_command")),
            "total_features": len(server.get("tools", []))
            + len(server.get("resources", []))
            + len(server.get("prompts", [])),
        }
        flattened_data.append(row)

    return pd.DataFrame(flattened_data)


def export_to_csv():
    """Export data to CSV file."""
    df = create_csv_export()
    output_path = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "mcp_servers"
        / f"mcp_servers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    df.to_csv(output_path, index=False)
    print(f"✅ Exported {len(df)} MCP servers to: {output_path}")
    return output_path


def streamlit_viewer():
    """Create Streamlit web interface for browsing MCP servers."""
    st.set_page_config(page_title="MCP Servers Browser", page_icon="🔍", layout="wide")

    st.title("🔍 MCP Servers Browser")
    st.write("Browse and filter Model Context Protocol servers")

    # Load data
    @st.cache_data
    def load_data():
        return create_csv_export()

    df = load_data()

    # Sidebar filters
    st.sidebar.header("🔧 Filters")

    # Category filter
    categories = ["All"] + sorted(df["category"].unique().tolist())
    selected_category = st.sidebar.selectbox("Category", categories)

    # Language filter
    languages = ["All"] + sorted(df["language"].unique().tolist())
    selected_language = st.sidebar.selectbox("Language", languages)

    # Stars filter
    min_stars = st.sidebar.number_input("Minimum Stars", min_value=0, value=0)

    # Features filter
    min_features = st.sidebar.number_input(
        "Minimum Total Features", min_value=0, value=0
    )

    # Has install command filter
    has_install = st.sidebar.checkbox("Has Install Command", value=False)

    # Apply filters
    filtered_df = df.copy()

    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]

    if selected_language != "All":
        filtered_df = filtered_df[filtered_df["language"] == selected_language]

    filtered_df = filtered_df[filtered_df["stars"] >= min_stars]
    filtered_df = filtered_df[filtered_df["total_features"] >= min_features]

    if has_install:
        filtered_df = filtered_df[filtered_df["has_install_command"] == True]

    # Sort options
    st.sidebar.header("📊 Sorting")
    sort_columns = [
        "stars",
        "total_features",
        "tools_count",
        "resources_count",
        "prompts_count",
        "name",
    ]
    sort_by = st.sidebar.selectbox("Sort by", sort_columns, index=0)
    sort_ascending = st.sidebar.checkbox("Ascending", value=False)

    filtered_df = filtered_df.sort_values(sort_by, ascending=sort_ascending)

    # Display stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Servers", len(df))
    with col2:
        st.metric("Filtered Results", len(filtered_df))
    with col3:
        st.metric("Categories", df["category"].nunique())
    with col4:
        st.metric("Languages", df["language"].nunique())

    # Search box
    search_term = st.text_input("🔍 Search servers (name, description, tools)")
    if search_term:
        mask = (
            filtered_df["name"].str.contains(search_term, case=False, na=False)
            | filtered_df["description"].str.contains(search_term, case=False, na=False)
            | filtered_df["tools"].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]

    # Display results
    st.write(f"📋 Showing {len(filtered_df)} servers")

    # Display table
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
        "has_install_command",
    ]

    st.dataframe(
        filtered_df[display_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            "repository_url": st.column_config.LinkColumn("Repository"),
            "stars": st.column_config.NumberColumn("⭐ Stars"),
            "total_features": st.column_config.NumberColumn("🔧 Features"),
            "tools_count": st.column_config.NumberColumn("🛠️ Tools"),
            "resources_count": st.column_config.NumberColumn("📚 Resources"),
            "prompts_count": st.column_config.NumberColumn("💬 Prompts"),
        },
    )

    # Export button
    if st.button("📥 Export to CSV"):
        output_path = export_to_csv()
        st.success(f"Exported to: {output_path}")

    # Category breakdown
    st.subheader("📊 Category Breakdown")
    category_counts = filtered_df["category"].value_counts()
    st.bar_chart(category_counts)

    # Top servers by stars
    if len(filtered_df) > 0:
        st.subheader("⭐ Top Servers by Stars")
        top_starred = filtered_df.nlargest(10, "stars")[
            ["name", "stars", "category", "total_features"]
        ]
        st.dataframe(top_starred, hide_index=True)


def main():
    """Main CLI interface."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--csv":
        # Export to CSV
        export_to_csv()
    elif len(sys.argv) > 1 and sys.argv[1] == "--web":
        # Launch Streamlit web interface
        import subprocess

        script_path = Path(__file__).absolute()
        subprocess.run(
            ["streamlit", "run", str(script_path), "--", "--streamlit"], check=False
        )
    elif len(sys.argv) > 1 and sys.argv[1] == "--streamlit":
        # Internal streamlit mode
        streamlit_viewer()
    else:
        print("MCP Servers CSV Viewer")
        print("Usage:")
        print("  poetry run python csv_viewer.py --csv    # Export to CSV")
        print("  poetry run python csv_viewer.py --web    # Launch web browser")

        # Show basic stats
        df = create_csv_export()
        print("\n📊 Dataset Stats:")
        print(f"  Total servers: {len(df)}")
        print(f"  Categories: {df['category'].nunique()}")
        print(f"  Languages: {df['language'].nunique()}")
        print(f"  Servers with stars: {(df['stars'] > 0).sum()}")
        print(f"  Servers with install commands: {df['has_install_command'].sum()}")

        print("\n🏆 Top categories:")
        print(df["category"].value_counts().head(10).to_string())


if __name__ == "__main__":
    main()
