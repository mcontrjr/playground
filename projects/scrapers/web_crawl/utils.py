"""
Utility functions for the web crawler.

This module contains helper functions for URL validation, content processing,
rate limiting, and other common operations.
"""

import re
import time
import logging
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.robotparser import RobotFileParser


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = "crawl.log") -> logging.Logger:
    """
    Set up logging configuration for the crawler.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Log file path (defaults to crawl.log)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("web_crawler")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler - always log to file
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def is_valid_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_url(url: str, base_url: str = "") -> str:
    """
    Normalize and clean a URL.
    
    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs
        
    Returns:
        Normalized absolute URL
    """
    # Handle relative URLs
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    # Parse and rebuild URL
    parsed = urlparse(url)
    
    # Remove fragment and query parameters that don't affect content
    query_params = parse_qs(parsed.query)
    # Keep only essential parameters (customize as needed)
    essential_params = ['id', 'page', 'category']
    filtered_params = {k: v for k, v in query_params.items() 
                      if k in essential_params}
    
    # Rebuild query string
    query_string = '&'.join([f"{k}={v[0]}" for k, v in filtered_params.items()])
    
    # Rebuild URL without fragment
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if query_string:
        normalized += f"?{query_string}"
    
    return normalized


def extract_links_from_html(html_content: str, base_url: str) -> Set[str]:
    """
    Extract and normalize all links from HTML content.
    
    Args:
        html_content: Raw HTML content
        base_url: Base URL for resolving relative links
        
    Returns:
        Set of normalized absolute URLs
    """
    from bs4 import BeautifulSoup
    
    links = set()
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Find all anchor tags with href
    for link in soup.find_all('a', href=True):
        url = normalize_url(link['href'], base_url)
        if is_valid_url(url):
            links.add(url)
    
    return links


def clean_text_content(text: str) -> str:
    """
    Clean and normalize text content for analysis.
    
    Args:
        text: Raw text content
        
    Returns:
        Cleaned text content
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E]', '', text)
    
    return text


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs belong to the same domain.
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        True if same domain, False otherwise
    """
    try:
        domain1 = urlparse(url1).netloc.lower()
        domain2 = urlparse(url2).netloc.lower()
        return domain1 == domain2
    except Exception:
        return False


def should_crawl_url(url: str, base_url: str, allowed_domains: Optional[Set[str]] = None) -> bool:
    """
    Determine if a URL should be crawled based on various criteria.
    
    Args:
        url: URL to check
        base_url: Base URL for domain comparison
        allowed_domains: Set of allowed domains (if None, same domain only)
        
    Returns:
        True if URL should be crawled, False otherwise
    """
    if not is_valid_url(url):
        return False
    
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    
    # Check domain restrictions
    if allowed_domains:
        if parsed_url.netloc not in allowed_domains:
            return False
    else:
        # Same domain only
        if parsed_url.netloc != parsed_base.netloc:
            return False
    
    # Skip common non-content URLs
    skip_patterns = [
        r'\.(css|js|png|jpg|jpeg|gif|pdf|zip|exe|dmg)$',
        r'(login|register|logout|admin)',
        r'(api/|ajax/|webhook)',
        r'mailto:',
        r'tel:',
        r'javascript:',
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, url.lower()):
            return False
    
    return True


class RateLimiter:
    """Simple rate limiter to avoid overwhelming servers."""
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            delay: Minimum delay between requests in seconds
        """
        self.delay = delay
        self.last_request_time = 0.0
    
    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


def parse_robots_txt(base_url: str) -> RobotFileParser:
    """
    Parse robots.txt for a domain.
    
    Args:
        base_url: Base URL of the domain
        
    Returns:
        RobotFileParser instance
    """
    try:
        robots_url = urljoin(base_url, '/robots.txt')
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp
    except Exception:
        # Return permissive parser if robots.txt can't be accessed
        rp = RobotFileParser()
        rp.allow_all = True
        return rp


def truncate_content(content: str, max_length: int = 1000000) -> str:
    """
    Truncate content to maximum length for processing.
    
    Args:
        content: Content to truncate
        max_length: Maximum length in characters
        
    Returns:
        Truncated content
    """
    if len(content) <= max_length:
        return content
    
    return content[:max_length] + "... [truncated]"


def extract_domain_from_url(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain string
    """
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def aggressive_content_filter(text: str) -> str:
    """
    Aggressively filter content to focus on event-related information.
    
    Removes common boilerplate, navigation text, and non-event content
    to reduce token usage and improve AI extraction quality.
    
    Args:
        text: Text content to filter
        
    Returns:
        Filtered text content
    """
    if not text:
        return ""
    
    # Convert to lowercase for pattern matching
    text_lower = text.lower()
    
    # Remove common boilerplate phrases
    remove_patterns = [
        r'cookie policy',
        r'privacy policy',
        r'terms of service',
        r'all rights reserved',
        r'copyright \d{4}',
        r'follow us on',
        r'share this',
        r'skip to (main content|navigation)',
        r'search this site',
        r'back to top',
    ]
    
    for pattern in remove_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    text = re.sub(r'\s{3,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove standalone URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    return text.strip()


def extract_event_keywords(text: str) -> List[str]:
    """
    Extract event-related keywords from text.
    
    Helps identify pages that likely contain event information.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of event-related keywords found
    """
    event_keywords = [
        'event', 'calendar', 'schedule', 'activity', 'program',
        'class', 'workshop', 'seminar', 'conference', 'meeting',
        'registration', 'rsvp', 'date', 'time', 'location',
        'address', 'venue', 'upcoming', 'happening', 'when',
        'where', 'join us', 'attend', 'participate'
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in event_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords
