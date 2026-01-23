"""Logging utilities for the LLM system."""

import sys
from enum import Enum
from datetime import datetime
from typing import Optional


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# Global debug flag (can be set via config)
DEBUG_ENABLED = True


def log_message(
    message: str,
    level: LogLevel = LogLevel.INFO,
    context: Optional[dict] = None
) -> None:
    """Log a message with timestamp and level.

    Args:
        message: The message to log
        level: Log severity level
        context: Optional context dictionary for additional info
    """
    # Skip debug messages if debug is disabled
    if level == LogLevel.DEBUG and not DEBUG_ENABLED:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level.value}] {message}"

    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        log_line += f" | {context_str}"

    # Print to stderr for errors, stdout for others
    output = sys.stderr if level == LogLevel.ERROR else sys.stdout
    print(log_line, file=output)


def set_debug_enabled(enabled: bool) -> None:
    """Enable or disable debug logging.

    Args:
        enabled: Whether to enable debug logs
    """
    global DEBUG_ENABLED
    DEBUG_ENABLED = enabled
