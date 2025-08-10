
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import AgentRunner
from llama_index.core.tools import FunctionTool
from llama_index.core.prompts import ChatPromptTemplate

class LCAgent:
    def __init__(self, llm, query_engine):
        self.llm = llm
        self.query_engine = query_engine

    def parse_lc_section(self, lc_content: str, section_name: str) -> str:
        """Parses a specific section from the LC content."""
        # This is a simplified parsing. In a real scenario, this would be more robust.
        # For now, we'll use the LLM to extract the section.
        prompt = f"""Extract the content of the '{section_name}' section from the following Letter of Credit:

        {lc_content}

        If the section is not explicitly mentioned, try to infer it from context.
        Return 'N/A' if the section cannot be found or inferred.
        """
        response = self.llm.complete(prompt)
        return response.text

    def validate_ucp600(self, lc_section_content: str, ucp600_article: str) -> str:
        """Validates the LC section content against the UCP600 article using the RAG pipeline."""
        query = f"""Given the LC section content: '{lc_section_content}',
        validate it against UCP600 Article: '{ucp600_article}'.
        Explain any discrepancies or confirm compliance.
        Use the retrieved UCP600 document information for validation.
        """
        response = self.query_engine.query(query)
        return response.response

    def validate_isbp745(self, lc_section_content: str, isbp745_section: str) -> str:
        """Validates the LC section content against the ISBP745 section using the RAG pipeline.""" 
        query = f"""Given the LC section content: '{lc_section_content}',
        validate it against ISBP745 Section: '{isbp745_section}'.
        Explain any discrepancies or confirm compliance.
        Use the retrieved ISBP745 document information for validation.
        """
        response = self.query_engine.query(query)
        return response.response

    def consolidate_results(self, validation_results: dict) -> str:
        """Consolidates validation results into a comprehensive report."""
        prompt = f"""Consolidate the following LC validation results into a clear and concise report.
        Highlight any issues or discrepancies found.

        {validation_results}
        """
        response = self.llm.complete(prompt)
        return response.text


class LCSectionParserAgent:
    def __init__(self, llm):
        self.llm = llm

    def parse_lc_sections(self, lc_content: str, mappings: list) -> dict:
        """Parses the LC content based on the provided mappings and extracts relevant sections."""
        parsed_data = {}
        for mapping in mappings:
            lc_section_name = mapping["LC Section"]
            prompt = f"""Extract the content of the '{lc_section_name}' section from the following Letter of Credit:

            {lc_content}

            If the section is not explicitly mentioned, try to infer it from context.
            Return 'N/A' if the section cannot be found or inferred.
            """
            response = self.llm.complete(prompt)
            parsed_data[lc_section_name] = response.text
        return parsed_data

class UCP600ValidationAgent:
    def __init__(self, llm, query_engine):
        self.llm = llm
        self.query_engine = query_engine

    def validate(self, lc_section_content: str, ucp600_article: str) -> str:
        """Validates the LC section content against the UCP600 article using the RAG pipeline."""
        query = f"""Given the LC section content: '{lc_section_content}',
        validate it against UCP600 Article: '{ucp600_article}'.
        Explain any discrepancies or confirm compliance.
        Use the retrieved UCP600 document information for validation.
        """
        response = self.query_engine.query(query)
        return response.response

class ISBP745ValidationAgent:
    def __init__(self, llm, query_engine):
        self.llm = llm
        self.query_engine = query_engine

    def validate(self, lc_section_content: str, isbp745_section: str) -> str:
        """Validates the LC section content against the ISBP745 section using the RAG pipeline.""" 
        query = f"""Given the LC section content: '{lc_section_content}',
        validate it against ISBP745 Section: '{isbp745_section}'.
        Explain any discrepancies or confirm compliance.
        Use the retrieved ISBP745 document information for validation.
        """
        response = self.query_engine.query(query)
        return response.response

class ConsolidationAgent:
    def __init__(self, llm):
        self.llm = llm

    def consolidate(self, validation_results: dict) -> str:
        """Consolidates validation results into a comprehensive report."""
        prompt = f"""Consolidate the following LC validation results into a clear and concise report.
        Highlight any issues or discrepancies found.

        {validation_results}
        """
        response = self.llm.complete(prompt)
        return response.text


