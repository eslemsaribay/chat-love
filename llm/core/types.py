"""Type definitions, protocols, and interfaces for the LLM system."""

from typing import Any, Iterator, Literal, Optional, Protocol, TypedDict


# Result type following the MCP pattern
class Result(TypedDict, total=False):
    """Type representing operation results."""
    success: bool
    data: Any
    error: Any


# Message types
MessageRole = Literal["system", "user", "assistant"]


class Message(TypedDict):
    """Represents a single conversation message."""
    role: MessageRole
    content: str
    timestamp: float


# Configuration types
class ModelConfig(TypedDict, total=False):
    """Configuration for model loading."""
    n_ctx: int  # Context window size
    n_gpu_layers: int  # Number of layers to offload to GPU
    n_threads: int  # Number of CPU threads
    use_mmap: bool  # Use memory mapping
    use_mlock: bool  # Lock model in RAM
    verbose: bool  # Verbose output


class InferenceConfig(TypedDict, total=False):
    """Configuration for inference."""
    max_tokens: int  # Maximum tokens to generate
    temperature: float  # Sampling temperature
    top_p: float  # Nucleus sampling
    top_k: int  # Top-k sampling
    repeat_penalty: float  # Repetition penalty
    stop: list[str]  # Stop sequences
    stream: bool  # Enable streaming


# Protocol interfaces for dependency inversion
class IModelManager(Protocol):
    """Protocol for model management."""

    def load_model(self, model_path: str, config: ModelConfig) -> Result:
        """Load a model with specified configuration."""
        ...

    def unload_model(self) -> Result:
        """Unload the current model."""
        ...

    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        ...

    def get_model_info(self) -> Result:
        """Get information about the loaded model."""
        ...

    def get_model(self) -> Any:
        """Get the underlying model instance."""
        ...


class IInferenceEngine(Protocol):
    """Protocol for inference execution."""

    def generate(self, prompt: str, config: InferenceConfig) -> Result:
        """Generate a response (non-streaming)."""
        ...

    def generate_stream(
        self,
        prompt: str,
        config: InferenceConfig
    ) -> Iterator[str]:
        """Generate a response (streaming)."""
        ...


class IConversationManager(Protocol):
    """Protocol for conversation management."""

    def add_message(self, role: MessageRole, content: str) -> None:
        """Add a message to the conversation."""
        ...

    def get_messages(self) -> list[Message]:
        """Get all messages in the conversation."""
        ...

    def clear_history(self) -> None:
        """Clear conversation history."""
        ...

    def get_context_for_inference(self, system_prompt: str) -> str:
        """Build context string for inference."""
        ...
