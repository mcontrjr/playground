#!/usr/bin/env python3

import os
import argparse
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Import our custom modules
from markdown import MarkdownFormatter, create_logger, Spinner


def format_message_for_api(message, role):
    """Format a message for the Gemini API"""
    return {"role": role, "parts": [{"text": message}]}


def process_message(message, file_path, logger, formatter, api_key):
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
            except Exception as e:
                logger.error(f"Failed to upload file {file_path}: {e}")
                return None
        else:
            logger.error(f"File not found: {file_path}")
            return None
    else:
        # Create user message with just text
        user_message_for_api = format_message_for_api(message, "user")

    # Make API request with spinner
    spinner = Spinner("Thinking", "dots")
    try:
        logger.debug("Sending request to Gemini API")
        spinner.start()
        
        # Get the model
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            [user_message_for_api],
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
        return None

    finally:
        # Clean up uploaded file if it exists
        if file_path and 'f' in locals():
            try:
                genai.delete_file(name=f.name)
            except Exception as e:
                logger.warning(f"Failed to delete uploaded file: {e}")
    
    return raw_text


def chat_mode(logger, formatter, api_key):
    """Interactive chat mode"""
    print("\n" + "=" * 60)
    print("GEMINI INTERACTIVE CHAT")
    print("=" * 60)
    print("Type your messages and press Enter. Type 'exit' or 'quit' to end the chat.")
    print("Type '/file <path>' followed by your message to include a file.")
    print("=" * 60)
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("\n> ").strip()
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            
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
            
            # Process the message
            response = process_message(
                user_input, file_path, logger, formatter, api_key
            )
            
            if not response:
                print("Failed to get response. Please try again.")
                    
        except KeyboardInterrupt:
            print("\n\nChat interrupted. Goodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def main():
    parser = argparse.ArgumentParser(description="Generate content using Gemini API")
    parser.add_argument("-m", "--message", type=str, help="Message to send to Gemini")
    parser.add_argument("-f", "--file", type=str, help="File path to add to message")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat mode")
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


    # Handle chat mode
    if args.chat:
        chat_mode(logger, formatter, api_key)
        return

    # Check if message is provided for single-message operation
    if not args.message:
        parser.print_help()
        return

    logger.debug(f"Processing user input: {args.message[:50]}...")

    # Process the message
    response = process_message(
        args.message, args.file, logger, formatter, api_key
    )
    
    if not response:
        logger.error("Failed to get response from Gemini API")
        return

if __name__ == "__main__":
    main()
