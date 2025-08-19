# MCP Testing Guide

This document provides a comprehensive guide for testing the MCP (Model Context Protocol) functionality.

## 🎯 What We Built

We created a comprehensive test suite for MCP server management, covering:

1. **MCP Server Setup & Management**
2. **Bulk Server Installation** 
3. **Individual Server Installation**
4. **Discovery of Installed Servers**
5. **Analysis & Viewing Tools**

## 📁 Test Files Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_mcp_server_setup.py      # Server lifecycle testing
├── test_bulk_download.py         # Bulk installation testing
├── test_specific_download.py     # Individual installer testing
├── test_viewing_installed.py     # Discovery and viewing testing
├── test_integration.py           # Integration testing
├── test_direct_functionality.py  # Direct CLI testing
├── simple_test.py                # Basic smoke tests
└── README.md                     # Test documentation
```

## 🚀 Running Tests

### Quick Start - Smoke Tests
```bash
# Basic functionality check
python tests/simple_test.py
```

### Command Line Interface Tests
```bash
# Test bulk installer CLI
PYTHONPATH=src python src/haive/mcp/installer/bulk_installer.py --help

# Test server discovery CLI
PYTHONPATH=src python src/haive/mcp/discovery/installed_servers.py --help

# Test server manager
PYTHONPATH=src python src/haive/mcp/servers/mcp_server_manager.py --help
```

### Analysis & Visualization Tests
```bash
# Extract CSV data from JSON
cd scratches/mcp-analysis
python extract_to_csv.py

# Analyze star distribution
python analyze_star_distribution.py

# View with Streamlit (if streamlit installed)
streamlit run mcp_viewer.py
```

## 🔧 Core Functionality Testing

### 1. MCP Server Management

**What it tests:**
- Starting and stopping MCP servers
- Server status monitoring
- Non-interactive mode operation

**Key commands:**
```bash
# Test server manager
PYTHONPATH=src python src/haive/mcp/servers/mcp_server_manager.py
```

### 2. Bulk Server Installation

**What it tests:**
- Installing servers by star count threshold
- Category-based installation
- Top N server installation
- Installation reporting

**Key commands:**
```bash
# Test with real data (if CSV exists)
PYTHONPATH=src python src/haive/mcp/installer/bulk_installer.py \
    --data-file scratches/mcp-analysis/mcp_servers_data.csv \
    --min-stars 1000 \
    --dry-run
```

### 3. Server Discovery

**What it tests:**
- Finding NPM-installed servers
- Finding pip-installed servers
- Configuration file discovery
- Server availability checking

**Key commands:**
```bash
# Discover installed servers
PYTHONPATH=src python src/haive/mcp/discovery/installed_servers.py

# Check specific server
PYTHONPATH=src python src/haive/mcp/discovery/installed_servers.py \
    --check "@modelcontextprotocol/server-filesystem"
```

## 📊 Data Analysis Testing

### Real Data Analysis

We work with **1,960 MCP servers** from GitHub:

```bash
cd scratches/mcp-analysis

# Extract and analyze
python extract_to_csv.py
python analyze_star_distribution.py

# Key findings:
# - 1,960 total servers
# - 194 servers with stars (9.9%)
# - Top 1% have 76.3% of all stars
# - 37 servers have 1000+ stars
```

### Visualization

```bash
# Generate distribution plots
python star_distribution_visual.py

# View interactive dashboard
streamlit run mcp_viewer.py
```

## 🧪 Test Categories

### Unit Tests (Fast)
- Individual component testing
- Mocked external dependencies
- No network or file system access

### Integration Tests (Slower)
- Component interaction testing
- Real file system operations
- May include network calls

### End-to-End Tests (Slowest)
- Full workflow testing
- Real server installations
- Complete data pipelines

## 📋 Test Data

### Sample Test Data
Tests use realistic sample data including:
- High-star servers (5000+ stars)
- Medium-star servers (100-1000 stars)
- Different categories (utility, ai_ml, database)
- Various installation methods (npm, pip, git)

### Real Data (Optional)
- Full 1,960 server dataset
- Real GitHub star counts
- Actual installation commands
- Complete metadata

## 🔍 Debugging Tests

### Common Issues

1. **Import Errors**
   ```bash
   # Fix with PYTHONPATH
   PYTHONPATH=src python your_test.py
   ```

2. **Missing Data**
   ```bash
   # Generate CSV data
   cd scratches/mcp-analysis
   python extract_to_csv.py
   ```

3. **Server Installation Failures**
   - Use `--dry-run` flag for testing
   - Check network connectivity
   - Verify npm/pip availability

### Debug Commands

```bash
# Check file structure
ls -la src/haive/mcp/

# Verify data exists
ls -la scratches/mcp-analysis/

# Test imports
PYTHONPATH=src python -c "import sys; print(sys.path)"

# Check server status
ps aux | grep mcp
```

## 📈 Success Criteria

### Functionality Tests
- ✅ All CLI tools have working --help
- ✅ Server manager can start/stop servers
- ✅ Bulk installer can process CSV data
- ✅ Discovery can find installed servers

### Data Pipeline Tests
- ✅ JSON data extracts to CSV (1,960 servers)
- ✅ Star distribution analysis works
- ✅ Streamlit viewer displays data correctly

### Integration Tests
- ✅ Components work together
- ✅ Error handling works properly
- ✅ Reports generate correctly

## 🎯 Next Steps

1. **Run the smoke tests**: `python tests/simple_test.py`
2. **Test bulk installation**: Try installing high-star servers
3. **View the data**: Use the Streamlit dashboard
4. **Explore individual installers**: Test NPM, pip, Git installers
5. **Monitor installed servers**: Use discovery tools

## 💡 Pro Tips

- Always use `PYTHONPATH=src` for direct script execution
- Use `--dry-run` flags to test without installing
- Check the CSV data first: `head scratches/mcp-analysis/mcp_servers_data.csv`
- Start with high-star servers (1000+) for reliability
- Use the Streamlit viewer to explore server categories

---

**Remember**: The goal is to test the complete MCP workflow from server discovery → installation → management → analysis!