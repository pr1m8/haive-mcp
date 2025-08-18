# Google-style Docstring Examples for MCP

## Module Docstring Example

```python
"""Simple FAISS-based MCP Retriever with Auto-Loading.

This module provides a FAISS-based vector retriever for MCP server documentation.
It automatically loads and indexes all available MCP server documentation,
providing efficient semantic search capabilities.

The retriever supports:
    - Automatic documentation loading from MCP database
    - FAISS vector indexing with HuggingFace embeddings
    - Caching for improved performance
    - Semantic search with configurable top-k results

Example:
    Basic usage of the FAISS retriever:

        from haive.mcp.retrieval import SimpleFAISSRetriever

        # Create and setup retriever
        retriever = SimpleFAISSRetriever(cache_dir="/tmp/mcp_cache")
        retriever.setup()

        # Search for MCP servers
        results = retriever.search("database operations", top_k=5)

        # Get specific server info
        server_info = retriever.get_server_info("postgresql")
"""
```

## Class Docstring Example

```python
class SimpleFAISSRetriever:
    """Simple FAISS-based retriever for MCP server documentation.

    This retriever provides semantic search capabilities over MCP server
    documentation using FAISS vector indexing. It automatically loads
    documentation from the MCP database and builds an efficient search index.

    Attributes:
        cache_dir: Directory path for caching FAISS index and documents.
        doc_loader: MCPDocumentationLoader instance for loading server docs.
        embeddings: HuggingFace embeddings model for vectorization.
        vectorstore: FAISS vector store instance.
        documents: List of loaded Document objects.

    Example:
        Creating and using the retriever:

            retriever = SimpleFAISSRetriever(cache_dir="/tmp/mcp_cache")
            retriever.setup()

            # Search for database-related servers
            results = retriever.search("postgresql database", top_k=3)
            for server in results:
                print(f"{server['name']}: {server['description']}")
    """
```

## Method Docstring Examples

```python
def setup(self) -> None:
    """Set up the retriever with auto-loading.

    Initializes the FAISS vector store by either loading from cache
    or building a new index from MCP documentation. This method must
    be called before using search functionality.

    The setup process:
        1. Checks for existing cache files
        2. Loads from cache if available
        3. Otherwise builds new index from documentation

    Raises:
        RuntimeError: If documentation loading fails.
        IOError: If cache directory is not accessible.
    """

def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """Search for MCP servers using semantic similarity.

    Performs semantic search over MCP server documentation to find
    servers matching the given query.

    Args:
        query: Natural language search query describing desired capabilities.
        top_k: Maximum number of results to return. Defaults to 10.

    Returns:
        List of dictionaries containing server information:
            - name: Server identifier
            - description: Server description
            - capabilities: List of server capabilities
            - install_command: Installation command
            - relevance_score: Similarity score (0-1)

    Raises:
        ValueError: If top_k is less than 1.
        RuntimeError: If retriever is not initialized (setup not called).

    Example:
        results = retriever.search("file system operations", top_k=5)
        for server in results:
            print(f"{server['name']}: {server['relevance_score']:.2f}")
    """

def _build_index(self) -> None:
    """Build FAISS index from MCP documentation.

    Internal method that loads all MCP server documentation,
    splits it into chunks, and builds a FAISS vector index.

    The indexing process:
        1. Loads documentation from MCPDocumentationLoader
        2. Splits documents into chunks for better retrieval
        3. Creates embeddings using HuggingFace model
        4. Builds FAISS index
        5. Saves to cache for future use

    Note:
        This is an internal method called by setup(). Users should
        not call this directly.

    Raises:
        RuntimeError: If documentation loading or indexing fails.
    """
```

## Function Docstring Example

```python
def create_filesystem_agent(
    engine: AugLLMConfig,
    allowed_paths: List[str] = None,
    read_only: bool = False
) -> MCPAgent:
    """Create an MCP agent with filesystem capabilities.

    Factory function that creates an MCPAgent pre-configured with
    the filesystem MCP server for file operations.

    Args:
        engine: Language model configuration for the agent.
        allowed_paths: List of directory paths the agent can access.
            If None, defaults to current directory only.
        read_only: If True, agent can only read files, not write.
            Defaults to False.

    Returns:
        MCPAgent configured with filesystem MCP server.

    Raises:
        ValueError: If allowed_paths contains invalid paths.
        RuntimeError: If filesystem MCP server is not available.

    Example:
        # Create agent with filesystem access
        agent = create_filesystem_agent(
            engine=AugLLMConfig(),
            allowed_paths=["/home/user/documents", "/tmp"],
            read_only=True
        )

        # Use agent to read files
        result = await agent.arun({
            "messages": [{"role": "user", "content": "List files in /tmp"}]
        })
    """
```

## Key Principles

1. **First line**: Brief one-line summary ending with period.
2. **Blank line**: After the summary.
3. **Extended description**: More detailed explanation of functionality.
4. **Sections**: Use consistent section headers (Args, Returns, Raises, Example, Note).
5. **Args format**: `name: Description starting with capital and ending with period.`
6. **Returns format**: Start with type description, then explain what it represents.
7. **Examples**: Use real, runnable code examples.
8. **Cross-references**: Use proper names for classes/functions that can be linked.
