#!/usr/bin/env python3

import os
import json
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Import our custom modules
from markdown_formatter import MarkdownFormatter
from colored_logger import create_logger
from spinner import Spinner

MAX_CONTEXT_LENGTH = 16000  # Adjust based on model context window size
HISTORY_FILE = "conversation_history.json"

def load_conversation_history():
    """Load conversation history from file if it exists"""
    history_path = Path(HISTORY_FILE)
    if history_path.exists():
        with open(history_path, 'r') as f:
            return json.load(f)
    return []

def save_conversation_history(history):
    """Save conversation history to file"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def manage_context_size(history, max_length=MAX_CONTEXT_LENGTH):
    """Ensure the conversation history fits within context limits"""
    # Simple strategy: remove oldest messages when over limit
    total_length = sum(len(str(msg)) for msg in history)

    while total_length > max_length and len(history) > 2:  # Keep at least the last exchange
        # Remove the oldest message pair (user message and model response)
        if len(history) >= 2:
            history.pop(0)  # Remove oldest user message
            if history:  # Check if there's still a message to remove
                history.pop(0)  # Remove oldest model response

        # Recalculate total length
        total_length = sum(len(str(msg)) for msg in history)

    return history

def format_message_for_api(message, role):
    """Format a message for the Gemini API"""
    return {"role": role, "parts": [{"text": message}]}


def main():
    parser = argparse.ArgumentParser(description="Generate content using Gemini API with conversation history")
    parser.add_argument("-c", "--content", type=str, help="Content to generate")
    parser.add_argument("-f", "--file", type=str, help="File path to add to content")
    parser.add_argument("--clear", action="store_true", help="Clear conversation history")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    # Initialize logger and formatter
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = create_logger("gemini_client", log_level)
    formatter = MarkdownFormatter()

    load_dotenv()

    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set")
        return

    logger.debug(f"API key loaded: {'*' * 10}{api_key[-4:] if len(api_key) > 4 else '****'}")

    # Initialize Gemini client
    try:
        client = genai.Client(api_key=api_key)
        logger.debug("Gemini client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return

    # Handle command to clear history
    if args.clear:
        if Path(HISTORY_FILE).exists():
            os.remove(HISTORY_FILE)
            logger.info("Conversation history cleared")
        else:
            logger.info("No history file found to clear")
        return

    # Removed --show argument and related code

    # Check if content is provided for normal operation
    if not args.content:
        parser.print_help()
        return

    logger.debug(f"Processing user input: {args.content[:50]}...")

    # Load conversation history
    conversation_history = load_conversation_history()
    logger.debug(f"Loaded {len(conversation_history)} messages from history")

    # Manage context size
    original_length = len(conversation_history)
    conversation_history = manage_context_size(conversation_history)
    if len(conversation_history) < original_length:
        logger.debug(f"Context trimmed from {original_length} to {len(conversation_history)} messages")

    # Add user message to history
    user_message = format_message_for_api(args.content, "user")
    conversation_history.append(user_message)
    text_content = " ".join([conv for conv in conversation_history if isinstance(conv, str)])
    if args.file:
        if os.path.exists(args.file):
            f = client.files.upload(file=args.file)
            contents = [f, text_content]
    else:
        contents = [text_content]

    # Make API request with spinner
    with Spinner("Generating response") as spinner:
        try:
            logger.debug("Sending request to Gemini API")
            response = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=conversation_history
            )
            raw_text = ""
            for chunk in response:
                raw_text += chunk.text
                formatted_text = formatter.format_for_terminal(chunk.text)
                print(formatted_text, end="")

        except Exception as e:
            logger.error(f"API request failed: {e}")
            return

    # Add model response to history (store original, not formatted)
    model_message = format_message_for_api(raw_text, "model")
    conversation_history.append(model_message)

    # Save updated history
    try:
        save_conversation_history(conversation_history)
        logger.debug(f"Saved conversation history with {len(conversation_history)} messages")
    except Exception as e:
        logger.warning(f"Failed to save conversation history: {e}")

if __name__ == "__main__":
    main()
