"""Transferable MCP agent implementation with resource/prompt/tool sharing capabilities.

This module provides an advanced MCP agent that supports sharing and transferring
capabilities between agent instances. It enables collaborative workflows where multiple
agents can share MCP clients, tools, resources, and prompts for efficient distributed
processing.

The TransferableMCPAgent extends the basic MCPAgent with:
    - Shared MCP client pools for resource efficiency
    - Tool transfer mechanisms between agents
    - Resource delegation and access control
    - Prompt sharing for consistent behavior
    - Collaborative session management
    - Transfer tracking and auditing

Classes:
    TransferableMCPAgent: Agent with MCP sharing and transfer capabilities

Functions:
    create_collaborative_agents: Factory for creating collaborative agent groups

Example:
    Creating and using transferable agents::
    
        from haive.mcp.agents import TransferableMCPAgent
        from haive.mcp.config import MCPConfig
        
        # Create collaborative agents with shared client
        agents = TransferableMCPAgent.create_collaborative_agents(
            engine=engine,
            mcp_config=mcp_config,
            num_agents=3,
            shared_client=True
        )
        
        # Initialize all agents
        for agent in agents:
            await agent.setup()
        
        # Transfer tools from first agent to others
        leader = agents[0]
        for follower in agents[1:]:
            count = await leader.transfer_all_tools_to_agent(follower)
            print(f"Transferred {count} tools to {follower.name}")
        
        # Collaborate on a task
        results = await leader.collaborate_with_agents(
            agents[1:],
            task="Analyze repository structure"
        )

Note:
    Shared clients reduce resource usage but require careful synchronization.
    Transfer operations are tracked for auditing and debugging purposes.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, ClassVar, Dict, List, Optional, Set

from haive.agents.simple import SimpleAgent
from pydantic import Field, PrivateAttr

from haive.mcp.config import MCPConfig
from haive.mcp.mixins.mcp_mixin import MCPMixin


class TransferableMCPAgent(MCPMixin, SimpleAgent):
    """An MCP-enabled agent with enhanced transferability features.
    
    TransferableMCPAgent extends SimpleAgent with sophisticated sharing and
    transfer mechanisms for MCP resources. It enables efficient multi-agent
    workflows by allowing agents to share clients, transfer tools, and
    collaborate on tasks.
    
    The agent supports:
        - Sharing MCP clients between agents to reduce resource usage
        - Transferring resources/prompts/tools to other agents
        - Session-based collaboration with shared state
        - Dynamic capability delegation for flexible workflows
        - Transfer tracking and auditing
    
    Attributes:
        share_client: Whether to share MCP client with other agents
        client_pool_key: Key for shared client pool identification
        _transferred_tools: Set of tool names transferred to other agents
        _transferred_resources: Set of resource URIs delegated
        _transferred_prompts: Set of prompts shared with other agents
    
    Class Attributes:
        _shared_mcp_clients: Pool of shared MCP client instances
        _shared_sessions: Pool of shared MCP sessions
    
    Example:
        Basic usage with tool transfer::
        
            # Create source agent with tools
            source = TransferableMCPAgent(
                engine=engine,
                mcp_config=mcp_config,
                name="source_agent"
            )
            await source.setup()
            
            # Create target agent
            target = TransferableMCPAgent(
                engine=engine,
                mcp_config=minimal_config,
                name="target_agent"
            )
            await target.setup()
            
            # Transfer specific tool
            success = await source.transfer_tool_to_agent(
                target,
                "filesystem_read_file"
            )
            
            # Now target can use the transferred tool
            result = await target.call_mcp_tool(
                "filesystem_read_file",
                {"path": "/path/to/file"}
            )
    "
    
    # Class-level shared resources
    _shared_mcp_clients: ClassVar[Dict[str, Any]] = {}
    _shared_sessions: ClassVar[Dict[str, Any]] = {}
    
    # Instance configuration
    share_client: bool = Field(
        default=True,
        description="Whether to share MCP client with other agents"
    )
    client_pool_key: Optional[str] = Field(
        default=None,
        description="Key for shared client pool (defaults to mcp_config hash)"
    )
    
    # Transfer tracking
    _transferred_tools: Set[str] = PrivateAttr(default_factory=set)
    _transferred_resources: Set[str] = PrivateAttr(default_factory=set)
    _transferred_prompts: Set[str] = PrivateAttr(default_factory=set)
    
    async def initialize_mcp(self) -> bool:
        """Initialize MCP with client sharing support.
        
        This method extends the base initialization to support client sharing
        between agent instances. When share_client is True, it will attempt
        to reuse an existing client from the shared pool before creating a
        new one.
        
        The client pool key is determined by:
            1. Explicit client_pool_key if provided
            2. Hash of the MCP configuration for automatic grouping
        
        Returns:
            bool: True if initialization successful, False otherwise
            
        Raises:
            Exception: Logged but not raised, ensures graceful degradation
            
        Example:
            Manual initialization with shared client::
            
                agent1 = TransferableMCPAgent(
                    engine=engine,
                    mcp_config=config,
                    share_client=True,
                    client_pool_key="my_shared_pool"
                )
                await agent1.initialize_mcp()  # Creates new client
                
                agent2 = TransferableMCPAgent(
                    engine=engine,
                    mcp_config=config,
                    share_client=True,
                    client_pool_key="my_shared_pool"
                )
                await agent2.initialize_mcp()  # Reuses agent1's client
        """
        if not self.mcp_config or not self.mcp_config.enabled:
            return False
        
        # Check for shared client
        if self.share_client:
            pool_key = self.client_pool_key or self._get_config_hash()
            
            if pool_key in self._shared_mcp_clients:
                # Reuse existing client
                self._mcp_client = self._shared_mcp_clients[pool_key]
                self._mcp_initialized = True
                
                # Sync tools and resources from shared client
                await self._sync_from_shared_client()
                return True
        
        # Initialize new client
        success = await super().initialize_mcp()
        
        if success and self.share_client:
            # Share the client
            pool_key = self.client_pool_key or self._get_config_hash()
            self._shared_mcp_clients[pool_key] = self._mcp_client
        
        return success
    
    def _get_config_hash(self) -> str:
        """Generate a hash key for the MCP configuration.
        
        Creates a deterministic hash of the MCP configuration to automatically
        group agents with identical configurations. This enables automatic
        client sharing without explicit pool keys.
        
        Returns:
            str: MD5 hash of the configuration JSON
            
        Note:
            The hash is based on the sorted JSON representation to ensure
            consistency across different dictionary orderings.
        """
        import hashlib
        import json
        
        config_str = json.dumps(self.mcp_config.model_dump(), sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    async def _sync_from_shared_client(self):
        """Sync tools and resources from shared client.
        
        When reusing a shared client, this method ensures the agent's local
        state is synchronized with the tools and resources available from
        the shared client. This maintains consistency across all agents
        using the same client.
        
        The sync process:
            1. Re-discovers all available tools
            2. Updates local tool registry
            3. Maintains tool references for the agent
            
        Note:
            This is called automatically when reusing a shared client.
        """
        if self._mcp_client:
            # Re-discover tools to sync state
            await self._discover_tools()
    
    async def transfer_tool_to_agent(
        self,
        agent: "TransferableMCPAgent",
        tool_name: str
    ) -> bool:
        """Transfer a specific tool to another agent.
        
        Transfers a single MCP tool from this agent to another agent. The tool
        reference is shared, not copied, so both agents will have access to
        the same tool instance. The transfer is tracked for auditing.
        
        Args:
            agent: Target agent to receive the tool
            tool_name: Name of the tool to transfer (e.g., "filesystem_read_file")
            
        Returns:
            bool: True if transfer successful, False if tool not found
            
        Raises:
            RuntimeError: If target agent initialization fails
            
        Example:
            Transferring a specific tool::
            
                # Transfer GitHub issue creation tool
                success = await source_agent.transfer_tool_to_agent(
                    target_agent,
                    "github_create_issue"
                )
                
                if success:
                    # Target can now create GitHub issues
                    await target_agent.call_mcp_tool(
                        "github_create_issue",
                        {"title": "New feature", "body": "Description"}
                    )
        """
        if tool_name not in self._mcp_tools:
            return False
        
        # Ensure target agent is initialized
        if not agent._mcp_initialized:
            await agent.initialize_mcp()
        
        # Transfer the tool
        tool = self._mcp_tools[tool_name]
        agent._mcp_tools[tool_name] = tool
        
        # Update agent's tool list if it has one
        if hasattr(agent, 'tools') and isinstance(agent.tools, list):
            if tool not in agent.tools:
                agent.tools.append(tool)
        
        # Track transfer
        self._transferred_tools.add(tool_name)
        
        return True
    
    async def transfer_all_tools_to_agent(
        self,
        agent: "TransferableMCPAgent"
    ) -> int:
        """Transfer all tools to another agent.
        
        Bulk transfer operation that shares all available MCP tools from this
        agent to the target agent. Useful for creating worker agents with
        full capabilities.
        
        Args:
            agent: Target agent to receive all tools
            
        Returns:
            int: Number of tools successfully transferred
            
        Example:
            Creating a fully-equipped worker::
            
                # Leader has all MCP servers configured
                leader = TransferableMCPAgent(
                    engine=engine,
                    mcp_config=full_config,
                    name="leader"
                )
                await leader.setup()
                
                # Worker starts with minimal config
                worker = TransferableMCPAgent(
                    engine=engine,
                    mcp_config=minimal_config,
                    name="worker"
                )
                await worker.setup()
                
                # Transfer all tools to worker
                count = await leader.transfer_all_tools_to_agent(worker)
                print(f"Worker now has {count} additional tools")
        """
        count = 0
        for tool_name in self._mcp_tools:
            if await self.transfer_tool_to_agent(agent, tool_name):
                count += 1
        return count
    
    async def delegate_resource_access(
        self,
        agent: "TransferableMCPAgent",
        server_name: str,
        resource_uris: Optional[List[str]] = None
    ) -> List[Any]:
        """Delegate resource access to another agent.
        
        Retrieves resources from an MCP server on behalf of another agent.
        This is useful when one agent has access to resources that another
        agent needs but cannot directly access.
        
        Args:
            agent: Target agent requesting resource access
            server_name: Name of the MCP server providing resources
            resource_uris: Specific resource URIs to retrieve, or None for all
            
        Returns:
            List[Any]: Resources retrieved from the server
            
        Raises:
            RuntimeError: If MCP client not initialized
            ValueError: If server not found
            
        Example:
            Delegating file access::
            
                # Admin agent has filesystem access
                admin = TransferableMCPAgent(
                    engine=engine,
                    mcp_config=admin_config,
                    name="admin"
                )
                
                # Worker needs specific files
                files = await admin.delegate_resource_access(
                    worker,
                    "filesystem",
                    ["file:///config/settings.json", "file:///data/users.csv"]
                )
                
                # Worker can now process the files
                for file in files:
                    print(f"Processing {file.uri}: {file.content}")
        """
        # Ensure both agents are initialized
        if not self._mcp_initialized:
            await self.initialize_mcp()
        if not agent._mcp_initialized:
            await agent.initialize_mcp()
        
        # Get resources
        resources = await self.get_mcp_resources(server_name, resource_uris)
        
        # Track delegation
        self._transferred_resources.update(resource_uris or [])
        
        return resources
    
    async def share_prompt_with_agent(
        self,
        agent: "TransferableMCPAgent",
        server_name: str,
        prompt_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """Share a prompt with another agent.
        
        Retrieves a prompt from an MCP server and shares it with another agent.
        This enables consistent prompting across multiple agents for coordinated
        behavior.
        
        Args:
            agent: Target agent to receive the prompt
            server_name: Name of the MCP server providing the prompt
            prompt_name: Name of the prompt to retrieve
            arguments: Optional arguments to customize the prompt
            
        Returns:
            List[Any]: Prompt messages that can be used by the target agent
            
        Raises:
            RuntimeError: If MCP client not initialized
            ValueError: If server or prompt not found
            
        Example:
            Sharing a code review prompt::
            
                # Lead agent gets specialized prompt
                review_prompt = await lead_agent.share_prompt_with_agent(
                    reviewer_agent,
                    "code_assistant",
                    "code_review_prompt",
                    {"language": "python", "style_guide": "PEP8"}
                )
                
                # Reviewer uses the shared prompt
                result = await reviewer_agent.arun({
                    "messages": review_prompt + [
                        {"role": "user", "content": "Review this code: ..."}
                    ]
                })
        """
        # Get the prompt
        prompt = await self.get_mcp_prompt(server_name, prompt_name, arguments)
        
        # Track sharing
        self._transferred_prompts.add(f"{server_name}:{prompt_name}")
        
        return prompt
    
    @asynccontextmanager
    async def shared_mcp_session(
        self,
        session_key: str,
        server_name: Optional[str] = None
    ):
        """Create or join a shared MCP session.
        
        Context manager that provides shared MCP sessions for coordinated
        operations between multiple agents. Sessions are identified by unique
        keys and automatically cleaned up when all agents exit.
        
        Args:
            session_key: Unique identifier for the shared session
            server_name: Optional specific server for the session
            
        Yields:
            Any: Shared MCP session instance
            
        Example:
            Coordinated file operations::
            
                # Multiple agents work on the same project
                async with agent1.shared_mcp_session("project_x", "filesystem") as session:
                    # Agent 1 creates project structure
                    await session.call_tool("create_directory", {"path": "/project_x"})
                    
                    # Agent 2 joins the same session
                    async with agent2.shared_mcp_session("project_x", "filesystem") as session2:
                        # Both agents share the same session state
                        await session2.call_tool("write_file", {
                            "path": "/project_x/README.md",
                            "content": "# Project X"
                        })
        """
        if session_key in self._shared_sessions:
            # Join existing session
            yield self._shared_sessions[session_key]
        else:
            # Create new shared session
            async with self.mcp_session(server_name) as session:
                self._shared_sessions[session_key] = session
                try:
                    yield session
                finally:
                    # Clean up shared session
                    del self._shared_sessions[session_key]
    
    async def collaborate_with_agents(
        self,
        agents: List["TransferableMCPAgent"],
        task: str
    ) -> Dict[str, Any]:
        """Collaborate with multiple agents on a task.
        
        Orchestrates collaboration by sharing tools and resources with a group
        of agents for a specific task. This method sets up the collaborative
        environment but does not execute the task itself.
        
        Args:
            agents: List of agents to collaborate with
            task: Description of the collaborative task
            
        Returns:
            Dict[str, Any]: Collaboration setup results including:
                - task: The task description
                - agents: List of agent details and tools received
                - shared_tools: Total number of tools shared
                - shared_resources: Total number of resources shared
                
        Example:
            Setting up a collaborative analysis::
            
                # Leader agent has all necessary tools
                leader = TransferableMCPAgent(
                    engine=engine,
                    mcp_config=full_config,
                    name="leader"
                )
                
                # Create worker agents
                workers = TransferableMCPAgent.create_collaborative_agents(
                    engine=engine,
                    mcp_config=minimal_config,
                    num_agents=3
                )
                
                # Set up collaboration
                results = await leader.collaborate_with_agents(
                    workers,
                    "Analyze codebase for security vulnerabilities"
                )
                
                # Workers now have tools to perform the analysis
                for worker in workers:
                    await worker.arun({
                        "messages": [{"role": "user", "content": f"Analyze: {task}"}]
                    })
        """
        results = {
            "task": task,
            "agents": [],
            "shared_tools": 0,
            "shared_resources": 0
        }
        
        # Share tools with all agents
        for agent in agents:
            tools_shared = await self.transfer_all_tools_to_agent(agent)
            results["shared_tools"] += tools_shared
            results["agents"].append({
                "name": agent.name,
                "tools_received": tools_shared
            })
        
        return results
    
    def get_transfer_status(self) -> Dict[str, Any]:
        """Get status of all transfers.
        
        Returns a summary of all transfer operations performed by this agent,
        useful for auditing and debugging collaborative workflows.
        
        Returns:
            Dict[str, Any]: Transfer status including:
                - transferred_tools: List of tool names transferred
                - transferred_resources: List of resource URIs delegated
                - transferred_prompts: List of prompts shared
                - shared_client: Whether client sharing is enabled
                - client_pool_key: Key used for client pooling
                
        Example:
            Checking transfer history::
            
                status = agent.get_transfer_status()
                print(f"Tools transferred: {len(status['transferred_tools'])}")
                print(f"Resources delegated: {len(status['transferred_resources'])}")
                
                # List all transferred tools
                for tool in status['transferred_tools']:
                    print(f"  - {tool}")
        """
        return {
            "transferred_tools": list(self._transferred_tools),
            "transferred_resources": list(self._transferred_resources),
            "transferred_prompts": list(self._transferred_prompts),
            "shared_client": self.share_client,
            "client_pool_key": self.client_pool_key
        }
    
    @classmethod
    def create_collaborative_agents(
        cls,
        engine: Any,
        mcp_config: MCPConfig,
        num_agents: int = 2,
        shared_client: bool = True
    ) -> List["TransferableMCPAgent"]:
        """Create multiple collaborative agents with shared MCP client.
        
        Factory method that creates a group of agents configured for
        collaboration. When shared_client is True, all agents will share
        the same MCP client instance for resource efficiency.
        
        Args:
            engine: LLM engine configuration (AugLLMConfig)
            mcp_config: MCP configuration to use for all agents
            num_agents: Number of agents to create (default: 2)
            shared_client: Whether agents should share MCP client (default: True)
            
        Returns:
            List[TransferableMCPAgent]: List of configured collaborative agents
            
        Raises:
            ValueError: If num_agents < 1
            
        Example:
            Creating a collaborative team::
            
                from haive.mcp.config import MCPConfig, MCPServerConfig
                
                # Configure MCP with multiple servers
                config = MCPConfig(
                    enabled=True,
                    servers={
                        "filesystem": MCPServerConfig(...),
                        "github": MCPServerConfig(...),
                        "database": MCPServerConfig(...)
                    }
                )
                
                # Create team of 5 collaborative agents
                team = TransferableMCPAgent.create_collaborative_agents(
                    engine=engine,
                    mcp_config=config,
                    num_agents=5,
                    shared_client=True  # Share resources
                )
                
                # Initialize all agents
                for agent in team:
                    await agent.setup()
                
                # Agents can now work together efficiently
                leader = team[0]
                workers = team[1:]
                
                # Leader coordinates the team
                await leader.collaborate_with_agents(
                    workers,
                    "Process customer data pipeline"
                )
        """
        agents = []
        pool_key = f"collaborative_{id(mcp_config)}"
        
        for i in range(num_agents):
            agent = cls(
                engine=engine,
                mcp_config=mcp_config,
                name=f"collaborative_agent_{i}",
                share_client=shared_client,
                client_pool_key=pool_key
            )
            agents.append(agent)
        
        return agents