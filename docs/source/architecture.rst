Architecture
============

Comprehensive overview of haive-mcp's architecture enabling dynamic integration with 1900+ MCP servers.

System Overview
---------------

Haive-mcp is designed as a modular, extensible system that bridges the Haive agent framework with the Model Context Protocol ecosystem:

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────┐
   │                     Haive Agent Framework                    │
   ├─────────────────────────────────────────────────────────────┤
   │                        haive-mcp Layer                       │
   │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
   │  │   Agents    │  │   Discovery  │  │     Manager      │  │
   │  │  • MCPAgent │  │  • Registry  │  │  • Lifecycle     │  │
   │  │  • Enhanced │  │  • Search    │  │  • Installation  │  │
   │  └─────────────┘  └──────────────┘  └──────────────────┘  │
   ├─────────────────────────────────────────────────────────────┤
   │                    MCP Protocol Layer                        │
   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
   │  │  STDIO   │  │   HTTP   │  │   SSE    │  │  WebSocket│  │
   │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
   ├─────────────────────────────────────────────────────────────┤
   │                   1900+ MCP Servers                          │
   │  [Filesystem] [Database] [AI Tools] [Web] [Crypto] [More]   │
   └─────────────────────────────────────────────────────────────┘

Core Components
---------------

Agent Layer
~~~~~~~~~~~

The agent layer provides MCP-enabled agents that extend Haive's base agent capabilities:

- **MCPAgent**: Base agent with MCP tool integration
- **EnhancedMCPAgent**: Automatic discovery and installation from 1900+ servers
- **IntelligentMCPAgent**: Task-aware tool selection
- **TransferableMCPAgent**: Tool sharing between agents

Discovery System
~~~~~~~~~~~~~~~~

The discovery system enables runtime tool discovery:

- **Registry**: Maintains catalog of 1900+ available servers
- **Discovery Engine**: Analyzes tasks to find relevant servers
- **Capability Matcher**: Maps requirements to server capabilities
- **Ranking System**: Prioritizes servers by relevance

Manager Component
~~~~~~~~~~~~~~~~~

The manager handles server lifecycle:

- **Installer**: Supports NPM, Pip, Git, Docker installation
- **Process Manager**: Starts, stops, monitors server processes
- **Configuration Manager**: Handles server-specific settings
- **Health Monitor**: Tracks server status and performance

Communication Patterns
----------------------

Request-Response Flow
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Agent → MCP Client → Transport → MCP Server → Tool
     ↑                                              ↓
     └──────────────── Response ←─────────────────┘

1. Agent receives user request
2. MCP client formats as MCP protocol message
3. Transport layer handles communication
4. MCP server executes tool
5. Response flows back through layers

Async Operations
~~~~~~~~~~~~~~~~

All MCP operations are asynchronous for optimal performance:

.. code-block:: python

   async def mcp_flow():
       # Discovery (async)
       servers = await discovery.find_servers_for_task(task)
       
       # Installation (async)
       await manager.install_servers(servers)
       
       # Execution (async)
       result = await agent.execute_tool(tool, params)

Transport Protocols
-------------------

STDIO Transport
~~~~~~~~~~~~~~~

Used for command-line based servers:

- Process-based communication
- JSON-RPC over stdin/stdout
- Suitable for Node.js, Python servers
- Most common transport (60% of servers)

HTTP Transport
~~~~~~~~~~~~~~

For web-based servers:

- RESTful API communication
- JSON payloads
- Authentication support
- Suitable for cloud services

SSE Transport
~~~~~~~~~~~~~

For streaming servers:

- Server-Sent Events
- Real-time updates
- Unidirectional streaming
- Used for monitoring, logs

WebSocket Transport
~~~~~~~~~~~~~~~~~~~

For bidirectional communication:

- Full-duplex channels
- Low latency
- Real-time interaction
- Advanced server features

Discovery Architecture
----------------------

Three-Tier Discovery
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Tier 1: Local Cache
   ├── Recently used servers
   ├── User preferences
   └── Performance metrics
   
   Tier 2: Registry Database
   ├── 1900+ server definitions
   ├── Capability mappings
   └── Version information
   
   Tier 3: Remote Discovery
   ├── GitHub repositories
   ├── NPM registry
   └── Community servers

Discovery Algorithm
~~~~~~~~~~~~~~~~~~~

1. **Task Analysis**: NLP processing of user request
2. **Capability Extraction**: Identify required capabilities
3. **Server Matching**: Find servers with capabilities
4. **Ranking**: Score by relevance, popularity, performance
5. **Selection**: Choose optimal server set

Installation Architecture
-------------------------

Multi-Stage Installation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Stage 1: Dependency Resolution
   ├── Check package manager
   ├── Resolve dependencies
   └── Verify compatibility
   
   Stage 2: Download & Install
   ├── Parallel downloads
   ├── Package installation
   └── Post-install scripts
   
   Stage 3: Verification
   ├── Health check
   ├── Tool discovery
   └── Performance test

Installer Types
~~~~~~~~~~~~~~~

- **NPM Installer**: Node.js packages via npx
- **Pip Installer**: Python packages via pip
- **Git Installer**: Direct from repositories
- **Docker Installer**: Containerized servers
- **Binary Installer**: Pre-compiled executables

Caching Architecture
--------------------

Multi-Level Cache
~~~~~~~~~~~~~~~~~

.. code-block:: text

   L1: Memory Cache (< 1ms)
   ├── Active connections
   ├── Recent responses
   └── Hot configuration
   
   L2: Local Disk (< 10ms)
   ├── Server metadata
   ├── Tool definitions
   └── Response cache
   
   L3: Redis Cache (< 50ms)
   ├── Shared state
   ├── Distributed cache
   └── Session data

Cache Strategies
~~~~~~~~~~~~~~~~

- **Write-Through**: Updates cache and backend
- **Write-Behind**: Async cache updates
- **Cache-Aside**: Lazy loading
- **Refresh-Ahead**: Predictive refresh

Security Architecture
---------------------

Defense in Depth
~~~~~~~~~~~~~~~~

.. code-block:: text

   Layer 1: Authentication
   ├── API keys
   ├── OAuth 2.0
   └── JWT tokens
   
   Layer 2: Authorization
   ├── Role-based access
   ├── Tool permissions
   └── Resource limits
   
   Layer 3: Isolation
   ├── Process sandboxing
   ├── Network segmentation
   └── Resource quotas
   
   Layer 4: Monitoring
   ├── Audit logging
   ├── Anomaly detection
   └── Rate limiting

Scaling Architecture
--------------------

Horizontal Scaling
~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Load Balancer
   ├── Agent Pool (N instances)
   ├── MCP Server Pool (M instances)
   └── Cache Cluster (K nodes)

Vertical Scaling
~~~~~~~~~~~~~~~~

- Resource allocation per server
- Connection pool sizing
- Cache size management
- Process priority tuning

Performance Optimizations
-------------------------

Connection Pooling
~~~~~~~~~~~~~~~~~~

Maintains persistent connections to frequently used servers:

- Reduces connection overhead
- Improves response times
- Handles connection lifecycle
- Automatic reconnection

Parallel Processing
~~~~~~~~~~~~~~~~~~~

Executes independent operations concurrently:

- Parallel server installation
- Concurrent tool execution
- Batch operation support
- Async/await throughout

Predictive Loading
~~~~~~~~~~~~~~~~~~

Anticipates user needs:

- Pre-loads likely servers
- Warms cache with common operations
- Background initialization
- Speculative execution

Extensibility Points
--------------------

Custom Agents
~~~~~~~~~~~~~

Extend base agents for domain-specific needs:

.. code-block:: python

   class CustomMCPAgent(MCPAgent):
       """Domain-specific MCP agent."""
       pass

Custom Servers
~~~~~~~~~~~~~~

Create proprietary MCP servers:

.. code-block:: python

   class CustomServer(MCPServer):
       """Custom MCP server implementation."""
       pass

Custom Transports
~~~~~~~~~~~~~~~~~

Implement new transport protocols:

.. code-block:: python

   class CustomTransport(Transport):
       """Custom transport implementation."""
       pass

Next Steps
----------

- Review :doc:`guides/platform-architecture` for detailed patterns
- Check :doc:`advanced` for advanced architectures
- Explore the :doc:`API Reference <autoapi/haive/mcp/index>`