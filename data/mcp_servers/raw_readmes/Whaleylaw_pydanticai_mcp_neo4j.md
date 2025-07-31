pip# Pydantic AI MCP Agent - Tool Integration Framework

This project demonstrates how to build an AI agent that integrates with Model Context Protocol (MCP) servers, allowing AI models to access external tools through a standardized interface. It uses Pydantic AI for the agent framework and MCP for tool integration, and the MCP configuration is similar to Claude Desktop/Windsurf/Cline.

## Quick Start

If you want to very quickly integrate MCP servers into your own Pydantic AI agents, just follow these simple steps:

1. Copy `mcp_client.py` from this repo into your own project

2. Install the necessary dependencies:

```bash
pip install pydantic-ai mcp
```

3. Set up an `mcp_config.json` file in your project which follows the **exact** same structure as configuring MCP servers for Claude Desktop. Use `mcp_config_example.json` for guidance.

4. Set up your Pydantic AI agent like:

```python
import mcp_client
from pydantic_ai import Agent

async def get_pydantic_ai_agent():
    client = mcp_client.MCPClient()
    client.load_servers("mcp_config.json")
    tools = await client.start()
    return client, Agent(model='your-llm-here', tools=tools)
```

Then you in your main function you can retrieve the client and agent like:

```python
client, agent = await get_pydantic_ai_agent()
```

This Pydantic AI agent will now have access to all the tools for the MCP servers you defined in `mcp_config.json`!

## Features

- **🔧 MCP Tool Integration**: Connect to any MCP-compatible tool server
- **🤖 Pydantic AI Framework**: Leverage the powerful Pydantic AI agent capabilities
- **🔄 Dynamic Tool Discovery**: Automatically convert MCP tools to Pydantic AI tools
- **💬 Interactive CLI**: Simple command-line interface for testing
- **📊 Conversation History**: Store and retrieve conversation history with Supabase
- **🌐 API Endpoint**: FastAPI integration example in `/studio-integration-version` (for Live Agent Studio deployment)

## Project Structure

This repository contains two main implementations:

1. **CLI Implementation** (root directory):

   - `pydantic_mcp_agent.py`: Main CLI application with interactive chat
   - `mcp_client.py`: Client for connecting to MCP servers
   - `mcp_config.json`: Configuration for MCP servers

2. **Live Agent Studio Integration** (`studio-integration-version/`):
   - `pydantic_mcp_agent_endpoint.py`: FastAPI endpoint for Live Agent Studio
   - `pydantic_mcp_agent.py`: Simplified agent setup for API integration
   - `mcp_client.py`: Client for connecting to MCP servers
   - `Dockerfile`: Container configuration for deployment

## How It Works

### MCP Integration Architecture

The system works by:

1. **Configuration**: Define MCP servers in `mcp_config.json`
2. **Connection**: Establish connections to MCP servers via stdio
3. **Tool Discovery**: Retrieve available tools from MCP servers
4. **Tool Conversion**: Transform MCP tools into Pydantic AI compatible tools
5. **Agent Initialization**: Create a Pydantic AI agent with the converted tools
6. **Execution**: Run the agent with user input, allowing it to call MCP tools

### Key Components

- **MCPClient**: Manages connections to one or more MCP servers
- **MCPServer**: Handles communication with a specific MCP server
- **Tool Conversion**: Transforms MCP tools to Pydantic AI compatible tools
- **Agent**: Pydantic AI agent that processes user requests and uses tools

## Prerequisites

- Python 3.9+
- Node.js (for MCP servers)
- OpenAI API key (or compatible API like OpenRouter, can use Ollama without an API key too)

## Setup Instructions

1. **Create and activate a virtual environment**:

   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Copy the `.env.example` file to `.env` and fill in your API keys:

   - `PROVIDER`: LLM provider (OpenAI, OpenRouter, or Ollama)
   - `BASE_URL`: API base URL for your LLM provider
   - `LLM_API_KEY`: Your API key for the LLM provider
   - `MODEL_CHOICE`: The LLM model to use (e.g., gpt-4o-mini)

4. **Configure MCP servers**:
   Create or modify `mcp_config.json` (use `mcp_config_example.json` as an example) to define your MCP servers. Example:

   ```json
   {
     "mcpServers": {
       "serverName": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "./"],
         "env": {}
       }
     }
   }
   ```

5. **Run the CLI application**:
   ```bash
   python pydantic_mcp_agent.py
   ```

## How to Extend

You can extend this project by:

1. **Adding more MCP servers**: Modify `mcp_config.json` to include additional servers
2. **Creating custom tools**: Develop your own MCP servers
3. **Enhancing the agent**: Modify the agent configuration for specialized use cases
4. **Adding memory capabilities**: Integrate with memory systems like Mem0

## Live Agent Studio Integration

The `studio-integration-version` folder contains everything needed to deploy this agent to the Live Agent Studio:

1. **Set up environment variables**:
   Copy `.env.example` to `.env` in the `studio-integration-version` directory and add:

   - LLM configuration (same as CLI version)
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_KEY`: Your Supabase service role key
   - `API_BEARER_TOKEN`: Secret token for API authentication

2. **Run the API server**:

   ```bash
   cd studio-integration-version
   python pydantic_mcp_agent_endpoint.py
   ```

3. **Deploy with Docker**:
   ```bash
   cd studio-integration-version
   docker build -t pydantic-mcp-agent .
   docker run -p 8001:8001 --env-file .env pydantic-mcp-agent
   ```

## Supabase Setup

For the Live Agent Studio integration:

1. Create a Supabase account and project at [supabase.com](https://supabase.com)
2. Create a `messages` table with the following schema:
   - `id`: UUID (primary key)
   - `created_at`: Timestamp with time zone
   - `session_id`: Text
   - `message`: JSON (contains `type`, `content`, and optional `data`)

## Learn More

- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/mcp)
- [Pydantic AI](https://github.com/pydantic/pydantic-ai)
- [Supabase](https://supabase.com/docs)
- [FastAPI](https://fastapi.tiangolo.com/)
