#!/bin/bash

# Fix imports in all __init__.py files to use haive.mcp prefix

echo "Fixing imports in haive-mcp package..."

# Fix cli/__init__.py
sed -i 's/from cli\./from haive.mcp.cli./g' src/haive/mcp/cli/__init__.py

# Fix agents/__init__.py  
sed -i 's/from agents\./from haive.mcp.agents./g' src/haive/mcp/agents/__init__.py

# Fix discovery/__init__.py
sed -i 's/from discovery\./from haive.mcp.discovery./g' src/haive/mcp/discovery/__init__.py

# Fix tools/__init__.py
sed -i 's/from tools\./from haive.mcp.tools./g' src/haive/mcp/tools/__init__.py

# Fix mixins/__init__.py
sed -i 's/from mixins\./from haive.mcp.mixins./g' src/haive/mcp/mixins/__init__.py

# Fix servers/__init__.py
sed -i 's/from servers\./from haive.mcp.servers./g' src/haive/mcp/servers/__init__.py

# Fix documentation/__init__.py
sed -i 's/from documentation\./from haive.mcp.documentation./g' src/haive/mcp/documentation/__init__.py

# Fix utils/__init__.py
sed -i 's/from utils\./from haive.mcp.utils./g' src/haive/mcp/utils/__init__.py

# Fix installers/__init__.py
sed -i 's/from installers\./from haive.mcp.installers./g' src/haive/mcp/installers/__init__.py

# Fix downloader/__init__.py
sed -i 's/from downloader\./from haive.mcp.downloader./g' src/haive/mcp/downloader/__init__.py

echo "Import fixes complete!"