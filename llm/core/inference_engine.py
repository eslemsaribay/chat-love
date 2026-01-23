"""Inference execution engine for Llama models."""

from typing import Iterator

from .types import InferenceConfig, Result, IModelManager
from ..utils.result import success_result, error_result
from ..utils.error_handling import handle_service_errors
from ..utils.logging import log_message, LogLevel


class LlamaInferenceEngine:
    """Handles inference execution with Llama models.

    Supports both streaming and non-streaming generation with
    configurable inference parameters.
    """

    def __init__(self, model_manager: IModelManager) -> None:
        """Initialize the inference engine.

        Args:
            model_manager: Model manager instance providing model access
        """
        self._model_manager = model_manager

    @handle_service_errors
    def generate(self, prompt: str, config: InferenceConfig) -> Result:
        """Generate a response from the model (non-streaming).

        Args:
            prompt: The input prompt for the model
            config: Inference configuration parameters

        Returns:
            Result with generated text and metadata or error
        """
        if not self._model_manager.is_loaded():
            return error_result("No model loaded")

        model = self._model_manager.get_model()

        log_message(
            f"Generating response (max_tokens={config.get('max_tokens', 512)})",
            LogLevel.INFO
        )

        response = model(
            prompt,
            max_tokens=config.get("max_tokens", 512),
            temperature=config.get("temperature", 0.7),
            top_p=config.get("top_p", 0.95),
            top_k=config.get("top_k", 40),
            repeat_penalty=config.get("repeat_penalty", 1.1),
            stop=config.get("stop", []),
            stream=False
        )

        return success_result({
            "text": response["choices"][0]["text"],
            "tokens_used": response["usage"]["total_tokens"],
            "finish_reason": response["choices"][0]["finish_reason"]
        })

    def generate_stream(
        self,
        prompt: str,
        config: InferenceConfig
    ) -> Iterator[str]:
        """Generate a response from the model (streaming).

        Args:
            prompt: The input prompt for the model
            config: Inference configuration parameters

        Yields:
            Text chunks as they are generated

        Raises:
            RuntimeError: If no model is loaded
        """
        if not self._model_manager.is_loaded():
            raise RuntimeError("No model loaded")

        model = self._model_manager.get_model()

        log_message(
            f"Generating streaming response (max_tokens={config.get('max_tokens', 512)})",
            LogLevel.INFO
        )

        stream = model(
            prompt,
            max_tokens=config.get("max_tokens", 512),
            temperature=config.get("temperature", 0.7),
            top_p=config.get("top_p", 0.95),
            top_k=config.get("top_k", 40),
            repeat_penalty=config.get("repeat_penalty", 1.1),
            stop=config.get("stop", []),
            stream=True
        )

        for chunk in stream:
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("text", "")
                if delta:
                    yield delta
