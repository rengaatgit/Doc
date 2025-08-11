import requests
from typing import Any
from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.core import Settings

class MyCompanyLLM(CustomLLM):
    context_window: int = 4096
    num_output: int = 256
    model_name: str = "your-llm-model"
    endpoint: str = "https://www.ep.net/v1/chat/completion"

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model_name,
        )

    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        payload = {
            "model": self.model_name,   # model in payload body
            "messages": [
                {"role": "user", "content": prompt}
            ],
            # add more fields if your API requires them (e.g., temperature, max_tokens)
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.endpoint, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        # This assumes your API returns {'choices':[{'message':{'content':...}}]}
        # Adjust according to your API spec
        text = data["choices"][0]["message"]["content"]
        return CompletionResponse(text=text)

# LlamaIndex global settings
Settings.llm = MyCompanyLLM(model_name="your-llm-model")

if __name__ == "__main__":
    # Usage example
    llm = Settings.llm
    prompt = "Tell me a joke."
    resp = llm.complete(prompt)
    print("LLM Response:", resp.text)
