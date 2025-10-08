#!/usr/bin/env python3
"""
Website Access Diagnostic Tool

This script helps diagnose why a website might be blocking crawler access.
It tests different User-Agent strings and provides recommendations.
"""

import requests
import argparse
from urllib.parse import urljoin
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Different User-Agent strings to test
USER_AGENTS = {
    "crawler": "WebCrawler/1.0 (+https://github.com/your-repo)",
    "chrome_mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "firefox_mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
    "safari_mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "chrome_win": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "mobile": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (Mobile/15E148) Version/14.1.2 Safari/604.1"
}


def test_access(url: str, user_agent: str, timeout: int = 10) -> dict:
    """Test access to URL with given user agent."""
    try:
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        return {
            'success': True,
            'status_code': response.status_code,
            'content_type': response.headers.get('content-type', 'Unknown'),
            'server': response.headers.get('server', 'Unknown'),
            'content_length': len(response.content),
            'final_url': response.url,
            'redirected': response.url != url
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': str(e),
            'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') and e.response else None
        }


def test_robots_txt(url: str) -> dict:
    """Test if robots.txt is accessible."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        response = requests.get(robots_url, timeout=10)
        
        return {
            'accessible': response.status_code == 200,
            'status_code': response.status_code,
            'content_preview': response.text[:500] if response.status_code == 200 else None,
            'robots_url': robots_url
        }
    except Exception as e:
        return {
            'accessible': False,
            'error': str(e)
        }


def analyze_blocking_patterns(results: dict) -> list:
    """Analyze results to identify blocking patterns."""
    recommendations = []
    
    # Check if all requests failed
    all_failed = all(not result['success'] for result in results.values())
    
    if all_failed:
        # Check for consistent 403 errors
        status_codes = {result.get('status_code') for result in results.values() if result.get('status_code')}
        if 403 in status_codes:
            recommendations.append("🛡️ Website uses strong anti-bot protection (likely CDN/WAF like Cloudflare, Akamai)")
            recommendations.append("💡 Try: --delay 3.0 to slow down requests")
            recommendations.append("💡 Try: Different times of day (some sites block during peak hours)")
            recommendations.append("💡 Consider: Using residential proxy services")
        elif 429 in status_codes:
            recommendations.append("⚠️ Rate limiting detected")
            recommendations.append("💡 Try: Increase --delay to 2-5 seconds")
        else:
            recommendations.append("❓ Network or DNS issues possible")
    else:
        # Some succeeded - analyze which user agents work
        successful_agents = [agent for agent, result in results.items() if result['success']]
        if successful_agents:
            recommendations.append(f"✅ These user agents work: {', '.join(successful_agents)}")
            if 'crawler' not in successful_agents:
                recommendations.append("💡 Use browser-like user agent instead of crawler identification")
    
    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Diagnose website access issues for web crawling")
    parser.add_argument("url", help="URL to test")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout (default: 10s)")
    
    args = parser.parse_args()
    
    console.print(Panel(f"🔍 Diagnosing website access for: [bold]{args.url}[/bold]", border_style="blue"))
    
    # Test with different user agents
    console.print("\n📋 Testing different User-Agent strings...")
    
    table = Table(title="User-Agent Test Results")
    table.add_column("User-Agent Type", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    
    results = {}
    
    for agent_name, user_agent in USER_AGENTS.items():
        console.print(f"Testing {agent_name}...", end=" ")
        result = test_access(args.url, user_agent, args.timeout)
        results[agent_name] = result
        
        if result['success']:
            status = f"✅ {result['status_code']}"
            details = f"Server: {result.get('server', 'Unknown')}, Size: {result.get('content_length', 0)} bytes"
            if result.get('redirected'):
                details += f", Redirected to: {result['final_url']}"
            console.print("✅")
        else:
            status = f"❌ {result.get('status_code', 'Error')}"
            details = result.get('error', 'Unknown error')
            console.print("❌")
        
        table.add_row(agent_name, status, details)
    
    console.print(table)
    
    # Test robots.txt
    console.print("\n🤖 Testing robots.txt accessibility...")
    robots_result = test_robots_txt(args.url)
    
    if robots_result['accessible']:
        console.print("✅ robots.txt is accessible")
        if robots_result.get('content_preview'):
            console.print("Preview:")
            console.print(Panel(robots_result['content_preview'], border_style="green"))
    else:
        console.print(f"❌ robots.txt not accessible: {robots_result.get('error', 'Unknown')}")
    
    # Analyze and provide recommendations
    console.print("\n💡 Analysis & Recommendations:")
    recommendations = analyze_blocking_patterns(results)
    
    if recommendations:
        for rec in recommendations:
            console.print(f"  {rec}")
    else:
        console.print("  ✅ No major blocking detected - website should be crawlable")
    
    # Crawler command suggestions
    console.print("\n🕷️ Suggested crawler commands:")
    
    successful_agents = [agent for agent, result in results.items() if result['success']]
    if successful_agents:
        best_agent = successful_agents[0]  # Pick first successful one
        if best_agent != 'crawler':
            console.print(f"python crawl.py --url '{args.url}' --delay 2.0")
            console.print("(Using browser-like user agent and slower requests)")
        else:
            console.print(f"python crawl.py --url '{args.url}'")
            console.print("(Standard crawler should work fine)")
    else:
        console.print("❌ Website appears to block all automated access")
        console.print("Consider manual browsing or specialized scraping services")


if __name__ == "__main__":
    main()