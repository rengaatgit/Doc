
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

        return "\n".join(analysis)
