"""Tests for MCP Documentation Agent."""

import pytest

from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.models.llm.base import LLMConfig
from haive.mcp.agents.documentation_agent import MCPDocumentationAgent
from haive.mcp.documentation.doc_loader import MCPDocumentationLoader


class TestMCPDocumentationAgent:
    """Test the MCP Documentation Agent."""

    @pytest.fixture
    def test_engine(self):
        """Create test engine configuration."""
        return AugLLMConfig(
            llm_config=LLMConfig(provider="openai", model="gpt-4o-mini"),
            name="test_doc_engine",
        )

    def test_create_documentation_agent(self, test_engine):
        """Test creating documentation agent."""
        agent = MCPDocumentationAgent(engine=test_engine, name="test_doc_agent")

        assert agent.name == "test_doc_agent"
        assert agent.doc_loader is not None
        assert isinstance(agent.doc_loader, MCPDocumentationLoader)

    def test_create_for_mcp_setup(self, test_engine):
        """Test convenience constructor for setup."""
        agent = MCPDocumentationAgent.create_for_mcp_setup(engine=test_engine)

        assert "Setup" in agent.name
        assert agent.chunking_strategy.value == "semantic"
        assert agent.extract_metadata is True

    def test_create_for_mcp_research(self, test_engine):
        """Test convenience constructor for research."""
        agent = MCPDocumentationAgent.create_for_mcp_research(engine=test_engine)

        assert "Research" in agent.name
        assert agent.processing_strategy.value == "parallel"
        assert agent.enable_embedding is True

    @pytest.mark.asyncio
    async def test_process_mcp_server_cached(self, test_engine):
        """Test processing MCP server from cached docs."""
        agent = MCPDocumentationAgent(engine=test_engine)

        # Create mock documentation
        mock_doc = {
            "metadata": {
                "name": "test/mcp-server",
                "repo_url": "https://github.com/test/mcp-server",
                "description": "Test MCP server",
                "category": "Testing",
                "capabilities": ["test", "demo"],
            },
            "readme_content": """# Test MCP Server
            
## Installation
npm install -g test-mcp-server

## Configuration
export TEST_API_KEY=your_key

## Usage
```javascript
const server = new TestMCPServer();
```
""",
        }

        # Mock the doc loader
        agent.doc_loader._loaded_docs = {"test/mcp-server": mock_doc}

        # Process the server
        result = await agent.process_mcp_server("test/mcp-server", fetch_latest=False)

        assert result["server_name"] == "test/mcp-server"
        assert len(result["setup_instructions"]) > 0
        assert result["mcp_config"] is not None
        assert result["capabilities"] == ["test", "demo"]

    def test_generate_setup_instructions(self, test_engine):
        """Test setup instruction generation."""
        agent = MCPDocumentationAgent(engine=test_engine)

        setup_info = {
            "installation": ["npm install -g mcp-server", "mcp-server init"],
            "configuration": {"API_KEY": "your_key", "PORT": "8080"},
            "dependencies": ["node", "npm"],
        }

        instructions = agent._generate_setup_instructions(setup_info)

        assert "# Installation" in instructions
        assert "npm install -g mcp-server" in instructions
        assert "export API_KEY=your_key" in instructions
        assert "Required: node, npm" in instructions

    def test_create_mcp_config(self, test_engine):
        """Test MCP config creation."""
        agent = MCPDocumentationAgent(engine=test_engine)

        setup_info = {
            "name": "test-server",
            "installation": ["npx -y test-mcp-server"],
            "capabilities": ["test"],
            "category": "Testing",
            "description": "Test server",
        }

        config = agent._create_mcp_config(setup_info)

        assert config.name == "test-server"
        assert config.transport == "stdio"
        assert config.command == "npx"
        assert "-y" in config.args
        assert "test-mcp-server" in config.args

    @pytest.mark.asyncio
    async def test_find_servers_by_capability(self, test_engine):
        """Test finding servers by capability."""
        agent = MCPDocumentationAgent(engine=test_engine)

        # Mock multiple servers
        mock_docs = {
            "server1": {
                "metadata": {"name": "server1", "description": "File operations server"}
            },
            "server2": {
                "metadata": {"name": "server2", "description": "Database server"}
            },
            "server3": {
                "metadata": {"name": "server3", "description": "Another file server"}
            },
        }

        agent.doc_loader._loaded_docs = mock_docs

        # Search for file capability
        results = await agent.find_servers_by_capability("file", limit=2)

        # Should find servers with "file" in description
        assert len(results) <= 2

    def test_generate_implementation_code(self, test_engine):
        """Test implementation code generation."""
        agent = MCPDocumentationAgent(engine=test_engine)

        from haive.mcp.config import MCPConfig, MCPServerConfig

        config = MCPConfig(
            enabled=True,
            servers={
                "test": MCPServerConfig(name="test", transport="stdio", command="test")
            },
        )

        code = agent._generate_implementation_code("research", config)

        assert "research" in code
        assert "MCPAgent" in code
        assert "mcp_config" in code
        assert "await agent.setup()" in code


class TestMCPDocumentationLoader:
    """Test the MCP documentation loader."""

    def test_loader_initialization(self):
        """Test documentation loader initialization."""
        loader = MCPDocumentationLoader()

        assert loader.resources_path is not None
        assert loader.mcp_servers_path.name == "mcp_servers"

    def test_search_by_category(self):
        """Test searching by category."""
        loader = MCPDocumentationLoader()

        # Mock loaded docs
        loader._loaded_docs = {
            "db1": {"metadata": {"category": "Databases"}},
            "fs1": {"metadata": {"category": "File Systems"}},
            "db2": {"metadata": {"category": "Databases"}},
        }

        results = loader.search_servers_by_category("Databases")
        assert len(results) == 2

    def test_extract_installation_steps(self):
        """Test installation step extraction."""
        loader = MCPDocumentationLoader()

        readme = """# MCP Server
        
## Installation
To install the server:
```bash
npm install -g mcp-server
npx mcp-server init
```

## Configuration
Set up your environment...
"""

        steps = loader._extract_installation_steps(readme)

        assert "npm install -g mcp-server" in steps
        assert "npx mcp-server init" in steps

    def test_extract_configuration(self):
        """Test configuration extraction."""
        loader = MCPDocumentationLoader()

        readme = """# Setup
        
Configure the following:
export API_KEY=your_api_key
export PORT=8080
export TOKEN="secret"
"""

        config = loader._extract_configuration(readme)

        assert config["API_KEY"] == "your_api_key"
        assert config["PORT"] == "8080"
        assert config["TOKEN"] == "secret"
