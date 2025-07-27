#!/usr/bin/env python3
"""Example MCP server using FastMCP for haive-dataflow integration."""

import logging
from pathlib import Path

# Use FastMCP from mcp.server
from mcp.server import FastMCP

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("haive-example-server")


@mcp.tool()
async def read_file(path: str) -> str:
    """Read contents of a file.

    Args:
        path: Path to the file to read

    Returns:
        Contents of the file
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File not found at {path}"

        if not file_path.is_file():
            return f"Error: {path} is not a file"

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        logger.info(f"Successfully read file: {path}")
        return content

    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return f"Error reading file: {e!s}"


@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """Write content to a file.

    Args:
        path: Path to the file to write
        content: Content to write to the file

    Returns:
        Success message or error
    """
    try:
        file_path = Path(path)

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Successfully wrote to file: {path}")
        return f"Successfully wrote {len(content)} characters to {path}"

    except Exception as e:
        logger.error(f"Error writing file {path}: {e}")
        return f"Error writing file: {e!s}"


@mcp.tool()
async def list_directory(path: str = ".", pattern: str = "*") -> list[str]:
    """List files in a directory.

    Args:
        path: Directory path to list (default: current directory)
        pattern: Glob pattern to filter files (default: *)

    Returns:
        List of file paths matching the pattern
    """
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return [f"Error: Directory not found at {path}"]

        if not dir_path.is_dir():
            return [f"Error: {path} is not a directory"]

        files = []
        for item in dir_path.glob(pattern):
            files.append(str(item))

        logger.info(f"Listed {len(files)} files in {path} matching {pattern}")
        return sorted(files)

    except Exception as e:
        logger.error(f"Error listing directory {path}: {e}")
        return [f"Error listing directory: {e!s}"]


@mcp.tool()
async def search_files(
    directory: str, search_term: str, file_pattern: str = "*.py"
) -> dict[str, list[str]]:
    """Search for a term in files within a directory.

    Args:
        directory: Directory to search in
        search_term: Term to search for
        file_pattern: Pattern for files to search (default: *.py)

    Returns:
        Dictionary mapping file paths to list of matching lines
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return {"error": [f"Invalid directory: {directory}"]}

        results = {}

        for file_path in dir_path.rglob(file_pattern):
            if file_path.is_file():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        lines = f.readlines()

                    matching_lines = []
                    for i, line in enumerate(lines, 1):
                        if search_term.lower() in line.lower():
                            matching_lines.append(f"{i}: {line.strip()}")

                    if matching_lines:
                        results[str(file_path)] = matching_lines

                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {e}")

        logger.info(f"Found {len(results)} files containing '{search_term}'")
        return results

    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return {"error": [str(e)]}


# Add resources
@mcp.resource("file://{path}")
async def read_file_resource(path: str) -> str:
    """Resource handler for reading files.

    Args:
        path: Path to the file

    Returns:
        File contents
    """
    return await read_file(path)


# Add prompts
@mcp.prompt()
async def code_review_prompt(
    code: str, language: str = "python"
) -> list[dict[str, str]]:
    """Generate a code review prompt.

    Args:
        code: Code to review
        language: Programming language of the code

    Returns:
        List of prompt messages
    """
    return [
        {
            "role": "user",
            "content": f"""Please review the following {language} code for:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance improvements
4. Security concerns
5. Suggestions for improvement

Code to review:
```{language}
{code}
```

Please provide specific, actionable feedback.""",
        }
    ]


@mcp.prompt()
async def refactor_prompt(
    code: str, goal: str, language: str = "python"
) -> list[dict[str, str]]:
    """Generate a refactoring prompt.

    Args:
        code: Code to refactor
        goal: Goal of the refactoring
        language: Programming language

    Returns:
        List of prompt messages
    """
    return [
        {
            "role": "user",
            "content": f"""Please refactor the following {language} code with the goal of: {goal}

Original code:
```{language}
{code}
```

Requirements:
1. Maintain the same functionality
2. Improve code quality
3. Follow {language} best practices
4. Add appropriate comments
5. Ensure the refactored code is more maintainable

Please provide the refactored code with explanations of the changes made.""",
        }
    ]


# Run the server
if __name__ == "__main__":
    logger.info("Starting haive-example MCP server...")

    # Run the FastMCP server using stdio transport
    mcp.run(transport="stdio")
