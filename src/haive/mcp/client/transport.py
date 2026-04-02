"""MCP Transport Layer Implementation.

This module provides transport layer implementations for the MCP protocol.
Different transports handle the underlying communication mechanism between
the MCP client and server.

Supported Transports:
    - STDIO: Communication via stdin/stdout with a subprocess
    - HTTP: RESTful communication over HTTP
    - SSE: Server-sent events for streaming
    - WebSocket: Real-time bidirectional communication
    - Docker: Communication via stdin/stdout with a Docker container

The transport layer is responsible for:
    - Establishing and managing connections
    - Sending and receiving raw messages
    - Handling transport-specific encoding/decoding
    - Managing connection lifecycle
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncIterator
import subprocess
import aiohttp
from pydantic import BaseModel, Field

from .exceptions import MCPTransportError, MCPConnectionError, MCPTimeoutError

logger = logging.getLogger(__name__)


class MCPTransport(ABC):
    """Abstract base class for MCP transports.
    
    All MCP transports must implement this interface to provide a consistent
    API for the protocol layer. The transport handles the low-level communication
    while the protocol layer handles MCP message semantics.
    
    The transport is responsible for:
        - Connection establishment and teardown
        - Raw message sending and receiving
        - Transport-specific error handling
        - Connection state management
    """
    
    def __init__(self, timeout: float = 30.0):
        """Initialize transport with timeout.
        
        Args:
            timeout: Default timeout for operations in seconds
        """
        self.timeout = timeout
        self.connected = False
        self._connection_lock = asyncio.Lock()
        
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the MCP server.
        
        Raises:
            MCPConnectionError: If connection fails
            MCPTimeoutError: If connection times out
        """
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the MCP server.
        
        Should be idempotent and safe to call multiple times.
        """
        pass
        
    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message to the server.
        
        Args:
            message: JSON-RPC message to send
            
        Raises:
            MCPTransportError: If sending fails
            MCPConnectionError: If not connected
        """
        pass
        
    @abstractmethod
    async def receive_message(self) -> Dict[str, Any]:
        """Receive a message from the server.
        
        Returns:
            JSON-RPC message from server
            
        Raises:
            MCPTransportError: If receiving fails
            MCPConnectionError: If not connected
            MCPTimeoutError: If receive times out
        """
        pass
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class StdioTransport(MCPTransport):
    """STDIO transport for MCP communication.
    
    This transport communicates with an MCP server via stdin/stdout of a
    subprocess. This is the most common transport for MCP servers that are
    designed to run as command-line tools.
    
    The transport handles:
        - Process lifecycle management
        - JSON-RPC message framing over stdio
        - Process cleanup on disconnection
        - Error handling for process failures
        
    Examples:
        Basic usage::
        
            transport = StdioTransport(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            )
            
        With environment variables::
        
            transport = StdioTransport(
                command="python",
                args=["-m", "my_mcp_server"],
                env={"API_KEY": "secret"},
                cwd="/path/to/server"
            )
    """
    
    def __init__(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: float = 30.0
    ):
        """Initialize STDIO transport.
        
        Args:
            command: Command to execute (e.g., "npx", "python")
            args: Command line arguments
            env: Environment variables for the process
            cwd: Working directory for the process
            timeout: Timeout for operations
        """
        super().__init__(timeout)
        self.command = command
        self.args = args or []
        self.env = env
        self.cwd = cwd
        self.process: Optional[asyncio.subprocess.Process] = None
        self._read_queue: Optional[asyncio.Queue] = None
        self._reader_task: Optional[asyncio.Task] = None
        
    async def connect(self) -> None:
        """Start the MCP server process and establish stdio communication."""
        async with self._connection_lock:
            if self.connected:
                return
                
            try:
                # Build full command
                full_command = [self.command] + self.args
                logger.info(f"Starting MCP server: {' '.join(full_command)}")
                
                # Start process
                self.process = await asyncio.create_subprocess_exec(
                    *full_command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=self.env,
                    cwd=self.cwd
                )
                
                # Set up message reading
                self._read_queue = asyncio.Queue()
                self._reader_task = asyncio.create_task(self._reader_loop())
                
                self.connected = True
                logger.info(f"MCP server started with PID {self.process.pid}")
                
            except Exception as e:
                await self._cleanup()
                raise MCPConnectionError(
                    f"Failed to start MCP server process: {e}",
                    details={"command": full_command, "error": str(e)}
                )
                
    async def disconnect(self) -> None:
        """Stop the MCP server process and cleanup resources."""
        async with self._connection_lock:
            if not self.connected:
                return
                
            await self._cleanup()
            self.connected = False
            logger.info("MCP server process stopped")
            
    async def _cleanup(self) -> None:
        """Clean up process and tasks."""
        # Cancel reader task
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None
            
        # Terminate process
        if self.process:
            try:
                # Try graceful shutdown first
                if self.process.returncode is None:
                    self.process.terminate()
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        # Force kill if graceful shutdown fails
                        self.process.kill()
                        await self.process.wait()
            except Exception as e:
                logger.warning(f"Error during process cleanup: {e}")
            finally:
                self.process = None
                
        self._read_queue = None
        
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send JSON-RPC message to server via stdin."""
        if not self.connected or not self.process or not self.process.stdin:
            raise MCPConnectionError("Not connected to MCP server")
            
        try:
            # Serialize message
            message_str = json.dumps(message, separators=(',', ':'))
            message_bytes = (message_str + '\n').encode('utf-8')
            
            # Send to process stdin
            self.process.stdin.write(message_bytes)
            await self.process.stdin.drain()
            
            logger.debug(f"Sent message: {message_str}")
            
        except Exception as e:
            raise MCPTransportError(
                f"Failed to send message: {e}",
                details={"message": message, "error": str(e)}
            )
            
    async def receive_message(self) -> Dict[str, Any]:
        """Receive JSON-RPC message from server via stdout."""
        if not self.connected or not self._read_queue:
            raise MCPConnectionError("Not connected to MCP server")
            
        try:
            # Wait for message with timeout
            message = await asyncio.wait_for(
                self._read_queue.get(),
                timeout=self.timeout
            )
            
            if isinstance(message, Exception):
                raise message
                
            logger.debug(f"Received message: {json.dumps(message, separators=(',', ':'))}")
            return message
            
        except asyncio.TimeoutError:
            raise MCPTimeoutError(
                f"No message received within {self.timeout}s timeout"
            )
            
    async def _reader_loop(self) -> None:
        """Background task to read messages from process stdout."""
        if not self.process or not self.process.stdout:
            return
            
        try:
            while True:
                # Read line from stdout
                line = await self.process.stdout.readline()
                if not line:
                    # Process has ended
                    break
                    
                try:
                    # Parse JSON message
                    line_str = line.decode('utf-8').strip()
                    if line_str:
                        message = json.loads(line_str)
                        await self._read_queue.put(message)
                        
                except json.JSONDecodeError as e:
                    # Invalid JSON - put error in queue
                    error = MCPTransportError(
                        f"Invalid JSON from server: {e}",
                        details={"raw_line": line_str}
                    )
                    await self._read_queue.put(error)
                    
        except Exception as e:
            # Reader error - put in queue
            error = MCPTransportError(
                f"Error reading from server: {e}",
                details={"error": str(e)}
            )
            await self._read_queue.put(error)


class HttpTransport(MCPTransport):
    """HTTP transport for MCP communication.
    
    This transport communicates with an MCP server over HTTP using JSON-RPC
    over HTTP POST requests. This is useful for servers that expose HTTP APIs
    or for remote MCP servers.
    
    Examples:
        Basic HTTP transport::
        
            transport = HttpTransport("http://localhost:8080/mcp")
            
        With authentication::
        
            transport = HttpTransport(
                "https://api.example.com/mcp",
                headers={"Authorization": "Bearer token123"}
            )
    """
    
    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ):
        """Initialize HTTP transport.
        
        Args:
            url: Base URL for the MCP server
            headers: HTTP headers to include in requests
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self.url = url
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def connect(self) -> None:
        """Create HTTP session."""
        async with self._connection_lock:
            if self.connected:
                return
                
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.headers
            )
            self.connected = True
            logger.info(f"HTTP transport connected to {self.url}")
            
    async def disconnect(self) -> None:
        """Close HTTP session."""
        async with self._connection_lock:
            if not self.connected:
                return
                
            if self.session:
                await self.session.close()
                self.session = None
                
            self.connected = False
            logger.info("HTTP transport disconnected")
            
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send JSON-RPC message via HTTP POST.
        
        Note: For HTTP transport, sending and receiving are combined
        in a request-response cycle. This method stores the message
        for the next receive_message call.
        """
        if not self.connected or not self.session:
            raise MCPConnectionError("HTTP transport not connected")
            
        # Store message for request-response cycle
        self._pending_message = message
        
    async def receive_message(self) -> Dict[str, Any]:
        """Send pending message and receive response."""
        if not self.connected or not self.session:
            raise MCPConnectionError("HTTP transport not connected")
            
        if not hasattr(self, '_pending_message'):
            raise MCPTransportError("No message to send")
            
        try:
            async with self.session.post(
                self.url,
                json=self._pending_message,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    raise MCPTransportError(
                        f"HTTP error {response.status}: {response.reason}",
                        details={"status": response.status, "url": self.url}
                    )
                    
                result = await response.json()
                delattr(self, '_pending_message')
                return result
                
        except aiohttp.ClientError as e:
            raise MCPTransportError(
                f"HTTP request failed: {e}",
                details={"url": self.url, "error": str(e)}
            )


class SseTransport(MCPTransport):
    """Server-Sent Events transport for MCP communication.
    
    This transport uses SSE for receiving messages and HTTP POST for sending.
    Useful for streaming scenarios where the server needs to push messages
    to the client.
    """
    
    def __init__(
        self,
        sse_url: str,
        post_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ):
        """Initialize SSE transport.
        
        Args:
            sse_url: URL for SSE stream (receiving messages)
            post_url: URL for POST requests (sending messages)
            headers: HTTP headers for both requests
            timeout: Request timeout
        """
        super().__init__(timeout)
        self.sse_url = sse_url
        self.post_url = post_url
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None
        self._sse_task: Optional[asyncio.Task] = None
        self._message_queue: Optional[asyncio.Queue] = None
        
    async def connect(self) -> None:
        """Establish SSE connection."""
        async with self._connection_lock:
            if self.connected:
                return
                
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.headers
            )
            self._message_queue = asyncio.Queue()
            self._sse_task = asyncio.create_task(self._sse_loop())
            
            self.connected = True
            logger.info(f"SSE transport connected to {self.sse_url}")
            
    async def disconnect(self) -> None:
        """Close SSE connection."""
        async with self._connection_lock:
            if not self.connected:
                return
                
            # Cancel SSE task
            if self._sse_task and not self._sse_task.done():
                self._sse_task.cancel()
                try:
                    await self._sse_task
                except asyncio.CancelledError:
                    pass
                    
            # Close session
            if self.session:
                await self.session.close()
                self.session = None
                
            self.connected = False
            logger.info("SSE transport disconnected")
            
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message via HTTP POST."""
        if not self.connected or not self.session:
            raise MCPConnectionError("SSE transport not connected")
            
        try:
            async with self.session.post(
                self.post_url,
                json=message,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    raise MCPTransportError(
                        f"HTTP error {response.status}: {response.reason}"
                    )
        except aiohttp.ClientError as e:
            raise MCPTransportError(f"Failed to send message: {e}")
            
    async def receive_message(self) -> Dict[str, Any]:
        """Receive message from SSE stream."""
        if not self.connected or not self._message_queue:
            raise MCPConnectionError("SSE transport not connected")
            
        try:
            message = await asyncio.wait_for(
                self._message_queue.get(),
                timeout=self.timeout
            )
            
            if isinstance(message, Exception):
                raise message
                
            return message
            
        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"No SSE message received within {self.timeout}s")
            
    async def _sse_loop(self) -> None:
        """Background task to read SSE messages."""
        if not self.session:
            return
            
        try:
            async with self.session.get(self.sse_url) as response:
                if response.status != 200:
                    error = MCPTransportError(
                        f"SSE connection failed: {response.status}"
                    )
                    await self._message_queue.put(error)
                    return
                    
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        data = line_str[6:]  # Remove 'data: ' prefix
                        try:
                            message = json.loads(data)
                            await self._message_queue.put(message)
                        except json.JSONDecodeError as e:
                            error = MCPTransportError(f"Invalid SSE JSON: {e}")
                            await self._message_queue.put(error)
                            
        except Exception as e:
            error = MCPTransportError(f"SSE stream error: {e}")
            await self._message_queue.put(error)


class WebSocketTransport(MCPTransport):
    """WebSocket transport for MCP communication.
    
    This transport provides real-time bidirectional communication over
    WebSocket. Useful for interactive applications and real-time scenarios.
    """
    
    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ):
        """Initialize WebSocket transport.
        
        Args:
            url: WebSocket URL (ws:// or wss://)
            headers: WebSocket headers
            timeout: Connection timeout
        """
        super().__init__(timeout)
        self.url = url
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        
    async def connect(self) -> None:
        """Establish WebSocket connection."""
        async with self._connection_lock:
            if self.connected:
                return
                
            try:
                self.session = aiohttp.ClientSession()
                self.websocket = await self.session.ws_connect(
                    self.url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                self.connected = True
                logger.info(f"WebSocket connected to {self.url}")
                
            except Exception as e:
                await self._cleanup()
                raise MCPConnectionError(f"WebSocket connection failed: {e}")
                
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        async with self._connection_lock:
            if not self.connected:
                return
                
            await self._cleanup()
            self.connected = False
            logger.info("WebSocket disconnected")
            
    async def _cleanup(self) -> None:
        """Clean up WebSocket resources."""
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        self.websocket = None
        
        if self.session:
            await self.session.close()
        self.session = None
        
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send message over WebSocket."""
        if not self.connected or not self.websocket:
            raise MCPConnectionError("WebSocket not connected")
            
        try:
            await self.websocket.send_str(json.dumps(message))
        except Exception as e:
            raise MCPTransportError(f"Failed to send WebSocket message: {e}")
            
    async def receive_message(self) -> Dict[str, Any]:
        """Receive message from WebSocket."""
        if not self.connected or not self.websocket:
            raise MCPConnectionError("WebSocket not connected")
            
        try:
            msg = await asyncio.wait_for(
                self.websocket.receive(),
                timeout=self.timeout
            )
            
            if msg.type == aiohttp.WSMsgType.TEXT:
                return json.loads(msg.data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                raise MCPTransportError(f"WebSocket error: {msg.data}")
            elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED):
                raise MCPConnectionError("WebSocket connection closed")
            else:
                raise MCPTransportError(f"Unexpected WebSocket message type: {msg.type}")
                
        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"No WebSocket message within {self.timeout}s")
        except json.JSONDecodeError as e:
            raise MCPTransportError(f"Invalid JSON in WebSocket message: {e}")


class DockerTransport(MCPTransport):
    """Docker transport for MCP communication.

    This transport runs an MCP server inside a Docker container and communicates
    via stdin/stdout, similar to StdioTransport but using ``docker run`` as the
    process wrapper. This provides isolation, reproducibility, and simplified
    dependency management for MCP servers.

    The transport handles:
        - Docker container lifecycle management
        - Volume mounting for data access
        - Port mapping for network services
        - Environment variable passing to the container
        - Graceful container shutdown with ``docker stop``

    Examples:
        Basic Docker transport::

            transport = DockerTransport(
                image="mcp/postgres",
                env={"POSTGRES_HOST": "host.docker.internal"},
            )

        With volumes and network::

            transport = DockerTransport(
                image="mcp/filesystem",
                volumes=["/home/user/data:/data:ro"],
                network="host",
                env={"ALLOWED_DIRS": "/data"},
            )
    """

    def __init__(
        self,
        image: str,
        env: Optional[Dict[str, str]] = None,
        volumes: Optional[List[str]] = None,
        ports: Optional[List[str]] = None,
        network: Optional[str] = None,
        docker_args: Optional[List[str]] = None,
        timeout: float = 30.0,
    ):
        """Initialize Docker transport.

        Args:
            image: Docker image name (e.g., ``"mcp/postgres"``)
            env: Environment variables to pass to the container
            volumes: Volume mounts (e.g., ``["/host/path:/container/path:ro"]``)
            ports: Port mappings (e.g., ``["8080:8080"]``)
            network: Docker network to attach to (e.g., ``"host"``)
            docker_args: Extra arguments to pass to ``docker run``
            timeout: Timeout for operations in seconds
        """
        super().__init__(timeout)
        self.image = image
        self.env = env or {}
        self.volumes = volumes or []
        self.ports = ports or []
        self.network = network
        self.docker_args = docker_args or []
        self.process: Optional[asyncio.subprocess.Process] = None
        self._read_queue: Optional[asyncio.Queue] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._container_id: Optional[str] = None

    def _build_docker_command(self) -> List[str]:
        """Build the ``docker run`` command."""
        cmd = ["docker", "run", "--rm", "-i"]

        # Environment variables
        for key, value in self.env.items():
            cmd.extend(["-e", f"{key}={value}"])

        # Volume mounts
        for vol in self.volumes:
            cmd.extend(["-v", vol])

        # Port mappings
        for port in self.ports:
            cmd.extend(["-p", port])

        # Network
        if self.network:
            cmd.extend(["--network", self.network])

        # Extra args
        cmd.extend(self.docker_args)

        # Image
        cmd.append(self.image)

        return cmd

    async def connect(self) -> None:
        """Start the Docker container and establish stdio communication."""
        async with self._connection_lock:
            if self.connected:
                return

            full_command = self._build_docker_command()
            logger.info(f"Starting MCP server in Docker: {' '.join(full_command)}")

            try:
                self.process = await asyncio.create_subprocess_exec(
                    *full_command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                self._read_queue = asyncio.Queue()
                self._reader_task = asyncio.create_task(self._reader_loop())

                self.connected = True
                logger.info(
                    f"Docker MCP server started (PID {self.process.pid}, "
                    f"image={self.image})"
                )

            except FileNotFoundError:
                raise MCPConnectionError(
                    "Docker is not installed or not in PATH. "
                    "Install Docker from https://docs.docker.com/get-docker/",
                    details={"command": full_command},
                )
            except Exception as e:
                await self._cleanup()
                raise MCPConnectionError(
                    f"Failed to start Docker container: {e}",
                    details={"command": full_command, "error": str(e)},
                )

    async def disconnect(self) -> None:
        """Stop the Docker container and clean up resources."""
        async with self._connection_lock:
            if not self.connected:
                return

            await self._cleanup()
            self.connected = False
            logger.info(f"Docker MCP server stopped (image={self.image})")

    async def _cleanup(self) -> None:
        """Clean up container and tasks."""
        # Cancel reader task
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        # Terminate container process
        if self.process:
            try:
                if self.process.returncode is None:
                    self.process.terminate()
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=10.0)
                    except asyncio.TimeoutError:
                        self.process.kill()
                        await self.process.wait()
            except Exception as e:
                logger.warning(f"Error during Docker container cleanup: {e}")
            finally:
                self.process = None

        self._read_queue = None

    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send JSON-RPC message to the container via stdin."""
        if not self.connected or not self.process or not self.process.stdin:
            raise MCPConnectionError("Not connected to Docker MCP server")

        try:
            message_str = json.dumps(message, separators=(",", ":"))
            message_bytes = (message_str + "\n").encode("utf-8")
            self.process.stdin.write(message_bytes)
            await self.process.stdin.drain()
            logger.debug(f"Sent message to Docker container: {message_str}")
        except Exception as e:
            raise MCPTransportError(
                f"Failed to send message to Docker container: {e}",
                details={"message": message, "error": str(e)},
            )

    async def receive_message(self) -> Dict[str, Any]:
        """Receive JSON-RPC message from the container via stdout."""
        if not self.connected or not self._read_queue:
            raise MCPConnectionError("Not connected to Docker MCP server")

        try:
            message = await asyncio.wait_for(
                self._read_queue.get(), timeout=self.timeout
            )
            if isinstance(message, Exception):
                raise message
            logger.debug(
                f"Received message from Docker container: "
                f"{json.dumps(message, separators=(',', ':'))}"
            )
            return message
        except asyncio.TimeoutError:
            raise MCPTimeoutError(
                f"No message received from Docker container within {self.timeout}s"
            )

    async def _reader_loop(self) -> None:
        """Background task to read messages from container stdout."""
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break

                try:
                    line_str = line.decode("utf-8").strip()
                    if line_str:
                        message = json.loads(line_str)
                        await self._read_queue.put(message)
                except json.JSONDecodeError as e:
                    error = MCPTransportError(
                        f"Invalid JSON from Docker container: {e}",
                        details={"raw_line": line_str},
                    )
                    await self._read_queue.put(error)
        except Exception as e:
            error = MCPTransportError(
                f"Error reading from Docker container: {e}",
                details={"error": str(e)},
            )
            await self._read_queue.put(error)