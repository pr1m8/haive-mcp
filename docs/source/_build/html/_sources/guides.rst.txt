Guides
======

In-depth guides for working with haive-mcp and its 1900+ available MCP servers.

.. toctree::
   :maxdepth: 2
   :caption: Available Guides

   guides/quickstart
   guides/platform-architecture
   guides/fastapi-integration
   guides/mcp-browser-plugin
   guides/real-world-examples

Guide Overview
--------------

**Quickstart Guide**
   Get up and running with haive-mcp in minutes. Learn how to create agents that automatically discover and use tools from 1900+ MCP servers.

**Platform Architecture**
   Understand the architecture behind haive-mcp's dynamic discovery system, server categories, and integration patterns.

**FastAPI Integration**
   Build web APIs that leverage MCP servers for enhanced functionality. Create REST endpoints powered by MCP tools.

**MCP Browser Plugin**
   Develop browser extensions and plugins that interact with MCP servers for web automation and data extraction.

**Real-World Examples**
   Explore production use cases and patterns from actual deployments using haive-mcp's extensive server ecosystem.

Key Concepts
------------

Dynamic Discovery
~~~~~~~~~~~~~~~~~

Haive-mcp's core innovation is automatic discovery from 1900+ available servers:

- Agents analyze task requirements
- Automatically find relevant servers
- Install and configure tools on-the-fly
- No manual configuration needed

Server Categories
~~~~~~~~~~~~~~~~~

Servers are organized into logical categories:

- **core** - Essential tools (filesystem, database, search)
- **ai_enhanced** - AI-powered capabilities
- **enhanced_filesystem** - Advanced file operations
- **time_utilities** - Date and scheduling tools
- **browser_automation** - Web interaction tools
- **crypto_finance** - Financial and blockchain tools
- **github_enhanced** - Code repository tools
- **notifications** - Alert and messaging tools

Best Practices
--------------

1. **Let agents discover tools** - Don't manually configure unless necessary
2. **Use categories wisely** - Start with "core" and add as needed
3. **Monitor performance** - Use health checks and status monitoring
4. **Handle failures gracefully** - Implement proper error handling
5. **Cache when possible** - Reuse initialized agents for better performance

Next Steps
----------

- Start with the :doc:`guides/quickstart` guide
- Review :doc:`tutorials` for hands-on learning
- Explore :doc:`examples` for code samples
- Check the :doc:`API Reference <autoapi/haive/mcp/index>` for detailed documentation