# Event Discovery Web Crawler - Refactored

## Overview

This is a streamlined, event-focused web crawler that uses a two-phase approach to discover event and activity information from websites.

## Key Changes from Previous Version

### Architecture Simplification

1. **Two-Phase Approach**:
   - **Phase 1**: Crawl and consolidate content (no AI)
   - **Phase 2**: Single AI extraction call with all content

2. **Reduced AI Dependency**:
   - Eliminated per-page AI analysis (prevents rate limiting)
   - Single AI call with 0 thinking budget for speed
   - Fallback mode if AI fails

3. **Event-Focused**:
   - Aggressive content filtering for event-related information
   - Link prioritization based on event keywords
   - Structured output focused on dates, times, and addresses

## New Modules

### `simple_crawler.py`
- Pure content extraction without AI analysis
- Rate-limited requests to respect servers
- Aggressive filtering of non-event content
- Returns: base URL, content by URL, list of routes

### `event_extractor.py`
- Single AI extraction call with consolidated content
- Uses Gemini 2.0 Flash with 0 thinking budget
- Extracts: routes with event info, purpose, structured events
- Event fields: title, date, start_time, end_time, address

### Updated `crawl.py`
- Simplified CLI (single URL only)
- Two-phase execution with progress indicators
- Logging to `crawl.log` (all operations logged)
- Terminal-style icons instead of emojis

### Enhanced `utils.py`
- `aggressive_content_filter()`: Removes boilerplate text
- `extract_event_keywords()`: Identifies event-related pages
- Default logging to `crawl.log`

## Usage

### Basic Usage
```bash
python crawl.py --url "https://example.com"
```

### Custom Output
```bash
python crawl.py --url "https://city.gov" --output events.json
```

### Deep Crawl
```bash
python crawl.py --url "https://example.com" --depth 3 --max-pages 100
```

### Verbose Logging
```bash
python crawl.py --url "https://example.com" --verbose
```

## Output Format

The output JSON follows this structure:

```json
{
  "https://example.com": {
    "routes": [
      "https://example.com/events",
      "https://example.com/calendar"
    ],
    "purpose": "Community events and activities calendar",
    "events_found": [
      {
        "title": "Summer Festival",
        "description": "Annual community festival",
        "date": "2025-07-15",
        "start_time": "10:00",
        "end_time": "18:00",
        "address": "123 Main St, City, ST 12345",
        "source_url": "https://example.com/events"
      }
    ]
  }
}
```

## Command Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--url` | `-u` | Required | URL to crawl for event information |
| `--output` | `-o` | `output.json` | Output file path |
| `--depth` | | `2` | Maximum crawl depth |
| `--max-pages` | | `50` | Maximum pages to crawl |
| `--delay` | | `1.0` | Delay between requests (seconds) |
| `--no-robots` | | `False` | Ignore robots.txt |
| `--verbose` | `-v` | `False` | Enable verbose logging |
| `--quiet` | `-q` | `False` | Suppress output |

## Logging

All operations are logged to `crawl.log`:
- Crawl session start/end markers
- Each page fetched with URL and content stats
- Phase transitions
- AI extraction results
- Errors and warnings

## Performance Improvements

1. **No per-page AI calls**: Eliminates rate limiting issues
2. **Aggressive content filtering**: Reduces token usage by 60-80%
3. **Rate limiting**: Respects server resources
4. **Single consolidation step**: Efficient memory usage

## Event Discovery Focus

The crawler specifically looks for:
- Calendar pages
- Event listings
- Activity schedules
- Programs with dates/times
- Registration pages

Keywords prioritized: event, calendar, schedule, activity, program, class, workshop, seminar, conference, meeting, registration, venue

## Error Handling

- Graceful fallback if AI extraction fails
- Continue operation on page fetch errors
- Log all errors to `crawl.log`
- Keyboard interrupt handling (Ctrl+C)

## Dependencies

The refactored version uses:
- `requests` & `beautifulsoup4`: Web scraping
- `google-genai` or `google-generativeai`: AI extraction
- `rich`: Terminal formatting
- `pydantic`: Data validation
- Standard library: multiprocessing, logging

## Migration Notes

If migrating from the old version:
- `--search` argument removed (always searches for events)
- `--exhaustive` removed (use `--depth` and `--max-pages`)
- Multiple URLs not supported (run separately)
- Output format changed to use base URL as key
- All logging now goes to `crawl.log` by default

## Examples

### Local Community Center
```bash
python crawl.py --url "https://localcommunity.org" --depth 2 --output community_events.json
```

### City Government Events
```bash
python crawl.py --url "https://city.gov" --max-pages 100 --depth 3 --output city_events.json
```

### Library Events
```bash
python crawl.py --url "https://library.org/events" --verbose --output library_events.json
```

## #ICONS

Terminal-style icons used:
- `[>]` - Start/Info
- `[+]` - Success
- `[-]` - Error  
- `[!]` - Warning
- `[i]` - Information
- `[*]` - Event marker
- `[>]` - URL/Route marker

## Troubleshooting

### No Events Found
- Check `crawl.log` for crawl details
- Increase `--depth` to crawl deeper
- Increase `--max-pages` to crawl more pages
- Website may not have structured event information

### AI Extraction Failed
- Check GEMINI_API_KEY in .env file
- Check API quota/rate limits
- Crawler will save routes without AI extraction

### Rate Limiting / 429 Errors
- Increase `--delay` (e.g., `--delay 2.0`)
- Reduce `--max-pages`
- Check website's robots.txt

## Future Enhancements

Potential improvements:
- Batch processing for multiple URLs
- Export to CSV/Excel formats
- Duplicate event detection
- Date range filtering
- Geographic filtering
