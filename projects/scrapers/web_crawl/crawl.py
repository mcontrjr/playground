#!/usr/bin/env python3
"""
Professional Web Crawler with AI-Powered Content Analysis

A sophisticated web crawling tool that combines traditional web scraping
with Google Gemini AI for intelligent content analysis and filtering.

Usage Examples:
    python crawl.py --url "https://example.com,https://another.com"
    python crawl.py --url "https://example.com" --search "events" --exhaustive
    python crawl.py --url "https://example.com" --search "products" --output results.json
"""

import argparse
import json
import sys
import os
from typing import List
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from utils import setup_logging, is_valid_url
from content_analyzer import ContentAnalyzer
from web_crawler import WebCrawler, CrawlConfig

console = Console()


def parse_urls(url_string: str) -> List[str]:
    """
    Parse comma-separated URLs from command line argument.
    
    Args:
        url_string: Comma-separated URL string
        
    Returns:
        List of valid URLs
    """
    urls = [url.strip() for url in url_string.split(',')]
    valid_urls = []
    
    for url in urls:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        if is_valid_url(url):
            valid_urls.append(url)
        else:
            console.print(f"[red]Warning: Invalid URL skipped: {url}[/red]")
    
    return valid_urls


def display_crawl_summary(results: dict):
    """Display a formatted summary of crawl results."""
    
    summary = results.get("crawl_summary", {})
    
    # Main summary table
    table = Table(title="🕷️ Crawl Summary", show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total URLs Processed", str(summary.get("total_urls_processed", 0)))
    table.add_row("Successful Crawls", str(summary.get("successful_crawls", 0)))
    table.add_row("Failed Crawls", str(summary.get("failed_crawls", 0)))
    table.add_row("Max Depth Reached", str(summary.get("max_depth_reached", 0)))
    table.add_row("Search Query", str(summary.get("search_query", "None")))
    table.add_row("Exhaustive Mode", str(summary.get("exhaustive_mode", False)))
    
    console.print(table)
    
    # Show failed crawls if any
    failed_pages = results.get("failed_pages", [])
    if failed_pages:
        console.print("\n❌ Failed Crawls:")
        for failed in failed_pages[:5]:  # Show first 5 failures
            error_msg = failed.get('error', 'Unknown error')
            status = failed.get('status_code', 'N/A')
            console.print(f"  • [red]{failed['url']}[/red] - {error_msg} (HTTP {status})")
        
        if len(failed_pages) > 5:
            console.print(f"  ... and {len(failed_pages) - 5} more failures")
    
    # AI Analysis summary if available
    ai_analysis = results.get("ai_analysis", {})
    if ai_analysis and "error" not in ai_analysis:
        console.print("\n🤖 AI Analysis Summary")
        
        insights_panel = Panel(
            ai_analysis.get("insights", "No insights available"),
            title="Key Insights",
            border_style="blue"
        )
        console.print(insights_panel)
        
        # Key themes
        themes = ai_analysis.get("key_themes", [])
        if themes:
            console.print(f"\n📋 Key Themes Found: {', '.join(themes)}")
        
        # Top URLs
        top_urls = ai_analysis.get("top_urls", [])[:3]
        if top_urls:
            console.print("\n🔗 Most Relevant URLs:")
            for i, url in enumerate(top_urls, 1):
                console.print(f"  {i}. [link]{url}[/link]")


def display_content_matches(results: dict):
    """Display content matches with relevance scores."""
    
    matches = results.get("content_matches", [])
    if not matches:
        return
    
    console.print(f"\n📊 Content Analysis Results ({len(matches)} pages analyzed)")
    
    # Sort by relevance score
    sorted_matches = sorted(matches, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    for match in sorted_matches[:5]:  # Show top 5
        score = match.get("relevance_score", 0)
        url = match.get("url", "")
        title = match.get("title", "No title")
        content = match.get("matched_content", "")[:200] + "..."
        
        # Color code by relevance
        if score > 0.7:
            color = "green"
        elif score > 0.4:
            color = "yellow"
        else:
            color = "red"
        
        console.print(f"\n[{color}]🎯 Relevance: {score:.2f}[/{color}]")
        console.print(f"[bold]Title:[/bold] {title}")
        console.print(f"[bold]URL:[/bold] [link]{url}[/link]")
        console.print(f"[bold]Content:[/bold] {content}")


def save_results(results: dict, output_file: str):
    """Save results to JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✅ Results saved to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error saving results: {e}[/red]")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Professional Web Crawler with AI-Powered Content Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  crawl.py --url "https://example.com,https://another.com"
  crawl.py --url "https://example.com" --search "events" --exhaustive
  crawl.py --url "https://example.com" --search "products" --output results.json
  crawl.py --url "https://example.com" --depth 3 --max-pages 100
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--url", "-u",
        required=True,
        help="Comma-separated list of URLs to crawl (e.g., 'url1.com,url2.gov,url3.org')"
    )
    
    # Optional arguments
    parser.add_argument(
        "--search", "-s",
        help="Search query to filter and prioritize content (enables AI analysis)"
    )
    
    parser.add_argument(
        "--exhaustive", "-e",
        action="store_true",
        help="Enable exhaustive crawling (deeper and more pages)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path for JSON results (default: prints to console)"
    )
    
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Maximum crawl depth (default: 2)"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Maximum pages to crawl (default: 50)"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Maximum concurrent workers (default: 5)"
    )
    
    parser.add_argument(
        "--no-robots",
        action="store_true",
        help="Ignore robots.txt restrictions"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-essential output"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    if args.quiet:
        log_level = "WARNING"
    
    logger = setup_logging(log_level)
    
    # Parse URLs
    urls = parse_urls(args.url)
    if not urls:
        console.print("[red]❌ No valid URLs provided![/red]")
        sys.exit(1)
    
    # Display startup info
    if not args.quiet:
        console.print(Panel.fit(
            "[bold blue]🕷️ Professional Web Crawler[/bold blue]\n"
            f"URLs to crawl: {len(urls)}\n"
            f"Search query: {args.search or 'None'}\n"
            f"AI Analysis: {'Enabled' if args.search else 'Disabled'}",
            border_style="blue"
        ))
    
    try:
        # Initialize components
        config = CrawlConfig(
            max_depth=args.depth,
            max_pages=args.max_pages,
            delay=args.delay,
            max_workers=args.workers,
            respect_robots=not args.no_robots
        )
        
        # Initialize AI analyzer if search query provided
        analyzer = None
        if args.search:
            try:
                analyzer = ContentAnalyzer()
                if not args.quiet:
                    console.print("[green]🤖 AI Content Analyzer initialized[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ AI Analyzer failed to initialize: {e}[/yellow]")
                console.print("[yellow]Continuing without AI analysis...[/yellow]")
        
        # Initialize crawler
        crawler = WebCrawler(config=config, analyzer=analyzer)
        
        if not args.quiet:
            console.print("[green]✅ Web crawler initialized[/green]")
            console.print(f"[cyan]Starting crawl of {len(urls)} URLs...[/cyan]")
        
        # Start crawling with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            
            if not args.quiet:
                task = progress.add_task("Crawling websites...", total=None)
            
            results = crawler.crawl_urls(
                start_urls=urls,
                search_query=args.search,
                exhaustive=args.exhaustive
            )
        
        # Clean up
        crawler.close()
        
        # Display results
        if not args.quiet:
            console.print("\n[green]🎉 Crawl completed successfully![/green]")
            display_crawl_summary(results)
            
            if args.search and results.get("content_matches"):
                display_content_matches(results)
        
        # Save or print results
        if args.output:
            save_results(results, args.output)
        elif args.quiet:
            # Print JSON for piping
            print(json.dumps(results, indent=2))
        else:
            console.print(f"\n📄 Full results available in memory. Use --output to save.")
    
    except KeyboardInterrupt:
        console.print(f"\n[yellow]⚠️ Crawl interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error during crawling: {e}[/red]")
        if args.verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()