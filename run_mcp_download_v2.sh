#!/bin/bash
# Script to run MCP server downloads with nohup - v2

echo "Starting MCP server download process (v2)..."

# Create output directory for logs
mkdir -p mcp_download_logs

# Run the v2 download script with nohup
echo "Running download_all_mcp_servers_v2.py with nohup..."
echo "This will download/install all available MCP servers in the background."
LOG_FILE="mcp_download_logs/download_v2_$(date +%Y%m%d_%H%M%S).log"
echo "Logs will be saved to: $LOG_FILE"

nohup poetry run python download_all_mcp_servers_v2.py --limit 20 \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo "Started download process with PID: $PID"
echo ""
echo "To monitor progress:"
echo "  tail -f $LOG_FILE"
echo "  ps -p $PID"
echo ""
echo "The script will install servers to: ~/.mcp/servers"
echo "A configuration file will be generated at: ~/.mcp/servers/mcp_servers_config.json"