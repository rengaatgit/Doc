import os
import base64
import zipfile
from io import BytesIO

# Create in-memory zip file
zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Create directory structure
    dirs = [
        'lc_validation/agents/',
        'lc_validation/data/',
        'lc_validation/services/',
    ]
    for d in dirs:
        zipf.writestr(d, b'')
    
    # 1. requirements.txt
    zipf.writestr('lc_validation/requirements.txt', """langchain==0.2.0
langgraph==0.0.52
chromadb==0.5.0
openai==1.30.1
pypdf2==3.0.1
python-dotenv==1.0.1
pandas==2.2.2
""")

    # 2. data/mappings.csv
    zipf.writestr('lc_validation/data/mappings.csv', """LC Section,UCP600 Article,ISBP745 Section,Remarks
Credit Type,Article 1,N/A,UCP600 Art. 3 states credit is irrevocable
UCP Reference Statement,Article 1,Preliminary Considerations,Essential for determining applicable rules
LC Number,Not specifically covered,A13,Good practice for identification
Date of Issue,Not specifically covered,A11;A13,Important for determining validity periods
Issuing Bank Details,Article 2,N/A,Defines the bank's role and obligations
Applicant Details,Article 2,A20,Party requesting credit issuance
Beneficiary Details,Article 2,C2,Party in whose favor credit is issued
Credit Amount,Article 30,C6,Must match invoice currency
Expiry Date,Article 6;Article 66,A14;A15,Critical for presentation timing
Expiry Place,Article 66,N/A,Determines where documents must be presented
Availability,Article 6,B1-B18,Defines payment mechanism
Incoterm,Not specifically covered,C8,Must appear on invoice with same source
Latest Shipment Date,Article 29c,A14;A15,Cannot be extended due to banking holidays
Port of Loading,Article 20,E64-g,Must match transport document
Port of Discharge,Article 20,E8-E10,Must match transport document
Goods Description,Article 18c,C3-C5,Must correspond between credit and invoice
Commercial Invoice Requirements,Article 18,C1-C15,Comprehensive invoice examination rules
Bill of Lading Requirements,Article 20;Article 27,E1-E28,Detailed BL examination requirements
Insurance Requirements,Article 28,K1-K23,All risks coverage, 110% minimum
Certificate of Origin Requirements,Article 14f,L1-L8,Chamber of Commerce issuance
Packing List Requirements,Article 14f,M1-M6,Document function and content rules
""")

    # 3. services/parser_service.py
    zipf.writestr('lc_validation/services/parser_service.py', """import re
from datetime import datetime

def parse_lc(lc_text: str) -> dict:
    patterns = {
        "credit_type": r"IRREVOCABLE DOCUMENTARY LETTER OF CREDIT",
        "ucp_reference": r"Subject to Uniform Customs & Practice for Documentary Credits.*?UCP 600",
        "lc_number": r"LC Number:\\s*(.+)",
        "date_of_issue": r"Date of Issue:\\s*(.+)",
        "issuing_bank": r"Issuing Bank:\\s*(.+?)(?=\\n\\n)",
        "applicant": r"Applicant:\\s*(.+?)(?=\\n\\n)",
        "beneficiary": r"Beneficiary:\\s*(.+?)(?=\\n\\n)",
        "amount": r"Amount:\\s*(.+)",
        "expiry_date": r"Expiry Date:\\s*(.+)",
        "expiry_place": r"Expiry Place:\\s*(.+)",
        "availability": r"Available by (.+?) draft",
        "incoterm": r"Incoterm:\\s*(.+)",
        "latest_shipment": r"Latest Shipment Date:\\s*(.+)",
        "port_loading": r"Port of Loading:\\s*(.+)",
        "port_discharge": r"Port of Discharge:\\s*(.+)",
        "goods_description": r"Goods:\\s*(.+)",
        "documents": r"Documents Required:(.+?)(?=Partial Shipments)",
        "partial_shipments": r"Partial Shipments:\\s*(.+)",
        "transshipment": r"Transshipment:\\s*(.+)",
    }
    
    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, lc_text, re.DOTALL | re.IGNORECASE)
        if match:
            # Extract the first group if exists, otherwise the whole match
            results[key] = match.group(1).strip() if match.lastindex else match.group(0).strip()
        else:
            results[key] = None
    
    # Convert dates to standard format
    date_fields = ['date_of_issue', 'expiry_date', 'latest_shipment']
    for field in date_fields:
        if results.get(field):
            try:
                results[field] = datetime.strptime(results[field], "%B %d, %Y").strftime("%Y-%m-%d")
            except:
                pass
    
    return results
""")

    # 4. services/embedding_service.py
    zipf.writestr('lc_validation/services/embedding_service.py', """import os
import pandas as pd
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document

def create_vector_store(csv_path: str):
    # Load mappings data
    df = pd.read_csv(csv_path)
    documents = []
    metadatas = []
    
    for _, row in df.iterrows():
        content = f"{row['LC Section']}: {row['Remarks']}"
        metadata = {
            "lc_section": row['LC Section'],
            "ucp600": row['UCP600 Article'],
            "isbp745": row['ISBP745 Section'],
            "remarks": row['Remarks']
        }
        documents.append(Document(page_content=content, metadata=metadata))
        metadatas.append(metadata)
    
    # Create embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Create vector store
    return Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

def get_relevant_rules(vector_store, query: str, k: int = 3):
    return vector_store.similarity_search(query, k=k)
""")

    # 5. agents/base_agent.py
    zipf.writestr('lc_validation/agents/base_agent.py', """from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

class BaseValidationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    def validate(self, lc_data: dict, rules: list) -> dict:
        prompt = self._create_prompt(lc_data, rules)
        response = self.llm.invoke(prompt)
        return self._parse_response(response.content)
    
    def _create_prompt(self, lc_data: dict, rules: list) -> list:
        raise NotImplementedError("Subclasses must implement this method")
    
    def _parse_response(self, response: str) -> dict:
        # Extract validation result from LLM response
        status = "Pass"
        details = response
        
        if "fail" in response.lower():
            status = "Fail"
        elif "warning" in response.lower():
            status = "Warning"
            
        return {
            "section": self.section_name,
            "status": status,
            "details": details,
            "rules": [rule.metadata for rule in rules]
        }
""")

    # 6. agents/credit_type_agent.py
    zipf.writestr('lc_validation/agents/credit_type_agent.py', """from .base_agent import BaseValidationAgent

class CreditTypeAgent(BaseValidationAgent):
    section_name = "Credit Type"
    
    def _create_prompt(self, lc_data: dict, rules: list) -> list:
        rules_text = "\\n".join([rule.page_content for rule in rules])
        credit_type = lc_data.get('credit_type')
        ucp_reference = lc_data.get('ucp_reference')
        
        return [
            SystemMessage(content=(
                "You are a trade finance expert validating Letters of Credit against UCP600 and ISBP745 rules. "
                "Validate if the LC credit type complies with the relevant rules. Focus on irrevocability."
            )),
            HumanMessage(content=(
                f"LC Credit Type: {credit_type}\\n"
                f"UCP Reference: {ucp_reference}\\n\\n"
                f"Relevant Rules:\\n{rules_text}\\n\\n"
                "Provide validation result in the format: "
                "Status: [Pass/Fail/Warning]\\nDetails: [explanation]"
            ))
        ]
""")

    # 7. agents/amount_agent.py
    zipf.writestr('lc_validation/agents/amount_agent.py', """from .base_agent import BaseValidationAgent

class AmountAgent(BaseValidationAgent):
    section_name = "Amount"
    
    def _create_prompt(self, lc_data: dict, rules: list) -> list:
        rules_text = "\\n".join([rule.page_content for rule in rules])
        amount = lc_data.get('amount')
        
        return [
            SystemMessage(content=(
                "You are a trade finance expert validating LC amount against UCP600 Article 30 "
                "and ISBP745 section C6. Check if the amount is expressed with proper currency and "
                "if tolerances are correctly applied."
            )),
            HumanMessage(content=(
                f"LC Amount: {amount}\\n\\n"
                f"Relevant Rules:\\n{rules_text}\\n\\n"
                "Validate the amount for compliance. Focus on: "
                "- Currency code consistency "
                "- Tolerance allowances (+/- 10% unless otherwise specified) "
                "- Expression in words and figures (if provided)\\n\\n"
                "Provide validation result in the format: "
                "Status: [Pass/Fail/Warning]\\nDetails: [explanation]"
            ))
        ]
""")

    # 8. agents/expiry_agent.py
    zipf.writestr('lc_validation/agents/expiry_agent.py', """from .base_agent import BaseValidationAgent
from datetime import datetime

class ExpiryAgent(BaseValidationAgent):
    section_name = "Expiry"
    
    def _create_prompt(self, lc_data: dict, rules: list) -> list:
        rules_text = "\\n".join([rule.page_content for rule in rules])
        today = datetime.now().strftime("%Y-%m-%d")
        
        return [
            SystemMessage(content=(
                "You are a trade finance expert validating LC expiry details against UCP600 Article 66 "
                "and ISBP745 sections A14-A15. Check if dates are properly formatted and calculate if "
                "presentation period is sufficient."
            )),
            HumanMessage(content=(
                f"Today's Date: {today}\\n"
                f"LC Issue Date: {lc_data.get('date_of_issue')}\\n"
                f"Expiry Date: {lc_data.get('expiry_date')}\\n"
                f"Latest Shipment Date: {lc_data.get('latest_shipment')}\\n"
                f"Presentation Period: 21 days after shipment\\n\\n"
                f"Relevant Rules:\\n{rules_text}\\n\\n"
                "Validate and calculate if presentation period is sufficient. "
                "Provide validation result in the format: "
                "Status: [Pass/Fail/Warning]\\nDetails: [explanation]"
            ))
        ]
""")

    # 9. agents/document_agent.py
    zipf.writestr('lc_validation/agents/document_agent.py', """from .base_agent import BaseValidationAgent

class DocumentAgent(BaseValidationAgent):
    section_name = "Documents"
    
    def _create_prompt(self, lc_data: dict, rules: list) -> list:
        rules_text = "\\n".join([rule.page_content for rule in rules])
        documents = lc_data.get("documents", "")
        
        return [
            SystemMessage(content=(
                "You are a trade finance expert validating LC document requirements against "
                "UCP600 and ISBP745 rules. Check for completeness, consistency, and compliance "
                "with standard banking practices."
            )),
            HumanMessage(content=(
                f"Required Documents:\\n{documents}\\n\\n"
                f"Relevant Rules:\\n{rules_text}\\n\\n"
                "Validate the document requirements for compliance. Focus on: "
                "- Invoice requirements (Article 18, C1-C15) "
                "- B/L requirements (Article 20, E1-E28) "
                "- Insurance requirements (Article 28, K1-K23) "
                "- Origin certificate requirements (Article 14f, L1-L8) "
                "- Packing list requirements (Article 14f, M1-M6)\\n\\n"
                "Provide validation result in the format: "
                "Status: [Pass/Fail/Warning]\\nDetails: [explanation]"
            ))
        ]
""")

    # 10. main.py
    zipf.writestr('lc_validation/main.py', """import os
import json
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from services.parser_service import parse_lc
from services.embedding_service import create_vector_store, get_relevant_rules
from agents.credit_type_agent import CreditTypeAgent
from agents.amount_agent import AmountAgent
from agents.expiry_agent import ExpiryAgent
from agents.document_agent import DocumentAgent

# Load environment variables
load_dotenv()

# Define state structure
class ValidationState(TypedDict):
    lc_data: dict
    vector_store: object
    results: dict

def run_validation(lc_text: str):
    # Parse LC
    lc_data = parse_lc(lc_text)
    print("Parsed LC Data:", json.dumps(lc_data, indent=2))
    
    # Create vector store
    vector_store = create_vector_store("./data/mappings.csv")
    
    # Initialize agents
    agents = {
        "credit_type": CreditTypeAgent(),
        "amount": AmountAgent(),
        "expiry": ExpiryAgent(),
        "documents": DocumentAgent(),
    }
    
    # Create workflow
    workflow = StateGraph(ValidationState)
    
    # Add nodes for each agent
    for agent_name in agents.keys():
        workflow.add_node(agent_name, lambda state, agent_name=agent_name: validate_section(state, agent_name, agents))
    
    # Set entry point
    workflow.set_entry_point("credit_type")
    
    # Define sequential execution
    workflow.add_edge("credit_type", "amount")
    workflow.add_edge("amount", "expiry")
    workflow.add_edge("expiry", "documents")
    workflow.add_edge("documents", END)
    
    # Compile the graph
    app = workflow.compile()
    
    # Execute validation
    results = app.invoke({
        "lc_data": lc_data,
        "vector_store": vector_store,
        "results": {}
    })
    
    return results["results"]

def validate_section(state: ValidationState, agent_name: str, agents: dict) -> dict:
    agent = agents[agent_name]
    
    # Get relevant rules
    rules = get_relevant_rules(
        state["vector_store"], 
        f"Validation rules for {agent.section_name}",
        k=3
    )
    
    # Run validation
    result = agent.validate(state["lc_data"], rules)
    
    # Update results
    state["results"][agent.section_name] = result
    return {"results": state["results"]}

if __name__ == "__main__":
    # Load sample LC
    try:
        with open("sampleLC.txt", "r") as f:
            lc_text = f.read()
    except FileNotFoundError:
        print("Sample LC file not found. Using default.")
        lc_text = \"\"\"IRREVOCABLE DOCUMENTARY LETTER OF CREDIT
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

Full set of clean on board marine bills of lading, consigned to order of issuing bank, marked 'Freight Prepaid'

Insurance policy/certificate in negotiable form, covering at least 110% of invoice value, indicating "All Risks"

Certificate of origin issued by Paris Chamber of Commerce

Packing list in 1 original and 2 copies

Documents must be presented within 21 days after shipment date but not later than expiry date.

Partial Shipments: Allowed
Transshipment: Not Allowed

This credit is subject to Uniform Customs and Practice for Documentary Credits (UCP 600), ICC Publication No. 600.

All banking charges outside Singapore are for beneficiary's account; Singapore charges for applicant's account.

Commercial invoice must indicate LC number.
All documents must be in English.

Confirmation: Not Requested

Authorized Signature:
[Signature]
Global Trust Bank
Singapore\"\"\"
    
    # Run validation
    results = run_validation(lc_text)
    print("\\nValidation Results:")
    print(json.dumps(results, indent=2))
""")

    # 11. sampleLC.txt
    zipf.writestr('lc_validation/sampleLC.txt', """IRREVOCABLE DOCUMENTARY LETTER OF CREDIT
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

Full set of clean on board marine bills of lading, consigned to order of issuing bank, marked 'Freight Prepaid'

Insurance policy/certificate in negotiable form, covering at least 110% of invoice value, indicating "All Risks"

Certificate of origin issued by Paris Chamber of Commerce

Packing list in 1 original and 2 copies

Documents must be presented within 21 days after shipment date but not later than expiry date.

Partial Shipments: Allowed
Transshipment: Not Allowed

This credit is subject to Uniform Customs and Practice for Documentary Credits (UCP 600), ICC Publication No. 600.

All banking charges outside Singapore are for beneficiary's account; Singapore charges for applicant's account.

Commercial invoice must indicate LC number.
All documents must be in English.

Confirmation: Not Requested

Authorized Signature:
[Signature]
Global Trust Bank
Singapore""")

    # 12. .env.example
    zipf.writestr('lc_validation/.env.example', """# Add your OpenAI API key
OPENAI_API_KEY=your_api_key_here

# ChromaDB settings
CHROMA_PERSIST_DIR=./chroma_db
""")

    # 13. README.md
    zipf.writestr('lc_validation/README.md', """# LC Validation System

This system validates Letters of Credit against UCP600 and ISBP745 standards using AI agents.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate   # Windows


