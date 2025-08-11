import os
import csv
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
import pandas as pd

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Read files
def read_files():
    with open('mappings.csv', 'r') as f:
        mappings = list(csv.DictReader(f))
    with open('sampleLC.txt', 'r') as f:
        lc_text = f.read()
    return mappings, lc_text

# Extract LC data using LLM
def extract_lc_data(lc_text):
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
        ("system", "You are a trade finance expert specialized in Letters of Credit, UCP600 and ISBP745."),
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
def validate_task(task):
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
    
    response = llm.invoke([HumanMessage(content=prompt)])
    result = json.loads(response.content)
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
    def tasks(self):
        return self.get("tasks", [])
    
    @property
    def results(self):
        return self.get("results", [])

def process_task(state):
    task = state["tasks"][0]
    result = validate_task(task)
    return {
        "tasks": state["tasks"][1:],
        "results": state["results"] + [result]
    }

def should_continue(state):
    return "tasks" if state["tasks"] else "end"

# Main execution
if __name__ == "__main__":
    # Set your OpenAI API key
    os.environ["OPENAI_API_KEY"] = "sk-xxx"
    
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
    df.to_csv("lc_validation_report.csv", index=False)
    print("Validation report saved to lc_validation_report.csv")
    print("\nSample validation results:")
    print(df.head())