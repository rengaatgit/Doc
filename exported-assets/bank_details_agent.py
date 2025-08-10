
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

        return "\n".join(analysis)
