# main.py
# Main script to run the LC Validation Agentic System

import os
import re
import csv
import json
from typing import List, Dict, TypedDict, Annotated
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, END

# --- Configuration ---
# It's recommended to set your OpenAI API key in your environment variables
# For example: export OPENAI_API_KEY='your_key_here'
# If not set, you might need to pass it directly to the models.
# Make sure you have placeholder files: sampleLC.txt, UCP600.txt, ISBP745.txt, and mappings.csv

CHROMA_PATH = "lc_chroma_db"
UCP_SOURCE = "UCP600.txt"
ISBP_SOURCE = "ISBP745.txt"
LC_SOURCE = "sampleLC.txt"
MAPPINGS_SOURCE = "mappings.csv"

# --- 1. Data Loading and Preparation ---

def create_placeholder_files():
    """Creates placeholder files if they don't exist to make the script runnable."""
    if not os.path.exists(UCP_SOURCE):
        with open(UCP_SOURCE, "w") as f:
            f.write("Article 1: UCP 600 applies to any documentary credit.\n")
            f.write("Article 18: A commercial invoice must correspond to the credit.\n")
            f.write("Article 20: A bill of lading must indicate the name of the carrier.\n")
            f.write("Article 28: An insurance document must be as stipulated in the credit.\n")

    if not os.path.exists(ISBP_SOURCE):
        with open(ISBP_SOURCE, "w") as f:
            f.write("Paragraph C1: The description of the goods in the commercial invoice must correspond with the description in the credit.\n")
            f.write("Paragraph E1: A bill of lading may be issued by any entity other than a carrier or master.\n")
            f.write("Paragraph K2: The currency in the insurance document must be the same as the currency of the credit.\n")

    if not os.path.exists(LC_SOURCE):
        with open(LC_SOURCE, "w") as f:
            f.write(
"""IRREVOCABLE DOCUMENTARY LETTER OF CREDIT
LC Number: LC2025-0001
Amount: USD 110,000
Goods: Industrial Widget Components
Incoterm: CIF Port Klang
Insurance Requirements: Insurance policy/certificate covering at least 110% of invoice value.
Bill of Lading Requirements: Full set of clean on board marine bills of lading.
"""
            )
    
    if not os.path.exists(MAPPINGS_SOURCE):
        with open(MAPPINGS_SOURCE, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["LC Section", "UCP600 Article", "ISBP745 Section", "Remarks"])
            writer.writerow(["Goods Description", "Article 18c", "C3-C5", "Must correspond between credit and invoice"])
            writer.writerow(["Bill of Lading Requirements", "Article 20", "E1-E28", "Detailed B/L examination requirements"])
            writer.writerow(["Insurance Requirements", "Article 28", "K1-K23", "All risks coverage, 110% minimum"])


def load_and_prepare_knowledge_base():
    """Loads UCP600 and ISBP745, splits them, and stores them in ChromaDB."""
    print("Loading knowledge base...")
    documents = TextLoader(UCP_SOURCE).load() + TextLoader(ISBP_SOURCE).load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    
    print(f"Creating vector store with {len(chunks)} chunks...")
    embedding_function = OpenAIEmbeddings()
    vector_store = Chroma.from_documents(chunks, embedding_function, persist_directory=CHROMA_PATH)
    vector_store.persist()
    print("Knowledge base created and persisted in ChromaDB.")
    return vector_store

def parse_lc(file_path: str) -> Dict[str, str]:
    """Parses the LC text file into a structured dictionary."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    lc_data = {}
    # A more robust regex might be needed for complex LCs
    # This simplified parser works for the sample format
    lines = content.split('\n')
    current_key = ""
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            lc_data[current_key] = value.strip()
        elif current_key and line.strip(): # handle multi-line values
            lc_data[current_key] += " " + line.strip()
            
    # Normalize keys for easier mapping
    lc_data_normalized = {k.replace(" ", "_").replace("/", "_").lower(): v for k, v in lc_data.items()}
    # Manual mapping for sample LC
    lc_data_normalized['goods_description'] = lc_data.get('Goods', 'Not Found')
    return lc_data_normalized

def load_mappings(file_path: str) -> List[Dict[str, str]]:
    """Loads the validation mappings from a CSV file."""
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

# --- 2. Agent and Graph Definition (LangGraph) ---

class ValidationResult(BaseModel):
    """Data model for the output of a single validation check."""
    lc_clause: str = Field(description="The specific LC clause being validated.")
    rules_checked: str = Field(description="The UCP 600 / ISBP 745 rules checked against.")
    is_compliant: bool = Field(description="True if compliant, False otherwise.")
    reasoning: str = Field(description="Detailed explanation for the compliance decision.")
    recommendation: str = Field(description="Suggested action if non-compliant.")

class AgentState(TypedDict):
    """Defines the state of our graph."""
    lc_data: Dict[str, str]
    mappings: List[Dict[str, str]]
    validation_tasks: List[Dict]
    results: list

# Initialize the LLM and Retriever
llm = ChatOpenAI(model="gpt-4o", temperature=0)
structured_llm = llm.with_structured_output(ValidationResult)
embedding_function = OpenAIEmbeddings()
vector_store = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
retriever = vector_store.as_retriever()

def validation_agent(task: Dict):
    """The core logic for a single validation agent."""
    lc_section_name = task["LC Section"]
    ucp_rules = task["UCP600 Article"]
    isbp_rules = task["ISBP745 Section"]
    
    # Find the relevant data in the parsed LC
    lc_clause_key = lc_section_name.replace(" ", "_").replace("/", "_").lower()
    lc_clause_text = task.get('lc_data', {}).get(lc_clause_key, f"Clause '{lc_section_name}' not found in LC.")
    
    print(f"\n🕵️  Agent starting validation for: '{lc_section_name}'...")
    print(f"   - Checking against: UCP {ucp_rules}, ISBP {isbp_rules}")

    # RAG: Retrieve relevant rules from the knowledge base
    query = f"What are the rules for '{lc_section_name}' according to UCP 600 {ucp_rules} and ISBP 745 {isbp_rules}?"
    retrieved_docs = retriever.invoke(query)
    context = "\n---\n".join([doc.page_content for doc in retrieved_docs])
    
    print(f"   - Retrieved {len(retrieved_docs)} relevant rule snippets.")

    # Generate: Use LLM to perform the validation
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an expert in Documentary Trade Finance, specializing in UCP 600 and ISBP 745. "
         "Your task is to validate a specific clause from a Letter of Credit (LC) against the provided rules. "
         "Analyze the LC clause and determine if it complies with the rules from the knowledge base. "
         "Provide a clear 'Pass' or 'Fail' (is_compliant) decision with detailed reasoning."),
        ("human", 
         "Please validate the following LC clause:\n\n"
         "**LC Clause to Validate:**\n'{lc_clause_text}'\n\n"
         "**Knowledge Base Rules:**\n'{context}'\n\n"
         "**Validation Task:**\nCheck compliance for '{lc_section_name}' based on UCP 600 rules '{ucp_rules}' and ISBP 745 rules '{isbp_rules}'.")
    ])
    
    chain = prompt | structured_llm
    
    result = chain.invoke({
        "lc_clause_text": lc_clause_text,
        "context": context,
        "lc_section_name": lc_section_name,
        "ucp_rules": ucp_rules,
        "isbp_rules": isbp_rules
    })
    
    result.lc_clause = lc_clause_text # Add the clause text to the final result
    print(f"   - Agent finished. Compliance: {'✅ Pass' if result.is_compliant else '❌ Fail'}")
    return result.dict()


# Define the nodes for the graph
def prepare_tasks(state: AgentState) -> AgentState:
    """Node to prepare all validation tasks for parallel execution."""
    print("--- Preparing Validation Tasks ---")
    lc_data = state['lc_data']
    mappings = state['mappings']
    tasks = []
    for mapping in mappings:
        task_with_data = mapping.copy()
        task_with_data['lc_data'] = lc_data
        tasks.append(task_with_data)
    
    state['validation_tasks'] = tasks
    return state

def run_all_validations(state: AgentState) -> AgentState:
    """Node that runs the validation agents in parallel."""
    print("\n--- Starting Parallel Validation ---")
    tasks = state['validation_tasks']
    # In a real-world scenario, you'd use a thread/process pool for true parallelism
    # For simplicity here, we map sequentially, but the logic is designed for parallel execution.
    results = [validation_agent(task) for task in tasks]
    state['results'] = results
    return state

def aggregate_results(state: AgentState) -> AgentState:
    """Node to print the final aggregated report."""
    print("\n\n--- 📋 Final Validation Report ---")
    results = state['results']
    overall_compliant = all(r['is_compliant'] for r in results)
    
    print(f"\nOverall LC Compliance Status: {'✅ COMPLIANT' if overall_compliant else '❌ NON-COMPLIANT'}\n")
    print("-" * 50)
    
    for res in results:
        status = "✅ PASS" if res['is_compliant'] else "❌ FAIL"
        print(f"\nClause: {res['lc_clause']}")
        print(f"Rules: {res['rules_checked']}")
        print(f"Status: {status}")
        print(f"Reasoning: {res['reasoning']}")
        if not res['is_compliant']:
            print(f"Recommendation: {res['recommendation']}")
        print("-" * 30)
        
    return state

# --- 3. Build and Run the Graph ---

def build_graph():
    """Builds the LangGraph workflow."""
    workflow = StateGraph(AgentState)
    workflow.add_node("prepare_tasks", prepare_tasks)
    workflow.add_node("run_validations", run_all_validations)
    workflow.add_node("aggregate_results", aggregate_results)
    
    workflow.set_entry_point("prepare_tasks")
    workflow.add_edge("prepare_tasks", "run_validations")
    workflow.add_edge("run_validations", "aggregate_results")
    workflow.add_edge("aggregate_results", END)
    
    return workflow.compile()

def main():
    """Main function to execute the entire process."""
    print("--- Initializing LC Validation System ---")
    
    # 1. Create placeholder files if they don't exist
    create_placeholder_files()
    
    # 2. Setup Knowledge Base (only if it doesn't exist)
    if not os.path.exists(CHROMA_PATH):
        load_and_prepare_knowledge_base()
    else:
        print("Existing ChromaDB found. Skipping knowledge base creation.")
        
    # 3. Load inputs
    lc_data = parse_lc(LC_SOURCE)
    mappings = load_mappings(MAPPINGS_SOURCE)
    
    # 4. Build and run the graph
    app = build_graph()
    initial_state = {"lc_data": lc_data, "mappings": mappings, "results": []}
    
    # Run the graph
    app.invoke(initial_state)

if __name__ == "__main__":
    main()

