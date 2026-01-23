"""LLM system configuration."""

from pathlib import Path
from typing import Any

# Enable debug logging
DEBUG = True

# Default model configuration
DEFAULT_MODEL_CONFIG: dict[str, Any] = {
    "n_ctx": 2048,  # Context window size
    "n_gpu_layers": 0,  # Set to > 0 if GPU acceleration available
    "n_threads": 4,  # Number of CPU threads
    "use_mmap": True,  # Use memory mapping
    "use_mlock": False,  # Lock model in RAM
    "verbose": False  # Verbose llama-cpp output
}

# Default inference configuration
DEFAULT_INFERENCE_CONFIG: dict[str, Any] = {
    "max_tokens": 512,  # Maximum tokens to generate
    "temperature": 0.7,  # Sampling temperature (0.0 = deterministic)
    "top_p": 0.95,  # Nucleus sampling threshold
    "top_k": 40,  # Top-k sampling
    "repeat_penalty": 1.1,  # Penalty for repeating tokens
    "stop": ["User:", "Human:"]  # Stop sequences
}

# LLM system configuration
LLM_CONFIG: dict[str, Any] = {
    "default_model_path": "llama3.2",  # Ollama model name (e.g., "llama3.2", "llama3.2:3b")
    "default_model_config": DEFAULT_MODEL_CONFIG,
    "default_inference_config": DEFAULT_INFERENCE_CONFIG,
    "conversation_log_dir": "./conversation_logs",
    "ollama_base_url": "http://localhost:11434"  # Ollama API URL
}
