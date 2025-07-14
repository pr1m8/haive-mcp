#!/usr/bin/env python3
"""
Simple test of MCP discovery without complex imports
"""

import json
from pathlib import Path

# Simple discovery test
current_dir = Path(__file__).parent
data_path = current_dir.parent / "data" / "mcp_servers" / "ALL_MCP_SERVERS_COMPLETE.json"

if data_path.exists():
    print(f"✅ Found MCP data at: {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
        servers = data.get('all_servers', [])
        
    print(f"📊 Total servers: {len(servers)}")
    
    # Search for calculator tools
    print("\n🔍 Searching for calculator tools...")
    calculators = []
    for server in servers:
        name = (server.get('name') or '').lower()
        desc = (server.get('description') or '').lower()
        if 'calculator' in name or 'calculator' in desc:
            calculators.append(server)
    
    print(f"✅ Found {len(calculators)} calculator tools:")
    for calc in calculators[:5]:
        print(f"\n- {calc.get('name')}")
        print(f"  Stars: {calc.get('stars', 0)}")
        print(f"  Language: {calc.get('language', 'unknown')}")
        print(f"  Tools: {calc.get('tools', [])}")
        
    # Search for database tools
    print("\n\n🔍 Searching for database tools...")
    databases = []
    for server in servers:
        name = (server.get('name') or '').lower()
        desc = (server.get('description') or '').lower()
        cat = (server.get('category') or '').lower()
        if 'database' in name or 'database' in desc or 'sql' in name or 'database' in cat:
            databases.append(server)
    
    print(f"✅ Found {len(databases)} database tools:")
    for db in databases[:5]:
        print(f"\n- {db.get('name')}")
        print(f"  Stars: {db.get('stars', 0)}")
        print(f"  Category: {db.get('category', 'unknown')}")
        
    print("\n\n📝 Integration Example:")
    print("""
# After finding a tool, here's how to use it with a haive agent:

from haive.agents.simple import SimpleAgent
from haive.core.engine.aug_llm import AugLLMConfig
from langchain_core.tools import Tool

# Create a tool wrapper for the discovered MCP server
def calculator_tool(expression: str) -> str:
    # This would connect to the actual MCP server
    return f"Result of {expression} = [calculated]"

calc_tool = Tool(
    name="calculator",
    description="Perform calculations",
    func=calculator_tool
)

# Create agent with the tool
agent = SimpleAgent(
    name="math_agent",
    engine=AugLLMConfig(),
    tools=[calc_tool]
)

# Use the agent
result = await agent.arun("Calculate 25 * 4")
    """)
else:
    print(f"❌ MCP data not found at: {data_path}")