"""
Chat LLM Worker - Background thread for LLM inference
Prevents UI freezing during LLM calls (which can take up to 2 minutes)
"""

import threading
from typing import Callable, Optional


class ChatLLMWorker(threading.Thread):
    """
    Background thread that calls LLM and provides callbacks
    Supports both streaming and non-streaming modes
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
        Args:
            llm_interface: LLM interface from llm package
            user_message: User's message to send
            config: Configuration dict
            callback: Called when complete - callback(final_text, success)
            streaming_callback: Optional - called per chunk - callback(chunk, accumulated_text)
        """
        # daemon=True ensures thread cleanup on TD exit
        super().__init__(daemon=True)

        self.llm_interface = llm_interface
        self.user_message = user_message
        self.config = config
        self.callback = callback
        self.streaming_callback = streaming_callback

    def run(self):
        """Execute in background thread"""
        try:
            if self.streaming_callback and self.config.get("streaming_enabled", True):
                # Streaming mode
                self._run_streaming()
            else:
                # Non-streaming mode
                self._run_blocking()
        except Exception as e:
            print(f"[LLM WORKER] Error: {e}")
            self.callback(str(e), False)

    def _run_streaming(self):
        """Run in streaming mode (incremental text display)"""
        accumulated_text = ""

        try:
            # Call LLM with streaming - yields plain text strings
            for chunk in self.llm_interface.send_message_stream(self.user_message):
                # chunk is a plain string from generate_stream()
                if isinstance(chunk, str):
                    accumulated_text += chunk
                    if self.streaming_callback:
                        self.streaming_callback(chunk, accumulated_text)

            # Call final callback with full text
            self.callback(accumulated_text, True)

        except Exception as e:
            print(f"[LLM WORKER] Streaming error: {e}")
            self.callback(str(e), False)

    def _run_blocking(self):
        """Run in blocking mode (wait for full response)"""
        try:
            # Call LLM (blocks until complete)
            result = self.llm_interface.send_message(self.user_message)

            # Extract response text - ChatInterface returns "response" key
            if isinstance(result, dict) and result.get("success") and "data" in result:
                # Try "response" first (from ChatInterface.send_message), then "text" (from raw inference)
                response_text = result["data"].get("response", "") or result["data"].get("text", "")
                self.callback(response_text, True)
            elif isinstance(result, dict) and "error" in result:
                print(f"[LLM WORKER] Error in result: {result['error']}")
                self.callback(result["error"], False)
            else:
                print(f"[LLM WORKER] Unexpected result format: {result}")
                self.callback(str(result), False)

        except Exception as e:
            print(f"[LLM WORKER] Exception: {e}")
            self.callback(str(e), False)
