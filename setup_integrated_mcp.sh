#!/bin/bash
# Setup script for Integrated MCP Discovery & Management System

echo "🚀 Setting up Integrated MCP System..."
echo "===================================="

# Check Python
if ! command -v python3 &>/dev/null; then
	echo "❌ Python 3 is required but not installed."
	exit 1
fi

echo "✅ Python 3 found"

# Install dependencies
echo ""
echo "📦 Installing required dependencies..."
pip install streamlit plotly pandas aiohttp psutil click

# Create FastMCP directory
echo ""
echo "📁 Creating FastMCP configuration directory..."
mkdir -p ~/.fastmcp

# Check for MCP data
DATA_FILE="$(dirname "$0")/../../data/mcp_servers/ALL_MCP_SERVERS_COMPLETE.json"
if [[ -f "${DATA_FILE}" ]]; then
	echo "✅ MCP database found ($(jq length${"$DATA_FI}LE" 2>/dev/null || echo "unknown") servers)"
else
	echo "⚠️  MCP database not found ${t: $DATA_}FILE"
	echo "   The system will have limited functionality without the server database."
fi

# Create launcher alias
echo ""
echo "🔗 Creating convenient launcher..."
cat >~/mcp-launcher.sh <<'EOF'
#!/bin/bash
# MCP Integrated System Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="__MCP_DIR__"

cd "$MCP_DIR"

case "$1" in
    web)
        echo "🌐 Launching MCP Web Interface..."
        python integrated_launcher.py web
        ;;
    status)
        python integrated_launcher.py status
        ;;
    server)
        shift
        python integrated_launcher.py server "$@"
        ;;
    install)
        python integrated_launcher.py install
        ;;
    *)
        echo "MCP Integrated System"
        echo "===================="
        echo "Usage:"
        echo "  mcp-launcher.sh web       # Launch web interface (recommended)"
        echo "  mcp-launcher.sh status    # Show system status"
        echo "  mcp-launcher.sh server    # Server management"
        echo "  mcp-launcher.sh install   # Interactive installation"
        ;;
esac
EOF

# Replace __MCP_DIR__ with actual path
MCP_DIR="$(cd "$(dirname "$0")/src/haive/mcp" && pwd)"
sed -i "s|__MCP_DIR__|${MCP_DIR}|g" ~/mcp-launcher.sh
chmod +x ~/mcp-launcher.sh

echo "✅ Setup complete!"
echo ""
echo "🎯 Quick Start Commands:"
echo "   1. Launch web interface:"
echo "      ~/mcp-launcher.sh web"
echo ""
echo "   2. Check status:"
echo "      ~/mcp-launcher.sh status"
echo ""
echo "   3. Or use poetry:"
echo "      poetry run python $(dirname "$0")/src/haive/mcp/integrated_launcher.py web"
echo ""
echo "📚 See INTEGRATED_MCP_README.md for full documentation"
echo ""
echo "Happy MCP server discovering! 🚀"
