Here's a comprehensive but concise changelog based on the provided Git changes:

---

### New Features

*   **AI-Powered Event Extraction**: Introduced a new `EventExtractor` component leveraging the Google Gemini API for efficient, single-call extraction of event information from crawled content.
*   **AI Token Usage Tracking**: Implemented `TokenTracker` to monitor and report token consumption for Gemini API calls, providing insights into AI resource usage.
*   **Configurable Crawler Parameters**: Added extensive configuration options via `CrawlerConfig` for `max_depth`, `max_pages`, `request_delay`, `timeout`, `user_agent`, `robots.txt` adherence, and `max_content_characters`.
*   **Event-Focused Link Prioritization**: Enhanced link extraction logic to prioritize URLs containing event-related keywords (e.g., "event", "calendar", "activity") for more relevant crawling.
*   **Centralized Logging**: Implemented a standardized logging setup across the crawler for improved visibility and debugging.
*   **CLI Interface**: Provided a command-line interface (`crawl.py`) for easy execution and configuration of the web crawler.

### Performance Improvements

*   **Aggressive Content Filtering**: Implemented more aggressive HTML element removal (e.g., `script`, `style`, `nav`, `header`, `footer`, `aside`, `form`) and text cleaning to reduce content size and optimize AI token usage.
*   **Rate Limiting**: Integrated a `RateLimiter` to introduce delays between requests, preventing server overload and improving crawl etiquette.
*   **Optimized AI Call Strategy**: Designed the event extraction to use a single, consolidated AI call with a "0 thinking budget" for faster processing.

### Breaking Changes

*   **Legacy AI SDK Removal**: All previous legacy AI SDK code has been removed, replaced entirely by the new Google GenAI SDK integration.

### Other Changes

*   **New Project Structure**: Established a clear, modular project structure with dedicated files for crawling logic (`crawl.py`), AI extraction (`event_extractor.py`), and utility functions (`utils.py`).
*   **Comprehensive Documentation**: Added `README.md` detailing the project's architecture, flow, components, and usage, along with `IMPROVE_CRAWL.md` outlining current limitations and a roadmap for future enhancements (e.g., Playwright integration for dynamic content, Cloudflare bypass).
*   **Dependency Management**: Introduced `pyproject.toml` for modern dependency management and project metadata, including new dependencies for `google-genai`, `pydantic`, `rich`, `aiohttp`, and `markdownify`.
*   **Development Tooling**: Added optional development dependencies for `pytest`, `black`, `flake8`, and `mypy` to ensure code quality and consistency.
*   **Environment Configuration**: Provided a `.env.example` file for easy setup of environment variables, including the `GEMINI_API_KEY`.
*   **Python Version Specification**: Explicitly set Python version to 3.13.

---