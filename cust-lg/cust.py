import requests
from typing import List, Dict, Any, Optional
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

class CustomLLM(LLM):
    """Custom LLM wrapper for your endpoint."""
    
    base_url: str = "https://www.ep.net/v1/chat/completion"
    model_name: str = "your-model-name"  # Set your default model
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Make API call to your custom endpoint."""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Format payload with model in body
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            **kwargs
        }
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            # Adjust based on your API response format
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API call failed: {str(e)}")
    
    @property
    def _llm_type(self) -> str:
        return "custom_llm"

# For Chat models (recommended for agents)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

class CustomChatModel(BaseChatModel):
    """Custom Chat Model for better agent integration."""
    
    base_url: str = "https://www.ep.net/v1/chat/completion"
    model_name: str = "your-model-name"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Any:
        """Generate response from messages."""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Convert LangChain messages to API format
        api_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                api_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                api_messages.append({"role": "system", "content": msg.content})
        
        payload = {
            "model": self.model_name,
            "messages": api_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            **kwargs
        }
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            from langchain_core.outputs import ChatGeneration, ChatResult
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API call failed: {str(e)}")
    
    @property
    def _llm_type(self) -> str:
        return "custom_chat_model"

# Usage in LangGraph Agent
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Initialize your custom model
llm = CustomChatModel(
    model_name="your-actual-model-name",
    api_key="your-api-key-if-needed",
    temperature=0.7
)

# Example agent state
class AgentState(TypedDict):
    messages: List[BaseMessage]
    next: str

def agent_node(state: AgentState):
    """Agent node using custom LLM."""
    messages = state["messages"]
    response = llm.invoke(messages)
    return {
        "messages": messages + [response],
        "next": END
    }

# Build the graph
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")
graph.add_edge("agent", END)

app = graph.compile()

# Run the agent
if __name__ == "__main__":
    initial_state = {
        "messages": [HumanMessage(content="Hello, how are you?")],
        "next": ""
    }
    
    result = app.invoke(initial_state)
    print(result["messages"][-1].content)