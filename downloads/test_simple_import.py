#!/usr/bin/env python
"""Simple import test to debug the import issue."""

import sys
from pathlib import Path

# Add the paths
mcp_src = Path(__file__).parent / "src"
dataflow_src = Path(__file__).parent.parent / "haive-dataflow" / "src"

sys.path.insert(0, str(mcp_src))
sys.path.insert(0, str(dataflow_src))

print(f"MCP src: {mcp_src} (exists: {mcp_src.exists()})")
print(f"Dataflow src: {dataflow_src} (exists: {dataflow_src.exists()})")

print(f"\nPython path:")
for i, path in enumerate(sys.path[:5]):  # Show first 5 paths
    print(f"  {i}: {path}")

# Check if haive namespace exists in MCP src
haive_mcp_ns = mcp_src / "haive" / "mcp"
print(f"\nMCP namespace check:")
print(f"  {haive_mcp_ns} exists: {haive_mcp_ns.exists()}")
if haive_mcp_ns.exists():
    print(f"  Contents: {list(haive_mcp_ns.iterdir())[:3]}")  # First 3 items

# Test 1: Import dataflow models directly
print("\n🧪 Test 1: Direct dataflow models import")
try:
    from haive.dataflow.platform.models import BasePlatform, MCPPlatform, PluginPlatform
    print("✅ Successfully imported platform models")
    
    # Test creation
    platform = BasePlatform(
        platform_id="test",
        platform_name="Test",
        description="Test platform"
    )
    print(f"✅ Created BasePlatform: {platform.platform_id}")
    
except Exception as e:
    print(f"❌ Failed to import dataflow models: {e}")
    exit(1)

# Test 2: Import our plugin directly using importlib
print("\n🧪 Test 2: Direct plugin import using importlib")
try:
    import importlib.util
    
    # Import the browser plugin module directly
    plugin_path = mcp_src / "haive" / "mcp" / "plugins" / "browser_plugin.py"
    spec = importlib.util.spec_from_file_location("browser_plugin", plugin_path)
    browser_plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(browser_plugin_module)
    
    MCPBrowserPlugin = browser_plugin_module.MCPBrowserPlugin
    print("✅ Successfully imported MCPBrowserPlugin using importlib")
    
    # Test creation
    plugin = MCPBrowserPlugin()
    print(f"✅ Created plugin: {plugin.platform_name}")
    
except Exception as e:
    print(f"❌ Failed to import plugin: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Test inheritance
print("\n🧪 Test 3: Test inheritance")
try:
    assert isinstance(plugin, PluginPlatform)
    assert isinstance(plugin, BasePlatform)
    print("✅ Inheritance working correctly")
    
except Exception as e:
    print(f"❌ Inheritance test failed: {e}")
    exit(1)

print("\n🎉 All tests passed! The plugin is working correctly.")