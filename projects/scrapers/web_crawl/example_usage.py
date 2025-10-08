#!/usr/bin/env python3
"""
Example usage of the Professional Web Crawler

This script demonstrates various ways to use the web crawler
both programmatically and via CLI commands.
"""

import json
from web_crawler import WebCrawler, CrawlConfig
from content_analyzer import ContentAnalyzer
from utils import setup_logging

def basic_crawling_example():
    """Example of basic web crawling without AI."""
    print("=== Basic Crawling Example ===")
    
    # Setup logging
    logger = setup_logging("INFO")
    
    # Create a simple config
    config = CrawlConfig(
        max_depth=2,
        max_pages=10,
        delay=1.0,
        max_workers=3
    )
    
    # Initialize crawler (no AI analyzer)
    crawler = WebCrawler(config=config)
    
    try:
        # Crawl a simple website
        results = crawler.crawl_urls(
            start_urls=["https://httpbin.org/html"],
            exhaustive=False
        )
        
        # Display results
        print(f"Crawled {results['crawl_summary']['successful_crawls']} pages")
        print(f"Found {len(results['pages'])} total pages")
        
        # Show first page details
        if results['pages']:
            first_page = results['pages'][0]
            print(f"First page: {first_page['title']}")
            print(f"Word count: {first_page['word_count']}")
            print(f"Links found: {first_page['links_found']}")
    
    finally:
        crawler.close()


def ai_powered_example():
    """Example of AI-powered content analysis (requires API key)."""
    print("\n=== AI-Powered Analysis Example ===")
    
    try:
        # Initialize AI analyzer (will fail without API key)
        analyzer = ContentAnalyzer()
        
        config = CrawlConfig(
            max_depth=2,
            max_pages=5,
            delay=1.0
        )
        
        crawler = WebCrawler(config=config, analyzer=analyzer)
        
        try:
            # Crawl with AI analysis
            results = crawler.crawl_urls(
                start_urls=["https://httpbin.org/html"],
                search_query="HTML documentation",
                exhaustive=False
            )
            
            # Show AI analysis results
            if 'ai_analysis' in results:
                ai_summary = results['ai_analysis']
                print(f"AI found {ai_summary.get('relevant_pages', 0)} relevant pages")
                print(f"Key themes: {', '.join(ai_summary.get('key_themes', []))}")
            
            # Show content matches
            if 'content_matches' in results:
                print(f"Content matches: {len(results['content_matches'])}")
                for match in results['content_matches'][:3]:  # Show top 3
                    print(f"  - {match['url']}: {match['relevance_score']:.2f}")
        
        finally:
            crawler.close()
            
    except ValueError as e:
        print(f"AI Analyzer not available: {e}")
        print("Set GEMINI_API_KEY environment variable to enable AI features")


def cli_examples():
    """Show CLI command examples."""
    print("\n=== CLI Command Examples ===")
    
    examples = [
        {
            "description": "Basic crawling",
            "command": "python crawl.py --url 'httpbin.org/html'"
        },
        {
            "description": "Multiple URLs",
            "command": "python crawl.py --url 'httpbin.org/html,httpbin.org/json'"
        },
        {
            "description": "Deep crawling with custom settings",
            "command": "python crawl.py --url 'example.com' --depth 3 --max-pages 50 --delay 1.5"
        },
        {
            "description": "AI-powered search (requires API key)",
            "command": "python crawl.py --url 'example.com' --search 'events calendar' --exhaustive"
        },
        {
            "description": "Save results to file",
            "command": "python crawl.py --url 'example.com' --search 'products' --output results.json"
        },
        {
            "description": "Quiet mode for scripting",
            "command": "python crawl.py --url 'example.com' --quiet > output.json"
        },
        {
            "description": "Verbose debugging",
            "command": "python crawl.py --url 'example.com' --verbose --delay 2.0"
        }
    ]
    
    for example in examples:
        print(f"\n{example['description']}:")
        print(f"  {example['command']}")


def configuration_example():
    """Show configuration examples."""
    print("\n=== Configuration Examples ===")
    
    # Basic config
    basic_config = CrawlConfig()
    print("Basic config:")
    print(f"  Max depth: {basic_config.max_depth}")
    print(f"  Max pages: {basic_config.max_pages}")
    print(f"  Delay: {basic_config.delay}s")
    
    # Advanced config
    advanced_config = CrawlConfig(
        max_depth=5,
        max_pages=200,
        delay=0.5,
        max_workers=10,
        user_agent="CustomBot/1.0",
        respect_robots=False,
        timeout=60
    )
    
    print("\nAdvanced config:")
    print(f"  Max depth: {advanced_config.max_depth}")
    print(f"  Max pages: {advanced_config.max_pages}")
    print(f"  Delay: {advanced_config.delay}s")
    print(f"  Workers: {advanced_config.max_workers}")
    print(f"  User agent: {advanced_config.user_agent}")
    print(f"  Respect robots: {advanced_config.respect_robots}")


def main():
    """Run all examples."""
    print("🕷️ Professional Web Crawler - Usage Examples\n")
    
    # Run examples
    basic_crawling_example()
    ai_powered_example()
    cli_examples()
    configuration_example()
    
    print("\n" + "="*50)
    print("🎉 Examples completed!")
    print("\nTo get started:")
    print("1. Set up your GEMINI_API_KEY in .env file")
    print("2. Try: python crawl.py --url 'httpbin.org/html'")
    print("3. For AI features: python crawl.py --url 'example.com' --search 'your query'")


if __name__ == "__main__":
    main()