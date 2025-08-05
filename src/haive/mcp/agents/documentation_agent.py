r"""MCP Documentation Agent for processing and setting up MCP servers.

This module provides a specialized agent that combines document processing
capabilities with MCP knowledge to help users understand, configure, and
implement MCP servers. It processes documentation from various sources and
generates actionable setup instructions.

The agent uses document processing capabilities to:
    1. Load MCP server documentation from stored resources (992+ servers)
    2. Fetch additional documentation from GitHub repositories
    3. Generate setup instructions for agents
    4. Provide implementation guidance with code examples
    5. Extract capabilities and configuration requirements
    6. Create ready-to-use MCPServerConfig instances

Classes:
    MCPDocumentationAgent: Document agent specialized for MCP documentation

Functions:
    create_for_mcp_setup: Factory for setup-focused documentation agent
    create_for_mcp_research: Factory for research-focused documentation agent

Example:
    Processing MCP server documentation::

        from haive.mcp.agents import MCPDocumentationAgent
from haive import core
from haive import agents


        # Create documentation agent
        doc_agent = MCPDocumentationAgent.create_for_mcp_setup()
        await doc_agent.setup()

        # Process filesystem server documentation
        result = await doc_agent.process_mcp_server(
            "modelcontextprotocol/server-filesystem",
            fetch_latest=True
        )

        # Get setup instructions
        print("\n".join(result["setup_instructions"]))

        # Get generated config
        config = result["mcp_config"]
        print(f"Server: {config.name}")
        print(f"Command: {config.command} {' '.join(config.args)}")

        # Find servers by capability
        search_results = await doc_agent.find_servers_by_capability(
            "database",
            limit=5
        )

        for server in search_results:
            print(f"Found: {server['server_name']}")

Note:
    The agent has access to pre-processed documentation for 992+ MCP servers
    stored in the agent_resources directory.
"""

import json
import logging
from pathlib import Path
from typing import Any

from haive.agents.document.agent import DocumentAgent
from pydantic import Field

from haive.mcp.config import MCPConfig, MCPServerConfig, MCPTransport
from haive.mcp.documentation.doc_loader import MCPDocumentationLoader
from haive.mcp.mixins.mcp_mixin import MCPMixin

logger = logging.getLogger(__name__)


class MCPDocumentationAgent(MCPMixin, DocumentAgent):
    r"""Agent specialized for processing MCP server documentation and generating setup instructions.

    MCPDocumentationAgent extends DocumentAgent with specialized capabilities for
    processing Model Context Protocol server documentation. It can extract setup
    instructions, generate configurations, and provide implementation guidance
    from various documentation sources.

    The agent combines document processing capabilities with MCP knowledge to:
        - Load and process MCP server documentation from stored resources
        - Extract setup instructions from README files and documentation
        - Generate MCPServerConfig instances from documentation
        - Provide implementation guidance with code examples
        - Search for servers by capability or category
        - Create combined configurations for multi-server setups

    Attributes:
        doc_loader: MCPDocumentationLoader instance for accessing stored docs
        resources_path: Path to MCP server resources directory

    Inherits from:
        MCPMixin: Provides MCP client capabilities
        DocumentAgent: Provides document processing capabilities

    Example:
        Basic documentation processing::

            # Create documentation agent
            doc_agent = MCPDocumentationAgent.create_for_mcp_setup(
                engine=engine
            )
            await doc_agent.setup()

            # Process filesystem server docs
            result = await doc_agent.process_mcp_server(
                "modelcontextprotocol/server-filesystem"
            )

            # Extract components
            setup_steps = result["setup_instructions"]
            mcp_config = result["mcp_config"]
            capabilities = result["capabilities"]

            print(f"Server: {mcp_config.name}")
            print(f"Capabilities: {', '.join(capabilities)}")
            print("\nSetup Instructions:")
            for step in setup_steps:
                print(f"  {step}")

        Advanced multi-server setup::

            # Generate implementation guide for multiple servers
            guide = await doc_agent.generate_implementation_guide(
                server_names=[
                    "modelcontextprotocol/server-filesystem",
                    "modelcontextprotocol/server-github",
                    "modelcontextprotocol/server-postgres"
                ],
                target_agent_type="research"
            )

            # Get combined configuration
            combined_config = guide["combined_config"]

            # Get implementation code
            implementation = guide["implementation_code"]
            print(implementation)
    """

    # MCP documentation loader
    doc_loader: MCPDocumentationLoader = Field(
        default_factory=MCPDocumentationLoader,
        description="MCP documentation loader instance",
    )

    # Resources path
    resources_path: Path | None = Field(
        default=None, description="Path to MCP server resources"
    )

    def __init__(self, **kwargs):
        """Initialize MCP documentation agent.

        Sets up the agent with optimized defaults for processing MCP documentation.
        Initializes the documentation loader with access to stored server docs.

        Args:
            **kwargs: Additional arguments passed to parent classes including:
                - engine: AugLLMConfig for the agent
                - resources_path: Path to MCP resources directory
                - processing_strategy: Document processing strategy
                - chunking_strategy: How to chunk documents
                - All other DocumentAgent parameters
        """
        # Set document processing defaults for MCP docs
        kwargs.setdefault("name", "MCP Documentation Agent")
        kwargs.setdefault("processing_strategy", "enhanced")
        kwargs.setdefault("chunking_strategy", "paragraph")
        kwargs.setdefault("chunk_size", 2000)
        kwargs.setdefault("extract_metadata", True)
        kwargs.setdefault("normalize_content", True)

        super().__init__(**kwargs)

        # Initialize doc loader with resources path
        if self.resources_path:
            self.doc_loader = MCPDocumentationLoader(self.resources_path)

    @classmethod
    def create_for_mcp_setup(cls, **kwargs) -> "MCPDocumentationAgent":
        """Create an agent optimized for MCP setup documentation.

        Factory method that creates an agent specifically configured for
        extracting setup instructions and configuration from MCP server
        documentation. Uses semantic chunking for better context preservation.

        Args:
            **kwargs: Additional arguments including:
                - engine: Required AugLLMConfig
                - resources_path: Optional path to resources

        Returns:
            MCPDocumentationAgent: Agent configured for setup extraction with:
                - Semantic chunking for preserving setup steps
                - Enhanced processing for code extraction
                - Metadata extraction enabled
                - Language detection for code blocks

        Example:
            Creating a setup-focused agent::

                agent = MCPDocumentationAgent.create_for_mcp_setup(
                    engine=engine
                )

                # Process server setup documentation
                result = await agent.process_mcp_server(
                    "modelcontextprotocol/server-brave-search"
                )

                # Get installation commands
                for cmd in result["setup_instructions"]:
                    if cmd.startswith("npm") or cmd.startswith("npx"):
                        print(f"Run: {cmd}")
        """
        return cls(
            name="MCP Setup Documentation Agent",
            processing_strategy="enhanced",
            chunking_strategy="semantic",
            chunk_size=1500,
            extract_metadata=True,
            normalize_content=True,
            detect_language=True,
            **kwargs,
        )

    @classmethod
    def create_for_mcp_research(cls, **kwargs) -> "MCPDocumentationAgent":
        r"""Create an agent for researching MCP capabilities.

        Factory method that creates an agent optimized for comprehensive
        research across multiple MCP server documentations. Uses parallel
        processing and embeddings for efficient search.

        Args:
            **kwargs: Additional arguments including:
                - engine: Required AugLLMConfig
                - resources_path: Optional path to resources

        Returns:
            MCPDocumentationAgent: Agent configured for research with:
                - Parallel processing for multiple documents
                - Recursive chunking with overlap
                - Embedding generation enabled
                - Maximum worker threads for speed

        Example:
            Researching MCP capabilities::

                agent = MCPDocumentationAgent.create_for_mcp_research(
                    engine=engine
                )

                # Find all database-related servers
                db_servers = await agent.find_servers_by_capability(
                    "database",
                    limit=10
                )

                # Research each server's capabilities
                for server in db_servers:
                    print(f"\n{server['server_name']}:")
                    print(f"  Capabilities: {server['capabilities']}")
                    print(f"  Setup: {len(server['setup_instructions'])} steps")
        """
        return cls(
            name="MCP Research Agent",
            processing_strategy="parallel",
            chunking_strategy="recursive",
            chunk_size=2000,
            chunk_overlap=300,
            enable_embedding=True,
            max_workers=8,
            **kwargs,
        )

    async def process_mcp_server(
        self, server_name: str, fetch_latest: bool = True
    ) -> dict[str, Any]:
        """Process documentation for a specific MCP server.

        Loads and processes documentation for a single MCP server, extracting
        setup instructions, configuration, and capabilities. Can fetch latest
        documentation from GitHub or use cached versions.

        Args:
            server_name: Full name of the MCP server including organization
                (e.g., "modelcontextprotocol/server-filesystem")
            fetch_latest: Whether to fetch latest docs from GitHub repository
                (default: True). Set to False for faster cached access.

        Returns:
            Dict[str, Any]: Processed server information containing:
                - server_name: The input server name
                - setup_instructions: List of setup command strings
                - mcp_config: MCPServerConfig instance ready to use
                - documentation: Full processed documentation dict
                - capabilities: List of capability strings

        Example:
            Processing with latest documentation::

                result = await agent.process_mcp_server(
                    "modelcontextprotocol/server-github",
                    fetch_latest=True
                )

                # Use the generated config
                config = result["mcp_config"]
                mcp_agent = MCPAgent(
                    engine=engine,
                    mcp_config=MCPConfig(
                        enabled=True,
                        servers={"github": config}
                    )
                )
        """
        result = {
            "server_name": server_name,
            "setup_instructions": [],
            "mcp_config": None,
            "documentation": None,
            "capabilities": [],
        }

        # Load stored documentation
        server_doc = self.doc_loader.get_server_documentation(server_name)

        if not server_doc and not fetch_latest:
            logger.warning(f"No documentation found for {server_name}")
            return result

        # Extract setup info from stored docs
        if server_doc:
            setup_info = self.doc_loader.extract_setup_info(server_doc)
            result["setup_instructions"] = self._generate_setup_instructions(setup_info)
            result["mcp_config"] = self._create_mcp_config(setup_info)
            result["capabilities"] = setup_info.get("capabilities", [])

        # Fetch latest documentation if requested
        if fetch_latest and server_doc:
            repo_url = server_doc.get("metadata", {}).get("repo_url")
            if repo_url:
                try:
                    # Use document agent to process GitHub README
                    github_result = await self.arun(
                        {"sources": [repo_url], "source_type": "url"}
                    )

                    if github_result and github_result.get("loaded_documents"):
                        # Update with latest info
                        latest_doc = github_result["loaded_documents"][0]
                        result["documentation"] = latest_doc

                        # Re-extract setup info from latest
                        latest_setup = self._extract_setup_from_content(
                            latest_doc.get("content", "")
                        )
                        if latest_setup.get("installation"):
                            result["setup_instructions"] = (
                                self._generate_setup_instructions(latest_setup)
                            )

                except Exception as e:
                    logger.exception(
                        f"Failed to fetch latest docs for {server_name}: {e}"
                    )

        return result

    async def find_servers_by_capability(
        self, capability: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Find MCP servers that provide a specific capability.

        Searches through all available MCP server documentation to find
        servers that mention a specific capability in their description
        or documentation. Returns detailed setup information for each.

        Args:
            capability: Capability to search for (e.g., "database", "search",
                "filesystem", "api", "git", "calendar")
            limit: Maximum number of results to return (default: 10)

        Returns:
            List[Dict[str, Any]]: List of server information dicts, each containing:
                - server_name: Full server identifier
                - setup_instructions: Installation and setup commands
                - mcp_config: Ready-to-use MCPServerConfig
                - capabilities: List of all server capabilities

        Example:
            Finding database servers::

                # Find all database-capable servers
                db_servers = await agent.find_servers_by_capability(
                    "database",
                    limit=5
                )

                # Create configs for all found servers
                configs = {}
                for server in db_servers:
                    config = server["mcp_config"]
                    configs[config.name] = config

                # Use in MCP agent
                agent = MCPAgent(
                    engine=engine,
                    mcp_config=MCPConfig(
                        enabled=True,
                        servers=configs
                    )
                )
        """
        # Load all documentation
        self.doc_loader.load_all_mcp_documents()

        # Search by capability
        matching_servers = self.doc_loader.search_servers_by_capability(capability)

        results = []
        for server_doc in matching_servers[:limit]:
            server_name = server_doc.get("metadata", {}).get("name", "")
            if server_name:
                # Process each matching server
                server_result = await self.process_mcp_server(
                    server_name,
                    fetch_latest=False,  # Use cached for bulk operations
                )
                results.append(server_result)

        return results

    async def generate_implementation_guide(
        self, server_names: list[str], target_agent_type: str = "general"
    ) -> dict[str, Any]:
        """Generate a complete implementation guide for using MCP servers.

        Creates a comprehensive guide including configurations, setup instructions,
        and implementation code for integrating multiple MCP servers into an agent.
        Processes each server documentation and combines them into a unified guide.

        Args:
            server_names: List of full MCP server names to include
                (e.g., ["modelcontextprotocol/server-filesystem", "modelcontextprotocol/server-github"])
            target_agent_type: Type of agent to generate code for. Options:
                - "general": Basic MCPAgent implementation
                - "research": Research-focused agent setup
                - "task": Task execution agent setup
                - "collaborative": Multi-agent collaborative setup

        Returns:
            Dict[str, Any]: Complete implementation guide containing:
                - agent_type: The specified target agent type
                - servers: Dict mapping server names to their processed info
                - combined_config: MCPConfig with all servers configured
                - implementation_code: Ready-to-use Python code
                - usage_examples: List of example code snippets

        Example:
            Generating a research agent guide::

                # Generate guide for research agent with multiple servers
                guide = await doc_agent.generate_implementation_guide(
                    server_names=[
                        "modelcontextprotocol/server-brave-search",
                        "modelcontextprotocol/server-arxiv",
                        "modelcontextprotocol/server-filesystem"
                    ],
                    target_agent_type="research"
                )

                # Save the implementation code
                with open("research_agent.py", "w") as f:
                    f.write(guide["implementation_code"])

                # Use the combined config directly
                agent = MCPAgent(
                    engine=engine,
                    mcp_config=guide["combined_config"],
                    name="research_mcp_agent"
                )
        """
        guide = {
            "agent_type": target_agent_type,
            "servers": {},
            "combined_config": None,
            "implementation_code": "",
            "usage_examples": [],
        }

        # Process each server
        server_configs = []
        for server_name in server_names:
            server_result = await self.process_mcp_server(server_name)
            guide["servers"][server_name] = server_result

            if server_result.get("mcp_config"):
                server_configs.append(server_result["mcp_config"])

        # Create combined MCP configuration
        if server_configs:
            guide["combined_config"] = self._create_combined_config(server_configs)

        # Generate implementation code
        guide["implementation_code"] = self._generate_implementation_code(
            target_agent_type, guide["combined_config"]
        )

        # Extract usage examples
        for server_data in guide["servers"].values():
            if server_data.get("documentation"):
                examples = self._extract_usage_examples(
                    server_data["documentation"].get("content", "")
                )
                guide["usage_examples"].extend(examples)

        return guide

    def _generate_setup_instructions(self, setup_info: dict[str, Any]) -> list[str]:
        """Generate step-by-step setup instructions.

        Formats extracted setup information into clear, executable instructions
        including installation commands, configuration steps, and dependencies.

        Args:
            setup_info: Dictionary containing extracted setup information with
                keys: installation, configuration, dependencies

        Returns:
            List[str]: Formatted setup instructions as strings
        """
        instructions = []

        # Installation steps
        if setup_info.get("installation"):
            instructions.append("# Installation")
            instructions.extend(setup_info["installation"])

        # Configuration steps
        if setup_info.get("configuration"):
            instructions.append("\n# Configuration")
            for key, value in setup_info["configuration"].items():
                instructions.append(f"export {key}={value}")

        # Dependencies
        if setup_info.get("dependencies"):
            instructions.append("\n# Dependencies")
            instructions.append(f"Required: {', '.join(setup_info['dependencies'])}")

        return instructions

    def _create_mcp_config(self, setup_info: dict[str, Any]) -> MCPServerConfig:
        """Create MCPServerConfig from setup information.

        Analyzes setup information to determine the appropriate transport type,
        connection parameters, and configuration for an MCP server.

        Args:
            setup_info: Dictionary containing server setup information including
                name, installation steps, configuration, and capabilities

        Returns:
            MCPServerConfig: Ready-to-use server configuration

        Note:
            Automatically detects stdio vs HTTP transports based on installation
            commands and URLs found in the setup information.
        """
        # Determine transport and connection info
        transport = MCPTransport.STDIO  # Default
        command = None
        args = []
        url = None

        # Extract from installation steps
        for step in setup_info.get("installation", []):
            if "npx" in step:
                command = "npx"
                # Extract package name
                parts = step.split()
                idx = parts.index("npx") if "npx" in parts else -1
                if idx >= 0 and idx + 1 < len(parts):
                    args = parts[idx + 1 :]
            elif "http" in step:
                # URL-based server
                transport = MCPTransport.SSE
                url = step

        return MCPServerConfig(
            name=setup_info.get("name", "unknown"),
            transport=transport,
            command=command,
            args=args,
            url=url,
            capabilities=setup_info.get("capabilities", []),
            category=setup_info.get("category", ""),
            description=setup_info.get("description", ""),
            env=setup_info.get("configuration", {}),
            api_key=setup_info.get("api_key"),
            health_check_interval=setup_info.get("health_check_interval", 60),
        )

    def _extract_setup_from_content(self, content: str) -> dict[str, Any]:
        """Extract setup information from document content.

        Wrapper method that uses the documentation loader to extract setup
        information from raw document content.

        Args:
            content: Raw document content (typically README markdown)

        Returns:
            Dict[str, Any]: Extracted setup information
        """
        return self.doc_loader.extract_setup_info({"readme_content": content})

    def _extract_usage_examples(self, content: str) -> list[str]:
        """Extract usage examples from content.

        Wrapper method that uses the documentation loader to extract code
        examples from document content.

        Args:
            content: Raw document content with code examples

        Returns:
            List[str]: Extracted code example strings
        """
        return self.doc_loader.extract_usage_examples(content)

    def _create_combined_config(
        self, server_configs: list[MCPServerConfig]
    ) -> MCPConfig:
        """Create combined MCP configuration.

        Merges multiple MCPServerConfig instances into a single MCPConfig
        for multi-server agent setups.

        Args:
            server_configs: List of individual server configurations

        Returns:
            MCPConfig: Combined configuration with all servers
        """
        servers = {}
        for config in server_configs:
            servers[config.name] = config

        return MCPConfig(
            enabled=True,
            servers=servers,
            auto_discover=False,
            categories=None,
            required_capabilities=None,
            on_server_connected=None,
            on_server_failed=None,
            on_tool_discovered=None,
        )

    def _generate_implementation_code(
        self, agent_type: str, mcp_config: MCPConfig | None
    ) -> str:
        """Generate implementation code for the agent type.

        Creates ready-to-use Python code for implementing an MCP-enabled agent
        with the specified configuration and agent type.

        Args:
            agent_type: Type of agent (general, research, task, etc.)
            mcp_config: Complete MCP configuration to embed in code

        Returns:
            str: Complete Python implementation code including imports,
                configuration, agent creation, and basic usage example
        """
        if not mcp_config:
            return ""

        # Generate the docstring separately to avoid nested triple quotes
        docstring = f'"""\n{agent_type.capitalize()} agent with MCP integration.\n"""'

        code = f"""{docstring}

from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.models.llm.base import LLMConfig

from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig, MCPTransport

# Create engine configuration
engine = AugLLMConfig(
    llm_config=LLMConfig(
        provider="openai",
        model="gpt-4o-mini"
    ),
    name="{agent_type}_engine"
)

# MCP configuration
mcp_config = {json.dumps(mcp_config.model_dump(), indent=2)}

# Create agent
agent = MCPAgent(
    engine=engine,
    mcp_config=MCPConfig(**mcp_config),
    name="{agent_type}_mcp_agent"
)

# Initialize
await agent.setup()

# Use the agent
result = await agent.arun({{
    "messages": [{{
        "role": "user",
        "content": "Your task here"
    }}]
}})
"""
        return code
