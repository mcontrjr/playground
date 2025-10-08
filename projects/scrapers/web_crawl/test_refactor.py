#!/usr/bin/env python3
"""
Quick test script to verify the refactored crawler works.
"""

import sys
from simple_crawler import SimpleCrawler, SimpleCrawlConfig
from event_extractor import EventExtractor
from utils import setup_logging

def test_crawler():
    """Test the simple crawler without AI."""
    print("\n[TEST] Testing simple crawler...")
    
    # Setup logging
    logger = setup_logging("INFO", "test_crawl.log")
    
    # Configure for quick test
    config = SimpleCrawlConfig(
        max_depth=1,
        max_pages=5,
        delay=0.5
    )
    
    crawler = SimpleCrawler(config)
    
    # Test with a simple URL
    test_url = "https://example.com"
    print(f"[TEST] Crawling {test_url}...")
    
    try:
        results = crawler.crawl(test_url)
        print(f"[+] Crawl successful!")
        print(f"    - Base URL: {results['base_url']}")
        print(f"    - Pages crawled: {results['total_pages']}")
        print(f"    - Routes found: {len(results['routes'])}")
        print(f"    - Content length: {len(results.get('base_content', ''))} chars")
        return True
    except Exception as e:
        print(f"[-] Crawl failed: {e}")
        return False


def test_event_extractor():
    """Test the event extractor with mock data."""
    print("\n[TEST] Testing event extractor...")
    
    # Mock crawl results
    mock_data = {
        "base_url": "https://example.com",
        "content_by_url": {
            "https://example.com": "Welcome to our community center. Join us for events and activities.",
            "https://example.com/events": "Summer Festival on July 15, 2025 from 10:00 AM to 6:00 PM at 123 Main Street."
        },
        "routes": ["https://example.com/events"]
    }
    
    try:
        extractor = EventExtractor()
        print("[+] Event extractor initialized")
        
        print("[TEST] Extracting events from mock data...")
        results = extractor.extract_events(
            base_url=mock_data['base_url'],
            content_by_url=mock_data['content_by_url'],
            routes=mock_data['routes']
        )
        
        print(f"[+] Extraction successful!")
        print(f"    - Purpose: {results.get('purpose', 'N/A')}")
        print(f"    - Event routes: {len(results.get('routes', []))}")
        print(f"    - Events found: {len(results.get('events_found', []))}")
        
        return True
        
    except ValueError as e:
        print(f"[-] Event extractor initialization failed: {e}")
        print("    (This is expected if GEMINI_API_KEY is not set)")
        return False
    except Exception as e:
        print(f"[-] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*50)
    print("REFACTORED CRAWLER TEST SUITE")
    print("="*50)
    
    # Test 1: Simple Crawler
    crawler_ok = test_crawler()
    
    # Test 2: Event Extractor (may fail without API key)
    extractor_ok = test_event_extractor()
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Simple Crawler: {'[+] PASS' if crawler_ok else '[-] FAIL'}")
    print(f"Event Extractor: {'[+] PASS' if extractor_ok else '[-] FAIL (check API key)'}")
    print("="*50)
    
    if crawler_ok:
        print("\n[+] Core functionality is working!")
        print("[i] You can now use: python crawl.py --url <URL>")
    else:
        print("\n[-] Tests failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
