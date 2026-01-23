"""
TouchDesigner Chat LLM Worker
Background thread for non-blocking LLM inference
"""

import threading
from typing import Callable, Optional


class ChatLLMWorker(threading.Thread):
    """
    Background thread for non-blocking LLM inference

    This prevents TouchDesigner's UI from freezing during LLM calls,
    which can take up to 2 minutes.

    Thread Safety:
    - Only modifies Python data structures (via callbacks)
    - Does NOT directly manipulate TouchDesigner operators
    - Callbacks trigger UI updates through ChatManager
    """

    def __init__(
        self,
        llm_interface,
        user_message: str,
        config: dict,
        callback: Callable[[str, bool], None],
        streaming_callback: Optional[Callable[[str, str], None]] = None
    ):
        """
        Initialize LLM worker thread

        Args:
            llm_interface: ChatInterface from llm package
            user_message: User's message to send
            config: Configuration dictionary
            callback: Called on completion with (response, success)
            streaming_callback: Called for each chunk with (chunk, full_text)
        """
        super().__init__(daemon=True)  # Daemon ensures cleanup on TD exit
        self.llm_interface = llm_interface
        self.user_message = user_message
        self.config = config
        self.callback = callback
        self.streaming_callback = streaming_callback
        self.accumulated_text = ""

    def run(self):
        """
        Execute LLM inference in background thread

        This method runs in a separate thread and should not directly
        manipulate TouchDesigner operators.
        """
        try:
            if self.config["streaming_enabled"] and self.streaming_callback:
                # Streaming mode - incremental updates
                self._run_streaming()
            else:
                # Non-streaming mode - single response
                self._run_non_streaming()

        except Exception as e:
            # Catch all exceptions and report via callback
            error_msg = f"LLM inference error: {str(e)}"
            self.callback(error_msg, False)

    def _run_streaming(self):
        """Run streaming inference"""
        inference_config = {
            "max_tokens": self.config["max_tokens"],
            "temperature": self.config["temperature"]
        }

        # Stream chunks as they arrive
        for chunk in self.llm_interface.send_message_stream(
            self.user_message,
            inference_config
        ):
            self.accumulated_text += chunk

            # Call streaming callback with chunk and full text
            if self.streaming_callback:
                self.streaming_callback(chunk, self.accumulated_text)

        # Final callback when complete
        self.callback(self.accumulated_text, True)

    def _run_non_streaming(self):
        """Run non-streaming inference"""
        inference_config = {
            "max_tokens": self.config["max_tokens"],
            "temperature": self.config["temperature"]
        }

        # Single blocking call
        result = self.llm_interface.send_message(
            self.user_message,
            inference_config
        )

        # Check result and call callback
        if result["success"]:
            response = result["data"]["response"]
            self.callback(response, True)
        else:
            error_msg = result["error"]
            self.callback(error_msg, False)
