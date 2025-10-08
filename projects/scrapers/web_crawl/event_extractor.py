"""
Event Extractor - Single AI call for event information extraction.

This module uses Google Gemini AI to extract event information from
consolidated crawl content in a single efficient API call.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError:
    import google.generativeai as genai
    types = None

load_dotenv()

logger = logging.getLogger("web_crawler")


class EventExtractor:
    """Extract event information using Google Gemini AI with a single call."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the event extractor.
        
        Args:
            api_key: Google Gemini API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or provided")
        
        # Configure Gemini with new SDK
        try:
            # Try new SDK first
            self.client = genai.Client(api_key=self.api_key)
            self.use_new_sdk = True
            logger.info("EventExtractor initialized with new Gemini SDK")
        except:
            # Fall back to old SDK
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
            self.use_new_sdk = False
            logger.info("EventExtractor initialized with legacy Gemini SDK")
    
    def extract_events(
        self,
        base_url: str,
        content_by_url: Dict[str, str],
        routes: List[str]
    ) -> Dict[str, Any]:
        """
        Extract event information from all crawled content in a single AI call.
        
        This method consolidates all content and makes ONE API call to extract
        relevant event information with 0 thinking budget for speed.
        
        Args:
            base_url: The base URL that was crawled
            content_by_url: Dictionary mapping URLs to their content
            routes: List of route URLs (excluding base URL)
            
        Returns:
            Dictionary with structured event information
        """
        logger.info(f"Extracting events from {len(content_by_url)} pages")
        
        # Consolidate all content with URL markers
        consolidated_content = self._consolidate_content(base_url, content_by_url, routes)
        
        # Build the extraction prompt
        prompt = self._build_extraction_prompt(base_url, consolidated_content, routes)
        
        # Make single AI call with 0 thinking budget
        try:
            result = self._call_gemini(prompt)
            logger.info("Successfully extracted event information")
            return result
        except Exception as e:
            logger.error(f"Error extracting events: {e}")
            return {
                "base_url": base_url,
                "routes": routes,
                "purpose": "Error during extraction",
                "events_found": [],
                "error": str(e)
            }
    
    def _consolidate_content(
        self,
        base_url: str,
        content_by_url: Dict[str, str],
        routes: List[str]
    ) -> str:
        """
        Consolidate all content into a single text block with URL markers.
        
        Args:
            base_url: Base URL
            content_by_url: Content mapped by URL
            routes: List of routes
            
        Returns:
            Consolidated content string
        """
        consolidated = []
        
        # Add base URL content first
        if base_url in content_by_url:
            base_content = content_by_url[base_url]
            # Limit content length per page
            if len(base_content) > 20000:
                base_content = base_content[:20000]
            consolidated.append(f"=== BASE URL: {base_url} ===\n{base_content}\n")
        
        # Add route contents
        for route in routes[:30]:  # Limit to 30 routes to avoid token limits
            if route in content_by_url:
                route_content = content_by_url[route]
                # Limit content length per page
                if len(route_content) > 15000:
                    route_content = route_content[:15000]
                consolidated.append(f"=== ROUTE: {route} ===\n{route_content}\n")
        
        return "\n".join(consolidated)
    
    def _build_extraction_prompt(
        self,
        base_url: str,
        consolidated_content: str,
        routes: List[str]
    ) -> str:
        """
        Build the extraction prompt for Gemini.
        
        Args:
            base_url: Base URL
            consolidated_content: All consolidated page content
            routes: List of routes
            
        Returns:
            Prompt string
        """
        prompt = f"""You are an event information extraction specialist. Your task is to analyze website content and extract ONLY pages and information related to events, calendars, and activities that have specific dates, times, and locations.

BASE URL: {base_url}

CONTENT FROM ALL PAGES:
{consolidated_content}

INSTRUCTIONS:
1. Identify which routes/pages contain event, calendar, or activity information
2. Filter OUT routes that are NOT related to events (e.g., general info, contact pages, about pages)
3. Extract ONLY routes that provide:
   - Events with dates and times
   - Calendars or schedules
   - Activities with registration or attendance information
   - Programs or classes with specific meeting times and locations

4. For each event found, extract:
   - date (in YYYY-MM-DD format, or null if not found)
   - start_time (in HH:MM format 24-hour, or null if not found)
   - end_time (in HH:MM format 24-hour, or null if not found)  
   - address (full address as string, or null if not found)
   - title (event name/title)
   - description (brief description)

5. Determine the overall purpose of this website in relation to events

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "routes": [
    "list of URLs that contain event/calendar/activity information",
    "DO NOT include URLs without event information"
  ],
  "purpose": "Brief description of what this website provides in terms of events/activities",
  "events_found": [
    {{
      "title": "Event Name",
      "description": "Brief description",
      "date": "YYYY-MM-DD or null",
      "start_time": "HH:MM or null",
      "end_time": "HH:MM or null",
      "address": "Full address or null",
      "source_url": "URL where this event was found"
    }}
  ]
}}

BE STRICT: Only include routes and events that have specific date/time/location information for activities or events.
If no events are found, return empty lists.
Respond with ONLY the JSON, no additional text."""
        
        return prompt
    
    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """
        Call Gemini API with the extraction prompt.
        
        Uses 0 thinking budget for fast response.
        
        Args:
            prompt: Extraction prompt
            
        Returns:
            Parsed JSON response
        """
        try:
            if self.use_new_sdk:
                # New SDK approach with 0 thinking budget
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash-thinking-exp',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=0  # No thinking for speed
                        ),
                        response_modalities=["TEXT"],
                    )
                )
                response_text = response.text
            else:
                # Legacy SDK approach
                generation_config = {
                    "temperature": 0.1,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                response_text = response.text
            
            # Clean response text (remove markdown code blocks if present)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            # Return minimal valid structure
            return {
                "routes": [],
                "purpose": "Failed to parse AI response",
                "events_found": []
            }
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise
