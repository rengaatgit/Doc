import requests
from llama_index.core.llms.custom import CustomLLM
from llama_index.core.base.llms.types import LLMMetadata, CompletionResponse, CompletionResponseGen
from typing import Optional, Sequence
import json

class MyCustomLLM(CustomLLM):
    def __init__(self, api_url: str, api_key: str, model: str, temperature: float = 0.7):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=4096,
            num_output=512,
            is_chat_model=True,
            model_name=self.model
        )

    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        """Non-chat style completion."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        # Adjust this extraction according to your API response format
        text = result["choices"][0]["message"]["content"]
        return CompletionResponse(text=text)

    def stream_complete(self, prompt: str, **kwargs) -> CompletionResponseGen:
        """Streaming is optional — here we just yield the full completion."""
        yield self.complete(prompt, **kwargs)


# ==== Example usage with LlamaIndex ====

from llama_index.core import VectorStoreIndex, Document

if __name__ == "__main__":
    # Your endpoint & credentials
    API_URL = "https://www.ep.net/v1/chat/completion"
    API_KEY = "YOUR_API_KEY"
    MODEL = "my-llm-model"

    # Create custom LLM instance
    llm = MyCustomLLM(api_url=API_URL, api_key=API_KEY, model=MODEL)

    # Create some documents
    documents = [
        Document(text="LlamaIndex is a framework for LLM apps."),
        Document(text="Your API can be integrated as a custom LLM.")
    ]

    # Create index with custom LLM
    index = VectorStoreIndex.from_documents(documents, llm=llm)

    # Query index
    query_engine = index.as_query_engine()
    response = query_engine.query("What is LlamaIndex?")
    print("Response:", response)
