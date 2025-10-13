"""
Event Extractor - Single AI call for event information extraction.

Uses Google Gemini AI to extract event information from
consolidated crawl content in a single efficient API call.
Tracks token usage via TokenTracker.
"""

import os
import json
import logging
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger("web_crawler")


class GeminiModel(Enum):
    """Gemini model codes with token limits.
    
    Source: https://ai.google.dev/gemini-api/docs/models
    """
    # Gemini 2.5 models
    GEMINI_2_5_PRO = ("gemini-2.5-pro", 1048576, 65536)
    GEMINI_2_5_PRO_TTS = ("gemini-2.5-pro-preview-tts", 8000, 16000)
    GEMINI_2_5_FLASH = ("gemini-2.5-flash", 1048576, 65536)
    GEMINI_2_5_FLASH_PREVIEW = ("gemini-2.5-flash-preview-09-2025", 1048576, 65536)
    GEMINI_2_5_FLASH_IMAGE = ("gemini-2.5-flash-image", 32768, 32768)
    GEMINI_2_5_FLASH_LITE = ("gemini-2.5-flash-lite-preview-09-2025", 1048576, 65536)
    
    # Gemini 2.0 models
    GEMINI_2_0_FLASH = ("gemini-2.0-flash", 1048576, 8192)
    
    def __init__(self, model_code: str, input_limit: int, output_limit: int):
        self.model_code = model_code
        self.input_limit = input_limit
        self.output_limit = output_limit
    
    @classmethod
    def from_code(cls, code: str) -> 'GeminiModel':
        """Get enum from model code string."""
        for model in cls:
            if model.model_code == code:
                return model
        raise ValueError(f"Unknown model code: {code}")


@dataclass
class TokenUsage:
    """Token usage for a single request."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class TokenTracker:
    """Tracks token usage across Gemini API calls."""
    
    def __init__(self, model: GeminiModel):
        """Initialize tracker for a specific model.
        
        Args:
            model: GeminiModel enum value
        """
        self.model = model
        self.requests: List[TokenUsage] = []
    
    def track_request(self, prompt_tokens: int, completion_tokens: int):
        """Record token usage for a request.
        
        Args:
            prompt_tokens: Input token count
            completion_tokens: Output token count
        """
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        self.requests.append(usage)
        logger.debug(f"Tracked: {prompt_tokens} prompt + {completion_tokens} completion = {usage.total_tokens} total")
    
    def report(self) -> Dict[str, Any]:
        """Generate token usage summary.
        
        Returns:
            Dict with usage statistics
        """
        if not self.requests:
            return {
                "model": self.model.model_code,
                "total_requests": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "model_limits": {
                    "input_limit": self.model.input_limit,
                    "output_limit": self.model.output_limit
                }
            }
        
        total_prompt = sum(r.prompt_tokens for r in self.requests)
        total_completion = sum(r.completion_tokens for r in self.requests)
        total = sum(r.total_tokens for r in self.requests)
        
        report = {
            "model": self.model.model_code,
            "total_requests": len(self.requests),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total,
            "avg_prompt_tokens": total_prompt // len(self.requests),
            "avg_completion_tokens": total_completion // len(self.requests),
            "model_limits": {
                "input_limit": self.model.input_limit,
                "output_limit": self.model.output_limit
            },
            "utilization": {
                "max_input_used_pct": round(max(r.prompt_tokens for r in self.requests) / self.model.input_limit * 100, 2),
                "max_output_used_pct": round(max(r.completion_tokens for r in self.requests) / self.model.output_limit * 100, 2)
            }
        }
        return json.dumps(report, indent=2)


class EventExtractor(TokenTracker):
    """Extract event information using Google Gemini AI with token tracking."""
    
    def __init__(self, api_key: Optional[str] = None, model: GeminiModel = GeminiModel.GEMINI_2_5_FLASH_LITE):
        """Initialize event extractor.
        
        Args:
            api_key: Google Gemini API key (defaults to env var)
            model: GeminiModel to use (default: 2.5 Flash Lite)
        """
        # Initialize TokenTracker
        super().__init__(model)
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or provided")
        
        # Initialize client with new SDK
        self.client = genai.Client(api_key=self.api_key)
        logger.info(f"EventExtractor initialized with {model.model_code}")
    
    def extract_events(
        self,
        base_url: str,
        content_by_url: Dict[str, str],
        routes: List[str]
    ) -> Dict[str, Any]:
        """Extract event information from all crawled content in a single AI call.
        
        Consolidates all content and makes ONE API call to extract
        relevant event information with 0 thinking budget for speed.
        
        Args:
            base_url: The base URL that was crawled
            content_by_url: Dictionary mapping URLs to their content
            routes: List of route URLs (excluding base URL)
            
        Returns:
            Dictionary with structured event information including token report
        """
        logger.info(f"Extracting events from {len(content_by_url)} pages")
        
        # Consolidate all content with URL markers
        consolidated_content = self._consolidate_content(base_url, content_by_url, routes)
        logger.info(f"Consolidated content length for {base_url}: {len(consolidated_content)} characters")
        
        # Build the extraction prompt
        prompt = self._build_extraction_prompt(base_url, consolidated_content, routes)
        logger.info(f"Built extraction prompt for {base_url}")
        
        # Make single AI call with 0 thinking budget
        try:
            result = self._call_gemini(prompt)
            logger.info("Successfully extracted event information")
            
            # Add token usage report
            result["token_usage"] = self.report()

            logger.info(f"Full Result for {base_url}: \n{json.dumps(result, indent=2)}")
            
            return result
        except Exception as e:
            logger.error(f"Error extracting events: {e}")
            return {
                "base_url": base_url,
                "routes": routes,
                "purpose": "Error during extraction",
                "events_found": [],
                "error": str(e),
                "token_usage": self.report()
            }
    
    def _consolidate_content(
        self,
        base_url: str,
        content_by_url: Dict[str, str],
        routes: List[str]
    ) -> str:
        """Consolidate all content into a single text block with URL markers.
        
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
        """Build the extraction prompt for Gemini.
        
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
        """Call Gemini API and track token usage.
        
        Uses 0 thinking budget for fast response.
        
        Args:
            prompt: Extraction prompt
            
        Returns:
            Parsed JSON response
        """
        try:
            # Count input tokens
            token_count = self.client.models.count_tokens(
                model=self.model.model_code,
                contents=prompt,
            )
            prompt_tokens = token_count.total_tokens
            logger.info(f"Input tokens: {prompt_tokens}")
            
            # Generate content with 0 thinking budget
            response = self.client.models.generate_content(
                model=self.model.model_code,
                contents=prompt,
                config=types.GenerateContentConfig(
                    # thinking_config=types.ThinkingConfig(
                    #     thinking_budget=0  # No thinking for speed
                    # ),
                    response_modalities=["TEXT"],
                )
            )
            
            # Extract response text
            response_text = response.text
            
            # Count output tokens
            completion_count = self.client.models.count_tokens(
                model=self.model.model_code,
                contents=response_text,
            )
            completion_tokens = completion_count.total_tokens
            logger.info(f"Output tokens: {completion_tokens}")
            
            # Track usage
            self.track_request(prompt_tokens, completion_tokens)
            
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
