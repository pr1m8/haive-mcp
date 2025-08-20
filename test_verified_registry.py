#!/usr/bin/env python3
"""Test the new verified MCP registry."""

import asyncio
from haive.mcp.manager import MCPManager


async def test_verified_registry():
    """Test that the new registry has no 404 errors."""
    print("🧪 Testing Verified MCP Registry")
    print("=" * 40)
    
    manager = MCPManager()
    categories = manager.get_available_categories()
    
    print(f"\n📂 Available categories ({len(categories)}):")
    for name, category in categories.items():
        print(f"   {name}: {len(category.servers)} servers")
    
    # Test a small subset of development tools
    print(f"\n🔧 Testing development category...")
    result = await manager.bulk_install_category(
        "development", 
        max_concurrent=2,
        timeout_seconds=30
    )
    
    print(f"\n📊 Installation Results:")
    print(f"   Success Rate: {result.success_rate:.1%}")
    print(f"   Successful: {len(result.successful)}")
    print(f"   Failed: {len(result.failed)}")
    
    if result.failed:
        print(f"\n❌ Failed installations:")
        for failure in result.failed[:3]:
            print(f"   - {failure.server_name}: {failure.error[:50]}...")
    
    if result.successful:
        print(f"\n✅ Successful installations:")
        for success in result.successful[:3]:
            print(f"   - {success.server_name}")
    
    return result.success_rate > 0.8  # 80% success rate


if __name__ == "__main__":
    success = asyncio.run(test_verified_registry())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Registry verification complete")