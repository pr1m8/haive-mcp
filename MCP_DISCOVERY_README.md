# 🔍 Enhanced MCP Discovery System

A comprehensive suite of tools for discovering, analyzing, and working with Model Context Protocol (MCP) servers.

## 🚀 Features Overview

### 1. **Self-Query RAG** 🎯

- Natural language queries with structured metadata filtering
- Example: "Python database servers with more than 10 stars"
- Automatically converts natural language to structured queries

### 2. **Parent Document Retrieval** 📚

- Small chunks for search, full documents for results
- Get complete README content and documentation
- Better context while maintaining search performance

### 3. **CSV Data Browser** 📊

- Sortable and filterable data viewer
- Export capabilities
- Interactive charts and analytics

### 4. **Enhanced Data Collection** 📈

- Full GitHub repository information
- README content extraction
- Dependency analysis
- Repository statistics

### 5. **Comprehensive Web Interface** 🌐

- All features in one unified interface
- Multiple search methodologies
- Advanced filtering and analytics

## 🛠️ Quick Start

### Install Dependencies

```bash
# Core dependencies (if not already installed)
poetry install

# Additional for web interface
pip install streamlit plotly
```

### Launch Tools

```bash
# Comprehensive web interface (recommended)
poetry run python packages/haive-mcp/src/haive/mcp/launcher.py web

# CSV data browser
poetry run python packages/haive-mcp/src/haive/mcp/launcher.py csv

# Test self-query search
poetry run python packages/haive-mcp/src/haive/mcp/launcher.py test

# Show all options
poetry run python packages/haive-mcp/src/haive/mcp/launcher.py all
```

## 📋 Individual Tools

### 1. Comprehensive Web Interface

**File**: `comprehensive_mcp_web.py`
**Launch**: `poetry run streamlit run packages/haive-mcp/src/haive/mcp/comprehensive_mcp_web.py`

**Features**:

- 🏠 Dashboard with overview and quick search
- 🔍 Advanced search with multiple retrieval methods
- 📊 Data browser with filtering and sorting
- 📚 Detailed server information
- 📈 Analytics and visualizations
- ⚙️ Export and utility tools

### 2. Self-Query RAG Agent

**File**: `self_query_mcp_agent.py`
**Launch**: `poetry run python packages/haive-mcp/src/haive/mcp/self_query_mcp_agent.py`

**Capabilities**:

- **Structured Queries**: "Database servers with more than 5 stars"
- **Metadata Filtering**: Automatic filtering by category, language, stars, etc.
- **Parent Document Retrieval**: Full content retrieval for detailed information
- **Hybrid Search**: Combines multiple search methods

**Example Queries**:

```
- "Python database servers with more than 5 stars"
- "JavaScript web servers"
- "Servers in the database category with tools"
- "How to install PostgreSQL MCP servers"
- "TypeScript servers with resources and prompts"
```

### 3. CSV Data Browser

**File**: `csv_viewer.py`
**Launch**: `poetry run python packages/haive-mcp/src/haive/mcp/csv_viewer.py --web`

**Features**:

- Interactive filtering by category, language, stars, features
- Sorting by any column
- Search within results
- Export to CSV
- Category breakdowns and top servers

### 4. Data Enhancement Tool

**File**: `enhance_mcp_data.py`
**Launch**: `poetry run python packages/haive-mcp/src/haive/mcp/enhance_mcp_data.py`

**Collects**:

- Full README content from GitHub
- Repository statistics (stars, forks, issues)
- Dependency information (package.json, requirements.txt)
- License information
- Latest releases
- Installation instructions extraction

**Usage**:

```bash
# Basic enhancement
poetry run python packages/haive-mcp/src/haive/mcp/enhance_mcp_data.py

# Test with limited servers
poetry run python packages/haive-mcp/src/haive/mcp/enhance_mcp_data.py --test

# With GitHub token for higher rate limits
poetry run python packages/haive-mcp/src/haive/mcp/enhance_mcp_data.py --github-token YOUR_TOKEN
```

### 5. Original RAG Agent

**File**: `mcp_simple_rag_agent.py`
**Launch**: `poetry run python packages/haive-mcp/src/haive/mcp/mcp_simple_rag_agent.py`

The original working RAG agent with web interface on http://localhost:6969

## 🔍 Search Methodologies Explained

### 1. Self-Query Retrieval

- **Best for**: Structured queries with specific criteria
- **Example**: "Python servers with more than 10 stars in database category"
- **How it works**: LLM converts natural language to structured query with metadata filters

### 2. Parent Document Retrieval

- **Best for**: Getting full documentation and README content
- **Example**: "How to install and configure SQLite MCP server"
- **How it works**: Searches small chunks but returns full parent documents

### 3. Similarity Search

- **Best for**: Semantic similarity and general queries
- **Example**: "Tools for working with databases"
- **How it works**: Traditional vector similarity search

## 📊 Data Structure

### Current Data Fields

```json
{
  "name": "Server name",
  "description": "Brief description",
  "category": "database|web|file|utility|etc",
  "language": "python|javascript|typescript|etc",
  "stars": 0,
  "repository_url": "GitHub URL",
  "tools": ["list", "of", "tools"],
  "resources": ["list", "of", "resources"],
  "prompts": ["list", "of", "prompts"],
  "install_command": "npm install...",
  "use_cases": "Description of use cases",
  "installation_notes": "Installation instructions"
}
```

### Enhanced Data (from enhancement tool)

```json
{
  "github_data": {
    "readme_content": "Full README text",
    "dependencies": { "npm": {}, "python": {} },
    "topics": ["tags", "from", "github"],
    "license": "MIT",
    "releases": [{ "tag_name": "v1.0.0" }]
  },
  "repo_stats": {
    "stars": 50,
    "forks": 10,
    "open_issues": 5,
    "created_at": "2024-01-01",
    "updated_at": "2024-12-01"
  }
}
```

## 🎯 Example Workflows

### Find Database Tools

1. Open web interface: `poetry run python launcher.py web`
2. Use search: "Python database servers with installation commands"
3. Filter by category: "database"
4. Sort by stars descending
5. Click on interesting servers for full details

### Analyze Server Ecosystem

1. Go to Analytics page in web interface
2. View category distribution
3. Check programming language breakdown
4. Analyze features vs stars correlation

### Export Data for Analysis

1. Use Data Browser page
2. Apply desired filters
3. Click "Export to CSV"
4. Open in Excel/Google Sheets for further analysis

### Enhance Data with GitHub Info

1. Run: `poetry run python launcher.py enhance --max-servers 10`
2. Wait for GitHub data collection
3. New enhanced file created with full repository information

## 🔧 Configuration

### Search Configuration

The self-query retriever uses these metadata fields for filtering:

- **category**: Server category (database, web, file, etc.)
- **language**: Programming language
- **stars**: GitHub stars count
- **tools_count**: Number of available tools
- **resources_count**: Number of available resources
- **prompts_count**: Number of available prompts
- **total_features**: Sum of tools + resources + prompts
- **has_install**: Whether installation command is available

### Web Interface Settings

- **Default results**: 5 per search method
- **Max results**: Adjustable up to 20
- **Search methods**: Auto-selection or manual choice
- **Filters**: Interactive sidebar filters

## 🚨 Troubleshooting

### Import Errors

```bash
# Make sure you're using poetry run
poetry run python packages/haive-mcp/src/haive/mcp/launcher.py web

# Check imports work
poetry run python -c "from haive.core import *; print('✅ Core imports work')"
```

### GitHub Rate Limits

- Get a GitHub token for higher rate limits
- Use `--max-servers` for testing with small datasets
- Enhancement tool respects rate limits automatically

### Memory Issues

- Large datasets may require more memory
- Use filters to reduce working set size
- Parent document retrieval is memory-intensive

### Streamlit Issues

```bash
# Install streamlit if missing
pip install streamlit plotly

# Clear streamlit cache
streamlit cache clear
```

## 📈 Performance Notes

### Search Performance

- **Self-Query**: Fast for structured queries
- **Parent Docs**: Slower but more comprehensive results
- **Similarity**: Fastest for simple searches

### Data Enhancement

- **GitHub API**: ~1-2 seconds per repository
- **Rate Limits**: 5000/hour without token, 60000/hour with token
- **Estimated Time**: ~30 minutes for all 1960 servers (with token)

### Memory Usage

- **Base system**: ~200MB
- **With all documents**: ~500MB
- **Parent retrieval**: ~1GB for full dataset

## 🔮 Future Enhancements

### Planned Features

- [ ] Real-time GitHub data updates
- [ ] MCP server testing and validation
- [ ] Installation automation
- [ ] Server recommendation engine
- [ ] Community ratings and reviews
- [ ] Integration with haive-agents ecosystem

### Data Improvements

- [ ] NPM package information
- [ ] Documentation quality scoring
- [ ] Code quality metrics
- [ ] Server compatibility matrix
- [ ] Performance benchmarks

## 📞 Support

### Getting Help

1. Check this README for common issues
2. Verify you're using `poetry run` for all commands
3. Check the original working RAG agent first
4. Use `launcher.py all` to see all available tools

### Contributing

- Data enhancement scripts are modular and extensible
- Web interface components can be easily modified
- Search algorithms can be tuned for better results

---

**Remember**: All tools are designed to work together. Start with the comprehensive web interface for the best experience, then use individual tools for specific needs.

🚀 **Quick Start**: `poetry run python packages/haive-mcp/src/haive/mcp/launcher.py web`
