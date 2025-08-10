
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
            'lc_number': r'LC Number:?\s*([A-Z0-9-]+)',
            'date_of_issue': r'Date of Issue:?\s*([A-Za-z]+ \d{1,2}, \d{4})',
            'amount': r'Amount:?\s*([A-Z]{3}\s*[\d,]+(?:\.\d{2})?)',
            'expiry_date': r'Expiry Date:?\s*([A-Za-z]+ \d{1,2}, \d{4})',
            'expiry_place': r'Expiry Place:?\s*([^\n]+)',
            'incoterm': r'Incoterm:?\s*([A-Z]+\s+[^\n]+)',
            'latest_shipment_date': r'Latest Shipment Date:?\s*([A-Za-z]+ \d{1,2}, \d{4})',
            'port_of_loading': r'Port of Loading:?\s*([^\n]+)',
            'port_of_discharge': r'Port of Discharge:?\s*([^\n]+)',
            'goods': r'Goods:?\s*([^\n]+(?:\n[^\n]*)*?)(?=\n\n|Documents Required|$)',
            'partial_shipments': r'Partial Shipments?:?\s*(Allowed|Not Allowed|Prohibited)',
            'transshipment': r'Transshipment:?\s*(Allowed|Not Allowed|Prohibited)'
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
        pattern = rf"{re.escape(bank_label)}\s*([^\n]+(?:\n[^\n]*)*?)(?=\n\n|Applicant:|Beneficiary:|Amount:|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)

        if match:
            bank_text = match.group(1).strip()
            lines = [line.strip() for line in bank_text.split('\n') if line.strip()]
            return {
                'name': lines[0] if lines else '',
                'address': '\n'.join(lines[1:]) if len(lines) > 1 else ''
            }
        return {'name': '', 'address': ''}

    def _extract_party_details(self, text: str, party_label: str) -> Dict[str, str]:
        """Extract party name and address"""
        return self._extract_bank_details(text, party_label)

    def _parse_amount(self, amount_str: str) -> tuple[str, str]:
        """Parse amount string to extract currency and amount"""
        match = re.match(r'([A-Z]{3})\s*([\d,]+(?:\.\d{2})?)', amount_str.strip())
        if match:
            return match.group(1), match.group(2).replace(',', '')
        return '', amount_str

    def _extract_documents_required(self, text: str) -> List[str]:
        """Extract list of required documents"""
        doc_section_pattern = r'Documents Required:?\s*([^\n]+(?:\n[^\n]*)*?)(?=\nDocuments must|\nPartial|\nTransshipment|$)'
        match = re.search(doc_section_pattern, text, re.IGNORECASE | re.MULTILINE)

        documents = []
        if match:
            doc_text = match.group(1).strip()
            # Split by document items (assuming each document starts on new line)
            doc_lines = [line.strip() for line in doc_text.split('\n') if line.strip()]
            documents = [doc for doc in doc_lines if doc and not doc.startswith('Documents must')]

        return documents

    def _extract_availability_type(self, text: str) -> str:
        """Extract availability type (sight, deferred payment, etc.)"""
        availability_pattern = r'Available by\s+([^\n]+)'
        match = re.search(availability_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ''

    def _extract_presentation_period(self, text: str) -> str:
        """Extract presentation period requirements"""
        period_pattern = r'Documents must be presented\s+([^\n]+)'
        match = re.search(period_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ''

    def _extract_special_conditions(self, text: str) -> List[str]:
        """Extract special conditions and requirements"""
        conditions = []

        # Common special condition patterns
        condition_patterns = [
            r'Commercial invoice must\s+([^\n]+)',
            r'All documents must\s+([^\n]+)',
            r'Banking charges\s+([^\n]+)',
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
