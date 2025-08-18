"""Advanced Code-Generating MCP Server Installer.

Version 2: Uses Aug_LLM agents to generate custom installation code.
More flexible but requires human oversight for safety.
"""

import os
import subprocess
from typing import Any

from haive.core.tools.interrupt_tool_wrapper import add_human_in_the_loop
from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from haive.mcp.installers.config_manager import MCPConfigManager, MCPEnvironmentConfig
from haive.mcp.installers.safe_pattern_installer import (
    InstallationRequest as SafeRequest,
)
from haive.mcp.installers.safe_pattern_installer import (
    SafePatternInstaller,
)

# Import haive agent for code generation (would need actual import)
# from haive.agents.simple import SimpleAgent
# from haive.core.engine.aug_llm import AugLLMConfig


class CodeGenerationRequest(BaseModel):
    """Request for LLM-generated installation code."""

    server_name: str = Field(description="Unique name for server instance")
    server_description: str = Field(description="Description of what the server does")
    package_info: dict[str, Any] = Field(
        description="Package metadata (name, repo, docs)"
    )
    context_documents: list[str] = Field(
        default_factory=list, description="Context from documentation"
    )
    custom_requirements: str = Field(
        default="", description="Special installation requirements"
    )
    risk_tolerance: str = Field(default="low", description="low, medium, high")


class GeneratedInstallPlan(BaseModel):
    """LLM-generated installation plan."""

    install_commands: list[str] = Field(description="Installation commands to execute")
    startup_command: str = Field(description="Command to start the server")
    environment_setup: dict[str, str] = Field(
        default_factory=dict, description="Environment variables needed"
    )
    validation_steps: list[str] = Field(description="Steps to validate installation")
    risk_assessment: str = Field(description="Security risk assessment")
    confidence_score: float = Field(description="Confidence in the plan (0-1)")
    fallback_to_safe: bool = Field(
        default=False, description="Whether to fallback to safe patterns"
    )


class SubprocessExecutionInput(BaseModel):
    """Input for subprocess execution tool."""

    command: str = Field(description="Command to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")
    working_directory: str | None = Field(default=None, description="Working directory")
    environment_vars: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )


class AdvancedCodeInstaller:
    """Advanced MCP installer with LLM code generation."""

    def __init__(self, config_manager: MCPConfigManager | None = None):
        """  Init  .

Args:
    config_manager: [TODO: Add description]
"""
        self.config_manager = config_manager or MCPConfigManager()
        self.safe_installer = SafePatternInstaller(config_manager)
        self.running_servers: dict[str, subprocess.Popen] = {}

        # This would be initialized with actual haive agent
        self.code_generation_agent = None  # SimpleAgent(...)

    def _mock_llm_code_generation(
        self, request: CodeGenerationRequest
    ) -> GeneratedInstallPlan:
        """Mock LLM code generation (replace with real agent)."""
        # This simulates what the LLM would generate
        package_name = request.package_info.get("name", "")

        if "@modelcontextprotocol" in package_name:
            # Standard MCP server
            return GeneratedInstallPlan(
                install_commands=[],  # npx handles installation
                startup_command=f"npx -y {package_name}",
                environment_setup={},
                validation_steps=[
                    "Check if npx is available",
                    "Test server startup",
                    "Verify MCP protocol communication",
                ],
                risk_assessment="LOW - Standard MCP server from official repository",
                confidence_score=0.9,
                fallback_to_safe=True,
            )

        if "python" in request.server_description.lower():
            # Python-based server
            return GeneratedInstallPlan(
                install_commands=[f"pip install {package_name}"],
                startup_command=f"python -m {package_name.replace('-', '_')}",
                environment_setup={},
                validation_steps=[
                    "Check if pip is available",
                    "Verify package installation",
                    "Test module import",
                ],
                risk_assessment="MEDIUM - Python package installation",
                confidence_score=0.8,
                fallback_to_safe=False,
            )
        if "git" in package_name.lower() or "github" in request.package_info.get(
            "repo", ""
        ):
            # Git-based installation
            repo_url = request.package_info.get("repo", "")
            return GeneratedInstallPlan(
                install_commands=[
                    f"git clone {repo_url}",
                    f"cd {package_name} && npm install",
                ],
                startup_command=f"cd {package_name} && npm start",
                environment_setup={},
                validation_steps=[
                    "Check if git is available",
                    "Verify repository accessibility",
                    "Check package.json exists",
                ],
                risk_assessment="HIGH - Git repository installation requires code review",
                confidence_score=0.6,
                fallback_to_safe=False,
            )
        # Unknown pattern
        return GeneratedInstallPlan(
            install_commands=["echo 'Unknown installation pattern'"],
            startup_command="echo 'Unknown startup pattern'",
            environment_setup={},
            validation_steps=["Manual review required"],
            risk_assessment="HIGH - Unknown installation pattern",
            confidence_score=0.3,
            fallback_to_safe=True,
        )

    async def generate_installation_plan(
        self, request: CodeGenerationRequest
    ) -> GeneratedInstallPlan:
        """Generate installation plan using LLM."""
        # In real implementation, this would use the haive agent:
        """
        prompt = f'''
        Generate an installation plan for MCP server:

        Server Name: {request.server_name}
        Description: {request.server_description}
        Package Info: {json.dumps(request.package_info, indent=2)}
        Custom Requirements: {request.custom_requirements}
        Risk Tolerance: {request.risk_tolerance}

        Context Documentation:
        {chr(10).join(request.context_documents)}

        Please provide:
        1. Installation commands (step by step)
        2. Startup command
        3. Required environment variables
        4. Validation steps
        5. Security risk assessment
        6. Confidence score (0-1)

        Focus on standard patterns: npm, pip, git clone, docker.
        Prefer official package managers over manual compilation.
        '''

        result = await self.code_generation_agent.arun(prompt)
        # Parse LLM result into GeneratedInstallPlan
        """

        # For now, use mock generation
        return self._mock_llm_code_generation(request)

    def create_subprocess_execution_tool(
        self, plan: GeneratedInstallPlan, request: CodeGenerationRequest
    ) -> StructuredTool:
        """Create tool for executing subprocess commands with oversight."""

        def execute_subprocess(
            command: str,
            timeout: int = 30,
            working_directory: str | None = None,
            environment_vars: dict[str, str] | None = None,
        ) -> str:
            """Execute subprocess command with safety checks."""
            # Security validation
            dangerous_patterns = ["rm -rf", "sudo", "curl | sh", "wget | sh", "| bash"]
            if any(pattern in command.lower() for pattern in dangerous_patterns):
                return f"❌ BLOCKED: Command contains dangerous pattern: {command}"

            # Risk assessment check
            if (
                plan.risk_assessment.startswith("HIGH")
                and request.risk_tolerance == "low"
            ):
                return f"❌ BLOCKED: High risk command not allowed with low risk tolerance: {command}"

            try:
                # Prepare environment
                env = os.environ.copy()
                if environment_vars:
                    env.update(environment_vars)
                if plan.environment_setup:
                    env.update(plan.environment_setup)

                # Execute command
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=working_directory,
                    env=env,
                    check=False,
                )

                if result.returncode == 0:
                    return f"✅ Command succeeded:\n{result.stdout}"
                return f"❌ Command failed (exit code {result.returncode}):\n{result.stderr}"

            except subprocess.TimeoutExpired:
                return f"❌ Command timed out after {timeout} seconds"
            except Exception as e:
                return f"❌ Execution error: {e}"

        # Create structured tool
        subprocess_tool = StructuredTool.from_function(
            func=execute_subprocess,
            name=f"execute_install_{request.server_name}",
            description=f"Execute installation commands for {request.server_name} (Risk: {
                plan.risk_assessment
            })",
            args_schema=SubprocessExecutionInput,
        )

        # Always wrap with human approval for generated code
        return add_human_in_the_loop(
            subprocess_tool,
            interrupt_config={
                "allow_accept": True,
                "allow_edit": True,
                "allow_respond": True,
            },
        )

    def create_validation_tool(
        self, plan: GeneratedInstallPlan, request: CodeGenerationRequest
    ) -> StructuredTool:
        """Create tool for validating installation."""

        @tool
        def validate_installation() -> str:
            """Validate that MCP server installation was successful."""
            results = []

            for step in plan.validation_steps:
                results.append(f"📋 {step}")

                # Simple validation logic (would be more sophisticated)
                if "npx" in step.lower():
                    try:
                        result = subprocess.run(
                            ["npx", "--version"],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if result.returncode == 0:
                            results.append(
                                f"   ✅ npx available: {result.stdout.strip()}"
                            )
                        else:
                            results.append("   ❌ npx not available")
                    except BaseException:
                        results.append("   ❌ npx check failed")

                elif "pip" in step.lower():
                    try:
                        result = subprocess.run(
                            ["pip", "--version"],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if result.returncode == 0:
                            results.append(
                                f"   ✅ pip available: {result.stdout.strip()}"
                            )
                        else:
                            results.append("   ❌ pip not available")
                    except BaseException:
                        results.append("   ❌ pip check failed")

                elif "git" in step.lower():
                    try:
                        result = subprocess.run(
                            ["git", "--version"],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if result.returncode == 0:
                            results.append(
                                f"   ✅ git available: {result.stdout.strip()}"
                            )
                        else:
                            results.append("   ❌ git not available")
                    except BaseException:
                        results.append("   ❌ git check failed")

                else:
                    results.append("   ⏭️  Manual validation required")

            return "\n".join(results)

        return validate_installation

    async def install_server_advanced(
        self, request: CodeGenerationRequest
    ) -> tuple[bool, str, list[StructuredTool]]:
        """Advanced server installation with code generation."""
        # Generate installation plan
        plan = await self.generate_installation_plan(request)

        # Check if we should fallback to safe installer
        if plan.fallback_to_safe and plan.confidence_score > 0.7:
            # Try to find matching pattern
            safe_request = SafeRequest(
                server_name=request.server_name,
                package_name=request.package_info.get("name", ""),
                pattern_type="web_api",  # Default
                require_approval=True,
            )

            safe_tool = self.safe_installer.create_installation_tool(safe_request)
            return True, "Using safe pattern installer", [safe_tool]

        # Create tools for advanced installation
        tools = []

        # 1. Subprocess execution tool (with human approval)
        subprocess_tool = self.create_subprocess_execution_tool(plan, request)
        tools.append(subprocess_tool)

        # 2. Validation tool
        validation_tool = self.create_validation_tool(plan, request)
        tools.append(validation_tool)

        # 3. Configuration creation tool
        @tool
        def create_server_config() -> str:
            """Create server configuration after successful installation."""
            try:
                env_config = MCPEnvironmentConfig(
                    server_name=request.server_name,
                    package_name=request.package_info.get("name", ""),
                    startup_args=[],
                    env_vars=plan.environment_setup,
                    transport_type="stdio",
                    requires_approval=True,
                )

                success = self.config_manager.add_server_config(env_config)
                if success:
                    return f"✅ Configuration created for {request.server_name}"
                return "❌ Failed to create configuration"

            except Exception as e:
                return f"❌ Configuration error: {e}"

        tools.append(create_server_config)

        summary = f"""🧠 Advanced installation plan generated:

📋 Installation Plan:
   Server: {request.server_name}
   Risk: {plan.risk_assessment}
   Confidence: {plan.confidence_score:.1%}
   Commands: {len(plan.install_commands)}

🔧 Tools Created:
   1. Subprocess execution (with human approval)
   2. Installation validation
   3. Configuration creation

⚠️  IMPORTANT: All commands require human approval
   Generated code will be reviewed before execution.

🚀 Next Steps:
   1. Review and execute installation commands
   2. Validate installation success
   3. Create server configuration
"""

        return True, summary, tools

    def get_advanced_status(self) -> dict[str, Any]:
        """Get status of advanced installer."""
        return {
            "installer_type": "AdvancedCodeInstaller",
            "llm_agent_available": self.code_generation_agent is not None,
            "safe_installer_status": self.safe_installer.get_status_summary(),
            "running_servers": list(self.running_servers.keys()),
            "human_approval_required": True,
        }

    def cleanup(self):
        """Clean up all resources."""
        self.safe_installer.cleanup()
        for _name, process in self.running_servers.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except BaseException:
                process.kill()
