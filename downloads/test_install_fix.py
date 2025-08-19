#!/usr/bin/env python3
"""Test script to verify install command generation works."""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
from haive.mcp.installer.bulk_installer import MCPBulkInstaller

def test_install_command_generation():
    """Test install command generation with sample data."""
    
    # Create sample test data
    test_data = pd.DataFrame([
        {
            'name': 'modelcontextprotocol/server-filesystem',
            'repository_url': 'https://github.com/modelcontextprotocol/server-filesystem',
            'repository_owner': 'modelcontextprotocol',
            'repository_name': 'server-filesystem',
            'language': 'TypeScript',
            'install_command': None,
            'npm_package': None,
            'stars': 100
        },
        {
            'name': 'someone/mcp-server-example',
            'repository_url': 'https://github.com/someone/mcp-server-example',
            'repository_owner': 'someone',
            'repository_name': 'mcp-server-example',
            'language': 'Python',
            'install_command': None,
            'npm_package': None,
            'stars': 50
        },
        {
            'name': 'test/regular-repo',
            'repository_url': 'https://github.com/test/regular-repo',
            'repository_owner': 'test',
            'repository_name': 'regular-repo',
            'language': 'JavaScript',
            'install_command': None,
            'npm_package': None,
            'stars': 25
        }
    ])
    
    # Create installer instance
    installer = MCPBulkInstaller()
    
    print("Testing install command generation:\n")
    
    for idx, row in test_data.iterrows():
        cmd = installer._generate_install_command(row)
        print(f"Server: {row['name']}")
        print(f"Language: {row['language']}")
        print(f"Generated command: {cmd}")
        print("-" * 50)

if __name__ == "__main__":
    test_install_command_generation()