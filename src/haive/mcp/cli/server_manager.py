#!/usr/bin/env python3
"""
CLI for MCP Server Manager.

This provides a command-line interface to manage MCP servers.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from haive.mcp.servers.mcp_server_manager import main

if __name__ == "__main__":
    main()