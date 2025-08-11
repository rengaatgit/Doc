import os
import requests
from typing import List, Dict, Any
from typing_extensions import TypedDict
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime

# --- Configuration ---
# This script is designed to call a custom LLM API endpoint.
# The endpoint has a generic URL, and the specific model is chosen
# by including a "model" key in the JSON payload of the POST request.

# --- State Definition ---
# The state of our graph is a list of messages, which is a standard
# pattern in LangGraph for conversational agents.
class AgentState(TypedDict):
    messages: List[BaseMessage]

# --- Runtime Context Definition ---
# This defines the configuration that can be passed to the graph at runtime.
# It allows for dynamic configuration of the API endpoint, model, and other
# parameters without hardcoding them or including them in the agent's state.
class AgentContext(TypedDict, total=False):
    api_base: str
    api_key: str
    model: str
    temperature: float
    timeout: float

# --- Custom LLM Node ---
# This function is a node in our LangGraph. It is responsible for calling
# the custom LLM API with the correct payload structure.
def call_custom_llm(state: AgentState, runtime: Runtime[AgentContext]) -> Dict[str, Any]:
    """
    This node calls the company's generic LLM endpoint.
    It reads the API base, key, and model from the runtime context.
    """
    # Get the current conversation history from the state
    current_messages = state['messages']

    # Get configuration from the runtime context, with fallbacks to environment variables or defaults
    context = runtime.context or {}
    api_base = context.get("api_base", os.getenv("COMPANY_API_BASE", "https://www.ep.net"))
    api_key = context.get("api_key", os.getenv("COMPANY_API_KEY"))
    model_name = context.get("model", "default-model-name")
    temperature = context.get("temperature", 0.7)
    timeout = context.get("timeout", 120.0)

    # Prepare the request for the custom endpoint
    endpoint_url = f"{api_base.rstrip('/')}/v1/chat/completion"

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Convert LangChain message objects to a list of dictionaries for the JSON payload
    payload_messages = [message.dict() for message in current_messages]

    # The model name is part of the payload, as specified
    payload = {
        "model": model_name,
        "messages": payload_messages,
        "temperature": temperature,
    }

    # Make the API call
    try:
        response = requests.post(endpoint_url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise an exception for bad status codes
        response_data = response.json()

        # Assuming the API response is similar to OpenAI's format:
        # {"choices": [{"message": {"role": "assistant", "content": "..."}}]}
        # Adjust the parsing here if your API's response format is different.
        ai_response_content = response_data["choices"][0]["message"]["content"]
        ai_message = AIMessage(content=ai_response_content)

        # Return the new message to be added to the state
        return {"messages": [ai_message]}

    except requests.exceptions.RequestException as e:
        print(f"Error calling the custom LLM API: {e}")
        # Return an error message to be added to the state
        error_message = AIMessage(content=f"Sorry, I encountered an error: {e}")
        return {"messages": [error_message]}

# --- Graph Definition ---
# We define a simple graph with a single node that calls our custom LLM.
# The graph starts, calls the LLM, and then ends.
workflow = StateGraph(AgentState, context_schema=AgentContext)

# Add the custom LLM caller function as a node in the graph
workflow.add_node("llm_call", call_custom_llm)

# Set the entry point of the graph
workflow.set_entry_point("llm_call")

# The graph ends after the LLM call is complete
workflow.add_edge("llm_call", END)

# Compile the graph into a runnable object
app = workflow.compile()

# --- Example Usage ---
if __name__ == "__main__":
    # Define the initial user input
    initial_input = {"messages": [{"role": "user", "content": "What is the capital of France?"}]}

    # Define the runtime configuration, including the model to be used
    runtime_config = {
        "context": {
            "api_base": "www.ep.net", # Your company's API base URL
            "api_key": "YOUR_SECRET_API_KEY", # Your secret API key
            "model": "advanced-model-alpha", # The specific model to use for this request
            "temperature": 0.5,
        }
    }

    # Invoke the graph with the input and runtime configuration
    # The `app.stream()` method allows you to see the output from each step.
    for event in app.stream(initial_input, runtime_config):
        for key, value in event.items():
            print(f"--- Output from node: {key} ---")
            print(value)
            print("\n")

    # You can also use `invoke` for a final result
    print("--- Final Result ---")
    final_result = app.invoke(initial_input, runtime_config)
    print(final_result['messages'][-1].content)
