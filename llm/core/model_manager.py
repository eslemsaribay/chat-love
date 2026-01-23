"""Model lifecycle management for Llama models."""

from typing import Optional
from llama_cpp import Llama

from .types import ModelConfig, Result
from ..utils.result import success_result, error_result
from ..utils.error_handling import handle_service_errors
from ..utils.logging import log_message, LogLevel


class LlamaModelManager:
    """Manages Llama model lifecycle and configuration.

    Handles loading, unloading, and managing the state of Llama models
    using llama-cpp-python.
    """

    def __init__(self) -> None:
        """Initialize the model manager with no model loaded."""
        self._model: Optional[Llama] = None
        self._model_path: Optional[str] = None
        self._config: Optional[ModelConfig] = None

    @handle_service_errors
    def load_model(self, model_path: str, config: ModelConfig) -> Result:
        """Load a Llama model with specified configuration.

        Args:
            model_path: Path to the GGUF model file
            config: Model configuration parameters

        Returns:
            Result with model info or error
        """
        if self._model is not None:
            log_message("Model already loaded, unloading first", LogLevel.INFO)
            self.unload_model()

        log_message(f"Loading model from {model_path}", LogLevel.INFO)

        self._model = Llama(
            model_path=model_path,
            n_ctx=config.get("n_ctx", 2048),
            n_gpu_layers=config.get("n_gpu_layers", 0),
            n_threads=config.get("n_threads", 4),
            use_mmap=config.get("use_mmap", True),
            use_mlock=config.get("use_mlock", False),
            verbose=config.get("verbose", False)
        )

        self._model_path = model_path
        self._config = config

        log_message("Model loaded successfully", LogLevel.INFO)

        return success_result({
            "model_path": model_path,
            "context_size": config.get("n_ctx", 2048)
        })

    @handle_service_errors
    def unload_model(self) -> Result:
        """Unload the current model and free resources.

        Returns:
            Result indicating success or error
        """
        if self._model is None:
            return error_result("No model loaded")

        # llama-cpp-python handles cleanup automatically
        self._model = None
        self._model_path = None
        self._config = None

        log_message("Model unloaded successfully", LogLevel.INFO)
        return success_result({"unloaded": True})

    def is_loaded(self) -> bool:
        """Check if a model is currently loaded.

        Returns:
            True if a model is loaded, False otherwise
        """
        return self._model is not None

    @handle_service_errors
    def get_model_info(self) -> Result:
        """Get information about the currently loaded model.

        Returns:
            Result with model information or error
        """
        if not self.is_loaded():
            return error_result("No model loaded")

        return success_result({
            "model_path": self._model_path,
            "config": self._config
        })

    def get_model(self) -> Optional[Llama]:
        """Get the underlying Llama model instance.

        Returns:
            The Llama model instance or None if not loaded
        """
        return self._model
