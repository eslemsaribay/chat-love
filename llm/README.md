# LLM Integration for TouchDesigner

A clean, modular Python architecture for integrating Llama 3.2 (via Ollama) with TouchDesigner projects.

## Features

- **Clean Architecture**: Protocol-based interfaces, Result pattern, proper separation of concerns
- **Simple Setup**: Uses Ollama for hassle-free local LLM deployment (no compilation needed)
- **Conversation Management**: Automatic context window management with message history
- **Multiple System Instructions**: Built-in templates (default, technical, creative, minimal)
- **Streaming Support**: Both streaming and non-streaming generation modes
- **Persistence**: Automatic conversation saving to JSON on shutdown
- **TD-Agnostic**: Clean API that can be easily integrated with TouchDesigner components

## Installation

### 1. Install Ollama

Download and install Ollama from: https://ollama.com/download

After installation, Ollama runs as a background service.

### 2. Pull Llama 3.2 Model

Open a terminal and run:

```bash
ollama pull llama3.2
```

Or for the 3B parameter version (faster, smaller):
```bash
ollama pull llama3.2:3b
```

To verify it's working:
```bash
ollama run llama3.2
```

Type a message to test, then exit with `/bye`

### 3. Install Python Dependencies

```bash
cd c:\ARKHE\Projects\TouchDesigner\Eslem\llm
pip install -r requirements.txt
```

This only installs `requests` and `typing-extensions` - no compilation needed!

## Quick Start

### Simple Usage

```python
from llm import initialize_llm, chat, shutdown_llm

# Initialize with Ollama model
initialize_llm(model_path="llama3.2")

# Chat with the model
response = chat("Hello! What is TouchDesigner?")
print(response)

# Continue the conversation
response = chat("Can you help me with Python scripting in TD?")
print(response)

# Shutdown (saves conversation)
shutdown_llm()
```

### Advanced Usage

```python
from llm import ChatInterface

# Create a custom chat interface
chat_interface = ChatInterface(
    model_path="llama3.2",  # or "llama3.2:3b" for smaller model
    model_config={"n_ctx": 2048},
    system_instruction="technical"  # Use technical assistant mode
)

# Send a message
result = chat_interface.send_message("How do I optimize my network?")
if result["success"]:
    print(result["data"]["response"])
    print(f"Tokens used: {result['data']['tokens_used']}")

# Stream responses
print("Streaming response:")
for chunk in chat_interface.send_message_stream("Explain CHOPs in detail"):
    print(chunk, end="", flush=True)
print()

# Custom inference config
result = chat_interface.send_message(
    "Create a simple feedback loop",
    config={
        "max_tokens": 256,
        "temperature": 0.8,
        "top_p": 0.95
    }
)

# Get conversation info
info = chat_interface.get_conversation_info()
print(f"Total messages: {info['message_count']}")

# Clear conversation if needed
chat_interface.clear_conversation()

# Shutdown (saves conversation)
chat_interface.shutdown()
```

## Configuration

### Model Configuration

```python
model_config = {
    "n_ctx": 2048,  # Context window size
}
```

Note: GPU layers, threads, and other low-level options are managed by Ollama automatically.

### Inference Configuration

```python
inference_config = {
    "max_tokens": 512,         # Maximum tokens to generate
    "temperature": 0.7,        # Sampling temperature (0.0 = deterministic)
    "top_p": 0.95,            # Nucleus sampling threshold
    "top_k": 40,              # Top-k sampling
    "repeat_penalty": 1.1,    # Penalty for repeating tokens
    "stop": ["User:", "Human:"]  # Stop sequences
}
```

### System Instruction Templates

Available templates:
- `"default"` - General helpful assistant for TouchDesigner
- `"technical"` - Python scripting and technical guidance
- `"creative"` - Creative partner for interactive media projects
- `"minimal"` - Brief, concise responses

```python
# Change template during initialization
chat_interface = ChatInterface(
    model_path="llama3.2",
    system_instruction="technical"
)

# Or change it later
chat_interface.set_system_instruction("creative")
```

## Available Ollama Models

You can use any model available in Ollama. Popular options:

- `llama3.2` - Latest Llama 3.2 (default, ~8B params)
- `llama3.2:3b` - Smaller, faster Llama 3.2 (3B params)
- `llama3.1` - Llama 3.1 (larger context window)
- `mistral` - Mistral 7B (fast and capable)
- `codellama` - Code-focused model

To use a different model:
```python
initialize_llm(model_path="mistral")
```

List all available models:
```bash
ollama list
```

## Architecture

```
llm/
├── core/                          # Core LLM functionality
│   ├── ollama_model_manager.py    # Model lifecycle management (Ollama)
│   ├── ollama_inference_engine.py # Inference execution (Ollama API)
│   ├── context_manager.py         # Context window management
│   └── types.py                   # Type definitions & protocols
│
├── conversation/                  # Conversation management
│   ├── conversation_manager.py    # Message history
│   ├── prompt_builder.py          # System prompts
│   └── persistence.py             # JSON persistence
│
├── prompts/                       # Prompt templates
│   ├── system_instructions.py
│   └── examples.py
│
├── utils/                         # Utilities
│   ├── result.py                  # Result pattern
│   ├── logging.py                 # Logging utilities
│   ├── error_handling.py          # Error decorators
│   └── config.py                  # Configuration
│
└── api/                           # Public API
    └── chat_interface.py          # Main interface
```

## TouchDesigner Integration

The ChatInterface is designed to be easily integrated with TouchDesigner:

```python
# In TouchDesigner Python script
import sys
sys.path.append("c:/ARKHE/Projects/TouchDesigner/Eslem")

from llm import initialize_llm, chat, get_chat_interface

# Initialize on project load
def onProjectLoad():
    initialize_llm(model_path="llama3.2")

# Use in callbacks or scripts
def onMessage(user_input):
    response = chat(user_input)
    # Connect response to Text DAT or other TD component
    op('text1').text = response

# Shutdown on project close
def onProjectClose():
    from llm import shutdown_llm
    shutdown_llm()
```

### Example: Connect to Text DAT

```python
# In a Text DAT with Python enabled
import sys
sys.path.append("c:/ARKHE/Projects/TouchDesigner/Eslem")
from llm import initialize_llm, chat

# Initialize once
if not hasattr(me, 'llm_initialized'):
    initialize_llm("llama3.2")
    me.llm_initialized = True

# Get response
user_input = parent().par.Userinput.eval()
response = chat(user_input)

# Return for Text DAT display
return response
```

## Conversation Persistence

Conversations are automatically saved to JSON on shutdown:

```json
{
  "session_id": "session_1706123456",
  "timestamp": 1706123456.789,
  "message_count": 10,
  "messages": [
    {
      "role": "user",
      "content": "Hello!",
      "timestamp": 1706123450.123
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": 1706123452.456
    }
  ]
}
```

Logs are saved to `conversation_logs/` directory (write-only, never loaded back).

## Performance Tips

1. **Model Size**: Use `llama3.2:3b` for faster responses, `llama3.2` for better quality
2. **Context Window**: Larger context windows (`n_ctx`) allow longer conversations but use more memory
3. **Temperature**: Lower temperature (0.1-0.3) for more focused/deterministic responses
4. **Ollama Settings**: Ollama automatically manages GPU acceleration and threading

## Troubleshooting

### "Could not connect to Ollama"

```
Error: Could not connect to Ollama at http://localhost:11434
```

**Solution**: Make sure Ollama is running. It should start automatically after installation. If not:
- Windows: Start Ollama from the Start Menu
- Check if it's running: Open browser to http://localhost:11434 (should see "Ollama is running")

### "Model not found in Ollama"

```
Error: Model 'llama3.2' not found in Ollama
```

**Solution**: Pull the model first:
```bash
ollama pull llama3.2
```

Check available models:
```bash
ollama list
```

### Slow Inference

- Use a smaller model: `ollama pull llama3.2:3b`
- Reduce `max_tokens` in inference config
- Close other applications to free up RAM/GPU

### Out of Memory

- Use `llama3.2:3b` instead of `llama3.2`
- Reduce `n_ctx` in model config
- Close other applications

## Why Ollama?

Ollama provides several advantages for local LLM deployment:

1. **No Compilation**: No need for C++ build tools or complex setup
2. **Automatic Optimization**: Handles GPU acceleration and threading automatically
3. **Model Management**: Easy model download and switching (`ollama pull`, `ollama list`)
4. **Cross-Platform**: Works on Windows, Mac, and Linux
5. **Memory Efficient**: Loads models on-demand and manages resources intelligently
6. **REST API**: Simple HTTP interface, easy to integrate

## License

This project is part of the Eslem TouchDesigner installation.

## Credits

- Built with [Ollama](https://ollama.com/)
- Designed for [TouchDesigner](https://derivative.ca/)
