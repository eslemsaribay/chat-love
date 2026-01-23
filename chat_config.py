"""
TouchDesigner Chat Application Configuration
Centralized configuration for chat layout, colors, and LLM settings
"""

CHAT_CONFIG = {
    # Layout (pixels)
    "chat_x": 100,              # Chat window left edge
    "chat_y": 800,              # Chat window top edge (from bottom)
    "message_spacing": 40,      # Vertical spacing between messages
    "font_size": 24,            # Font size for all text
    "max_messages": 20,         # Maximum messages to display

    # Colors (RGB 0-1)
    "user_color": (0.2, 0.8, 1.0),      # Cyan for user messages
    "assistant_color": (1.0, 1.0, 1.0),  # White for assistant responses
    "system_color": (0.8, 0.8, 0.8),     # Gray for system messages

    # Behavior
    "input_prefix": "> ",       # Prefix for input line
    "auto_scroll": True,        # Auto-scroll to latest message

    # LLM Settings
    "ollama_model": "llama3.2",
    "streaming_enabled": True,  # Use streaming for incremental display
    "max_tokens": 512,
    "temperature": 0.7,
}
