# haive-mcp/src/haive/mcp/plugins/browser_plugin.py
"""
MCP Browser Plugin - Manage Our 63 Downloaded MCP Servers

This plugin inherits from PluginPlatform and specializes in managing the 63 MCP servers
we successfully downloaded using our bulk installer. It implements the intelligent
inheritance pattern from our architecture plan.

Key Features:
- Inherits all PluginPlatform capabilities
- Loads servers from our actual CSV and install report data
- Intelligent caching for performance
- FastAPI route registration for server browsing
- Real integration with our download infrastructure

Architecture:
- Inherits from: PluginPlatform (which inherits from BasePlatform)
- Manages: DownloadedServerInfo instances
- Provides: Server discovery, health checks, browsing interface
- Integrates: Real CSV data and install reports from our bulk download
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import Field, field_validator, ConfigDict

# Import our platform models
from haive.dataflow.platform.models import (
    PluginPlatform,
    DownloadedServerInfo,
    MCPServerInfo,
    validate_server_inheritance,
)

logger = logging.getLogger(__name__)


class MCPBrowserPlugin(PluginPlatform):
    """Plugin for managing our 63 downloaded MCP servers.
    
    This plugin inherits from PluginPlatform and specializes in managing the MCP servers
    we successfully downloaded during our bulk download session. It demonstrates the
    intelligent inheritance pattern by extending platform capabilities while maintaining
    the Pydantic-first design philosophy.
    
    Inheritance Features:
    - Inherits: platform_id, status, metadata, lifecycle methods from BasePlatform (via PluginPlatform)
    - Inherits: entry_point, routes, priorities, dependencies from PluginPlatform
    - Extends: MCP-specific server management and discovery capabilities
    - Specializes: Downloaded server data integration and caching
    
    Real Integration:
    - Works with our actual mcp_servers_data.csv file
    - Uses our install report JSON files
    - Loads our 63 successfully downloaded servers
    - Provides web interface for browsing servers
    
    Examples:
        Basic plugin creation::
        
            plugin = MCPBrowserPlugin()
            # Uses intelligent defaults for all inherited fields
            
        With custom data paths::
        
            plugin = MCPBrowserPlugin(
                servers_data_file=Path("custom/path/servers.csv"),
                install_reports_pattern="custom_install_*.json"
            )
            
        Plugin initialization::
        
            await plugin.initialize()
            servers = plugin.get_servers()
            print(f"Loaded {len(servers)} downloaded servers")
    """
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True  # Allow FastAPI router and other complex types
    )
    
    # Plugin identity - inherited and specialized from PluginPlatform
    platform_id: str = Field(default="mcp-browser-plugin")
    platform_name: str = Field(default="MCP Server Browser")
    description: str = Field(default="Browse and manage 63+ downloaded MCP servers")
    entry_point: str = Field(default="haive.mcp.plugins:MCPBrowserPlugin")
    routes_prefix: str = Field(default="/mcp")
    
    # Plugin capabilities - inherited and enabled from PluginPlatform
    provides_servers: bool = Field(default=True)
    provides_discovery: bool = Field(default=True)
    provides_health_checks: bool = Field(default=True)
    priority: int = Field(default=10)  # High priority - core functionality
    
    # Platform capabilities - inherited from BasePlatform and enabled
    supports_discovery: bool = Field(default=True)
    supports_health_monitoring: bool = Field(default=True)
    
    # Plugin-specific configuration for our downloaded servers
    downloaded_servers_path: Path = Field(
        default_factory=lambda: Path.cwd(),
        description="Path containing downloaded server directories"
    )
    servers_data_file: Path = Field(
        default_factory=lambda: Path("scratches/mcp-analysis/mcp_servers_data.csv"),
        description="CSV file with server metadata from our analysis"
    )
    install_reports_pattern: str = Field(
        default="mcp_install_report_*.json",
        description="Pattern for install report files from our bulk installer"
    )
    
    # Intelligent caching system - performance optimization
    cached_servers: Optional[List[DownloadedServerInfo]] = Field(
        default=None,
        exclude=True,  # Don't serialize in model dumps
        description="Cached server list for performance"
    )
    cache_timestamp: Optional[datetime] = Field(
        default=None,
        exclude=True,
        description="When cache was last updated"
    )
    cache_ttl_seconds: int = Field(
        default=300,
        description="Cache TTL in seconds (5 minutes default)",
        ge=60,
        le=3600
    )
    
    # FastAPI router for plugin routes
    router: Optional[APIRouter] = Field(default=None, exclude=True)
    
    @field_validator("servers_data_file")
    @classmethod
    def validate_servers_data_file_exists(cls, v: Path) -> Path:
        """Validate that servers data file exists (when not using defaults)."""
        if v != Path("scratches/mcp-analysis/mcp_servers_data.csv") and not v.exists():
            logger.warning(f"Servers data file not found: {v}")
        return v
    
    def get_servers(self) -> List[DownloadedServerInfo]:
        """Get our 63 downloaded servers with intelligent caching.
        
        This method implements intelligent caching to avoid repeatedly loading and
        processing our server data. It uses the cache TTL to determine when to
        refresh the data.
        
        Returns:
            List of DownloadedServerInfo instances for our downloaded servers
            
        Examples:
            >>> plugin = MCPBrowserPlugin()
            >>> servers = plugin.get_servers()
            >>> len(servers)
            63
            >>> all(s.source == ServerSource.DOWNLOADED for s in servers)
            True
        """
        # Check cache first - intelligent caching pattern
        if self._is_cache_valid():
            logger.debug("Returning cached server list")
            return self.cached_servers or []
        
        logger.info("Loading fresh server data from CSV and install reports")
        
        # Load fresh data from our real download infrastructure
        try:
            servers = self._load_servers_from_data()
            
            # Update cache with fresh data
            self.cached_servers = servers
            self.cache_timestamp = datetime.utcnow()
            
            # Update metadata to track loading
            self.add_metadata("last_server_load", datetime.utcnow().isoformat())
            self.add_metadata("loaded_server_count", len(servers))
            
            logger.info(f"Successfully loaded {len(servers)} servers from data")
            return servers
            
        except Exception as e:
            logger.error(f"Failed to load servers from data: {e}")
            # Return cached data if available, empty list otherwise
            return self.cached_servers or []
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid based on TTL.
        
        Returns:
            True if cache exists and is within TTL, False otherwise
        """
        if not self.cached_servers or not self.cache_timestamp:
            return False
        
        age_seconds = (datetime.utcnow() - self.cache_timestamp).total_seconds()
        return age_seconds < self.cache_ttl_seconds
    
    def _load_servers_from_data(self) -> List[DownloadedServerInfo]:
        """Load servers from our actual CSV and install reports.
        
        This method integrates with our real download infrastructure, loading
        server data from the CSV file we generated during analysis and the
        install reports from our bulk installer.
        
        Returns:
            List of DownloadedServerInfo instances
            
        Raises:
            FileNotFoundError: If required data files are missing
            ValueError: If data format is invalid
        """
        servers = []
        
        # Load CSV data - our server analysis results
        if not self.servers_data_file.exists():
            logger.warning(f"CSV data file not found: {self.servers_data_file}")
            return []
        
        try:
            df = pd.read_csv(self.servers_data_file)
            logger.debug(f"Loaded CSV with {len(df)} server records")
        except Exception as e:
            logger.error(f"Failed to load CSV data: {e}")
            return []
        
        # Find latest install report - our bulk installer results
        install_report = self._get_latest_install_report()
        if not install_report:
            logger.warning("No install reports found")
            return []
        
        installed_servers = install_report.get('installed_servers', [])
        install_log = install_report.get('install_log', [])
        session_id = install_report.get('session_id', 'unknown-session')
        
        logger.info(f"Processing {len(installed_servers)} installed servers from session {session_id}")
        
        # Create server objects for each successfully installed server
        for server_name in installed_servers:
            try:
                # Find server in CSV data
                server_rows = df[df['name'] == server_name]
                if server_rows.empty:
                    logger.debug(f"Server {server_name} not found in CSV data")
                    continue
                
                csv_data = server_rows.iloc[0].to_dict()
                
                # Find corresponding install entry
                install_entry = next(
                    (entry for entry in install_log if entry.get('name') == server_name),
                    {}
                )
                
                # Create DownloadedServerInfo using factory method
                server = DownloadedServerInfo.from_csv_and_install_report(
                    csv_data, 
                    install_entry,
                    session_id
                )
                
                servers.append(server)
                logger.debug(f"Created server: {server.server_name}")
                
            except Exception as e:
                logger.warning(f"Failed to create server {server_name}: {e}")
                continue
        
        logger.info(f"Successfully created {len(servers)} server objects")
        return servers
    
    def _get_latest_install_report(self) -> Optional[Dict[str, Any]]:
        """Get the latest install report from our bulk installer.
        
        Returns:
            Install report data if found, None otherwise
        """
        try:
            # Find all install report files matching our pattern
            report_files = list(Path('.').glob(self.install_reports_pattern))
            if not report_files:
                logger.debug(f"No install report files found matching pattern: {self.install_reports_pattern}")
                return None
            
            # Get most recent report file by modification time
            latest_file = max(report_files, key=lambda p: p.stat().st_mtime)
            logger.debug(f"Using latest install report: {latest_file}")
            
            # Load and return report data
            with open(latest_file) as f:
                report_data = json.load(f)
            
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to load install reports: {e}")
            return None
    
    def get_server_by_name(self, server_name: str) -> Optional[DownloadedServerInfo]:
        """Get a specific server by name.
        
        Args:
            server_name: Server name to search for
            
        Returns:
            Server if found, None otherwise
        """
        servers = self.get_servers()
        return next((s for s in servers if s.server_name == server_name), None)
    
    def get_servers_by_language(self, language: str) -> List[DownloadedServerInfo]:
        """Get servers filtered by programming language.
        
        Args:
            language: Programming language to filter by
            
        Returns:
            List of servers matching the language
        """
        servers = self.get_servers()
        return [s for s in servers if s.language and s.language.lower() == language.lower()]
    
    def get_servers_by_stars(self, min_stars: int = 0) -> List[DownloadedServerInfo]:
        """Get servers with at least the specified number of stars.
        
        Args:
            min_stars: Minimum number of GitHub stars
            
        Returns:
            List of servers sorted by star count (descending)
        """
        servers = self.get_servers()
        filtered = [s for s in servers if s.stars and s.stars >= min_stars]
        return sorted(filtered, key=lambda s: s.stars or 0, reverse=True)
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get comprehensive plugin statistics.
        
        Returns:
            Dictionary with plugin statistics and server information
        """
        servers = self.get_servers()
        
        # Language distribution
        languages = {}
        for server in servers:
            if server.language:
                languages[server.language] = languages.get(server.language, 0) + 1
        
        # Star distribution
        stars = [s.stars for s in servers if s.stars is not None]
        total_stars = sum(stars) if stars else 0
        avg_stars = total_stars / len(stars) if stars else 0
        
        # Transport distribution
        transports = {}
        for server in servers:
            transport = str(server.transport)
            transports[transport] = transports.get(transport, 0) + 1
        
        return {
            "plugin_info": {
                "platform_id": self.platform_id,
                "platform_name": self.platform_name,
                "status": str(self.status),
                "cache_ttl": self.cache_ttl_seconds
            },
            "server_stats": {
                "total_servers": len(servers),
                "languages": languages,
                "transports": transports,
                "total_stars": total_stars,
                "average_stars": round(avg_stars, 1)
            },
            "inheritance_info": {
                "is_plugin_platform": True,
                "provides_servers": self.provides_servers,
                "provides_discovery": self.provides_discovery,
                "plugin_priority": self.priority
            },
            "cache_info": {
                "is_cached": self.cached_servers is not None,
                "cache_age_seconds": (
                    (datetime.utcnow() - self.cache_timestamp).total_seconds()
                    if self.cache_timestamp else None
                ),
                "cache_valid": self._is_cache_valid()
            }
        }
    
    def register_routes(self, app: FastAPI) -> None:
        """Register plugin routes with FastAPI app.
        
        This method creates FastAPI routes for browsing our downloaded servers.
        It's called by the platform during plugin initialization.
        
        Args:
            app: FastAPI application instance to register routes with
        """
        if self.router is None:
            self.router = APIRouter(prefix=self.routes_prefix, tags=["MCP Browser"])
            self._setup_routes()
        
        app.include_router(self.router)
        logger.info(f"Registered MCP browser routes with prefix: {self.routes_prefix}")
    
    def _setup_routes(self) -> None:
        """Setup FastAPI routes for the plugin."""
        if not self.router:
            return
        
        @self.router.get("/servers")
        async def list_servers(
            language: Optional[str] = Query(None, description="Filter by programming language"),
            min_stars: Optional[int] = Query(0, description="Minimum GitHub stars"),
            limit: Optional[int] = Query(100, description="Maximum number of servers to return")
        ):
            """List downloaded MCP servers with optional filtering."""
            try:
                servers = self.get_servers()
                
                # Apply filters
                if language:
                    servers = [s for s in servers if s.language and s.language.lower() == language.lower()]
                
                if min_stars and min_stars > 0:
                    servers = [s for s in servers if s.stars and s.stars >= min_stars]
                
                # Apply limit
                servers = servers[:limit] if limit else servers
                
                return {
                    "servers": [s.model_dump() for s in servers],
                    "total": len(servers),
                    "filters_applied": {
                        "language": language,
                        "min_stars": min_stars,
                        "limit": limit
                    }
                }
                
            except Exception as e:
                logger.error(f"Error listing servers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/servers/{server_name:path}")
        async def get_server_details(server_name: str):
            """Get detailed information about a specific server."""
            try:
                server = self.get_server_by_name(server_name)
                if not server:
                    raise HTTPException(status_code=404, detail=f"Server not found: {server_name}")
                
                # Get comprehensive information
                server_data = server.model_dump()
                download_summary = server.get_download_summary()
                inheritance_validation = validate_server_inheritance(server)
                
                return {
                    "server": server_data,
                    "download_summary": download_summary,
                    "inheritance_validation": inheritance_validation
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting server details: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/stats")
        async def get_plugin_stats():
            """Get comprehensive plugin and server statistics."""
            try:
                return self.get_plugin_stats()
            except Exception as e:
                logger.error(f"Error getting plugin stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/languages")
        async def list_languages():
            """Get list of all programming languages in our downloaded servers."""
            try:
                servers = self.get_servers()
                languages = list(set(s.language for s in servers if s.language))
                languages.sort()
                
                return {
                    "languages": languages,
                    "total": len(languages)
                }
                
            except Exception as e:
                logger.error(f"Error listing languages: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/cache/refresh")
        async def refresh_cache():
            """Manually refresh the server cache."""
            try:
                # Clear cache
                self.cached_servers = None
                self.cache_timestamp = None
                
                # Reload servers
                servers = self.get_servers()
                
                return {
                    "message": "Cache refreshed successfully",
                    "servers_loaded": len(servers),
                    "refresh_time": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error refreshing cache: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def initialize(self) -> None:
        """Initialize plugin with validation and server loading.
        
        This method extends the base PluginPlatform initialization with
        MCP-specific setup and validation.
        """
        logger.info(f"Initializing {self.platform_name}...")
        
        # Call parent initialization (from PluginPlatform)
        await super().initialize()
        
        # Validate our data sources exist
        if self.servers_data_file.exists():
            logger.info(f"Found servers data file: {self.servers_data_file}")
        else:
            logger.warning(f"Servers data file not found: {self.servers_data_file}")
        
        # Load and validate server data
        try:
            servers = self.get_servers()
            if not servers:
                logger.warning("No downloaded servers found")
            else:
                logger.info(f"Successfully loaded {len(servers)} downloaded servers")
                
                # Update metadata with initialization results
                self.add_metadata("servers_loaded", len(servers))
                self.add_metadata("data_sources_validated", True)
                self.add_metadata("initialization_successful", True)
                
        except Exception as e:
            logger.error(f"Failed to load servers during initialization: {e}")
            self.add_metadata("initialization_error", str(e))
            self.add_metadata("initialization_successful", False)
            # Don't raise - allow plugin to start even if server loading fails
        
        logger.info(f"{self.platform_name} initialization complete")
    
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        logger.info(f"Cleaning up {self.platform_name}...")
        
        # Clear cache
        self.cached_servers = None
        self.cache_timestamp = None
        
        # Call parent cleanup (from PluginPlatform)
        await super().cleanup()
        
        logger.info(f"{self.platform_name} cleanup complete")