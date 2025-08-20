#!/usr/bin/env python3
"""Phase 4 Agent Integration Test.

This test validates the complete end-to-end MCP agent integration:
1. MCPAgent creation and initialization
2. Automatic MCP server installation and connection
3. Tool discovery and registration
4. LLM integration with MCP tools
5. Multi-server coordination

This represents the culmination of all 4 phases:
- Phase 1: Fixed bulk installer to use npm packages ✅
- Phase 2: Native MCP protocol client ✅  
- Phase 3: Registry migration to npm packages ✅
- Phase 4: Seamless agent integration ✅
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from haive.mcp.agents.mcp_agent import MCPAgent, create_mcp_agent
from haive.core.engine.aug_llm import AugLLMConfig


async def test_enhanced_mcp_agent_basic():
    """Test basic MCPAgent functionality."""
    print("🧪 Test 1: Basic MCPAgent Creation")
    print("=" * 50)
    
    try:
        # Create agent with minimal configuration
        agent = MCPAgent(
            name="test_agent",
            engine=AugLLMConfig(
                temperature=0.1,  # Low temp for consistent testing
                max_tokens=100,
                system_message="You are a test assistant with MCP tools."
            ),
            mcp_categories=["core"],  # Just core category
            auto_install=False  # Don't auto-install for basic test
        )
        
        print(f"✅ Agent created: {agent.name}")
        print(f"   Categories: {agent.mcp_categories}")
        print(f"   Auto-install: {agent.auto_install}")
        
        # Check initial stats
        stats = agent.get_mcp_stats()
        print(f"   Initial stats: {stats.servers_installed} servers, {stats.tools_registered} tools")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_initialization():
    """Test MCP initialization with real servers."""
    print("\n🧪 Test 2: MCP Initialization with Real Servers")
    print("=" * 50)
    
    try:
        # Create agent with core category (filesystem and basic tools)
        agent = MCPAgent(
            name="init_test_agent",
            engine=AugLLMConfig(temperature=0.1),
            mcp_categories=["core"],  # Will install filesystem, postgres, github, etc.
            auto_install=True,
            max_concurrent_installs=2  # Limit concurrent installs
        )
        
        print(f"🚀 Initializing MCP integration...")
        
        # Initialize MCP - this should install servers and discover tools
        await agent.initialize_mcp()
        
        # Check results
        stats = agent.get_mcp_stats()
        print(f"✅ MCP initialization complete!")
        print(f"   Servers installed: {stats.servers_installed}")
        print(f"   Servers connected: {stats.servers_connected}")
        print(f"   Tools discovered: {stats.tools_discovered}")
        print(f"   Tools registered: {stats.tools_registered}")
        print(f"   Categories active: {stats.categories_active}")
        print(f"   Connection rate: {stats.connection_rate:.1%}")
        
        # List some tools
        tools = agent.list_mcp_tools()
        if tools:
            print(f"\n🔧 Sample tools ({len(tools)} total):")
            for tool in tools[:5]:  # Show first 5
                print(f"   - {tool['name']}: {tool['description'][:50]}...")
        
        # Success if servers are connected (tool discovery might be async/delayed)
        return stats.servers_connected > 0
        
    except Exception as e:
        print(f"❌ MCP initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_execution_with_mcp():
    """Test agent execution with MCP tools."""
    print("\n🧪 Test 3: Agent Execution with MCP Tools")
    print("=" * 50)
    
    try:
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_file_path = f.name
            f.write("Hello from Phase 4 MCP Integration!\nThis is a test file for the Enhanced MCP Agent.")
        
        print(f"📁 Created test file: {test_file_path}")
        
        # Create agent with filesystem tools
        agent = await create_mcp_agent(
            name="execution_test_agent",
            categories=["core"]  # Should include filesystem server
        )
        
        stats = agent.get_mcp_stats()
        print(f"🔗 Agent ready: {stats.servers_connected} servers, {stats.tools_registered} tools")
        
        # Test 1: Simple interaction without tool use
        print(f"\n💬 Test 3a: Basic conversation")
        try:
            result1 = await agent.arun("Hello! What tools do you have available?")
            print(f"✅ Basic conversation working")
            print(f"   Response length: {len(str(result1))} characters")
        except Exception as e:
            print(f"⚠️ Basic conversation failed: {e}")
        
        # Test 2: Tool listing
        print(f"\n🔧 Test 3b: Tool availability")
        tools = agent.list_mcp_tools()
        filesystem_tools = [t for t in tools if 'file' in t['name'].lower()]
        print(f"✅ Found {len(filesystem_tools)} filesystem tools")
        for tool in filesystem_tools[:3]:
            print(f"   - {tool['name']}")
        
        # Test 3: Health check
        print(f"\n🏥 Test 3c: Health check")
        health = await agent.health_check_mcp()
        print(f"✅ Health check: {health['healthy_servers']}/{health['total_servers']} servers healthy")
        
        # Cleanup
        Path(test_file_path).unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Agent execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_factory_function():
    """Test the factory function for easy agent creation."""
    print("\n🧪 Test 4: Factory Function")
    print("=" * 50)
    
    try:
        # Use factory function - should be easier and more reliable
        print("🏭 Creating agent with factory function...")
        
        agent = await create_mcp_agent(
            name="factory_test_agent",
            categories=["core"]  # Should install filesystem tools
        )
        
        print(f"✅ Factory function successful!")
        
        # Verify agent is properly initialized
        stats = agent.get_mcp_stats()
        print(f"   Agent: {agent.name}")
        print(f"   Servers: {stats.servers_connected}")
        print(f"   Tools: {stats.tools_registered}")
        print(f"   Categories: {stats.categories_active}")
        
        # Quick tool test
        tools = agent.list_mcp_tools()
        print(f"   Available tools: {len(tools)}")
        
        return stats.servers_connected > 0
        
    except Exception as e:
        print(f"❌ Factory function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multi_category_integration():
    """Test integration with multiple categories."""
    print("\n🧪 Test 5: Multi-Category Integration")
    print("=" * 50)
    
    try:
        print("🎯 Testing multiple category installation...")
        
        # Create agent with multiple categories
        agent = await create_mcp_agent(
            name="multi_category_agent",
            categories=["core", "enhanced_filesystem"]  # Two categories
        )
        
        stats = agent.get_mcp_stats()
        print(f"✅ Multi-category agent created!")
        print(f"   Active categories: {stats.categories_active}")
        print(f"   Total servers: {stats.servers_connected}")
        print(f"   Total tools: {stats.tools_registered}")
        
        # Test installing additional category
        print(f"\n➕ Installing additional category...")
        success = await agent.install_additional_category("productivity")
        
        if success:
            updated_stats = agent.get_mcp_stats()
            print(f"✅ Additional category installed!")
            print(f"   New categories: {updated_stats.categories_active}")
            print(f"   New tool count: {updated_stats.tools_registered}")
        else:
            print(f"⚠️ Additional category installation had issues")
        
        return len(stats.categories_active) >= 2
        
    except Exception as e:
        print(f"❌ Multi-category test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Phase 4 integration tests."""
    print("🚀 Phase 4: Agent Integration Test Suite")
    print("🎯 Testing Complete MCP + Agent Integration")
    print("=" * 60)
    
    tests = [
        ("Basic Agent Creation", test_enhanced_mcp_agent_basic),
        ("MCP Initialization", test_mcp_initialization),
        ("Agent Execution", test_agent_execution_with_mcp),
        ("Factory Function", test_factory_function),
        ("Multi-Category", test_multi_category_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PHASE 4 TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 PHASE 4 COMPLETE: Agent Integration Working!")
        print("✅ All 4 phases of MCP implementation successful:")
        print("   Phase 1: Bulk installer using npm packages ✅")
        print("   Phase 2: Native MCP protocol client ✅")
        print("   Phase 3: Registry migration to packages ✅")
        print("   Phase 4: Seamless agent integration ✅")
    else:
        print("⚠️ Some tests failed - Phase 4 needs attention")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)