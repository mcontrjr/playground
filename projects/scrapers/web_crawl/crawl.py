#!/usr/bin/env python3
"""
Event Discovery Web Crawler

A streamlined web crawling tool focused on discovering event and activity information.
Uses a two-phase approach:
1. Crawl and consolidate content from website
2. Single AI extraction call to identify event information

Usage Examples:
    python crawl.py --url "https://example.com"
    python crawl.py --url "https://example.com" --depth 3 --output events.json
    python crawl.py --url "https://city.gov" --max-pages 100 --verbose
"""

import argparse
import json
import sys
import os
from typing import List
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from utils import setup_logging, is_valid_url
from simple_crawler import SimpleCrawler, SimpleCrawlConfig
from event_extractor import EventExtractor

console = Console()


def parse_url(url_string: str) -> str:
    """
    Parse and validate a single URL from command line argument.
    
    Args:
        url_string: URL string
        
    Returns:
        Valid URL or None
    """
    url = url_string.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    if is_valid_url(url):
        return url
    else:
        console.print(f"[red]Error: Invalid URL: {url}[/red]")
        return None


def display_results(results: dict):
    """Display event extraction results."""
    
    # #ICONS
    # Replace emojis with terminal-style icons
    ICON_SUCCESS = "[+]"
    ICON_INFO = "[i]"
    ICON_EVENT = "[*]"
    ICON_URL = "[>]"
    
    base_url = results.get("base_url", "Unknown")
    purpose = results.get("purpose", "No purpose determined")
    routes = results.get("routes", [])
    events = results.get("events_found", [])
    
    # Summary table
    console.print(f"\n{ICON_SUCCESS} Event Discovery Results", style="bold green")
    console.print(f"\n{ICON_INFO} Base URL: {base_url}")
    console.print(f"{ICON_INFO} Purpose: {purpose}")
    console.print(f"{ICON_INFO} Event-related routes found: {len(routes)}")
    console.print(f"{ICON_INFO} Events extracted: {len(events)}")
    
    # Display event routes
    if routes:
        console.print(f"\n{ICON_URL} Event-Related Routes:", style="bold cyan")
        for i, route in enumerate(routes[:10], 1):
            console.print(f"  {i}. {route}")
        if len(routes) > 10:
            console.print(f"  ... and {len(routes) - 10} more routes")
    
    # Display events
    if events:
        console.print(f"\n{ICON_EVENT} Events Found:", style="bold yellow")
        for i, event in enumerate(events[:5], 1):
            console.print(f"\n  Event {i}:")
            console.print(f"    Title: {event.get('title', 'N/A')}")
            if event.get('date'):
                console.print(f"    Date: {event['date']}")
            if event.get('start_time'):
                time_str = f"{event['start_time']}"
                if event.get('end_time'):
                    time_str += f" - {event['end_time']}"
                console.print(f"    Time: {time_str}")
            if event.get('address'):
                console.print(f"    Address: {event['address']}")
            if event.get('source_url'):
                console.print(f"    Source: {event['source_url']}")
        
        if len(events) > 5:
            console.print(f"\n  ... and {len(events) - 5} more events")
    else:
        console.print(f"\n{ICON_INFO} No events found on this website.", style="yellow")


def save_results(results: dict, output_file: str):
    """Save results to JSON file."""
    try:
        # Format output according to spec: base_url as key
        output = {
            results.get("base_url", "unknown"): {
                "routes": results.get("routes", []),
                "purpose": results.get("purpose", ""),
                "events_found": results.get("events_found", [])
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        console.print(f"[green][+] Results saved to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red][-] Error saving results: {e}[/red]")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Event Discovery Web Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  crawl.py --url "https://example.com"
  crawl.py --url "https://city.gov" --depth 3 --output events.json
  crawl.py --url "https://example.com" --max-pages 100 --verbose
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--url", "-u",
        required=True,
        help="URL to crawl for event information"
    )
    
    # Optional arguments
    parser.add_argument(
        "--output", "-o",
        default="output.json",
        help="Output file path for JSON results (default: output.json)"
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
    
    # Setup logging to crawl.log
    log_level = "DEBUG" if args.verbose else "INFO"
    if args.quiet:
        log_level = "WARNING"
    
    logger = setup_logging(log_level, "crawl.log")
    logger.info("=" * 50)
    logger.info("Starting new crawl session")
    logger.info(f"URL: {args.url}")
    logger.info(f"Depth: {args.depth}, Max pages: {args.max_pages}")
    
    # #ICONS
    ICON_START = "[>]"
    ICON_SUCCESS = "[+]"
    ICON_ERROR = "[-]"
    ICON_WARNING = "[!]"
    
    # Parse URL
    url = parse_url(args.url)
    if not url:
        console.print(f"[red]{ICON_ERROR} No valid URL provided![/red]")
        sys.exit(1)
    
    # Display startup info
    if not args.quiet:
        console.print(Panel.fit(
            f"[bold cyan]{ICON_START} Event Discovery Web Crawler[/bold cyan]\n"
            f"URL: {url}\n"
            f"Depth: {args.depth} | Max Pages: {args.max_pages}\n"
            f"Output: {args.output}",
            border_style="cyan"
        ))
    
    try:
        # PHASE 1: Crawl and consolidate content
        if not args.quiet:
            console.print(f"\n{ICON_START} Phase 1: Crawling website...", style="bold cyan")
        
        logger.info("Phase 1: Starting crawl")
        
        config = SimpleCrawlConfig(
            max_depth=args.depth,
            max_pages=args.max_pages,
            delay=args.delay,
            respect_robots=not args.no_robots
        )
        
        crawler = SimpleCrawler(config=config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
            transient=True
        ) as progress:
            if not args.quiet:
                task = progress.add_task("Crawling pages...", total=None)
            
            crawl_results = crawler.crawl(url)
        
        logger.info(f"Crawl completed: {crawl_results['total_pages']} pages")
        
        if not args.quiet:
            console.print(f"{ICON_SUCCESS} Crawled {crawl_results['total_pages']} pages at depth {crawl_results['depth_reached']}")
            console.print(f"{ICON_SUCCESS} Found {len(crawl_results['routes'])} routes")
        
        # PHASE 2: Extract events with single AI call
        if not args.quiet:
            console.print(f"\n{ICON_START} Phase 2: Extracting event information...", style="bold cyan")
        
        logger.info("Phase 2: Starting event extraction")
        
        try:
            extractor = EventExtractor()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                if not args.quiet:
                    task = progress.add_task("Analyzing content with AI...", total=None)
                
                event_results = extractor.extract_events(
                    base_url=crawl_results['base_url'],
                    content_by_url=crawl_results['content_by_url'],
                    routes=crawl_results['routes']
                )
            
            logger.info(f"Event extraction completed: {len(event_results.get('events_found', []))} events found")
            
            if not args.quiet:
                console.print(f"{ICON_SUCCESS} Event extraction complete")
            
        except Exception as e:
            logger.error(f"Event extraction failed: {e}")
            console.print(f"[yellow]{ICON_WARNING} AI extraction failed: {e}[/yellow]")
            console.print(f"[yellow]{ICON_WARNING} Continuing with crawl results only...[/yellow]")
            
            # Fallback: save crawl results without AI extraction
            event_results = {
                "base_url": crawl_results['base_url'],
                "routes": crawl_results['routes'],
                "purpose": "Unable to extract with AI",
                "events_found": []
            }
        
        # Display results
        if not args.quiet:
            console.print(f"\n{ICON_SUCCESS} Processing complete!", style="bold green")
            display_results(event_results)
        
        # Save results
        save_results(event_results, args.output)
        logger.info(f"Results saved to {args.output}")
        
        if not args.quiet:
            console.print(f"\n{ICON_SUCCESS} All done! Check {args.output} for results.", style="bold green")
    
    except KeyboardInterrupt:
        logger.warning("Crawl interrupted by user")
        console.print(f"\n[yellow]{ICON_WARNING} Crawl interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during crawling: {e}", exc_info=True)
        console.print(f"[red]{ICON_ERROR} Error: {e}[/red]")
        if args.verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)
    finally:
        logger.info("Crawl session ended")
        logger.info("=" * 50)


if __name__ == "__main__":
    main()