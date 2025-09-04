#!/usr/bin/env python3

import os
import json
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

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


def process_message(message, file_path, conversation_history, logger, formatter, api_key):
    """Process a single message and return the response"""
    
    # Prepare the current user message with optional file
    if file_path:
        if os.path.exists(file_path):
            try:
                # Upload the file using the Gemini API
                f = genai.upload_file(path=file_path)
                logger.debug(f"File uploaded successfully: {f.name}")
                
                # Create user message with both file and text for API
                user_message_for_api = {
                    "role": "user",
                    "parts": [f, {"text": message}]
                }
                # Create user message for history (without file object)
                user_message_for_history = {
                    "role": "user",
                    "parts": [{"text": message}],
                    "file_uploaded": file_path
                }
            except Exception as e:
                logger.error(f"Failed to upload file {file_path}: {e}")
                return None, None
        else:
            logger.error(f"File not found: {file_path}")
            return None, None
    else:
        # Create user message with just text
        user_message_for_api = format_message_for_api(message, "user")
        user_message_for_history = user_message_for_api
    
    # Add user message to history (for saving to file)
    conversation_history.append(user_message_for_history)
    
    # Create the actual request content (includes file object if present)
    # Always clean the conversation history first to remove file_uploaded fields
    clean_conversation_history = []
    for msg in conversation_history[:-1]:  # Exclude the last message (current user input)
        if 'file_uploaded' in msg:
            # Create a clean version without file_uploaded field
            clean_msg = {k: v for k, v in msg.items() if k != 'file_uploaded'}
            clean_conversation_history.append(clean_msg)
        else:
            clean_conversation_history.append(msg)
    
    if file_path:
        # Add the API version of the current message (with file object)
        api_conversation_history = clean_conversation_history + [user_message_for_api]
    else:
        # Add the current message as-is (no file object)
        api_conversation_history = clean_conversation_history + [user_message_for_api]

    # Make API request with spinner
    spinner = Spinner("Thinking", "dots")
    try:
        logger.debug("Sending request to Gemini API")
        spinner.start()
        
        # Get the model
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            api_conversation_history,
            stream=True
        )

        raw_text = ""
        first_chunk = True

        for chunk in response:
            if first_chunk:
                # Stop spinner before first chunk and ensure clean line
                spinner.stop()
                first_chunk = False

            raw_text += chunk.text
            formatted_text = formatter.format_for_terminal(chunk.text)
            print(formatted_text, end="", flush=True)

        # Add a newline after streaming is complete
        print()

    except Exception as e:
        spinner.stop()  # Make sure spinner stops on error
        logger.error(f"API request failed: {e}")
        return None, None

    finally:
        # Clean up uploaded file if it exists
        if file_path and 'f' in locals():
            try:
                genai.delete_file(name=f.name)
            except Exception as e:
                logger.warning(f"Failed to delete uploaded file: {e}")

    # Add model response to history (store original, not formatted)
    model_message = format_message_for_api(raw_text, "model")
    conversation_history.append(model_message)
    
    return raw_text, conversation_history


def chat_mode(logger, formatter, api_key):
    """Interactive chat mode"""
    print("\n" + "=" * 60)
    print("GEMINI INTERACTIVE CHAT")
    print("=" * 60)
    print("Type your messages and press Enter. Type 'exit' or 'quit' to end the chat.")
    print("Type '/clear' to clear conversation history.")
    print("Type '/file <path>' followed by your message to include a file.")
    print("=" * 60)
    print()
    
    # Load conversation history
    conversation_history = load_conversation_history()
    logger.debug(f"Loaded {len(conversation_history)} messages from history")
    
    while True:
        try:
            # Get user input
            user_input = input("\n> ").strip()
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            
            if user_input == '/clear':
                if Path(HISTORY_FILE).exists():
                    os.remove(HISTORY_FILE)
                    conversation_history = []
                    print("Conversation history cleared.")
                else:
                    print("No history to clear.")
                continue
            
            if not user_input:
                continue
            
            # Handle file upload
            file_path = None
            if user_input.startswith('/file '):
                parts = user_input[6:].split(' ', 1)
                if len(parts) == 2:
                    file_path = parts[0]
                    user_input = parts[1]
                else:
                    print("Usage: /file <path> <your message>")
                    continue
            
            # Manage context size
            original_length = len(conversation_history)
            conversation_history = manage_context_size(conversation_history)
            if len(conversation_history) < original_length:
                logger.debug(f"Context trimmed from {original_length} to {len(conversation_history)} messages")
            
            # Process the message
            response, updated_history = process_message(
                user_input, file_path, conversation_history, logger, formatter, api_key
            )
            
            if response and updated_history:
                conversation_history = updated_history
                # Save updated history
                try:
                    save_conversation_history(conversation_history)
                    logger.debug(f"Saved conversation history with {len(conversation_history)} messages")
                except Exception as e:
                    logger.warning(f"Failed to save conversation history: {e}")
                    
        except KeyboardInterrupt:
            print("\n\nChat interrupted. Goodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def main():
    parser = argparse.ArgumentParser(description="Generate content using Gemini API with conversation history")
    parser.add_argument("-m", "--message", type=str, help="Message to send to Gemini")
    parser.add_argument("-f", "--file", type=str, help="File path to add to message")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat mode")
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

    # Configure Gemini API
    try:
        genai.configure(api_key=api_key)
        logger.debug("Gemini API configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}")
        return

    # Handle command to clear history
    if args.clear:
        if Path(HISTORY_FILE).exists():
            os.remove(HISTORY_FILE)
            logger.info("Conversation history cleared")
        else:
            logger.info("No history file found to clear")
        return

    # Handle chat mode
    if args.chat:
        chat_mode(logger, formatter, api_key)
        return

    # Check if message is provided for single-message operation
    if not args.message:
        parser.print_help()
        return

    logger.debug(f"Processing user input: {args.message[:50]}...")

    # Load conversation history
    conversation_history = load_conversation_history()
    logger.debug(f"Loaded {len(conversation_history)} messages from history")

    # Manage context size
    original_length = len(conversation_history)
    conversation_history = manage_context_size(conversation_history)
    if len(conversation_history) < original_length:
        logger.debug(f"Context trimmed from {original_length} to {len(conversation_history)} messages")

    # Process the message
    response, updated_history = process_message(
        args.message, args.file, conversation_history, logger, formatter, api_key
    )
    
    if response and updated_history:
        # Save updated history
        try:
            save_conversation_history(updated_history)
            logger.debug(f"Saved conversation history with {len(updated_history)} messages")
        except Exception as e:
            logger.warning(f"Failed to save conversation history: {e}")

if __name__ == "__main__":
    main()
