#!/usr/bin/env python3
import os
import json
import requests
from typing import Any, Dict, List, Optional, Iterator

from llama_index.core import Settings
from llama_index.core.llms import CustomLLM, CompletionResponse, CompletionResponseGen, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback, llm_chat_callback

# Optional: if you plan to use chat-style interfaces from LlamaIndex
from llama_index.core.base.llms.types import ChatMessage, MessageRole

class MyCompanyLLM(CustomLLM):
    """
    Custom LLM wrapper for a generic chat/completion endpoint where:
      - Endpoint is fixed (e.g., https://www.ep.net/v1/chat/completion)
      - Model name is part of the JSON payload, not a parameter on the client
    """

    # Basic model/limits metadata LlamaIndex expects
    context_window: int = 4096
    num_output: int = 512
    model_name: str = "your-model-name"

    # Endpoint and auth
    endpoint: str = "https://www.ep.net/v1/chat/completion"
    api_key: Optional[str] = None

    # Default generation params; extend with temperature, top_p, etc., as needed
    temperature: float = 0.2
    max_tokens: int = 512
    stream: bool = False

    def __init__(
        self,
        model_name: str = "your-model-name",
        endpoint: str = "https://www.ep.net/v1/chat/completion",
        api_key: Optional[str] = None,
        context_window: int = 4096,
        num_output: int = 512,
        temperature: float = 0.2,
        max_tokens: int = 512,
        stream: bool = False,
    ) -> None:
        self.model_name = model_name
        self.endpoint = endpoint
        self.api_key = api_key or os.getenv("MY_COMPANY_API_KEY")
        self.context_window = context_window
        self.num_output = num_output
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stream = stream

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model_name,
        )

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            # Change header name to match your service (e.g., "Authorization": f"Bearer {self.api_key}")
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _post(self, payload: Dict[str, Any], stream: bool = False):
        resp = requests.post(self.endpoint, headers=self._build_headers(), json=payload, stream=stream, timeout=300)
        resp.raise_for_status()
        return resp

    def _format_messages_from_prompt(self, prompt: str) -> List[Dict[str, str]]:
        # Convert a single prompt into a chat-format payload expected by most chat/completions APIs
        return [{"role": "user", "content": prompt}]

    def _format_messages_from_chat(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        for m in messages:
            # Map LlamaIndex MessageRole to provider roles
            if m.role == MessageRole.SYSTEM:
                role = "system"
            elif m.role == MessageRole.ASSISTANT:
                role = "assistant"
            else:
                role = "user"
            out.append({"role": role, "content": m.content})
        return out

    def _build_payload_base(self) -> Dict[str, Any]:
        # Base payload your API expects; ensure "model" is in the JSON body per your spec
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            # Add other provider-specific options here
        }

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """
        Non-streaming text completion with a single prompt.
        """
        payload = self._build_payload_base()
        payload["messages"] = self._format_messages_from_prompt(prompt)
        payload["stream"] = False

        # Allow overrides via kwargs (e.g., temperature=..., max_tokens=...)
        for k in ("temperature", "max_tokens"):
            if k in kwargs and kwargs[k] is not None:
                payload[k] = kwargs[k]

        data = self._post(payload, stream=False).json()

        # Adjust parsing according to your API response schema
        # Common schema: {"choices":[{"message":{"role":"assistant","content":"..."}}], ...}
        text = data["choices"][0]["message"]["content"]
        return CompletionResponse(text=text)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        """
        Streaming text completion if your API supports server-sent events (SSE) or chunked JSON.
        """
        payload = self._build_payload_base()
        payload["messages"] = self._format_messages_from_prompt(prompt)
        payload["stream"] = True

        for k in ("temperature", "max_tokens"):
            if k in kwargs and kwargs[k] is not None:
                payload[k] = kwargs[k]

        with self._post(payload, stream=True) as resp:
            # Example for SSE-like "data: {...}" lines, adjust to your server’s format
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except Exception:
                        continue
                    # Common streaming schema: delta tokens appear under choices[0].delta.content
                    delta = chunk.get("choices", [{}]).get("delta", {}).get("content", "")
                    if delta:
                        yield CompletionResponse(text=delta, delta=delta)

    @llm_chat_callback()
    def chat(self, messages: List[ChatMessage], **kwargs: Any) -> CompletionResponse:
        """
        Non-streaming chat with full message history.
        """
        payload = self._build_payload_base()
        payload["messages"] = self._format_messages_from_chat(messages)
        payload["stream"] = False

        for k in ("temperature", "max_tokens"):
            if k in kwargs and kwargs[k] is not None:
                payload[k] = kwargs[k]

        data = self._post(payload, stream=False).json()
        text = data["choices"][0]["message"]["content"]
        return CompletionResponse(text=text)

    def stream_chat(self, messages: List[ChatMessage], **kwargs: Any) -> CompletionResponseGen:
        """
        Streaming chat with full message history (optional).
        """
        payload = self._build_payload_base()
        payload["messages"] = self._format_messages_from_chat(messages)
        payload["stream"] = True

        for k in ("temperature", "max_tokens"):
            if k in kwargs and kwargs[k] is not None:
                payload[k] = kwargs[k]

        with self._post(payload, stream=True) as resp:
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except Exception:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        yield CompletionResponse(text=delta, delta=delta)


def main():
    # Instantiate and register as the global default LLM so all LlamaIndex modules use it
    llm = MyCompanyLLM(
        model_name="your-model-name",
        endpoint="https://www.ep.net/v1/chat/completion",
        api_key=os.getenv("MY_COMPANY_API_KEY"),
        temperature=0.2,
        max_tokens=512,
        stream=False,  # set True to use streaming functions
    )
    Settings.llm = llm  # Global default used by indexes, query/chat engines, etc. [25][12]

    # 1) Direct completion
    resp = llm.complete("Write a one-sentence product tagline for a task manager app.")
    print("Completion:", resp.text)

    # 2) Streaming completion (uncomment if your endpoint supports it)
    # for chunk in llm.stream_complete("List three creative team names:"):
    #     print(chunk.delta, end="", flush=True)
    # print()

    # 3) Chat-style call using messages
    msgs = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a concise assistant."),
        ChatMessage(role=MessageRole.USER, content="Give me a two-line poem about the ocean."),
    ]
    chat_resp = llm.chat(msgs)
    print("Chat:", chat_resp.text)

    # From here, you can plug into any index/query engine as usual.
    # Example (if you have docs and want to RAG):
    # from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
    # docs = SimpleDirectoryReader("data").load_data()
    # index = VectorStoreIndex.from_documents(docs)  # uses Settings.llm under the hood [25][12]
    # qe = index.as_query_engine()
    # print(qe.query("What are the key ideas?"))

if __name__ == "__main__":
    main()
