import requests

def call_llm(messages, model_name, **kwargs):
    payload = {
        "model": model_name,
        "messages": messages,
        # add other parameters here (e.g., temperature)
    }
    response = requests.post("https://www.ep.net/v1/chat/completion", json=payload)
    return response.json()  # adjust as needed for your API's response format



def llm_node(state, runtime):
    # Get messages and model selection from state or runtime context
    messages = state["messages"]
    model_name = runtime.context.get("model", "default-model")
    result = call_llm(messages, model_name)
    # Parse the model output; assume API returns {'choices': [{'message': {...}}]}
    new_message = result['choices'][0]['message']
    return {"messages": state["messages"] + [new_message]}



from langgraph.graph import StateGraph, START, END

# Define your state schema
from typing_extensions import TypedDict

class MessagesState(TypedDict):
    messages: list

# Optionally define a context schema for model selection
class ContextSchema(TypedDict):
    model: str

builder = StateGraph(MessagesState, context_schema=ContextSchema)
builder.add_node("llm_node", llm_node)
builder.add_edge(START, "llm_node")
builder.add_edge("llm_node", END)
graph = builder.compile()

# Usage - specify the model at runtime
result = graph.invoke({"messages": [{"role": "user", "content": "Hello!"}]}, context={"model": "your-llm-model-name"})
