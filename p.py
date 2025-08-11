#!/usr/bin/env python3
"""
LC Compliance Checker using GPT-4o and LangGraph

This script:
1. Extracts data from LC using GPT-4o based on mappings.csv
2. Creates 30 validation tasks  
3. Uses LangGraph agent powered by GPT-4o to validate each task
4. Outputs results in tabular format

Requirements:
- pip install openai pandas langgraph
- Set OPENAI_API_KEY environment variable
- Place sampleLC.txt and mappings.csv in same directory
"""

import os
import re
import json
import time
import pandas as pd
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from openai import OpenAI

# LangGraph imports
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

# Configuration
OPENAI_MODEL = "gpt-4o"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY environment variable before running.")

client = OpenAI(api_key=OPENAI_API_KEY)

# Data structures
@dataclass
class ValidationTask:
    element1: str  # LC Section (key)
    element2: str  # Extracted LC value
    element3: str  # UCP600 Article(s)
    element4: str  # Articles text (dummy)
    element5: str  # ISBP745 Paragraph(s)  
    element6: str  # Paragraphs text (dummy)

class AgentState(TypedDict):
    tasks: List[ValidationTask]
    current_index: int
    results: List[Dict[str, str]]
    completed: bool

# Utility functions
def load_text_file(filename: str) -> str:
    """Load text file with encoding detection"""
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            with open(filename, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not read {filename} with any encoding")

def load_csv_file(filename: str) -> pd.DataFrame:
    """Load CSV file with encoding detection"""
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            return pd.read_csv(filename, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not read {filename} with any encoding")

def extract_lc_data(lc_text: str, lc_sections: List[str]) -> Dict[str, str]:
    """
    Use GPT-4o to extract values from LC text for each section
    """
    system_prompt = """You are an expert in documentary trade finance, specifically Letter of Credit (LC) documents, UCP600, and ISBP745.

Your task is to extract specific information from the provided Letter of Credit document.

Instructions:
1. Carefully read the LC document
2. For each requested LC section, extract the corresponding value from the document
3. If a section is not found or not applicable, return an empty string
4. Return your response as a valid JSON object with LC section names as keys and extracted values as strings

Be precise and extract exactly what appears in the document."""

    user_prompt = f"""
LC Document:
{lc_text}

Please extract values for the following LC sections:
{json.dumps(lc_sections, indent=2)}

Return a JSON object with each section name as key and the extracted value as string value.
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            extracted_data = json.loads(json_match.group())
            return extracted_data
        else:
            # Fallback: create empty dict
            return {section: "" for section in lc_sections}
            
    except Exception as e:
        print(f"Error in extraction: {e}")
        return {section: "" for section in lc_sections}

def validate_compliance(element1: str, element2: str, element4: str, element6: str) -> Tuple[str, str]:
    """
    Use GPT-4o to validate compliance of extracted LC value against UCP600/ISBP745 requirements
    """
    system_prompt = """You are a senior trade finance compliance officer with expertise in UCP600 and ISBP745 regulations.

Your task is to evaluate whether an extracted value from a Letter of Credit complies with the specified UCP600 Articles and ISBP745 Paragraphs.

You must provide:
1. A clear compliance decision: "COMPLIANT" or "NON-COMPLIANT" 
2. Brief, actionable remarks explaining your decision

Be strict in your assessment and base decisions on trade finance best practices."""

    user_prompt = f"""
Please evaluate the following for compliance:

LC FIELD: {element1}
EXTRACTED VALUE: {element2}

REFERENCE STANDARDS:
- UCP600 Articles Text: {element4}
- ISBP745 Paragraphs Text: {element6}

Instructions:
1. Check if the extracted LC value complies with both reference standards
2. Consider completeness, format, and content requirements
3. If the extracted value is empty or insufficient, mark as NON-COMPLIANT
4. If reference standards are dummy/placeholder text, make reasonable assessment

Provide your response in this JSON format:
{{
    "compliance_status": "COMPLIANT" or "NON-COMPLIANT",
    "remarks": "Brief explanation of your decision (max 200 characters)"
}}
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            status = result.get("compliance_status", "NON-COMPLIANT")
            remarks = result.get("remarks", "Assessment failed")
            return status, remarks
        else:
            # Fallback parsing
            if "COMPLIANT" in content and "NON-COMPLIANT" not in content:
                return "COMPLIANT", content[:200]
            else:
                return "NON-COMPLIANT", content[:200]
                
    except Exception as e:
        return "NON-COMPLIANT", f"Validation error: {str(e)[:150]}"

# LangGraph nodes
def process_task_node(state: AgentState) -> AgentState:
    """Process one validation task"""
    current_index = state["current_index"]
    tasks = state["tasks"]
    results = state["results"]
    
    if current_index >= len(tasks):
        state["completed"] = True
        return state
    
    # Get current task
    task = tasks[current_index]
    
    print(f"Processing task {current_index + 1}/{len(tasks)}: {task.element1}")
    
    # Validate compliance using GPT-4o
    compliance_status, remarks = validate_compliance(
        task.element1, task.element2, task.element4, task.element6
    )
    
    # Add result to table
    result_row = {
        "LC Section": task.element1,           # column 1: element1
        "Extracted Value": task.element2,      # column 2: element2  
        "UCP600 Articles": task.element3,      # column 3: element3
        "ISBP745 Paragraphs": task.element5,   # column 4: element5
        "Compliance Status": compliance_status, # column 5: compliance status
        "Remarks": remarks                     # column 6: remarks
    }
    
    results.append(result_row)
    
    # Move to next task
    state["current_index"] = current_index + 1
    
    # Small delay to avoid rate limiting
    time.sleep(0.5)
    
    return state

def should_continue(state: AgentState) -> str:
    """Determine if agent should continue processing"""
    if state["completed"] or state["current_index"] >= len(state["tasks"]):
        return "end"
    else:
        return "continue"

def create_agent_graph() -> StateGraph:
    """Create LangGraph agent workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("process_task", process_task_node)
    
    # Set entry point
    workflow.set_entry_point("process_task")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "process_task",
        should_continue,
        {
            "continue": "process_task",
            "end": END
        }
    )
    
    return workflow.compile()

def main():
    """Main execution function"""
    print("🚀 Starting LC Compliance Checker")
    print("=" * 50)
    
    # Load files
    print("📁 Loading files...")
    try:
        lc_text = load_text_file("sampleLC.txt")
        mappings_df = load_csv_file("mappings.csv")
        print(f"✅ Loaded LC document ({len(lc_text)} characters)")
        print(f"✅ Loaded mappings ({len(mappings_df)} rows)")
    except Exception as e:
        print(f"❌ Error loading files: {e}")
        return
    
    # Validate mappings structure
    required_columns = ["LC Section", "UCP600 Article(s)", "Articles text", 
                       "ISBP745 Paragraph(s)", "Paragraphs text"]
    
    for col in required_columns:
        if col not in mappings_df.columns:
            print(f"❌ Missing required column: {col}")
            return
    
    # Get first 30 rows (29 available in the CSV, so we'll use all available)
    df_subset = mappings_df.head(30)
    print(f"📋 Processing {len(df_subset)} validation tasks")
    
    # Extract LC data using GPT-4o
    print("🤖 Extracting LC data using GPT-4o...")
    lc_sections = df_subset["LC Section"].tolist()
    extracted_dict = extract_lc_data(lc_text, lc_sections)
    print(f"✅ Extracted data for {len(extracted_dict)} sections")
    
    # Create validation tasks
    print("📝 Creating validation tasks...")
    tasks = []
    
    for _, row in df_subset.iterrows():
        task = ValidationTask(
            element1=str(row["LC Section"]),
            element2=extracted_dict.get(str(row["LC Section"]), ""),
            element3=str(row["UCP600 Article(s)"]),
            element4=str(row["Articles text"]),  # dummy data for now
            element5=str(row["ISBP745 Paragraph(s)"]),
            element6=str(row["Paragraphs text"])  # dummy data for now
        )
        tasks.append(task)
    
    print(f"✅ Created {len(tasks)} validation tasks")
    
    # Initialize agent state
    initial_state: AgentState = {
        "tasks": tasks,
        "current_index": 0,
        "results": [],
        "completed": False
    }
    
    # Create and run agent
    print("🤖 Starting LangGraph agent for validation...")
    agent = create_agent_graph()
    
    try:
        final_state = agent.invoke(initial_state)
        results = final_state["results"]
        
        # Display results
        print("\n" + "=" * 80)
        print("📊 VALIDATION RESULTS")
        print("=" * 80)
        
        results_df = pd.DataFrame(results)
        print(results_df.to_string(index=False, max_colwidth=50))
        
        # Save results
        output_file = "lc_validation_results.csv"
        results_df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
        
        # Summary statistics
        total_tasks = len(results)
        compliant_tasks = len([r for r in results if r["Compliance Status"] == "COMPLIANT"])
        compliance_rate = (compliant_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        print(f"\n📈 SUMMARY:")
        print(f"   Total tasks processed: {total_tasks}")
        print(f"   Compliant: {compliant_tasks}")
        print(f"   Non-compliant: {total_tasks - compliant_tasks}")
        print(f"   Compliance rate: {compliance_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        return
    
    print("\n✅ LC Compliance Check completed successfully!")

if __name__ == "__main__":
    main()