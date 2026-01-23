"""Clean, TD-agnostic interface for chat interactions.

This is the main API that TouchDesigner components will call.
"""

from typing import Optional, Iterator

from ..core.ollama_model_manager import OllamaModelManager
from ..core.ollama_inference_engine import OllamaInferenceEngine
from ..core.context_manager import ContextManager
from ..core.types import ModelConfig, InferenceConfig, Result
from ..conversation.conversation_manager import ConversationManager
from ..conversation.prompt_builder import PromptBuilder
from ..conversation.persistence import ConversationPersistence
from ..utils.result import success_result, error_result
from ..utils.logging import log_message, LogLevel


class ChatInterface:
    """Clean, TD-agnostic interface for chat interactions.

    This class provides a simple API for interacting with the LLM,
    managing conversations, and handling model lifecycle.
    """

    def __init__(
        self,
        model_path: str,
        model_config: Optional[ModelConfig] = None,
        system_instruction: str = "default",
        conversation_log_dir: str = "./conversation_logs"
    ) -> None:
        """Initialize the chat interface.

        Args:
            model_path: Path to the GGUF model file
            model_config: Optional model configuration
            system_instruction: System instruction template name
            conversation_log_dir: Directory for saving conversation logs

        Raises:
            RuntimeError: If model fails to load
        """
        # Initialize components
        self._model_manager = OllamaModelManager()
        self._inference_engine = OllamaInferenceEngine(self._model_manager)

        context_size = model_config.get("n_ctx", 2048) if model_config else 2048
        self._context_manager = ContextManager(max_context_tokens=context_size)

        self._conversation_manager = ConversationManager(self._context_manager)
        self._prompt_builder = PromptBuilder(instruction_template=system_instruction)
        self._persistence = ConversationPersistence(conversation_log_dir)

        # Load model
        config = model_config or {}
        load_result = self._model_manager.load_model(model_path, config)

        if not load_result["success"]:
            raise RuntimeError(f"Failed to load model: {load_result['error']}")

        log_message("ChatInterface initialized successfully", LogLevel.INFO)

    def send_message(
        self,
        user_message: str,
        config: Optional[InferenceConfig] = None
    ) -> Result:
        """Send a user message and get a response.

        Args:
            user_message: The user's input message
            config: Optional inference configuration

        Returns:
            Result with assistant's response or error
        """
        # Add user message to history
        self._conversation_manager.add_message("user", user_message)

        # Build prompt with context
        system_prompt = self._prompt_builder.build_system_prompt()
        full_prompt = self._conversation_manager.get_context_for_inference(system_prompt)

        # Generate response
        inference_config = config or {}
        result = self._inference_engine.generate(full_prompt, inference_config)

        if result["success"]:
            assistant_response = result["data"]["text"].strip()

            # Add assistant response to history
            self._conversation_manager.add_message("assistant", assistant_response)

            return success_result({
                "response": assistant_response,
                "tokens_used": result["data"]["tokens_used"],
                "message_count": self._conversation_manager.get_message_count()
            })

        return result

    def send_message_stream(
        self,
        user_message: str,
        config: Optional[InferenceConfig] = None
    ) -> Iterator[str]:
        """Send a user message and get a streaming response.

        Args:
            user_message: The user's input message
            config: Optional inference configuration

        Yields:
            Chunks of the assistant's response
        """
        # Add user message to history
        self._conversation_manager.add_message("user", user_message)

        # Build prompt with context
        system_prompt = self._prompt_builder.build_system_prompt()
        full_prompt = self._conversation_manager.get_context_for_inference(system_prompt)

        # Generate streaming response
        inference_config = config or {}
        full_response = []

        for chunk in self._inference_engine.generate_stream(full_prompt, inference_config):
            full_response.append(chunk)
            yield chunk

        # Add complete assistant response to history
        assistant_response = "".join(full_response).strip()
        self._conversation_manager.add_message("assistant", assistant_response)

    def clear_conversation(self) -> None:
        """Clear the conversation history."""
        self._conversation_manager.clear_history()
        log_message("Conversation history cleared", LogLevel.INFO)

    def save_conversation(self, session_id: Optional[str] = None) -> Result:
        """Save the current conversation to JSON.

        Args:
            session_id: Optional session identifier

        Returns:
            Result with save information or error
        """
        messages = self._conversation_manager.get_messages()
        return self._persistence.save_conversation(messages, session_id)

    def get_conversation_info(self) -> dict:
        """Get information about the current conversation.

        Returns:
            Dictionary with conversation metadata
        """
        return {
            "message_count": self._conversation_manager.get_message_count(),
            "model_info": self._model_manager.get_model_info()
        }

    def set_system_instruction(self, template_name: str) -> None:
        """Change the system instruction template.

        Args:
            template_name: Name of the template to use
        """
        self._prompt_builder.set_template(template_name)
        log_message(f"System instruction changed to: {template_name}", LogLevel.INFO)

    def shutdown(self) -> Result:
        """Clean shutdown: save conversation and unload model.

        Returns:
            Result with shutdown status
        """
        log_message("Shutting down ChatInterface", LogLevel.INFO)

        # Save conversation
        save_result = self.save_conversation()

        # Unload model
        unload_result = self._model_manager.unload_model()

        return success_result({
            "conversation_saved": save_result["success"],
            "model_unloaded": unload_result["success"]
        })
