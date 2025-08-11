"""
lc_compliance_checker.py
-------------------------------------------
End-to-end pipeline:
1. Read sampleLC.txt and mappings.csv.
2. Ask GPT-4o to extract every “LC Section” value → dict.
3. Build 30 validation-task objects (6 elements each).
4. LangGraph agent picks one task at a time, sends
   elements 1 2 4 6 to GPT-4o to judge compliance vs. UCP/ISBP text.
5. Agent appends the outcome (6-column row) to an in-memory list.
6. Loop until all tasks complete → save validation_results.csv
-------------------------------------------
Requires:
pip install openai langgraph pandas python-dotenv
-------------------------------------------
"""

import os, re, json, time
from dataclasses import dataclass
from typing import List, Dict, Tuple, TypedDict
import pandas as pd
from openai import OpenAI
from langgraph.graph import StateGraph, END

# ---------- configuration ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Set OPENAI_API_KEY in your shell before running.")
MODEL = "gpt-4o"
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- data structures ----------
@dataclass
class ValidationTask:
    element1: str  # LC Section (key)
    element2: str  # extracted value
    element3: str  # UCP article(s)
    element4: str  # UCP article text
    element5: str  # ISBP paragraph(s)
    element6: str  # ISBP paragraph text

class AgentState(TypedDict):
    tasks: List[ValidationTask]
    idx: int
    results: List[Dict[str, str]]

# ---------- helpers ----------
def read_text(path: str) -> str:
    for enc in ("utf-8", "latin1", "cp1252"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot decode {path}")

def extract_fields(lc_text: str, keys: List[str]) -> Dict[str, str]:
    prompt = (
        "You are a trade-finance specialist. "
        "Extract the following fields from the LC. "
        f"Return ONLY valid JSON with exactly these keys:\n{keys}\n\nLC:\n{lc_text}"
    )
    msg = [
        {"role": "system", "content": "Expert LC parser."},
        {"role": "user", "content": prompt},
    ]
    resp = client.chat.completions.create(
        model=MODEL, messages=msg, temperature=0, max_tokens=2048
    )
    # pull first {...} block
    m = re.search(r"\{.*\}", resp.choices[0].message.content, re.S)
    data = json.loads(m.group() if m else "{}")
    return {k: data.get(k, "") for k in keys}

def check_compliance(e1: str, e2: str, art_txt: str, para_txt: str) -> Tuple[str, str]:
    prompt = (
        "Act as a UCP-600 & ISBP-745 compliance examiner.\n"
        f"Field: {e1}\nValue: {e2}\n--- UCP Text ---\n{art_txt}\n"
        f"--- ISBP Text ---\n{para_txt}\n"
        "Reply ONLY with JSON like "
        '{"compliance":"Yes/No","remarks":"≤150 chars reason"}'
    )
    msg = [
        {"role": "system", "content": "Compliance adjudicator."},
        {"role": "user", "content": prompt},
    ]
    resp = client.chat.completions.create(
        model=MODEL, messages=msg, temperature=0, max_tokens=256
    )
    m = re.search(r"\{.*\}", resp.choices[0].message.content, re.S)
    try:
        data = json.loads(m.group())
        ok = "Yes" if str(data.get("compliance", "")).lower().startswith("y") else "No"
        return ok, data.get("remarks", "").strip()[:150]
    except Exception:
        return "No", "ParseError"

# ---------- LangGraph nodes ----------
def process_task(state: AgentState) -> AgentState:
    i = state["idx"]
    if i >= len(state["tasks"]):
        return state  # finished
    t = state["tasks"][i]
    comp, note = check_compliance(t.element1, t.element2, t.element4, t.element6)
    state["results"].append(
        {
            "LC Section": t.element1,
            "Extracted Value": t.element2,
            "UCP Article(s)": t.element3,
            "ISBP Paragraph(s)": t.element5,
            "Compliance": comp,
            "Remarks": note,
        }
    )
    state["idx"] = i + 1
    time.sleep(0.4)  # gentle rate-limit
    return state

def router(state: AgentState) -> str:
    return "next" if state["idx"] < len(state["tasks"]) else END

# ---------- main ----------
def main():
    print("▶ Reading files …")
    lc_text = read_text("sampleLC.txt")
    df = pd.read_csv("mappings.csv")
    keys = df["LC Section"].tolist()

    print("▶ GPT-4o extracting LC fields …")
    extracted = extract_fields(lc_text, keys)

    # build first 30 tasks (mapping.csv has 30 rows)
    tasks = []
    for _, row in df.iloc[:30].iterrows():
        tasks.append(
            ValidationTask(
                element1=row["LC Section"],
                element2=extracted.get(row["LC Section"], ""),
                element3=row["UCP600 Article(s)"],
                element4=row["Articles text"],
                element5=row["ISBP745 Paragraph(s)"],
                element6=row["Paragraphs text"],
            )
        )

    # init agent state
    state: AgentState = {"tasks": tasks, "idx": 0, "results": []}

    print("▶ Running LangGraph agent …")
    g = StateGraph(AgentState)
    g.add_node("do", process_task)
    g.set_entry_point("do")
    g.add_conditional_edges("do", router, {"next": "do", END: END})
    final_state = g.invoke(state)

    print("▶ Saving validation_results.csv")
    pd.DataFrame(final_state["results"]).to_csv("validation_results.csv", index=False)
    print("✅ Done – see validation_results.csv")

if __name__ == "__main__":
    main()
