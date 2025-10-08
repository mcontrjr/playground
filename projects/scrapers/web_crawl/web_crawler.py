"""
Web Crawler - Core crawling functionality with BeautifulSoup.

This module provides the main WebCrawler class that handles URL fetching,
content extraction, link discovery, and coordination with the AI analyzer.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify
from pydantic import BaseModel, Field

from utils import (
    is_valid_url, 
    normalize_url, 
    should_crawl_url, 
    clean_text_content,
    RateLimiter,
    parse_robots_txt,
    truncate_content
)
from content_analyzer import ContentAnalyzer, ContentMatch

logger = logging.getLogger("web_crawler.crawler")


@dataclass
class CrawlResult:
    """Result of crawling a single URL."""
    url: str
    title: str
    content: str
    links: List[str]
    status_code: int
    error: Optional[str] = None
    content_type: str = ""
    word_count: int = 0


class CrawlConfig(BaseModel):
    """Configuration for web crawling."""
    max_depth: int = Field(default=2, description="Maximum crawl depth")
    max_pages: int = Field(default=50, description="Maximum pages to crawl")
    delay: float = Field(default=1.0, description="Delay between requests")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_workers: int = Field(default=5, description="Max concurrent workers")
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
        description="User agent string"
    )
    respect_robots: bool = Field(default=True, description="Respect robots.txt")
    follow_redirects: bool = Field(default=True, description="Follow HTTP redirects")
    max_content_length: int = Field(default=1000000, description="Max content length")


class WebCrawler:
    """Professional web crawler with AI-powered content analysis."""
    
    def __init__(self, config: Optional[CrawlConfig] = None, analyzer: Optional[ContentAnalyzer] = None):
        """
        Initialize the web crawler.
        
        Args:
            config: Crawling configuration
            analyzer: Content analyzer instance
        """
        self.config = config or CrawlConfig()
        self.analyzer = analyzer
        self.rate_limiter = RateLimiter(delay=self.config.delay)
        self.session = requests.Session()
        # More realistic browser headers to avoid detection
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Track crawled URLs to avoid duplicates
        self.crawled_urls: Set[str] = set()
        self.robots_cache: Dict[str, Any] = {}
        
        logger.info(f"WebCrawler initialized with config: {self.config}")
    
    def can_crawl_url(self, url: str) -> bool:
        """
        Check if URL can be crawled based on robots.txt and other rules.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL can be crawled
        """
        if not is_valid_url(url):
            return False
        
        if not self.config.respect_robots:
            return True
        
        try:
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Check robots.txt cache
            if domain not in self.robots_cache:
                self.robots_cache[domain] = parse_robots_txt(domain)
            
            robots_parser = self.robots_cache[domain]
            return robots_parser.can_fetch(self.config.user_agent, url)
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Allow crawling if robots.txt check fails
    
    def fetch_url(self, url: str) -> CrawlResult:
        """
        Fetch content from a single URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            CrawlResult with page content and metadata
        """
        self.rate_limiter.wait_if_needed()
        
        try:
            logger.debug(f"Fetching: {url}")
            
            response = self.session.get(
                url,
                timeout=self.config.timeout,
                allow_redirects=self.config.follow_redirects
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'html' not in content_type:
                return CrawlResult(
                    url=url,
                    title="",
                    content="",
                    links=[],
                    status_code=response.status_code,
                    error=f"Non-HTML content type: {content_type}",
                    content_type=content_type
                )
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ""
            
            # Extract main content (remove scripts, styles, etc.)
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Get text content
            text_content = clean_text_content(soup.get_text())
            text_content = truncate_content(text_content, self.config.max_content_length)
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                normalized_url = normalize_url(absolute_url)
                if should_crawl_url(normalized_url, url):
                    links.append(normalized_url)
            
            return CrawlResult(
                url=url,
                title=title,
                content=text_content,
                links=list(set(links)),  # Remove duplicates
                status_code=response.status_code,
                content_type=content_type,
                word_count=len(text_content.split())
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            status_code = 0
            
            # Extract status code if available
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code == 403:
                    error_msg = f"403 Forbidden - Website blocking automated access (likely anti-bot protection)"
                elif status_code == 404:
                    error_msg = f"404 Not Found - Page does not exist"
                elif status_code in [429, 503]:
                    error_msg = f"{status_code} - Server overloaded or rate limiting active"
            
            logger.error(f"Request error for {url}: {error_msg}")
            return CrawlResult(
                url=url,
                title="",
                content="",
                links=[],
                status_code=status_code,
                error=error_msg
            )
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return CrawlResult(
                url=url,
                title="",
                content="",
                links=[],
                status_code=0,
                error=str(e)
            )
    
    def crawl_urls(
        self, 
        start_urls: List[str], 
        search_query: Optional[str] = None,
        exhaustive: bool = False
    ) -> Dict[str, Any]:
        """
        Crawl multiple URLs with optional AI-powered filtering.
        
        Args:
            start_urls: List of starting URLs
            search_query: Optional search query for content filtering
            exhaustive: If True, crawl more deeply
            
        Returns:
            Dictionary with crawl results and analysis
        """
        logger.info(f"Starting crawl of {len(start_urls)} URLs")
        logger.info(f"Search query: {search_query}")
        logger.info(f"Exhaustive mode: {exhaustive}")
        
        # Adjust config for exhaustive crawling
        if exhaustive:
            self.config.max_depth = 3
            self.config.max_pages = 100
        
        all_results = []
        failed_results = []
        content_matches = []
        urls_to_crawl = set(start_urls)
        processed_urls = set()
        depth = 0
        
        while urls_to_crawl and depth < self.config.max_depth and len(processed_urls) < self.config.max_pages:
            current_batch = list(urls_to_crawl)
            urls_to_crawl.clear()
            
            logger.info(f"Crawling depth {depth + 1}: {len(current_batch)} URLs")
            
            # Crawl current batch with threading
            batch_results = self._crawl_batch(current_batch)
            
            for result in batch_results:
                processed_urls.add(result.url)
                
                if result.error:
                    logger.warning(f"Failed to crawl {result.url}: {result.error}")
                    failed_results.append(result)
                    continue
                
                all_results.append(result)
                
                # Analyze content with AI if search query provided
                if search_query and self.analyzer and result.content:
                    try:
                        match = self.analyzer.analyze_content_relevance(
                            result.content,
                            search_query,
                            result.url,
                            result.title
                        )
                        content_matches.append(match)
                        
                        # If content is relevant, prioritize its links
                        if match.relevance_score > 0.5:
                            logger.info(f"High relevance ({match.relevance_score:.2f}): {result.url}")
                    except Exception as e:
                        logger.error(f"Error analyzing content for {result.url}: {e}")
                
                # Add new URLs from this page for next depth level
                if depth < self.config.max_depth - 1:
                    for link in result.links:
                        if (link not in processed_urls and 
                            link not in urls_to_crawl and 
                            self.can_crawl_url(link)):
                            
                            # If we have search query, use AI to filter links
                            if search_query and self.analyzer:
                                try:
                                    relevant_links = self.analyzer.find_relevant_links(
                                        [link], search_query, max_links=1
                                    )
                                    if relevant_links and relevant_links[0]['relevance_score'] > 0.3:
                                        urls_to_crawl.add(link)
                                except Exception as e:
                                    logger.error(f"Error filtering link {link}: {e}")
                                    urls_to_crawl.add(link)  # Add anyway if AI fails
                            else:
                                urls_to_crawl.add(link)
            
            depth += 1
        
        # Generate final results
        results = {
            "crawl_summary": {
                "total_urls_processed": len(processed_urls),
                "successful_crawls": len(all_results),
                "failed_crawls": len(failed_results),
                "max_depth_reached": depth,
                "search_query": search_query,
                "exhaustive_mode": exhaustive
            },
            "pages": [self._result_to_dict(result) for result in all_results],
            "failed_pages": [self._result_to_dict(result) for result in failed_results]
        }
        
        # Add AI analysis if available
        if content_matches and self.analyzer:
            try:
                ai_summary = self.analyzer.summarize_crawl_results(content_matches, search_query)
                results["ai_analysis"] = ai_summary
                results["content_matches"] = [match.model_dump() for match in content_matches]
            except Exception as e:
                logger.error(f"Error generating AI summary: {e}")
                results["ai_analysis"] = {"error": str(e)}
        
        logger.info(f"Crawl completed: {len(all_results)} pages crawled")
        return results
    
    def _crawl_batch(self, urls: List[str]) -> List[CrawlResult]:
        """
        Crawl a batch of URLs using ThreadPoolExecutor.
        
        Args:
            urls: List of URLs to crawl
            
        Returns:
            List of CrawlResult objects
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self.fetch_url, url): url 
                for url in urls if self.can_crawl_url(url)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    url = future_to_url[future]
                    logger.error(f"Error processing {url}: {e}")
                    results.append(CrawlResult(
                        url=url,
                        title="",
                        content="",
                        links=[],
                        status_code=0,
                        error=str(e)
                    ))
        
        return results
    
    def _result_to_dict(self, result: CrawlResult) -> Dict[str, Any]:
        """Convert CrawlResult to dictionary for JSON serialization."""
        return {
            "url": result.url,
            "title": result.title,
            "content": result.content[:1000] + "..." if len(result.content) > 1000 else result.content,
            "links_found": len(result.links),
            "word_count": result.word_count,
            "status_code": result.status_code,
            "error": result.error,
            "content_type": result.content_type
        }
    
    def close(self):
        """Clean up resources."""
        self.session.close()
        logger.info("WebCrawler session closed")