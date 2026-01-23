"""Result pattern for consistent error handling across the LLM system.

Following the railway-oriented programming pattern used in the MCP server.
"""

from typing import Any, Optional


def success_result(data: Any) -> dict[str, Any]:
    """Create a success result with data.

    Args:
        data: The successful result data

    Returns:
        A dictionary with success=True and the data
    """
    return {"success": True, "data": data, "error": None}


def error_result(message: str, metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Create an error result with message and optional metadata.

    Args:
        message: Error message describing what went wrong
        metadata: Optional additional error context

    Returns:
        A dictionary with success=False and error details
    """
    result = {"success": False, "data": None, "error": message}
    if metadata:
        result.update(metadata)
    return result
