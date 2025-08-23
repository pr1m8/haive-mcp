Haive MCP Documentation
=======================

.. toctree::
   :maxdepth: 3
   :caption: 🚀 Quick Start
   :hidden:

   getting_started
   installation
   quickstart

.. toctree::
   :maxdepth: 3
   :caption: 📚 Learning Center
   :hidden:

   tutorials
   examples
   guides
   user_guide

.. toctree::
   :maxdepth: 3
   :caption: 🛠️ Developer Guide
   :hidden:

   advanced
   advanced_config
   server_manager_guide
   managing_mcp_servers

.. toctree::
   :maxdepth: 3
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

   api_reference
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

Watch as an agent automatically discovers and integrates tools based on your request::

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
            "content": "Search GitHub for Python AI projects, analyze their code quality, and save a report"
        }]
    })

    # The agent automatically:
    # 1. Discovers it needs GitHub access → finds @modelcontextprotocol/server-github
    # 2. Discovers it needs file writing → finds @modelcontextprotocol/server-filesystem  
    # 3. Discovers it needs code analysis → finds relevant code analysis servers
    # 4. Installs and integrates all tools dynamically
    # 5. Completes the complex task with its newly acquired capabilities!

Self-Query Through 1900+ Servers from Top Repositories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The agent can search through a massive database of MCP servers from leading GitHub projects::

    # Ask for any capability - the agent will find it from top repositories
    "Extract data from PDFs"           → Discovers PDF processing servers
    "Connect to PostgreSQL"            → Finds database servers  
    "Create data visualizations"       → Locates visualization tools
    "Send emails"                      → Identifies email servers
    "Scrape websites"                  → Finds web scraping tools
    "Generate music"                   → Discovers audio generation servers
    "Analyze stock market data"        → Finds financial data servers
    "Control smart home devices"       → Finds IoT integration servers
    "Process medical images"           → Discovers healthcare ML servers
    "Translate documents"              → Finds translation API servers
    "Optimize cloud resources"         → Locates cloud management tools
    "Analyze blockchain data"          → Finds crypto analysis servers
    ... and 1888+ more capabilities from the most popular GitHub projects!

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