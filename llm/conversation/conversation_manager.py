"""Conversation state and history management."""

import time
from typing import Optional

from ..core.types import Message, MessageRole
from ..core.context_manager import ContextManager


class ConversationManager:
    """Manages conversation state and history.

    Maintains a list of messages with timestamps and integrates with
    the context manager for automatic truncation when needed.
    """

    def __init__(self, context_manager: ContextManager) -> None:
        """Initialize the conversation manager.

        Args:
            context_manager: Context manager for token budgeting
        """
        self._messages: list[Message] = []
        self._context_manager = context_manager

    def add_message(self, role: MessageRole, content: str) -> None:
        """Add a message to the conversation history.

        Args:
            role: Message role (system, user, or assistant)
            content: Message content
        """
        message: Message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        self._messages.append(message)

    def get_messages(self) -> list[Message]:
        """Get all messages in the conversation.

        Returns:
            Copy of the message list
        """
        return self._messages.copy()

    def clear_history(self) -> None:
        """Clear all conversation history."""
        self._messages = []

    def get_context_for_inference(self, system_prompt: str = "") -> str:
        """Build the full context string for inference.

        Formats messages and applies truncation if needed to fit
        within the context window.

        Args:
            system_prompt: Optional system prompt to prepend

        Returns:
            Formatted prompt string ready for inference
        """
        # Format messages into a single prompt string
        formatted_messages = []

        if system_prompt:
            formatted_messages.append(f"System: {system_prompt}")

        # Convert messages to text
        message_texts = []
        for msg in self._messages:
            message_texts.append(f"{msg['role'].capitalize()}: {msg['content']}")

        # Truncate if necessary
        truncated = self._context_manager.truncate_messages(message_texts)
        formatted_messages.extend(truncated)

        # Add assistant prefix for completion
        formatted_messages.append("Assistant:")

        return "\n\n".join(formatted_messages)

    def get_message_count(self) -> int:
        """Get the total number of messages.

        Returns:
            Number of messages in the conversation
        """
        return len(self._messages)

    def get_last_message(self) -> Optional[Message]:
        """Get the most recent message.

        Returns:
            The last message or None if conversation is empty
        """
        return self._messages[-1] if self._messages else None
