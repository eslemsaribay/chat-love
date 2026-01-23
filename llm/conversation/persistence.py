"""Conversation persistence (write-only JSON saving)."""

import json
import time
from pathlib import Path
from typing import Optional

from ..core.types import Message, Result
from ..utils.result import success_result, error_result
from ..utils.logging import log_message, LogLevel


class ConversationPersistence:
    """Handles saving conversation history to JSON files.

    Write-only persistence - saves conversations on shutdown but
    never loads them back (as per requirements).
    """

    def __init__(self, save_directory: str = "./conversation_logs") -> None:
        """Initialize the persistence handler.

        Args:
            save_directory: Directory to save conversation logs
        """
        self._save_directory = Path(save_directory)
        self._save_directory.mkdir(parents=True, exist_ok=True)

    def save_conversation(
        self,
        messages: list[Message],
        session_id: Optional[str] = None
    ) -> Result:
        """Save conversation to a JSON file.

        Args:
            messages: List of messages to save
            session_id: Optional session identifier (generated if None)

        Returns:
            Result with save information or error
        """
        try:
            if session_id is None:
                session_id = f"session_{int(time.time())}"

            filename = f"{session_id}.json"
            filepath = self._save_directory / filename

            conversation_data = {
                "session_id": session_id,
                "timestamp": time.time(),
                "message_count": len(messages),
                "messages": messages
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)

            log_message(f"Conversation saved to {filepath}", LogLevel.INFO)

            return success_result({
                "filepath": str(filepath),
                "message_count": len(messages)
            })

        except Exception as e:
            log_message(f"Error saving conversation: {str(e)}", LogLevel.ERROR)
            return error_result(f"Failed to save conversation: {str(e)}")

    def set_save_directory(self, directory: str) -> None:
        """Update the save directory.

        Args:
            directory: New directory path for saving conversations
        """
        self._save_directory = Path(directory)
        self._save_directory.mkdir(parents=True, exist_ok=True)
        log_message(f"Save directory updated to {directory}", LogLevel.INFO)
