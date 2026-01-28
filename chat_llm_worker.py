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
            print(f"LLM Worker Error: {e}")
            self.callback(str(e), False)

    def _run_streaming(self):
        """Run in streaming mode (incremental text display)"""
        accumulated_text = ""

        try:
            # Call LLM with streaming
            for chunk in self.llm_interface.send_message_stream(self.user_message):
                # Accumulate text
                if isinstance(chunk, dict) and "data" in chunk:
                    chunk_text = chunk["data"].get("response", "")
                    accumulated_text += chunk_text

                    # Call streaming callback
                    if self.streaming_callback:
                        self.streaming_callback(chunk_text, accumulated_text)

            # Call final callback with full text
            self.callback(accumulated_text, True)

        except Exception as e:
            print(f"Streaming error: {e}")
            self.callback(str(e), False)

    def _run_blocking(self):
        """Run in blocking mode (wait for full response)"""
        try:
            # Call LLM (blocks until complete)
            result = self.llm_interface.send_message(self.user_message)

            # Extract response text
            if isinstance(result, dict) and "data" in result:
                response_text = result["data"].get("response", "")
                self.callback(response_text, True)
            else:
                self.callback(str(result), True)

        except Exception as e:
            print(f"LLM error: {e}")
            self.callback(str(e), False)
