📊 Class Inheritance Diagram
=============================

This interactive diagram shows the class hierarchy within the Haive MCP package and its relationships to the core Haive framework.

.. raw:: html

   <details>
   <summary><strong>🔍 Click to View Complete Inheritance Diagram</strong></summary>

.. mermaid::

   graph TD
       %% Core Haive Classes (from haive-central)
       Agent[🤖 Agent<br/>Base agent class]:::central
       BaseModel[📋 BaseModel<br/>Pydantic base]:::central
       Tool[🔧 Tool<br/>LangChain tool base]:::central
       
       %% MCP Core Classes
       MCPClient[🌐 MCPClient<br/>Protocol client]:::mcp
       MCPServer[🖥️ MCPServer<br/>Protocol server]:::mcp
       MCPTool[⚙️ MCPTool<br/>MCP-enabled tool]:::mcp
       
       %% MCP Agent Classes
       MCPAgent[🤖 MCPAgent<br/>MCP-aware agent]:::mcpagent
       IntelligentMCPAgent[🧠 IntelligentMCPAgent<br/>Auto-discovery agent]:::mcpagent
       
       %% MCP Registry Classes
       ServerRegistry[📚 ServerRegistry<br/>Server catalog]:::registry
       ToolRegistry[🔍 ToolRegistry<br/>Tool discovery]:::registry
       
       %% MCP Configuration Classes
       MCPConfig[⚙️ MCPConfig<br/>Configuration]:::config
       ServerConfig[🖥️ ServerConfig<br/>Server settings]:::config
       ClientConfig[💻 ClientConfig<br/>Client settings]:::config
       
       %% Plugin System
       MCPPlugin[🔌 MCPPlugin<br/>Plugin base]:::plugin
       FilesystemPlugin[📁 FilesystemPlugin<br/>File operations]:::plugin
       DatabasePlugin[🗄️ DatabasePlugin<br/>DB operations]:::plugin
       
       %% Inheritance relationships
       Agent --> MCPAgent
       MCPAgent --> IntelligentMCPAgent
       
       Tool --> MCPTool
       
       BaseModel --> MCPConfig
       MCPConfig --> ServerConfig
       MCPConfig --> ClientConfig
       
       BaseModel --> MCPPlugin
       MCPPlugin --> FilesystemPlugin
       MCPPlugin --> DatabasePlugin
       
       %% Composition relationships (uses/contains)
       MCPClient -.->|uses| ServerRegistry
       MCPAgent -.->|uses| MCPClient
       MCPAgent -.->|uses| ToolRegistry
       ServerRegistry -.->|manages| MCPServer
       ToolRegistry -.->|discovers| MCPTool
       
       %% Links to documentation
       click Agent "https://haive-central.readthedocs.io/en/latest/agents/base.html" "🔗 View in Haive Central Docs"
       click BaseModel "https://haive-central.readthedocs.io/en/latest/schema/base.html" "🔗 View in Haive Central Docs"
       click Tool "https://haive-central.readthedocs.io/en/latest/tools/base.html" "🔗 View in Haive Central Docs"
       
       click MCPClient "autoapi/haive/mcp/client/index.html" "📖 View API Documentation"
       click MCPServer "autoapi/haive/mcp/servers/index.html" "📖 View API Documentation" 
       click MCPAgent "autoapi/haive/mcp/agents/index.html" "📖 View API Documentation"
       click IntelligentMCPAgent "autoapi/haive/mcp/agents/index.html" "📖 View API Documentation"
       click ServerRegistry "autoapi/haive/mcp/registry/index.html" "📖 View API Documentation"
       click ToolRegistry "autoapi/haive/mcp/registry/index.html" "📖 View API Documentation"
       
       %% Styling
       classDef central fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#000
       classDef mcp fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
       classDef mcpagent fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
       classDef registry fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000
       classDef config fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000
       classDef plugin fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#000

.. raw:: html

   </details>

🔗 **External References**
--------------------------

This diagram shows relationships between haive-mcp classes and core Haive framework classes:

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: 🏠 **Haive Central Documentation**
      :link: https://haive-central.readthedocs.io/
      :class-header: sd-bg-primary sd-text-white
      
      Complete framework documentation including base Agent, Tool, and Schema classes that haive-mcp extends.

   .. grid-item-card:: 📖 **Local API Reference**
      :link: autoapi/index.html
      :class-header: sd-bg-secondary sd-text-white
      
      Detailed API documentation for all haive-mcp specific classes and methods.

📋 **Legend**
-------------

.. list-table:: 
   :header-rows: 1
   :class: sd-table-striped

   * - **Color**
     - **Component Type**  
     - **Description**
   * - 🔵 Blue
     - Haive Central
     - Core framework classes from haive-central
   * - 🟣 Purple  
     - MCP Core
     - Core MCP protocol implementation
   * - 🟢 Green
     - MCP Agents
     - Agent classes with MCP capabilities
   * - 🟠 Orange
     - Registry
     - Server and tool discovery systems
   * - 🔴 Pink
     - Configuration
     - Settings and configuration classes
   * - 🟤 Teal
     - Plugins
     - Extensible plugin system

📚 **Key Relationships**
------------------------

- **Inheritance** (solid arrows): Direct class inheritance
- **Composition** (dashed arrows): Classes that use or contain other classes
- **External Links**: Click blue classes to view in Haive Central docs
- **Internal Links**: Click colored classes to view local API documentation

.. note::
   
   **Interactive Features**: 
   
   - Click any class node to view detailed documentation
   - Blue nodes link to haive-central documentation
   - Colored nodes link to local API reference
   - Expand/collapse the diagram using the details toggle