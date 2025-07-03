# AnalyticDB PostgreSQL MCP Server

AnalyticDB PostgreSQL MCP Server serves as a universal interface between AI Agents and AnalyticDB PostgreSQL databases. It enables seamless communication between AI Agents and AnalyticDB PostgreSQL, helping AI Agents retrieve database metadata and execute SQL operations.

## Configuration

### Mode 1: Download

Download from Github

```shell
git clone https://github.com/aliyun/alibabacloud-adbpg-mcp-server.git
```

#### MCP Integration

Add the following configuration to the MCP client configuration file:

```json
"mcpServers": {
  "adbpg-mcp-server": {
    "command": "uv",
    "args": [
      "--directory",
      "/path/to/adbpg-mcp-server",
      "run",
      "adbpg-mcp-server"
    ],
    "env": {
      "ADBPG_HOST": "host",
      "ADBPG_PORT": "port",
      "ADBPG_USER": "username",
      "ADBPG_PASSWORD": "password",
      "ADBPG_DATABASE": "database"
    }
  }
}
```

### Mode 2: Using pip

```
pip install adbpg_mcp_server
```

#### MCP Integration

```json
"mcpServers": {
  "adbpg-mcp-server": {
    "command": "uvx",
    "args": [
      "adbpg_mcp_server"
    ],
    "env": {
      "ADBPG_HOST": "host",
      "ADBPG_PORT": "port",
      "ADBPG_USER": "username",
      "ADBPG_PASSWORD": "password",
      "ADBPG_DATABASE": "database"
    }
  }
}
```

## Components

### Tools

- `execute_select_sql`: Execute SELECT SQL queries on the AnalyticDB PostgreSQL server
- `execute_dml_sql`: Execute DML (INSERT, UPDATE, DELETE) SQL queries on the AnalyticDB PostgreSQL server
- `execute_ddl_sql`: Execute DDL (CREATE, ALTER, DROP) SQL queries on the AnalyticDB PostgreSQL server
- `analyze_table`: Collect table statistics
- `explain_query`: Get query execution plan

### Resources

#### Built-in Resources

- `adbpg:///schemas`: Get all schemas in the database

#### Resource Templates

- `adbpg:///{schema}/tables`: List all tables in a specific schema
- `adbpg:///{schema}/{table}/ddl`: Get table DDL
- `adbpg:///{schema}/{table}/statistics`: Show table statistics

## Environment Variables

MCP Server requires the following environment variables to connect to AnalyticDB PostgreSQL instance:

- `ADBPG_HOST`: Database host address
- `ADBPG_PORT`: Database port
- `ADBPG_USER`: Database username
- `ADBPG_PASSWORD`: Database password
- `ADBPG_DATABASE`: Database name

## Dependencies

- Python 3.10 or higher
- Required packages:
  - mcp >= 1.4.0
  - psycopg >= 3.1.0
  - python-dotenv >= 1.0.0
  - pydantic >= 2.0.0

## Running

```bash
# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -e .

# Run server
uv run adbpg-mcp-server
```
