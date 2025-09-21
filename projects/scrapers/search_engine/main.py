#!/usr/bin/env python3
"""
Search Engine CLI using Docker MCP Gateway with DuckDuckGo tools
"""

import sys
from mcp_search import search_web_mcp, DockerMCPSearchError
import click
import logging
from rich.console import Console
from rich.table import Table

console = Console()

@click.command()
@click.argument('query', required=True)
@click.option('--max-results', '-n', default=10, help='Maximum number of results to return')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'table']), default='table', help='Output format')
def main(query: str, max_results: int, verbose: bool, format: str):
    """Search the web using DuckDuckGo via Docker MCP Gateway."""
    
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    try:
        console.print(f"🔍 Searching for: [bold blue]{query}[/bold blue]")
        console.print("⏳ Using Docker MCP Gateway for search...")
        
        results = search_web_mcp(query, max_results)
        
        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return
        
        if format == 'json':
            import json
            result_data = [{
                'title': r.title,
                'url': r.url,
                'snippet': r.snippet,
                'position': r.position,
                'source': r.source
            } for r in results]
            print(json.dumps(result_data, indent=2))
            
        elif format == 'text':
            for result in results:
                console.print(f"{result.position}. [bold]{result.title}[/bold]")
                if result.url:
                    console.print(f"   URL: {result.url}")
                console.print(f"   {result.snippet}")
                console.print(f"   Source: {result.source}")
                console.print()
                
        else:  # table format
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("#", width=3)
            table.add_column("Title", width=40)
            table.add_column("Snippet", width=60)
            table.add_column("Source", width=15)
            
            for result in results:
                table.add_row(
                    str(result.position),
                    result.title,
                    result.snippet[:100] + "..." if len(result.snippet) > 100 else result.snippet,
                    result.source
                )
            
            console.print(table)
            
        console.print(f"\n✅ Found [bold green]{len(results)}[/bold green] results")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Search interrupted by user[/yellow]")
        sys.exit(130)
    except DockerMCPSearchError as e:
        console.print(f"[red]Search Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
