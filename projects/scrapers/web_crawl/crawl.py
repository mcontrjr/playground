#!/usr/bin/env python3
"""
Event Discovery Web Crawler

Simplified architecture with two phases:
1) Crawl and consolidate content (no UI dependencies)
2) Single AI extraction call to identify event information

CLI entrypoint: crawl.py
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

# Prefer a 'kogging' library if installed; fallback to stdlib logging
try:  # pragma: no cover
    import kogging as logging  # type: ignore
except Exception:  # pragma: no cover
    import logging  # type: ignore

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from utils import (
    is_valid_url,
    normalize_url,
    should_crawl_url,
    clean_text_content,
    aggressive_content_filter,
    RateLimiter,
)
from event_extractor import EventExtractor

# Module-level logger (handlers configured in main)
logger = logging.getLogger("crawler")


# ---------- CLI helpers ----------

def parse_url(url_string: str) -> Optional[str]:
    url = (url_string or "").strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url if is_valid_url(url) else None


def setup_logger(level: str = "INFO", log_file: str = "crawl.log", to_stderr: bool = True) -> logging.Logger:
    root = logging.getLogger()
    # Map string -> level
    lvl = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(lvl)
    # Reset handlers
    root.handlers.clear()
    # File handler
    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    fh.setLevel(lvl)
    root.addHandler(fh)
    # Optional console handler (lightweight)
    if to_stderr:
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        sh.setLevel(lvl)
        root.addHandler(sh)
    return logging.getLogger("crawler")


# ---------- Crawler (merged from simple_crawler.py) ----------

class CrawlerConfig(BaseModel):
    max_depth: int = Field(default=2, description="Maximum crawl depth")
    max_pages: int = Field(default=50, description="Maximum pages to crawl")
    delay: float = Field(default=1.0, description="Delay between requests in seconds")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    user_agent: str = Field(default="EventCrawler/1.0 (Event Discovery Bot)", description="User agent")
    respect_robots: bool = Field(default=True, description="Respect robots.txt")
    max_content_chars: int = Field(default=50000, description="Max content characters per page")


class Crawler:
    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self.rate_limiter = RateLimiter(delay=self.config.delay)
        logger.info(f"Crawler initialized: {self.config}")

    def _fetch_page(self, url: str, base_url: str) -> Dict[str, Optional[object]]:
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        })
        try:
            logger.info(f"Fetching: {url}")
            resp = session.get(url, timeout=self.config.timeout, allow_redirects=True)
            resp.raise_for_status()
            ctype = resp.headers.get("content-type", "").lower()
            if "html" not in ctype:
                return {"url": url, "content": "", "links": [], "ok": False, "err": f"Non-HTML: {ctype}"}

            soup = BeautifulSoup(resp.content, "lxml")
            for el in soup(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript", "svg", "form"]):
                el.decompose()

            text = soup.get_text(separator=" ", strip=True)
            text = clean_text_content(text)
            text = aggressive_content_filter(text)
            if len(text) > self.config.max_content_chars:
                text = text[: self.config.max_content_chars]

            links: List[str] = []
            for a in soup.find_all("a", href=True):
                absolute = requests.compat.urljoin(url, a["href"])
                normalized = normalize_url(absolute)
                ltxt = (a.get_text() or "").strip().lower()
                href_l = a["href"].lower()
                if should_crawl_url(normalized, base_url):
                    if any(k in href_l or k in ltxt for k in [
                        "event", "calendar", "activity", "schedule", "happening", "program", "class"
                    ]):
                        links.insert(0, normalized)
                    else:
                        links.append(normalized)
            # dedupe preserve order
            seen = set()
            uniq: List[str] = []
            for l in links:
                if l not in seen:
                    seen.add(l)
                    uniq.append(l)

            logger.info(f"Fetched {url}: {len(text)} chars, {len(uniq)} links")
            return {"url": url, "content": text, "links": uniq, "ok": True, "err": None}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return {"url": url, "content": "", "links": [], "ok": False, "err": str(e)}
        except Exception as e:  # pragma: no cover
            logger.error(f"Unexpected error for {url}: {e}")
            return {"url": url, "content": "", "links": [], "ok": False, "err": str(e)}
        finally:
            session.close()

    def crawl(self, start_url: str) -> Dict[str, object]:
        start_url = normalize_url(start_url)
        if not start_url.startswith(("http://", "https://")):
            start_url = f"https://{start_url}"
        logger.info(f"Starting crawl from: {start_url}")

        urls_to_crawl: List[str] = [start_url]
        processed = set()
        pages: List[Dict[str, object]] = []
        depth = 0

        while urls_to_crawl and depth < self.config.max_depth:
            batch = urls_to_crawl[: self.config.max_pages - len(processed)]
            urls_to_crawl = []
            logger.info(f"Depth {depth + 1}: {len(batch)} URLs")

            for u in batch:
                if u in processed:
                    continue
                self.rate_limiter.wait_if_needed()
                processed.add(u)
                page = self._fetch_page(u, start_url)
                if page.get("ok") and page.get("content"):
                    pages.append(page)  # type: ignore
                    if depth < self.config.max_depth - 1:
                        for link in (page.get("links") or [])[:20]:  # type: ignore
                            if link not in processed:
                                urls_to_crawl.append(link)  # type: ignore
                if len(processed) >= self.config.max_pages:
                    logger.info(f"Reached max pages: {self.config.max_pages}")
                    break
            depth += 1

        content_by_url: Dict[str, str] = {}
        routes: List[str] = []
        base_content = ""
        for p in pages:
            url = p["url"]  # type: ignore
            content = p["content"]  # type: ignore
            content_by_url[url] = content  # type: ignore
            if url == start_url:
                base_content = content  # type: ignore
            else:
                routes.append(url)  # type: ignore

        logger.info(f"Crawl complete: {len(pages)} pages, {len(routes)} routes")
        return {
            "base_url": start_url,
            "base_content": base_content,
            "routes": routes,
            "content_by_url": content_by_url,
            "total_pages": len(pages),
            "depth_reached": depth,
        }


# ---------- CLI ----------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Event Discovery Web Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  crawl.py --url \"https://example.com\"\n"
            "  crawl.py --url \"https://city.gov\" --depth 3 --output events.json\n"
            "  crawl.py --url \"https://city.gov\" --max-pages 100 --verbose\n"
        ),
    )
    parser.add_argument("--url", "-u", required=True, help="URL to crawl for event information")
    parser.add_argument("--output", "-o", default="output.json", help="Output JSON file path")
    parser.add_argument("--depth", type=int, default=2, help="Max crawl depth")
    parser.add_argument("--max-pages", type=int, default=50, help="Max pages to crawl")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (s)")
    parser.add_argument("--no-robots", action="store_true", help="Ignore robots.txt restrictions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging (DEBUG)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet logging (WARNING)")

    args = parser.parse_args()

    level = "DEBUG" if args.verbose else "INFO"
    if args.quiet:
        level = "WARNING"
    setup_logger(level=level, log_file="crawl.log", to_stderr=not args.quiet)

    # ICONS
    ICON_START = "[>]"
    ICON_SUCCESS = "[+]"
    ICON_WARN = "[!]"
    ICON_ERR = "[-]"

    url = parse_url(args.url)
    if not url:
        print(f"{ICON_ERR} invalid URL")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("Starting new crawl session")
    logger.info(f"URL: {url}")
    logger.info(f"Depth: {args.depth}, Max pages: {args.max_pages}")

    try:
        # Phase 1: Crawl
        logger.info("Phase 1: crawl start")
        config = CrawlerConfig(
            max_depth=args.depth,
            max_pages=args.max_pages,
            delay=args.delay,
            respect_robots=not args.no_robots,
        )
        crawler = Crawler(config=config)
        crawl_results = crawler.crawl(url)
        logger.info(f"Crawled {crawl_results['total_pages']} pages @ depth {crawl_results['depth_reached']} for {crawl_results['base_url']}")

        # Phase 2: Extract
        logger.info("Phase 2: extract start")
        try:
            extractor = EventExtractor()
            event_results = extractor.extract_events(
                base_url=crawl_results["base_url"],
                content_by_url=crawl_results["content_by_url"],
                routes=crawl_results["routes"],
            )
            logger.info(
                f"Event extraction complete: {len(event_results.get('events_found', []))} events for {event_results.get('base_url')}"
            )
        except Exception as e:
            logger.warning(f"AI extraction failed: {e}")
            logger.warning("Continuing with crawl results only")
            event_results = {
                "base_url": crawl_results["base_url"],
                "routes": crawl_results["routes"],
                "purpose": "Unable to extract with AI",
                "events_found": [],
                "extractor_report": extractor.report()
            }

        # Save
        try:
            output = {
                event_results.get("base_url", url): {
                    "routes": event_results.get("routes", []),
                    "purpose": event_results.get("purpose", ""),
                    "events_found": event_results.get("events_found", []),
                }
            }
            os.makedirs('output', exist_ok=True)
            with open(os.path.join('output', args.output), "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {args.output}")
            if not args.quiet:
                print(f"{ICON_SUCCESS} saved -> {args.output}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            print(f"{ICON_ERR} error saving results: {e}")
            sys.exit(1)

        if not args.quiet:
            print(f"{ICON_SUCCESS} done")

    except KeyboardInterrupt:
        logger.warning("Crawl interrupted by user")
        print(f"{ICON_WARN} interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during crawling: {e}", exc_info=True)
        print(f"{ICON_ERR} error: {e}")
        sys.exit(1)
    finally:
        logger.info("Crawl session ended")
        logger.info("=" * 50)


if __name__ == "__main__":
    main()
