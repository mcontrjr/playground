# Local AI Agent

A lightweight Python-based AI agent that interfaces with Ollama's llama3.2:1b model for local AI interactions.

## Features

- 🤖 Interactive chat interface
- 💾 Conversation persistence (save/load)
- 🔧 Configurable system prompts
- 📊 Model management
- 🎯 Single-shot queries
- 🔍 Status monitoring

## Prerequisites

- Python 3.7+
- Ollama installed and running
- llama3.2:1b model pulled in Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull llama3.2:1b

# Start Ollama service
ollama serve
```

## Installation

```bash
# Clone and setup
git clone <this-repo>
cd ollama

# Install dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x cli.py
```

## Usage

### Interactive Chat
```bash
# Start interactive chat
python cli.py chat

# With custom system prompt
python cli.py chat -s "You are a helpful coding assistant"

# With different model
python cli.py --model gemma2:2b chat
```

### Single Questions
```bash
# Ask a single question
python cli.py ask "What is Python?"

# With custom system prompt
python cli.py ask -s "You are a math tutor" "Explain calculus"
```

### Model Management
```bash
# List available models
python cli.py models

# Check system status
python cli.py status
```

### Chat Commands
While in interactive chat mode:
- `/quit` or `/exit` - Exit the program
- `/reset` - Clear conversation history  
- `/help` - Show available commands
- `/save <filename>` - Save conversation to file
- `/load <filename>` - Load conversation from file

## Examples

### Basic Chat
```bash
$ python cli.py chat
🤖 Local Agent initialized with llama3.2:1b
Commands: /quit, /reset, /help, /save, /load

You: Hello! Can you help me with Python?
Assistant: Hello! I'd be happy to help you with Python. What specifically would you like to know about? Whether it's basics, specific concepts, debugging, or anything else Python-related, feel free to ask!

You: /save my_conversation.json
Conversation saved to my_conversation.json
```

### Single Query
```bash
$ python cli.py ask "Write a Python function to calculate fibonacci"
Here's a Python function to calculate Fibonacci numbers:

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# More efficient iterative version:
def fibonacci_iterative(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```
```

### Custom System Prompt
```bash
$ python cli.py chat -s "You are a creative writing assistant who speaks in metaphors"
🤖 Local Agent initialized with llama3.2:1b
Commands: /quit, /reset, /help, /save, /load

You: Help me write a story about courage
Assistant: Courage is like a seed buried deep in winter's frozen ground - it lies dormant until the right moment, when warmth and necessity call it forth...
```

## Configuration

Copy `.env.example` to `.env` and customize:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
SYSTEM_PROMPT=You are a helpful AI assistant.
MAX_HISTORY=10
TEMPERATURE=0.7
TOP_P=0.9
```

## Architecture

- **`agent.py`** - Core LocalAgent class with Ollama integration
- **`cli.py`** - Click-based command-line interface
- **Message/Conversation classes** - Simple conversation management
- **Request handling** - Direct HTTP API calls to Ollama

## Troubleshooting

**"Ollama is not running"**
- Start Ollama: `ollama serve`
- Check if running: `curl http://localhost:11434/api/tags`

**"Model not available"**
- Pull model: `ollama pull llama3.2:1b`
- List models: `ollama list`

**Connection errors**
- Check Ollama host in config
- Verify firewall settings
- Ensure Ollama is accessible on specified port