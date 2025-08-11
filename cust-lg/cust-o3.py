"""
one_file_langgraph_agent.py
—————————————
LangGraph example that calls a proprietary LLM endpoint whose
URL is fixed and whose model is passed inside the JSON payload.

Endpoint spec (company-internal):
    POST https://www.ep.net/v1/chat/completion
    Headers:
        Content-Type: application/json
        Authorization: Bearer <API_KEY>          # optional
    Body:
        {
          "model": "<model-name>",
          "messages": [...],
          "temperature": 0.7,
          ...
        }

This script shows:
1. A runtime-context schema for transport-level config (model, key, etc.).
2. A single LangGraph node that builds the payload and hits the endpoint.
3. Compilation of a minimal graph that echoes the assistant’s reply.
4. An example `graph.invoke` call that supplies the model name at runtime.
"""
import os
import requests
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.runtime import Runtime
from langchain_core.messages import AIMessage, BaseMessage

# ──────────────────────────────────────────────────────────────────────────────
# 1.  Runtime-context schema  (NOT stored in state, changes per invocation)
# ──────────────────────────────────────────────────────────────────────────────
class Ctx(TypedDict, total=False):
    api_base: str           # e.g. "https://www.ep.net"
    api_key: str            # bearer token, if required
    model: str              # model name the backend expects
    temperature: float      # optional sampling params
    timeout: float          # request timeout in seconds


# ──────────────────────────────────────────────────────────────────────────────
# 2.  Node that performs the HTTP request
# ──────────────────────────────────────────────────────────────────────────────
def llm_node(state: MessagesState, runtime: Runtime[Ctx]):
    """Add an assistant reply by POSTing to company LLM endpoint."""
    ctx: Ctx = runtime.context or {}

    # Transport config with sensible fallbacks
    api_base     = ctx.get("api_base", os.getenv("EP_API_BASE", "https://www.ep.net"))
    api_key      = ctx.get("api_key",  os.getenv("EP_API_KEY"))
    model        = ctx.get("model",    "default-model")
    temperature  = ctx.get("temperature", 0.7)
    timeout      = ctx.get("timeout", 60.0)

    # Endpoint URL & headers
    url = f"{api_base.rstrip('/')}/v1/chat/completion"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Build request body.  Convert LangChain message objects → dicts if needed.
    messages = [
        m.dict() if hasattr(m, "dict") else m
        for m in state["messages"]
    ]
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    # Call the backend
    resp = requests.post(url, json=body, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    # Parse response → LangChain AIMessage (adjust if your schema differs)
    choice = data["choices"][0]["message"]          # {'role':'assistant', ...}
    ai_msg = AIMessage(content=choice.get("content", ""),
                       additional_kwargs=choice)

    # Return state delta expected by LangGraph
    return {"messages": [ai_msg]}


# ──────────────────────────────────────────────────────────────────────────────
# 3.  Assemble minimal graph (START → llm_node → END)
# ──────────────────────────────────────────────────────────────────────────────
builder = StateGraph(MessagesState, context_schema=Ctx)
builder.add_node("llm", llm_node)
builder.add_edge(START, "llm")
builder.add_edge("llm", END)
graph = builder.compile()


# ──────────────────────────────────────────────────────────────────────────────
# 4.  Demo run — provide model name & key at invocation time
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    user_prompt: BaseMessage | dict = {"role": "user", "content": "Hello!"}
    out = graph.invoke(
        {"messages": [user_prompt]},
        context={
            "api_base": "https://www.ep.net",
            "api_key":  "<YOUR_API_KEY>",
            "model":    "my-company-llm-002",
            "temperature": 0.3,
        },
    )
    assistant_reply = out["messages"][-1].content
    print("Assistant:", assistant_reply)


