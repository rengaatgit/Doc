import os
import requests
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.runtime import Runtime
from langchain_core.messages import AIMessage

class ContextSchema(TypedDict, total=False):
    api_base: str
    api_key: str
    model: str
    temperature: float
    timeout: float

def call_llm_node(state: MessagesState, runtime: Runtime[ContextSchema]):
    ctx = runtime.context or {}
    api_base = ctx.get("api_base", os.getenv("EP_API_BASE", "https://www.ep.net"))
    api_key = ctx.get("api_key", os.getenv("EP_API_KEY"))
    model = ctx.get("model", "default-model")
    temperature = ctx.get("temperature", 0.7)
    timeout = ctx.get("timeout", 60.0)

    url = f"{api_base}/v1/chat/completion"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,                      # model in payload (not URL param)
        "messages": state["messages"],       # pass messages as-is or adapt format
        "temperature": temperature,
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    # Parse to AIMessage. Adjust fields based on your API’s shape.
    choice = data["choices"][0]["message"]
    return {"messages": [AIMessage(content=choice.get("content", ""), additional_kwargs=choice)]}

builder = StateGraph(MessagesState, context_schema=ContextSchema)
builder.add_node("llm", call_llm_node)
builder.add_edge(START, "llm")
builder.add_edge("llm", END)
graph = builder.compile()

# Per-invocation dynamic model and transport
result = graph.invoke(
    {"messages": [{"role": "user", "content": "Hi"}]},
    context={"api_base": "https://www.ep.net", "api_key": "<KEY>", "model": "my-model", "temperature": 0.2},
)
