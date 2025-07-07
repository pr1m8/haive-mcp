"""Extension module to add MCP support to AugLLMConfig.

This module provides utilities and mixins to enhance AugLLMConfig with MCP
integration capabilities, allowing seamless use of MCP tools, resources, and
prompts within the Haive agent framework.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Union

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from haive.core.engine.aug_llm import AugLLMConfig
from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.manager import MCPManager

logger = logging.getLogger(__name__)


class MCPResource(BaseModel):
    """Model representing an MCP resource."""
    
    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: str = Field(default="", description="Resource description")
    mime_type: str = Field(default="application/json", description="MIME type")
    content: Optional[Any] = Field(None, description="Cached content")


class MCPPromptTemplate(BaseModel):
    """Model representing an MCP prompt template."""
    
    name: str = Field(..., description="Prompt name")
    description: str = Field(..., description="Prompt description")
    arguments: List[Dict[str, Any]] = Field(default_factory=list, description="Prompt arguments")
    template: str = Field(..., description="Prompt template string")


class MCPToolWrapper(BaseTool):
    """Wrapper to convert MCP tools to Haive-compatible tools.
    
    This wrapper allows MCP tools to be used seamlessly within the Haive
    framework by adapting their interface to match BaseTool expectations.
    """
    
    name: str
    description: str
    mcp_tool: Dict[str, Any]
    mcp_client: Any  # MCPClient instance
    
    def _run(self, **kwargs: Any) -> Any:
        """Synchronous execution (not implemented for MCP)."""
        raise NotImplementedError("MCP tools only support async execution")
    
    async def _arun(self, **kwargs: Any) -> Any:
        """Execute the MCP tool asynchronously.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            result = await self.mcp_client.call_tool(
                self.name,
                arguments=kwargs
            )
            return result
        except Exception as e:
            logger.error(f"Error executing MCP tool {self.name}: {e}")
            raise


class MCPAugLLMConfig(AugLLMConfig):
    """Extended AugLLMConfig with MCP integration support.
    
    This class extends the base AugLLMConfig to add MCP-specific fields and
    functionality, enabling agents to use MCP servers for tools, resources,
    and prompts.
    """
    
    # MCP-specific fields
    mcp_config: Optional[MCPConfig] = Field(
        None,
        description="MCP configuration for server connections"
    )
    
    mcp_resources: Optional[List[MCPResource]] = Field(
        None,
        description="MCP resources available to the agent"
    )
    
    mcp_prompts: Optional[Dict[str, MCPPromptTemplate]] = Field(
        None,
        description="MCP prompt templates"
    )
    
    mcp_manager: Optional[MCPManager] = Field(
        None,
        description="MCP manager instance (not serialized)",
        exclude=True
    )
    
    # Control flags
    auto_discover_mcp_tools: bool = Field(
        True,
        description="Automatically discover and add MCP tools"
    )
    
    inject_mcp_resources: bool = Field(
        True,
        description="Inject MCP resources into agent context"
    )
    
    use_mcp_prompts: bool = Field(
        True,
        description="Use MCP prompts to enhance system prompts"
    )
    
    async def setup_mcp(self) -> None:
        """Initialize MCP integration.
        
        Sets up the MCP manager, discovers tools, loads resources, and
        configures prompts based on the MCP configuration.
        """
        if not self.mcp_config or not self.mcp_config.enabled:
            logger.info("MCP not enabled or configured")
            return
        
        try:
            # Create MCP manager
            self.mcp_manager = MCPManager(self.mcp_config)
            await self.mcp_manager.initialize()
            
            # Discover and wrap tools
            if self.auto_discover_mcp_tools:
                await self._discover_mcp_tools()
            
            # Load resources
            if self.inject_mcp_resources:
                await self._load_mcp_resources()
            
            # Load prompts
            if self.use_mcp_prompts:
                await self._load_mcp_prompts()
                
            logger.info("MCP integration setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up MCP integration: {e}")
            raise
    
    async def _discover_mcp_tools(self) -> None:
        """Discover and wrap MCP tools as Haive tools."""
        if not self.mcp_manager:
            return
        
        wrapped_tools = []
        
        for server_name, client in self.mcp_manager.clients.items():
            try:
                # Get tools from server
                tools = await client.list_tools()
                
                for tool in tools:
                    # Create wrapper
                    wrapper = MCPToolWrapper(
                        name=f"{server_name}_{tool['name']}",
                        description=tool.get('description', ''),
                        mcp_tool=tool,
                        mcp_client=client
                    )
                    wrapped_tools.append(wrapper)
                    
                logger.info(f"Discovered {len(tools)} tools from {server_name}")
                
            except Exception as e:
                logger.error(f"Error discovering tools from {server_name}: {e}")
        
        # Add wrapped tools to the config
        if wrapped_tools:
            if not self.tools:
                self.tools = []
            self.tools.extend([tool.name for tool in wrapped_tools])
            
            # Store tool instances (would need proper registry integration)
            # For now, log the discovery
            logger.info(f"Added {len(wrapped_tools)} MCP tools to configuration")
    
    async def _load_mcp_resources(self) -> None:
        """Load MCP resources from connected servers."""
        if not self.mcp_manager:
            return
        
        self.mcp_resources = []
        
        for server_name, client in self.mcp_manager.clients.items():
            try:
                # List resources
                resources = await client.list_resources()
                
                for resource in resources:
                    mcp_resource = MCPResource(
                        uri=resource['uri'],
                        name=resource.get('name', resource['uri']),
                        description=resource.get('description', ''),
                        mime_type=resource.get('mimeType', 'application/json')
                    )
                    self.mcp_resources.append(mcp_resource)
                    
                logger.info(f"Loaded {len(resources)} resources from {server_name}")
                
            except Exception as e:
                logger.error(f"Error loading resources from {server_name}: {e}")
    
    async def _load_mcp_prompts(self) -> None:
        """Load MCP prompts from connected servers."""
        if not self.mcp_manager:
            return
        
        self.mcp_prompts = {}
        
        for server_name, client in self.mcp_manager.clients.items():
            try:
                # List prompts
                prompts = await client.list_prompts()
                
                for prompt in prompts:
                    template = MCPPromptTemplate(
                        name=prompt['name'],
                        description=prompt.get('description', ''),
                        arguments=prompt.get('arguments', []),
                        template=""  # Would need to fetch actual template
                    )
                    self.mcp_prompts[f"{server_name}_{prompt['name']}"] = template
                    
                logger.info(f"Loaded {len(prompts)} prompts from {server_name}")
                
            except Exception as e:
                logger.error(f"Error loading prompts from {server_name}: {e}")
    
    def enhance_system_prompt_with_mcp(self) -> str:
        """Enhance the system prompt with MCP information.
        
        Returns:
            Enhanced system prompt including MCP resources and capabilities
        """
        base_prompt = self.system_message or ""
        
        if not self.mcp_config or not self.mcp_config.enabled:
            return base_prompt
        
        enhancements = []
        
        # Add resource information
        if self.mcp_resources:
            resource_section = "\n## Available MCP Resources:\n"
            for resource in self.mcp_resources:
                resource_section += f"- {resource.name}: {resource.description} ({resource.uri})\n"
            enhancements.append(resource_section)
        
        # Add MCP prompt information
        if self.mcp_prompts:
            prompt_section = "\n## Available MCP Operations:\n"
            for name, prompt in self.mcp_prompts.items():
                prompt_section += f"- {name}: {prompt.description}\n"
            enhancements.append(prompt_section)
        
        # Add MCP tool information (already handled by tool discovery)
        
        if enhancements:
            return base_prompt + "\n" + "\n".join(enhancements)
        
        return base_prompt
    
    async def get_mcp_resource_content(self, uri: str) -> Any:
        """Fetch content for an MCP resource.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        if not self.mcp_manager:
            raise ValueError("MCP manager not initialized")
        
        # Find which server handles this resource
        for server_name, client in self.mcp_manager.clients.items():
            try:
                content = await client.read_resource(uri)
                
                # Update cached content
                for resource in self.mcp_resources or []:
                    if resource.uri == uri:
                        resource.content = content
                        break
                
                return content
                
            except Exception as e:
                logger.debug(f"Server {server_name} cannot handle resource {uri}: {e}")
                continue
        
        raise ValueError(f"No MCP server can handle resource: {uri}")


def extend_aug_llm_config_for_mcp(
    base_config: AugLLMConfig,
    mcp_config: MCPConfig
) -> MCPAugLLMConfig:
    """Utility function to extend an existing AugLLMConfig with MCP support.
    
    Args:
        base_config: Existing AugLLMConfig instance
        mcp_config: MCP configuration to add
        
    Returns:
        MCPAugLLMConfig with MCP support added
    """
    # Convert base config to dict
    config_dict = base_config.model_dump()
    
    # Add MCP configuration
    config_dict['mcp_config'] = mcp_config
    
    # Create extended config
    return MCPAugLLMConfig(**config_dict)


async def create_mcp_enabled_aug_config(
    name: str,
    model: str = "gpt-4o-mini",
    mcp_servers: Dict[str, MCPServerConfig] = None,
    **kwargs
) -> MCPAugLLMConfig:
    """Factory function to create an MCP-enabled AugLLMConfig.
    
    Args:
        name: Configuration name
        model: LLM model to use
        mcp_servers: Dictionary of MCP server configurations
        **kwargs: Additional AugLLMConfig parameters
        
    Returns:
        Initialized MCPAugLLMConfig with MCP integration
    """
    # Create MCP config
    mcp_config = MCPConfig(
        enabled=True,
        servers=mcp_servers or {},
        auto_discover=False
    )
    
    # Create extended config
    config = MCPAugLLMConfig(
        name=name,
        llm_config={"provider": "openai", "model": model},
        mcp_config=mcp_config,
        **kwargs
    )
    
    # Set up MCP integration
    await config.setup_mcp()
    
    # Enhance system prompt
    config.system_message = config.enhance_system_prompt_with_mcp()
    
    return config