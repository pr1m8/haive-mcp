# PubChem MCP Server

[![smithery badge](https://smithery.ai/badge/@JackKuo666/pubchem-mcp-server)](https://smithery.ai/server/@JackKuo666/pubchem-mcp-server)

🧪 Enable AI assistants to search and access chemical compound information through a simple MCP interface.

The PubChem MCP Server provides a bridge between AI assistants and PubChem's chemical database through the Model Context Protocol (MCP). It allows AI models to search for chemical compounds and access their detailed information in a programmatic way.

🤝 Contribute • 📝 Report Bug

## ✨ Core Features

- 🔎 Compound Search: Query PubChem compounds by name, SMILES, or CID ✅
- 🧪 Chemical Structure: Access molecular structures and identifiers ✅
- 📊 Property Data: Retrieve detailed chemical and physical properties ✅
- 🔬 Advanced Search: Combine multiple parameters for precise queries ✅
- 🧬 Molecular Visualization: Generate and display molecular structures 📝
- 📈 Property Analysis: Compare properties across multiple compounds 📝
- 🗃️ Local Storage: Save frequently used compounds for faster access 📝
- 📝 Chemistry Prompts: Specialized prompts for chemical analysis 📝

## 🚀 Quick Start

### Installing via Smithery

To install PubChem Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@JackKuo666/pubchem-mcp-server):

#### Claude

```bash
npx -y @smithery/cli@latest install @JackKuo666/pubchem-mcp-server --client claude --config "{}"
```

#### Cursor

Paste the following into Settings → Cursor Settings → MCP → Add new server:

- Mac/Linux

```s
npx -y @smithery/cli@latest run @JackKuo666/pubchem-mcp-server --client cursor --config "{}"
```

#### Windsurf

```sh
npx -y @smithery/cli@latest install @JackKuo666/pubchem-mcp-server --client windsurf --config "{}"
```

### CLine

```sh
npx -y @smithery/cli@latest install @JackKuo666/pubchem-mcp-server --client cline --config "{}"
```

### Installing Manually

Install using uv:

```bash
uv tool install pubchem-mcp-server
```

For development:

```bash
# Clone and set up development environment
git clone https://github.com/JackKuo666/PubChem-MCP-Server.git
cd PubChem-MCP-Server

# Create and activate virtual environment
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 📊 Usage

Start the MCP server:

```bash
python pubchem_server.py
```

Once the server is running, you can use the provided MCP tools in your AI assistant or application. Here are some examples of how to use the tools:

### Example 1: Search for compounds by name

```python
result = await mcp.use_tool("search_pubchem_by_name", {
    "name": "aspirin",
    "max_results": 3
})
print(result)
```

### Example 2: Search for compounds by SMILES notation

```python
result = await mcp.use_tool("search_pubchem_by_smiles", {
    "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin's SMILES
    "max_results": 2
})
print(result)
```

### Example 3: Get detailed information for a specific compound

```python
result = await mcp.use_tool("get_pubchem_compound_by_cid", {
    "cid": 2244  # Aspirin's CID
})
print(result)
```

### Example 4: Perform an advanced search with multiple parameters

```python
result = await mcp.use_tool("search_pubchem_advanced", {
    "name": "caffeine",
    "formula": "C8H10N4O2",
    "max_results": 2
})
print(result)
```

These examples demonstrate how to use the four main tools provided by the PubChem MCP Server. Adjust the parameters as needed for your specific use case.

## 🛠 MCP Tools

The PubChem MCP Server provides the following tools:

### search_pubchem_by_name

Search for chemical compounds on PubChem using a compound name.

**Parameters:**

- `name` (str): Name of the chemical compound
- `max_results` (int, optional): Maximum number of results to return (default: 5)

**Returns:** List of dictionaries containing compound information

### search_pubchem_by_smiles

Search for chemical compounds on PubChem using a SMILES string.

**Parameters:**

- `smiles` (str): SMILES notation of the chemical compound
- `max_results` (int, optional): Maximum number of results to return (default: 5)

**Returns:** List of dictionaries containing compound information

### get_pubchem_compound_by_cid

Fetch detailed information about a chemical compound using its PubChem CID.

**Parameters:**

- `cid` (int): PubChem Compound ID (CID)

**Returns:** Dictionary containing compound information

### search_pubchem_advanced

Perform an advanced search for compounds on PubChem.

**Parameters:**

- `name` (str, optional): Name of the chemical compound
- `smiles` (str, optional): SMILES notation of the chemical compound
- `formula` (str, optional): Molecular formula
- `cid` (int, optional): PubChem Compound ID
- `max_results` (int, optional): Maximum number of results to return (default: 5)

**Returns:** List of dictionaries containing compound information

## Usage with Claude Desktop

Add this configuration to your `claude_desktop_config.json`:

(Mac OS)

```json
{
  "mcpServers": {
    "pubchem": {
      "command": "python",
      "args": ["-m", "pubchem-mcp-server"]
    }
  }
}
```

(Windows version):

```json
{
  "mcpServers": {
    "pubchem": {
      "command": "C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      "args": ["-m", "pubchem-mcp-server"]
    }
  }
}
```

Using with Cline

```json
{
  "mcpServers": {
    "pubchem": {
      "command": "bash",
      "args": [
        "-c",
        "source /home/YOUR/PATH/mcp-hub/PubChem-MCP-Server/.venv/bin/activate && python /home/YOUR/PATH/mcp-hub/PubChem-MCP-Server/pubchem_server.py"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

After restarting Claude Desktop, the following capabilities will be available:

### Searching Compounds

You can ask Claude to search for chemical compounds using queries like:

```
Can you search PubChem for information about aspirin?
```

The search will return basic information about matching compounds including:

• Compound name

• CID (PubChem Compound ID)

• Molecular formula

• Molecular weight

### Getting Compound Details

Once you have a CID, you can ask for more details:

```
Can you show me the details for compound with CID 2244?
```

This will return:

• IUPAC name

• Molecular formula

• Molecular weight

• SMILES notation

• InChI and InChIKey

• Physical and chemical properties

• Synonyms

## 📝 TODO

### visualize_compound

Generate and display a 2D or 3D visualization of a chemical compound.

### compare_compounds

Compare properties and structures of multiple compounds.

### save_compound

Save a compound locally for faster access.

### list_saved_compounds

List all saved compounds.

### 📝 Chemistry Prompts

The server will offer specialized prompts to help analyze chemical compounds:

#### Compound Analysis Prompt

A comprehensive workflow for analyzing chemical compounds that only requires a compound ID:

```python
result = await call_prompt("deep-compound-analysis", {
    "compound_id": "2244"
})
```

This prompt will include:

- Detailed instructions for using available tools
- A systematic workflow for compound analysis
- Comprehensive analysis structure covering:
  - Chemical structure and properties
  - Pharmacological properties
  - Biological activities
  - Applications and uses
  - Safety and toxicity information
  - Related compounds

## 📁 Project Structure

- `pubchem_server.py`: The main MCP server implementation using FastMCP
- `pubchem_search.py`: Contains example code for searching PubChem

## 🔧 Dependencies

- Python 3.10+
- FastMCP
- asyncio
- logging
- pubchempy (for PubChem API access)
- pandas (for data handling)

You can install the required dependencies using:

```bash
pip install mcp pubchempy pandas
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is for research purposes only. Please respect PubChem's terms of service and use this tool responsibly.
