import os
import json
import requests
from typing import Any, Dict, List, Optional, Sequence

# Core LlamaIndex components for custom LLM implementation
from llama_index.core.llms import (
    CustomLLM,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback
from llama_index.core.base.llms.types import ChatMessage, MessageRole, ChatResponse
from llama_index.core import Settings

class CompanyLLM(CustomLLM):
    """
    A custom LlamaIndex LLM class to interface with a generic corporate
    endpoint that requires the model name in the payload.
    
    This class handles:
    1.  Calling the specified generic endpoint (e.g., www.ep.net/v1/chat/completion).
    2.  Placing the `model` identifier inside the JSON request body.
    3.  Supporting both standard and streaming responses.
    """
    
    # Configuration for your company's endpoint and model
    model: str = "default-model"
    endpoint_url: str = "https://www.ep.net/v1/chat/completion"
    api_key: Optional[str] = None
    
    # Standard generation parameters
    temperature: float = 0.1
    max_tokens: int = 1024
    
    # Metadata required by LlamaIndex
    context_window: int = 4096
    num_output: int = 1024
    is_chat_model: bool = True # Assuming it's a chat model based on the endpoint path

    def __init__(
        self,
        model: str,
        endpoint_url: str,
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        context_window: int = 4096,
    ) -> None:
        super().__init__()
        self.model = model
        self.endpoint_url = endpoint_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.context_window = context_window
        
        # Prefer provided API key, fall back to environment variable
        self.api_key = api_key or os.getenv("COMPANY_API_KEY")
        if not self.api_key:
            print("Warning: COMPANY_API_KEY environment variable not set.")

    @property
    def metadata(self) -> LLMMetadata:
        """Provides metadata about the LLM to LlamaIndex."""
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model,
            is_chat_model=self.is_chat_model,
        )

    def _prepare_payload(self, messages: Sequence[ChatMessage], stream: bool) -> Dict[str, Any]:
        """Constructs the JSON payload for the API request."""
        
        # Convert LlamaIndex ChatMessage objects to a list of dicts
        message_dicts = [
            {"role": msg.role.value, "content": msg.content} for msg in messages
        ]
        
        return {
            "model": self.model,  # Model is part of the payload
            "messages": message_dicts,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
            # Add any other parameters your API supports
        }

    def _get_headers(self) -> Dict[str, str]:
        """Constructs the request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @llm_completion_callback()
    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        """Handles non-streaming chat requests."""
        payload = self._prepare_payload(messages, stream=False)
        headers = self._get_headers()

        with requests.post(
            self.endpoint_url, json=payload, headers=headers, stream=False
        ) as response:
            response.raise_for_status()
            data = response.json()
            
            # --- IMPORTANT ---
            # You must adapt the parsing below to match your API's response structure.
            # This example assumes an OpenAI-compatible response format.
            content = data["choices"][0]["message"]["content"]
            
            return ChatResponse(
                message=ChatMessage(role=MessageRole.ASSISTANT, content=content),
                raw=data,
            )

    @llm_completion_callback()
    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> CompletionResponseGen:
        """Handles streaming chat requests."""
        payload = self._prepare_payload(messages, stream=True)
        headers = self._get_headers()

        with requests.post(
            self.endpoint_url, json=payload, headers=headers, stream=True
        ) as response:
            response.raise_for_status()
            
            # --- IMPORTANT ---
            # This parsing assumes a Server-Sent Events (SSE) stream similar to OpenAI's.
            # You may need to adjust this logic for your API's streaming protocol.
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    if decoded_line.startswith("data:"):
                        data_str = decoded_line[len("data:"):].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            content_delta = delta.get("content", "")
                            if content_delta:
                                yield CompletionResponse(delta=content_delta, text=content_delta)
                        except json.JSONDecodeError:
                            # Handle cases where a line is not valid JSON
                            continue
                            
    # The 'complete' and 'stream_complete' methods are older interfaces.
    # For modern LlamaIndex, implementing 'chat' and 'stream_chat' is sufficient.
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Legacy completion method (delegates to chat)."""
        response = self.chat([ChatMessage(role=MessageRole.USER, content=prompt)])
        return CompletionResponse(text=response.message.content, raw=response.raw)
    
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        """Legacy streaming completion method (delegates to stream_chat)."""
        return self.stream_chat([ChatMessage(role=MessageRole.USER, content=prompt)])


# --- Main execution block to demonstrate usage ---
if __name__ == "__main__":
    # --- Configuration ---
    # It's recommended to set the API key as an environment variable
    # For example, in your terminal: export COMPANY_API_KEY='your-secret-key'
    
    YOUR_MODEL = "super-model-v3"
    YOUR_ENDPOINT = "https://www.ep.net/v1/chat/completion"
    
    print(f"Using model '{YOUR_MODEL}' at endpoint '{YOUR_ENDPOINT}'\n")

    # --- Step 1: Instantiate your custom LLM ---
    # This creates an instance of your custom wrapper.
    llm = CompanyLLM(model=YOUR_MODEL, endpoint_url=YOUR_ENDPOINT)
    
    # --- Step 2: Set it as the global default for LlamaIndex ---
    # This ensures that any LlamaIndex component (QueryEngine, Index, etc.)
    # will automatically use your custom LLM without needing to pass it explicitly.
    Settings.llm = llm

    # --- Step 3: Use the LLM to make API calls ---
    
    # Example 1: Direct, non-streaming chat call
    print("--- 1. Non-Streaming API Call ---")
    try:
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant that provides concise answers."),
            ChatMessage(role=MessageRole.USER, content="What are the three main benefits of using a framework like LlamaIndex?"),
        ]
        response = llm.chat(messages)
        print("Assistant Response:")
        print(response.message.content)
    except requests.exceptions.RequestException as e:
        print(f"API call failed. Please check your endpoint URL and API key.")
        print(f"Error: {e}")
        print("NOTE: This script uses a placeholder URL and will fail without a real, running endpoint.")

    print("\n" + "="*50 + "\n")

    # Example 2: Direct, streaming chat call
    print("--- 2. Streaming API Call ---")
    try:
        stream = llm.stream_chat(messages)
        print("Assistant Response (streaming):")
        for chunk in stream:
            print(chunk.delta, end="", flush=True)
        print("\n")
    except requests.exceptions.RequestException as e:
        print(f"Streaming API call failed. Please check your endpoint URL and API key.")
        print(f"Error: {e}")

