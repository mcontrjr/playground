#!/usr/bin/env python3
import os
import argparse
import json
from datetime import datetime
from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
import uvicorn

load_dotenv()

app = FastAPI()

class SearchSchema(BaseModel):
    url: str
    summary: str
    contains_events: bool

EventSchema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "date": {"type": "string"},
            "location": {"type": "string"},
            "time": {"type": "string"},
            "description": {"type": "string"},
            "url": {"type": "string"}
        },
        "required": ["title", "date", "location", "time", "description", "url"]
    }
}

firecrawl_app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

@app.post("/scrape")
async def scrape_endpoint(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        return {"error": "URL is required"}

    try:
        scraped_data = firecrawl_app.scrape(url=url)
        return scraped_data
    except Exception as e:
        return {"error": str(e)}

def output_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Output saved to {filename}")

def scrape(args: argparse.Namespace):
    """
    Scrape a URL and print the result.
    """
    try:
        scraped_data = firecrawl_app.scrape(
            url=args.url,
            formats=[{
                "type": "json",
                "schema": SearchSchema
            }])
        print(scraped_data)
        if args.file:
            output_to_file(scraped_data.json, args.file)
    except Exception as e:
        print(f"Error: {e}")

def extract(args: argparse.Namespace):
    """
    Extract data from a URL and print the result.
    """
    try:
        print(f"Args: {args}")
        extracted_data = firecrawl_app.extract(
            urls=args.urls,
            prompt="Find all events in San Jose that are related to farmers markets and outdoor activities in the next 7 days. Return the results in JSON format with fields for title, date, location, time, description, and URL.",
            enable_web_search=True
        )
        print(extracted_data)
        if args.file:
            output_to_file(extracted_data.data, args.file)
    except Exception as e:
        print(f"Error: {e}")

def search(args: argparse.Namespace):
    """
    Search for a query and print the result.
    """
    try:
        results = firecrawl_app.search(
            query=args.query,
            limit=3
        )
        print(results)
        if args.file:
            output_to_file(results, args.file)
    except Exception as e:
        print(f"Error: {e}")

def map_url(args: argparse.Namespace, search: str = None):
    """
    Map a URL to its routes and print the result.
    """
    try:
        mapped_data = firecrawl_app.map(url=args.url, search=search, limit=10, sitemap="include")
        print(mapped_data)
        if args.file:
            output_to_file(mapped_data.data, args.file)
    except Exception as e:
        print(f"Error: {e}")

def server():
    """
    Start the FastAPI server.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Firecrawl Scraper")
    subparsers = parser.add_subparsers(dest="command")
    scrape_parser = subparsers.add_parser("scrape", help="Scrape a URL")
    extract_parser = subparsers.add_parser("extract", help="Extract data from a URL")
    search_parser = subparsers.add_parser("search", help="Search for a query")
    map_parser = subparsers.add_parser("map", help="Map a URL to its routes")
    scrape_parser.add_argument("--url", required=True, help="URL to scrape")
    extract_parser.add_argument("--urls", nargs='+', required=True, help="URLs to extract data from e.g. --urls url1 url2 url3")
    search_parser.add_argument("--query", required=True, help="Search query")
    map_parser.add_argument("--url", required=True, help="URL to map")
    map_parser.add_argument("--search", required=False, help="Search term to include in mapping")
    parser.add_argument("--file", required=False, help="Output file name")


    server_parser = subparsers.add_parser("server", help="Start the FastAPI server")

    args = parser.parse_args()

    if args.command == "scrape":
        scrape(args)
    elif args.command == "extract":
        extract(args)
    elif args.command == "map":
        map_url(args)
    elif args.command == "search":
        search(args)
    elif args.command == "server":
        server()
    else:
        parser.print_help()
