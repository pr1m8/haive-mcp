"""MCP Connection Management.

This module provides connection management utilities for MCP clients.
It handles connection pooling, health monitoring, and connection lifecycle
management for different transport types.
"""

import asyncio
import logging
import time
from typing import Dict, Optional, List, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from .mcp_client import MCPClient
from .transport import MCPTransport, StdioTransport, HttpTransport
from .exceptions import MCPConnectionError, MCPTimeoutError

logger = logging.getLogger(__name__)


class ConnectionStatus(str, Enum):
    """Connection status states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class ConnectionInfo:
    """Information about an MCP connection."""
    name: str
    transport: MCPTransport
    client: Optional[MCPClient] = None
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    last_connected: Optional[float] = None
    last_error: Optional[str] = None
    reconnect_attempts: int = 0
    health_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPConnection:
    """MCP connection manager with health monitoring and auto-reconnection.
    
    This class manages individual MCP connections with features like:
        - Health monitoring and scoring
        - Automatic reconnection with backoff
        - Connection lifecycle management
        - Error tracking and recovery
        - Performance metrics
        
    Examples:
        Basic connection management::
        
            from haive.mcp.client import MCPConnection, StdioTransport
            
            transport = StdioTransport("npx", ["-y", "@modelcontextprotocol/server-filesystem"])
            connection = MCPConnection("filesystem", transport)
            
            await connection.connect()
            client = connection.get_client()
            tools = await client.list_tools()
            await connection.disconnect()
            
        With health monitoring::
        
            connection = MCPConnection(
                "filesystem",
                transport,
                health_check_interval=30.0,
                auto_reconnect=True
            )
            
            await connection.start_monitoring()
            # Connection will be monitored and auto-reconnected
            
        Connection status checking::
        
            if connection.is_healthy():
                client = connection.get_client()
                result = await client.call_tool("read_file", {"path": "/tmp/test"})
    """
    
    def __init__(
        self,
        name: str,
        transport: MCPTransport,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 60.0,
        health_check_interval: float = 30.0,
        connection_timeout: float = 30.0
    ):
        """Initialize MCP connection manager.
        
        Args:
            name: Connection name/identifier
            transport: Transport implementation
            auto_reconnect: Enable automatic reconnection
            max_reconnect_attempts: Maximum reconnection attempts
            reconnect_delay: Initial reconnection delay (seconds)
            max_reconnect_delay: Maximum reconnection delay (seconds)
            health_check_interval: Health check interval (seconds)
            connection_timeout: Connection timeout (seconds)
        """
        self.name = name
        self.transport = transport
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay
        self.health_check_interval = health_check_interval
        self.connection_timeout = connection_timeout
        
        # Connection state
        self.client: Optional[MCPClient] = None
        self.status = ConnectionStatus.DISCONNECTED
        self.last_connected: Optional[float] = None
        self.last_error: Optional[str] = None
        self.reconnect_attempts = 0
        self.health_score = 1.0
        
        # Monitoring
        self._monitor_task: Optional[asyncio.Task] = None
        self._connection_lock = asyncio.Lock()
        self._health_history: List[float] = []
        self._error_count = 0
        self._last_health_check = 0.0
        
        # Metrics
        self.connection_count = 0
        self.error_count = 0
        self.total_uptime = 0.0
        self.last_operation_time = 0.0
        
    async def connect(self, timeout: Optional[float] = None) -> MCPClient:
        """Connect to the MCP server.
        
        Args:
            timeout: Connection timeout (uses default if None)
            
        Returns:
            Connected MCP client
            
        Raises:
            MCPConnectionError: If connection fails
        """
        async with self._connection_lock:
            if self.status == ConnectionStatus.CONNECTED and self.client:
                return self.client
                
            if self.status == ConnectionStatus.CONNECTING:
                raise MCPConnectionError(f"Connection {self.name} already in progress")
                
            self.status = ConnectionStatus.CONNECTING
            
            try:
                logger.info(f"Connecting to MCP server: {self.name}")
                
                # Create client
                self.client = MCPClient(
                    transport=self.transport,
                    timeout=timeout or self.connection_timeout,
                    auto_reconnect=False  # We handle reconnection ourselves
                )
                
                # Connect with timeout
                connect_timeout = timeout or self.connection_timeout
                await asyncio.wait_for(
                    self.client.connect(),
                    timeout=connect_timeout
                )
                
                # Update state
                self.status = ConnectionStatus.CONNECTED
                self.last_connected = time.time()
                self.last_error = None
                self.reconnect_attempts = 0
                self.connection_count += 1
                
                logger.info(f"Successfully connected to MCP server: {self.name}")
                return self.client
                
            except Exception as e:
                self.status = ConnectionStatus.ERROR
                self.last_error = str(e)
                self._error_count += 1
                self.error_count += 1
                
                logger.error(f"Failed to connect to MCP server {self.name}: {e}")
                
                if isinstance(e, asyncio.TimeoutError):
                    raise MCPTimeoutError(f"Connection to {self.name} timed out")
                elif isinstance(e, MCPConnectionError):
                    raise
                else:
                    raise MCPConnectionError(f"Connection to {self.name} failed: {e}")
                    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        async with self._connection_lock:
            if self.client:
                try:
                    await self.client.disconnect()
                except Exception as e:
                    logger.warning(f"Error during disconnect of {self.name}: {e}")
                finally:
                    self.client = None
                    
            self.status = ConnectionStatus.DISCONNECTED
            
            # Update uptime
            if self.last_connected:
                self.total_uptime += time.time() - self.last_connected
                
            logger.info(f"Disconnected from MCP server: {self.name}")
            
    async def reconnect(self) -> Optional[MCPClient]:
        """Attempt to reconnect to the server.
        
        Returns:
            Connected client if successful, None if failed
        """
        if not self.auto_reconnect:
            return None
            
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.warning(
                f"Max reconnection attempts ({self.max_reconnect_attempts}) "
                f"reached for {self.name}"
            )
            return None
            
        self.status = ConnectionStatus.RECONNECTING
        self.reconnect_attempts += 1
        
        # Calculate backoff delay
        delay = min(
            self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)),
            self.max_reconnect_delay
        )
        
        logger.info(
            f"Attempting reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts} "
            f"to {self.name} in {delay:.1f}s"
        )
        
        await asyncio.sleep(delay)
        
        try:
            return await self.connect()
        except Exception as e:
            logger.warning(f"Reconnection attempt {self.reconnect_attempts} failed for {self.name}: {e}")
            return None
            
    def get_client(self) -> MCPClient:
        """Get the MCP client if connected.
        
        Returns:
            MCP client instance
            
        Raises:
            MCPConnectionError: If not connected
        """
        if self.status != ConnectionStatus.CONNECTED or not self.client:
            raise MCPConnectionError(f"Connection {self.name} is not active")
            
        return self.client
        
    def is_connected(self) -> bool:
        """Check if connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        return self.status == ConnectionStatus.CONNECTED and self.client is not None
        
    def is_healthy(self, threshold: float = 0.7) -> bool:
        """Check if connection is healthy.
        
        Args:
            threshold: Health score threshold (0.0-1.0)
            
        Returns:
            True if health score is above threshold
        """
        return self.health_score >= threshold
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the connection.
        
        Returns:
            Health check results
        """
        health_info = {
            "name": self.name,
            "status": self.status.value,
            "connected": self.is_connected(),
            "health_score": self.health_score,
            "last_connected": self.last_connected,
            "last_error": self.last_error,
            "reconnect_attempts": self.reconnect_attempts,
            "connection_count": self.connection_count,
            "error_count": self.error_count,
            "uptime": self.total_uptime,
            "transport_type": type(self.transport).__name__
        }
        
        if self.is_connected():
            try:
                # Perform actual health check via client
                client_health = await self.client.health_check()
                health_info.update(client_health)
                
                # Update health score based on success
                self._update_health_score(True)
                
            except Exception as e:
                health_info["error"] = str(e)
                self._update_health_score(False)
                
                # Trigger reconnection if auto-reconnect enabled
                if self.auto_reconnect:
                    asyncio.create_task(self.reconnect())
                    
        else:
            health_info["error"] = "Not connected"
            
        self._last_health_check = time.time()
        return health_info
        
    async def start_monitoring(self) -> None:
        """Start background health monitoring."""
        if self._monitor_task and not self._monitor_task.done():
            return
            
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started health monitoring for connection: {self.name}")
        
    async def stop_monitoring(self) -> None:
        """Stop background health monitoring."""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
                
        logger.info(f"Stopped health monitoring for connection: {self.name}")
        
    def get_info(self) -> ConnectionInfo:
        """Get connection information.
        
        Returns:
            ConnectionInfo object with current state
        """
        return ConnectionInfo(
            name=self.name,
            transport=self.transport,
            client=self.client,
            status=self.status,
            last_connected=self.last_connected,
            last_error=self.last_error,
            reconnect_attempts=self.reconnect_attempts,
            health_score=self.health_score,
            metadata={
                "connection_count": self.connection_count,
                "error_count": self.error_count,
                "total_uptime": self.total_uptime,
                "transport_type": type(self.transport).__name__
            }
        )
        
    async def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        try:
            while True:
                await asyncio.sleep(self.health_check_interval)
                
                try:
                    await self.health_check()
                except Exception as e:
                    logger.error(f"Health check error for {self.name}: {e}")
                    
        except asyncio.CancelledError:
            logger.debug(f"Monitoring cancelled for {self.name}")
            raise
        except Exception as e:
            logger.error(f"Monitoring loop error for {self.name}: {e}")
            
    def _update_health_score(self, success: bool) -> None:
        """Update health score based on operation success."""
        # Add to history
        self._health_history.append(1.0 if success else 0.0)
        
        # Keep only recent history (last 10 checks)
        if len(self._health_history) > 10:
            self._health_history = self._health_history[-10:]
            
        # Calculate weighted score (recent events have more weight)
        if self._health_history:
            weights = [0.5 ** i for i in range(len(self._health_history))]
            weights.reverse()  # Recent events get higher weights
            
            weighted_sum = sum(h * w for h, w in zip(self._health_history, weights))
            weight_sum = sum(weights)
            
            self.health_score = weighted_sum / weight_sum
        else:
            self.health_score = 1.0 if success else 0.0
            
        # Track error count
        if not success:
            self._error_count += 1
        else:
            self._error_count = max(0, self._error_count - 1)
            
        self.last_operation_time = time.time()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        await self.stop_monitoring()