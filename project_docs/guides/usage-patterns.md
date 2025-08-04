# MCP Usage Patterns

**Common patterns and scenarios for dynamic MCP integration with Haive agents**

## 🎯 Overview

This guide covers the most common usage patterns for integrating MCP capabilities into your Haive agents, from simple static configurations to advanced dynamic discovery workflows.

## 🚀 Basic Usage Patterns

### Pattern 1: Static MCP Configuration

**When to use**: Production environments with known, stable tool requirements.

```python
from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.core.engine.aug_llm import AugLLMConfig

# Define static server configuration
config = MCPConfig(
    servers={
        "filesystem": MCPServerConfig(
            name="filesystem",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
        ),
        "postgres": MCPServerConfig(
            name="postgres",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres"],
            env={"DATABASE_URL": "postgresql://localhost/mydb"}
        )
    }
)

# Create agent with static configuration
agent = MCPAgent(
    engine=AugLLMConfig(temperature=0.3),
    mcp_config=config
)

await agent.setup()

# Agent has access to filesystem and database tools
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Read the config file and update the database"
    }]
})
```

**Benefits**:

- Predictable tool set
- Fast startup (no discovery overhead)
- Production-ready reliability
- Clear dependency management

**Use Cases**:

- Production deployments
- Known workflows
- Regulated environments
- Performance-critical applications

### Pattern 2: Dynamic Discovery with Approval

**When to use**: Interactive environments where users may have varying tool needs.

```python
from haive.mcp.agents import IntelligentMCPAgent

async def approval_handler(request):
    """Custom approval logic for server installations."""
    print(f"🔔 Install {request.recommendation.server_name}?")
    print(f"Reason: {request.recommendation.reason}")
    print(f"Capabilities: {', '.join(request.recommendation.capabilities)}")

    response = input("Approve? (y/n): ")
    return response.lower() == 'y'

# Create dynamic agent with approval
agent = IntelligentMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True,
    require_approval=True,
    approval_callback=approval_handler
)

await agent.setup()

# Agent analyzes request and asks for approval to install needed servers
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Search for recent AI papers and create a summary spreadsheet"
    }]
})
# May prompt to install: web-search server, spreadsheet server
```

**Benefits**:

- Human oversight and control
- Adaptive to user needs
- Safe exploration of new tools
- Educational (shows what tools are needed)

**Use Cases**:

- Research and development
- Interactive AI assistants
- Learning environments
- Exploratory data analysis

### Pattern 3: Fully Autonomous Discovery

**When to use**: Trusted environments where agents can install tools automatically.

```python
# Fully autonomous agent
agent = IntelligentMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True,
    require_approval=False  # Automatic installation
)

await agent.setup()

# Agent automatically installs any needed servers
result = await agent.arun({
    "messages": [{
        "role": "user",
        "content": "Monitor system performance and alert if CPU > 80%"
    }]
})
# Automatically installs: system-monitoring server, notification server
```

**Benefits**:

- Zero-friction tool acquisition
- Fully adaptive workflows
- Maximum automation
- Rapid prototyping

**Use Cases**:

- Trusted development environments
- Personal AI assistants
- Automated workflows
- Rapid prototyping

## 🔧 Advanced Usage Patterns

### Pattern 4: Conditional Tool Loading

**When to use**: Optimize resource usage by loading tools only when needed.

```python
class ConditionalMCPAgent(IntelligentMCPAgent):
    """Agent that conditionally loads tools based on context."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tool_usage_patterns = {}

    async def _analyze_capability_needs(self, user_message: str) -> list[str]:
        """Enhanced capability analysis with conditional loading."""
        base_capabilities = await super()._analyze_capability_needs(user_message)

        # Add contextual capabilities
        context_capabilities = []

        # Time-based capabilities
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Business hours
            context_capabilities.extend(["email", "calendar", "slack"])

        # User pattern-based capabilities
        user_id = self.get_user_id(user_message)
        if user_id in self.tool_usage_patterns:
            frequent_tools = self.tool_usage_patterns[user_id]
            context_capabilities.extend(frequent_tools)

        return base_capabilities + context_capabilities

# Usage
agent = ConditionalMCPAgent(
    engine=AugLLMConfig(),
    auto_discover=True,
    require_approval=False
)
```

### Pattern 5: Multi-Agent Tool Sharing

**When to use**: Multiple agents need to share expensive or limited resources.

```python
from haive.mcp.agents import TransferableMCPAgent
from haive.agents.multi import MultiAgent

async def create_collaborative_agents():
    """Create agents that share tools efficiently."""

    # Create primary agent with expensive tools
    primary_agent = TransferableMCPAgent(
        name="primary",
        engine=AugLLMConfig(),
        mcp_config=MCPConfig(
            servers={
                "expensive_api": MCPServerConfig(
                    name="expensive_api",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@company/expensive-api-server"],
                    env={"API_KEY": "expensive-key"}
                )
            }
        )
    )

    # Create secondary agents
    research_agent = TransferableMCPAgent(
        name="researcher",
        engine=AugLLMConfig(),
        mcp_config=basic_tools_config
    )

    analysis_agent = TransferableMCPAgent(
        name="analyst",
        engine=AugLLMConfig(),
        mcp_config=basic_tools_config
    )

    # Setup all agents
    await primary_agent.setup()
    await research_agent.setup()
    await analysis_agent.setup()

    # Share expensive tools
    await primary_agent.transfer_tools_to_agent(
        research_agent,
        tool_names=["expensive_api_call"]
    )

    await primary_agent.transfer_tools_to_agent(
        analysis_agent,
        tool_names=["expensive_api_call"]
    )

    # Create multi-agent system
    return MultiAgent(
        agents={
            "primary": primary_agent,
            "research": research_agent,
            "analysis": analysis_agent
        },
        execution_mode="parallel"
    )
```

### Pattern 6: Hot-Reload Development Workflow

**When to use**: Development environments where tools change frequently.

```python
from haive.mcp.manager import MCPManager

class DevelopmentMCPAgent(MCPAgent):
    """Agent optimized for development with hot-reload capabilities."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dev_mode = True
        self.auto_reload_interval = 5.0

    async def setup(self):
        await super().setup()
        if self.dev_mode:
            # Start auto-reload monitoring
            asyncio.create_task(self._monitor_for_changes())

    async def _monitor_for_changes(self):
        """Monitor for server configuration changes."""
        while True:
            try:
                # Check for config file changes
                if self._config_changed():
                    print("🔄 Configuration changed, reloading servers...")
                    await self._reload_all_servers()

                await asyncio.sleep(self.auto_reload_interval)

            except Exception as e:
                print(f"Error monitoring changes: {e}")
                await asyncio.sleep(self.auto_reload_interval)

    async def _reload_all_servers(self):
        """Reload all MCP servers."""
        for server_name in self.mcp_manager.get_server_names():
            try:
                await self.mcp_manager.reload_server(server_name)
                print(f"✅ Reloaded {server_name}")
            except Exception as e:
                print(f"❌ Failed to reload {server_name}: {e}")

# Usage in development
dev_agent = DevelopmentMCPAgent(
    engine=AugLLMConfig(),
    mcp_config=dev_config
)
```

## 🎨 Domain-Specific Patterns

### Pattern 7: Research Assistant

**When to use**: Academic research, market research, competitive analysis.

```python
class ResearchAssistantAgent(IntelligentMCPAgent):
    """Specialized agent for research workflows."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.research_capabilities = [
            "web_search", "academic_search", "document_analysis",
            "pdf_extraction", "citation_management", "spreadsheet",
            "note_taking", "bibliography"
        ]

    async def _analyze_capability_needs(self, user_message: str) -> list[str]:
        """Research-focused capability analysis."""
        base_capabilities = await super()._analyze_capability_needs(user_message)

        # Always include core research capabilities
        return list(set(base_capabilities + self.research_capabilities))

    async def conduct_research(self, topic: str, depth: str = "standard"):
        """Specialized research workflow."""
        workflow_steps = [
            f"Search for recent papers on '{topic}'",
            f"Analyze top 10 results and extract key findings",
            f"Create summary document with citations",
            f"Generate bibliography in APA format"
        ]

        results = []
        for step in workflow_steps:
            result = await self.arun({"messages": [{"role": "user", "content": step}]})
            results.append(result)

        return self._compile_research_report(results)

# Usage
research_agent = ResearchAssistantAgent(
    engine=AugLLMConfig(temperature=0.3),
    auto_discover=True,
    require_approval=False
)

report = await research_agent.conduct_research("AI safety alignment", depth="comprehensive")
```

### Pattern 8: Data Analysis Pipeline

**When to use**: Data science workflows, business intelligence, reporting.

```python
class DataAnalysisAgent(IntelligentMCPAgent):
    """Agent specialized for data analysis workflows."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_capabilities = [
            "database", "sql", "csv", "excel", "json",
            "pandas", "numpy", "plotting", "statistics",
            "machine_learning", "visualization"
        ]

    async def analyze_dataset(self, data_source: str, analysis_type: str):
        """Complete data analysis workflow."""

        # Step 1: Data ingestion
        await self.arun({
            "messages": [{
                "role": "user",
                "content": f"Load data from {data_source} and show basic statistics"
            }]
        })

        # Step 2: Analysis based on type
        if analysis_type == "exploratory":
            analysis_prompt = "Perform exploratory data analysis with visualizations"
        elif analysis_type == "predictive":
            analysis_prompt = "Build predictive model and evaluate performance"
        else:
            analysis_prompt = f"Perform {analysis_type} analysis"

        result = await self.arun({
            "messages": [{"role": "user", "content": analysis_prompt}]
        })

        # Step 3: Generate report
        report = await self.arun({
            "messages": [{
                "role": "user",
                "content": "Create executive summary and save results to presentation format"
            }]
        })

        return report

# Usage
data_agent = DataAnalysisAgent(
    engine=AugLLMConfig(),
    auto_discover=True,
    require_approval=True  # Approval for database connections
)
```

### Pattern 9: DevOps Automation

**When to use**: Infrastructure management, deployment automation, monitoring.

```python
class DevOpsAgent(IntelligentMCPAgent):
    """Agent for DevOps and infrastructure automation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.devops_capabilities = [
            "docker", "kubernetes", "terraform", "aws", "azure",
            "monitoring", "logging", "alerting", "ci_cd",
            "git", "ssh", "shell", "database_admin"
        ]

    async def deploy_application(self, app_config: dict):
        """Complete application deployment workflow."""

        deployment_steps = [
            "Validate application configuration",
            "Build Docker image",
            "Push to container registry",
            "Update Kubernetes manifests",
            "Apply deployment to cluster",
            "Verify deployment health",
            "Update monitoring dashboards"
        ]

        results = {}
        for step in deployment_steps:
            try:
                result = await self.arun({
                    "messages": [{
                        "role": "user",
                        "content": f"{step} for application: {app_config['name']}"
                    }]
                })
                results[step] = {"status": "success", "result": result}

            except Exception as e:
                results[step] = {"status": "error", "error": str(e)}
                # Rollback on failure
                await self._rollback_deployment(app_config, results)
                break

        return results

# Usage
devops_agent = DevOpsAgent(
    engine=AugLLMConfig(),
    auto_discover=True,
    require_approval=True  # Approval for infrastructure changes
)
```

## 🔄 Workflow Patterns

### Pattern 10: Sequential Tool Discovery

**When to use**: Complex workflows where tools are needed in sequence.

```python
async def sequential_discovery_workflow():
    """Workflow that discovers tools as needed."""

    agent = IntelligentMCPAgent(
        engine=AugLLMConfig(),
        auto_discover=True,
        require_approval=False
    )

    await agent.setup()

    # Phase 1: Data collection (discovers web search tools)
    await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Collect recent news about electric vehicles"
        }]
    })

    # Phase 2: Data processing (discovers spreadsheet tools)
    await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Organize the collected data into a structured spreadsheet"
        }]
    })

    # Phase 3: Analysis (discovers analysis tools)
    await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Analyze trends and create visualizations"
        }]
    })

    # Phase 4: Reporting (discovers presentation tools)
    final_result = await agent.arun({
        "messages": [{
            "role": "user",
            "content": "Create executive presentation with key findings"
        }]
    })

    return final_result
```

### Pattern 11: Parallel Tool Usage

**When to use**: Independent tasks that can be parallelized.

```python
async def parallel_processing_workflow():
    """Workflow using multiple agents with different tool sets."""

    # Create specialized agents
    web_agent = IntelligentMCPAgent(
        name="web_specialist",
        engine=AugLLMConfig(),
        auto_discover=True
    )

    data_agent = IntelligentMCPAgent(
        name="data_specialist",
        engine=AugLLMConfig(),
        auto_discover=True
    )

    doc_agent = IntelligentMCPAgent(
        name="document_specialist",
        engine=AugLLMConfig(),
        auto_discover=True
    )

    # Setup agents
    await asyncio.gather(
        web_agent.setup(),
        data_agent.setup(),
        doc_agent.setup()
    )

    # Parallel execution
    web_task = web_agent.arun({
        "messages": [{"role": "user", "content": "Research market trends"}]
    })

    data_task = data_agent.arun({
        "messages": [{"role": "user", "content": "Analyze sales database"}]
    })

    doc_task = doc_agent.arun({
        "messages": [{"role": "user", "content": "Review legal documents"}]
    })

    # Wait for all tasks
    web_result, data_result, doc_result = await asyncio.gather(
        web_task, data_task, doc_task
    )

    # Combine results
    return {
        "market_research": web_result,
        "sales_analysis": data_result,
        "legal_review": doc_result
    }
```

## 🎯 Best Practices

### 1. Tool Selection Strategy

- **Static** for production reliability
- **Dynamic** for exploration and development
- **Hybrid** for most enterprise scenarios

### 2. Approval Workflows

- **Auto-approve** trusted, low-risk tools
- **Require approval** for data access, external APIs
- **Custom logic** for domain-specific security requirements

### 3. Error Handling

- Always have fallback configurations
- Graceful degradation when tools unavailable
- Comprehensive logging for debugging

### 4. Performance Optimization

- Cache tool metadata
- Connection pooling for frequently used servers
- Lazy loading for expensive tools

---

**Next**: [Implementation Patterns](../implementation/README.md) | [Examples](../examples/README.md)
