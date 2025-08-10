
"""
Credit Type Validation Agent
Validates LC type, irrevocability, and UCP600 compliance
"""

from typing import List, Dict, Any
from .base_agent import BaseValidationAgent
from ..parsers.lc_parser import LCData


class CreditTypeAgent(BaseValidationAgent):
    """Agent for validating credit type and basic LC structure"""

    def get_validation_focus(self) -> List[str]:
        return ["credit_type", "irrevocability", "ucp600_compliance"]

    def create_validation_prompt(self, lc_data: LCData, context: Dict) -> str:
        prompt = f"""
As an expert in documentary credits and UCP600 rules, validate the following Letter of Credit structure and type compliance.

LC Details:
- Document Type: Irrevocable Documentary Letter of Credit
- UCP Reference: Subject to UCP 600
- LC Number: {lc_data.lc_number}
- Date of Issue: {lc_data.date_of_issue}
- Availability: {lc_data.availability_type}

Relevant UCP600 Rules and ISBP745 Practices:
{self._format_context(context)}

Validation Requirements:
1. Verify the LC is properly declared as irrevocable
2. Check UCP600 reference is correctly stated
3. Validate availability type compliance with UCP600 Article 6
4. Ensure proper LC structure according to UCP600 Article 1

Please provide validation results in the following JSON format:
{{
    "compliant": true/false,
    "issues": ["list of compliance issues"],
    "recommendations": ["list of recommendations"],
    "confidence": 0.0-1.0,
    "specific_checks": {{
        "irrevocability_declared": true/false,
        "ucp600_reference_correct": true/false,
        "availability_type_valid": true/false,
        "structure_compliant": true/false
    }}
}}
"""
        return prompt

    def _format_context(self, context: Dict) -> str:
        formatted = ""
        for section, content in context.items():
            if content.get('ucp600_rules'):
                formatted += f"\nUCP600 Rules for {section}:\n"
                for rule in content['ucp600_rules'][:3]:
                    formatted += f"- {rule['content'][:200]}...\n"

            if content.get('isbp745_practices'):
                formatted += f"\nISBP745 Practices for {section}:\n"
                for practice in content['isbp745_practices'][:2]:
                    formatted += f"- {practice['content'][:200]}...\n"

        return formatted
