# Create specialized validation agents
credit_type_agent_code = '''
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
                formatted += f"\\nUCP600 Rules for {section}:\\n"
                for rule in content['ucp600_rules'][:3]:
                    formatted += f"- {rule['content'][:200]}...\\n"
            
            if content.get('isbp745_practices'):
                formatted += f"\\nISBP745 Practices for {section}:\\n"
                for practice in content['isbp745_practices'][:2]:
                    formatted += f"- {practice['content'][:200]}...\\n"
        
        return formatted
'''

date_validation_agent_code = '''
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
        
        return "\\n".join(analysis)
'''

amount_validation_agent_code = '''
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
        unit_price_match = re.search(r'unit price.*?([\\d,]+(?:\\.\\d{2})?)', goods_text, re.IGNORECASE)
        quantity_match = re.search(r'(\\d+(?:,\\d+)*)\\s*units?', goods_text, re.IGNORECASE)
        
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
        
        return "\\n".join(analysis)
'''

# Save the specialized agents
with open('lc_validation_system/src/agents/credit_type_agent.py', 'w') as f:
    f.write(credit_type_agent_code)

with open('lc_validation_system/src/agents/date_validation_agent.py', 'w') as f:
    f.write(date_validation_agent_code)

with open('lc_validation_system/src/agents/amount_validation_agent.py', 'w') as f:
    f.write(amount_validation_agent_code)

print("Specialized validation agents created:")
print("- src/agents/credit_type_agent.py")
print("- src/agents/date_validation_agent.py")
print("- src/agents/amount_validation_agent.py")