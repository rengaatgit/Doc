# Create LC Parser
lc_parser_code = '''
"""
Letter of Credit Parser
Extracts structured data from LC documents for validation
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LCData:
    """Structured LC data class"""
    lc_number: str
    date_of_issue: str
    issuing_bank: Dict[str, str]
    applicant: Dict[str, str] 
    beneficiary: Dict[str, str]
    amount: str
    currency: str
    expiry_date: str
    expiry_place: str
    availability_type: str
    incoterm: str
    latest_shipment_date: str
    port_of_loading: str
    port_of_discharge: str
    goods_description: str
    documents_required: List[str]
    partial_shipments: bool
    transshipment_allowed: bool
    presentation_period: str
    special_conditions: List[str]
    raw_text: str


class LCParser:
    def __init__(self):
        self.patterns = {
            'lc_number': r'LC Number:?\\s*([A-Z0-9-]+)',
            'date_of_issue': r'Date of Issue:?\\s*([A-Za-z]+ \\d{1,2}, \\d{4})',
            'amount': r'Amount:?\\s*([A-Z]{3}\\s*[\\d,]+(?:\\.\\d{2})?)',
            'expiry_date': r'Expiry Date:?\\s*([A-Za-z]+ \\d{1,2}, \\d{4})',
            'expiry_place': r'Expiry Place:?\\s*([^\\n]+)',
            'incoterm': r'Incoterm:?\\s*([A-Z]+\\s+[^\\n]+)',
            'latest_shipment_date': r'Latest Shipment Date:?\\s*([A-Za-z]+ \\d{1,2}, \\d{4})',
            'port_of_loading': r'Port of Loading:?\\s*([^\\n]+)',
            'port_of_discharge': r'Port of Discharge:?\\s*([^\\n]+)',
            'goods': r'Goods:?\\s*([^\\n]+(?:\\n[^\\n]*)*?)(?=\\n\\n|Documents Required|$)',
            'partial_shipments': r'Partial Shipments?:?\\s*(Allowed|Not Allowed|Prohibited)',
            'transshipment': r'Transshipment:?\\s*(Allowed|Not Allowed|Prohibited)'
        }
    
    def parse_lc_document(self, lc_text: str) -> LCData:
        """Parse LC document text and extract structured data"""
        extracted_data = {}
        
        # Extract basic fields using regex patterns
        for field, pattern in self.patterns.items():
            match = re.search(pattern, lc_text, re.IGNORECASE | re.MULTILINE)
            if match:
                extracted_data[field] = match.group(1).strip()
        
        # Parse bank details
        issuing_bank = self._extract_bank_details(lc_text, "Issuing Bank:")
        applicant = self._extract_party_details(lc_text, "Applicant:")
        beneficiary = self._extract_party_details(lc_text, "Beneficiary:")
        
        # Parse amount and currency
        amount_match = extracted_data.get('amount', '')
        currency, amount = self._parse_amount(amount_match)
        
        # Extract documents required
        documents = self._extract_documents_required(lc_text)
        
        # Extract availability type
        availability = self._extract_availability_type(lc_text)
        
        # Extract presentation period
        presentation_period = self._extract_presentation_period(lc_text)
        
        # Extract special conditions
        special_conditions = self._extract_special_conditions(lc_text)
        
        return LCData(
            lc_number=extracted_data.get('lc_number', ''),
            date_of_issue=extracted_data.get('date_of_issue', ''),
            issuing_bank=issuing_bank,
            applicant=applicant,
            beneficiary=beneficiary,
            amount=amount,
            currency=currency,
            expiry_date=extracted_data.get('expiry_date', ''),
            expiry_place=extracted_data.get('expiry_place', ''),
            availability_type=availability,
            incoterm=extracted_data.get('incoterm', ''),
            latest_shipment_date=extracted_data.get('latest_shipment_date', ''),
            port_of_loading=extracted_data.get('port_of_loading', ''),
            port_of_discharge=extracted_data.get('port_of_discharge', ''),
            goods_description=extracted_data.get('goods', ''),
            documents_required=documents,
            partial_shipments=self._parse_boolean_field(extracted_data.get('partial_shipments')),
            transshipment_allowed=self._parse_boolean_field(extracted_data.get('transshipment')),
            presentation_period=presentation_period,
            special_conditions=special_conditions,
            raw_text=lc_text
        )
    
    def _extract_bank_details(self, text: str, bank_label: str) -> Dict[str, str]:
        """Extract bank name and address"""
        pattern = rf"{re.escape(bank_label)}\\s*([^\\n]+(?:\\n[^\\n]*)*?)(?=\\n\\n|Applicant:|Beneficiary:|Amount:|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        if match:
            bank_text = match.group(1).strip()
            lines = [line.strip() for line in bank_text.split('\\n') if line.strip()]
            return {
                'name': lines[0] if lines else '',
                'address': '\\n'.join(lines[1:]) if len(lines) > 1 else ''
            }
        return {'name': '', 'address': ''}
    
    def _extract_party_details(self, text: str, party_label: str) -> Dict[str, str]:
        """Extract party name and address"""
        return self._extract_bank_details(text, party_label)
    
    def _parse_amount(self, amount_str: str) -> tuple[str, str]:
        """Parse amount string to extract currency and amount"""
        match = re.match(r'([A-Z]{3})\\s*([\\d,]+(?:\\.\\d{2})?)', amount_str.strip())
        if match:
            return match.group(1), match.group(2).replace(',', '')
        return '', amount_str
    
    def _extract_documents_required(self, text: str) -> List[str]:
        """Extract list of required documents"""
        doc_section_pattern = r'Documents Required:?\\s*([^\\n]+(?:\\n[^\\n]*)*?)(?=\\nDocuments must|\\nPartial|\\nTransshipment|$)'
        match = re.search(doc_section_pattern, text, re.IGNORECASE | re.MULTILINE)
        
        documents = []
        if match:
            doc_text = match.group(1).strip()
            # Split by document items (assuming each document starts on new line)
            doc_lines = [line.strip() for line in doc_text.split('\\n') if line.strip()]
            documents = [doc for doc in doc_lines if doc and not doc.startswith('Documents must')]
        
        return documents
    
    def _extract_availability_type(self, text: str) -> str:
        """Extract availability type (sight, deferred payment, etc.)"""
        availability_pattern = r'Available by\\s+([^\\n]+)'
        match = re.search(availability_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ''
    
    def _extract_presentation_period(self, text: str) -> str:
        """Extract presentation period requirements"""
        period_pattern = r'Documents must be presented\\s+([^\\n]+)'
        match = re.search(period_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ''
    
    def _extract_special_conditions(self, text: str) -> List[str]:
        """Extract special conditions and requirements"""
        conditions = []
        
        # Common special condition patterns
        condition_patterns = [
            r'Commercial invoice must\\s+([^\\n]+)',
            r'All documents must\\s+([^\\n]+)',
            r'Banking charges\\s+([^\\n]+)',
        ]
        
        for pattern in condition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                conditions.append(match.group(0).strip())
        
        return conditions
    
    def _parse_boolean_field(self, field_value: Optional[str]) -> bool:
        """Parse boolean fields like partial shipments"""
        if not field_value:
            return True  # Default to allowed if not specified
        return field_value.lower() in ['allowed', 'yes', 'true']
'''

# Create Base Validation Agent
base_agent_code = '''
"""
Base Validation Agent Class
Provides common functionality for all LC validation agents
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from dataclasses import asdict
import json


class BaseValidationAgent(ABC):
    """Base class for all LC validation agents"""
    
    def __init__(self, config: Dict, vector_db_manager):
        self.config = config
        self.vector_db = vector_db_manager
        self.llm = ChatOpenAI(
            model=config["model_name"],
            temperature=config["temperature"],
            api_key=config["openai_api_key"]
        )
        self.agent_name = self.__class__.__name__
    
    @abstractmethod
    def get_validation_focus(self) -> List[str]:
        """Return list of LC sections this agent validates"""
        pass
    
    @abstractmethod
    def create_validation_prompt(self, lc_data: Any, context: Dict) -> str:
        """Create validation prompt specific to this agent"""
        pass
    
    async def validate(self, lc_data: Any, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Main validation method"""
        try:
            # Get relevant context from vector database
            validation_context = await self._get_validation_context(lc_data)
            
            # Merge with any additional context
            if context:
                validation_context.update(context)
            
            # Create validation prompt
            prompt = self.create_validation_prompt(lc_data, validation_context)
            
            # Execute validation using LLM
            response = await self.llm.ainvoke(prompt)
            
            # Parse and structure response
            validation_result = self._parse_validation_response(response.content)
            
            return {
                "agent": self.agent_name,
                "status": "completed",
                "validation_result": validation_result,
                "confidence_score": validation_result.get("confidence", 0.0),
                "context_used": validation_context
            }
            
        except Exception as e:
            return {
                "agent": self.agent_name,
                "status": "error",
                "error": str(e),
                "validation_result": None
            }
    
    async def _get_validation_context(self, lc_data: Any) -> Dict[str, Any]:
        """Retrieve relevant context from vector database"""
        context = {}
        
        for section in self.get_validation_focus():
            # Create search query based on LC section
            query = self._create_search_query(lc_data, section)
            
            # Get relevant rules and practices
            relevant_content = self.vector_db.get_relevant_rules(section, query)
            context[section] = relevant_content
        
        return context
    
    def _create_search_query(self, lc_data: Any, section: str) -> str:
        """Create search query for specific LC section"""
        lc_dict = asdict(lc_data) if hasattr(lc_data, '__dict__') else lc_data
        
        # Extract relevant information for the section
        section_mapping = {
            "credit_type": f"irrevocable documentary letter of credit {lc_dict.get('availability_type', '')}",
            "dates": f"expiry date {lc_dict.get('expiry_date', '')} shipment date {lc_dict.get('latest_shipment_date', '')}",
            "amounts": f"credit amount {lc_dict.get('currency', '')} {lc_dict.get('amount', '')}",
            "documents": f"documents required {' '.join(lc_dict.get('documents_required', []))}",
            "shipping": f"shipment from {lc_dict.get('port_of_loading', '')} to {lc_dict.get('port_of_discharge', '')}",
            "parties": f"issuing bank applicant beneficiary {lc_dict.get('issuing_bank', {}).get('name', '')}"
        }
        
        return section_mapping.get(section, section)
    
    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM validation response into structured format"""
        try:
            # Try to parse as JSON if structured
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # Otherwise, create structured response from text
            lines = response.split('\\n')
            result = {
                "compliant": True,
                "issues": [],
                "recommendations": [],
                "confidence": 0.8,
                "details": response
            }
            
            # Simple parsing for compliance indicators
            compliance_indicators = ["non-compliant", "violation", "error", "invalid", "incorrect"]
            if any(indicator in response.lower() for indicator in compliance_indicators):
                result["compliant"] = False
                result["confidence"] = 0.9
            
            return result
            
        except Exception as e:
            return {
                "compliant": False,
                "issues": [f"Failed to parse validation response: {str(e)}"],
                "recommendations": ["Review validation logic"],
                "confidence": 0.1,
                "details": response
            }
    
    def get_validation_summary(self) -> str:
        """Return summary of what this agent validates"""
        return f"{self.agent_name} validates: {', '.join(self.get_validation_focus())}"
'''

# Save the files
with open('lc_validation_system/src/parsers/lc_parser.py', 'w') as f:
    f.write(lc_parser_code)

with open('lc_validation_system/src/agents/base_agent.py', 'w') as f:
    f.write(base_agent_code)

print("Parser and base agent created:")
print("- src/parsers/lc_parser.py")
print("- src/agents/base_agent.py")