Examples
========

Comprehensive examples demonstrating haive-mcp capabilities with 1900+ MCP servers.

Example Scripts
---------------

Our examples directory contains working scripts that demonstrate various MCP integration patterns:

Basic Examples
~~~~~~~~~~~~~~

- **basic_mcp_agent.py** - Simple agent with MCP tools
- **basic_download.py** - Basic file download operations
- **simple_discovery_demo.py** - Discovering MCP servers
- **simple_test_discovery.py** - Testing discovery functionality

Advanced Integration
~~~~~~~~~~~~~~~~~~~~

- **aug_llm_mcp_integration.py** - Integration with AugLLM engine
- **complete_mcp_integration.py** - Full MCP integration example
- **dynamic_mcp_agent_system.py** - Dynamic agent creation
- **typed_mcp_aug_llm_example.py** - Type-safe MCP integration

Automation & Discovery
~~~~~~~~~~~~~~~~~~~~~~

- **automated_discovery_agent.py** - Automatic server discovery from 1900+ servers
- **comprehensive_mcp_discovery.py** - Comprehensive discovery patterns
- **dynamic_activation_mcp_example.py** - Dynamic tool activation
- **procedural_mcp_addition.py** - Adding MCP servers procedurally

Production Examples
~~~~~~~~~~~~~~~~~~~

- **production_mcp_harvester.py** - Production-ready MCP harvesting
- **background_mcp_processor.py** - Background processing with MCP
- **mcp_integration_pipeline.py** - Complete integration pipeline
- **documentation_processing_pipeline.py** - Processing documentation with MCP

Specialized Use Cases
~~~~~~~~~~~~~~~~~~~~~

- **ai_enhanced_coding.py** - AI-powered coding assistance
- **dataflow_mcp_example.py** - Dataflow integration
- **batch_operations.py** - Batch processing with MCP
- **custom_installer.py** - Custom server installation

Quick Example
-------------

Here's a simple example to get started:

.. code-block:: python

   from haive.mcp.agents.enhanced_mcp_agent import EnhancedMCPAgent
   from haive.core.engine.aug_llm import AugLLMConfig
   import asyncio

   async def main():
       # Create agent with automatic MCP discovery
       agent = EnhancedMCPAgent(
           name="example_agent",
           engine=AugLLMConfig(temperature=0.7),
           mcp_categories=["core", "ai_enhanced"],
           auto_install=True
       )
       
       # Initialize (auto-installs servers)
       await agent.initialize_mcp()
       
       # Use the agent
       result = await agent.arun("Analyze Python files and create a summary")
       print(result)

   asyncio.run(main())

Running Examples
----------------

To run any example:

.. code-block:: bash

   # Navigate to examples directory
   cd docs/source/examples
   
   # Run an example
   poetry run python basic_mcp_agent.py
   
   # Or run with the shell script
   ./run_mcp_agent.sh

Configuration
-------------

Some examples use the ``mcp_servers_config.json`` file for configuration. This file defines server categories and installation preferences.

Next Steps
----------

- Review :doc:`tutorials` for step-by-step guides
- Check :doc:`guides` for architectural patterns
- Explore the :doc:`API Reference <autoapi/haive/mcp/index>` for detailed documentation