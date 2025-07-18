"""MCP documentation and setup instruction generation.

This module provides tools for processing MCP server documentation, extracting
setup instructions, and generating configuration from documentation files.
It can parse README files, extract tool/resource definitions, and create
ready-to-use configurations.

The documentation system helps users:
- Understand server capabilities from docs
- Generate proper configurations
- Extract setup requirements
- Create implementation guides

Classes:
    MCPDocumentationLoader: Loads and processes MCP documentation

Example:
    Processing MCP server documentation::

        from haive.mcp.documentation import MCPDocumentationLoader

        loader = MCPDocumentationLoader()

        # Load documentation for a server
        doc = await loader.load_server_docs("@modelcontextprotocol/server-filesystem")

        print(f"Server: {doc.name}")
        print(f"Description: {doc.description}")
        print("\\nTools:")
        for tool in doc.tools:
            print(f"  - {tool.name}: {tool.description}")

        print("\\nSetup Instructions:")
        print(doc.setup_instructions)

        # Generate configuration from docs
        config = doc.generate_config()
        print(f"\\nGenerated config: {config}")

Advanced Usage:
    Batch processing and analysis::

        from haive.mcp.documentation import MCPDocumentationLoader

        loader = MCPDocumentationLoader()

        # Process multiple server docs
        servers = [
            "@modelcontextprotocol/server-github",
            "@modelcontextprotocol/server-postgres",
            "@modelcontextprotocol/server-slack"
        ]

        docs = await loader.batch_load(servers)

        # Find servers with specific capabilities
        file_servers = [
            doc for doc in docs
            if any("file" in tool.name for tool in doc.tools)
        ]

        # Generate implementation guide
        guide = await loader.generate_implementation_guide(
            server_docs=file_servers,
            use_case="File management system"
        )

        print(guide.markdown)

Documentation Processing:
    The loader extracts:
    - **Tools**: Function definitions and parameters
    - **Resources**: Available data sources
    - **Prompts**: Pre-defined prompt templates
    - **Setup**: Installation and configuration steps
    - **Examples**: Usage examples from docs
    - **Dependencies**: Required packages and environment

Output Formats:
    - Raw documentation data
    - Pydantic configuration models
    - Markdown guides
    - JSON schemas

See Also:
    haive.mcp.discovery: Discovering servers to document
    haive.mcp.config: Configuration models generated from docs
    haive.mcp.agents.documentation_agent: Agent for doc processing
"""

from haive.mcp.documentation.doc_loader import MCPDocumentationLoader


__all__ = ["MCPDocumentationLoader"]
