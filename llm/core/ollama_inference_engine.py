"""Inference execution engine for Ollama models."""

from typing import Iterator
import requests
import json

from .types import InferenceConfig, Result, IModelManager
from ..utils.result import success_result, error_result
from ..utils.error_handling import handle_service_errors
from ..utils.logging import log_message, LogLevel


class OllamaInferenceEngine:
    """Handles inference execution with Ollama models.

    Supports both streaming and non-streaming generation with
    configurable inference parameters via the Ollama API.
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

        model_name = self._model_manager.get_model()
        base_url = self._model_manager.get_base_url()

        log_message(
            f"Generating response with {model_name}",
            LogLevel.INFO
        )

        # Prepare request payload
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "context": [],  # Always start fresh - no cached context from previous requests
            "options": {
                "num_predict": config.get("max_tokens", 512),
                "temperature": config.get("temperature", 0.7),
                "top_p": config.get("top_p", 0.95),
                "top_k": config.get("top_k", 40),
                "repeat_penalty": config.get("repeat_penalty", 1.1),
            }
        }

        # Add stop sequences if provided
        if config.get("stop"):
            payload["options"]["stop"] = config["stop"]

        try:
            response = requests.post(
                f"{base_url}/api/generate",
                json=payload,
                timeout=120  # 2 minutes timeout
            )
            response.raise_for_status()
            data = response.json()

            return success_result({
                "text": data.get("response", ""),
                "tokens_used": data.get("eval_count", 0),
                "finish_reason": "stop" if data.get("done") else "length"
            })

        except requests.exceptions.RequestException as e:
            return error_result(f"Ollama API error: {str(e)}")

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
            RuntimeError: If no model is loaded or API error occurs
        """
        if not self._model_manager.is_loaded():
            raise RuntimeError("No model loaded")

        model_name = self._model_manager.get_model()
        base_url = self._model_manager.get_base_url()

        log_message(
            f"Generating streaming response with {model_name}",
            LogLevel.INFO
        )

        # Prepare request payload
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "context": [],  # Always start fresh - no cached context from previous requests
            "options": {
                "num_predict": config.get("max_tokens", 512),
                "temperature": config.get("temperature", 0.7),
                "top_p": config.get("top_p", 0.95),
                "top_k": config.get("top_k", 40),
                "repeat_penalty": config.get("repeat_penalty", 1.1),
            }
        }

        # Add stop sequences if provided
        if config.get("stop"):
            payload["options"]["stop"] = config["stop"]

        try:
            response = requests.post(
                f"{base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=120
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        chunk = data.get("response", "")
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")
