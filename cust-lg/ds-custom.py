import os
import csv
import json
import requests
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph
import pandas as pd
from typing import List, Optional, Dict, Any

# Custom LLM class for your company's endpoint
class CustomChatModel(BaseChatModel):
    endpoint_url: str = "https://www.ep.net/v1/chat/completion"
    model_name: str = "your-model-name"  # Replace with your model name
    api_key: str = os.getenv("COMPANY_API_KEY")  # Set your API key in env
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Convert LangChain messages to endpoint format
        formatted_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            elif isinstance(message, SystemMessage):
                role = "system"
            else:
                continue
            formatted_messages.append({"role": role, "content": message.content})
        
        # Prepare payload with model name
        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": 0.0,
            "max_tokens": 2000
        }
        
        # Add stop sequences if provided
        if stop:
            payload["stop"] = stop
        
        # Add any additional parameters
        payload.update(kwargs)
        
        # Make API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(self.endpoint_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise ValueError(f"API call failed: {response.text}")
        
        response_data = response.json()
        
        # Extract content from first choice
        content = response_data["choices"][0]["message"]["content"]
        message = AIMessage(content=content)
        return ChatResult(generations=[ChatGeneration(message=message)])
    
    @property
    def _llm_type(self) -> str:
        return "custom_company_llm"

# Initialize custom LLM
llm = CustomChatModel()

# Read files function
def read_files():
    with open('mappings.csv', 'r') as f:
        mappings = list(csv.DictReader(f))
    with open('sampleLC.txt', 'r') as f:
        lc_text = f.read()
    return mappings, lc_text

# Extract LC data using custom LLM
def extract_lc_data(lc_text: str) -> Dict[str, str]:
    keys = [
        "Credit Type", "UCP Reference Statement", "LC Number", "Date of Issue",
        "Issuing Bank Details", "Applicant Details", "Beneficiary Details", "Amount",
        "Expiry Date", "Expiry Place", "Availability (Sight Draft)", "Incoterm (CIF)",
        "Latest Shipment Date", "Port of Loading", "Port of Discharge", "Goods Description",
        "Commercial Invoice", "Bill of Lading", "Insurance Document", "Certificate of Origin",
        "Packing List", "Presentation Period (21 days)", "Partial Shipments", "Transshipment",
        "Banking Charges", "Invoice LC Number Requirement", "Document Language (English)",
        "Confirmation", "Authorized Signature"
    ]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a trade finance expert specialized in Letters of Credit."),
        ("human", f"""
        Extract data from this Letter of Credit text. Return ONLY JSON with keys from this list:
        {keys}
        
        Rules:
        1. Use exact keys provided
        2. Return "Not Found" for missing data
        3. Keep values verbatim from text
        4. Handle multi-line values appropriately
        
        LC Text:
        '''{lc_text}'''
        """)
    ])
    
    chain = prompt | llm
    response = chain.invoke({})
    return json.loads(response.content)

# Create validation tasks
def create_tasks(mappings, lc_data):
    tasks = []
    for row in mappings:
        key = row['LC Section']
        tasks.append({
            "key": key,
            "value": lc_data.get(key, "Not Found"),
            "ucp_articles": row['UCP600 Article(s)'],
            "articles_text": row['Articles text'],
            "isbp_paragraphs": row['ISBP745 Paragraph(s)'],
            "paragraphs_text": row['Paragraphs text']
        })
    return tasks

# Validate single task
def validate_task(task: Dict) -> Dict:
    prompt = f"""
    **Trade Finance Compliance Validation**
    Validate this LC field against UCP600 and ISBP745 requirements:

    Field: {task['key']}
    Value: {task['value']}
    UCP600 Reference: Articles {task['ucp_articles']} 
    UCP600 Rules: {task['articles_text']}
    ISBP745 Reference: Paragraphs {task['isbp_paragraphs']}
    ISBP745 Rules: {task['paragraphs_text']}

    Instructions:
    1. Check if value complies with BOTH UCP600 and ISBP745 requirements
    2. Return JSON format: {{"status": "Compliant"|"Non-Compliant", "remarks": "<detailed explanation>"}}
    3. Consider:
       - Exact textual compliance
       - Contextual interpretation
       - Banking practice standards
    4. For 'Not Found' values, check if mandatory per rules
    """
    
    # Create HumanMessage with the prompt
    human_message = HumanMessage(content=prompt)
    
    # Call LLM through your endpoint
    response = llm.generate(messages=[[human_message]])
    
    # Extract content from response
    content = response.generations[0][0].text
    result = json.loads(content)
    
    return {
        "key": task["key"],
        "value": task["value"],
        "ucp_articles": task["ucp_articles"],
        "isbp_paragraphs": task["isbp_paragraphs"],
        "status": result["status"],
        "remarks": result["remarks"]
    }

# LangGraph state and graph definition
class AgentState(dict):
    @property
    def tasks(self) -> List[Dict]:
        return self.get("tasks", [])
    
    @property
    def results(self) -> List[Dict]:
        return self.get("results", [])

def process_task(state: AgentState) -> Dict:
    task = state["tasks"][0]
    result = validate_task(task)
    return {
        "tasks": state["tasks"][1:],
        "results": state["results"] + [result]
    }

def should_continue(state: AgentState) -> str:
    return "tasks" if state["tasks"] else "end"

# Main execution flow
if __name__ == "__main__":
    # Set your API key
    os.environ["COMPANY_API_KEY"] = "your_api_key_here"  # Replace with your actual key
    
    # Prepare data
    mappings, lc_text = read_files()
    lc_data = extract_lc_data(lc_text)
    tasks = create_tasks(mappings, lc_data)
    
    # Initialize state
    initial_state = AgentState({"tasks": tasks, "results": []})
    
    # Build workflow
    workflow = StateGraph(AgentState)
    workflow.add_node("process_task", process_task)
    workflow.add_conditional_edges(
        "process_task",
        should_continue,
        {
            "tasks": "process_task",
            "end": END
        }
    )
    workflow.set_entry_point("process_task")
    app = workflow.compile()
    
    # Execute validation
    for step in app.stream(initial_state):
        if "__end__" not in step:
            remaining = len(step["process_task"]["tasks"])
            print(f"Processed task. Remaining: {remaining}")
    
    # Generate final report
    final_state = step["__end__"]
    df = pd.DataFrame(final_state["results"])
    
    # Create final table with required columns
    final_table = pd.DataFrame({
        "LC Section": df["key"],
        "Extracted Value": df["value"],
        "UCP Articles": df["ucp_articles"],
        "ISBP Paragraphs": df["isbp_paragraphs"],
        "Compliant Status": df["status"],
        "Remarks": df["remarks"]
    })
    
    final_table.to_csv("lc_validation_report.csv", index=False)
    print("Validation report saved to lc_validation_report.csv")
    print("\nSample validation results:")
    print(final_table.head())
    
    
    -----------------------------
    
    class CustomChatModel(BaseChatModel):
    endpoint_url: str = "https://www.ep.net/v1/chat/completion"
    model_name: str = "your-model-name"
    
    def _generate(self, messages, **kwargs) -> ChatResult:
        # Convert messages to endpoint format
        formatted_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                role = "user"
            # ... other message types
        
        # Prepare payload with model name
        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            # ... other parameters
        }
        
        # Make API call
        response = requests.post(self.endpoint_url, headers=headers, json=payload)
        
        # Process response
        content = response.json()["choices"][0]["message"]["content"]
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
    
    
    ----------------------------------
    
    def validate_task(task):
    # ... create prompt
    human_message = HumanMessage(content=prompt)
    response = llm.generate(messages=[[human_message]])
    content = response.generations[0][0].text
    # ... process response
    
    -------------------------------
    
    os.environ["COMPANY_API_KEY"] = "your_api_key_here"
llm = CustomChatModel()  # Uses your endpoint


---------------------------------

pip install langchain-core langgraph requests pandas