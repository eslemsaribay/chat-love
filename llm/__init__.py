"""LLM Integration Package for TouchDesigner.

This package provides a clean, modular architecture for integrating
Llama 3.2 (via llama-cpp-python) with TouchDesigner projects.

Quick Start:
    from llm import initialize_llm, chat, shutdown_llm

    # Initialize with your model
    initialize_llm(
        model_path="llm/models/llama-3.2-3b-instruct.gguf",
        model_config={"n_ctx": 2048, "n_threads": 4}
    )

    # Chat with the model
    response = chat("Hello! What is TouchDesigner?")
    print(response)

    # Shutdown when done
    shutdown_llm()

Advanced Usage:
    from llm import ChatInterface

    # Create a custom chat interface
    chat_interface = ChatInterface(
        model_path="path/to/model.gguf",
        system_instruction="technical"
    )

    # Use the interface
    result = chat_interface.send_message("How do I optimize my network?")
    print(result["data"]["response"])

    # Stream responses
    for chunk in chat_interface.send_message_stream("Explain CHOPs"):
        print(chunk, end="", flush=True)

    # Shutdown
    chat_interface.shutdown()
"""

from .main import (
    initialize_llm,
    get_chat_interface,
    chat,
    shutdown_llm
)
from .api import ChatInterface
from .core.types import ModelConfig, InferenceConfig
from .utils.config import DEFAULT_MODEL_CONFIG, DEFAULT_INFERENCE_CONFIG

__version__ = "1.0.0"

__all__ = [
    "initialize_llm",
    "get_chat_interface",
    "chat",
    "shutdown_llm",
    "ChatInterface",
    "ModelConfig",
    "InferenceConfig",
    "DEFAULT_MODEL_CONFIG",
    "DEFAULT_INFERENCE_CONFIG",
]
