#!/usr/bin/env python3
"""
LC Compliance Checker using GPT-4o and LangGraph

This script implements the complete workflow:
1. Uses GPT-4o to extract LC data based on mappings.csv
2. Creates 30 validation tasks with 6 elements each
3. Uses LangGraph agent to process tasks sequentially
4. Validates compliance using GPT-4o against UCP600/ISBP745 rules
5. Outputs results in 6-column table format

Requirements:
- pip install openai pandas langgraph typing-extensions
- Set OPENAI_API_KEY environment variable
- Place sampleLC.txt and mappings.csv in same directory

Usage:
    python lc_compliance_checker.py
"""

import os
import re
import json
import time
import pandas as pd
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
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
    element1: str  # LC Section (key from dictionary)
    element2: str  # Extracted LC value (value from dictionary)
    element3: str  # UCP600 Article(s) - 2nd column of mapping.csv
    element4: str  # Articles text - 3rd column of mapping.csv (dummy)
    element5: str  # ISBP745 Paragraph(s) - 4th column of mapping.csv
    element6: str  # Paragraphs text - 5th column of mapping.csv (dummy)

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

def extract_lc_data_with_gpt4o(lc_text: str, lc_sections: List[str]) -> Dict[str, str]:
    """
    Use GPT-4o to extract values from LC text for each section in mapping.csv
    Creates dictionary with first column of mapping.csv as key and extracted value as value
    """
    system_prompt = """You are an expert in documentary trade finance, specifically Letter of Credit (LC) documents, UCP600, and ISBP745.

Your task is to extract specific information from the provided Letter of Credit document based on the requested LC sections.

Instructions:
1. Carefully analyze the LC document
2. For each requested LC section, extract the exact corresponding value from the document
3. If a section is not found or not clearly identifiable, return an empty string
4. Be precise and extract exactly what appears in the document without interpretation
5. Return your response as a valid JSON object with LC section names as keys and extracted values as strings

Important: Focus on accuracy and completeness of extraction."""

    user_prompt = f"""
Letter of Credit Document:
{lc_text}

Please extract values for the following LC sections and return as JSON:
{json.dumps(lc_sections, indent=2)}

Example format:
{{
    "Credit Type": "IRREVOCABLE DOCUMENTARY LETTER OF CREDIT",
    "LC Number": "LC2025-0001",
    "Amount": "USD 110,000 (One Hundred Ten Thousand U.S. Dollars)",
    ...
}}

Return only the JSON object with extracted values.
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=3000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            extracted_data = json.loads(json_match.group())
            
            # Ensure all sections are present in the dictionary
            result_dict = {}
            for section in lc_sections:
                result_dict[section] = extracted_data.get(section, "")
            
            return result_dict
        else:
            # Fallback: create empty dict for all sections
            return {section: "" for section in lc_sections}
            
    except Exception as e:
        print(f"Warning: Error in GPT-4o extraction: {e}")
        # Fallback: create empty dict for all sections
        return {section: "" for section in lc_sections}

def validate_compliance_with_gpt4o(element1: str, element2: str, element4: str, element6: str) -> Tuple[str, str]:
    """
    Use GPT-4o to validate compliance of extracted LC value (element2) 
    against both UCP600 Articles text (element4) and ISBP745 Paragraphs text (element6)
    
    Returns: (compliance_status, remarks)
    """
    system_prompt = """You are a senior trade finance compliance officer with deep expertise in UCP600 and ISBP745 regulations.

Your task is to evaluate whether an extracted value from a Letter of Credit complies with the specified UCP600 Articles and ISBP745 Paragraphs.

Evaluation Criteria:
1. Check if the extracted LC value meets the requirements specified in both reference standards
2. Consider completeness, format, content, and regulatory compliance
3. Be strict but fair in your assessment
4. If extracted value is empty/missing and it's required, mark as non-compliant
5. If reference standards are dummy/placeholder text, make reasonable professional judgment

You must provide:
- A clear compliance decision: "COMPLIANT" or "NON-COMPLIANT"
- Brief, actionable remarks explaining your decision (max 150 words)"""

    user_prompt = f"""
Please evaluate the following LC field for UCP600/ISBP745 compliance:

LC FIELD: {element1}
EXTRACTED VALUE FROM LC: {element2}

COMPLIANCE REFERENCES:
1. UCP600 Articles Text: {element4}
2. ISBP745 Paragraphs Text: {element6}

EVALUATION TASK:
Check if the "EXTRACTED VALUE FROM LC" (element2) complies with BOTH:
- UCP600 Articles Text (element4) 
- ISBP745 Paragraphs Text (element6)

Provide your response in this exact JSON format:
{{
    "compliance_status": "COMPLIANT" or "NON-COMPLIANT",
    "remarks": "Your detailed explanation and reasoning (max 150 words)"
}}

Focus on practical compliance assessment based on trade finance best practices."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=800
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            status = result.get("compliance_status", "NON-COMPLIANT")
            remarks = result.get("remarks", "Assessment failed - no remarks provided")
            
            # Normalize status
            if status.upper() == "COMPLIANT":
                return "COMPLIANT", remarks
            else:
                return "NON-COMPLIANT", remarks
        else:
            # Fallback parsing
            if "COMPLIANT" in content.upper() and "NON-COMPLIANT" not in content.upper():
                return "COMPLIANT", content[:200]
            else:
                return "NON-COMPLIANT", content[:200]
                
    except Exception as e:
        return "NON-COMPLIANT", f"Validation error occurred: {str(e)[:100]}"

# LangGraph Agent Nodes
def process_single_task_node(state: AgentState) -> AgentState:
    """
    LangGraph node to process one validation task at a time using GPT-4o
    Updates the results table after each task completion
    """
    current_index = state["current_index"]
    tasks = state["tasks"]
    results = state["results"]
    
    if current_index >= len(tasks):
        state["completed"] = True
        return state
    
    # Get current task
    task = tasks[current_index]
    
    print(f"🔄 Processing task {current_index + 1}/{len(tasks)}: {task.element1}")
    
    # Validate compliance using GPT-4o
    # Send elements 1, 2, 4, and 6 to GPT-4o as specified
    compliance_status, remarks = validate_compliance_with_gpt4o(
        element1=task.element1,  # LC Section key
        element2=task.element2,  # Extracted LC value  
        element4=task.element4,  # Articles text (dummy)
        element6=task.element6   # Paragraphs text (dummy)
    )
    
    # Update results table with 6 columns as specified:
    # column1: 1st element from task
    # column2: 2nd element from task  
    # column3: 3rd element from task
    # column4: 5th element from task
    # compliant status as 5th column
    # remarks as 6th column
    result_row = {
        "LC Section": task.element1,              # column1: 1st element
        "Extracted Value": task.element2,         # column2: 2nd element
        "UCP600 Articles": task.element3,         # column3: 3rd element  
        "ISBP745 Paragraphs": task.element5,      # column4: 5th element
        "Compliance Status": compliance_status,   # column5: compliant status
        "Remarks": remarks                       # column6: remarks
    }
    
    results.append(result_row)
    
    # Move to next task
    state["current_index"] = current_index + 1
    
    # Small delay to manage API rate limits
    time.sleep(0.8)
    
    return state

def should_continue_processing(state: AgentState) -> str:
    """
    LangGraph routing function to determine if agent should continue processing tasks
    """
    if state["completed"] or state["current_index"] >= len(state["tasks"]):
        return "end"
    else:
        return "continue"

def create_langgraph_agent() -> StateGraph:
    """
    Create LangGraph agent workflow for sequential task processing
    """
    workflow = StateGraph(AgentState)
    
    # Add the processing node
    workflow.add_node("process_task", process_single_task_node)
    
    # Set entry point
    workflow.set_entry_point("process_task")
    
    # Add conditional edges for looping
    workflow.add_conditional_edges(
        "process_task",
        should_continue_processing,
        {
            "continue": "process_task",  # Loop back to process next task
            "end": END                   # End when all tasks completed
        }
    )
    
    return workflow.compile()

def main():
    """
    Main execution function implementing the complete workflow:
    1. Load LC and mappings.csv
    2. Extract data from LC using GPT-4o to create dictionary 
    3. Create validation tasks with 6 elements each
    4. Run LangGraph agent to process tasks sequentially
    5. Output final results table
    """
    print("🚀 LC Compliance Checker - GPT-4o + LangGraph")
    print("=" * 60)
    
    # Step 1: Load files
    print("📁 Loading input files...")
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
    
    missing_cols = [col for col in required_columns if col not in mappings_df.columns]
    if missing_cols:
        print(f"❌ Missing required columns in mappings.csv: {missing_cols}")
        return
    
    # Step 2: Extract LC data using GPT-4o to create dictionary
    print("🤖 Extracting LC data using GPT-4o...")
    lc_sections = mappings_df["LC Section"].tolist()
    
    # Create dictionary with first column of mapping.csv as key and extracted value as value
    extracted_dict = extract_lc_data_with_gpt4o(lc_text, lc_sections)
    
    print(f"✅ Created dictionary with {len(extracted_dict)} LC sections")
    print("📋 Sample extractions:")
    for i, (key, value) in enumerate(list(extracted_dict.items())[:3]):
        preview = value[:80] + "..." if len(value) > 80 else value
        print(f"   {key}: {preview}")
    
    # Step 3: Create validation tasks (up to 30 as requested)
    print("📝 Creating validation tasks...")
    tasks = []
    
    # Use all available rows (29 in the CSV, so we'll get 29 tasks instead of 30)
    task_count = min(30, len(mappings_df))
    
    for idx, (_, row) in enumerate(mappings_df.head(task_count).iterrows()):
        lc_section = str(row["LC Section"])
        
        task = ValidationTask(
            element1=lc_section,                           # key from dictionary
            element2=extracted_dict.get(lc_section, ""),   # value from dictionary
            element3=str(row["UCP600 Article(s)"]),        # 2nd column of mapping.csv
            element4=str(row["Articles text"]),            # 3rd column of mapping.csv (dummy)
            element5=str(row["ISBP745 Paragraph(s)"]),     # 4th column of mapping.csv  
            element6=str(row["Paragraphs text"])           # 5th column of mapping.csv (dummy)
        )
        tasks.append(task)
    
    print(f"✅ Created {len(tasks)} validation tasks")
    
    # Step 4: Initialize LangGraph agent state
    initial_state: AgentState = {
        "tasks": tasks,
        "current_index": 0,
        "results": [],
        "completed": False
    }
    
    # Step 5: Run LangGraph agent for sequential task processing
    print("🤖 Starting LangGraph agent powered by GPT-4o...")
    agent = create_langgraph_agent()
    
    try:
        final_state = agent.invoke(initial_state)
        results = final_state["results"]
        
        # Step 6: Display and save results
        print("\n" + "=" * 100)
        print("📊 FINAL VALIDATION RESULTS")
        print("=" * 100)
        
        # Create results DataFrame with the 6 specified columns
        results_df = pd.DataFrame(results, columns=[
            "LC Section",           # column1: 1st element from task
            "Extracted Value",      # column2: 2nd element from task
            "UCP600 Articles",      # column3: 3rd element from task
            "ISBP745 Paragraphs",   # column4: 5th element from task
            "Compliance Status",    # column5: compliant status
            "Remarks"              # column6: remarks
        ])
        
        # Display results
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 60)
        
        print(results_df.to_string(index=False))
        
        # Save results to CSV
        output_file = "lc_validation_results.csv"
        results_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n💾 Results saved to: {output_file}")
        
        # Summary statistics
        total_tasks = len(results)
        compliant_count = sum(1 for r in results if r["Compliance Status"] == "COMPLIANT")
        compliance_rate = (compliant_count / total_tasks) * 100 if total_tasks > 0 else 0
        
        print(f"\n📈 SUMMARY STATISTICS:")
        print(f"   Total tasks processed: {total_tasks}")
        print(f"   Compliant tasks: {compliant_count}")
        print(f"   Non-compliant tasks: {total_tasks - compliant_count}")
        print(f"   Overall compliance rate: {compliance_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ LC Compliance Check completed successfully!")
    print("🎯 Process Summary:")
    print("   1. ✅ Extracted LC data using GPT-4o → Created dictionary")
    print("   2. ✅ Created validation tasks with 6 elements each")  
    print("   3. ✅ LangGraph agent processed tasks sequentially")
    print("   4. ✅ GPT-4o validated compliance against Articles & Paragraphs")
    print("   5. ✅ Generated final results table with 6 columns")

if __name__ == "__main__":
    main()
