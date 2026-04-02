#!/usr/bin/env python3
"""Search and Install - Full installer pipeline with HITL approval.

Demonstrates the complete MCPInstallerService flow:
1. Search the 1,960 server database
2. Plan install (README extraction + LLM fallback)
3. HITL approval (interactive prompt)
4. Connect and verify tools
5. Export config in multiple formats

Usage:
    poetry run python examples/search_and_install.py
"""

import asyncio
import json

from haive.mcp.installer_service import MCPInstallerService


async def main():
    service = MCPInstallerService(require_approval=True)
    print(f"MCP Server Database: {service.server_count} servers\n")

    # Search
    query = "filesystem"
    results = service.search(query, limit=5)
    print(f"Search results for '{query}':")
    for i, r in enumerate(results[:5], 1):
        detail = service.get_detail(r["name"])
        cmd = (detail or {}).get("install_command", "")
        print(f"  {i}. {r['name']}")
        if cmd:
            print(f"     Install: {cmd}")
    print()

    # Plan install for top result
    plan = await service.plan_install(results[0]["name"])
    if plan is None:
        print("Could not create install plan.")
        return

    print(f"Install plan:")
    print(f"  Server:     {plan.server_name}")
    print(f"  Command:    {plan.install_command}")
    print(f"  Method:     {plan.method.value} (confidence {plan.confidence:.0%})")
    if plan.repository_url:
        print(f"  Repository: {plan.repository_url}")
    print()

    # HITL approval (will prompt on stdin)
    approved = await service.approve(plan)
    if not approved:
        print("Installation rejected.")
        return

    # Install and verify
    print(f"\nConnecting to {plan.server_name}...")
    result = await service.install(plan)

    if result.success:
        print(f"Success! {result.message}")
        if result.tools_discovered:
            print(f"\nDiscovered tools:")
            for tool in result.tools_discovered:
                print(f"  - {tool}")
    else:
        print(f"Failed: {result.message}")

    # Export configs
    print("\n--- langchain-mcp-adapters config ---")
    lc_cfg = service.generate_langchain_config(plan.server_name)
    print(json.dumps(lc_cfg, indent=2))

    print("\n--- Claude Desktop config ---")
    claude_cfg = service.generate_claude_desktop_config(plan.server_name)
    print(json.dumps(claude_cfg, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
