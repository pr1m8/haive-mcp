#!/bin/bash

# MCP Discovery Agent Runner Script
# Runs the MCP SimpleRAG agent in the background on port 6969

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
AGENT_SCRIPT="${SCRIPT_DIR}/src/haive/mcp/mcp_simple_rag_agent.py"
LOG_FILE="/tmp/mcp_agent.log"
PID_FILE="/tmp/mcp_agent.pid"

print_status() {
	echo -e "${BLUE}[MCP Agent]${NC} $1"
}

print_success() {
	echo -e "${GREEN}[MCP Agent]${NC} $1"
}

print_error() {
	echo -e "${RED}[MCP Agent]${NC} $1"
}

print_warning() {
	echo -e "${YELLOW}[MCP Agent]${NC} $1"
}

check_status() {
	if [[ -f "${PID_FILE}" ]]; then
		PID=$(cat "${PID_FILE}")
		if ps -p "$PID" >/dev/null 2>&1; then
			return 0 # Running
		else
			rm -f "${PID_FILE}"
			return 1 # Not running
		fi
	else
		return 1 # Not running
	fi
}

start_agent() {
	print_status "Starting MCP Discovery Agent..."

	# Check if already running
	if check_status; then
		print_warning "Agent is already running (PID: $(cat "$PID_FILE"))"
		print_status "Access at: http://localhost:6969"
		return 0
	fi

	# Change to project directory
	cd "${PROJECT_DIR}" || {
		print_error "Failed to change to project directory: ${PROJECT_DIR}"
		return 1
	}

	# Start the agent in background
	print_status "Starting agent in background..."
	nohup poetry run python "${AGENT_SCRIPT}" >"${LOG_FILE}" 2>&1 &
	echo $! >"${PID_FILE}"

	# Wait a moment and check if it started successfully
	sleep 3

	if check_status; then
		print_success "✅ MCP Discovery Agent started successfully!"
		print_success "🌐 Web interface: http://localhost:6969"
		print_success "📝 Log${: $LOG_F}ILE"
		print_success "🔍 PID: $(c"at $PID_F"ILE)"

		# Show recent logs
		print_status "Recent logs:"
		tail -5 "${LOG_FILE}"

		return 0
	else
		print_error "❌ Failed to start agent"
		print_error "Check logs: ${LOG_FILE}"
		return 1
	fi
}

stop_agent() {
	print_status "Stopping MCP Discovery Agent..."

	if check_status; then
		PID=$(cat "${PID_FILE}")
		print_status "Stopping agent (PID: ${PID})..."

		# Try graceful shutdown first
		kill "$PID" 2>/dev/null

		# Wait for graceful shutdown
		sleep 2

		# Force kill if still running
		if ps -p "$PID" >/dev/null 2>&1; then
			print_warning "Forcing shutdown..."
			kill -9 "$PID" 2>/dev/null
		fi

		rm -f "${PID_FILE}"
		print_success "✅ Agent stopped"
	else
		print_warning "Agent is not running"
	fi
}

restart_agent() {
	print_status "Restarting MCP Discovery Agent..."
	stop_agent
	sleep 1
	start_agent
}

show_status() {
	print_status "MCP Discovery Agent Status:"

	if check_status; then
		PID=$(cat "${PID_FILE}")
		print_success "✅ Running (PID${ $P}ID)"
		print_success "🌐 Web interface: http://localhost:6969"
		print_success "📝 Log${: $LOG_F}ILE"

		# Show CPU and memory usage
		print_status "Resource usage:"
		ps -p "$PID" -o pid,ppid,pcpu,pmem,command 2>/dev/null || print_warning "Could not get process info"

		# Show port status
		print_status "Port status:"
		lsof -i :6969 2>/dev/null || print_warning "Port 6969 not found"

	else
		print_error "❌ Not running"
	fi
}

show_logs() {
	if [[ -f "${LOG_FILE}" ]]; then
		print_status "Showing logs (last 50 lines):"
		tail -50 "${LOG_FILE}"
	else
		print_warning "No log file found at ${LOG_FILE}"
	fi
}

follow_logs() {
	if [[ -f "${LOG_FILE}" ]]; then
		print_status "Following logs (Ctrl+C to stop):"
		tail -f "${LOG_FILE}"
	else
		print_warning "No log file found at ${LOG_FILE}"
	fi
}

show_help() {
	echo "MCP Discovery Agent Control Script"
	echo ""
	echo "Usage: $0 {start|stop|restart|status|logs|follow|help}"
	echo ""
	echo "Commands:"
	echo "  start   - Start the MCP Discovery Agent in background"
	echo "  stop    - Stop the MCP Discovery Agent"
	echo "  restart - Restart the MCP Discovery Agent"
	echo "  status  - Show current status and resource usage"
	echo "  logs    - Show recent logs"
	echo "  follow  - Follow logs in real-time"
	echo "  help    - Show this help message"
	echo ""
	echo "The agent runs on port 6969 and provides a web interface for"
	echo "discovering and learning about MCP servers."
}

# Main command handling
case "$1" in
start)
	start_agent
	;;
stop)
	stop_agent
	;;
restart)
	restart_agent
	;;
status)
	show_status
	;;
logs)
	show_logs
	;;
follow)
	follow_logs
	;;
help | --help | -h)
	show_help
	;;
*)
	print_error "Unknown command: $1"
	show_help
	exit 1
	;;
esac

exit $?
