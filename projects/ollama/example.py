#!/usr/bin/env python3

"""
Example usage of the Local AI Agent
"""

from agent import LocalAgent
import time


def main():
    # Initialize agent
    agent = LocalAgent()
    
    # Check if Ollama is running
    if not agent.is_ollama_running():
        print("❌ Ollama is not running. Please start it first with: ollama serve")
        return
    
    print("🤖 Local AI Agent Example")
    print(f"Model: {agent.model}")
    print("-" * 50)
    
    # Set a custom system prompt
    agent.set_system_prompt("You are a helpful Python programming assistant. Keep responses concise but informative.")
    
    # Example conversations
    examples = [
        "What is a Python decorator?",
        "Show me how to read a file in Python",
        "What's the difference between a list and a tuple?",
        "How do I handle exceptions in Python?"
    ]
    
    for i, question in enumerate(examples, 1):
        print(f"\n📝 Example {i}: {question}")
        print("🔄 Thinking...", end=" ", flush=True)
        
        start_time = time.time()
        response = agent.chat(question)
        end_time = time.time()
        
        print(f"(took {end_time - start_time:.2f}s)")
        print(f"🤖 Response: {response}")
        print("-" * 50)
    
    # Show conversation history
    print(f"\n📚 Total messages in conversation: {len(agent.get_conversation_history())}")
    
    # Reset and try a different system prompt
    print("\n🔄 Resetting conversation and changing system prompt...")
    agent.reset_conversation()
    agent.set_system_prompt("You are a creative storyteller. Write very short, engaging stories.")
    
    story_response = agent.chat("Tell me a story about a robot learning to paint")
    print(f"📖 Story: {story_response}")


if __name__ == "__main__":
    main()