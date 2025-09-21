#!/usr/bin/env python3
"""
MCP Client for Docker MCP Gateway

This module provides a Python client to interact with the Docker MCP Gateway
and use DuckDuckGo search tools through the Model Context Protocol (MCP).
"""

import json
import subprocess
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pydantic import BaseModel


@dataclass
class MCPTool:
    """Represents an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class SearchResult:
    """Represents a search result."""
    title: str
    url: str
    snippet: str
    position: int
    source: str = "duckduckgo"


class MCPResponse(BaseModel):
    """MCP JSON-RPC response model."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class MCPRequest(BaseModel):
    """MCP JSON-RPC request model."""
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None


class MCPGatewayClient:
    """Client for communicating with Docker MCP Gateway."""
    
    def __init__(self, gateway_command: List[str] = None):
        """
        Initialize MCP Gateway Client.
        
        Args:
            gateway_command: Command to start the MCP gateway. 
                           Default: ["docker", "mcp", "gateway", "run"]
        """
        self.gateway_command = gateway_command or ["docker", "mcp", "gateway", "run"]
        self.process = None
        self.logger = logging.getLogger(__name__)
        self.request_id = 0
        
    async def start(self):
        """Start the MCP Gateway process."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.gateway_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.logger.info("MCP Gateway process started")
            
            # Wait longer for the gateway to initialize fully
            self.logger.info("Waiting for MCP Gateway to initialize...")
            await asyncio.sleep(10)
            
            # Check if process is still running
            if self.process.returncode is not None:
                stderr_output = await self.process.stderr.read()
                raise RuntimeError(f"MCP Gateway failed to start: {stderr_output.decode()}")
                
        except Exception as e:
            self.logger.error(f"Failed to start MCP Gateway: {e}")
            raise
    
    async def stop(self):
        """Stop the MCP Gateway process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.logger.info("MCP Gateway process stopped")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a JSON-RPC request to the MCP Gateway.
        
        Args:
            method: The MCP method to call
            params: Parameters for the method
            
        Returns:
            Response from the MCP Gateway
        """
        if not self.process:
            raise RuntimeError("MCP Gateway process not started")
        
        self.request_id += 1
        request = MCPRequest(
            method=method,
            params=params or {},
            id=self.request_id
        )
        
        request_json = request.model_dump_json() + "\n"
        self.logger.debug(f"Sending request: {request_json.strip()}")
        
        # Send request
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # Read response (with timeout)
        try:
            response_line = await asyncio.wait_for(self.process.stdout.readline(), timeout=30.0)
        except asyncio.TimeoutError:
            raise RuntimeError(f"Timeout waiting for response to {method}")
            
        response_text = response_line.decode().strip()
        
        if not response_text:
            # Check if process is still alive
            if self.process.returncode is not None:
                stderr_output = await self.process.stderr.read()
                raise RuntimeError(f"MCP Gateway process exited: {stderr_output.decode()}")
            raise RuntimeError("Empty response from MCP Gateway")
        
        self.logger.debug(f"Received response: {response_text}")
        
        try:
            response_data = json.loads(response_text)
            response = MCPResponse(**response_data)
            
            if response.error:
                self.logger.error(f"MCP Error for {method}: {response.error}")
                raise RuntimeError(f"MCP Error: {response.error}")
            
            return response.result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {response_text}")
            raise RuntimeError(f"Invalid JSON response: {e}")
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP session."""
        return await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {
                    "listChanged": False
                },
                "sampling": {}
            },
            "clientInfo": {
                "name": "search-engine-client",
                "version": "1.0.0"
            }
        })
    
    async def list_tools(self) -> List[MCPTool]:
        """List available MCP tools."""
        result = await self.send_request("tools/list")
        
        tools = []
        for tool_data in result.get("tools", []):
            tools.append(MCPTool(
                name=tool_data["name"],
                description=tool_data["description"],
                input_schema=tool_data.get("inputSchema", {})
            ))
        
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        return await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
    
    async def send_notification(self, method: str, params: Dict[str, Any] = None):
        """
        Send a JSON-RPC notification to the MCP Gateway (no response expected).
        
        Args:
            method: The MCP method to call
            params: Parameters for the method
        """
        if not self.process:
            raise RuntimeError("MCP Gateway process not started")
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        self.logger.debug(f"Sending notification: {request_json.strip()}")
        
        # Send notification
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()


class DuckDuckGoMCPClient:
    """High-level client for DuckDuckGo search via MCP Gateway."""
    
    def __init__(self):
        self.mcp_client = MCPGatewayClient()
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self):
        """Start the MCP client and initialize session."""
        await self.mcp_client.start()
        init_result = await self.mcp_client.initialize()
        self.logger.debug(f"Initialization result: {init_result}")
        
        # Send initialized notification to complete handshake
        await self.mcp_client.send_notification("initialized", {})
        
        self._initialized = True
        self.logger.info("DuckDuckGo MCP client initialized")
    
    async def stop(self):
        """Stop the MCP client."""
        await self.mcp_client.stop()
        self._initialized = False
    
    async def get_available_tools(self) -> List[MCPTool]:
        """Get list of available DuckDuckGo tools."""
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        tools = await self.mcp_client.list_tools()
        ddg_tools = [tool for tool in tools if "duckduckgo" in tool.name.lower()]
        return ddg_tools
    
    async def search_web(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        try:
            # Call DuckDuckGo web search tool
            result = await self.mcp_client.call_tool(
                name="duckduckgo_web_search",
                arguments={
                    "query": query,
                    "max_results": max_results
                }
            )
            
            # Parse results
            search_results = []
            for i, item in enumerate(result.get("content", []), 1):
                if isinstance(item, dict) and item.get("type") == "text":
                    # Parse the text content for search results
                    text_content = item.get("text", "")
                    # This would need to be adapted based on actual response format
                    search_results.append(SearchResult(
                        title=f"Result {i}",
                        url="",
                        snippet=text_content,
                        position=i,
                        source="duckduckgo_mcp"
                    ))
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {e}")
            raise
    
    async def search_news(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search for news using DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of news results
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        try:
            # Call DuckDuckGo news search tool
            result = await self.mcp_client.call_tool(
                name="duckduckgo_news_search",
                arguments={
                    "query": query,
                    "max_results": max_results
                }
            )
            
            # Parse results - similar to web search
            search_results = []
            for i, item in enumerate(result.get("content", []), 1):
                if isinstance(item, dict) and item.get("type") == "text":
                    text_content = item.get("text", "")
                    search_results.append(SearchResult(
                        title=f"News {i}",
                        url="",
                        snippet=text_content,
                        position=i,
                        source="duckduckgo_news"
                    ))
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"DuckDuckGo news search failed: {e}")
            raise


# Convenience functions
async def search_web_mcp(query: str, max_results: int = 10) -> List[SearchResult]:
    """
    Convenience function to search the web using DuckDuckGo MCP.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of search results
    """
    async with DuckDuckGoMCPClient() as client:
        return await client.search_web(query, max_results)


def search_web_mcp_sync(query: str, max_results: int = 10) -> List[SearchResult]:
    """
    Synchronous wrapper for DuckDuckGo MCP search.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of search results
    """
    return asyncio.run(search_web_mcp(query, max_results))


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_client():
        """Test the MCP client."""
        try:
            async with DuckDuckGoMCPClient() as client:
                print("Getting available tools...")
                tools = await client.get_available_tools()
                print(f"Available DuckDuckGo tools: {[tool.name for tool in tools]}")
                
                if tools:
                    print("\nTesting web search...")
                    results = await client.search_web("Python programming", max_results=3)
                    for result in results:
                        print(f"- {result.title}: {result.snippet[:100]}...")
                else:
                    print("No DuckDuckGo tools available")
                    
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Searching for: {query}")
        results = search_web_mcp_sync(query)
        for result in results:
            print(f"{result.position}. {result.title}")
            print(f"   {result.snippet}")
            print()
    else:
        asyncio.run(test_client())