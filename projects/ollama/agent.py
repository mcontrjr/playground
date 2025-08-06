#!/usr/bin/env python3

import json
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import time


@dataclass
class Message:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Conversation:
    messages: List[Message] = field(default_factory=list)
    max_history: int = 10

    def add_message(self, role: str, content: str):
        self.messages.append(Message(role, content))
        if len(self.messages) > self.max_history * 2:
            self.messages = self.messages[-self.max_history:]

    def get_context(self) -> List[Dict[str, str]]:
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]


class LocalAgent:
    def __init__(self, model: str = "llama3.2:1b", host: str = "http://localhost:11434", auto_warmup: bool = False):
        self.model = model
        self.host = host
        self.conversation = Conversation()
        self.system_prompt = "You are a helpful AI assistant. Respond concisely and accurately."
        self._is_warmed_up = False

        if auto_warmup and self.is_ollama_running():
            self.warmup()

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt

    def _make_request(self, messages: List[Dict[str, str]], timeout: int = 60, is_warmup: bool = False) -> str:
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt}] + messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            if not is_warmup:
                self._is_warmed_up = True
            return response.json()["message"]["content"]
        except requests.RequestException as e:
            return f"Error communicating with Ollama: {e}"

    def chat(self, user_input: str) -> str:
        # Auto-warmup if not already done
        if not self._is_warmed_up:
            self.warmup()

        self.conversation.add_message("user", user_input)
        context = self.conversation.get_context()

        # Use longer timeout for first few requests if not warmed up
        timeout = 120 if not self._is_warmed_up else 60
        response = self._make_request(context, timeout=timeout)
        self.conversation.add_message("assistant", response)

        return response

    def reset_conversation(self):
        self.conversation = Conversation()

    def get_conversation_history(self) -> List[Message]:
        return self.conversation.messages.copy()

    def is_ollama_running(self) -> bool:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_available_models(self) -> List[str]:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
        except requests.RequestException:
            pass
        return []

    def warmup(self, timeout: int = 120, show_progress: bool = True) -> bool:
        """Warm up the model by sending a simple request to preload it into memory"""
        # First check if model might already be warm with a quick test
        if not show_progress:  # Skip quick test if we want to show progress
            quick_test = self._quick_warmup_test()
            if quick_test:
                self._is_warmed_up = True
                return True

        if show_progress:
            print(f"🔥 Warming up {self.model} model...", end="", flush=True)

        start_time = time.time()
        warmup_message = [{"role": "user", "content": "Hi"}]

        try:
            response = self._make_request(warmup_message, timeout=timeout, is_warmup=True)

            if "Error communicating" not in response:
                self._is_warmed_up = True
                elapsed = time.time() - start_time
                if show_progress:
                    print(f" ✅ Ready! ({elapsed:.1f}s)")
                return True
            else:
                if show_progress:
                    print(f" ❌ Failed: {response}")
                return False

        except Exception as e:
            if show_progress:
                print(f" ❌ Failed: {e}")
            return False

    def _quick_warmup_test(self) -> bool:
        """Quick test to see if model is already responsive"""
        try:
            start_time = time.time()
            test_message = [{"role": "user", "content": "test"}]
            response = self._make_request(test_message, timeout=5, is_warmup=True)
            elapsed = time.time() - start_time

            # If response is fast (< 3 seconds), model is likely already warm
            return elapsed < 3.0 and "Error communicating" not in response
        except:
            return False

    def is_warmed_up(self) -> bool:
        """Check if the model is currently warmed up"""
        return self._is_warmed_up

    def force_warmup_reset(self):
        """Reset warmup status (for testing or troubleshooting)"""
        self._is_warmed_up = False


if __name__ == "__main__":
    agent = LocalAgent()

    if not agent.is_ollama_running():
        print("Error: Ollama is not running. Please start Ollama service first.")
        exit(1)

    print("Available models:", agent.get_available_models())
    print(f"Using model: {agent.model}")
    print("Type 'quit' to exit, 'reset' to clear conversation, 'help' for commands\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit']:
            break
        elif user_input.lower() == 'reset':
            agent.reset_conversation()
            print("Conversation reset.")
            continue
        elif user_input.lower() == 'help':
            print("Commands:")
            print("  quit/exit - Exit the program")
            print("  reset - Clear conversation history")
            print("  help - Show this help message")
            continue
        elif not user_input:
            continue

        print("Assistant: ", end="", flush=True)
        response = agent.chat(user_input)
        print(response)
        print()