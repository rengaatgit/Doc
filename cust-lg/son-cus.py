import os
import requests
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.runtime import Runtime

# ============================================================================
# LangGraph Agent for Custom Company LLM Endpoint
# ============================================================================
# This script demonstrates how to create a LangGraph agent that calls your
# company's custom LLM API where:
# 1. Endpoint is generic: www.ep.net/v1/chat/completion
# 2. Model name is specified in the JSON payload (not URL parameter)
# ============================================================================

class CompanyLLMContext(TypedDict, total=False):
    """Runtime context schema for dynamic model and API configuration"""
    api_base: str
    api_key: Optional[str]
    model: str
    temperature: float
    max_tokens: Optional[int]
    timeout: float

def call_company_llm(state: MessagesState, runtime: Runtime[CompanyLLMContext]) -> Dict[str, Any]:
    """
    LangGraph node that calls the company's generic LLM endpoint.
    
    Args:
        state: Current conversation state containing messages
        runtime: Runtime context with API configuration
        
    Returns:
        Dictionary with new messages to add to state
    """
    # Extract configuration from runtime context
    ctx = runtime.context or {}
    
    # API configuration with fallbacks
    api_base = ctx.get("api_base", os.getenv("COMPANY_API_BASE", "https://www.ep.net"))
    api_key = ctx.get("api_key", os.getenv("COMPANY_API_KEY"))
    model = ctx.get("model", "default-model")
    temperature = ctx.get("temperature", 0.7)
    max_tokens = ctx.get("max_tokens")
    timeout = ctx.get("timeout", 60.0)
    
    # Build the request
    url = f"{api_base.rstrip('/')}/v1/chat/completion"
    headers = {"Content-Type": "application/json"}
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Convert LangChain messages to API format
    api_messages = []
    for msg in state["messages"]:
        if hasattr(msg, 'content'):
            # LangChain message object
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            api_messages.append({
                "role": role,
                "content": msg.content
            })
        else:
            # Already in dict format
            api_messages.append(msg)
    
    # Build payload with model in the body (as per your spec)
    payload = {
        "model": model,
        "messages": api_messages,
        "temperature": temperature,
    }
    
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    try:
        # Make the API call
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Extract assistant response (assuming OpenAI-like format)
        # Adjust this section if your API has different response structure
        if "choices" in data and len(data["choices"]) > 0:
            assistant_content = data["choices"][0]["message"]["content"]
            assistant_message = AIMessage(content=assistant_content)
        else:
            # Fallback if response structure is different
            assistant_message = AIMessage(content="I received an unexpected response format.")
        
        return {"messages": [assistant_message]}
        
    except requests.exceptions.RequestException as e:
        # Handle API errors gracefully
        error_msg = f"API call failed: {str(e)}"
        error_message = AIMessage(content=f"Sorry, I encountered an error: {error_msg}")
        return {"messages": [error_message]}
    
    except (KeyError, IndexError) as e:
        # Handle response parsing errors
        error_msg = f"Failed to parse API response: {str(e)}"
        error_message = AIMessage(content=f"Sorry, I received an invalid response: {error_msg}")
        return {"messages": [error_message]}

# ============================================================================
# Graph Definition
# ============================================================================

# Create the graph with MessagesState and context schema
builder = StateGraph(MessagesState, context_schema=CompanyLLMContext)

# Add the LLM calling node
builder.add_node("llm", call_company_llm)

# Define the flow: START -> llm -> END
builder.add_edge(START, "llm")
builder.add_edge("llm", END)

# Compile the graph
agent = builder.compile()

# ============================================================================
# Example Usage
# ============================================================================

def run_example():
    """Example of how to use the agent with different models"""
    
    # Example 1: Basic conversation
    print("=== Example 1: Basic Conversation ===")
    
    initial_messages = [
        HumanMessage(content="Hello! What can you tell me about artificial intelligence?")
    ]
    
    result = agent.invoke(
        {"messages": initial_messages},
        context={
            "api_base": "https://www.ep.net",  # Your company endpoint
            "api_key": "your-api-key-here",    # Your API key
            "model": "company-gpt-4",          # Model name in payload
            "temperature": 0.7,
            "timeout": 30.0
        }
    )
    
    print("User:", initial_messages[0].content)
    print("Assistant:", result["messages"][-1].content)
    print("\n")
    
    # Example 2: Different model with conversation history
    print("=== Example 2: Different Model ===")
    
    # Continue conversation with a different model
    follow_up_messages = result["messages"] + [
        HumanMessage(content="Can you summarize that in one sentence?")
    ]
    
    result2 = agent.invoke(
        {"messages": follow_up_messages},
        context={
            "api_base": "https://www.ep.net",
            "api_key": "your-api-key-here",
            "model": "company-claude-3",       # Different model
            "temperature": 0.3,                # Lower temperature
            "max_tokens": 100,                 # Token limit
        }
    )
    
    print("User:", follow_up_messages[-1].content)
    print("Assistant:", result2["messages"][-1].content)
    print("\n")
    
    # Example 3: Streaming responses (if you want to see intermediate steps)
    print("=== Example 3: Streaming ===")
    
    streaming_messages = [
        HumanMessage(content="Tell me a short joke")
    ]
    
    for event in agent.stream(
        {"messages": streaming_messages},
        context={
            "api_base": "https://www.ep.net",
            "api_key": "your-api-key-here",
            "model": "company-llama-3",
            "temperature": 0.9,  # Higher temperature for creativity
        }
    ):
        for node_name, node_output in event.items():
            print(f"Node '{node_name}' output:")
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    print(f"  {msg.content}")
            print()

if __name__ == "__main__":
    # Set environment variables (optional, can be overridden in context)
    # os.environ["COMPANY_API_BASE"] = "https://www.ep.net"
    # os.environ["COMPANY_API_KEY"] = "your-api-key-here"
    
    # Run the examples
    run_example()
