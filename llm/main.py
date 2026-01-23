"""LLM Integration Entry Point for TouchDesigner.

This module provides the main initialization and setup for the LLM system.
It exports a simple API that can be easily integrated with TouchDesigner components.
"""

from typing import Optional

from .api.chat_interface import ChatInterface
from .core.types import ModelConfig, InferenceConfig
from .utils.logging import log_message, LogLevel
from .utils.config import LLM_CONFIG

# Global chat interface instance (singleton pattern for TD integration)
_chat_interface: Optional[ChatInterface] = None


def initialize_llm(
    model_path: Optional[str] = None,
    model_config: Optional[ModelConfig] = None,
    system_instruction: str = "default",
    conversation_log_dir: Optional[str] = None
) -> ChatInterface:
    """Initialize the LLM system.

    Args:
        model_path: Path to the GGUF model file
        model_config: Optional model configuration
        system_instruction: System instruction template to use
        conversation_log_dir: Directory for saving conversation logs

    Returns:
        ChatInterface instance ready for use

    Raises:
        ValueError: If no model path provided and no default configured
        RuntimeError: If model fails to load
    """
    global _chat_interface

    if _chat_interface is not None:
        log_message("LLM already initialized", LogLevel.WARNING)
        return _chat_interface

    # Use default model path from config if not provided
    if model_path is None:
        model_path = LLM_CONFIG.get("default_model_path")
        if model_path is None:
            raise ValueError("No model path provided and no default configured")

    # Use default config if not provided
    if model_config is None:
        model_config = LLM_CONFIG.get("default_model_config", {})

    # Use default log directory if not provided
    if conversation_log_dir is None:
        conversation_log_dir = LLM_CONFIG.get("conversation_log_dir", "./conversation_logs")

    log_message(f"Initializing LLM with model: {model_path}", LogLevel.INFO)

    _chat_interface = ChatInterface(
        model_path=model_path,
        model_config=model_config,
        system_instruction=system_instruction,
        conversation_log_dir=conversation_log_dir
    )

    log_message("LLM initialized successfully", LogLevel.INFO)
    return _chat_interface


def get_chat_interface() -> Optional[ChatInterface]:
    """Get the global chat interface instance.

    Returns:
        ChatInterface instance or None if not initialized
    """
    return _chat_interface


def chat(message: str, config: Optional[InferenceConfig] = None) -> str:
    """Simple chat function for quick interactions.

    Args:
        message: User message
        config: Optional inference configuration

    Returns:
        Assistant's response text

    Raises:
        RuntimeError: If LLM not initialized
    """
    if _chat_interface is None:
        raise RuntimeError("LLM not initialized. Call initialize_llm() first.")

    result = _chat_interface.send_message(message, config)

    if result["success"]:
        return result["data"]["response"]
    else:
        raise RuntimeError(f"Chat error: {result['error']}")


def shutdown_llm() -> None:
    """Shutdown the LLM system cleanly.

    Saves the conversation and unloads the model.
    """
    global _chat_interface

    if _chat_interface is not None:
        log_message("Shutting down LLM", LogLevel.INFO)
        _chat_interface.shutdown()
        _chat_interface = None
    else:
        log_message("LLM not initialized, nothing to shutdown", LogLevel.WARNING)


# Public API exports
__all__ = [
    "initialize_llm",
    "get_chat_interface",
    "chat",
    "shutdown_llm",
    "ChatInterface"
]
