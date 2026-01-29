"""
Chat Application Configuration
All configurable constants for chat layout, colors, and LLM settings
"""

from global_context import GLOBAL_CONTEXT

CHAT_CONFIG = {
    # Layout (pixels) - Uses global resolution settings
    "canvas_width": GLOBAL_CONTEXT.width,   # Canvas width from global context
    "canvas_height": GLOBAL_CONTEXT.height, # Canvas height from global context
    "chat_x": 280,              # Chat window left edge
    "chat_y": 230,              # Chat window top edge (distance from top)
    "message_spacing": 20,      # Vertical spacing between messages
    "font_size": 16,            # Font size for all text
    "max_messages": 15,         # Maximum messages to display (trim older ones)
    "text_width": 800,          # Width for word wrapping (legacy)

    # Word wrap settings
    "wrap_chars": 80,           # Characters per line before wrapping
    "line_height": 20,          # Pixels between wrapped lines (should match message_spacing)

    # Scrolling settings
    "chat_window_top": 230,     # Top boundary of visible chat area (pixels from top)
    "chat_window_height": 400,  # Visible height of chat area (pixels)
    "scroll_step": 60,          # Pixels to scroll per Page Up/Down (3 lines × 20px)

    # Colors (RGB 0-1)
    "user_color": (0.0, 0.7, 0.0),       # Cyan for user messages
    "assistant_color": (0.0, 0.0, 0.7),  # White for assistant messages
    "input_color": (0.5, 0.0, 0.0),      # Gray for current input

    # Behavior
    "input_prefix": "> ",       # Prefix for input line

    # Identity
    "bot_name": "lovebot",                      # AI assistant name
    "user_name": None,                          # User name (determined dynamically)
    "initial_message": "Hi! What is your name?",  # First message from bot

    # LLM Settings
    "ollama_model": "llama3.2",
    "streaming_enabled": True,
    "max_tokens": 512,
    "temperature": 0.6,
}
