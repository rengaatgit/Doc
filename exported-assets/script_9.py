# Create __init__.py files for proper package structure

# Create main __init__.py
main_init = '''
"""
LC Validation System
A comprehensive system for validating Letters of Credit against UCP600 and ISBP745 standards
"""

__version__ = "1.0.0"
__author__ = "Trade Finance Expert"
__description__ = "AI-powered Letter of Credit validation using RAG and multi-agent architecture"

from .main import LCValidationSystem
from .src.parsers.lc_parser import LCParser, LCData
from .src.orchestrator import LCValidationOrchestrator

__all__ = ["LCValidationSystem", "LCParser", "LCData", "LCValidationOrchestrator"]
'''

# Create src __init__.py  
src_init = '''
"""
Source modules for LC validation system
"""
'''

# Create agents __init__.py
agents_init = '''
"""
Validation agents for different aspects of LC compliance
"""

from .base_agent import BaseValidationAgent
from .credit_type_agent import CreditTypeAgent
from .date_validation_agent import DateValidationAgent
from .amount_validation_agent import AmountValidationAgent
from .document_requirements_agent import DocumentRequirementsAgent
from .shipping_terms_agent import ShippingTermsAgent
from .bank_details_agent import BankDetailsAgent

__all__ = [
    "BaseValidationAgent",
    "CreditTypeAgent", 
    "DateValidationAgent",
    "AmountValidationAgent",
    "DocumentRequirementsAgent",
    "ShippingTermsAgent",
    "BankDetailsAgent"
]
'''

# Create rag __init__.py
rag_init = '''
"""
RAG (Retrieval Augmented Generation) components
"""

from .document_processor import DocumentProcessor
from .vector_database import VectorDatabaseManager

__all__ = ["DocumentProcessor", "VectorDatabaseManager"]
'''

# Create parsers __init__.py
parsers_init = '''
"""
Document parsers for LC and other trade documents
"""

from .lc_parser import LCParser, LCData

__all__ = ["LCParser", "LCData"]
'''

# Save all __init__.py files
init_files = {
    'lc_validation_system/__init__.py': main_init,
    'lc_validation_system/src/__init__.py': src_init,
    'lc_validation_system/src/agents/__init__.py': agents_init,
    'lc_validation_system/src/rag/__init__.py': rag_init,
    'lc_validation_system/src/parsers/__init__.py': parsers_init,
    'lc_validation_system/src/validators/__init__.py': '# Validators module\n',
    'lc_validation_system/tests/__init__.py': '# Tests module\n'
}

for file_path, content in init_files.items():
    with open(file_path, 'w') as f:
        f.write(content)

print("Package structure files created:")
for file_path in init_files.keys():
    print(f"- {file_path}")