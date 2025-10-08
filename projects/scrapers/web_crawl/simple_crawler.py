"""
Simple Web Crawler - Focused on content extraction without AI analysis.

This module provides efficient web crawling with multiprocessing support,
extracting clean content and links for downstream event analysis.
"""

import logging
import time
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from utils import (
    is_valid_url,
    normalize_url,
    should_crawl_url,
    clean_text_content,
    aggressive_content_filter,
    extract_event_keywords,
    RateLimiter,
    parse_robots_txt
)

logger = logging.getLogger("web_crawler")


@dataclass
class PageContent:
    """Content extracted from a single page."""
    url: str
    content: str
    links: List[str]
    success: bool
    error: Optional[str] = None


class SimpleCrawlConfig(BaseModel):
    """Configuration for simple web crawling."""
    max_depth: int = Field(default=2, description="Maximum crawl depth")
    max_pages: int = Field(default=50, description="Maximum pages to crawl")
    delay: float = Field(default=1.0, description="Delay between requests")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_workers: int = Field(default=5, description="Max concurrent workers")
    user_agent: str = Field(
        default="EventCrawler/1.0 (Event Discovery Bot)",
        description="User agent string"
    )
    respect_robots: bool = Field(default=True, description="Respect robots.txt")
    max_content_chars: int = Field(default=50000, description="Max content characters per page")


def fetch_page(url: str, config: SimpleCrawlConfig, base_url: str) -> PageContent:
    """
    Fetch and extract content from a single URL.
    
    This function is designed to be called by multiprocessing workers.
    
    Args:
        url: URL to fetch
        config: Crawl configuration
        base_url: Base URL for the crawl (for link filtering)
        
    Returns:
        PageContent with extracted data
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': config.user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    })
    
    try:
        logger.info(f"Fetching: {url}")
        
        response = session.get(url, timeout=config.timeout, allow_redirects=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'html' not in content_type:
            return PageContent(
                url=url,
                content="",
                links=[],
                success=False,
                error=f"Non-HTML content: {content_type}"
            )
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove unwanted elements aggressively
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                           'aside', 'iframe', 'noscript', 'svg', 'form']):
            element.decompose()
        
        # Extract and clean text content
        text_content = soup.get_text(separator=' ', strip=True)
        text_content = clean_text_content(text_content)
        text_content = aggressive_content_filter(text_content)
        
        # Truncate if too long
        if len(text_content) > config.max_content_chars:
            text_content = text_content[:config.max_content_chars]
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(url, link['href'])
            normalized_url = normalize_url(absolute_url)
            
            # Check if this link is relevant for event pages
            link_text = link.get_text().strip().lower()
            href = link['href'].lower()
            
            # Prioritize event-related links
            if should_crawl_url(normalized_url, base_url):
                # Boost event-related links
                if any(keyword in href or keyword in link_text 
                       for keyword in ['event', 'calendar', 'activity', 'schedule', 
                                      'happening', 'program', 'class']):
                    links.insert(0, normalized_url)  # Add to front
                else:
                    links.append(normalized_url)
        
        # Remove duplicate links while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        logger.info(f"Successfully fetched {url}: {len(text_content)} chars, {len(unique_links)} links")
        
        return PageContent(
            url=url,
            content=text_content,
            links=unique_links,
            success=True
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {url}: {e}")
        return PageContent(
            url=url,
            content="",
            links=[],
            success=False,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}")
        return PageContent(
            url=url,
            content="",
            links=[],
            success=False,
            error=str(e)
        )
    finally:
        session.close()


class SimpleCrawler:
    """Simplified web crawler focused on content extraction."""
    
    def __init__(self, config: Optional[SimpleCrawlConfig] = None):
        """
        Initialize the crawler.
        
        Args:
            config: Crawl configuration
        """
        self.config = config or SimpleCrawlConfig()
        self.rate_limiter = RateLimiter(delay=self.config.delay)
        logger.info(f"SimpleCrawler initialized with config: {self.config}")
    
    def crawl(self, start_url: str) -> Dict[str, any]:
        """
        Crawl starting from a base URL and extract all content.
        
        This implements a breadth-first crawl with multiprocessing support.
        
        Args:
            start_url: Starting URL to crawl
            
        Returns:
            Dictionary with base_url, all_content, and routes
        """
        logger.info(f"Starting crawl from: {start_url}")
        
        # Normalize start URL
        start_url = normalize_url(start_url)
        if not start_url.startswith(('http://', 'https://')):
            start_url = f"https://{start_url}"
        
        # Track URLs
        urls_to_crawl = [start_url]
        processed_urls = set()
        all_pages = []
        current_depth = 0
        
        # Crawl by depth
        while urls_to_crawl and current_depth < self.config.max_depth:
            current_batch = urls_to_crawl[:self.config.max_pages - len(processed_urls)]
            urls_to_crawl = []
            
            logger.info(f"Crawling depth {current_depth + 1}: {len(current_batch)} URLs")
            
            # Process batch with rate limiting
            batch_results = []
            for url in current_batch:
                if url in processed_urls:
                    continue
                
                self.rate_limiter.wait_if_needed()
                processed_urls.add(url)
                
                # Fetch page (in main process to respect rate limiting)
                page = fetch_page(url, self.config, start_url)
                batch_results.append(page)
                
                if len(processed_urls) >= self.config.max_pages:
                    break
            
            # Process results
            for page in batch_results:
                if page.success and page.content:
                    all_pages.append(page)
                    
                    # Add links for next depth
                    if current_depth < self.config.max_depth - 1:
                        for link in page.links[:20]:  # Limit links per page
                            if link not in processed_urls:
                                urls_to_crawl.append(link)
            
            current_depth += 1
            
            if len(processed_urls) >= self.config.max_pages:
                logger.info(f"Reached max pages limit: {self.config.max_pages}")
                break
        
        # Consolidate results
        base_url_content = ""
        all_content_by_url = {}
        routes = []
        
        for page in all_pages:
            all_content_by_url[page.url] = page.content
            if page.url == start_url:
                base_url_content = page.content
            else:
                routes.append(page.url)
        
        logger.info(f"Crawl completed: {len(all_pages)} pages crawled, {len(routes)} routes found")
        
        return {
            "base_url": start_url,
            "base_content": base_url_content,
            "routes": routes,
            "content_by_url": all_content_by_url,
            "total_pages": len(all_pages),
            "depth_reached": current_depth
        }
