# Create remaining specialized agents

document_agent_code = '''
"""
Document Requirements Agent
Validates all document requirements against UCP600 articles and ISBP745 practices
"""

from typing import List, Dict, Any
from .base_agent import BaseValidationAgent
from ..parsers.lc_parser import LCData


class DocumentRequirementsAgent(BaseValidationAgent):
    """Agent for validating document requirements and specifications"""
    
    def get_validation_focus(self) -> List[str]:
        return ["documents", "document_requirements", "originals_copies"]
    
    def create_validation_prompt(self, lc_data: LCData, context: Dict) -> str:
        doc_analysis = self._analyze_documents(lc_data)
        
        prompt = f"""
As an expert in documentary credits and document examination, validate the document requirements of this Letter of Credit.

Required Documents:
{self._format_documents(lc_data.documents_required)}

Document Analysis:
{doc_analysis}

Relevant UCP600/ISBP745 Rules:
{self._format_context(context)}

Validation Requirements:
1. All required documents properly specified per UCP600 Articles 18-28
2. Original/copy requirements per UCP600 Article 17
3. Document titles and functions per ISBP745 practices
4. Signature requirements per UCP600 Article 3 and ISBP745
5. Specific document validation per relevant articles

Provide validation results in JSON format:
{{
    "compliant": true/false,
    "issues": ["document requirement issues"],
    "recommendations": ["document requirement improvements"],
    "confidence": 0.0-1.0,
    "document_checks": {{
        "invoice_requirements_clear": true/false,
        "transport_document_compliant": true/false,
        "insurance_requirements_adequate": true/false,
        "other_documents_specified": true/false,
        "originals_copies_clear": true/false
    }}
}}
"""
        return prompt
    
    def _analyze_documents(self, lc_data: LCData) -> str:
        """Analyze document requirements for completeness and clarity"""
        analysis = []
        
        doc_categories = {
            "Invoice": ["invoice", "commercial invoice"],
            "Transport": ["bill of lading", "b/l", "waybill", "transport"],
            "Insurance": ["insurance", "policy", "certificate"],
            "Origin": ["certificate of origin", "origin"],
            "Packing": ["packing list", "packing"]
        }
        
        found_categories = set()
        
        for doc in lc_data.documents_required:
            doc_lower = doc.lower()
            for category, keywords in doc_categories.items():
                if any(keyword in doc_lower for keyword in keywords):
                    found_categories.add(category)
                    break
        
        analysis.append(f"Document categories found: {', '.join(found_categories)}")
        
        # Check for essential documents
        essential_docs = {"Invoice", "Transport"}
        missing_essential = essential_docs - found_categories
        if missing_essential:
            analysis.append(f"WARNING: Missing essential document types: {', '.join(missing_essential)}")
        else:
            analysis.append("Essential document types present")
        
        # Analyze original/copy specifications
        original_copy_specified = any("original" in doc.lower() or "copy" in doc.lower() or "copies" in doc.lower() 
                                     for doc in lc_data.documents_required)
        analysis.append(f"Original/copy specifications: {'Present' if original_copy_specified else 'Not specified'}")
        
        return "\\n".join(analysis)
    
    def _format_documents(self, documents: List[str]) -> str:
        """Format document list for prompt"""
        return "\\n".join(f"- {doc}" for doc in documents)
'''

shipping_agent_code = '''
"""
Shipping Terms Agent
Validates shipping terms, ports, incoterms, and transport requirements
"""

from typing import List, Dict, Any
from .base_agent import BaseValidationAgent
from ..parsers.lc_parser import LCData


class ShippingTermsAgent(BaseValidationAgent):
    """Agent for validating shipping and transport terms"""
    
    def get_validation_focus(self) -> List[str]:
        return ["shipping", "transport", "incoterms", "ports"]
    
    def create_validation_prompt(self, lc_data: LCData, context: Dict) -> str:
        shipping_analysis = self._analyze_shipping_terms(lc_data)
        
        prompt = f"""
As an expert in international trade and documentary credits, validate the shipping terms and transport requirements.

Shipping Information:
- Incoterm: {lc_data.incoterm}
- Port of Loading: {lc_data.port_of_loading}
- Port of Discharge: {lc_data.port_of_discharge}
- Latest Shipment Date: {lc_data.latest_shipment_date}
- Partial Shipments: {'Allowed' if lc_data.partial_shipments else 'Not Allowed'}
- Transshipment: {'Allowed' if lc_data.transshipment_allowed else 'Not Allowed'}

Shipping Analysis:
{shipping_analysis}

Relevant UCP600/ISBP745 Rules:
{self._format_context(context)}

Validation Requirements:
1. Incoterm properly specified and consistent with document requirements
2. Port names clear and unambiguous per ISBP745
3. Partial shipment terms per UCP600 Article 31
4. Transshipment provisions per UCP600 Articles 20-21
5. Transport document requirements alignment

Provide validation results in JSON format:
{{
    "compliant": true/false,
    "issues": ["shipping term issues"],
    "recommendations": ["shipping term improvements"],
    "confidence": 0.0-1.0,
    "shipping_checks": {{
        "incoterm_valid": true/false,
        "ports_clearly_specified": true/false,
        "partial_shipment_clear": true/false,
        "transshipment_terms_clear": true/false,
        "transport_mode_consistent": true/false
    }}
}}
"""
        return prompt
    
    def _analyze_shipping_terms(self, lc_data: LCData) -> str:
        """Analyze shipping terms for compliance and consistency"""
        analysis = []
        
        # Analyze incoterm
        incoterm = lc_data.incoterm.upper()
        if incoterm.startswith('CIF'):
            analysis.append("Incoterm CIF: Seller responsible for cost, insurance, freight")
            analysis.append("Insurance document required (confirmed by CIF term)")
        elif incoterm.startswith('FOB'):
            analysis.append("Incoterm FOB: Free on Board - buyer arranges insurance")
        else:
            analysis.append(f"Incoterm {incoterm}: Please verify standard incoterm compliance")
        
        # Analyze port specifications
        if lc_data.port_of_loading and lc_data.port_of_discharge:
            analysis.append(f"Port routing: {lc_data.port_of_loading} → {lc_data.port_of_discharge}")
            
            # Check for potential geographical issues
            if "france" in lc_data.port_of_loading.lower() and "malaysia" in lc_data.port_of_discharge.lower():
                analysis.append("International shipping route: Europe to Southeast Asia")
            else:
                analysis.append("Port routing appears standard")
        
        # Analyze shipment terms
        analysis.append(f"Partial shipments: {'Permitted' if lc_data.partial_shipments else 'Prohibited'}")
        analysis.append(f"Transshipment: {'Permitted' if lc_data.transshipment_allowed else 'Prohibited'}")
        
        # Check consistency
        if not lc_data.transshipment_allowed:
            analysis.append("Note: Transshipment prohibition may require specific B/L terms per UCP600")
        
        return "\\n".join(analysis)
'''

bank_details_agent_code = '''
"""
Bank Details Agent
Validates bank information, addresses, and roles per UCP600
"""

from typing import List, Dict, Any
from .base_agent import BaseValidationAgent
from ..parsers.lc_parser import LCData


class BankDetailsAgent(BaseValidationAgent):
    """Agent for validating bank details and roles"""
    
    def get_validation_focus(self) -> List[str]:
        return ["parties", "banks", "addresses"]
    
    def create_validation_prompt(self, lc_data: LCData, context: Dict) -> str:
        bank_analysis = self._analyze_bank_details(lc_data)
        
        prompt = f"""
As an expert in documentary credits, validate the bank and party details of this Letter of Credit.

Bank and Party Information:
Issuing Bank: {lc_data.issuing_bank['name']}
Address: {lc_data.issuing_bank['address']}

Applicant: {lc_data.applicant['name']}
Address: {lc_data.applicant['address']}

Beneficiary: {lc_data.beneficiary['name']}  
Address: {lc_data.beneficiary['address']}

Bank Analysis:
{bank_analysis}

Relevant UCP600/ISBP745 Rules:
{self._format_context(context)}

Validation Requirements:
1. Issuing bank clearly identified per UCP600 Article 2
2. All parties properly named and addressed
3. Address consistency requirements per UCP600 Article 14(j)
4. Party roles clearly defined
5. Geographic considerations for operations

Provide validation results in JSON format:
{{
    "compliant": true/false,
    "issues": ["bank/party detail issues"],
    "recommendations": ["improvements for bank/party details"],
    "confidence": 0.0-1.0,
    "party_checks": {{
        "issuing_bank_identified": true/false,
        "applicant_properly_named": true/false,
        "beneficiary_properly_named": true/false,
        "addresses_complete": true/false,
        "roles_clear": true/false
    }}
}}
"""
        return prompt
    
    def _analyze_bank_details(self, lc_data: LCData) -> str:
        """Analyze bank and party details for completeness"""
        analysis = []
        
        # Check issuing bank details
        if lc_data.issuing_bank['name'] and lc_data.issuing_bank['address']:
            analysis.append("Issuing bank: Name and address provided")
            if 'singapore' in lc_data.issuing_bank['address'].lower():
                analysis.append("Issuing bank location: Singapore")
        else:
            analysis.append("WARNING: Issuing bank details incomplete")
        
        # Check applicant details
        if lc_data.applicant['name'] and lc_data.applicant['address']:
            analysis.append("Applicant: Name and address provided")
            if 'malaysia' in lc_data.applicant['address'].lower():
                analysis.append("Applicant location: Malaysia")
        else:
            analysis.append("WARNING: Applicant details incomplete")
        
        # Check beneficiary details
        if lc_data.beneficiary['name'] and lc_data.beneficiary['address']:
            analysis.append("Beneficiary: Name and address provided")
            if 'france' in lc_data.beneficiary['address'].lower():
                analysis.append("Beneficiary location: France")
        else:
            analysis.append("WARNING: Beneficiary details incomplete")
        
        # Geographic analysis
        countries = []
        for party in ['issuing_bank', 'applicant', 'beneficiary']:
            address = lc_data.__dict__.get(party, {}).get('address', '').lower()
            if 'singapore' in address:
                countries.append('Singapore')
            elif 'malaysia' in address:
                countries.append('Malaysia')  
            elif 'france' in address:
                countries.append('France')
        
        if len(set(countries)) == 3:
            analysis.append("Multi-country transaction: Singapore, Malaysia, France")
        
        return "\\n".join(analysis)
'''

# Save the remaining specialized agents
with open('lc_validation_system/src/agents/document_requirements_agent.py', 'w') as f:
    f.write(document_agent_code)

with open('lc_validation_system/src/agents/shipping_terms_agent.py', 'w') as f:
    f.write(shipping_agent_code)

with open('lc_validation_system/src/agents/bank_details_agent.py', 'w') as f:
    f.write(bank_details_agent_code)

print("Remaining specialized agents created:")
print("- src/agents/document_requirements_agent.py")
print("- src/agents/shipping_terms_agent.py")
print("- src/agents/bank_details_agent.py")