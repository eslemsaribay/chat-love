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
        self.scroll_offset = 0  # Pixels scrolled (positive = scrolled up to see older messages)
        self.reveal_ready = False  # Set to True when reveal condition is met (logic TBD)

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
        """Add the initial bot greeting message (to both display and LLM context)"""
        bot_name = self.config["bot_name"]
        initial_msg = self.config["initial_message"]
        full_msg = f"{bot_name}: {initial_msg}"

        # Add to display
        self.add_assistant_message(full_msg)

        # Also add to LLM conversation context so it knows what it said
        if self.llm_interface:
            try:
                self.llm_interface._conversation_manager.add_message("assistant", full_msg)
                print(f"[CHAT] Initial message added to LLM context")
            except Exception as e:
                print(f"[CHAT] Warning: Could not add initial message to LLM context: {e}")

    def reset(self):
        """
        Reset the entire chat state:
        - Reload config and LLM prompt modules
        - Clear all messages
        - Clear input buffer
        - Reset username to None
        - Reset awaiting_username flag
        - Clear LLM conversation context
        - Add initial bot greeting
        """
        import sys
        import importlib

        print("[CHAT RESET] Resetting chat state...")

        # Reset debug session so next conversation gets a new file
        try:
            from llm.core.ollama_inference_engine import _reset_debug_session
            _reset_debug_session()
            print("[CHAT RESET] Debug session reset")
        except Exception:
            pass  # Module may not be loaded yet on first run

        # Reload chat config module
        if 'config.chat_config' in sys.modules:
            try:
                importlib.reload(sys.modules['config.chat_config'])
                print("[CHAT RESET] Reloaded: config.chat_config")
            except Exception as e:
                print(f"[CHAT RESET] Warning: Could not reload chat_config: {e}")

        # Update config from reloaded module
        from config.chat_config import CHAT_CONFIG
        self.config.update(CHAT_CONFIG)
        print("[CHAT RESET] Config updated from chat_config.py")

        # Clear local state
        self.messages = []
        self.current_input = ""
        self.config["user_name"] = None
        self.awaiting_username = True
        self.scroll_offset = 0  # Reset scroll position
        self.reveal_ready = False  # Reset reveal state

        # FULL LLM RESET: Destroy singleton and recreate with fresh prompts
        # This ensures prompt modules are reloaded and new ChatInterface is created
        if self.llm_interface:
            try:
                # IMPORTANT: Save conversation and shutdown BEFORE reloading modules
                # Otherwise the module reload resets _chat_interface to None and we lose the reference
                print("[CHAT RESET] Saving conversation and shutting down LLM...")
                shutdown_result = self.llm_interface.shutdown()
                print(f"[CHAT RESET] Shutdown result: {shutdown_result}")

                # Now reload the llm package to pick up any code changes
                if 'llm' in sys.modules:
                    # Reload ALL llm submodules that may have changed
                    reload_modules = [
                        'llm.prompts.system_instructions',
                        'llm.prompts.examples',
                        'llm.utils.result',
                        'llm.utils.error_handling',
                        'llm.utils.logging',
                        'llm.core.types',
                        'llm.core.context_manager',
                        'llm.core.ollama_model_manager',
                        'llm.core.ollama_inference_engine',
                        'llm.conversation.conversation_manager',
                        'llm.conversation.prompt_builder',
                        'llm.conversation.persistence',
                        'llm.api.chat_interface',
                        'llm.main',
                    ]
                    for mod in reload_modules:
                        if mod in sys.modules:
                            importlib.reload(sys.modules[mod])
                            print(f"[CHAT RESET] Reloaded: {mod}")
                    # Reload the package __init__ to update exports
                    importlib.reload(sys.modules['llm'])

                # Re-initialize LLM with fresh modules
                from llm import initialize_llm, get_chat_interface
                initialize_llm(model_path=self.config["ollama_model"])
                self.llm_interface = get_chat_interface()
                print("[CHAT RESET] LLM fully reset with fresh prompts")

                # Verify loaded prompts after reset
                try:
                    from llm.prompts.system_instructions import get_system_instruction
                    from llm.prompts.examples import get_few_shot_examples
                    si = get_system_instruction()
                    ex = get_few_shot_examples()
                    print(f"[CHAT RESET] Verified system_instructions: {len(si)} chars, starts with: '{si[:80]}...'")
                    print(f"[CHAT RESET] Verified examples: {len(ex)} chars, {ex.count('EXAMPLES:') if ex else 0} stages")
                except Exception as ve:
                    print(f"[CHAT RESET] WARNING: Could not verify prompts after reset: {ve}")
            except Exception as e:
                print(f"[CHAT RESET] Warning: Could not reset LLM: {e}")
                import traceback
                traceback.print_exc()

        # Add initial bot greeting
        self.add_initial_message()

        # Trigger display refresh
        self._notify_update()

        print("[CHAT RESET] Chat reset complete!")

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

    def scroll_up(self, pixels: int = None):
        """Scroll up to see older messages (increases scroll offset)"""
        step = pixels or self.config.get("scroll_step", 60)
        max_scroll = self._calculate_max_scroll()
        self.scroll_offset = min(max_scroll, self.scroll_offset + step)

    def scroll_down(self, pixels: int = None):
        """Scroll down to see newer messages (decreases scroll offset)"""
        step = pixels or self.config.get("scroll_step", 60)
        self.scroll_offset = max(0, self.scroll_offset - step)

    def reset_scroll(self):
        """Reset scroll to bottom (most recent messages visible)"""
        self.scroll_offset = 0

    def _calculate_max_scroll(self):
        """Calculate maximum scroll offset (prevents scrolling beyond top of content)"""
        import textwrap

        # Calculate total content height
        wrap_chars = self.config.get("wrap_chars", 50)
        line_height = self.config.get("line_height", 30)

        total_lines = 0
        for msg in self.get_display_messages():
            wrapped = textwrap.wrap(msg.text, width=wrap_chars, break_long_words=True, break_on_hyphens=True) or [msg.text]
            total_lines += len(wrapped)

        total_content_height = total_lines * line_height
        visible_height = self.config.get("chat_window_height", 400)

        # Max scroll is when top of content aligns with top of window
        max_scroll = max(0, total_content_height - visible_height)
        return max_scroll

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

        print(f"[CHAT INPUT] User submitted: '{user_text}'")
        print(f"[CHAT INPUT] awaiting_username={self.awaiting_username}, llm_available={self.llm_interface is not None}")

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
        print(f"[CHAT MSG] Adding user message: '{text}'")
        msg = Message(role="user", text=text)
        self.messages.append(msg)
        self._trim_messages()
        self._recalculate_positions()
        self.reset_scroll()  # Auto-scroll to bottom when new message added

    def add_assistant_message(self, text: str):
        """Add assistant message to history"""
        print(f"[CHAT MSG] Adding assistant message: '{text[:80]}{'...' if len(text) > 80 else ''}'")
        msg = Message(role="assistant", text=text)
        self.messages.append(msg)
        self._trim_messages()
        self._recalculate_positions()
        self.reset_scroll()  # Auto-scroll to bottom when new message added

    def update_last_assistant_message(self, text: str):
        """
        Update the last assistant message (for streaming)
        If last message isn't assistant, create new one
        """
        if self.messages and self.messages[-1].role == "assistant":
            self.messages[-1].text = text
            self._recalculate_positions()
            self.reset_scroll()  # Auto-scroll to bottom during streaming
        else:
            self.add_assistant_message(text)  # This already calls reset_scroll()

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
        Extract username from first user response using LLM.
        LLM returns either:
        - Just the name (e.g., "Berk") if understood
        - "<USERNAME_NOT_FOUND> [message]" if not understood
        """
        # Import here to avoid circular dependency
        from chat_llm_worker import ChatLLMWorker

        # IMPORTANT: Clear LLM conversation context before each extraction attempt
        # This ensures each extraction is independent (no confusion from previous attempts)
        if self.llm_interface:
            try:
                self.llm_interface.clear_conversation()
                print("[USERNAME EXTRACTION] Cleared LLM context for fresh extraction")
            except Exception as e:
                print(f"[USERNAME EXTRACTION] Warning: Could not clear context: {e}")

        # Prompt with clear instructions for name extraction or follow-up
        # Include examples of international names to help with non-English names
        # IMPORTANT: Add explicit "fresh start" instruction to override Ollama's context cache
        extraction_prompt = f"""IMPORTANT: This is a BRAND NEW conversation. Ignore any previous context or names you may remember. You have NO prior knowledge of this user.

The user was JUST asked "What is your name?" and responded with: "{user_response}"

Your task: Extract the user's name ONLY from THIS response (not from any previous memory).

RULES:
1. If you can identify a name (including international names from any culture/language), respond with ONLY the name
2. Single words that could be names should be accepted - names come from many cultures (Turkish, Arabic, Japanese, etc.)
3. If the response is clearly nonsense, gibberish, or a joke (not a plausible name), respond with:
   <USERNAME_NOT_FOUND> [your friendly follow-up question asking for their real name]

EXAMPLES:
- User: "My name is John" → Response: "John"
- User: "I'm Sarah" → Response: "Sarah"
- User: "Call me Mike" → Response: "Mike"
- User: "Berk" → Response: "Berk" (Turkish name)
- User: "Ayşe" → Response: "Ayşe" (Turkish name)
- User: "Kenji" → Response: "Kenji" (Japanese name)
- User: "Mohammed" → Response: "Mohammed" (Arabic name)
- User: "asdfasdf" → Response: "<USERNAME_NOT_FOUND> I didn't quite catch that! What's your name?"
- User: "banana" → Response: "<USERNAME_NOT_FOUND> Haha, that's funny! But seriously, what's your name?"
- User: "12345" → Response: "<USERNAME_NOT_FOUND> That doesn't look like a name. What should I call you?"

Now extract the name from: "{user_response}"
"""

        # Add placeholder message
        self.add_assistant_message("...")

        # Define callback
        NOT_FOUND_TAG = "<USERNAME_NOT_FOUND>"

        def is_valid_name(name: str) -> bool:
            """Check if extracted name looks valid (single word, reasonable length, no gibberish patterns)"""
            name = name.strip()
            # Reject empty
            if not name:
                return False
            # Reject multi-word (names should be single word from extraction)
            if ' ' in name:
                return False
            # Reject too long (names are typically < 20 chars)
            if len(name) > 20:
                return False
            # Reject names with special characters (like <, >, _, etc.)
            # Names should only contain letters and possibly hyphens/apostrophes
            allowed_special = {'-', "'"}
            for char in name:
                if not char.isalpha() and char not in allowed_special:
                    return False
            # Reject if mostly non-alphabetic
            alpha_count = sum(1 for c in name if c.isalpha())
            if alpha_count < len(name) * 0.7:
                return False
            return True

        def on_complete(extracted_response: str, success: bool):
            """Called when name extraction complete"""
            print(f"[USERNAME EXTRACTION] success={success}, response='{extracted_response}'")

            # Handle LLM failure
            if not success or not extracted_response.strip():
                print("[USERNAME EXTRACTION] LLM failed, asking again...")
                # Remove placeholder
                if self.messages and self.messages[-1].text == "...":
                    self.messages.pop()

                # Add the user's message
                self.add_user_message(f"?: {user_response}")

                # Ask again - don't use raw input as username
                self.add_assistant_message(f"{self.config['bot_name']}: Sorry, I didn't catch that. What's your name?")
                # Keep awaiting_username = True
                self._notify_update()
                return

            response = extracted_response.strip()

            # Check for USERNAME_NOT_FOUND tag
            if response.startswith(NOT_FOUND_TAG):
                # Username not understood - extract the follow-up message
                follow_up_message = response[len(NOT_FOUND_TAG):].strip()
                print(f"[USERNAME EXTRACTION] NOT_FOUND, follow-up: '{follow_up_message}'")

                # Remove placeholder message
                if self.messages and self.messages[-1].text == "...":
                    self.messages.pop()

                # Add the user's message (without username prefix since we don't know it yet)
                self.add_user_message(f"?: {user_response}")

                # Add bot's follow-up question
                if follow_up_message:
                    self.add_assistant_message(f"{self.config['bot_name']}: {follow_up_message}")
                else:
                    self.add_assistant_message(f"{self.config['bot_name']}: I didn't quite catch that. What's your name?")

                # Keep awaiting_username = True (don't change it)
            else:
                # Validate the extracted name
                name = response.strip()
                print(f"[USERNAME EXTRACTION] Extracted name: '{name}', valid={is_valid_name(name)}")

                if not is_valid_name(name):
                    # Name looks invalid, ask again
                    print(f"[USERNAME EXTRACTION] Invalid name, asking again...")
                    if self.messages and self.messages[-1].text == "...":
                        self.messages.pop()

                    self.add_user_message(f"?: {user_response}")
                    self.add_assistant_message(f"{self.config['bot_name']}: Hmm, I'm not sure I got your name. Could you tell me again?")
                    # Keep awaiting_username = True
                else:
                    # Username extracted successfully
                    self.config["user_name"] = name
                    self.awaiting_username = False
                    print(f"[USERNAME EXTRACTION] SUCCESS! Username set to: '{name}'")

                    # IMPORTANT: Clear LLM context after successful extraction
                    # This removes the extraction prompt so normal chat starts fresh
                    if self.llm_interface:
                        try:
                            self.llm_interface.clear_conversation()
                            print("[USERNAME EXTRACTION] Cleared LLM context for fresh chat start")

                            # RE-SEED conversation with intro context so LLM remembers the user
                            # Otherwise LLM has no memory of who they're talking to
                            bot_name = self.config['bot_name']
                            initial_msg = self.config.get('initial_message', f"Hi, I'm {bot_name}! What's your name?")

                            # Add to LLM conversation (not display - that's handled separately)
                            # NOTE: Don't include name prefixes here - /api/chat uses
                            # role fields for speaker identity. Adding "Luna:" to assistant
                            # content teaches the model to prefix all its responses with "Luna:".
                            self.llm_interface._conversation_manager.add_message("assistant", initial_msg)
                            self.llm_interface._conversation_manager.add_message("user", user_response)
                            print(f"[USERNAME EXTRACTION] Re-seeded LLM context with intro (2 messages):")
                            print(f"[USERNAME EXTRACTION]   assistant: '{seed_assistant}'")
                            print(f"[USERNAME EXTRACTION]   user: '{seed_user}'")
                        except Exception as e:
                            print(f"[USERNAME EXTRACTION] Warning: Could not clear context: {e}")

                    # Remove placeholder message
                    if self.messages and self.messages[-1].text == "...":
                        self.messages.pop()

                    # Add the user's message with extracted name
                    self.add_user_message(f"{name}: {user_response}")

                    # Spawn LLM to generate a creative opening question
                    # The LLM context is already seeded with the intro, so it knows the user's name
                    self._spawn_llm_worker(f"(You asked the user who they are and they told you their name is {name}. Stay in character and continue the conversation.)")

            self._notify_update()  # Trigger display refresh

        # Spawn worker thread (no streaming for name extraction)
        print(f"[USERNAME EXTRACTION] Spawning LLM worker for name extraction...")
        print(f"[USERNAME EXTRACTION] Extraction prompt ({len(extraction_prompt)} chars):\n{extraction_prompt[:500]}{'...' if len(extraction_prompt) > 500 else ''}")
        worker = ChatLLMWorker(
            llm_interface=self.llm_interface,
            user_message=extraction_prompt,
            config=self.config,
            callback=on_complete,
            streaming_callback=None  # No streaming for extraction
        )
        worker.start()
        self.llm_worker = worker
        print(f"[USERNAME EXTRACTION] Worker started")

    def _spawn_llm_worker(self, user_message: str):
        """
        Spawn background thread to get LLM response
        Thread will call callbacks when chunks arrive
        """
        # Import here to avoid circular dependency
        from chat_llm_worker import ChatLLMWorker

        bot_name = self.config["bot_name"]

        print(f"[LLM REQUEST] Sending to LLM: '{user_message}'")

        # Create placeholder message for streaming
        self.add_assistant_message(f"{bot_name}: ...")

        # Strip bot name prefix if LLM includes it (e.g. "Luna: Hello" -> "Hello")
        def _strip_bot_prefix(text: str) -> str:
            prefix = f"{bot_name}: "
            return text[len(prefix):] if text.startswith(prefix) else text

        REVEAL_TAG = "<REVEAL>"

        def _strip_reveal_tag(text: str) -> str:
            """Strip <REVEAL> prefix from text for display."""
            return text[len(REVEAL_TAG):] if text.startswith(REVEAL_TAG) else text

        def _clean_text(text: str) -> str:
            """Strip all special prefixes for display."""
            return _strip_bot_prefix(_strip_reveal_tag(text))

        # Define callbacks
        def on_chunk(chunk_text: str, full_text: str):
            """Called when streaming chunk arrives"""
            self.update_last_assistant_message(f"{bot_name}: {_clean_text(full_text)}")
            self._notify_update()  # Trigger display refresh

        def on_complete(final_text: str, success: bool):
            """Called when response complete"""
            if success:
                # Check for <REVEAL> signal
                if final_text.startswith(REVEAL_TAG):
                    min_msgs = self.config.get("reveal_min_messages", 7)
                    if len(self.messages) >= min_msgs:
                        self.reveal_ready = True
                        print(f"[REVEAL] Signal detected after {len(self.messages)} messages. reveal_ready = True")
                    else:
                        print(f"[REVEAL] Signal detected but only {len(self.messages)}/{min_msgs} messages. Ignoring.")

                self.update_last_assistant_message(f"{bot_name}: {_clean_text(final_text)}")
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
