#!/usr/bin/env python3

import time
from markdown_formatter import MarkdownFormatter
from colored_logger import create_logger
from spinner import Spinner

def test_markdown_formatting():
    """Test the markdown formatter"""
    print("Testing Markdown Formatting")
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
    print("\\n" + "=" * 50)

def test_logger():
    """Test the colored logger"""
    print("\\nTesting Colored Logger")
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
    print("\\nTesting Spinner")
    print("=" * 50)

    # Test different spinner styles
    styles = ["dots", "bars", "arrows", "simple"]

    for style in styles:
        print(f"Testing {style} spinner...")
        with Spinner(f"Loading with {style}", style) as spinner:
            time.sleep(1)
        print(f"{style} spinner completed!")

    print("=" * 50)

if __name__ == "__main__":
    test_markdown_formatting()
    test_logger()
    test_spinner()
    print("\\nAll tests completed!")
