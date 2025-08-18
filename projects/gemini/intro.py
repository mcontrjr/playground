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
    parser.add_argument("--clear", action="store_true", help="Clear conversation history")
    parser.add_argument("--show", action="store_true", help="Show conversation history")
    parser.add_argument("--raw", action="store_true", help="Show raw markdown output without formatting")
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
    
    # Handle command to show history
    if args.show:
        history = load_conversation_history()
        if not history:
            logger.info("No conversation history found")
            return
        
        print("\n" + "=" * 60)
        print("CONVERSATION HISTORY")
        print("=" * 60)
        
        for i, msg in enumerate(history):
            role = msg.get("role", "unknown")
            text = msg.get("parts", [{}])[0].get("text", "")
            
            if role == "user":
                print(f"\n\033[32m[USER]:\033[0m")
            else:
                print(f"\n\033[36m[ASSISTANT]:\033[0m")
            
            if args.raw:
                print(text)
            else:
                formatted_text = formatter.format_for_terminal(text)
                print(formatted_text)
            
            print("-" * 50)
        return
    
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
    
    # Make API request with spinner
    with Spinner("Generating response") as spinner:
        try:
            logger.debug("Sending request to Gemini API")
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=conversation_history
            )
            logger.debug("Received response from Gemini API")
            
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return
    
    # Extract and format response text
    response_text = response.text
    logger.debug(f"Response length: {len(response_text)} characters")
    
    # Format and display output
    if args.raw:
        print(response_text)
    else:
        formatted_text = formatter.format_for_terminal(response_text)
        print(formatted_text)
    
    # Add model response to history (store original, not formatted)
    model_message = format_message_for_api(response_text, "model")
    conversation_history.append(model_message)
    
    # Save updated history
    try:
        save_conversation_history(conversation_history)
        logger.debug(f"Saved conversation history with {len(conversation_history)} messages")
    except Exception as e:
        logger.warning(f"Failed to save conversation history: {e}")

if __name__ == "__main__":
    main()
