# Polymarket MCP - Prediction Market Tools

A collection of Model Context Protocol (MCP) servers for interacting with prediction markets, specifically designed to work with Claude Desktop and other AI assistants.

## 🌟 Features

- **Real-time market data** from Polymarket API
- **Multiple server implementations** with varying complexity
- **Seamless integration** with Claude Desktop
- **Custom data analysis tools** for prediction markets
- **Synthetic data generation** for testing and demonstration

## 📋 Project Overview

This project provides MCP server implementations for prediction market data:

1. **Enhanced Server (v3)** - The main implementation with real-time Polymarket API integration, data analysis, and market insights.
2. **Core API Library** - Reusable components for building custom prediction market tools.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- [Claude Desktop](https://anthropic.com/claude) (for using the tools with Claude)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/Mcp-polymarket.git
   cd Mcp-polymarket
   ```

2. Run the setup script:

   ```bash
   ./scripts/setup.sh
   ```

   This will:

   - Create a virtual environment
   - Install dependencies
   - Set up configuration files
   - Provide Claude Desktop configuration instructions

### Running the Server

Use the provided script to start the server:

```bash
./scripts/start_server.sh
```

Or run it manually:

```bash
source venv/bin/activate
python3 enhanced_server_v3.py
```

## 🛠️ Available Tools

### Enhanced Server (v3)

1. **getMarkets** - Retrieve current prediction markets with filtering options
2. **refreshMarkets** - Force refresh the market data from the API
3. **analyzeMarket** - Get detailed analysis for a specific market

## 📊 Data Sources

The server can use multiple data sources:

1. **Polymarket API** - Real-time data from the Polymarket platform
2. **Synthetic Data** - Generated market data for testing and demonstration
3. **Local Cache** - Stored data for faster response times

## 🔧 Configuration

### Claude Desktop Configuration

Add the following to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "polymarket-mcp": {
      "command": "sh",
      "args": [
        "-c",
        "cd /Onfinance-MCP-Polymarket && source .venv/bin/activate && PYTHONUNBUFFERED=1 python src/polymarket_mcp/server.py 2>/tmp/polymarket_server.log"
      ],
      "restartOnExit": true,
      "maxRestarts": 5
    }
  }
}
```

The configuration file can be found at:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

## 📑 Documentation

Detailed documentation is available in the `docs` directory:

- [Enhanced Server (v3) Documentation](docs/enhanced_server_v3.md) - Comprehensive guide to the main server implementation

## 📁 Project Structure

```
Mcp-polymarket/
├── enhanced_server_v3.py        # Main server implementation
├── src/
│   └── polymarket_mcp/          # Core library components
│       ├── __init__.py
│       ├── server.py            # Base MCP server functionality
│       ├── models/              # Data models
│       ├── utils/               # Utility functions
│       └── api/                 # API integrations
├── docs/
│   └── enhanced_server_v3.md    # Detailed documentation
├── scripts/
│   ├── setup.sh                 # Setup script
│   └── start_server.sh          # Server startup script
├── archive/                     # Archive of older versions
├── venv/                        # Virtual environment (generated)
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
└── README.md                    # This file
```

## 📜 Available Scripts

The project includes several utility scripts in the `scripts` directory:

- `setup.sh` - Sets up the project environment (virtual env, dependencies, etc.)
- `start_server.sh` - Starts the server and shows live logs
- Other utility scripts for specific purposes

To run any script:

```bash
./scripts/script_name.sh
```

## 💡 Usage Examples

### Querying Markets with Claude

Once the server is running and configured in Claude Desktop, you can use the tools with queries like:

```
Can you show me the latest prediction markets related to US elections?
```

Claude will use the `getMarkets` tool with appropriate filters.

### Market Analysis

```
Analyze the market with ID "pm-123456" and give me your insights.
```

Claude will use the `analyzeMarket` tool to provide detailed market analysis.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Anthropic](https://www.anthropic.com/) for Claude and the MCP protocol
- [Polymarket](https://polymarket.com/) for the prediction market platform
- All contributors to this project

# Onfinance-MCP-Polymarket
