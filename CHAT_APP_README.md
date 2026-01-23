# TouchDesigner Chat Application

A visual chat interface for TouchDesigner that integrates with Ollama LLM. Type messages directly in TouchDesigner and see AI responses appear as text overlaid on your background.

## Features

- **Keyboard Input**: Type directly in TouchDesigner
- **LLM Integration**: Connects to Ollama for AI responses
- **Non-Blocking**: UI stays responsive during inference (uses threading)
- **Streaming Responses**: See text appear incrementally as AI generates it
- **Configurable Layout**: Easily adjust chat window position, colors, and styling
- **Efficient Rendering**: Uses Specification DAT for optimal performance

## Prerequisites

Before running the chat application:

1. **Background must be set up**
   ```python
   exec(open('c:/ARKHE/Projects/TouchDesigner/Eslem/setup_background_simple.py').read())
   ```

2. **Ollama must be running** with llama3.2 model
   - Install Ollama: https://ollama.com/download
   - Pull model: `ollama pull llama3.2`
   - Verify running: Check http://localhost:11434

## Installation

### Step 1: Run Setup Script

In TouchDesigner's Textport (Alt+T):

```python
exec(open('c:/ARKHE/Projects/TouchDesigner/Eslem/chat_app.py').read())
```

This creates a new container at `/project1/chat_application/` with:
- Keyboard input capture (Keyboard In CHOP)
- Keyboard event handlers (Execute DAT)
- Text rendering system (Python DAT → Table DAT → Text TOP)
- Final composite output (NULL TOP)

### Step 2: View the Output

Navigate to `/project1/chat_application/OUT` and press `1` to view in the viewer.

## Usage

### Basic Chat

1. **Click anywhere in TouchDesigner** to focus the window
2. **Type your message** (you'll see it appear with "> " prefix)
3. **Press ENTER** to send message to LLM
4. **Wait for response** (you'll see "[Thinking...]" then the AI response)

### Keyboard Shortcuts

- **ENTER**: Send message
- **BACKSPACE**: Delete last character
- **ESCAPE**: Clear current input
- **Any letter/number**: Add to input

### Configuration

Custom parameters are available on `/project1/chat_application`:

**Layout**:
- `Chatx`, `Chaty`: Chat window position (pixels)
- `Messagespacing`: Vertical spacing between messages
- `Fontsize`: Font size for all text
- `Maxmessages`: Maximum messages to display

**Colors**:
- `Usercolor`: Color for user messages (default: cyan)
- `Assistantcolor`: Color for AI responses (default: white)
- `Systemcolor`: Color for system messages (default: gray)

**LLM Settings**:
- `Ollamamodel`: Model name (default: "llama3.2")
- `Streamingenabled`: Enable streaming responses (default: True)
- `Maxtokens`: Max tokens per response (default: 512)
- `Temperature`: Creativity level 0-1 (default: 0.7)

## File Structure

```
c:\ARKHE\Projects\TouchDesigner\Eslem\
├── chat_app.py              # Main setup script
├── chat_manager.py          # Core chat state management
├── chat_llm_worker.py       # Threading for non-blocking LLM
├── chat_config.py           # Configuration constants
└── llm/                     # LLM integration package (already exists)
```

## Architecture

### TouchDesigner Network

```
/project1/chat_application/
├── keyboard_in              # Captures keyboard events
├── keyboard_callbacks       # Handles key press callbacks
├── chat_spec_generator      # Generates text specification table
├── chat_spec_table          # Table DAT with text positions/colors
├── chat_display             # Text TOP rendering all messages
└── OUT                      # Final composite output
```

### Data Flow

```
User types → Keyboard CHOP
          → Execute DAT callback
          → ChatManager updates state
          → Python DAT generates spec
          → Table DAT updates
          → Text TOP renders
          → Composited over background
```

### Threading Architecture

LLM calls happen in background threads to prevent UI freezing:

1. User presses ENTER → `ChatManager.submit_input()`
2. ChatManager spawns `ChatLLMWorker` thread
3. Worker calls `llm_interface.send_message_stream()` in background
4. Response chunks call callbacks to update ChatManager
5. ChatManager updates message list (thread-safe)
6. UI re-renders via Python DAT cook

## Troubleshooting

### "Error initializing LLM"

**Problem**: LLM package not found or Ollama not running

**Solutions**:
- Verify Ollama is running: http://localhost:11434
- Check model is pulled: `ollama list` should show llama3.2
- Verify llm/ directory exists at `c:/ARKHE/Projects/TouchDesigner/Eslem/llm/`

### No text appears when typing

**Problem**: Keyboard CHOP not capturing input

**Solutions**:
- Click anywhere in TouchDesigner window to focus
- Check keyboard_in CHOP is active (green flag)
- Verify keyboard_callbacks Execute DAT is monitoring keyboard_in

### "[Thinking...]" stays forever

**Problem**: LLM call failed or is taking very long

**Solutions**:
- Check Ollama is responding: `curl http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"test"}'`
- Check console for error messages
- Try restarting Ollama service
- Increase timeout in chat_llm_worker.py if needed

### Text rendering looks wrong

**Problem**: Specification DAT format incorrect

**Solutions**:
- Check chat_spec_table DAT has columns: x, y, text, fontsize, fontcolorr, fontcolorg, fontcolorb
- Verify Python DAT is cooking (check for errors)
- Force cook Python DAT manually
- Check ChatManager is initialized (look for "[Error initializing...]" message)

### Multiple responses to same message

**Problem**: Thread not preventing concurrent requests

**Solutions**:
- Check `is_waiting_response` flag is working
- Look for "[Already waiting for response...]" system message
- Only one request should be active at a time

## Advanced Customization

### Change Chat Window Position

Edit parameters on `/project1/chat_application`:
- `Chatx`: X position (0 = left edge)
- `Chaty`: Y position (0 = bottom edge)

Or edit [chat_config.py](chat_config.py):
```python
CHAT_CONFIG = {
    "chat_x": 100,     # Change this
    "chat_y": 800,     # Change this
    ...
}
```

### Change Colors

Edit parameters or modify [chat_config.py](chat_config.py):
```python
CHAT_CONFIG = {
    "user_color": (0.2, 0.8, 1.0),       # RGB 0-1
    "assistant_color": (1.0, 1.0, 1.0),
    ...
}
```

### Use Different LLM Model

Change `Ollamamodel` parameter to any Ollama model:
- llama3.2 (default)
- llama3.2:1b (smaller, faster)
- codellama (for code generation)
- mistral (alternative model)

Make sure to pull the model first: `ollama pull <model-name>`

### Disable Streaming

Set `Streamingenabled` parameter to False. Responses will appear all at once instead of incrementally.

## Performance Notes

- **Specification DAT**: Uses 1 Text TOP instead of 20+ for efficiency
- **Threading**: Prevents UI freezes during LLM inference
- **Message Trimming**: Automatically removes old messages beyond `max_messages`
- **Background Thread**: Daemon thread auto-cleans up on TD exit

## Integration with Existing Project

The chat application is completely separate from your existing face tracking pipeline. To composite them together:

```python
# Create a composite TOP
comp = op('/project1').create(compositeTOP, 'final_composite')

# Layer 1: Background
comp.par.operand = 'background_simple/OUT'

# Layer 2: Chat
comp.appendLayer('chat_application/OUT')

# Layer 3: Woman character (if you have this)
comp.appendLayer('woman_render/OUT')
```

## API Reference

### ChatManager

**Methods**:
- `initialize_llm()`: Initialize LLM connection
- `append_to_input(char)`: Add character to input buffer
- `backspace_input()`: Remove last character
- `clear_input()`: Clear input buffer
- `submit_input()`: Send message to LLM
- `add_user_message(text)`: Add user message
- `add_assistant_message(text)`: Add AI response
- `add_system_message(text)`: Add system message
- `get_display_messages()`: Get all messages for rendering

**Attributes**:
- `messages`: List of Message objects
- `current_input`: Current input buffer text
- `is_waiting_response`: Whether waiting for LLM response

### Message

**Attributes**:
- `role`: "user", "assistant", "input", or "system"
- `text`: Message content
- `timestamp`: Unix timestamp
- `y_position`: Y coordinate for rendering (calculated)

## Notes

- Conversation history is automatically saved on shutdown via the LLM package
- Logs are saved to `llm/conversation_logs/`
- Maximum context is managed by the LLM package (older messages truncated)
- Threading is critical - never remove it or UI will freeze
- Background must exist before running chat_app.py

## Support

If you encounter issues:
1. Check console/Textport for error messages
2. Verify all prerequisites are met
3. Try running components individually
4. Check TouchDesigner version compatibility

---

Created for TouchDesigner with Ollama LLM integration
