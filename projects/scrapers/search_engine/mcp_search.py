#!/usr/bin/env python3
"""
Docker MCP CLI Wrapper for DuckDuckGo Search

This module provides a simple Python wrapper around the Docker MCP CLI
to perform web searches using the DuckDuckGo tool via Docker's MCP Gateway.
"""

import subprocess
import re
import logging
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a search result from DuckDuckGo via MCP Gateway."""
    title: str
    url: str
    snippet: str
    position: int
    source: str = "duckduckgo_mcp"


class DockerMCPSearchError(Exception):
    """Exception raised when Docker MCP search fails."""
    pass


class DockerMCPSearch:
    """Simple wrapper for Docker MCP Gateway DuckDuckGo search."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search DuckDuckGo using Docker MCP Gateway.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
            
        Raises:
            DockerMCPSearchError: If the search fails
        """
        try:
            # Run the docker mcp tools call command
            cmd = [
                "docker", "mcp", "tools", "call", "search",
                f"query={query}",
                f"max_results={max_results}"
            ]
            
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode != 0:
                error_msg = f"Docker MCP search failed: {result.stderr}"
                self.logger.error(error_msg)
                raise DockerMCPSearchError(error_msg)
            
            # Parse the output
            return self._parse_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise DockerMCPSearchError("Search timeout after 60 seconds")
        except Exception as e:
            raise DockerMCPSearchError(f"Search failed: {e}")
    
    def _parse_output(self, output: str) -> List[SearchResult]:
        """Parse the Docker MCP CLI output into SearchResult objects."""
        results = []
        
        # Split the output into lines
        lines = output.strip().split('\n')
        
        # Find the start of results (skip timing info)
        start_idx = 0
        for i, line in enumerate(lines):
            if "Found" in line and "search results:" in line:
                start_idx = i + 2  # Skip the "Found X results:" line and empty line
                break
        
        if start_idx >= len(lines):
            self.logger.warning("No search results found in output")
            return results
        
        # Parse each result block
        current_result = {}
        position = 0
        
        for line in lines[start_idx:]:
            line = line.strip()
            
            if not line:
                # Empty line might indicate end of a result block
                if current_result:
                    results.append(self._create_search_result(current_result, position))
                    current_result = {}
                continue
            
            # Check if this is a new result (starts with number and title)
            title_match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if title_match:
                # Save previous result if exists
                if current_result:
                    results.append(self._create_search_result(current_result, position))
                
                # Start new result
                position = int(title_match.group(1))
                current_result = {
                    'position': position,
                    'title': title_match.group(2).strip()
                }
                continue
            
            # Check for URL line
            url_match = re.match(r'^URL:\s+(.+)$', line)
            if url_match and current_result:
                current_result['url'] = url_match.group(1).strip()
                continue
            
            # Check for Summary line  
            summary_match = re.match(r'^Summary:\s+(.+)$', line)
            if summary_match and current_result:
                current_result['snippet'] = summary_match.group(1).strip()
                continue
        
        # Add the last result if exists
        if current_result:
            results.append(self._create_search_result(current_result, position))
        
        return results
    
    def _create_search_result(self, result_data: dict, position: int) -> SearchResult:
        """Create a SearchResult from parsed data."""
        return SearchResult(
            title=result_data.get('title', f'Result {position}'),
            url=result_data.get('url', ''),
            snippet=result_data.get('snippet', ''),
            position=position,
            source='duckduckgo_mcp'
        )


# Convenience functions
def search_web_mcp(query: str, max_results: int = 10) -> List[SearchResult]:
    """
    Convenience function to search the web using Docker MCP Gateway.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of SearchResult objects
    """
    search_engine = DockerMCPSearch()
    return search_engine.search(query, max_results)


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python mcp_search.py <query> [max_results]")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:-1]) if len(sys.argv) > 2 and sys.argv[-1].isdigit() else " ".join(sys.argv[1:])
    max_results = int(sys.argv[-1]) if len(sys.argv) > 2 and sys.argv[-1].isdigit() else 10
    
    try:
        print(f"🔍 Searching for: {query}")
        print(f"📊 Max results: {max_results}")
        print()
        
        results = search_web_mcp(query, max_results)
        
        if not results:
            print("❌ No results found")
            sys.exit(1)
        
        print(f"✅ Found {len(results)} results:")
        print()
        
        for result in results:
            print(f"{result.position}. {result.title}")
            if result.url:
                print(f"   🔗 {result.url}")
            if result.snippet:
                print(f"   📝 {result.snippet}")
            print()
            
    except DockerMCPSearchError as e:
        print(f"❌ Search error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Search interrupted")
        sys.exit(130)