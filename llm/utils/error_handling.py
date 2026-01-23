"""Error handling utilities and decorators."""

from functools import wraps
from typing import Any, Callable
from .result import error_result
from .logging import log_message, LogLevel


def handle_service_errors(func: Callable) -> Callable:
    """Decorator to handle errors in service methods.

    Catches exceptions and returns error_result instead of raising.
    Logs the error before returning.

    Args:
        func: The function to wrap

    Returns:
        Wrapped function that returns Result instead of raising
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Error in {func.__name__}: {str(e)}"
            log_message(error_msg, LogLevel.ERROR, {"exception_type": type(e).__name__})
            return error_result(error_msg, {"exception_type": type(e).__name__})

    return wrapper
