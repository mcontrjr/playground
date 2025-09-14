
import os
import argparse
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
import uvicorn

load_dotenv()

app = FastAPI()

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

def scrape(url: str):
    """
    Scrape a URL and print the result.
    """
    try:
        scraped_data = firecrawl_app.scrape(url=url)
        print(scraped_data)
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
    scrape_parser.add_argument("--url", required=True, help="URL to scrape")

    server_parser = subparsers.add_parser("server", help="Start the FastAPI server")

    args = parser.parse_args()

    if args.command == "scrape":
        scrape(args.url)
    elif args.command == "server":
        server()
    else:
        parser.print_help()
