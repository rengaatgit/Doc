import os
import requests
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.runtime import Runtime
from langchain_core.messages import AnyMessage, AIMessage

# 1) Define runtime context schema (no state pollution)
class ContextSchema(TypedDict, total=False):
    api_base: str          # e.g., "https://www.ep.net"
    api_key: str           # if needed
    model: str             # e.g., "my-llm-1"
    temperature: float     # optional
    timeout: float         # optional seconds

# 2) The node that calls your generic endpoint
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

    # Build payload with model INSIDE the body as per your spec
    payload = {
        "model": model,
        "messages": [m if isinstance(m, dict) else m.dict() for m in state["messages"]],
        "temperature": temperature,
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    # Adjust parsing to your API’s shape; this mirrors OpenAI-like responses
    # Expect: {"choices":[{"message":{"role":"assistant","content":"..."}]}]
    choice = data["choices"][0]["message"]
    ai_msg = AIMessage(content=choice.get("content", ""), additional_kwargs=choice)

    return {"messages": [ai_msg]}

# 3) Build graph with context schema
builder = StateGraph(MessagesState, context_schema=ContextSchema)
builder.add_node("llm", call_llm_node)
builder.add_edge(START, "llm")
builder.add_edge("llm", END)
graph = builder.compile()

# 4) Invoke with model in context (not in state)
# messages should be list of {"role": "...", "content": "..."} or LangChain message objects
result = graph.invoke(
    {"messages": [{"role": "user", "content": "Hello!"}]},
    context={
        "api_base": "https://www.ep.net",
        "api_key": "<YOUR_KEY>",
        "model": "your-llm-model-name",
        "temperature": 0.3,
    },
)
print(result["messages"][-1].content)
