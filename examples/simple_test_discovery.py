#!/usr/bin/env python3
"""Simple test of MCP discovery without complex imports."""

import json
from pathlib import Path

# Simple discovery test
current_dir = Path(__file__).parent
data_path = (
    current_dir.parent / "data" / "mcp_servers" / "ALL_MCP_SERVERS_COMPLETE.json"
)

if data_path.exists():

    with open(data_path) as f:
        data = json.load(f)
        servers = data.get("all_servers", [])

    # Search for calculator tools
    calculators = []
    for server in servers:
        name = (server.get("name") or "").lower()
        desc = (server.get("description") or "").lower()
        if "calculator" in name or "calculator" in desc:
            calculators.append(server)

    for _calc in calculators[:5]:
        pass

    # Search for database tools
    databases = []
    for server in servers:
        name = (server.get("name") or "").lower()
        desc = (server.get("description") or "").lower()
        cat = (server.get("category") or "").lower()
        if (
            "database" in name
            or "database" in desc
            or "sql" in name
            or "database" in cat
        ):
            databases.append(server)

    for _db in databases[:5]:
        pass

else:
    pass
