#!/usr/bin/env python3

import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from google import genai

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
    args = parser.parse_args()
    
    load_dotenv()
    
    # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Handle command to clear history
    if args.clear:
        if Path(HISTORY_FILE).exists():
            os.remove(HISTORY_FILE)
            print("Conversation history cleared.")
        return
    
    # Handle command to show history
    if args.show:
        history = load_conversation_history()
        if not history:
            print("No conversation history found.")
            return
        
        print("\nConversation History:")
        for i, msg in enumerate(history):
            role = msg.get("role", "unknown")
            text = msg.get("parts", [{}])[0].get("text", "")
            print(f"\n[{role.upper()}]: {text}\n{'='*50}")
        return
    
    # Check if content is provided for normal operation
    if not args.content:
        parser.print_help()
        return
    
    # Load conversation history
    conversation_history = load_conversation_history()
    
    # Manage context size
    conversation_history = manage_context_size(conversation_history)
    
    # Add user message to history
    user_message = format_message_for_api(args.content, "user")
    conversation_history.append(user_message)
    
    # Create messages array for API request
    try:
        # Generate response using conversation history
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=conversation_history
        )
        
        # Extract response text
        response_text = response.text
        print(response_text)
        
        # Add model response to history
        model_message = format_message_for_api(response_text, "model")
        conversation_history.append(model_message)
        
        # Save updated history
        save_conversation_history(conversation_history)
        
    except Exception as e:
        print(f"Error generating content: {e}")

if __name__ == "__main__":
    main()
