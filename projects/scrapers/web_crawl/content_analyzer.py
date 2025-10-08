"""
Content Analyzer using Google Gemini AI for intelligent web scraping.

This module provides AI-powered content analysis capabilities using Google's Gemini
model to extract relevant information from scraped web content.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

logger = logging.getLogger("web_crawler.content_analyzer")


class ContentMatch(BaseModel):
    """Model for content match results."""
    url: str = Field(..., description="URL of the matched content")
    title: str = Field(..., description="Title of the page")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    matched_content: str = Field(..., description="Relevant content snippet")
    reasoning: str = Field(..., description="AI reasoning for the match")


class ContentAnalyzer:
    """AI-powered content analyzer using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the content analyzer.

        Args:
            api_key: Google Gemini API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or provided")

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

        logger.info("ContentAnalyzer initialized with Gemini model")

    def analyze_content_relevance(
        self,
        content: str,
        search_query: str,
        url: str = "",
        title: str = ""
    ) -> ContentMatch:
        """
        Analyze if content is relevant to search query using AI.

        Args:
            content: Text content to analyze
            search_query: Search query to match against
            url: URL of the content
            title: Title of the page

        Returns:
            ContentMatch with relevance analysis
        """
        prompt = f"""
        Analyze the following web page content for relevance to the search query: "{search_query}"

        Page Title: {title}
        URL: {url}

        Content:
        {content[:3000]}  # Limit content to avoid token limits

        Tasks:
        1. Determine if this content is relevant to "{search_query}"
        2. Score relevance from 0.0 (not relevant) to 1.0 (highly relevant)
        3. Extract the most relevant snippet (max 200 words)
        4. Provide reasoning for your decision

        Respond in JSON format:
        {{
            "relevance_score": 0.0,
            "matched_content": "relevant snippet here",
            "reasoning": "explain why this is/isn't relevant"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            result_data = json.loads(response.text.strip())

            return ContentMatch(
                url=url,
                title=title,
                relevance_score=result_data.get("relevance_score", 0.0),
                matched_content=result_data.get("matched_content", ""),
                reasoning=result_data.get("reasoning", "")
            )

        except Exception as e:
            logger.error(f"Error analyzing content relevance: {e}")
            return ContentMatch(
                url=url,
                title=title,
                relevance_score=0.0,
                matched_content="",
                reasoning=f"Analysis failed: {str(e)}"
            )

    def extract_structured_data(
        self,
        content: str,
        data_schema: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from content using AI.

        Args:
            content: Text content to analyze
            data_schema: Optional schema defining what data to extract

        Returns:
            Dictionary with extracted structured data
        """
        if data_schema:
            schema_desc = "\n".join([f"- {key}: {desc}" for key, desc in data_schema.items()])
            extraction_prompt = f"Extract the following data:\n{schema_desc}"
        else:
            extraction_prompt = "Extract key information like titles, dates, names, prices, etc."

        prompt = f"""
        {extraction_prompt}

        Content:
        {content[:4000]}

        Respond in clean JSON format with the extracted data.
        If information is not available, use null values.
        """

        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text.strip())

        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return {"error": str(e)}

    def find_relevant_links(
        self,
        links: List[str],
        search_query: str,
        max_links: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Filter and rank links by relevance to search query.

        Args:
            links: List of URLs to analyze
            search_query: Search query to match against
            max_links: Maximum number of links to return

        Returns:
            List of relevant links with relevance scores
        """
        if not links:
            return []

        # Limit links to avoid token limits
        links_sample = links[:20]
        links_text = "\n".join([f"{i+1}. {link}" for i, link in enumerate(links_sample)])

        prompt = f"""
        Analyze these URLs for relevance to the search query: "{search_query}"

        URLs:
        {links_text}

        Tasks:
        1. Score each URL for relevance (0.0 to 1.0)
        2. Look for keywords in the URL path that relate to "{search_query}"
        3. Return the top {max_links} most relevant URLs

        Respond in JSON format:
        [
            {{
                "url": "full_url_here",
                "relevance_score": 0.0,
                "reasoning": "why this URL seems relevant"
            }}
        ]
        """

        try:
            response = self.model.generate_content(prompt)
            results = json.loads(response.text.strip())

            # Sort by relevance score and return top results
            return sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True)[:max_links]

        except Exception as e:
            logger.error(f"Error analyzing link relevance: {e}")
            return []

    def summarize_crawl_results(
        self,
        results: List[ContentMatch],
        search_query: str
    ) -> Dict[str, Any]:
        """
        Generate a summary of crawl results.

        Args:
            results: List of content matches
            search_query: Original search query

        Returns:
            Summary dictionary with key insights
        """
        if not results:
            return {"summary": "No relevant content found", "total_matches": 0}

        # Prepare results for analysis
        relevant_results = [r for r in results if r.relevance_score > 0.3]
        results_text = "\n\n".join([
            f"URL: {r.url}\nRelevance: {r.relevance_score:.2f}\nContent: {r.matched_content[:200]}..."
            for r in relevant_results[:10]
        ])

        prompt = f"""
        Summarize the crawling results for search query: "{search_query}"

        Results found ({len(relevant_results)} relevant out of {len(results)} total):
        {results_text}

        Provide:
        1. Key themes/topics found
        2. Most relevant URLs (top 3)
        3. Overall insights about "{search_query}"

        Respond in JSON format:
        {{
            "total_pages": {len(results)},
            "relevant_pages": {len(relevant_results)},
            "key_themes": ["theme1", "theme2"],
            "top_urls": ["url1", "url2", "url3"],
            "insights": "summary of findings",
            "search_query": "{search_query}"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text.strip())

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "error": str(e),
                "total_pages": len(results),
                "relevant_pages": len(relevant_results),
                "search_query": search_query
            }