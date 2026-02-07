"""Inference execution engine for Ollama models."""

from typing import Iterator
import requests
import json
import os
import time

from .types import InferenceConfig, Result, IModelManager
from ..utils.result import success_result, error_result
from ..utils.error_handling import handle_service_errors
from ..utils.logging import log_message, LogLevel

# Debug output directory: project root (2 levels up from llm/core/)
# Use normpath to resolve '..' on Windows, and abspath as fallback
_DEBUG_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_debug_prompts'))

# Session file: one file per conversation session, appended to on each LLM call
_session_file_path = None
_session_message_index = 0


def _reset_debug_session():
    """Reset the debug session (call on F5 / conversation reset).

    Starts a new session file for the next conversation.
    """
    global _session_file_path, _session_message_index
    _session_file_path = None
    _session_message_index = 0


def _save_debug_prompt(prompt, payload: dict, label: str = "generate"):
    """Save full prompt and payload to debug file for inspection.

    Creates _debug_prompts/ directory in project root with:
    - latest.txt: Always overwritten with the most recent prompt (quick look)
    - session_YYYYMMDD_HHMMSS.txt: One file per conversation, appended to

    Also prints a structured summary to textport.

    Args:
        prompt: Either a flat prompt string (for /api/generate) or a
                list of message dicts (for /api/chat)
        payload: The full request payload
        label: Label for this request type
    """
    global _session_file_path, _session_message_index

    try:
        created = not os.path.exists(_DEBUG_DIR)
        os.makedirs(_DEBUG_DIR, exist_ok=True)
        if created:
            print(f"[DEBUG PROMPT] Created debug directory: {_DEBUG_DIR}")

        # Initialize session file on first call
        if _session_file_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            _session_file_path = os.path.join(_DEBUG_DIR, f"session_{timestamp}.txt")
            _session_message_index = 0
            # Write session header
            with open(_session_file_path, 'w', encoding='utf-8') as f:
                f.write(f"SESSION START: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"MODEL: {payload.get('model', '?')}\n")
                f.write(f"ENDPOINT: {'/api/chat' if isinstance(prompt, list) else '/api/generate'}\n")
                f.write(f"{'='*60}\n\n")
            print(f"[DEBUG PROMPT] New session file: {_session_file_path}")

        _session_message_index += 1

        # Handle both flat string and structured messages
        if isinstance(prompt, list):
            # Structured messages (chat API)
            prompt_text = ""
            system_len = 0
            user_count = 0
            assistant_count = 0
            has_examples = False

            for msg in prompt:
                role = msg.get("role", "?")
                content = msg.get("content", "")
                if role == "system":
                    system_len = len(content)
                    has_examples = "# Examples:" in content or "EXAMPLES:" in content
                    # Only log full system prompt on first message of session
                    if _session_message_index == 0:
                        prompt_text += f"[SYSTEM]\n{content}\n\n"
                    else:
                        prompt_text += f"[SYSTEM] ({system_len} chars, same as message #1)\n\n"
                elif role == "user":
                    user_count += 1
                    prompt_text += f"[USER]\n{content}\n\n"
                elif role == "assistant":
                    assistant_count += 1
                    prompt_text += f"[ASSISTANT]\n{content}\n\n"

            total_len = sum(len(m.get("content", "")) for m in prompt)
        else:
            # Flat string (generate API) - legacy path
            prompt_text = prompt
            total_len = len(prompt)
            user_count = prompt.count("\n\nUser:")
            assistant_count = prompt.count("\n\nAssistant:")
            has_examples = "# Examples:" in prompt or "EXAMPLES:" in prompt
            system_len = 0
            if "System:" in prompt:
                system_end = prompt.find("\n\nUser:") if "\n\nUser:" in prompt else prompt.find("\n\nAssistant:")
                if system_end > 0:
                    system_len = system_end - len("System: ")

        endpoint = "/api/chat" if isinstance(prompt, list) else "/api/generate"

        # Print structured summary to textport
        print(f"\n{'='*60}")
        print(f"[DEBUG PROMPT] === #{_session_message_index} {label.upper()} REQUEST ===")
        print(f"[DEBUG PROMPT] Endpoint: {endpoint}")
        print(f"[DEBUG PROMPT] Model: {payload.get('model', '?')}")
        print(f"[DEBUG PROMPT] Streaming: {payload.get('stream', False)}")
        print(f"[DEBUG PROMPT] Total prompt length: {total_len} chars")
        print(f"[DEBUG PROMPT] Conversation turns: {user_count} user, {assistant_count} assistant")
        print(f"[DEBUG PROMPT] Examples included: {'YES' if has_examples else 'NO'}")
        if system_len:
            print(f"[DEBUG PROMPT] System instruction: {system_len} chars")
        print(f"[DEBUG PROMPT] Options: temp={payload.get('options', {}).get('temperature', '?')}, "
              f"max_tokens={payload.get('options', {}).get('num_predict', '?')}, "
              f"top_p={payload.get('options', {}).get('top_p', '?')}")
        print(f"[DEBUG PROMPT] Session file: {os.path.basename(_session_file_path)}")
        print(f"{'='*60}\n")

        # Build content block for this message
        content = f"\n{'='*60}\n"
        content += f"MESSAGE #{_session_message_index} | {time.strftime('%H:%M:%S')} | {label} | {endpoint}\n"
        content += f"Prompt length: {total_len} chars | Turns: {user_count} user, {assistant_count} assistant\n"
        content += f"Options: {json.dumps(payload.get('options', {}), indent=2)}\n"
        content += f"{'='*60}\n\n"
        content += prompt_text
        content += f"\n\n{'- '*30}\n"

        # Append to session file
        with open(_session_file_path, 'a', encoding='utf-8') as f:
            f.write(content)

        # Overwrite latest.txt for quick look
        latest_path = os.path.join(_DEBUG_DIR, "latest.txt")
        with open(latest_path, 'w', encoding='utf-8') as f:
            f.write(content)

    except Exception as e:
        print(f"[DEBUG PROMPT] Warning: Could not save debug prompt: {e}")


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

        # Debug: Save full prompt to file and print structured summary
        _save_debug_prompt(prompt, payload, label="generate")

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

        # Debug: Save full prompt to file and print structured summary
        _save_debug_prompt(prompt, payload, label="stream")

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

    @handle_service_errors
    def chat(self, messages: list[dict], config: InferenceConfig) -> Result:
        """Send a chat request with structured messages (non-streaming).

        Uses /api/chat endpoint which properly separates system/user/assistant
        roles, preventing the model from reading system instructions as text.

        Args:
            messages: List of {"role": ..., "content": ...} dicts
            config: Inference configuration parameters

        Returns:
            Result with generated text and metadata or error
        """
        if not self._model_manager.is_loaded():
            return error_result("No model loaded")

        model_name = self._model_manager.get_model()
        base_url = self._model_manager.get_base_url()

        log_message(
            f"Chat request with {model_name} ({len(messages)} messages)",
            LogLevel.INFO
        )

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": config.get("max_tokens", 512),
                "temperature": config.get("temperature", 0.7),
                "top_p": config.get("top_p", 0.95),
                "top_k": config.get("top_k", 40),
                "repeat_penalty": config.get("repeat_penalty", 1.1),
            }
        }

        if config.get("stop"):
            payload["options"]["stop"] = config["stop"]

        _save_debug_prompt(messages, payload, label="chat")

        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()

            return success_result({
                "text": data.get("message", {}).get("content", ""),
                "tokens_used": data.get("eval_count", 0),
                "finish_reason": "stop" if data.get("done") else "length"
            })

        except requests.exceptions.RequestException as e:
            return error_result(f"Ollama API error: {str(e)}")

    def chat_stream(
        self,
        messages: list[dict],
        config: InferenceConfig
    ) -> Iterator[str]:
        """Send a chat request with structured messages (streaming).

        Uses /api/chat endpoint which properly separates system/user/assistant
        roles, preventing the model from reading system instructions as text.

        Args:
            messages: List of {"role": ..., "content": ...} dicts
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
            f"Chat stream with {model_name} ({len(messages)} messages)",
            LogLevel.INFO
        )

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "num_predict": config.get("max_tokens", 512),
                "temperature": config.get("temperature", 0.7),
                "top_p": config.get("top_p", 0.95),
                "top_k": config.get("top_k", 40),
                "repeat_penalty": config.get("repeat_penalty", 1.1),
            }
        }

        if config.get("stop"):
            payload["options"]["stop"] = config["stop"]

        _save_debug_prompt(messages, payload, label="chat-stream")

        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=120
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")
