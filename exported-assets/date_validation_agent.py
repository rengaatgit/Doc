
"""
Date Validation Agent  
Validates all date-related aspects of LC including expiry, shipment dates, and presentation periods
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from .base_agent import BaseValidationAgent
from ..parsers.lc_parser import LCData


class DateValidationAgent(BaseValidationAgent):
    """Agent for validating all LC date requirements"""

    def get_validation_focus(self) -> List[str]:
        return ["dates", "expiry_date", "shipment_date", "presentation_period"]

    def create_validation_prompt(self, lc_data: LCData, context: Dict) -> str:
        # Calculate date relationships
        date_analysis = self._analyze_dates(lc_data)

        prompt = f"""
As an expert in documentary credits, validate the date structure and compliance of this Letter of Credit.

LC Date Information:
- Date of Issue: {lc_data.date_of_issue}
- Expiry Date: {lc_data.expiry_date}
- Latest Shipment Date: {lc_data.latest_shipment_date}
- Presentation Period: {lc_data.presentation_period}
- Expiry Place: {lc_data.expiry_place}

Date Analysis:
{date_analysis}

Relevant UCP600/ISBP745 Rules:
{self._format_context(context)}

Validation Requirements:
1. Expiry date must be after issue date and shipment date
2. Latest shipment date must be before expiry date
3. Presentation period compliance with UCP600 Article 14(c)
4. Date format and clarity per ISBP745 paragraphs A11-A16
5. Expiry place specification per UCP600 Article 6

Provide validation results in JSON format:
{{
    "compliant": true/false,
    "issues": ["list of date-related issues"],
    "recommendations": ["recommendations for date corrections"],
    "confidence": 0.0-1.0,
    "date_checks": {{
        "expiry_after_issue": true/false,
        "shipment_before_expiry": true/false,
        "presentation_period_valid": true/false,
        "date_formats_clear": true/false,
        "expiry_place_specified": true/false
    }}
}}
"""
        return prompt

    def _analyze_dates(self, lc_data: LCData) -> str:
        """Analyze date relationships and calculate periods"""
        analysis = []

        try:
            issue_date = datetime.strptime(lc_data.date_of_issue, "%B %d, %Y")
            expiry_date = datetime.strptime(lc_data.expiry_date, "%B %d, %Y") 
            shipment_date = datetime.strptime(lc_data.latest_shipment_date, "%B %d, %Y")

            # Calculate periods
            lc_validity_days = (expiry_date - issue_date).days
            shipment_to_expiry_days = (expiry_date - shipment_date).days

            analysis.append(f"LC Validity Period: {lc_validity_days} days")
            analysis.append(f"Shipment to Expiry Period: {shipment_to_expiry_days} days")

            # Check logical order
            if issue_date <= shipment_date <= expiry_date:
                analysis.append("Date sequence: CORRECT")
            else:
                analysis.append("Date sequence: INCORRECT - dates are not in logical order")

        except ValueError as e:
            analysis.append(f"Date parsing error: {str(e)}")

        return "\n".join(analysis)
