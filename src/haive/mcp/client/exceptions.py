"""MCP Client Exception Classes.

This module defines all exception types used by the MCP client implementation.
These exceptions follow the MCP protocol error specifications and provide
detailed error information for debugging and error handling.
"""

from typing import Any, Dict, Optional


class MCPError(Exception):
    """Base exception for all MCP-related errors.
    
    This is the root exception class for all MCP client errors. It provides
    a consistent interface for error handling and includes optional error
    details and context information.
    
    Args:
        message: Human-readable error description
        error_code: MCP protocol error code (if applicable)
        details: Additional error details or context
        
    Examples:
        Basic error::
        
            raise MCPError("Connection failed")
            
        With error code::
        
            raise MCPError("Invalid request", error_code=-32600)
            
        With details::
        
            raise MCPError(
                "Tool execution failed",
                details={"tool": "filesystem", "args": {...}}
            )
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        
    def __str__(self) -> str:
        """Return formatted error message."""
        parts = [self.message]
        if self.error_code is not None:
            parts.append(f"[Code: {self.error_code}]")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " ".join(parts)


class MCPConnectionError(MCPError):
    """Error during MCP connection establishment or management.
    
    Raised when there are issues connecting to, maintaining, or disconnecting
    from an MCP server. This includes transport-level failures, timeout issues,
    and connection state problems.
    
    Examples:
        Connection timeout::
        
            raise MCPConnectionError("Connection timeout after 30s")
            
        Transport failure::
        
            raise MCPConnectionError(
                "Failed to start server process",
                details={"command": ["npx", "server"], "exit_code": 1}
            )
    """
    pass


class MCPProtocolError(MCPError):
    """Error in MCP protocol communication.
    
    Raised when there are protocol-level issues such as invalid messages,
    unsupported protocol versions, or malformed responses. This indicates
    a problem with the MCP protocol implementation or server compliance.
    
    Examples:
        Protocol version mismatch::
        
            raise MCPProtocolError(
                "Unsupported protocol version",
                details={"client": "1.0", "server": "0.9"}
            )
            
        Invalid message format::
        
            raise MCPProtocolError(
                "Malformed JSON-RPC message",
                error_code=-32700,
                details={"raw_message": "invalid json"}
            )
    """
    pass


class MCPTimeoutError(MCPConnectionError):
    """Timeout during MCP operation.
    
    Raised when an MCP operation (connection, tool call, etc.) exceeds the
    configured timeout period. This is a specialized connection error that
    specifically indicates timing issues.
    
    Args:
        operation: Name of the operation that timed out
        timeout: Timeout value that was exceeded
        
    Examples:
        Tool execution timeout::
        
            raise MCPTimeoutError(
                "Tool call timed out",
                details={"operation": "call_tool", "timeout": 30.0}
            )
    """
    pass


class MCPTransportError(MCPConnectionError):
    """Error in the transport layer.
    
    Raised when there are issues with the underlying transport mechanism
    (STDIO, HTTP, WebSocket, etc.). This includes process management failures,
    network issues, and transport-specific problems.
    
    Examples:
        Process died unexpectedly::
        
            raise MCPTransportError(
                "Server process died",
                details={"pid": 12345, "exit_code": -9}
            )
            
        Network error::
        
            raise MCPTransportError(
                "HTTP connection failed",
                details={"url": "http://localhost:8080", "status": 500}
            )
    """
    pass


class MCPAuthenticationError(MCPError):
    """Authentication failure with MCP server.
    
    Raised when authentication is required but fails, or when authorization
    is denied for a specific operation. This includes token validation failures
    and permission issues.
    
    Examples:
        Invalid token::
        
            raise MCPAuthenticationError(
                "Invalid authentication token",
                error_code=401
            )
            
        Insufficient permissions::
        
            raise MCPAuthenticationError(
                "Insufficient permissions for tool execution",
                details={"tool": "sensitive_operation", "required_scope": "admin"}
            )
    """
    pass


class MCPCapabilityError(MCPProtocolError):
    """Error related to MCP capabilities.
    
    Raised when there are issues with capability negotiation, unsupported
    capabilities, or capability validation failures. This indicates a mismatch
    between client requirements and server capabilities.
    
    Examples:
        Unsupported capability::
        
            raise MCPCapabilityError(
                "Server doesn't support required capability",
                details={"required": "tools", "supported": ["logging"]}
            )
    """
    pass


class MCPToolError(MCPError):
    """Error during tool execution.
    
    Raised when there are issues executing tools on the MCP server. This
    includes tool not found errors, invalid arguments, and execution failures.
    
    Examples:
        Tool not found::
        
            raise MCPToolError(
                "Tool not found",
                details={"tool_name": "nonexistent_tool"}
            )
            
        Invalid arguments::
        
            raise MCPToolError(
                "Invalid tool arguments",
                details={"tool": "read_file", "error": "path is required"}
            )
    """
    pass