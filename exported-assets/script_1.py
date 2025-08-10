# Create the project structure and system architecture
import os
import json

# Create project directory structure
project_structure = {
    'lc_validation_system': {
        'src': {
            'agents': {},
            'rag': {},
            'parsers': {},
            'validators': {}
        },
        'data': {},
        'config': {},
        'tests': {},
        'docs': {}
    }
}

def create_directory_structure(structure, base_path='.'):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        os.makedirs(path, exist_ok=True)
        if isinstance(content, dict):
            create_directory_structure(content, path)

create_directory_structure(project_structure)
print("Project structure created successfully!")

# Create system architecture diagrams in Mermaid format
logical_diagram = '''
graph TD
    A[LC Document Input] --> B[LC Parser]
    B --> C[Validation Router]
    C --> D[Agent Orchestrator - LangGraph]
    
    D --> E1[Credit Type Agent]
    D --> E2[Date Validation Agent]
    D --> E3[Bank Details Agent]
    D --> E4[Amount Validation Agent]
    D --> E5[Document Requirements Agent]
    D --> E6[Shipping Terms Agent]
    D --> E7[Insurance Terms Agent]
    D --> E8[General Terms Agent]
    
    E1 --> F[RAG Knowledge Base]
    E2 --> F
    E3 --> F
    E4 --> F
    E5 --> F
    E6 --> F
    E7 --> F
    E8 --> F
    
    F --> G1[UCP600 Vector Store]
    F --> G2[ISBP745 Vector Store]
    F --> G3[Mappings Store]
    
    E1 --> H[Results Aggregator]
    E2 --> H
    E3 --> H
    E4 --> H
    E5 --> H
    E6 --> H
    E7 --> H
    E8 --> H
    
    H --> I[Validation Report Generator]
    I --> J[Final Validation Report]
'''

data_flow_diagram = '''
graph TD
    A[Input LC Document] --> B[Text Preprocessing]
    B --> C[LC Section Extraction]
    C --> D[Mapping Resolution]
    
    D --> E[Parallel Agent Processing]
    
    E --> F1[Agent 1: Query Vector DB]
    E --> F2[Agent 2: Query Vector DB]  
    E --> F3[Agent 3: Query Vector DB]
    E --> F4[Agent N: Query Vector DB]
    
    F1 --> G1[UCP600 Rules Retrieval]
    F2 --> G2[ISBP745 Guidelines Retrieval]
    F3 --> G3[Compliance Checking]
    F4 --> G4[Validation Logic]
    
    G1 --> H[LLM Analysis]
    G2 --> H
    G3 --> H
    G4 --> H
    
    H --> I[Validation Results]
    I --> J[Aggregation & Scoring]
    J --> K[Report Generation]
    K --> L[JSON/PDF Output]
'''

# Save diagrams
with open('lc_validation_system/docs/logical_architecture.md', 'w') as f:
    f.write(f"# LC Validation System - Logical Architecture\n\n```mermaid\n{logical_diagram}\n```")

with open('lc_validation_system/docs/data_flow.md', 'w') as f:
    f.write(f"# LC Validation System - Data Flow\n\n```mermaid\n{data_flow_diagram}\n```")

print("Architecture diagrams created!")
print("Logical Architecture:", "lc_validation_system/docs/logical_architecture.md")
print("Data Flow:", "lc_validation_system/docs/data_flow.md")