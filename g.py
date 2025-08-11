import pandas as pd
import io
import re
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

# --- 1. Embedded Data ---
# This section contains the data from the uploaded files.
def get_mappings_csv() -> str:
    """Provides the content of mappings.csv."""
    return """LC Section,UCP600 Article(s),Articles text,ISBP745 Paragraph(s),Paragraphs text
Credit Type,"Art. 1, 2, 3",dummy1,"Preliminary i-ii",para-dummy1
UCP Reference Statement,Art. 1,dummy2,"Preliminary i-ii",para-dummy2
LC Number,Art. 14(i),dummy3,A19,para-dummy3
Date of Issue,"Art. 7(b), 14(i)",dummy4,A11-A16,para-dummy4
Issuing Bank Details,"Art. 2, 7",dummy5,A20,para-dummy5
Applicant Details,"Art. 2, 14(j)",dummy6,"A20, A21",para-dummy6
Beneficiary Details,"Art. 2, 18(a)(i), 14(j)",dummy7,"C2(a), A20, A21",para-dummy7
Amount,"Art. 18(a)(iii), 30",dummy8,"C6, C13-C14",para-dummy8
Expiry Date,"Art. 6(d)(i), 29",dummy9,"A14, A15",para-dummy9
Expiry Place,Art. 6(d)(ii),dummy10,A14(b)(ii),para-dummy10
Availability (Sight Draft),"Art. 6(b), 7(a)",dummy11,B1-B18,para-dummy11
Incoterm (CIF),"Art. 18, 28(f)(ii)",dummy12,"C8-C9, K12, K18",para-dummy12
Latest Shipment Date,"Art. 6, 29(c)",dummy13,A14,para-dummy13
Port of Loading,Art. 20(a)(iii),dummy14,E6(f-g),para-dummy14
Port of Discharge,Art. 20(a)(iii),dummy15,E8-E10,para-dummy15
Goods Description,"Art. 18(c), 14(e)",dummy16,"C3-C5, E22",para-dummy16
Commercial Invoice,"Art. 17, 18",dummy17,C1-C15,para-dummy17
Bill of Lading,"Art. 20, 27, 26(c)",dummy18,E1-E28,para-dummy18
Insurance Document,Art. 28,dummy19,K1-K23,para-dummy19
Certificate of Origin,Art. 14(f),dummy20,L1-L8,para-dummy20
Packing List,"Art. 14(f), 17",dummy21,M1-M6,para-dummy21
Presentation Period (21 days),Art. 14(c),dummy22,A18(b)(ii),para-dummy22
Partial Shipments,Art. 31,dummy23,E19(c),para-dummy23
Transshipment,Art. 20(c),dummy24,E17,para-dummy24
Banking Charges,Art. 37(c),dummy25,–,para-dummy25
Invoice LC Number Requirement,Art. 14(d),dummy26,"C3, A22",para-dummy26
Document Language (English),Art. 14(d),dummy27,A21(a-e),para-dummy27
Confirmation,Art. 8,dummy28,–,para-dummy28
Authorized Signature,"Art. 3, 7(b)",dummy29,A35-A38,para-dummy29
"""

def get_sample_lc_txt() -> str:
    """Provides the content of sampleLC.txt."""
    return """IRREVOCABLE DOCUMENTARY LETTER OF CREDIT
Subject to Uniform Customs & Practice for Documentary Credits, ICC Publication No. 600 (UCP 600)

LC Number: LC2025-0001
Date of Issue: August 09, 2025
Issuing Bank:
Global Trust Bank
123 Finance Avenue
Singapore 018956

Applicant:
NeoTech Imports Ltd.
456 Commerce Road
Kuala Lumpur 50450
Malaysia

Beneficiary:
Atlas Widgets S.A.
12 Rue des Marchés
Paris 75002
France

Amount: USD 110,000 (One Hundred Ten Thousand U.S. Dollars)
Expiry Date: November 15, 2025
Expiry Place: At the counters of Global Trust Bank, Singapore

Available by sight draft drawn on Global Trust Bank, Singapore, accompanied by the documents listed below.
Incoterm: CIF Port Klang
Latest Shipment Date: October 31, 2025
Port of Loading: Le Havre, France
Port of Discharge: Port Klang, Malaysia
Goods: Industrial Widget Components, Model IW2025, 10,000 units, unit price USD 11

Documents Required:

Signed commercial invoice in 1 original and 2 copies

Full set of clean on board marine bills of lading, consigned to order of issuing bank, marked ‘Freight Prepaid’

Insurance policy/certificate in negotiable form, covering at least 110% of invoice value, indicating “All Risks”

Certificate of origin issued by Paris Chamber of Commerce

Packing list in 1 original and 2 copies

Documents must be presented within 21 days after shipment date but not later than expiry date.

Partial Shipments: Allowed
Transshipment: Not Allowed

This credit is subject to Uniform Customs and Practice for Documentary Credits (UCP 600), ICC Publication No. 600.

All banking charges outside Singapore are for beneficiary’s account; Singapore charges for applicant’s account.

Commercial invoice must indicate LC number.
All documents must be in English.
Confirmation: Not Requested

Authorized Signature:
[Signature]
Global Trust Bank
Singapore
"""


# --- 2. AI Simulation and Helper Functions ---
def extract_lc_data(lc_content: str, mapping_df: pd.DataFrame) -> Dict[str, str]:
    """
    Simulates an LLM extracting data from the LC text.
    In a real scenario, this would involve a call to a model like GPT-4o.
    For this example, we use regular expressions for reliable extraction.
    """
    print("Step 1: Extracting data from Letter of Credit...")
    
    # Helper to find a value by its key pattern
    def find_value(pattern, content, multiline=False):
        match = re.search(pattern, content, re.DOTALL if multiline else 0)
        if not match:
            return "Not Found"
        if multiline:
            return match.group(1).strip()
        return match.group(1).strip()

    # Define extraction patterns for each key
    patterns = {
        "Credit Type": r"^(IRREVOCABLE DOCUMENTARY LETTER OF CREDIT)",
        "UCP Reference Statement": r"^(This credit is subject to Uniform Customs and Practice.*600)\.",
        "LC Number": r"LC Number: (LC\d{4}-\d{4})",
        "Date of Issue": r"Date of Issue: (.*)",
        "Issuing Bank Details": r"Issuing Bank:\n(.*?)\n\nApplicant:",
        "Applicant Details": r"Applicant:\n(.*?)\n\nBeneficiary:",
        "Beneficiary Details": r"Beneficiary:\n(.*?)\n\nAmount:",
        "Amount": r"Amount: (.*)",
        "Expiry Date": r"Expiry Date: (.*)",
        "Expiry Place": r"Expiry Place: (.*)",
        "Availability (Sight Draft)": r"^(Available by sight draft.*)\.",
        "Incoterm (CIF)": r"Incoterm: (.*)",
        "Latest Shipment Date": r"Latest Shipment Date: (.*)",
        "Port of Loading": r"Port of Loading: (.*)",
        "Port of Discharge": r"Port of Discharge: (.*)",
        "Goods Description": r"Goods: (.*)",
        "Commercial Invoice": r"^(Signed commercial invoice.*)",
        "Bill of Lading": r"^(Full set of clean on board.*)",
        "Insurance Document": r"^(Insurance policy/certificate.*)",
        "Certificate of Origin": r"^(Certificate of origin.*)",
        "Packing List": r"^(Packing list.*)",
        "Presentation Period (21 days)": r"^(Documents must be presented within 21 days.*)\.",
        "Partial Shipments": r"Partial Shipments: (.*)",
        "Transshipment": r"Transshipment: (.*)",
        "Banking Charges": r"^(All banking charges.*)\.",
        "Invoice LC Number Requirement": r"^(Commercial invoice must indicate LC number)\.",
        "Document Language (English)": r"^(All documents must be in English)\.",
        "Confirmation": r"Confirmation: (.*)",
        "Authorized Signature": r"Authorized Signature:\n(.*?)$"
    }

    extracted_data = {}
    lc_lines = lc_content.splitlines()
    
    for key in mapping_df['LC Section']:
        # Use regex patterns for most fields
        if key in patterns:
            # For multiline fields, search the whole content
            if key in ["Issuing Bank Details", "Applicant Details", "Beneficiary Details", "Authorized Signature"]:
                 extracted_data[key] = find_value(patterns[key], lc_content, multiline=True)
            # For single-line fields, search line by line for a match
            else:
                 for line in lc_lines:
                     match = re.search(patterns[key], line)
                     if match:
                         extracted_data[key] = match.group(1).strip()
                         break
                 if key not in extracted_data:
                     extracted_data[key] = "Not Found"
        else:
            extracted_data[key] = "Not Found"
            
    print("   ...Extraction complete.\n")
    return extracted_data


def create_validation_tasks(lc_data: Dict, mappings_df: pd.DataFrame) -> List[Dict]:
    """Creates a list of validation tasks based on mappings and extracted data."""
    print("Step 2: Creating validation task queue...")
    tasks = []
    for _, row in mappings_df.iterrows():
        key = row['LC Section']
        task = {
            "element1": key,
            "element2": lc_data.get(key, "Data not extracted"),
            "element3": row["UCP600 Article(s)"],
            "element4": row["Articles text"],
            "element5": row["ISBP745 Paragraph(s)"],
            "element6": row["Paragraphs text"],
        }
        tasks.append(task)
    print(f"   ...{len(tasks)} tasks created.\n")
    return tasks


def mock_llm_compliance_check(task: Dict) -> Dict[str, str]:
    """
    Simulates a call to gpt-4o for compliance checking.
    
    In a real application, this function would be replaced with an actual API call
    to a service like OpenAI or Google AI, sending a detailed prompt.
    
    Example Prompt for the real LLM:
    ---
    You are an expert in Documentary Trade Finance, specializing in UCP 600 and ISBP 745.
    Analyze the following clause from a Letter of Credit and determine if it is compliant
    with the provided articles and paragraphs.

    **LC Clause:** "{task['element1']}"
    **Extracted Value:** "{task['element2']}"

    **UCP 600 Rules to check against (Text):** "{task['element4']}"

    **ISBP 745 Rules to check against (Text):** "{task['element6']}"

    Provide your response as a dictionary with two keys:
    1. "status": Must be one of ["Compliant", "Non-Compliant", "Not Applicable"].
    2. "remarks": A brief, one-sentence explanation for your decision.
    ---
    """
    # For this script, we'll return a plausible, hardcoded result.
    # This allows the LangGraph agent to function without a live API key.
    
    # A little logic to make the simulation more realistic
    if "Not Found" in task['element2'] or not task['element2']:
        return {
            "status": "Non-Compliant",
            "remarks": f"The required clause '{task['element1']}' was not found in the LC document."
        }

    return {
        "status": "Compliant",
        "remarks": "The clause adheres to the standard requirements of UCP 600 and ISBP 745."
    }


# --- 3. LangGraph Agent Setup ---

class AgentState(TypedDict):
    """Defines the state for our LangGraph agent."""
    tasks: List[Dict]
    results: List[Dict]
    
def run_validation_task(state: AgentState) -> AgentState:
    """
    The primary node of the graph. It processes one task from the queue.
    """
    # Get the current tasks list
    tasks = state['tasks']
    if not tasks:
        return state # Should be routed to END, but as a safeguard.
        
    # Pop the next task from the front of the list
    current_task = tasks.pop(0)
    
    key = current_task['element1']
    print(f"   - Agent picking up task: '{key}'")

    # Call the (mock) LLM to perform the compliance check
    llm_response = mock_llm_compliance_check(current_task)
    
    # Format the result for the final table
    result_entry = {
        "LC Section": key,
        "Extracted Value": current_task['element2'],
        "UCP600 Article(s)": current_task['element3'],
        "ISBP745 Paragraph(s)": current_task['element5'],
        "Compliant Status": llm_response['status'],
        "Remarks": llm_response['remarks']
    }
    
    # Add the result to the state
    state['results'].append(result_entry)
    print(f"   - Task '{key}' complete. Status: {llm_response['status']}")
    
    return state
    
def should_continue(state: AgentState) -> str:
    """
    Conditional edge. Determines if there are more tasks to process.
    """
    if not state['tasks']:
        print("\nAll tasks completed. Ending workflow.")
        return "end"
    else:
        print(f"   ...{len(state['tasks'])} tasks remaining.")
        return "continue"

# --- 4. Main Execution ---

if __name__ == "__main__":
    # Load data from embedded strings
    mappings_file = io.StringIO(get_mappings_csv())
    mappings_df = pd.read_csv(mappings_file)
    lc_content = get_sample_lc_txt()

    # Step 1: Extract data from LC
    extracted_lc_data = extract_lc_data(lc_content, mappings_df)

    # Step 2: Create a list of tasks for the agent
    validation_tasks = create_validation_tasks(extracted_lc_data, mappings_df)
    
    # Step 3: Set up and run the LangGraph agent
    print("Step 3: Initializing LangGraph agent...")
    
    # Define the workflow graph
    workflow = StateGraph(AgentState)
    workflow.add_node("validator", run_validation_task)
    workflow.add_conditional_edges(
        "validator",
        should_continue,
        {
            "continue": "validator",
            "end": END
        }
    )
    workflow.set_entry_point("validator")
    
    # Compile the graph into a runnable app
    app = workflow.compile()

    # Define the initial state for the agent
    initial_state = {
        "tasks": validation_tasks,
        "results": []
    }
    
    print("   ...Agent initialized. Starting compliance check process.\n")
    
    # Run the agent with the initial state
    final_state = app.invoke(initial_state)

    # Step 4: Display the final results in a table
    print("\n--- Final Compliance Report ---")
    results_df = pd.DataFrame(final_state['results'])
    
    # Configure pandas for better display
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_colwidth', 60)
    pd.set_option('display.width', 120)

    print(results_df)