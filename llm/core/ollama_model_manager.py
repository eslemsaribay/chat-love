"""Model lifecycle management for Ollama models."""

from typing import Optional
import requests

from .types import ModelConfig, Result
from ..utils.result import success_result, error_result
from ..utils.error_handling import handle_service_errors
from ..utils.logging import log_message, LogLevel


class OllamaModelManager:
    """Manages Ollama model lifecycle and configuration.

    Handles loading, checking, and managing the state of Ollama models
    via the Ollama REST API.
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        """Initialize the model manager.

        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self._base_url = base_url
        self._model_name: Optional[str] = None
        self._config: Optional[ModelConfig] = None

    @handle_service_errors
    def load_model(self, model_path: str, config: ModelConfig) -> Result:
        """Load/verify an Ollama model is available.

        Args:
            model_path: Model name (e.g., "llama3.2", "llama3.2:3b")
            config: Model configuration (context size, etc.)

        Returns:
            Result with model info or error
        """
        # Extract model name from path if it's a full path
        model_name = model_path.split("/")[-1].replace(".gguf", "")

        log_message(f"Checking Ollama model: {model_name}", LogLevel.INFO)

        # Check if Ollama is running
        try:
            response = requests.get(f"{self._base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return error_result(
                f"Could not connect to Ollama at {self._base_url}. "
                "Make sure Ollama is installed and running. "
                f"Error: {str(e)}"
            )

        # Check if model exists
        models_data = response.json()
        available_models = [m["name"] for m in models_data.get("models", [])]

        # Check for exact match or partial match
        model_available = any(
            model_name in available_model or available_model.startswith(model_name)
            for available_model in available_models
        )

        if not model_available:
            log_message(
                f"Model '{model_name}' not found. Available models: {available_models}",
                LogLevel.WARNING
            )
            return error_result(
                f"Model '{model_name}' not found in Ollama. "
                f"Run 'ollama pull {model_name}' to download it. "
                f"Available models: {', '.join(available_models)}"
            )

        self._model_name = model_name
        self._config = config

        log_message(f"Ollama model '{model_name}' is available", LogLevel.INFO)

        return success_result({
            "model_name": model_name,
            "context_size": config.get("n_ctx", 2048),
            "ollama_url": self._base_url
        })

    @handle_service_errors
    def unload_model(self) -> Result:
        """Unload the current model reference.

        Note: Ollama manages model lifecycle automatically, so this just
        clears the internal reference.

        Returns:
            Result indicating success
        """
        if self._model_name is None:
            return error_result("No model loaded")

        log_message(f"Releasing model reference: {self._model_name}", LogLevel.INFO)
        self._model_name = None
        self._config = None

        return success_result({"unloaded": True})

    def is_loaded(self) -> bool:
        """Check if a model is currently loaded.

        Returns:
            True if a model reference exists, False otherwise
        """
        return self._model_name is not None

    @handle_service_errors
    def get_model_info(self) -> Result:
        """Get information about the currently loaded model.

        Returns:
            Result with model information or error
        """
        if not self.is_loaded():
            return error_result("No model loaded")

        return success_result({
            "model_name": self._model_name,
            "config": self._config,
            "backend": "ollama",
            "base_url": self._base_url
        })

    def get_model(self) -> Optional[str]:
        """Get the model name.

        Returns:
            Model name string or None if not loaded
        """
        return self._model_name

    def get_base_url(self) -> str:
        """Get the Ollama API base URL.

        Returns:
            Base URL string
        """
        return self._base_url
