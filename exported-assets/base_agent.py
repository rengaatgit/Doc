
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
            lines = response.split('\n')
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
