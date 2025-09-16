import asyncio
import aiohttp
import json
import re
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import logging
from bs4 import BeautifulSoup
import google.generativeai as genai
from geopy.geocoders import Nominatim
import time

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Event:
    title: str
    date: str
    time: str
    location: str
    address: str
    url: str
    description: str
    source_domain: str

@dataclass
class LocationInfo:
    city: str
    state: str
    county: str
    zip_code: str

class LocationResolver:
    """Resolve various location inputs to standardized location info"""

    def __init__(self):
        self.geolocator = Nominatim(user_agent="event_scraper")

    def resolve_location(self, location_input: str) -> LocationInfo:
        """Convert zip code, city name, etc. to standardized location info"""
        try:
            location = self.geolocator.geocode(location_input, addressdetails=True)
            if not location:
                raise ValueError(f"Could not resolve location: {location_input}")

            address = location.raw.get('address', {})

            return LocationInfo(
                city=address.get('city') or address.get('town') or address.get('village', ''),
                state=address.get('state', ''),
                county=address.get('county', ''),
                zip_code=address.get('postcode', '')
            )
        except Exception as e:
            logger.error(f"Error resolving location {location_input}: {e}")
            raise

class SourceDiscoverer:
    """AI-powered discovery of event sources for a given location"""

    def __init__(self, genai_api_key: str):
        genai.configure(api_key=genai_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def discover_sources(self, location: LocationInfo, interests: List[str]) -> List[str]:
        """Use AI to generate potential event source URLs"""

        # Create search queries for web scraping
        search_queries = self._generate_search_queries(location, interests)

        # Use AI to predict common URL patterns and suggest sources
        ai_suggested_sources = await self._ai_suggest_sources(location, interests)

        # Combine web search results with AI suggestions
        all_sources = []

        # Search for sources using the queries
        async with aiohttp.ClientSession() as session:
            for query in search_queries:
                sources = await self._web_search_sources(session, query)
                all_sources.extend(sources)

        # Add AI suggested sources
        all_sources.extend(ai_suggested_sources)

        # Deduplicate and validate URLs
        return list(set([url for url in all_sources if self._is_valid_url(url)]))

    def _generate_search_queries(self, location: LocationInfo, interests: List[str]) -> List[str]:
        """Generate search queries for finding event sources"""
        base_queries = [
            f"{location.city} {location.state} events calendar",
            f"{location.city} parks recreation events",
            f"{location.county} county events",
            f"{location.city} municipal events",
            f"{location.city} farmers market",
            f"{location.city} community events",
            f"{location.city} city hall events"
        ]

        # Add interest-specific queries
        for interest in interests:
            base_queries.extend([
                f"{location.city} {interest} events",
                f"{location.city} {interest} calendar"
            ])

        return base_queries

    async def _ai_suggest_sources(self, location: LocationInfo, interests: List[str]) -> List[str]:
        """Use AI to suggest likely event source URLs"""

        prompt = f"""
        Given the location: {location.city}, {location.state} (County: {location.county})
        And user interests: {', '.join(interests)}

        Suggest 10-15 likely URLs where local events might be posted. Focus on:
        1. Official city/municipal websites
        2. Parks & Recreation departments
        3. County government sites
        4. Local chambers of commerce
        5. Community centers
        6. Libraries
        7. Farmers markets
        8. Local event listing sites

        Return only the URLs, one per line. Use realistic URL patterns like:
        - cityof[cityname].com/events
        - [cityname].gov/events
        - [cityname]parksandrec.org/events
        - [county]county.gov/events

        Make the URLs realistic for {location.city}, {location.state}.
        """

        try:
            response = await asyncio.to_thread(
                self.model.generate_content, prompt
            )

            # Extract URLs from AI response
            urls = []
            for line in response.text.split('\n'):
                line = line.strip()
                if line and ('http' in line or '.com' in line or '.org' in line or '.gov' in line):
                    # Clean up the line to extract just the URL
                    url_match = re.search(r'https?://[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?', line)
                    if url_match:
                        url = url_match.group()
                        if not url.startswith('http'):
                            url = 'https://' + url
                        urls.append(url)

            return urls[:15]  # Limit to 15 suggestions

        except Exception as e:
            logger.error(f"Error getting AI suggestions: {e}")
            return []

    async def _web_search_sources(self, session: aiohttp.ClientSession, query: str) -> List[str]:
        """Search for event sources (simplified - in production use proper search API)"""
        # This is a placeholder - in production, integrate with Google Search API,
        # Bing API, or use a service like SerpAPI

        # For now, generate some common patterns based on the query
        sources = []

        # Extract city from query
        words = query.lower().split()
        if len(words) >= 2:
            city = words[0]
            sources.extend([
                f"https://www.cityof{city}.com/events",
                f"https://{city}.gov/events",
                f"https://{city}parks.org/events",
                f"https://www.{city}chamber.com/events"
            ])

        return sources

    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

class EventScraper:
    """Scrape events from discovered sources"""

    def __init__(self, genai_api_key: str):
        genai.configure(api_key=genai_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def scrape_events(self, sources: List[str], interests: List[str]) -> List[Event]:
        """Scrape events from all sources"""
        all_events = []

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; EventBot/1.0)'}
        ) as session:

            # Process sources concurrently but with rate limiting
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

            tasks = [
                self._scrape_single_source(session, semaphore, source, interests)
                for source in sources
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_events.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Error scraping source: {result}")

        # Deduplicate events
        return self._deduplicate_events(all_events)

    async def _scrape_single_source(self, session: aiohttp.ClientSession,
                                   semaphore: asyncio.Semaphore,
                                   source_url: str,
                                   interests: List[str]) -> List[Event]:
        """Scrape events from a single source"""
        async with semaphore:
            try:
                # Add delay to be respectful
                await asyncio.sleep(1)

                async with session.get(source_url) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {source_url}: {response.status}")
                        return []

                    html_content = await response.text()

                # Use AI to extract events from HTML
                events = await self._ai_extract_events(html_content, source_url, interests)
                return events

            except Exception as e:
                logger.error(f"Error scraping {source_url}: {e}")
                return []

    async def _ai_extract_events(self, html_content: str, source_url: str, interests: List[str]) -> List[Event]:
        """Use AI to extract event information from HTML"""

        # Clean HTML with BeautifulSoup first
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text_content = soup.get_text()

        # Limit content size for AI processing
        if len(text_content) > 8000:
            text_content = text_content[:8000] + "..."

        domain = urlparse(source_url).netloc

        prompt = f"""
        Extract event information from this webpage content. Focus on events that match these interests: {', '.join(interests)}

        Webpage URL: {source_url}
        Content:
        {text_content}

        Extract events and return them in this exact JSON format:
        [
            {{
                "title": "Event Title",
                "date": "YYYY-MM-DD",
                "time": "HH:MM AM/PM",
                "location": "Venue Name",
                "address": "Full Address",
                "url": "Event URL or source URL",
                "description": "Event description"
            }}
        ]

        Requirements:
        - Only extract actual events (not general information)
        - Date must be in YYYY-MM-DD format
        - Time in 12-hour format with AM/PM
        - Include full address if available
        - Description should be 1-2 sentences max
        - If event URL not available, use the source URL
        - Only return valid JSON array

        If no events found, return: []
        """

        try:
            response = await asyncio.to_thread(
                self.model.generate_content, prompt
            )

            # Extract JSON from response
            response_text = response.text.strip()

            # Try to find JSON in the response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1

            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                events_data = json.loads(json_str)

                events = []
                for event_data in events_data:
                    try:
                        event = Event(
                            title=event_data.get('title', ''),
                            date=event_data.get('date', ''),
                            time=event_data.get('time', ''),
                            location=event_data.get('location', ''),
                            address=event_data.get('address', ''),
                            url=event_data.get('url', source_url),
                            description=event_data.get('description', ''),
                            source_domain=domain
                        )
                        events.append(event)
                    except Exception as e:
                        logger.error(f"Error creating event object: {e}")
                        continue

                return events

            return []

        except Exception as e:
            logger.error(f"Error extracting events with AI: {e}")
            return []

    def _deduplicate_events(self, events: List[Event]) -> List[Event]:
        """Remove duplicate events based on title, date, and location"""
        seen = set()
        unique_events = []

        for event in events:
            # Create a key for deduplication
            key = (
                event.title.lower().strip(),
                event.date,
                event.location.lower().strip()
            )

            if key not in seen:
                seen.add(key)
                unique_events.append(event)

        return unique_events

class LocalEventsFinder:
    """Main class that orchestrates the event finding process"""

    def __init__(self, genai_api_key: str):
        self.location_resolver = LocationResolver()
        self.source_discoverer = SourceDiscoverer(genai_api_key)
        self.event_scraper = EventScraper(genai_api_key)

    async def find_events(self, location_input: str, interests: List[str]) -> Dict:
        """Main method to find events"""
        try:
            # Step 1: Resolve location
            logger.info(f"Resolving location: {location_input}")
            location = self.location_resolver.resolve_location(location_input)
            logger.info(f"Resolved to: {location.city}, {location.state}")

            # Step 2: Discover sources
            logger.info("Discovering event sources...")
            sources = await self.source_discoverer.discover_sources(location, interests)
            logger.info(f"Found {len(sources)} potential sources")

            # Step 3: Scrape events
            logger.info("Scraping events from sources...")
            events = await self.event_scraper.scrape_events(sources, interests)
            logger.info(f"Found {len(events)} events")

            # Step 4: Format output
            result = {
                "location": asdict(location),
                "interests": interests,
                "sources": sources,
                "events": [asdict(event) for event in events],
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "total_sources": len(sources),
                    "total_events": len(events)
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error in find_events: {e}")
            raise

# Example usage
async def main():
    """Example usage of the LocalEventsFinder"""

    # Initialize with your Google AI API key
    GENAI_API_KEY = os.getenv("GEMINI_API_KEY")

    finder = LocalEventsFinder(GENAI_API_KEY)

    try:
        result = await finder.find_events(
            location_input="95126 San Jose, CA",
            interests=["farmers market"]
        )

        # Save results to JSON file
        with open("events_output.json", "w") as f:
            json.dump(result, f, indent=2)

        print(f"Found {result['metadata']['total_events']} events from {result['metadata']['total_sources']} sources")
        print("\nSample events:")
        for event in result['events'][:3]:
            print(f"- {event['title']} on {event['date']} at {event['location']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())