# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Python-based Gemini AI CLI client that provides conversational AI interactions with Google's Gemini models. The project includes two main executables:
- `intro.py` - Interactive Gemini chat client with conversation history and file upload support
- `changelog.py` - AI-powered changelog generator from Git commits

## Environment Setup

**Virtual Environment**: Always use the existing `.venv` virtual environment:
```bash
source .venv/bin/activate
```

**Environment Variables**: Create a `.env` file (never edit existing `.env` files) with:
```
GEMINI_API_KEY=your_api_key_here
```

## Core Commands

### Development Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or install from pyproject.toml
uv pip install -e .
```

### Main Applications
```bash
# Interactive chat with Gemini (basic usage)
python intro.py -c "Your question here"

# Chat with file upload
python intro.py -c "Analyze this file" -f path/to/file.txt

# Clear conversation history
python intro.py --clear

# Enable verbose logging
python intro.py -c "Your question" -v

# Generate changelog from recent Git commits
python changelog.py

# Generate changelog from specific Git range
python changelog.py -r HEAD~5..HEAD

# Use specific Gemini model
python changelog.py -m gemini-2.5-pro

# Show token statistics and cost estimates
python changelog.py --show-stats --show-prompt
```

### Testing
```bash
# Test all markdown formatting features
python markdown_formatter.py

# Test individual modules (no formal test suite exists)
python colored_logger.py
python spinner.py
```

## Architecture Overview

### Core Modules

**`intro.py`** - Main chat client with these key features:
- Persistent conversation history in `conversation_history.json`
- Context window management (16k tokens max by default)
- File upload support with automatic cleanup
- Streaming response display with formatted markdown
- Uses `gemini-2.5-flash` model by default

**`changelog.py`** - Git changelog generator with:
- Automatic model selection based on content size
- Token counting and cost estimation
- Smart content filtering (ignores `.csv`, `.json`, `.log`, `.md`, etc.)
- Optimal prompt construction to fit model context windows
- Support for both `gemini-2.5-flash` and `gemini-2.5-pro`

**`markdown_formatter.py`** - Advanced terminal markdown renderer featuring:
- Syntax highlighting for Python, JavaScript, and JSON
- Table formatting with borders and alignment
- Code block rendering with language detection
- Comprehensive color scheme using ANSI codes
- Inline formatting (bold, italic, links, strikethrough)

**Utility Modules**:
- `colored_logger.py` - Colored console logging with spinner compatibility
- `spinner.py` - Loading animations with multiple styles

### Data Flow

1. **Chat Sessions**: User input → API formatting → Gemini API → Streaming response → Markdown formatting → Terminal display → History storage
2. **Changelog Generation**: Git analysis → File filtering → Token optimization → Model selection → Prompt generation → Formatted output

### Configuration

- **Models**: Primary `gemini-2.5-flash`, fallback `gemini-2.5-pro`
- **Token Limits**: Configurable per model in `MODEL_CONFIGS`
- **File Filtering**: Extensible ignore list in `IGNORE_EXTENSIONS`
- **Context Management**: Automatic trimming when approaching limits

## Development Guidelines

- All scripts are executable and include proper shebang lines
- Error handling includes API cleanup (file deletion after upload)
- Modular design allows individual component testing
- Uses modern Python features (f-strings, type hints, pathlib)
- ANSI color codes provide rich terminal output

## Key Dependencies

- `google-genai` - Primary Gemini API client
- `google-generativeai` - Additional Gemini functionality  
- `python-dotenv` - Environment variable management
- Built with Python 3.12+ requirement

## File Structure Notes

- Entry points: `intro.py` and `changelog.py` (both executable)
- Persistent data: `conversation_history.json` (gitignored)
- Package management: Both `requirements.txt` and `pyproject.toml` present
- Lock file: `uv.lock` indicates use of UV package manager

## # ICONS

- [+] New features
- [*] Modifications  
- [-] Bug fixes
- [!] Breaking changes
- [~] Performance improvements
- [?] Questions/unclear items
