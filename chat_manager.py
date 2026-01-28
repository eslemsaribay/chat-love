"""
Chat Manager - Core chat state management
Manages message list, input buffer, positioning, and LLM integration
"""

import time
from typing import List, Optional, Callable, Callable


class Message:
    """Represents a single chat message"""

    def __init__(self, role: str, text: str, timestamp: Optional[float] = None):
        """
        Args:
            role: "user", "assistant", or "input" (current input line)
            text: Message text content
            timestamp: Unix timestamp (defaults to current time)
        """
        self.role = role
        self.text = text
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.y_position = 0  # Calculated by layout manager


class ChatManager:
    """
    Manages chat state: message history, input buffer, positions
    Coordinates with LLM worker threads for responses
    """

    def __init__(self, config: dict, on_update_callback: Optional[Callable[[], None]] = None):
        """
        Args:
            config: Configuration dictionary from chat_config.py
            on_update_callback: Optional callback to trigger display refresh after message updates
        """
        self.config = config
        self.messages: List[Message] = []
        self.current_input = ""
        self.llm_interface = None
        self.llm_worker = None  # Reference to current worker thread
        self.awaiting_username = True  # First message will determine username
        self.on_update_callback = on_update_callback  # Callback for display refresh

    def initialize_llm(self):
        """Initialize LLM from existing llm/ package"""
        try:
            from llm import initialize_llm, get_chat_interface
            initialize_llm(model_path=self.config["ollama_model"])
            self.llm_interface = get_chat_interface()
            print(f"✓ LLM initialized: {self.config['ollama_model']}")
        except Exception as e:
            print(f"ERROR: Failed to initialize LLM: {e}")
            self.llm_interface = None

    def _notify_update(self):
        """Call the update callback if registered (for display refresh after LLM responses)"""
        if self.on_update_callback:
            try:
                self.on_update_callback()
            except Exception as e:
                print(f"Update callback error: {e}")

    def add_initial_message(self):
        """Add the initial bot greeting message"""
        bot_name = self.config["bot_name"]
        initial_msg = self.config["initial_message"]
        self.add_assistant_message(f"{bot_name}: {initial_msg}")

    def reset(self):
        """
        Reset the entire chat state:
        - Clear all messages
        - Clear input buffer
        - Reset username to None
        - Reset awaiting_username flag
        - Clear LLM conversation context
        - Add initial bot greeting
        """
        print("Resetting chat...")

        # Clear local state
        self.messages = []
        self.current_input = ""
        self.config["user_name"] = None
        self.awaiting_username = True

        # Clear LLM conversation context if available
        if self.llm_interface:
            try:
                self.llm_interface.clear_conversation()
                print("  - LLM context cleared")
            except Exception as e:
                print(f"  - Warning: Could not clear LLM context: {e}")

        # Add initial bot greeting
        self.add_initial_message()

        # Trigger display refresh
        self._notify_update()

        print("Chat reset complete!")

    def append_to_input(self, char: str):
        """Add character to current input buffer"""
        self.current_input += char

    def backspace_input(self):
        """Remove last character from input buffer"""
        if self.current_input:
            self.current_input = self.current_input[:-1]

    def clear_input(self):
        """Clear input buffer"""
        self.current_input = ""

    def submit_input(self):
        """
        Submit current input as user message
        Spawn LLM worker thread to get response
        Special handling for first message (username extraction)
        """
        if not self.current_input.strip():
            return  # Don't submit empty messages

        user_text = self.current_input
        self.clear_input()

        # Special handling for first message (username extraction)
        if self.awaiting_username:
            if self.llm_interface:
                self._extract_username(user_text)
            else:
                # Fallback: use raw input as username if LLM not available
                self.config["user_name"] = user_text.strip()
                self.awaiting_username = False
                self.add_user_message(f"{self.config['user_name']}: {user_text}")
                self.add_assistant_message(f"{self.config['bot_name']}: Nice to meet you, {self.config['user_name']}!")
        else:
            # Normal message flow
            self.add_user_message(f"{self.config['user_name']}: {user_text}")

            # Spawn LLM worker thread (if LLM is initialized)
            if self.llm_interface:
                self._spawn_llm_worker(user_text)
            else:
                # Add error message if LLM not available
                self.add_assistant_message(f"{self.config['bot_name']}: [LLM not initialized - check Ollama]")

    def add_user_message(self, text: str):
        """Add user message to history"""
        msg = Message(role="user", text=text)
        self.messages.append(msg)
        self._trim_messages()
        self._recalculate_positions()

    def add_assistant_message(self, text: str):
        """Add assistant message to history"""
        msg = Message(role="assistant", text=text)
        self.messages.append(msg)
        self._trim_messages()
        self._recalculate_positions()

    def update_last_assistant_message(self, text: str):
        """
        Update the last assistant message (for streaming)
        If last message isn't assistant, create new one
        """
        if self.messages and self.messages[-1].role == "assistant":
            self.messages[-1].text = text
        else:
            self.add_assistant_message(text)
        self._recalculate_positions()

    def get_display_messages(self) -> List[Message]:
        """
        Get all messages to display (history + current input)
        Returns list of Messages with calculated positions
        """
        display = list(self.messages)  # Copy

        # Add current input as pseudo-message
        if self.current_input or True:  # Always show input line
            prefix = self.config["input_prefix"]
            input_msg = Message(
                role="input",
                text=f"{prefix}{self.current_input}_"
            )
            # Position will be calculated
            display.append(input_msg)

        # Recalculate positions for all
        self._recalculate_positions_for_list(display)

        return display

    def _recalculate_positions(self):
        """Recalculate Y positions for all messages"""
        # Text TOP coordinates: Y increases upward, so start high and go down
        canvas_height = self.config["canvas_height"]
        y = canvas_height - self.config["chat_y"]  # Start from top
        spacing = self.config["message_spacing"]

        for msg in self.messages:
            msg.y_position = y
            y -= spacing  # Subtract to move down visually

    def _recalculate_positions_for_list(self, messages: List[Message]):
        """Recalculate Y positions for a list of messages"""
        # Text TOP coordinates: Y increases upward, so start high and go down
        canvas_height = self.config["canvas_height"]
        y = canvas_height - self.config["chat_y"]  # Start from top
        spacing = self.config["message_spacing"]

        for msg in messages:
            msg.y_position = y
            y -= spacing  # Subtract to move down visually

    def _trim_messages(self):
        """Remove old messages if exceeding max_messages"""
        max_msgs = self.config["max_messages"]
        if len(self.messages) > max_msgs:
            # Keep most recent messages
            self.messages = self.messages[-max_msgs:]

    def _extract_username(self, user_response: str):
        """
        Extract username from first user response using LLM
        Sends special prompt to extract ONLY the name
        """
        # Import here to avoid circular dependency
        from chat_llm_worker import ChatLLMWorker

        # Special prompt to extract name only
        extraction_prompt = f"""The user responded to "What is your name?" with: "{user_response}"
Extract ONLY the person's name from their response. Output ONLY the name, nothing else.
If they said "My name is John", output: John
If they said "I'm Sarah", output: Sarah
If they just said "Mike", output: Mike
Output ONLY the name:"""

        # Add placeholder message
        self.add_assistant_message("...")

        # Define callbacks
        def on_complete(extracted_name: str, success: bool):
            """Called when name extraction complete"""
            if success and extracted_name.strip():
                # Clean the extracted name (remove any extra text)
                name = extracted_name.strip().split()[0]  # Take first word if multiple
                self.config["user_name"] = name
                self.awaiting_username = False

                # Remove placeholder message
                if self.messages and self.messages[-1].text == "...":
                    self.messages.pop()

                # Add the first user message with extracted name
                self.add_user_message(f"{name}: {user_response}")

                # Add greeting response
                self.add_assistant_message(f"{self.config['bot_name']}: Nice to meet you, {name}!")
            else:
                # Fallback: use raw input if extraction failed
                self.config["user_name"] = user_response.strip()
                self.awaiting_username = False
                self.add_user_message(f"{self.config['user_name']}: {user_response}")
                self.add_assistant_message(f"{self.config['bot_name']}: Nice to meet you!")

            self._notify_update()  # Trigger display refresh after username extraction

        # Spawn worker thread (no streaming for name extraction)
        worker = ChatLLMWorker(
            llm_interface=self.llm_interface,
            user_message=extraction_prompt,
            config=self.config,
            callback=on_complete,
            streaming_callback=None  # No streaming for extraction
        )
        worker.start()
        self.llm_worker = worker

    def _spawn_llm_worker(self, user_message: str):
        """
        Spawn background thread to get LLM response
        Thread will call callbacks when chunks arrive
        """
        # Import here to avoid circular dependency
        from chat_llm_worker import ChatLLMWorker

        bot_name = self.config["bot_name"]

        # Create placeholder message for streaming
        self.add_assistant_message(f"{bot_name}: ...")

        # Define callbacks
        def on_chunk(chunk_text: str, full_text: str):
            """Called when streaming chunk arrives"""
            self.update_last_assistant_message(f"{bot_name}: {full_text}")
            self._notify_update()  # Trigger display refresh

        def on_complete(final_text: str, success: bool):
            """Called when response complete"""
            if success:
                self.update_last_assistant_message(f"{bot_name}: {final_text}")
            else:
                self.update_last_assistant_message(f"{bot_name}: [Error: {final_text}]")
            self._notify_update()  # Trigger display refresh

        # Spawn worker thread
        worker = ChatLLMWorker(
            llm_interface=self.llm_interface,
            user_message=user_message,
            config=self.config,
            callback=on_complete,
            streaming_callback=on_chunk if self.config["streaming_enabled"] else None
        )
        worker.start()
        self.llm_worker = worker
