# Event Discovery Web Crawler (architecture-first)

Purpose: discover events/activities from a single site using a two-phase flow. Focus on minimal AI calls, deterministic crawl, structured JSON output.

Entry point: crawl.py (CLI)

## Flow (high level)

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#0ea5e9',
    'primaryTextColor': '#e2e8f0',
    'primaryBorderColor': '#38bdf8',
    'lineColor': '#94a3b8',
    'secondaryColor': '#1f2937',
    'tertiaryColor': '#334155'
  }
}}%%
flowchart TD
  accTitle: Event discovery pipeline
  accDescr: CLI orchestrates Phase 1 crawl and Phase 2 single-call extraction to JSON

  subgraph P1["Phase 1 • Crawl"]
    direction TB
CLI["crawl.py CLI"] --> CCFG["CrawlerConfig"]
CCFG --> CRAWL[["Crawler.crawl(url)"]]
    CRAWL --> RSLT{{"crawl_results"}}
  end

  subgraph P2["Phase 2 • Extract"]
    direction TB
    EX[["EventExtractor.extract_events"]]
    EX --> JSON[("output.json")]
  end

  RSLT --> EX

  classDef cli fill:#0b1020,stroke:#38bdf8,stroke-width:2px,color:#e2e8f0;
  classDef config fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#ecfeff;
  classDef crawl fill:#0f172a,stroke:#60a5fa,stroke-width:2px,color:#eaf2ff;
  classDef result fill:#111827,stroke:#94a3b8,stroke-dasharray: 5 3,stroke-width:2px,color:#f8fafc;
  classDef extract fill:#7c2d12,stroke:#fb923c,stroke-width:2px,color:#fff7ed;
  classDef output fill:#1f2937,stroke:#f59e0b,stroke-width:2px,color:#fffbeb;

  class CLI cli
  class CCFG config
  class CRAWL crawl
  class RSLT result
  class EX extract
  class JSON output

  linkStyle default stroke:#64748b,stroke-width:1.5px;color:#94a3b8
```

## Components used by crawl.py

- crawl.py (embedded Crawler/CrawlerConfig)
- CrawlerConfig: max_depth, max_pages, delay, timeout, user_agent, respect_robots, max_content_chars
- Crawler
    - crawl(start_url): breadth-first crawl within domain; prioritizes event-like links; returns
      - base_url
      - base_content
      - routes (list of URLs)
      - content_by_url {url -> cleaned text}
      - total_pages, depth_reached
- _fetch_page(url, base_url): request + parse + clean + link extract
- event_extractor.py
  - EventExtractor
    - extract_events(base_url, content_by_url, routes): single Gemini call
    - _consolidate_content(): concatenate per-URL text with limits
    - _build_extraction_prompt(): strict JSON schema for routes/purpose/events
    - _call_gemini(): new SDK if available, else legacy
- utils.py (subset used)
  - is_valid_url, normalize_url, should_crawl_url
  - clean_text_content, aggressive_content_filter
- RateLimiter

Notes
- ignore console/formatting and logging utilities in this doc

## Data contracts

crawl_results (from Crawler.crawl)
- base_url: str
- base_content: str
- routes: list[str]
- content_by_url: dict[str,str]
- total_pages: int
- depth_reached: int

event_results (from EventExtractor.extract_events)
- base_url: str
- routes: list[str] (event-related only)
- purpose: str
- events_found: list[{title, description, date, start_time, end_time, address, source_url}]

Output file
- JSON keyed by base_url: { base_url: { routes, purpose, events_found } }

## CLI (minimal)

```bash
python crawl.py --url "https://example.com" --depth 2 --max-pages 50 --output output.json
# optional: --delay 1.0 --verbose/--quiet
```

## Programmatic usage (optional)

```python
from crawl import Crawler, CrawlerConfig
from event_extractor import EventExtractor

cfg = CrawlerConfig(max_depth=2, max_pages=50, delay=1.0)
crawler = Crawler(cfg)
res = crawler.crawl("https://example.com")

extractor = EventExtractor()
events = extractor.extract_events(
    base_url=res["base_url"],
    content_by_url=res["content_by_url"],
    routes=res["routes"],
)

# Save structure mirrors CLI output
out = { events.get("base_url", "unknown"): {
    "routes": events.get("routes", []),
    "purpose": events.get("purpose", ""),
    "events_found": events.get("events_found", []),
}}
```

## Mermaid (detailed interactions)

```mermaid
sequenceDiagram
  autonumber
  participant U as User
  participant CLI as crawl.py
participant SC as Crawler
  participant UT as utils
  participant EE as EventExtractor

  Note over CLI,SC: Phase 1 • Crawl
  U->>CLI: args(url, depth, max_pages, delay, no_robots)
CLI->>SC: CrawlerConfig(...)
  CLI->>SC: crawl(url)
  rect rgba(33, 150, 243, .08)
    loop BFS by depth
      SC->>UT: should_crawl_url / normalize_url
      SC->>UT: clean_text_content / aggressive_content_filter
      SC-->>CLI: PageContent(content, links)
    end
  end
  SC-->>CLI: {base_url, routes, content_by_url}

  Note over CLI,EE: Phase 2 • Extract
  rect rgba(245, 158, 11, .10)
    CLI->>EE: extract_events(base_url, content_by_url, routes)
    EE->>EE: _consolidate_content()
    EE->>EE: _build_extraction_prompt()
    EE->>EE: _call_gemini()
    EE-->>CLI: {routes, purpose, events_found}
  end

  CLI-->>U: write output.json
```

## File map

Used by crawl.py
- crawl.py: CLI + embedded Crawler/CrawlerConfig (crawl + save)
- event_extractor.py: single-call event extraction
- utils.py: URL/text helpers, rate limiting

## #ICONS

- [>] start/info
- [+] success
- [-] error
- [!] warning
- [i] info
- [*] event marker


