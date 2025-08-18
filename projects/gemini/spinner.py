#!/usr/bin/env python3

import threading
import time
from typing import Optional

class Spinner:
    """A simple spinner for showing loading progress"""
    
    def __init__(self, message: str = "Loading", style: str = "dots"):
        self.message = message
        self.spinning = False
        self.spinner_thread: Optional[threading.Thread] = None
        
        # Different spinner styles
        self.styles = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "bars": ["▁", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃"],
            "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            "clock": ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"],
            "moon": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
            "simple": ["|", "/", "-", "\\"],
        }
        
        self.spinner_chars = self.styles.get(style, self.styles["dots"])
    
    def _spin(self):
        """Internal method that runs the spinner animation"""
        i = 0
        while self.spinning:
            char = self.spinner_chars[i % len(self.spinner_chars)]
            print(f"\r\033[36m{char}\033[0m \033[2m{self.message}...\033[0m", end="", flush=True)
            i += 1
            time.sleep(0.1)
    
    def start(self):
        """Start the spinner animation"""
        if not self.spinning:
            self.spinning = True
            self.spinner_thread = threading.Thread(target=self._spin, daemon=True)
            self.spinner_thread.start()
    
    def stop(self):
        """Stop the spinner animation and clear the line"""
        if self.spinning:
            self.spinning = False
            if self.spinner_thread and self.spinner_thread.is_alive():
                self.spinner_thread.join(timeout=0.2)
            
            # Clear the spinner line
            clear_length = len(self.message) + 10
            print(f"\r{' ' * clear_length}\r", end="", flush=True)
    
    def update_message(self, new_message: str):
        """Update the spinner message while it's running"""
        self.message = new_message
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
