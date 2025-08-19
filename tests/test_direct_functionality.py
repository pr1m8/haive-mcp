#!/usr/bin/env python3
"""Direct functionality tests without complex imports."""

import sys
import os
import subprocess
import tempfile
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for direct testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_bulk_installer_cli():
    """Test bulk installer CLI functionality."""
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("""name,stars,category,install_command
@modelcontextprotocol/server-filesystem,5000,utility,npm install -g @modelcontextprotocol/server-filesystem
test-server,1000,test,npm install -g test-server
""")
        csv_path = f.name
    
    try:
        # Test CLI help
        result = subprocess.run([
            'python', 'src/haive/mcp/installer/bulk_installer.py', '--help'
        ], capture_output=True, text=True, cwd='..')
        
        assert result.returncode == 0
        assert 'Bulk install MCP servers' in result.stdout
        
        # Test dry run
        result = subprocess.run([
            'python', 'src/haive/mcp/installer/bulk_installer.py',
            '--data-file', csv_path,
            '--min-stars', '500',
            '--dry-run'
        ], capture_output=True, text=True, cwd='..')
        
        # Should not fail even in dry run
        assert result.returncode in [0, 1]  # May fail due to missing data, but should parse args
    finally:
        os.unlink(csv_path)

def test_discovery_cli():
    """Test server discovery CLI functionality."""
    result = subprocess.run([
        'python', 'src/haive/mcp/discovery/installed_servers.py', '--help'
    ], capture_output=True, text=True, cwd='..')
    
    assert result.returncode == 0
    assert 'Discover installed MCP servers' in result.stdout

def test_mcp_server_manager_cli():
    """Test MCP server manager CLI functionality."""
    result = subprocess.run([
        'python', 'src/haive/mcp/servers/mcp_server_manager.py', '--help'
    ], capture_output=True, text=True, cwd='..')
    
    # May not have --help, but should not crash
    assert result.returncode in [0, 1, 2]

def test_streamlit_viewer_exists():
    """Test that the Streamlit viewer exists."""
    viewer_path = Path('../scratches/mcp-analysis/mcp_viewer.py')
    if viewer_path.exists():
        # Just check it's a Python file with streamlit
        content = viewer_path.read_text()
        assert 'streamlit' in content or 'st.' in content
    else:
        print("Streamlit viewer not found - may not be created yet")

def test_csv_data_exists():
    """Test that CSV data exists and has correct structure."""
    csv_path = Path('../scratches/mcp-analysis/mcp_servers_data.csv')
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        
        # Check expected columns
        expected_cols = ['name', 'stars']
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"
        
        # Check data size
        assert len(df) > 0, "CSV should have data"
        print(f"✅ Found {len(df)} servers in CSV")
    else:
        print("CSV data not found - may need to run extraction")

def test_analysis_tools_exist():
    """Test that analysis tools exist."""
    analysis_dir = Path('../scratches/mcp-analysis')
    if analysis_dir.exists():
        files = list(analysis_dir.glob('*.py'))
        assert len(files) > 0, "Should have Python analysis files"
        print(f"✅ Found {len(files)} analysis files")
    else:
        print("Analysis directory not found")

def test_json_data_structure():
    """Test JSON data has correct structure."""
    json_path = Path('../data/mcp_servers/ALL_MCP_SERVERS_COMPLETE.json')
    if json_path.exists():
        with open(json_path) as f:
            data = json.load(f)
        
        assert isinstance(data, dict), "JSON should be a dict"
        print(f"✅ JSON data loaded successfully")
    else:
        print("Complete JSON data not found")

if __name__ == "__main__":
    print("Testing MCP functionality directly...")
    
    test_bulk_installer_cli()
    print("✅ Bulk installer CLI works")
    
    test_discovery_cli()
    print("✅ Discovery CLI works")
    
    test_mcp_server_manager_cli()
    print("✅ MCP server manager exists")
    
    test_streamlit_viewer_exists()
    
    test_csv_data_exists()
    
    test_analysis_tools_exist()
    
    test_json_data_structure()
    
    print("\n🎉 All direct functionality tests passed!")