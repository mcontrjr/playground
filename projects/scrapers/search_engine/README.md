# Search Engine using Docker MCP Gateway

A Python-based search engine that uses Docker's MCP (Model Context Protocol) Gateway to perform web searches via DuckDuckGo tools. This solution bypasses the 403 forbidden errors encountered with direct SearX instances by using Docker's containerized MCP servers.

## Features

- 🔍 **Web Search**: Search the web using DuckDuckGo via Docker MCP Gateway
- 🐳 **Docker Integration**: Uses Docker's MCP Gateway for secure, containerized tool execution
- 📊 **Multiple Output Formats**: Support for table, text, and JSON output formats
- 🎨 **Rich CLI**: Beautiful command-line interface with colors and formatting
- ⚡ **Fast & Reliable**: No more 403 errors or rate limiting issues

## Prerequisites

- **Docker Desktop** with MCP Toolkit feature enabled
- **Python 3.13+**
- **uv** package manager

## Installation

1. Clone or navigate to the project directory:
   ```bash
   cd /path/to/search_engine
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. Verify Docker MCP Gateway is available:
   ```bash
   docker mcp tools list
   ```

## Usage

### Command Line Interface

```bash
# Basic search
uv run python main.py "your search query"

# Limit number of results
uv run python main.py "farmers markets in san jose" --max-results 5

# Different output formats
uv run python main.py "python programming" --format table
uv run python main.py "python programming" --format text
uv run python main.py "python programming" --format json

# Verbose logging
uv run python main.py "machine learning" --verbose
```

### Python API

```python
from mcp_search import search_web_mcp, DockerMCPSearchError

try:
    # Perform a search
    results = search_web_mcp("python programming", max_results=5)
    
    # Process results
    for result in results:
        print(f"{result.position}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Snippet: {result.snippet}")
        print()
        
except DockerMCPSearchError as e:
    print(f"Search failed: {e}")
```

### Direct Docker MCP CLI Usage

```bash
# List available tools
docker mcp tools list

# Describe the search tool
docker mcp tools inspect search

# Call the search tool directly
docker mcp tools call search query="farmers markets" max_results=3
```

## Architecture

This solution consists of three main components:

1. **Docker MCP Gateway** (`docker mcp gateway run`)
   - Manages containerized MCP servers
   - Provides secure, isolated tool execution
   - Handles DuckDuckGo, Brave, Playwright, and Firecrawl tools

2. **Python Wrapper** (`mcp_search.py`)
   - Provides a clean Python API around the Docker MCP CLI
   - Handles subprocess execution and output parsing
   - Returns structured `SearchResult` objects

3. **CLI Interface** (`main.py`)
   - Rich command-line interface using Click and Rich
   - Multiple output formats (table, text, JSON)
   - Verbose logging and error handling

## Available MCP Tools

The Docker MCP Gateway provides access to 35+ tools including:

- **DuckDuckGo**: Web search with formatted results
- **Brave Search**: Web, image, news, video search and summarization
- **Playwright**: Browser automation and web scraping
- **Firecrawl**: Content extraction and web crawling

## Troubleshooting

### Docker MCP Gateway not found
```bash
# Ensure Docker Desktop is running and MCP Toolkit is enabled
docker --version
docker mcp --version
```

### Tool execution errors
```bash
# Check if MCP servers are running
docker ps | grep mcp

# View detailed error logs
uv run python main.py "test query" --verbose
```

### No search results
- Verify your search query is not empty
- Try reducing the number of max_results
- Check Docker MCP Gateway logs

## Why This Solution?

The original search engine encountered 403 forbidden errors when accessing public SearX instances due to:
- Rate limiting on public instances
- IP blocking and anti-bot measures
- Inconsistent availability of SearX services

Docker's MCP Gateway solves these issues by:
- ✅ Running search tools in isolated containers
- ✅ Using official, maintained search APIs
- ✅ Providing enterprise-grade reliability and security
- ✅ Offering multiple search engines as alternatives

## License

This project is part of a larger search engine exploration and follows the same licensing terms.