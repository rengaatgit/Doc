
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

        return "\n".join(analysis)

    def _format_documents(self, documents: List[str]) -> str:
        """Format document list for prompt"""
        return "\n".join(f"- {doc}" for doc in documents)
