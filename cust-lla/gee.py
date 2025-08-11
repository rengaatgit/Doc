# filename: custom_llm_api_call.py

import os
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    PromptTemplate,
    Document
)
from llama_index.llms.openai_like import OpenAILike

# --- Configuration ---
# Replace with your actual API key and model name.
# It's recommended to use environment variables for security.
API_KEY = "YOUR_COMPANY_API_KEY" 
# This is the base URL for your company's LLM endpoint.
# LlamaIndex will automatically append '/chat/completions' to this base URL.
API_BASE_URL = "https://www.ep.net/v1" 
# This is the model name that will be sent in the JSON payload.
MODEL_NAME = "your-company-model-v1" 

# --- 1. Configure the Custom LLM ---
# This is the core part. We instantiate OpenAILike to connect to your custom endpoint.
# The 'model' parameter here will be included in the body of the POST request,
# not in the URL.
llm = OpenAILike(
    model=MODEL_NAME,
    api_base=API_BASE_URL,
    api_key=API_KEY,
    is_chat_model=True,  # Specify this for chat endpoints
    # You can add other parameters like temperature if needed
    # temperature=0.7 
)

print(f"✅ Configured to use model '{llm.model}' via endpoint '{llm.api_base}'")

# --- 2. Set the Custom LLM in LlamaIndex Settings ---
# By setting the llm in the global Settings, any LlamaIndex component
# that needs a language model will automatically use your custom one.
Settings.llm = llm
Settings.chunk_size = 512

# --- 3. Create a Simple RAG Pipeline to Test the API Call ---
# We'll create a simple index to demonstrate a real-world use case.

# Create a dummy document to query against.
# In a real application, you would load your data here, e.g., using SimpleDirectoryReader.
print("\nCreating a sample index...")
documents = [Document(text="The sky is blue because of a phenomenon called Rayleigh scattering.")]
index = VectorStoreIndex.from_documents(documents)

# --- 4. Create a Query Engine and Make the API Call ---
# The query engine will use the custom LLM from the global Settings.
query_engine = index.as_query_engine()

# Now, when we query the engine, LlamaIndex will format the request
# and send it to your custom endpoint: POST https://www.ep.net/v1/chat/completions
# with a JSON payload like: {"model": "your-company-model-v1", "messages": [...]}
print("🚀 Sending query to the custom LLM endpoint...")
query = "Why is the sky blue?"
response = query_engine.query(query)

# --- 5. Print the Response ---
print("\n--- Query ---")
print(query)
print("\n--- Response from Custom LLM ---")
print(str(response))

# You can also inspect the source of the information
# print("\n--- Source Nodes ---")
# print(response.source_nodes)