#!/usr/bin/env python3
import json
from pathlib import Path

# Load the JSON file
json_file = Path("agent_resources/mcp_servers/all_mcp_documents.json")
with open(json_file, 'r') as f:
    data = json.load(f)

print(f"Type of data: {type(data)}")
print(f"Number of items: {len(data)}")

if isinstance(data, list) and len(data) > 0:
    print(f"\nFirst item keys: {list(data[0].keys())}")
    print(f"\nFirst item structure:")
    first_item = data[0]
    
    # Print key info
    for key in first_item.keys():
        value = first_item[key]
        if isinstance(value, dict):
            print(f"  {key}: dict with keys {list(value.keys())[:5]}...")
        elif isinstance(value, list):
            print(f"  {key}: list with {len(value)} items")
        elif isinstance(value, str):
            print(f"  {key}: string (length {len(value)})")
        else:
            print(f"  {key}: {type(value)}")
    
    # Show example metadata
    if 'metadata' in first_item:
        print(f"\nExample metadata:")
        for k, v in list(first_item['metadata'].items())[:10]:
            print(f"  {k}: {v}")