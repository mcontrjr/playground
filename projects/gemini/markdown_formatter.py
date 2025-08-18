#!/usr/bin/env python3

import re
from typing import List

class TerminalColors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

class MarkdownFormatter:
    """Converts markdown to colorized terminal output"""
    
    def __init__(self):
        self.colors = TerminalColors()
        
    def format_for_terminal(self, text: str) -> str:
        """Convert markdown text to colorized terminal output"""
        lines = text.split('\n')
        formatted_lines = []
        in_code_block = False
        code_block_lang = ""
        list_level = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Handle code blocks
            if line.startswith('```'):
                if not in_code_block:
                    # Starting code block
                    in_code_block = True
                    code_block_lang = line[3:].strip()
                    if code_block_lang:
                        formatted_lines.append(
                            f"{self.colors.DIM}{self.colors.CYAN}┌─ {code_block_lang} ─{self.colors.RESET}"
                        )
                    else:
                        formatted_lines.append(
                            f"{self.colors.DIM}{self.colors.CYAN}┌─ code ─{self.colors.RESET}"
                        )
                else:
                    # Ending code block
                    in_code_block = False
                    formatted_lines.append(
                        f"{self.colors.DIM}{self.colors.CYAN}└─────────{self.colors.RESET}"
                    )
                    code_block_lang = ""
                i += 1
                continue
            
            # Inside code block
            if in_code_block:
                formatted_lines.append(
                    f"{self.colors.DIM}{self.colors.CYAN}│{self.colors.RESET} "
                    f"{self.colors.BRIGHT_WHITE}{self.colors.DIM}{line}{self.colors.RESET}"
                )
                i += 1
                continue
            
            # Headers
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                header_text = line.lstrip('# ').strip()
                if level == 1:
                    formatted_lines.append("")
                    formatted_lines.append(
                        f"{self.colors.BOLD}{self.colors.BRIGHT_BLUE}{header_text}{self.colors.RESET}"
                    )
                    formatted_lines.append(
                        f"{self.colors.BRIGHT_BLUE}{'=' * min(len(header_text), 60)}{self.colors.RESET}"
                    )
                elif level == 2:
                    formatted_lines.append("")
                    formatted_lines.append(
                        f"{self.colors.BOLD}{self.colors.CYAN}{header_text}{self.colors.RESET}"
                    )
                    formatted_lines.append(
                        f"{self.colors.CYAN}{'-' * min(len(header_text), 50)}{self.colors.RESET}"
                    )
                elif level == 3:
                    formatted_lines.append("")
                    formatted_lines.append(
                        f"{self.colors.BOLD}{self.colors.YELLOW}{header_text}{self.colors.RESET}"
                    )
                else:
                    formatted_lines.append("")
                    formatted_lines.append(
                        f"{self.colors.BOLD}{self.colors.WHITE}{header_text}{self.colors.RESET}"
                    )
                i += 1
                continue
            
            # Horizontal rules
            if re.match(r'^[-*_]{3,}$', line.strip()):
                formatted_lines.append("")
                formatted_lines.append(
                    f"{self.colors.DIM}{self.colors.BRIGHT_BLACK}{'─' * 50}{self.colors.RESET}"
                )
                formatted_lines.append("")
                i += 1
                continue
            
            # Bullet points and numbered lists
            bullet_match = re.match(r'^(\s*)[*+-]\s+(.+)', line)
            number_match = re.match(r'^(\s*)(\d+)\.\s+(.+)', line)
            
            if bullet_match:
                indent = bullet_match.group(1)
                content = bullet_match.group(2)
                formatted_content = self._format_inline(content)
                formatted_lines.append(
                    f"{indent}{self.colors.BRIGHT_YELLOW}•{self.colors.RESET} {formatted_content}"
                )
                i += 1
                continue
                
            if number_match:
                indent = number_match.group(1)
                number = number_match.group(2)
                content = number_match.group(3)
                formatted_content = self._format_inline(content)
                formatted_lines.append(
                    f"{indent}{self.colors.BRIGHT_MAGENTA}{number}.{self.colors.RESET} {formatted_content}"
                )
                i += 1
                continue
            
            # Block quotes
            if line.strip().startswith('>'):
                quote_text = line.strip()[1:].strip()
                formatted_quote = self._format_inline(quote_text)
                formatted_lines.append(
                    f"{self.colors.DIM}{self.colors.BRIGHT_BLACK}│{self.colors.RESET} "
                    f"{self.colors.ITALIC}{self.colors.BRIGHT_WHITE}{formatted_quote}{self.colors.RESET}"
                )
                i += 1
                continue
            
            # Empty lines
            if not line.strip():
                formatted_lines.append("")
                i += 1
                continue
            
            # Regular paragraphs
            formatted_line = self._format_inline(line)
            formatted_lines.append(formatted_line)
            i += 1
        
        return '\n'.join(formatted_lines)
    
    def _format_inline(self, text: str) -> str:
        """Format inline markdown elements like bold, italic, code, links"""
        # Bold (**text** or __text__)
        text = re.sub(
            r'\*\*(.*?)\*\*', 
            f'{self.colors.BOLD}\\1{self.colors.RESET}', 
            text
        )
        text = re.sub(
            r'__(.*?)__', 
            f'{self.colors.BOLD}\\1{self.colors.RESET}', 
            text
        )
        
        # Italic (*text* or _text_) - be careful not to match bold
        text = re.sub(
            r'(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)', 
            f'{self.colors.ITALIC}\\1{self.colors.RESET}', 
            text
        )
        text = re.sub(
            r'(?<!_)_(?!_)([^_]+?)_(?!_)', 
            f'{self.colors.ITALIC}\\1{self.colors.RESET}', 
            text
        )
        
        # Inline code (`code`)
        text = re.sub(
            r'`([^`]+)`', 
            f'{self.colors.BRIGHT_BLACK}{self.colors.DIM}\\1{self.colors.RESET}', 
            text
        )
        
        # Links [text](url)
        text = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)', 
            f'{self.colors.UNDERLINE}{self.colors.BRIGHT_BLUE}\\1{self.colors.RESET}', 
            text
        )
        
        # Strikethrough ~~text~~
        text = re.sub(
            r'~~(.*?)~~', 
            f'{self.colors.DIM}\\1{self.colors.RESET}', 
            text
        )
        
        return text
    
    def remove_markdown(self, text: str) -> str:
        """Remove all markdown formatting, returning plain text"""
        # Remove headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Remove bold and italic
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        text = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)', r'\1', text)
        text = re.sub(r'(?<!_)_(?!_)([^_]+?)_(?!_)', r'\1', text)
        
        # Remove strikethrough
        text = re.sub(r'~~(.*?)~~', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
        
        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove links
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove horizontal rules
        text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
        
        # Convert bullet points and numbered lists
        text = re.sub(r'^\s*[*+-]\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Remove block quotes
        text = re.sub(r'^\s*>\s*', '', text, flags=re.MULTILINE)
        
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        return text
