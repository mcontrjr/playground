
import logging
from datetime import datetime
from google import genai
from google.genai.types import GenerateContentResponse
from dotenv import load_dotenv

from mcp_search import search_web_mcp, DockerMCPSearchError

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler("mcp_gemini.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(file_handler)

load_dotenv()
client = genai.Client()

def track_token_usage(response: GenerateContentResponse):
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        thoughts_tokens = getattr(response.usage_metadata, "thoughts_token_count", None)
        output_tokens = getattr(response.usage_metadata, "candidates_token_count", None)
        logger.info(f"Gemini token usage - Thoughts tokens: {thoughts_tokens}, Output tokens: {output_tokens}")
        logger.info(f"Thoughts tokens: {thoughts_tokens}")
        logger.info(f"Output tokens: {output_tokens}")


# Initial search with MCP Server
location = "san jose california"

search_prompt = f"""
city, municipal, parks and recreation websites from {location}
"""

logger.info(f"Starting MCP search for location: {location}")
results = search_web_mcp(search_prompt, max_results=10)
logger.info(f"Received {len(results)} results from MCP search.")

results_str = ""
for result in results:
    results_str += f"{result.position}. [bold]{result.title}[/bold]"
    if result.url:
        results_str += f"   URL: {result.url}"
    results_str += f"   {result.snippet}"
    results_str += f"   Source: {result.source}"
    results_str += "\n"


# Refine results with Gemini 2.5
refinement_prompt = f"""
The following are search results from the search query: {search_prompt}:
{results_str}
Use the results crawl through the urls of the results and any child pages or routes.
We are looking for helpful resources to find city hosted events or activities for residents.
The main child pages or routes we are looking for are things like:
- events calendar
- activities calendar
Return refined list of only the sources that are relevant to the query as well as any child pages or routes.
Return the results as a list of of json objects with the following fields:
- title
- url
- purpose
- website routes list[str]
"""
logger.info("Sending refinement prompt to Gemini model.")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=refinement_prompt
)
logger.info("Received response from Gemini model.")
logger.info(response.text)
track_token_usage(response)

# Search result sources and extract event information
extract_prompt = f"""
The following are results from the following refinement prompt: {refinement_prompt}
{response.text}
Search through the sources (urls) in the results and extract any event information you can find for events in the next 7 days.
Today is {datetime.now().strftime('%Y-%m-%d')}.
Focus on events that align
Return the results as a list of json objects with the following fields:
- event name
- date
- time
- location
- description
- url
"""
logger.info("Sending extract prompt to Gemini model.")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=extract_prompt
)
logger.info("Received response from Gemini model.")
logger.info(response.text)
track_token_usage(response)