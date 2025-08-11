pip install llama-index-llms-openai-like


from llama_index.llms.openai_like import OpenAILike
from llama_index.core import Settings
import asyncio

# Configure the custom LLM
def setup_custom_llm(model_name="your-model-name", api_key="your-api-key"):
    """
    Setup custom LLM endpoint compatible with OpenAI API format
    """
    llm = OpenAILike(
        model=model_name,
        api_base="https://www.ep.net/v1",  # Your base URL
        api_key=api_key,  # Your API key if required
        is_chat_model=True,
        timeout=60,
        max_retries=3
    )
    
    # Set as default LLM for LlamaIndex
    Settings.llm = llm
    return llm

# Synchronous chat completion
def chat_completion(messages, model_name="gpt-3.5-turbo", api_key="your-api-key"):
    """
    Perform synchronous chat completion
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model_name: Model to use (sent in payload)
        api_key: API key for authentication
    """
    llm = setup_custom_llm(model_name, api_key)
    
    # Convert messages to string if needed
    if isinstance(messages, list):
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
    else:
        prompt = messages
    
    response = llm.complete(prompt)
    return response.text

# Asynchronous chat completion
async def async_chat_completion(messages, model_name="gpt-3.5-turbo", api_key="your-api-key"):
    """
    Perform asynchronous chat completion
    """
    llm = setup_custom_llm(model_name, api_key)
    
    if isinstance(messages, list):
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
    else:
        prompt = messages
    
    response = await llm.acomplete(prompt)
    return response.text

# Chat interface (maintains conversation context)
def chat_interface(messages, model_name="gpt-3.5-turbo", api_key="your-api-key"):
    """
    Chat interface that properly handles message format
    """
    llm = setup_custom_llm(model_name, api_key)
    
    # Use chat method for proper message handling
    from llama_index.core.llms import ChatMessage, MessageRole
    
    chat_messages = []
    for msg in messages:
        role = MessageRole.USER if msg['role'] == 'user' else MessageRole.ASSISTANT
        if msg['role'] == 'system':
            role = MessageRole.SYSTEM
        chat_messages.append(ChatMessage(role=role, content=msg['content']))
    
    response = llm.chat(chat_messages)
    return response.message.content

# Streaming completion
def stream_completion(prompt, model_name="gpt-3.5-turbo", api_key="your-api-key"):
    """
    Streaming completion example
    """
    llm = setup_custom_llm(model_name, api_key)
    
    response = llm.stream_complete(prompt)
    full_response = ""
    
    for chunk in response:
        print(chunk.delta, end="", flush=True)
        full_response += chunk.delta
    
    return full_response

# Example usage
if __name__ == "__main__":
    # Configuration
    MODEL_NAME = "gpt-3.5-turbo"  # Replace with your model name
    API_KEY = "your-api-key-here"  # Replace with your API key or remove if not needed
    
    # Example 1: Simple completion
    print("=== Simple Completion ===")
    simple_prompt = "What is the capital of France?"
    result = chat_completion(simple_prompt, MODEL_NAME, API_KEY)
    print(result)
    
    # Example 2: Chat with messages
    print("\n=== Chat Messages ===")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! What can you help me with?"}
    ]
    chat_result = chat_interface(messages, MODEL_NAME, API_KEY)
    print(chat_result)
    
    # Example 3: Streaming completion
    print("\n=== Streaming Completion ===")
    stream_prompt = "Write a short story about a robot:"
    stream_result = stream_completion(stream_prompt, MODEL_NAME, API_KEY)
    print(f"\n\nFull response: {stream_result}")
    
    # Example 4: Async completion
    print("\n=== Async Completion ===")
    async def async_example():
        async_messages = [
            {"role": "user", "content": "Explain quantum computing in simple terms"}
        ]
        result = await async_chat_completion(async_messages, MODEL_NAME, API_KEY)
        print(result)
    
    # Run async example
    asyncio.run(async_example())

# Alternative: Direct API call without global settings
def direct_api_call(messages, model_name="gpt-3.5-turbo", api_key="your-api-key"):
    """
    Direct API call without setting global LlamaIndex settings
    """
    llm = OpenAILike(
        model=model_name,
        api_base="https://www.ep.net/v1",
        api_key=api_key,
        is_chat_model=True
    )
    
    from llama_index.core.llms import ChatMessage, MessageRole
    
    chat_messages = []
    for msg in messages:
        role = MessageRole.USER if msg['role'] == 'user' else MessageRole.ASSISTANT
        if msg['role'] == 'system':
            role = MessageRole.SYSTEM
        chat_messages.append(ChatMessage(role=role, content=msg['content']))
    
    response = llm.chat(chat_messages)
    return response.message.content

# Configuration helper
class CustomLLMConfig:
    def __init__(self, base_url="https://www.ep.net/v1", api_key=None, default_model="gpt-3.5-turbo"):
        self.base_url = base_url
        self.api_key = api_key
        self.default_model = default_model
    
    def create_llm(self, model_name=None):
        return OpenAILike(
            model=model_name or self.default_model,
            api_base=self.base_url,
            api_key=self.api_key,
            is_chat_model=True,
            timeout=60,
            max_retries=3
        )