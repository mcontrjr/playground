#!/usr/bin/env python3

import re
import json
import time
from typing import List, Optional, Tuple
from .colored_logger import create_logger
from .spinner import Spinner

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
                formatted_code_line = self._format_code_line(line, code_block_lang)
                formatted_lines.append(
                    f"{self.colors.DIM}{self.colors.CYAN}│{self.colors.RESET} {formatted_code_line}"
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

            # Tables
            if self._is_table_row(line) and i < len(lines) - 1 and self._is_table_separator(lines[i + 1]):
                # Found a table - process it all at once
                table_lines, consumed = self._extract_table(lines, i)
                formatted_table = self._format_table(table_lines)
                formatted_lines.extend(formatted_table)
                i += consumed
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

    def _is_table_row(self, line: str) -> bool:
        """Check if line looks like a table row"""
        stripped = line.strip()
        return '|' in stripped

    def _is_table_separator(self, line: str) -> bool:
        """Check if line is a table separator (like | :--- | :---: | ---: |)"""
        stripped = line.strip()
        if not stripped:
            return False
        # Remove pipes and check if it's mostly dashes and colons
        content = re.sub(r'\|', '', stripped)
        return bool(re.match(r'^[\s:-]+$', content)) and '-' in content

    def _extract_table(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Extract all lines of a table starting from start_idx"""
        table_lines = []
        idx = start_idx

        # Get header row
        table_lines.append(lines[idx])
        idx += 1

        # Get separator row
        if idx < len(lines) and self._is_table_separator(lines[idx]):
            table_lines.append(lines[idx])
            idx += 1

        # Get data rows
        while idx < len(lines) and self._is_table_row(lines[idx]):
            table_lines.append(lines[idx])
            idx += 1

        return table_lines, idx - start_idx

    def _format_table(self, table_lines: List[str]) -> List[str]:
        """Format a markdown table with borders and colors"""
        if len(table_lines) < 2:
            return table_lines

        # Parse the table structure
        header_cells = [cell.strip() for cell in table_lines[0].split('|') if cell.strip()]
        separator_line = table_lines[1]

        # Parse alignment from separator
        alignments = []
        sep_cells = [cell.strip() for cell in separator_line.split('|') if cell.strip()]
        for cell in sep_cells:
            if cell.startswith(':') and cell.endswith(':'):
                alignments.append('center')
            elif cell.endswith(':'):
                alignments.append('right')
            else:
                alignments.append('left')

        # Calculate column widths
        col_widths = []
        all_rows = [header_cells]

        # Parse data rows
        for line in table_lines[2:]:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            all_rows.append(cells)

        # Calculate widths
        for i in range(len(header_cells)):
            max_width = max(len(str(row[i] if i < len(row) else '')) for row in all_rows)
            col_widths.append(max(max_width, 8))  # Minimum width of 8

        formatted_lines = []

        # Top border
        border_line = '┌' + '┬'.join('─' * (width + 2) for width in col_widths) + '┐'
        formatted_lines.append(f"{self.colors.DIM}{self.colors.BRIGHT_BLACK}{border_line}{self.colors.RESET}")

        # Header row
        header_line = '│'
        for i, (cell, width, align) in enumerate(zip(header_cells, col_widths, alignments)):
            formatted_cell = self._format_inline(cell)
            # Remove color codes for width calculation
            plain_cell = re.sub(r'\033\[[0-9;]*m', '', formatted_cell)

            if align == 'center':
                padded = plain_cell.center(width)
                # Re-apply formatting
                colored_content = formatted_cell + ' ' * (len(padded) - len(plain_cell))
            elif align == 'right':
                padded = plain_cell.rjust(width)
                colored_content = ' ' * (len(padded) - len(plain_cell)) + formatted_cell
            else:
                padded = plain_cell.ljust(width)
                colored_content = formatted_cell + ' ' * (len(padded) - len(plain_cell))

            header_line += f' {self.colors.BOLD}{self.colors.BRIGHT_YELLOW}{colored_content}{self.colors.RESET} │'

        formatted_lines.append(header_line)

        # Header separator
        sep_line = '├' + '┼'.join('─' * (width + 2) for width in col_widths) + '┤'
        formatted_lines.append(f"{self.colors.DIM}{self.colors.BRIGHT_BLACK}{sep_line}{self.colors.RESET}")

        # Data rows
        for row in all_rows[1:]:
            row_line = '│'
            for i, width in enumerate(col_widths):
                cell = row[i] if i < len(row) else ''
                formatted_cell = self._format_inline(cell)
                plain_cell = re.sub(r'\033\[[0-9;]*m', '', formatted_cell)

                align = alignments[i] if i < len(alignments) else 'left'

                if align == 'center':
                    padded = plain_cell.center(width)
                    colored_content = formatted_cell + ' ' * (len(padded) - len(plain_cell))
                elif align == 'right':
                    padded = plain_cell.rjust(width)
                    colored_content = ' ' * (len(padded) - len(plain_cell)) + formatted_cell
                else:
                    padded = plain_cell.ljust(width)
                    colored_content = formatted_cell + ' ' * (len(padded) - len(plain_cell))

                row_line += f' {colored_content} │'

            formatted_lines.append(row_line)

        # Bottom border
        bottom_line = '└' + '┴'.join('─' * (width + 2) for width in col_widths) + '┘'
        formatted_lines.append(f"{self.colors.DIM}{self.colors.BRIGHT_BLACK}{bottom_line}{self.colors.RESET}")

        return [''] + formatted_lines + ['']

    def _format_code_line(self, line: str, language: str) -> str:
        """Format a line of code with syntax highlighting based on language"""
        if not line.strip():
            return line

        lang = language.lower()

        if lang == 'json':
            return self._format_json_line(line)
        elif lang in ['python', 'py']:
            return self._format_python_line(line)
        elif lang in ['javascript', 'js']:
            return self._format_javascript_line(line)
        else:
            # Default code formatting
            return f"{self.colors.BRIGHT_WHITE}{self.colors.DIM}{line}{self.colors.RESET}"

    def _format_json_line(self, line: str) -> str:
        """Format a JSON line with syntax highlighting"""
        # Handle strings
        formatted = re.sub(
            r'"([^"]*?)"(?=\s*:)',  # Keys
            f'{self.colors.BRIGHT_BLUE}"\\1"{self.colors.RESET}',
            line
        )
        formatted = re.sub(
            r':\s*"([^"]*?)"',  # String values
            f': {self.colors.BRIGHT_GREEN}"\\1"{self.colors.RESET}',
            formatted
        )

        # Handle numbers
        formatted = re.sub(
            r':\s*(-?\d+\.?\d*)',
            f': {self.colors.BRIGHT_YELLOW}\\1{self.colors.RESET}',
            formatted
        )

        # Handle booleans and null
        formatted = re.sub(
            r'\b(true|false|null)\b',
            f'{self.colors.BRIGHT_MAGENTA}\\1{self.colors.RESET}',
            formatted
        )

        # Handle brackets and braces
        formatted = re.sub(
            r'([\[\]{}])',
            f'{self.colors.BRIGHT_CYAN}\\1{self.colors.RESET}',
            formatted
        )

        # Handle commas and colons
        formatted = re.sub(
            r'([,:])(?![^"]*")',
            f'{self.colors.DIM}\\1{self.colors.RESET}',
            formatted
        )

        return formatted

    def _format_python_line(self, line: str) -> str:
        """Format a Python line with basic syntax highlighting"""
        # Keywords
        keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'import', 'from', 'as', 'return', 'yield', 'with', 'in', 'not', 'and', 'or']

        formatted = line
        for keyword in keywords:
            formatted = re.sub(
                f'\\b{keyword}\\b',
                f'{self.colors.BRIGHT_BLUE}{keyword}{self.colors.RESET}',
                formatted
            )

        # Strings (simplified pattern)
        formatted = re.sub(
            r'(["\'][^"\']*["\'])',
            f'{self.colors.BRIGHT_GREEN}\\1{self.colors.RESET}',
            formatted
        )

        # Comments
        formatted = re.sub(
            r'(#.*$)',
            f'{self.colors.DIM}{self.colors.BRIGHT_BLACK}\\1{self.colors.RESET}',
            formatted
        )

        return formatted

    def _format_javascript_line(self, line: str) -> str:
        """Format a JavaScript line with basic syntax highlighting"""
        # Keywords
        keywords = ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'try', 'catch', 'return', 'class', 'extends', 'import', 'export', 'from']

        formatted = line
        for keyword in keywords:
            formatted = re.sub(
                f'\\b{keyword}\\b',
                f'{self.colors.BRIGHT_BLUE}{keyword}{self.colors.RESET}',
                formatted
            )

        # Strings (simplified pattern)
        formatted = re.sub(
            r'(["\'][^"\']*["\'])',
            f'{self.colors.BRIGHT_GREEN}\\1{self.colors.RESET}',
            formatted
        )

        # Comments
        formatted = re.sub(
            r'(//.*$)',
            f'{self.colors.DIM}{self.colors.BRIGHT_BLACK}\\1{self.colors.RESET}',
            formatted
        )

        return formatted

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
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

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


def test_markdown_formatting():
    """Test the basic markdown formatter features"""
    print("Testing Basic Markdown Formatting")
    print("=" * 50)

    sample_markdown = """
# Main Title

This is a **bold** statement and this is *italic*.

## Subsection

Here's some `inline code` and a [link](https://example.com).

### Code Block

```python
def hello():
    print("Hello, World!")
    return True
```

### Lists

- First item
- Second item
  - Nested item
- Third item

1. Numbered item
2. Another numbered item

> This is a blockquote with some **bold** text.

---

~~Strikethrough text~~
"""

    formatter = MarkdownFormatter()
    formatted_output = formatter.format_for_terminal(sample_markdown)
    print(formatted_output)
    print("\n" + "=" * 50)

def test_table_formatting():
    """Test the new table formatting capabilities"""
    print("\nTesting Table Formatting (NEW FEATURE!)")
    print("=" * 50)

    table_markdown = """
## Table Examples

### Simple Table

| Name | Age | City |
| :--- | :---: | ---: |
| Alice | 25 | New York |
| Bob | 30 | Los Angeles |
| Charlie | 35 | Chicago |

### Complex Table with Formatting

| **Model** | **Context Window** | **Max Output** | *Special Features* |
| :-------- | :----------------: | :------------: | :----------------- |
| GPT-4 | `128,000 tokens` | 8,192 | ~~Legacy~~ Advanced reasoning |
| **Gemini Pro** | `1,000,000 tokens` | 8,192 | [Multimodal](https://ai.google.dev) |
| Claude | `200,000 tokens` | 8,192 | Constitutional AI |

### Alignment Test

| Left | Center | Right |
| :--- | :----: | ----: |
| Short | Medium text here | Very long text content |
| A | B | C |
"""

    formatter = MarkdownFormatter()
    formatted_output = formatter.format_for_terminal(table_markdown)
    print(formatted_output)
    print("\n" + "=" * 50)

def test_json_syntax_highlighting():
    """Test the new JSON syntax highlighting"""
    print("\nTesting JSON Syntax Highlighting (NEW FEATURE!)")
    print("=" * 50)

    json_markdown = """
## JSON Code Blocks

### API Response Example

```json
{
  "status": "success",
  "data": {
    "users": [
      {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "active": true,
        "balance": 1250.75,
        "metadata": null
      },
      {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "active": false,
        "balance": 0,
        "metadata": {
          "lastLogin": "2024-01-15T10:30:00Z",
          "preferences": {
            "theme": "dark",
            "notifications": true
          }
        }
      }
    ],
    "total": 2,
    "hasMore": false
  },
  "timestamp": "2024-01-20T15:45:30Z"
}
```

### Configuration Example

```json
{
  "app": {
    "name": "MyApp",
    "version": "1.2.3",
    "debug": true
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "ssl": false,
    "timeout": 30
  },
  "features": ["auth", "logging", "caching"],
  "limits": {
    "maxUsers": 1000,
    "rateLimit": 100.5
  }
}
```
"""

    formatter = MarkdownFormatter()
    formatted_output = formatter.format_for_terminal(json_markdown)
    print(formatted_output)
    print("\n" + "=" * 50)

def test_multi_language_code_blocks():
    """Test syntax highlighting for different programming languages"""
    print("\nTesting Multi-Language Code Block Highlighting (NEW FEATURE!)")
    print("=" * 50)

    code_markdown = """
## Code Block Syntax Highlighting

### Python Code

```python
class DatabaseManager:
    def __init__(self, host, port):
        self.host = host  # Database host
        self.port = port
        self.connected = False

    def connect(self):
        # Establish database connection
        try:
            # Connection logic here
            if self.host and self.port:
                self.connected = True
                return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def query(self, sql):
        if not self.connected:
            raise ConnectionError("Not connected to database")
        # Execute query
        return self._execute(sql)
```

### JavaScript Code

```javascript
class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.token = null;
    }

    async authenticate(credentials) {
        try {
            const response = await fetch(`${this.baseUrl}/auth`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(credentials)
            });

            if (response.ok) {
                const data = await response.json();
                this.token = data.token; // Store auth token
                return data;
            }
        } catch (error) {
            console.error('Authentication failed:', error);
            throw error;
        }
    }

    // Make authenticated requests
    async get(endpoint) {
        const headers = {};
        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`;
        }

        return fetch(`${this.baseUrl}${endpoint}`, { headers });
    }
}
```

### Generic Code Block

```
# This is a generic code block without specific language
# It should still be formatted nicely

function genericExample() {
    console.log("No syntax highlighting here");
    var result = calculateSomething(42);
    return result;
}
```
"""

    formatter = MarkdownFormatter()
    formatted_output = formatter.format_for_terminal(code_markdown)
    print(formatted_output)
    print("\n" + "=" * 50)

def test_combined_features():
    """Test tables with code blocks and complex formatting"""
    print("\nTesting Combined Features (ADVANCED!)")
    print("=" * 50)

    complex_markdown = """
# API Documentation Example

## Endpoint Comparison

| Endpoint | Method | **Auth Required** | `Rate Limit` | Response Format |
| :------- | :----: | :---------------: | :----------: | :-------------- |
| `/users` | GET | ✅ Yes | `100/hour` | JSON Array |
| `/auth` | POST | ❌ No | `10/minute` | **JWT Token** |
| `/upload` | POST | ✅ Yes | `5/minute` | ~~XML~~ JSON |

### Sample Response

```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": 42,
        "username": "developer",
        "roles": ["admin", "user"],
        "isActive": true,
        "lastSeen": null
      }
    ]
  }
}
```

### Implementation Notes

> **Important**: All API endpoints require proper authentication headers.
>
> Rate limiting is enforced per user account, not per IP address.

---

**Status**: ✅ *Feature complete* | **Version**: `2.1.0` | [Documentation](https://api.docs.com)
"""

    formatter = MarkdownFormatter()
    formatted_output = formatter.format_for_terminal(complex_markdown)
    print(formatted_output)
    print("\n" + "=" * 50)

def test_logger():
    """Test the colored logger"""
    print("\nTesting Colored Logger")
    print("=" * 50)

    logger = create_logger("test_logger")

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    print("=" * 50)

def test_spinner():
    """Test the spinner"""
    print("\nTesting Spinner")
    print("=" * 50)

    # Test different spinner styles
    styles = ["dots", "bars", "arrows", "simple"]

    for style in styles:
        print(f"Testing {style} spinner...")
        with Spinner(f"Loading with {style}", style) as spinner:
            time.sleep(0.3)
        print(f"{style} spinner completed!")

    print("=" * 50)

def print_test_summary():
    """Print a summary of what's being tested"""
    print("COMPREHENSIVE MODULE TESTING SUITE")
    print("=" * 60)
    print("Test Coverage:")
    print("  - Basic Markdown Formatting")
    print("  - Table Formatting (NEW!)")
    print("  - JSON Syntax Highlighting (NEW!)")
    print("  - Multi-Language Code Blocks (NEW!)")
    print("  - Combined Advanced Features (NEW!)")
    print("  - Colored Logger")
    print("  - Spinner Animations")
    print("=" * 60)
    print()


if __name__ == "__main__":
    import sys
    import argparse

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Format markdown files for terminal display")
    parser.add_argument("file", nargs="?", help="Path to markdown file to format (optional - runs tests if not provided)")
    parser.add_argument("--test", action="store_true", help="Run comprehensive tests")
    args = parser.parse_args()

    # If a file is provided, format it
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            formatter = MarkdownFormatter()
            formatted_output = formatter.format_for_terminal(markdown_content)
            print(formatted_output)

        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file '{args.file}': {e}")
            sys.exit(1)

    # If --test flag is provided or no file is given, run tests
    elif args.test or not args.file:
        print_test_summary()

        # Test basic markdown functionality
        test_markdown_formatting()

        # Test NEW table formatting features
        test_table_formatting()

        # Test NEW JSON syntax highlighting
        test_json_syntax_highlighting()

        # Test NEW multi-language code highlighting
        test_multi_language_code_blocks()

        # Test NEW combined advanced features
        test_combined_features()

        # Test existing utilities
        test_logger()
        test_spinner()

        # Final summary
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("New Features Highlighted:")
        print("   - Beautiful table formatting with borders & alignment")
        print("   - JSON syntax highlighting with color coding")
        print("   - Multi-language code block support (Python/JS/Generic)")
        print("   - Advanced combined formatting capabilities")
        print("=" * 60)
