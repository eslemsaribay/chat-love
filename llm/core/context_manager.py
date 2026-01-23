"""Context window management and token budgeting."""

from typing import Optional

from ..utils.logging import log_message, LogLevel


class ContextManager:
    """Manages context window and token budgets.

    Tracks token usage and provides truncation strategies for
    long conversations that exceed the context window.
    """

    def __init__(self, max_context_tokens: int = 2048) -> None:
        """Initialize the context manager.

        Args:
            max_context_tokens: Maximum context window size in tokens
        """
        self._max_context_tokens = max_context_tokens
        self._reserved_tokens = 512  # Reserve for system prompt + completion

    def get_available_tokens(self) -> int:
        """Get the number of tokens available for conversation history.

        Returns:
            Available token count (max - reserved)
        """
        return self._max_context_tokens - self._reserved_tokens

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text.

        This is a simple heuristic approximation. For precise counting,
        use the model's tokenizer directly.

        Args:
            text: The text to estimate tokens for

        Returns:
            Estimated token count (approximately 4 characters per token)
        """
        return len(text) // 4

    def truncate_messages(
        self,
        messages: list[str],
        target_tokens: Optional[int] = None
    ) -> list[str]:
        """Truncate message list to fit within token budget.

        Keeps the most recent messages that fit within the budget.

        Args:
            messages: List of message strings to truncate
            target_tokens: Target token budget (uses available tokens if None)

        Returns:
            Truncated list of messages
        """
        if target_tokens is None:
            target_tokens = self.get_available_tokens()

        # Keep most recent messages that fit within budget
        truncated = []
        current_tokens = 0

        for msg in reversed(messages):
            msg_tokens = self.estimate_tokens(msg)
            if current_tokens + msg_tokens <= target_tokens:
                truncated.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break

        if len(truncated) < len(messages):
            log_message(
                f"Truncated {len(messages) - len(truncated)} messages to fit context",
                LogLevel.INFO
            )

        return truncated

    def set_max_context_tokens(self, max_tokens: int) -> None:
        """Update the maximum context token limit.

        Args:
            max_tokens: New maximum context size
        """
        self._max_context_tokens = max_tokens
        log_message(f"Context window updated to {max_tokens} tokens", LogLevel.INFO)
