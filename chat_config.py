"""
Chat Application Configuration
All configurable constants for chat layout, colors, and LLM settings
"""

from global_context import GLOBAL_CONTEXT

CHAT_CONFIG = {
    # Layout (pixels) - Uses global resolution settings
    "canvas_width": GLOBAL_CONTEXT.width,   # Canvas width from global context
    "canvas_height": GLOBAL_CONTEXT.height, # Canvas height from global context
    "chat_x": 300,              # Chat window left edge
    "chat_y": 230,              # Chat window top edge (distance from top)
    "message_spacing": 30,      # Vertical spacing between messages
    "font_size": 24,            # Font size for all text
    "max_messages": 15,         # Maximum messages to display (trim older ones)
    "text_width": 800,          # Width for word wrapping

    # Colors (RGB 0-1)
    "user_color": (1.0, 0.0, 0.0),       # Cyan for user messages
    "assistant_color": (1.0, 0.0, 0.0),  # White for assistant messages
    "input_color": (1.0, 0.5, 0.5),      # Gray for current input

    # Behavior
    "input_prefix": "> ",       # Prefix for input line

    # Identity
    "bot_name": "lovebot",                      # AI assistant name
    "user_name": None,                          # User name (determined dynamically)
    "initial_message": "Hello! What is your name?",  # First message from bot

    # LLM Settings
    "ollama_model": "llama3.2",
    "streaming_enabled": True,
    "max_tokens": 512,
    "temperature": 0.7,
}
