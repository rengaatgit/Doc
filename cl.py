import pandas as pd
import json
from typing import Dict, List, Any, TypedDict
from langgraph.graph import StateGraph, END
from openai import OpenAI
import os

# Set your OpenAI API key
# os.environ["OPENAI_API_KEY"] = "your-api-key-here"

class ValidationState(TypedDict):
    tasks: List[Dict[str, Any]]
    current_task_index: int
    results: List[Dict[str, Any]]
    lc_data: Dict[str, Any]
    completed: bool

class LCComplianceValidator:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        
    def extract_lc_data(self, lc_content: str, mappings_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract LC data using GPT-4o based on mapping requirements"""
        
        extraction_fields = mappings_df['LC Section'].tolist()
        
        prompt = f"""
        You are a trade finance expert. Extract the following information from the Letter of Credit below:
        
        Fields to extract: {extraction_fields}
        
        Letter of Credit:
        {lc_content}
        
        Return a JSON object with the field names as keys and extracted values as values.
        If a field is not found, use "Not Specified" as the value.
        
        Example format:
        {{
            "Credit Type": "IRREVOCABLE DOCUMENTARY LETTER OF CREDIT",
            "UCP Reference Statement": "Subject to UCP 600",
            "LC Number": "LC2025-0001"
        }}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            # Fallback parsing if JSON is malformed
            content = response.choices[0].message.content
            # Extract JSON from response if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
    
    def validate_compliance(self, field_name: str, extracted_value: str, 
                          articles_text: str, paragraphs_text: str) -> Dict[str, Any]:
        """Validate compliance using GPT-4o"""
        
        prompt = f"""
        As a trade finance compliance expert, evaluate whether the extracted LC field value complies with UCP600 articles and ISBP745 paragraphs.
        
        Field: {field_name}
        Extracted Value: {extracted_value}
        UCP600 Articles Requirements: {articles_text}
        ISBP745 Paragraphs Requirements: {paragraphs_text}
        
        Analyze compliance and respond in JSON format:
        {{
            "compliant": true/false,
            "remarks": "Detailed explanation of compliance status and any issues found"
        }}
        
        Consider:
        - Does the extracted value meet UCP600 article requirements?
        - Does it align with ISBP745 paragraph guidelines?
        - Are there any compliance gaps or issues?
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return {
                "compliant": result.get("compliant", False),
                "remarks": result.get("remarks", "Unable to determine compliance")
            }
        except:
            return {
                "compliant": False,
                "remarks": "Error in compliance validation"
            }

def create_tasks(mappings_df: pd.DataFrame, lc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create validation tasks from mappings"""
    tasks = []
    
    for _, row in mappings_df.iterrows():
        task = {
            "field_name": row['LC Section'],  # element1
            "extracted_value": lc_data.get(row['LC Section'], "Not Specified"),  # element2
            "ucp_articles": row['UCP600 Article(s)'],  # element3
            "articles_text": row['Articles text'],  # element4
            "isbp_paragraphs": row['ISBP745 Paragraph(s)'],  # element5
            "paragraphs_text": row['Paragraphs text']  # element6
        }
        tasks.append(task)
    
    return tasks

def initialize_state(state: ValidationState) -> ValidationState:
    """Initialize the validation state"""
    print(f"Initializing validation for {len(state['tasks'])} tasks...")
    return {
        **state,
        "current_task_index": 0,
        "results": [],
        "completed": False
    }

def process_task(state: ValidationState) -> ValidationState:
    """Process current validation task"""
    if state["current_task_index"] >= len(state["tasks"]):
        return {**state, "completed": True}
    
    current_task = state["tasks"][state["current_task_index"]]
    print(f"Processing task {state['current_task_index'] + 1}: {current_task['field_name']}")
    
    # Initialize validator (you'll need to pass the API key)
    validator = LCComplianceValidator(os.getenv("OPENAI_API_KEY", "your-api-key-here"))
    
    # Validate compliance
    compliance_result = validator.validate_compliance(
        current_task["field_name"],
        current_task["extracted_value"],
        current_task["articles_text"],
        current_task["paragraphs_text"]
    )
    
    # Create result record
    result = {
        "Field Name": current_task["field_name"],
        "Extracted Value": current_task["extracted_value"],
        "UCP600 Articles": current_task["ucp_articles"],
        "ISBP745 Paragraphs": current_task["isbp_paragraphs"],
        "Compliant": compliance_result["compliant"],
        "Remarks": compliance_result["remarks"]
    }
    
    # Update state
    new_results = state["results"] + [result]
    
    return {
        **state,
        "results": new_results,
        "current_task_index": state["current_task_index"] + 1
    }

def check_completion(state: ValidationState) -> str:
    """Check if all tasks are completed"""
    if state["completed"] or state["current_task_index"] >= len(state["tasks"]):
        return "end"
    return "process_task"

def main():
    """Main execution function"""
    
    # Load data
    print("Loading data...")
    mappings_df = pd.read_csv('mappings.csv')
    
    with open('sampleLC.txt', 'r') as f:
        lc_content = f.read()
    
    # Initialize validator
    validator = LCComplianceValidator(os.getenv("OPENAI_API_KEY", "your-api-key-here"))
    
    # Extract LC data
    print("Extracting LC data...")
    lc_data = validator.extract_lc_data(lc_content, mappings_df)
    print(f"Extracted {len(lc_data)} fields from LC")
    
    # Create tasks
    tasks = create_tasks(mappings_df, lc_data)
    print(f"Created {len(tasks)} validation tasks")
    
    # Create LangGraph workflow
    workflow = StateGraph(ValidationState)
    
    # Add nodes
    workflow.add_node("initialize", initialize_state)
    workflow.add_node("process_task", process_task)
    
    # Add edges
    workflow.add_edge("initialize", "process_task")
    workflow.add_conditional_edges("process_task", check_completion, {
        "process_task": "process_task",
        "end": END
    })
    
    # Set entry point
    workflow.set_entry_point("initialize")
    
    # Compile workflow
    app = workflow.compile()
    
    # Initialize state
    initial_state = ValidationState(
        tasks=tasks,
        current_task_index=0,
        results=[],
        lc_data=lc_data,
        completed=False
    )
    
    # Run workflow
    print("Starting validation workflow...")
    final_state = app.invoke(initial_state)
    
    # Create results DataFrame
    results_df = pd.DataFrame(final_state["results"])
    
    # Display results
    print("\n" + "="*80)
    print("VALIDATION RESULTS")
    print("="*80)
    print(results_df.to_string(index=False, max_colwidth=50))
    
    # Save results
    results_df.to_csv('lc_compliance_results.csv', index=False)
    print(f"\nResults saved to 'lc_compliance_results.csv'")
    
    # Summary
    total_tasks = len(results_df)
    compliant_tasks = sum(results_df['Compliant'])
    non_compliant_tasks = total_tasks - compliant_tasks
    
    print(f"\nSUMMARY:")
    print(f"Total validations: {total_tasks}")
    print(f"Compliant: {compliant_tasks}")
    print(f"Non-compliant: {non_compliant_tasks}")
    print(f"Compliance rate: {(compliant_tasks/total_tasks)*100:.1f}%")

if __name__ == "__main__":
    # Set your OpenAI API key before running
    # os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"
    main()