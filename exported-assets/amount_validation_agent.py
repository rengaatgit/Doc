
"""
Amount Validation Agent
Validates credit amount, currency, and tolerance provisions
"""

from typing import List, Dict, Any
from .base_agent import BaseValidationAgent
from ..parsers.lc_parser import LCData
import re


class AmountValidationAgent(BaseValidationAgent):
    """Agent for validating LC amount and currency specifications"""

    def get_validation_focus(self) -> List[str]:
        return ["amounts", "currency", "tolerance"]

    def create_validation_prompt(self, lc_data: LCData, context: Dict) -> str:
        amount_analysis = self._analyze_amount(lc_data)

        prompt = f"""
As an expert in documentary credits, validate the amount and currency specifications of this Letter of Credit.

LC Amount Information:
- Currency: {lc_data.currency}
- Amount: {lc_data.amount}
- Goods Description: {lc_data.goods_description}
- Incoterm: {lc_data.incoterm}

Amount Analysis:
{amount_analysis}

Relevant UCP600/ISBP745 Rules:
{self._format_context(context)}

Validation Requirements:
1. Currency code compliance with ISO standards
2. Amount format and clarity
3. Tolerance provisions per UCP600 Article 30
4. Consistency with goods description and pricing
5. Invoice amount requirements per UCP600 Article 18

Provide validation results in JSON format:
{{
    "compliant": true/false,
    "issues": ["amount-related compliance issues"],
    "recommendations": ["recommendations for amount corrections"],
    "confidence": 0.0-1.0,
    "amount_checks": {{
        "currency_valid": true/false,
        "amount_format_clear": true/false,
        "tolerance_specified": true/false,
        "unit_pricing_consistent": true/false,
        "total_amount_correct": true/false
    }}
}}
"""
        return prompt

    def _analyze_amount(self, lc_data: LCData) -> str:
        """Analyze amount specifications and calculations"""
        analysis = []

        # Extract unit price and quantity from goods description
        goods_text = lc_data.goods_description
        unit_price_match = re.search(r'unit price.*?([\d,]+(?:\.\d{2})?)', goods_text, re.IGNORECASE)
        quantity_match = re.search(r'(\d+(?:,\d+)*)\s*units?', goods_text, re.IGNORECASE)

        if unit_price_match and quantity_match:
            try:
                unit_price = float(unit_price_match.group(1).replace(',', ''))
                quantity = int(quantity_match.group(1).replace(',', ''))
                calculated_total = unit_price * quantity

                analysis.append(f"Unit Price: {lc_data.currency} {unit_price:,.2f}")
                analysis.append(f"Quantity: {quantity:,} units")
                analysis.append(f"Calculated Total: {lc_data.currency} {calculated_total:,.2f}")
                analysis.append(f"LC Amount: {lc_data.currency} {lc_data.amount}")

                lc_amount = float(lc_data.amount.replace(',', ''))
                if abs(calculated_total - lc_amount) < 0.01:
                    analysis.append("Amount calculation: CORRECT")
                else:
                    analysis.append("Amount calculation: MISMATCH DETECTED")

            except (ValueError, AttributeError):
                analysis.append("Unable to verify amount calculation")
        else:
            analysis.append("Unit pricing information not found in goods description")

        return "\n".join(analysis)
