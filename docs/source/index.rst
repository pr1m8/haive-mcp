Haive MCP Documentation
=======================

.. toctree::
   :maxdepth: 4
   :caption: 🔍 API Reference
   :hidden:

   API Overview <api_reference>
   autoapi/index

.. toctree::
   :maxdepth: 3
   :caption: 🚀 Quick Start
   :hidden:

   getting_started
   installation 
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: 📚 Tutorials & Examples
   :hidden:

   tutorials
   examples

.. toctree::
   :maxdepth: 2
   :caption: 📖 User Guides
   :hidden:

   guides
   user_guide

.. toctree::
   :maxdepth: 2
   :caption: 🛠️ Developer Resources
   :hidden:

   advanced
   advanced_config
   server_manager_guide
   managing_mcp_servers

.. toctree::
   :maxdepth: 2
   :caption: 🔧 MCP Servers
   :hidden:

   mcp_servers/index
   mcp_servers/installation
   mcp_servers/configuration
   mcp_servers/catalog

.. toctree::
   :maxdepth: 2
   :caption: 📖 References
   :hidden:

   changelog
   glossary

Welcome to Haive MCP
--------------------

Haive MCP (Model Context Protocol) revolutionizes how AI agents acquire capabilities by enabling **dynamic, runtime integration** of tools, resources, and prompts from a vast ecosystem of **1900+ MCP servers from top GitHub repositories**.

🚀 **The Game Changer**: Your agents can now **automatically discover and integrate** the exact tools they need, when they need them, without any predefined configuration!

Dynamic Integration at Its Core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Imagine an agent that starts with zero tools but can:

* **Self-query** through 992+ servers to find capabilities
* **Automatically install** and configure needed tools at runtime
* **Dynamically integrate** tools, resources, and prompts into its workflow
* **Adapt capabilities** based on the task at hand

Example: Ask your agent to "analyze this GitHub repo and create visualizations" - it will automatically discover and integrate GitHub tools, code analysis tools, and visualization libraries without any manual setup!

Key Features
~~~~~~~~~~~~

* **🔍 Self-Query Retrieval** - Agents search through 1900+ servers using intelligent matching
* **⚡ Dynamic Tool Integration** - Tools are discovered, installed, and integrated at runtime
* **🧠 AI-Powered Discovery** - Smart recommendations based on task analysis
* **🔌 Zero Configuration** - Many servers work instantly via npx
* **🎯 Capability Matching** - Find servers by what they can do, not by name
* **🔄 Runtime Adaptation** - Agents evolve their capabilities during execution
* **📚 Beyond Tools** - Also discovers resources (databases, APIs) and domain-specific prompts
* **🛡️ HITL Workflows** - Optional human approval for security
* **💪 Automatic Failover** - Finds alternative servers if primaries fail

What is MCP?
~~~~~~~~~~~~

Model Context Protocol (MCP) is an open standard that allows AI systems to securely connect to data sources and tools. With MCP, your agents can:

- Access file systems and databases
- Use web search and APIs
- Control development tools
- Interact with specialized services
- And much more!

Quick Example: Dynamic Discovery in Action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :caption: Watch an agent automatically discover and integrate tools

   from haive.mcp.agents import IntelligentMCPAgent
   from haive.core.engine import AugLLMConfig

   # Create an intelligent agent with dynamic discovery
   agent = IntelligentMCPAgent(
       engine=AugLLMConfig(),
       auto_discover=True  # Enable automatic tool discovery
   )

   # Ask it to do something - it will find the tools it needs!
   result = await agent.arun({
       "messages": [{
           "role": "user", 
           "content": "Search GitHub for Python AI projects and create a report"
       }]
   })

.. note::
   The agent automatically:
   
   1. **Discovers GitHub access** → finds @modelcontextprotocol/server-github
   2. **Discovers file writing** → finds @modelcontextprotocol/server-filesystem  
   3. **Finds code analysis** → locates relevant analysis servers
   4. **Installs all tools** dynamically at runtime
   5. **Completes the task** with newly acquired capabilities!

Massive Server Discovery Database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: 🔍 **Smart Discovery**
      :text-align: center

      Ask for any capability and agents find the right tools:
      
      * "Extract data from PDFs" → PDF processing servers
      * "Connect to PostgreSQL" → Database servers  
      * "Create visualizations" → Charting tools
      * "Send emails" → Email API servers
      * "Scrape websites" → Web scraping tools

   .. grid-item-card:: 🚀 **Vast Ecosystem**
      :text-align: center

      Access to **1900+ servers** from top repositories:
      
      * Financial data & crypto analysis
      * Smart home & IoT integration  
      * Medical image processing
      * Document translation
      * Cloud resource optimization

Getting Help
~~~~~~~~~~~~

* **Documentation**: You're reading it!
* **GitHub Issues**: https://github.com/pr1m8/haive-mcp/issues
* **Examples**: See the ``examples/`` directory
* **Community**: Join our Discord server

Next Steps
~~~~~~~~~~

- :doc:`getting_started` - Understand MCP concepts
- :doc:`installation` - Install haive-mcp
- :doc:`quickstart` - Create your first MCP agent
- :doc:`examples` - Explore example implementations

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`