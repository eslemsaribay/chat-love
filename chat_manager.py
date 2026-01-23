"""
TouchDesigner Chat Manager
Core state management for chat application
"""

import time
from typing import Optional, Callable


class Message:
    """Represents a single chat message"""

    def __init__(self, role: str, text: str, timestamp: float):
        """
        Initialize a message

        Args:
            role: Message role ("user", "assistant", "input", "system")
            text: Message content
            timestamp: Unix timestamp when message was created
        """
        self.role = role
        self.text = text
        self.timestamp = timestamp
        self.y_position = 0  # Calculated by layout manager


class ChatManager:
    """
    Manages chat state, messages, and LLM interaction

    This class is the central coordinator for the chat application:
    - Maintains message history
    - Manages current input buffer
    - Coordinates LLM worker threads
    - Calculates text positions for rendering
    """

    def __init__(self, config: dict):
        """
        Initialize ChatManager

        Args:
            config: Configuration dictionary from chat_config.py
        """
        self.config = config
        self.messages: list[Message] = []
        self.current_input: str = ""
        self.llm_interface = None
        self.llm_worker = None
        self.is_waiting_response = False

    def initialize_llm(self):
        """Initialize LLM using existing llm package"""
        try:
            import sys
            import os

            # Add llm package to path if needed
            script_dir = os.path.dirname(os.path.abspath(__file__))
            llm_path = os.path.join(script_dir, 'llm')
            if llm_path not in sys.path:
                sys.path.insert(0, llm_path)

            # Import and initialize
            from llm import initialize_llm, get_chat_interface

            initialize_llm(model_path=self.config["ollama_model"])
            self.llm_interface = get_chat_interface()

            # Add welcome message
            welcome_msg = Message(
                "system",
                "Chat initialized. Type a message and press ENTER to start.",
                time.time()
            )
            self.messages.append(welcome_msg)
            self._recalculate_positions()

            print("✓ LLM initialized successfully")

        except Exception as e:
            error_msg = Message(
                "system",
                f"[Error initializing LLM: {str(e)}]",
                time.time()
            )
            self.messages.append(error_msg)
            self._recalculate_positions()
            print(f"✗ LLM initialization failed: {e}")

    def append_to_input(self, char: str):
        """
        Add character to current input buffer

        Args:
            char: Single character to append
        """
        self.current_input += char

    def backspace_input(self):
        """Remove last character from input buffer"""
        if self.current_input:
            self.current_input = self.current_input[:-1]

    def clear_input(self):
        """Clear the input buffer"""
        self.current_input = ""

    def submit_input(self):
        """
        Submit current input as user message
        Adds user message to display and triggers LLM response
        """
        if not self.current_input.strip():
            return

        # Add user message
        self.add_user_message(self.current_input)

        # Clear input
        self.current_input = ""

    def add_user_message(self, text: str):
        """
        Add user message and trigger LLM response

        Args:
            text: User message text
        """
        msg = Message("user", text, time.time())
        self.messages.append(msg)
        self._recalculate_positions()

        # Trigger LLM response in background thread
        self._request_llm_response(text)

    def add_assistant_message(self, text: str):
        """
        Add assistant response message

        Args:
            text: Assistant message text
        """
        msg = Message("assistant", text, time.time())
        self.messages.append(msg)
        self._recalculate_positions()
        self._trim_messages()

    def add_system_message(self, text: str):
        """
        Add system message

        Args:
            text: System message text
        """
        msg = Message("system", text, time.time())
        self.messages.append(msg)
        self._recalculate_positions()

    def update_streaming_message(self, text: str):
        """
        Update the last assistant message (for streaming)

        Args:
            text: Updated message text
        """
        if self.messages and self.messages[-1].role == "assistant":
            self.messages[-1].text = text
            self._recalculate_positions()
        else:
            self.add_assistant_message(text)

    def get_display_messages(self) -> list[Message]:
        """
        Get messages for display (including current input)

        Returns:
            List of messages to display
        """
        display_msgs = self.messages.copy()

        # Add current input as temporary message
        if self.current_input:
            input_msg = Message(
                "input",
                self.config["input_prefix"] + self.current_input,
                time.time()
            )
            input_msg.y_position = self._calculate_input_position()
            display_msgs.append(input_msg)

        return display_msgs

    def _recalculate_positions(self):
        """Calculate Y positions for all messages"""
        y = self.config["chat_y"]
        spacing = self.config["message_spacing"]

        # Start from bottom (highest Y), work down
        for msg in reversed(self.messages):
            msg.y_position = y
            y -= spacing

    def _calculate_input_position(self) -> int:
        """
        Calculate Y position for input line

        Returns:
            Y position for input
        """
        if self.messages:
            # Position below last message
            last_y = self.messages[-1].y_position
            return last_y + self.config["message_spacing"]
        else:
            # No messages, use base position
            return self.config["chat_y"]

    def _trim_messages(self):
        """Remove old messages if exceeding max_messages"""
        max_msgs = self.config["max_messages"]
        if len(self.messages) > max_msgs:
            # Keep most recent messages
            self.messages = self.messages[-max_msgs:]
            self._recalculate_positions()

    def _request_llm_response(self, user_message: str):
        """
        Request LLM response in background thread

        Args:
            user_message: User's message to send to LLM
        """
        if self.is_waiting_response:
            self.add_system_message("[Already waiting for response...]")
            return

        if not self.llm_interface:
            self.add_system_message("[Error: LLM not initialized]")
            return

        self.is_waiting_response = True

        # Add "thinking" indicator
        self.add_system_message("[Thinking...]")

        # Start worker thread
        from chat_llm_worker import ChatLLMWorker

        self.llm_worker = ChatLLMWorker(
            self.llm_interface,
            user_message,
            self.config,
            callback=self._on_llm_response,
            streaming_callback=self._on_llm_chunk if self.config["streaming_enabled"] else None
        )
        self.llm_worker.start()

    def _on_llm_chunk(self, chunk: str, full_text: str):
        """
        Callback for streaming LLM chunks

        Args:
            chunk: New chunk of text
            full_text: Complete text so far
        """
        # Remove "thinking" message if it's the last message
        if self.messages and self.messages[-1].role == "system" and "[Thinking...]" in self.messages[-1].text:
            self.messages.pop()

        # Update or create assistant message
        self.update_streaming_message(full_text)

    def _on_llm_response(self, response: str, success: bool):
        """
        Callback when LLM response complete

        Args:
            response: Complete response text or error message
            success: Whether the request succeeded
        """
        self.is_waiting_response = False

        # Remove "thinking" message if it's still there
        if self.messages and self.messages[-1].role == "system" and "[Thinking...]" in self.messages[-1].text:
            self.messages.pop()

        if not success:
            # Add error message
            self.add_system_message(f"[Error: {response}]")
        elif not self.config["streaming_enabled"]:
            # Add complete response (streaming already added it)
            self.add_assistant_message(response)
