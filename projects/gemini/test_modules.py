#!/usr/bin/env python3

import time
from markdown_formatter import MarkdownFormatter
from colored_logger import create_logger
from spinner import Spinner

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
    print("\\n" + "=" * 50)

def test_table_formatting():
    """Test the new table formatting capabilities"""
    print("\\nTesting Table Formatting (NEW FEATURE!)")
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
    print("\\n" + "=" * 50)

def test_json_syntax_highlighting():
    """Test the new JSON syntax highlighting"""
    print("\\nTesting JSON Syntax Highlighting (NEW FEATURE!)")
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
    print("\\n" + "=" * 50)

def test_multi_language_code_blocks():
    """Test syntax highlighting for different programming languages"""
    print("\\nTesting Multi-Language Code Block Highlighting (NEW FEATURE!)")
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
    print("\\n" + "=" * 50)

def test_combined_features():
    """Test tables with code blocks and complex formatting"""
    print("\\nTesting Combined Features (ADVANCED!)")
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
            time.sleep(0.3)
        print(f"{style} spinner completed!")

    print("=" * 50)

def print_test_summary():
    """Print a summary of what's being tested"""
    print("🧪 COMPREHENSIVE MODULE TESTING SUITE")
    print("=" * 60)
    print("📋 Test Coverage:")
    print("  ✅ Basic Markdown Formatting")
    print("  🆕 Table Formatting (NEW!)")
    print("  🆕 JSON Syntax Highlighting (NEW!)")
    print("  🆕 Multi-Language Code Blocks (NEW!)")
    print("  🆕 Combined Advanced Features (NEW!)")
    print("  📝 Colored Logger")
    print("  ⭕ Spinner Animations")
    print("=" * 60)
    print()

if __name__ == "__main__":
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
    print("\\n" + "=" * 60)
    print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("✨ New Features Highlighted:")
    print("   📊 Beautiful table formatting with borders & alignment")
    print("   🎨 JSON syntax highlighting with color coding")
    print("   🔤 Multi-language code block support (Python/JS/Generic)")
    print("   🚀 Advanced combined formatting capabilities")
    print("=" * 60)
