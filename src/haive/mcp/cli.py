#!/usr/bin/env python3
"""CLI tool for MCP server selection and configuration.

This command-line interface provides easy access to MCP server selection,
filtering, and configuration tools. Perfect for setting up MCP servers
for AI agents or interactive development.

Usage:
    python -m haive.mcp.cli list-servers                    # List all available servers
    python -m haive.mcp.cli filter --prefix "anthropic/"    # Filter by prefix
    python -m haive.mcp.cli recommend "analyze GitHub repo" # Get recommendations
    python -m haive.mcp.cli select                         # Interactive selection
    python -m haive.mcp.cli auto-config "my task"          # Auto-configure for task
"""

import argparse
import asyncio
import json
import sys

from haive.core.errors import install_short_tracebacks

from haive.mcp.documentation.doc_loader import MCPDocumentationLoader
from haive.mcp.tools.ai_assistant import MCPAssistant
from haive.mcp.tools.server_selector import MCPServerSelector


def print_servers(servers: list[dict], show_details: bool = False):
    """Print server information in a readable format.

    Displays a list of MCP servers with their metadata in a human-readable format.
    Can optionally show detailed information including capabilities.

    Args:
        servers: List of server dictionaries containing metadata.
        show_details: If True, show additional details like capabilities.
            Defaults to False for concise output.

    Note:
        Server dictionaries should contain a 'metadata' key with nested
        'name', 'description', and 'category' fields.
    """
    if not servers:
        return

    for server in servers:
        metadata = server.get("metadata", {})
        metadata.get("name", "Unknown")
        description = metadata.get("description", "No description")
        metadata.get("category", "Uncategorized")

        if show_details:
            # Show capabilities if available
            loader = MCPDocumentationLoader()
            setup_info = loader.extract_setup_info(server)
            if setup_info.get("capabilities"):
                setup_info["capabilities"][:5]  # Show first 5
                "..." if len(setup_info["capabilities"]) > 5 else ""
        else:
            # Truncate description
            (description[:60] + "..." if len(description) > 60 else description)


def print_recommendations(recommendations: list, show_reasoning: bool = False):
    """Print server recommendations.

    Displays recommended MCP servers with optional reasoning for each recommendation.
    Handles both AI assistant recommendations (with confidence scores) and basic
    selector recommendations.

    Args:
        recommendations: List of recommendation objects or dictionaries.
        show_reasoning: If True, show the reasoning behind each recommendation.
            Defaults to False.

    Note:
        Recommendations can be either simple server names or objects with
        attributes like 'confidence', 'reasoning', and 'required_env_vars'.
    """
    if not recommendations:
        return

    for _i, rec in enumerate(recommendations, 1):
        getattr(rec, "confidence", getattr(rec, "score", 0))
        getattr(rec, "server_name", rec)

        if hasattr(rec, "confidence"):
            # From AI assistant
            if show_reasoning and hasattr(rec, "reasoning"):
                pass
            if hasattr(rec, "estimated_setup_time"):
                pass
            if hasattr(rec, "required_env_vars") and rec.required_env_vars:
                pass
        # From basic selector
        elif show_reasoning and hasattr(rec, "reasons"):
            pass


async def cmd_list_servers(args):
    """List all available MCP servers.

    Command handler for listing MCP servers with optional filtering by prefix
    or category. Displays results using the print_servers function.

    Args:
        args: Parsed command line arguments containing:
            - prefix: Optional server prefix filter
            - category: Optional category filter
            - details: Whether to show detailed information

    Example:
        Called when user runs: mcp-cli list-servers --prefix "anthropic/"
    """
    selector = MCPServerSelector()

    if args.prefix:
        servers = selector.filter_by_prefix(args.prefix)
    elif args.category:
        servers = selector.filter.filter_by_category(args.category)
    else:
        servers = selector.servers

    print_servers(servers, args.details)


async def cmd_filter(args):
    """Filter servers by various criteria.

    Command handler for filtering MCP servers using multiple criteria including
    prefixes, categories, keywords, and exclusions. Supports combining multiple
    filters for precise server selection.

    Args:
        args: Parsed command line arguments containing:
            - prefix: List of prefixes to include
            - category: List of categories to include
            - keyword: List of keywords to search for
            - exclude_prefix: List of prefixes to exclude
            - details: Whether to show detailed information

    Example:
        Called when user runs: mcp-cli filter --category "development" --keyword "git"
    """
    selector = MCPServerSelector()

    servers = selector.filter.filter_by_multiple_criteria(
        prefixes=args.prefix,
        categories=args.category,
        keywords=args.keyword,
        exclude_prefixes=args.exclude_prefix,
    )

    criteria = []
    if args.prefix:
        criteria.append(f"prefix: {args.prefix}")
    if args.category:
        criteria.append(f"category: {args.category}")
    if args.keyword:
        criteria.append(f"keywords: {args.keyword}")
    if args.exclude_prefix:
        criteria.append(f"excluding: {args.exclude_prefix}")

    print_servers(servers, args.details)


async def cmd_recommend(args):
    """Get server recommendations for a task.

    Command handler for getting MCP server recommendations based on a task
    description. Can use either basic keyword matching or AI-powered analysis
    for more intelligent recommendations.

    Args:
        args: Parsed command line arguments containing:
            - task: Description of the task requiring MCP servers
            - ai_mode: Whether to use AI assistant for recommendations
            - max_servers: Maximum number of servers to recommend
            - simple: Prefer servers with simple setup
            - reasoning: Show reasoning for recommendations
            - save_config: Path to save configuration file

    Returns:
        Displays recommendations and optionally saves configuration.

    Example:
        Called when user runs: mcp-cli recommend "analyze GitHub repository" --ai-mode
    """
    if args.ai_mode:
        assistant = MCPAssistant()
        config = await assistant.auto_configure_for_task(
            args.task, prefer_simple_setup=args.simple, max_servers=args.max_servers
        )

        if config.warnings:
            for _warning in config.warnings:
                pass

        for _server_name in config.primary_servers:
            pass

        if config.fallback_servers:
            for _server_name in config.fallback_servers:
                pass

        if args.save_config:
            config_dict = config.config.model_dump()
            with open(args.save_config, "w") as f:
                json.dump(config_dict, f, indent=2)

    else:
        selector = MCPServerSelector()
        recommendations = selector.recommend_for_task(
            args.task, max_servers=args.max_servers
        )

        print_recommendations(recommendations, args.reasoning)


async def cmd_select(args):
    """Interactive server selection.

    Command handler for interactive MCP server selection. Presents available
    servers and filters, allowing users to interactively choose servers for
    their project.

    Args:
        args: Parsed command line arguments containing:
            - max_servers: Maximum number of servers to select
            - no_filters: Skip showing available filters
            - skip_filters: Skip filter input prompts
            - save_config: Path to save configuration file

    Returns:
        Creates configuration for selected servers and optionally saves it.

    Example:
        Called when user runs: mcp-cli select --save-config my_project.json
    """
    selector = MCPServerSelector()

    # Show available filters
    if not args.no_filters:
        prefixes = selector.get_available_prefixes()
        for _i, _prefix in enumerate(prefixes[:10], 1):  # Show first 10
            pass

        categories = selector.get_available_categories()
        for _i, _category in enumerate(categories, 1):
            pass

    # Get filter preferences
    filter_prefixes = None
    filter_categories = None

    if not args.skip_filters:
        prefix_input = input(
            "\nFilter by prefixes (comma-separated, or enter for all): "
        ).strip()
        if prefix_input:
            filter_prefixes = [p.strip() for p in prefix_input.split(",")]

        category_input = input(
            "Filter by categories (comma-separated, or enter for all): "
        ).strip()
        if category_input:
            filter_categories = [c.strip() for c in category_input.split(",")]

    # Interactive selection
    selected = await selector.interactive_select(
        prompt="Select servers for your project:",
        prefixes=filter_prefixes,
        categories=filter_categories,
        max_selections=args.max_servers,
    )

    if selected:
        for _server in selected:
            pass

        # Generate configuration
        config = selector.create_config_for_selection(selected)

        if args.save_config:
            config_dict = config.model_dump()
            with open(args.save_config, "w") as f:
                json.dump(config_dict, f, indent=2)

        # Show summary
        selector.get_selection_summary(selected)

    else:
        pass


async def cmd_auto_config(args):
    """Auto-configure servers for a task using AI.

    Command handler for automatic MCP server configuration using AI analysis.
    Analyzes the task description and automatically selects and configures
    appropriate servers with validation.

    Args:
        args: Parsed command line arguments containing:
            - task: Description of the task requiring MCP servers
            - max_servers: Maximum number of servers to include
            - complex_ok: Allow servers with complex setup
            - no_fallbacks: Don't include fallback servers
            - output: Path to save configuration file
            - generate_script: Path to generate Python setup script

    Returns:
        Creates optimized configuration and optionally generates setup script.

    Example:
        Called when user runs: mcp-cli auto-config "research papers" --output config.json
    """
    assistant = MCPAssistant()

    config = await assistant.auto_configure_for_task(
        args.task,
        prefer_simple_setup=not args.complex_ok,
        max_servers=args.max_servers,
        include_fallbacks=not args.no_fallbacks,
    )

    if config.warnings:
        for _warning in config.warnings:
            pass

    for _server_name in config.primary_servers:
        pass

    # Validate configuration
    validation = await assistant.validate_configuration(config.config)

    if not validation["valid"]:
        for _issue in validation["issues"]:
            pass

    if validation["suggestions"]:
        for _suggestion in validation["suggestions"]:
            pass

    if validation["required_env_vars"]:
        for _var in set(validation["required_env_vars"]):
            pass

    # Save configuration
    if args.output:
        config_dict = config.config.model_dump()
        with open(args.output, "w") as f:
            json.dump(config_dict, f, indent=2)

    # Generate setup script
    if args.generate_script:
        script = generate_setup_script(config)
        script_path = args.generate_script
        with open(script_path, "w") as f:
            f.write(script)


def generate_setup_script(config) -> str:
    """Generate a Python setup script for the configuration.

    Creates a ready-to-run Python script that sets up an MCP agent with the
    given configuration. The script includes all necessary imports, configuration,
    and basic testing code.

    Args:
        config: Configuration object containing MCP setup details including
            server configurations and selected servers.

    Returns:
        Complete Python script as a string, ready to be saved and executed.

    Example:
        script = generate_setup_script(auto_config)
        with open("setup_mcp.py", "w") as f:
            f.write(script)
    """
    script = f'''#!/usr/bin/env python3
"""
Auto-generated MCP setup script.
Generated by haive-mcp CLI tool.
"""

import asyncio
from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.models.llm.base import LLMConfig
from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig

# Configuration
MCP_CONFIG = {config.config.model_dump_json(indent=4)}

async def main():
    """Setup and test MCP agent."""
    # Create engine
    engine = AugLLMConfig(
        llm_config=LLMConfig(
            provider="openai",  # Change as needed
            model="gpt-4o-mini"  # Change as needed
        ),
        name="mcp_test_engine"
    )

    # Create MCP configuration
    mcp_config = MCPConfig(**MCP_CONFIG)

    # Create agent
    agent = MCPAgent(
        engine=engine,
        mcp_config=mcp_config,
        name="auto_configured_agent"
    )

    # Initialize
    print("Initializing MCP agent...")
    await agent.setup()

    # Test
    status = agent.get_mcp_status()
    print(f"MCP Status: {{status}}")

    if status["connected_servers"]:
        print("✅ MCP agent ready!")
        print(f"Connected servers: {{', '.join(status['connected_servers'])}}")
        print(f"Available tools: {{status['tool_count']}}")
    else:
        print("❌ No servers connected. Check configuration and environment variables.")

if __name__ == "__main__":
    asyncio.run(main())
'''
    return script


def main():
    """Main CLI entry point.

    Sets up the command-line argument parser and routes commands to appropriate
    handlers. Configures all subcommands with their respective options and
    handles execution with proper error handling.

    The CLI supports the following commands:
        - list-servers: List all available MCP servers
        - filter: Filter servers by various criteria
        - recommend: Get server recommendations for a task
        - select: Interactive server selection
        - auto-config: Auto-configure servers using AI

    Example:
        python -m haive.mcp.cli list-servers --details
    """
    install_short_tracebacks()  # Apply minimal tracebacks globally
    parser = argparse.ArgumentParser(
        description="MCP Server Selection and Configuration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list-servers --details
  %(prog)s filter --prefix "modelcontextprotocol/" --category "development"
  %(prog)s recommend "analyze GitHub repository for security issues" --ai-mode
  %(prog)s select --save-config my_config.json
  %(prog)s auto-config "research AI papers on arxiv" --output research_config.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List servers command
    list_parser = subparsers.add_parser(
        "list-servers", help="List available MCP servers"
    )
    list_parser.add_argument("--prefix", help="Filter by server prefix")
    list_parser.add_argument("--category", help="Filter by category")
    list_parser.add_argument(
        "--details", action="store_true", help="Show detailed information"
    )

    # Filter command
    filter_parser = subparsers.add_parser("filter", help="Filter servers by criteria")
    filter_parser.add_argument(
        "--prefix", action="append", help="Include prefix (can use multiple)"
    )
    filter_parser.add_argument(
        "--category", action="append", help="Include category (can use multiple)"
    )
    filter_parser.add_argument(
        "--keyword", action="append", help="Include keyword (can use multiple)"
    )
    filter_parser.add_argument(
        "--exclude-prefix", action="append", help="Exclude prefix (can use multiple)"
    )
    filter_parser.add_argument(
        "--details", action="store_true", help="Show detailed information"
    )

    # Recommend command
    recommend_parser = subparsers.add_parser(
        "recommend", help="Get server recommendations for a task"
    )
    recommend_parser.add_argument("task", help="Task description")
    recommend_parser.add_argument(
        "--ai-mode",
        action="store_true",
        help="Use AI assistant for smart recommendations",
    )
    recommend_parser.add_argument(
        "--max-servers", type=int, default=5, help="Maximum servers to recommend"
    )
    recommend_parser.add_argument(
        "--simple", action="store_true", help="Prefer simple setup"
    )
    recommend_parser.add_argument(
        "--reasoning", action="store_true", help="Show reasoning for recommendations"
    )
    recommend_parser.add_argument("--save-config", help="Save configuration to file")

    # Select command
    select_parser = subparsers.add_parser("select", help="Interactive server selection")
    select_parser.add_argument(
        "--max-servers", type=int, help="Maximum servers to select"
    )
    select_parser.add_argument(
        "--no-filters", action="store_true", help="Skip showing available filters"
    )
    select_parser.add_argument(
        "--skip-filters", action="store_true", help="Skip filter input"
    )
    select_parser.add_argument("--save-config", help="Save configuration to file")

    # Auto-config command
    auto_parser = subparsers.add_parser(
        "auto-config", help="Auto-configure servers using AI"
    )
    auto_parser.add_argument("task", help="Task description")
    auto_parser.add_argument(
        "--max-servers", type=int, default=3, help="Maximum servers to include"
    )
    auto_parser.add_argument(
        "--complex-ok", action="store_true", help="Allow complex setup servers"
    )
    auto_parser.add_argument(
        "--no-fallbacks", action="store_true", help="Don't include fallback servers"
    )
    auto_parser.add_argument("--output", "-o", help="Output configuration file")
    auto_parser.add_argument("--generate-script", help="Generate Python setup script")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Command mapping
    commands = {
        "list-servers": cmd_list_servers,
        "filter": cmd_filter,
        "recommend": cmd_recommend,
        "select": cmd_select,
        "auto-config": cmd_auto_config,
    }

    command_func = commands.get(args.command)
    if command_func:
        try:
            asyncio.run(command_func(args))
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception:
            # The custom excepthook will handle printing the error
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
