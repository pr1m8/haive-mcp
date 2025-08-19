Platform Architecture
====================

Understanding the Haive MCP platform architecture and design principles.

Design Philosophy
-----------------

The Haive MCP architecture is built on three core principles:

1. **Pydantic-First Design** - Pure Pydantic models with no ``__init__`` methods
2. **Intelligent Inheritance** - Platform-based architecture through inheritance  
3. **Real Component Testing** - No mocks, validation with actual components

Pydantic-First Design
~~~~~~~~~~~~~~~~~~~~~

All our models use pure Pydantic initialization and validation:

.. code-block:: python

   # ✅ CORRECT - Pure Pydantic approach
   class MCPBrowserPlugin(PluginPlatform):
       """Plugin for managing MCP servers - no __init__ method"""
       
       model_config = ConfigDict(
           arbitrary_types_allowed=True,
           str_strip_whitespace=True,
           validate_assignment=True
       )
       
       server_directory: Path = Field(..., description="Directory containing servers")
       cache_ttl: int = Field(default=3600, ge=60, le=86400)
       
       # NO __init__ method defined - Pydantic handles everything
       # Validation through field_validator decorators
       # Configuration through ConfigDict

   # ❌ WRONG - Manual initialization breaks our design
   class BadPlugin(PluginPlatform):
       def __init__(self, **kwargs):  # Breaks Pydantic principles
           super().__init__(**kwargs)

Platform Hierarchy
-------------------

The platform follows a clear inheritance hierarchy:

.. code-block:: text

   BasePlatform (haive-dataflow)
       ↓ (adds core platform functionality)
   PluginPlatform (haive-dataflow)
       ↓ (adds plugin-specific features)
   MCPBrowserPlugin (haive-mcp)

BasePlatform
~~~~~~~~~~~~

Foundation for all platform components:

.. code-block:: python

   from haive.dataflow.platform.models import BasePlatform

   class BasePlatform(BaseModel):
       """Core platform functionality"""
       
       model_config = ConfigDict(
           str_strip_whitespace=True,
           validate_assignment=True,
           extra="forbid"
       )
       
       name: str = Field(..., min_length=1, max_length=100)
       description: str = Field(default="")
       version: str = Field(default="1.0.0")
       metadata: Dict[str, Any] = Field(default_factory=dict)

PluginPlatform
~~~~~~~~~~~~~~

Extended platform for plugins:

.. code-block:: python

   from haive.dataflow.platform.models import PluginPlatform

   class PluginPlatform(BasePlatform):
       """Plugin-specific platform extensions"""
       
       plugin_type: str = Field(..., description="Type of plugin")
       enabled: bool = Field(default=True)
       configuration: Dict[str, Any] = Field(default_factory=dict)
       
       def get_router(self) -> APIRouter:
           """Generate FastAPI router - method-based, not __init__"""
           # Implementation here

MCPBrowserPlugin
~~~~~~~~~~~~~~~~

Concrete implementation:

.. code-block:: python

   from haive.mcp.plugins import MCPBrowserPlugin

   class MCPBrowserPlugin(PluginPlatform):
       """Complete MCP browser implementation"""
       
       # Inherits all platform functionality
       # Adds MCP-specific fields and methods
       # No __init__ method needed

Server Information Architecture
-------------------------------

Server information follows a similar hierarchy:

.. code-block:: text

   BaseServerInfo (haive-dataflow)
       ↓ (adds MCP-specific metadata)
   MCPServerInfo (haive-mcp) 
       ↓ (adds local installation details)
   DownloadedServerInfo (haive-mcp)

BaseServerInfo
~~~~~~~~~~~~~~

Foundation for server information:

.. code-block:: python

   from haive.dataflow.platform.models import BaseServerInfo

   class BaseServerInfo(BaseModel):
       """Base server information model"""
       
       name: str = Field(..., description="Server identifier")
       description: str = Field(default="")
       version: str = Field(default="1.0.0")
       capabilities: List[str] = Field(default_factory=list)
       
       @field_validator("name")
       @classmethod
       def normalize_name(cls, v: str) -> str:
           """Normalize names to lowercase-hyphen format"""
           return v.lower().replace(" ", "-").replace("_", "-")

MCPServerInfo
~~~~~~~~~~~~~

MCP-specific server metadata:

.. code-block:: python

   from haive.mcp.models import MCPServerInfo

   class MCPServerInfo(BaseServerInfo):
       """MCP server with protocol-specific metadata"""
       
       mcp_version: str = Field(default="0.1.0")
       transport_types: List[str] = Field(default_factory=lambda: ["stdio"])
       command_template: str = Field(default="")
       
       @field_validator("capabilities")
       @classmethod
       def normalize_capabilities(cls, v: List[str]) -> List[str]:
           """Map capabilities to standard categories"""
           capability_map = {
               "AI": "ai-tools",
               "Database": "database", 
               "Web Search": "web"
           }
           return [capability_map.get(cap, cap.lower()) for cap in v]

DownloadedServerInfo
~~~~~~~~~~~~~~~~~~~~

Complete server with local installation:

.. code-block:: python

   from haive.mcp.models import DownloadedServerInfo

   class DownloadedServerInfo(MCPServerInfo):
       """Downloaded MCP server with local details"""
       
       local_path: Path = Field(..., description="Local installation path")
       file_size: int = Field(..., ge=0, description="File size in bytes")
       installed_date: datetime = Field(default_factory=datetime.now)
       download_source: str = Field(default="unknown")
       is_verified: bool = Field(default=False)

Validation Architecture
-----------------------

Comprehensive validation at multiple levels:

Field Validation
~~~~~~~~~~~~~~~~

.. code-block:: python

   class MCPServerInfo(BaseServerInfo):
       @field_validator("name")
       @classmethod
       def validate_name(cls, v: str) -> str:
           """Validate and normalize server names"""
           if not v.strip():
               raise ValueError("Server name cannot be empty")
           # Auto-normalize: "My Server" → "my-server"
           return v.lower().replace(" ", "-").strip("-")
       
       @field_validator("mcp_version")
       @classmethod
       def validate_mcp_version(cls, v: str) -> str:
           """Validate MCP version format"""
           if not re.match(r"^\d+\.\d+\.\d+$", v):
               raise ValueError("MCP version must be in format X.Y.Z")
           return v

Model Validation
~~~~~~~~~~~~~~~~

.. code-block:: python

   class DownloadedServerInfo(MCPServerInfo):
       @model_validator(mode="after")
       def validate_installation(self) -> "DownloadedServerInfo":
           """Validate installation consistency"""
           if self.local_path and not self.local_path.exists():
               raise ValueError(f"Local path does not exist: {self.local_path}")
           
           if self.file_size == 0 and self.is_verified:
               raise ValueError("Cannot verify server with zero file size")
           
           return self

ConfigDict Settings
~~~~~~~~~~~~~~~~~~~

Comprehensive configuration for all models:

.. code-block:: python

   model_config = ConfigDict(
       # String handling
       str_strip_whitespace=True,      # Auto-strip whitespace
       
       # Validation
       validate_assignment=True,        # Validate on attribute assignment
       use_enum_values=True,           # Use enum values in serialization
       
       # Field handling
       extra="forbid",                 # Prevent unknown fields
       arbitrary_types_allowed=True,   # Allow FastAPI routers, etc.
       
       # JSON Schema
       json_schema_extra={
           "examples": [{
               "name": "postgres-server",
               "capabilities": ["database", "sql"]
           }]
       }
   )

Composition Patterns
--------------------

Factory Methods
~~~~~~~~~~~~~~~

Create platforms from various sources:

.. code-block:: python

   class MCPBrowserPlugin(PluginPlatform):
       @classmethod
       def from_directory_scan(cls, directory: Path) -> "MCPBrowserPlugin":
           """Create plugin by scanning directory"""
           return cls(
               server_directory=directory,
               name=f"browser-{directory.name}",
               plugin_type="browser"
           )
       
       @classmethod
       def from_installer_results(
           cls, 
           results: List[Dict], 
           base_dir: Path
       ) -> "MCPBrowserPlugin":
           """Create plugin from bulk installer results"""
           return cls(
               server_directory=base_dir,
               name="bulk-installer-browser",
               plugin_type="browser",
               metadata={"installer_results": len(results)}
           )

Builder Patterns
~~~~~~~~~~~~~~~~

Build complex configurations:

.. code-block:: python

   class MCPConfigBuilder:
       """Builder for MCP plugin configurations"""
       
       def __init__(self):
           self.config = {}
       
       def with_directory(self, path: Path) -> "MCPConfigBuilder":
           self.config["server_directory"] = path
           return self
       
       def with_caching(self, ttl: int = 3600) -> "MCPConfigBuilder":
           self.config["cache_ttl"] = ttl
           return self
       
       def with_filters(self, categories: List[str]) -> "MCPConfigBuilder":
           self.config["configuration"] = {"allowed_categories": categories}
           return self
       
       def build(self) -> MCPBrowserPlugin:
           return MCPBrowserPlugin.model_validate(self.config)

   # Usage
   plugin = (MCPConfigBuilder()
       .with_directory(Path("/servers"))
       .with_caching(7200)
       .with_filters(["database", "ai-tools"])
       .build())

Integration Patterns
--------------------

FastAPI Integration
~~~~~~~~~~~~~~~~~~~

Platform provides built-in FastAPI support:

.. code-block:: python

   from fastapi import FastAPI, APIRouter

   class MCPBrowserPlugin(PluginPlatform):
       def get_router(self) -> APIRouter:
           """Generate router based on platform configuration"""
           router = APIRouter(tags=[f"MCP-{self.name}"])
           
           @router.get("/servers")
           async def list_servers():
               return await self.load_servers()
           
           @router.get("/servers/{server_name}")
           async def get_server(server_name: str):
               servers = await self.load_servers()
               return next(
                   (s for s in servers if s.name == server_name), 
                   None
               )
           
           return router

   # Integration
   app = FastAPI()
   plugin = MCPBrowserPlugin(server_directory=Path("/servers"))
   app.include_router(plugin.get_router(), prefix="/mcp")

Async Support
~~~~~~~~~~~~~

Built-in async operations:

.. code-block:: python

   class MCPBrowserPlugin(PluginPlatform):
       async def load_servers(self) -> List[DownloadedServerInfo]:
           """Async server loading with caching"""
           if self._is_cache_valid():
               return self.cached_servers
           
           # Async directory scanning
           servers = []
           async for server_path in self._scan_directory_async():
               server_info = await self._load_server_info(server_path)
               servers.append(server_info)
           
           # Update cache
           self.cached_servers = servers
           self.cache_timestamp = datetime.now()
           
           return servers

Performance Considerations
--------------------------

Efficient Model Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ EFFICIENT - Use model_copy for updates
   updated_plugin = plugin.model_copy(
       update={"cache_ttl": 7200}
   )

   # ✅ EFFICIENT - Use model_dump with exclusions  
   api_data = plugin.model_dump(
       exclude={"cached_servers", "cache_timestamp"}
   )

   # ✅ EFFICIENT - Use model_construct for trusted data
   fast_plugin = MCPBrowserPlugin.model_construct(
       name="fast",
       server_directory=Path("/servers"),
       plugin_type="browser"
   )

Caching Strategies
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class MCPBrowserPlugin(PluginPlatform):
       # Cache fields excluded from serialization
       cached_servers: Optional[List[DownloadedServerInfo]] = Field(
           default=None,
           exclude=True  # Don't serialize cache
       )
       
       cache_timestamp: Optional[datetime] = Field(
           default=None,
           exclude=True
       )
       
       def _is_cache_valid(self) -> bool:
           """Check if cache is still valid"""
           if not self.cached_servers or not self.cache_timestamp:
               return False
           
           age = datetime.now() - self.cache_timestamp
           return age.total_seconds() < self.cache_ttl

Testing Architecture
--------------------

Following our "no mocks" philosophy:

Real Component Testing
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from pathlib import Path
   from haive.mcp.plugins import MCPBrowserPlugin

   def test_plugin_creation_real():
       """Test plugin creation with real Pydantic validation"""
       plugin = MCPBrowserPlugin(
           server_directory=Path("/tmp/test_servers")
       )
       
       # Verify Pydantic validation worked
       assert isinstance(plugin.server_directory, Path)
       assert plugin.cache_ttl == 3600  # Default value
       assert plugin.plugin_type == "browser"

   def test_server_validation_real():
       """Test server validation with real Pydantic"""
       from haive.mcp.models import MCPServerInfo
       
       server = MCPServerInfo(
           name="PostgreSQL Server",  # Will be normalized
           capabilities=["Database", "SQL"]  # Will be normalized
       )
       
       assert server.name == "postgresql-server"
       assert server.capabilities == ["database", "sql"]

Integration Testing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_fastapi_integration_real():
       """Test FastAPI integration with real components"""
       from fastapi.testclient import TestClient
       from fastapi import FastAPI
       
       app = FastAPI()
       plugin = MCPBrowserPlugin(server_directory=Path("/tmp"))
       app.include_router(plugin.get_router(), prefix="/mcp")
       
       client = TestClient(app)
       response = client.get("/mcp/servers")
       
       assert response.status_code == 200
       # Test actual response structure

Architecture Benefits
---------------------

1. **Type Safety** - Full Pydantic validation and type hints
2. **Maintainability** - Clear inheritance hierarchy
3. **Extensibility** - Easy to add new platform types
4. **Performance** - Efficient caching and serialization
5. **Testing** - Real component validation
6. **Integration** - Built-in FastAPI and async support

Next Steps
----------

- :doc:`mcp-browser-plugin` - Detailed plugin usage
- :doc:`fastapi-integration` - Web API development  
- :doc:`custom-plugins` - Building your own plugins
- :doc:`real-world-examples` - Production usage patterns