# 🕷️ Professional Web Crawler with AI-Powered Analysis

A sophisticated web crawling tool that combines traditional web scraping techniques with Google Gemini AI for intelligent content analysis and filtering. Built with Python and designed for both simplicity and power.

## ✨ Features

- **🤖 AI-Powered Content Analysis**: Uses Google Gemini to analyze and filter content based on search queries
- **🔄 Exhaustive Crawling**: Deep crawling with configurable depth and breadth
- **⚡ Concurrent Processing**: Multi-threaded crawling for better performance
- **🛡️ Respectful Crawling**: Honors robots.txt and implements rate limiting
- **📊 Rich Output**: Beautiful console output with detailed analysis results
- **💾 Flexible Export**: Save results in JSON format
- **🎯 Smart Link Filtering**: AI-driven link prioritization based on relevance

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- UV package manager
- Google Gemini API key

### Installation

1. **Clone and setup the project:**
```bash
git clone <repository-url>
cd web_crawl
```

2. **Install dependencies with UV:**
```bash
uv sync
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Basic Usage

```bash
# Simple crawl of single URL
python crawl.py --url "https://example.com"

# Crawl multiple URLs
python crawl.py --url "https://example.com,https://another.com"

# AI-powered search for specific content
python crawl.py --url "https://example.com" --search "events"

# Exhaustive crawling with AI analysis
python crawl.py --url "https://example.com" --search "products" --exhaustive

# Save results to file
python crawl.py --url "https://example.com" --search "events" --output results.json
```

## 📖 Detailed Usage

### Command Line Arguments

| Argument | Short | Required | Description |
|----------|-------|----------|-------------|
| `--url` | `-u` | ✅ | Comma-separated URLs to crawl |
| `--search` | `-s` | ❌ | Search query for AI-powered filtering |
| `--exhaustive` | `-e` | ❌ | Enable deeper crawling |
| `--output` | `-o` | ❌ | Output file path for JSON results |
| `--depth` | | ❌ | Maximum crawl depth (default: 2) |
| `--max-pages` | | ❌ | Maximum pages to crawl (default: 50) |
| `--delay` | | ❌ | Delay between requests (default: 1.0s) |
| `--workers` | | ❌ | Concurrent workers (default: 5) |
| `--no-robots` | | ❌ | Ignore robots.txt |
| `--verbose` | `-v` | ❌ | Enable verbose logging |
| `--quiet` | `-q` | ❌ | Suppress non-essential output |

### Advanced Examples

```bash
# Deep crawling with custom parameters
python crawl.py --url "https://example.com" \
  --depth 3 \
  --max-pages 100 \
  --delay 0.5 \
  --workers 10

# Search for events with verbose output
python crawl.py --url "https://city.gov" \
  --search "community events calendar" \
  --exhaustive \
  --verbose \
  --output city_events.json

# Quiet mode for scripting
python crawl.py --url "https://example.com" --quiet > results.json
```

## 🏗️ Architecture

### Core Classes

#### 1. WebCrawler

The main crawling engine that handles URL fetching, content extraction, and coordination.

```python
from web_crawler import WebCrawler, CrawlConfig
from content_analyzer import ContentAnalyzer

# Initialize with custom configuration
config = CrawlConfig(
    max_depth=3,
    max_pages=100,
    delay=1.0,
    max_workers=5
)

analyzer = ContentAnalyzer()
crawler = WebCrawler(config=config, analyzer=analyzer)

# Crawl URLs
results = crawler.crawl_urls(
    start_urls=["https://example.com"],
    search_query="events",
    exhaustive=True
)
```

**Key Methods:**
- `crawl_urls()`: Main crawling method
- `fetch_url()`: Fetch single URL content
- `can_crawl_url()`: Check if URL is crawlable

#### 2. ContentAnalyzer

AI-powered content analysis using Google Gemini.

```python
from content_analyzer import ContentAnalyzer

analyzer = ContentAnalyzer()

# Analyze content relevance
match = analyzer.analyze_content_relevance(
    content="Page content here",
    search_query="events",
    url="https://example.com",
    title="Page Title"
)

print(f"Relevance Score: {match.relevance_score}")
print(f"Matched Content: {match.matched_content}")
```

**Key Methods:**
- `analyze_content_relevance()`: Score content relevance
- `find_relevant_links()`: Filter links by relevance
- `extract_structured_data()`: Extract structured information
- `summarize_crawl_results()`: Generate AI summary

#### 3. CrawlConfig

Configuration class for crawling parameters.

```python
from web_crawler import CrawlConfig

config = CrawlConfig(
    max_depth=2,           # Maximum crawl depth
    max_pages=50,          # Maximum pages to crawl
    delay=1.0,            # Delay between requests
    timeout=30,           # Request timeout
    max_workers=5,        # Concurrent workers
    respect_robots=True,  # Honor robots.txt
    max_content_length=1000000  # Max content length
)
```

### Utility Functions

The `utils.py` module provides essential utility functions:

```python
from utils import (
    is_valid_url,
    normalize_url,
    clean_text_content,
    should_crawl_url,
    RateLimiter,
    setup_logging
)

# URL validation
if is_valid_url("https://example.com"):
    print("Valid URL")

# Rate limiting
rate_limiter = RateLimiter(delay=1.0)
rate_limiter.wait_if_needed()

# Logging setup
logger = setup_logging("INFO", "crawler.log")
```

## 📊 Output Format

### Console Output

The crawler provides rich console output with:
- Progress indicators
- Crawl summary table
- AI analysis insights
- Content match results with relevance scores

### JSON Output

```json
{
  "crawl_summary": {
    "total_urls_processed": 25,
    "successful_crawls": 23,
    "failed_crawls": 2,
    "max_depth_reached": 2,
    "search_query": "events",
    "exhaustive_mode": true
  },
  "pages": [
    {
      "url": "https://example.com",
      "title": "Example Page",
      "content": "Page content...",
      "links_found": 15,
      "word_count": 500,
      "status_code": 200
    }
  ],
  "ai_analysis": {
    "total_pages": 23,
    "relevant_pages": 8,
    "key_themes": ["community events", "calendar", "activities"],
    "top_urls": [
      "https://example.com/events",
      "https://example.com/calendar"
    ],
    "insights": "Found 8 relevant pages about community events..."
  },
  "content_matches": [
    {
      "url": "https://example.com/events",
      "title": "Community Events",
      "relevance_score": 0.92,
      "matched_content": "Relevant content snippet...",
      "reasoning": "This page contains detailed event information..."
    }
  ]
}
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Crawler Configuration
DEFAULT_REQUEST_TIMEOUT=30
MAX_CONCURRENT_REQUESTS=5
DEFAULT_USER_AGENT=WebCrawler/1.0 (+https://github.com/your-repo)
RATE_LIMIT_DELAY=1.0

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=crawler.log

# Output Configuration
OUTPUT_FORMAT=json
MAX_CONTENT_LENGTH=1000000
```

### Custom Configuration

```python
# Custom crawler configuration
config = CrawlConfig(
    max_depth=5,              # Deep crawling
    max_pages=200,            # More pages
    delay=0.5,               # Faster crawling
    max_workers=10,          # More concurrency
    user_agent="MyBot/1.0",  # Custom user agent
    respect_robots=False,    # Ignore robots.txt
    timeout=60               # Longer timeout
)
```

## 🛡️ Best Practices

### Respectful Crawling

1. **Honor robots.txt**: The crawler respects robots.txt by default
2. **Rate limiting**: Built-in delays between requests
3. **User agent**: Identifies itself properly
4. **Content limits**: Limits content size to avoid memory issues

### Performance Optimization

1. **Concurrent workers**: Adjust based on target server capacity
2. **Request delays**: Balance speed with server load
3. **Content filtering**: Use AI to focus on relevant content
4. **Depth limits**: Prevent infinite crawling

### Error Handling

```python
try:
    results = crawler.crawl_urls(urls, search_query="events")
except Exception as e:
    logger.error(f"Crawling failed: {e}")
finally:
    crawler.close()  # Always clean up
```

## 🔧 Development

### Running Tests

```bash
# Install dev dependencies
uv sync --dev

# Run tests (when available)
pytest

# Run linting
flake8 .
black .
```

### Adding New Features

1. **Content Analyzers**: Extend `ContentAnalyzer` for domain-specific analysis
2. **Output Formats**: Add new output formats (CSV, XML, etc.)
3. **Data Extractors**: Create specialized extractors for specific sites
4. **Storage Backends**: Add database storage options

### Example: Custom Content Analyzer

```python
class EcommerceAnalyzer(ContentAnalyzer):
    """Specialized analyzer for e-commerce sites."""
    
    def extract_product_data(self, content: str) -> dict:
        """Extract product information from content."""
        prompt = f"""
        Extract product information from this content:
        {content}
        
        Return JSON with: name, price, description, availability
        """
        
        response = self.model.generate_content(prompt)
        return json.loads(response.text)
```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Errors**
   ```bash
   # Check if API key is set
   python -c "import os; print(os.getenv('GEMINI_API_KEY'))"
   ```

2. **Rate Limiting**
   ```bash
   # Increase delay between requests
   python crawl.py --url "example.com" --delay 2.0
   ```

3. **Memory Issues**
   ```bash
   # Reduce max pages and content length
   python crawl.py --url "example.com" --max-pages 20
   ```

4. **Robots.txt Blocking**
   ```bash
   # Check robots.txt manually or ignore it
   python crawl.py --url "example.com" --no-robots
   ```

### Debug Mode

```bash
# Enable verbose logging
python crawl.py --url "example.com" --verbose

# Check what's being crawled
cat crawler.log
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs with `--verbose` flag
3. Open an issue on GitHub

---

**Happy Crawling!** 🕷️✨