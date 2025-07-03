#!/bin/bash
# Script to run MCP server downloads with nohup

echo "Starting MCP server download process..."

# Create output directory for logs
mkdir -p mcp_download_logs

# Run the download script with nohup
echo "Running download_all_mcp_servers.py with nohup..."
echo "This will download/install all available MCP servers in the background."
echo "Logs will be saved to: mcp_download_logs/download_$(date +%Y%m%d_%H%M%S).log"

nohup poetry run python download_all_mcp_servers.py --limit 10 \
    > "mcp_download_logs/download_$(date +%Y%m%d_%H%M%S).log" 2>&1 &

PID=$!
echo "Started download process with PID: $PID"
echo ""
echo "To monitor progress:"
echo "  tail -f mcp_download_logs/download_*.log"
echo "  ps -p $PID"
echo ""
echo "The script will install servers to: ~/.mcp/servers"
echo "A configuration file will be generated at: ~/.mcp/servers/mcp_servers_config.json"