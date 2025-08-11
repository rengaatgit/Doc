
from langgraph.graph import StateGraph, END, State
from dataclasses import dataclass
from typing import List, Dict, Tuple
import pandas as pd
import time
import json
import re
from openai import OpenAI
import os

@dataclass
class ValidationTask:
    element1: str   # LC Section (key)
    element2: str   # Extracted value
    element3: str   # UCP Article(s)
    element4: str   # Articles text
    element5: str   # ISBP Paragraph(s)
    element6: str   # Paragraphs text

class AgentState(State):
    tasks: List[ValidationTask]
    idx: int = 0
    results: List[Dict] = []
    finished: bool = False

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY environment variable.")
client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "gpt-4o"

def load_text_file(path:str) -> str:
    for enc in ("utf-8","latin1","cp1252"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except:
            continue
    raise ValueError(f"Cannot decode file: {path}")

def extract_lc_fields(lc_text: str, keys: List[str]) -> Dict[str,str]:
    prompt = f"""
    You are a trade finance LC document expert. Extract the following fields, each exactly as listed:
    {keys}
    
    LC Document:
    {lc_text}
    
    Return ONLY a JSON object with these keys and extracted values.
    If a field is not present, use empty string.
    """
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Expert LC field extractor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=2048
    )
    content = resp.choices[0].message.content
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        data = json.loads(match.group())
        # Ensure all keys present
        return {k: data.get(k, "") for k in keys}
    else:
        return {k: "" for k in keys}

def gpt_validate_compliance(element1: str, element2: str, element4: str, element6: str) -> Tuple[str, str]:
    prompt = f"""
    You are a trade finance compliance expert. Assess if this LC value is compliant with both UCP Articles and ISBP Paragraphs.

    Field: {element1}
    Value: {element2}
    Articles: {element4}
    Paragraphs: {element6}

    Reply in JSON exactly: {{"compliance": "COMPLIANT" or "NON-COMPLIANT", "remarks": "max 150 chars"}}
    """
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Compliance adjudicator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=300
    )
    content = resp.choices.message.content
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            compliance = data.get("compliance", "NON-COMPLIANT")
            remarks = data.get("remarks", "No remarks")
            return compliance, remarks
        except:
            pass
    return "NON-COMPLIANT", "Failed to parse compliance response"

def process_task(state: AgentState) -> AgentState:
    if state.finished or state.idx >= len(state.tasks):
        state.finished = True
        return state
    task = state.tasks[state.idx]
    print(f"Validating {state.idx+1}/{len(state.tasks)}: {task.element1}")
    compliance, remarks = gpt_validate_compliance(
        element1=task.element1,
        element2=task.element2,
        element4=task.element4,
        element6=task.element6
    )
    state.results.append({
        "LC Section": task.element1,
        "Extracted Value": task.element2,
        "UCP Articles": task.element3,
        "ISBP Paragraphs": task.element5,
        "Compliance": compliance,
        "Remarks": remarks
    })
    state.idx += 1
    time.sleep(0.8)  # rate limit
    return state

def router(state: AgentState) -> str:
    return "process" if not state.finished else END

def main():
    # Load inputs
    lc_text = load_text_file("sampleLC.txt")
    mapping_df = pd.read_csv("mappings.csv")

    # Extract all LC fields as per mapping
    keys = mapping_df["LC Section"].tolist()
    extracted = extract_lc_fields(lc_text, keys)

    # Prepare tasks (up to 30)
    tasks = []
    for idx, row in mapping_df.head(30).iterrows():
        tasks.append(ValidationTask(
            element1=row["LC Section"],
            element2=extracted.get(row["LC Section"], ""),
            element3=row["UCP600 Article(s)"],
            element4=row["Articles text"],
            element5=row["ISBP745 Paragraph(s)"],
            element6=row["Paragraphs text"]
        ))

    # Set up LangGraph agent
    workflow = StateGraph(AgentState)
    workflow.add_node("process", process_task)
    workflow.set_entry_point("process")
    workflow.add_conditional_edges("process", router, {"process": "process", END: END})
    app = workflow.compile()

    # Execute!
    state = app.invoke(AgentState(tasks=tasks))

    # Output results
    df = pd.DataFrame(state.results)
    print(df)
    df.to_csv("lc_validation_results.csv", index=False)
    print("Results saved to lc_validation_results.csv")

if __name__ == "__main__":
    main()

pip install langgraph langchain-openai pandas openai
