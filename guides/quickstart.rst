Quick Start Guide
================

This guide will get you up and running with Haive MCP integration in 5 minutes.

**Haive MCP** provides seamless integration with 1900+ MCP servers, enabling dynamic tool discovery and runtime agent enhancement.

Installation
------------

Install the haive-mcp package:

.. code-block:: bash

   poetry add haive-mcp
   # or
   pip install haive-mcp

Basic Usage
-----------

Creating Your First MCP-Enhanced Agent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   from haive.mcp.agents.enhanced_mcp_agent import EnhancedMCPAgent
   from haive.core.engine.aug_llm import AugLLMConfig

   # Create MCP-enhanced agent
   agent = EnhancedMCPAgent(
       name="my_mcp_agent",
       engine=AugLLMConfig(temperature=0.7),
       mcp_categories=["core"],  # Install filesystem, postgres, github tools
       auto_install=True
   )

   print(f"Created agent: {agent.name}")
   print(f"Categories: {agent.mcp_categories}")
   print(f"Auto-install enabled: {agent.auto_install}")

Initializing MCP Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def initialize_agent():
       # Initialize MCP integration (installs servers and discovers tools)
       await agent.initialize_mcp()
       
       # Get integration statistics
       stats = agent.get_mcp_stats()
       print(f"Servers connected: {stats.servers_connected}")
       print(f"Tools discovered: {stats.tools_registered}")
       print(f"Categories active: {stats.categories_active}")
       
       # List available tools
       tools = agent.list_mcp_tools()
       print(f"\nDiscovered {len(tools)} MCP tools:")
       for tool in tools[:5]:  # Show first 5
           print(f"- {tool['name']}: {tool['description'][:50]}...")

   # Run initialization
   asyncio.run(initialize_agent())

Working with Available Categories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Check available server categories
   manager = agent.mcp_manager
   categories = manager.get_available_categories()
   
   print("Available MCP server categories:")
   for name, category in categories.items():
       print(f"- {name}: {len(category.servers)} servers")
       
   # Available categories:
   # - core: filesystem, postgres, github, puppeteer, brave-search
   # - ai_enhanced: sequential-thinking, memory
   # - time_utilities: time tools
   # - crypto_finance: crypto pricing tools
   # - enhanced_filesystem: filenexus, vuln-fs
   # - browser_automation: puppeteer variants
   # - github_enhanced: github code fetching
   # - notifications: ntfy-me self-hosted notifications

Using the Agent with Real Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def use_mcp_agent():
       # Create agent with filesystem and web search tools
       agent = EnhancedMCPAgent(
           name="task_agent",
           engine=AugLLMConfig(temperature=0.7),
           mcp_categories=["core", "enhanced_filesystem"],
           auto_install=True
       )
       
       # Initialize MCP integration
       await agent.initialize_mcp()
       
       # Use the agent for tasks (filesystem tools will be auto-discovered)
       result = await agent.arun(
           "Please list the files in the current directory and read any README files"
       )
       
       print(f"Agent response: {result}")
       
       # Check health and statistics
       health = await agent.health_check_mcp()
       print(f"MCP health: {health}")

   asyncio.run(use_mcp_agent())

Factory Function for Quick Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.agents.enhanced_mcp_agent import create_enhanced_mcp_agent

   async def quick_setup():
       # Quick factory function setup
       agent = await create_enhanced_mcp_agent(
           name="quick_agent",
           categories=["core"]  # Will auto-install and initialize
       )
       
       stats = agent.get_mcp_stats()
       print(f"Ready! {stats.servers_connected} servers, {stats.tools_registered} tools")
       
       return agent

   # Use the agent immediately
   agent = asyncio.run(quick_setup())

Working with MCP Manager Directly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from haive.mcp.manager import MCPManager
   from haive.mcp.config import MCPServerConfig, MCPTransport

   async def direct_manager_usage():
       # Create MCP manager directly
       manager = MCPManager()
       
       # Add a specific server manually
       fs_config = MCPServerConfig(
           name="filesystem",
           transport=MCPTransport.STDIO,
           command="npx",
           args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
       )
       
       result = await manager.add_server("filesystem", fs_config)
       print(f"Server added: {result.success}")
       
       # Get all tools from connected servers
       tools = await manager.get_all_tools()
       print(f"Available tools: {len(tools)}")
       
       # Bulk install from category
       bulk_result = await manager.bulk_install_category("core", max_concurrent=3)
       print(f"Bulk install success rate: {bulk_result.success_rate:.1%}")

   asyncio.run(direct_manager_usage())

Checking Server Status
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def check_status():
       agent = EnhancedMCPAgent(
           name="status_agent",
           engine=AugLLMConfig(),
           mcp_categories=["core"],
           auto_install=True
       )
       
       await agent.initialize_mcp()
       
       # Get detailed status
       status = await agent.mcp_manager.get_all_server_status()
       for server_name, server_status in status.items():
           print(f"{server_name}: {server_status}")
       
       # Health check all servers
       health_results = await agent.mcp_manager.bulk_health_check()
       print(f"Healthy servers: {len([r for r in health_results if r.is_healthy])}")

   asyncio.run(check_status())

Real-World Example
------------------

Complete file analysis and web search workflow:

.. code-block:: python

   import asyncio
   from haive.mcp.agents.enhanced_mcp_agent import EnhancedMCPAgent
   from haive.core.engine.aug_llm import AugLLMConfig

   async def analyze_project_files():
       """Real-world example: Analyze project files and research topics."""
       
       # Create agent with filesystem and web search capabilities
       agent = EnhancedMCPAgent(
           name="project_analyzer",
           engine=AugLLMConfig(
               temperature=0.7,
               model="gpt-4"
           ),
           mcp_categories=["core", "enhanced_filesystem"],  # filesystem + brave search
           auto_install=True
       )
       
       # Initialize MCP integration
       print("🔄 Initializing MCP servers...")
       await agent.initialize_mcp()
       
       # Get MCP statistics
       stats = agent.get_mcp_stats()
       print(f"✅ Ready! {stats.servers_connected} servers, {stats.tools_registered} tools")
       
       # Task 1: Analyze project structure
       print("\n📁 Analyzing project structure...")
       structure_result = await agent.arun(
           "Please analyze the current directory structure and identify the main components. "
           "Look for README files, configuration files, and source code directories."
       )
       print(f"Structure Analysis: {structure_result[:200]}...")
       
       # Task 2: Research related technologies
       print("\n🔍 Researching related technologies...")
       research_result = await agent.arun(
           "Based on the project files you found, research the latest best practices "
           "for the main technologies used. Provide a summary of current trends."
       )
       print(f"Research Results: {research_result[:200]}...")
       
       # Get final health check
       health = await agent.health_check_mcp()
       print(f"\n💚 MCP Health: {health}")
       
       return {
           "structure_analysis": structure_result,
           "research_results": research_result,
           "mcp_stats": stats
       }

   if __name__ == "__main__":
       results = asyncio.run(analyze_project_files())

Expected Output
~~~~~~~~~~~~~~~

.. code-block:: text

   🔄 Initializing MCP servers...
   ✅ Ready! 4 servers, 12 tools

   📁 Analyzing project structure...
   Structure Analysis: I can see this is a Python project with the following structure:
   - pyproject.toml: Poetry-based dependency management
   - src/haive/: Main source code directory
   - tests/: Test files...

   🔍 Researching related technologies...
   Research Results: Based on the Python files and dependencies I found, here are the current best practices:
   1. Poetry for dependency management is excellent
   2. Pydantic v2 for data validation is the current standard...

   💚 MCP Health: {'filesystem': 'healthy', 'brave_search': 'healthy', 'postgres': 'healthy'}

Testing Your Setup
------------------

Quick validation test:

.. code-block:: python

   import asyncio
   from haive.mcp.agents.enhanced_mcp_agent import EnhancedMCPAgent
   from haive.core.engine.aug_llm import AugLLMConfig

   async def test_basic_setup():
       """Test basic MCP setup works"""
       # Create agent with minimal configuration
       agent = EnhancedMCPAgent(
           name="test_agent",
           engine=AugLLMConfig(temperature=0.1),  # Low temp for consistent testing
           mcp_categories=["core"],  # Just core servers for testing
           auto_install=True
       )
       
       # Test initialization
       await agent.initialize_mcp()
       
       # Verify setup
       stats = agent.get_mcp_stats()
       assert stats.servers_connected > 0, "No servers connected"
       assert stats.tools_registered > 0, "No tools registered"
       
       # Test basic execution
       result = await agent.arun("Say hello and list your available tools")
       assert result, "Agent returned no result"
       assert len(str(result)) > 10, "Agent response too short"
       
       # Health check
       health = await agent.health_check_mcp()
       assert health, "Health check failed"
       
       print("✅ All tests passed!")
       return True

   # Run test
   if asyncio.run(test_basic_setup()):
       print("🎉 MCP setup is working correctly!")

Common Issues
-------------

**ImportError: No module named 'haive.mcp'**

.. code-block:: bash

   # Ensure package is installed with all dependencies
   poetry install
   # or
   pip install -e .

**MCP Server Installation Failures**

.. code-block:: bash

   # Check npm/npx is available
   which npx
   
   # Update npm if needed
   npm install -g npm@latest
   
   # Test manual server installation
   npx -y @modelcontextprotocol/server-filesystem /tmp

**Agent Initialization Timeouts**

.. code-block:: python

   # Increase timeout for slow networks
   agent = EnhancedMCPAgent(
       name="patient_agent",
       engine=AugLLMConfig(),
       mcp_categories=["core"],
       auto_install=True,
       initialization_timeout=120  # 2 minutes instead of default 30s
   )

**No Tools Discovered**

.. code-block:: python

   # Debug tool discovery
   manager = agent.mcp_manager
   status = await manager.get_all_server_status()
   
   for server_name, server_status in status.items():
       print(f"{server_name}: {server_status}")
       if server_status == "failed":
           # Check server logs
           logs = await manager.get_server_logs(server_name)
           print(f"Logs: {logs}")

**Permission Errors**

.. code-block:: bash

   # Ensure correct permissions for MCP server directories
   chmod +x ~/.local/bin/npx  # If using local npm
   
   # Or use global npm installation
   sudo npm install -g @modelcontextprotocol/server-filesystem

Next Steps
----------

1. :doc:`advanced-usage` - Advanced MCP patterns and workflows
2. :doc:`server-development` - Creating custom MCP servers
3. :doc:`agent-integration` - Integrating MCP with existing agents
4. :doc:`performance-tuning` - Optimizing MCP performance

.. note::
   Haive MCP uses real-time server discovery and installation. All examples use actual 
   MCP servers, not mocks or simulations, ensuring your development matches production behavior.