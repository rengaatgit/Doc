
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator

from agents import LCSectionParserAgent, UCP600ValidationAgent, ISBP745ValidationAgent, ConsolidationAgent
from rag_pipeline import RAGPipeline
from mappings import mappings_data

class AgentState(TypedDict):
    lc_content: str
    parsed_lc_sections: dict
    validation_results: Annotated[List[dict], operator.add]

class LCValidationGraph:
    def __init__(self, llm, query_engine):
        self.lc_parser = LCSectionParserAgent(llm)
        self.ucp600_validator = UCP600ValidationAgent(llm, query_engine)
        self.isbp745_validator = ISBP745ValidationAgent(llm, query_engine)
        self.consolidation_agent = ConsolidationAgent(llm)
        self.mappings = mappings_data

        self.graph = StateGraph(AgentState)

        self.graph.add_node("parse_lc", self.parse_lc_sections)
        self.graph.add_node("validate_ucp600", self.validate_ucp600_sections)
        self.graph.add_node("validate_isbp745", self.validate_isbp745_sections)
        self.graph.add_node("consolidate_results", self.consolidate_validation_results)

        self.graph.set_entry_point("parse_lc")

        self.graph.add_edge("parse_lc", "validate_ucp600")
        self.graph.add_edge("parse_lc", "validate_isbp745")

        self.graph.add_conditional_edges(
            "validate_ucp600",
            lambda state: "consolidate_results", # Always go to consolidate after UCP600 validation
            {"consolidate_results": "consolidate_results"}
        )
        self.graph.add_conditional_edges(
            "validate_isbp745",
            lambda state: "consolidate_results", # Always go to consolidate after ISBP745 validation
            {"consolidate_results": "consolidate_results"}
        )

        self.graph.add_edge("consolidate_results", END)

        self.app = self.graph.compile()

    def parse_lc_sections(self, state: AgentState):
        print("---Parsing LC Sections---")
        lc_content = state["lc_content"]
        parsed_sections = self.lc_parser.parse_lc_sections(lc_content, self.mappings)
        return {"parsed_lc_sections": parsed_sections, "validation_results": []}

    def validate_ucp600_sections(self, state: AgentState):
        print("---Validating UCP600 Sections---")
        parsed_lc_sections = state["parsed_lc_sections"]
        validation_results = state["validation_results"]

        for mapping in self.mappings:
            lc_section_name = mapping["LC Section"]
            ucp600_article = mapping["UCP600 Article"]

            if ucp600_article and ucp600_article != "Not specifically covered" and ucp600_article != "N/A":
                lc_section_content = parsed_lc_sections.get(lc_section_name, "N/A")
                result = self.ucp600_validator.validate(lc_section_content, ucp600_article)
                validation_results.append({
                    "section": lc_section_name,
                    "rule_type": "UCP600",
                    "rule": ucp600_article,
                    "validation_output": result
                })
        return {"validation_results": validation_results}

    def validate_isbp745_sections(self, state: AgentState):
        print("---Validating ISBP745 Sections---")
        parsed_lc_sections = state["parsed_lc_sections"]
        validation_results = state["validation_results"]

        for mapping in self.mappings:
            lc_section_name = mapping["LC Section"]
            isbp745_section = mapping["ISBP745 Section"]

            if isbp745_section and isbp745_section != "N/A":
                lc_section_content = parsed_lc_sections.get(lc_section_name, "N/A")
                result = self.isbp745_validator.validate(lc_section_content, isbp745_section)
                validation_results.append({
                    "section": lc_section_name,
                    "rule_type": "ISBP745",
                    "rule": isbp745_section,
                    "validation_output": result
                })
        return {"validation_results": validation_results}

    def consolidate_validation_results(self, state: AgentState):
        print("---Consolidating Results---")
        validation_results = state["validation_results"]
        final_report = self.consolidation_agent.consolidate(validation_results)
        return {"final_report": final_report}


if __name__ == "__main__":
    # Example usage:
    from llama_index.llms.openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()

    llm = OpenAI(model="gpt-4o")
    rag_pipeline = RAGPipeline()
    # Ensure documents are loaded and index is created/persisted before running the graph
    docs = rag_pipeline.load_documents()
    rag_pipeline.create_and_persist_index(docs)
    query_engine = rag_pipeline.get_query_engine()

    graph = LCValidationGraph(llm, query_engine)

    with open("../data/sampleLC.txt", "r") as f:
        sample_lc_content = f.read()

    initial_state = {"lc_content": sample_lc_content, "parsed_lc_sections": {}, "validation_results": []}
    for s in graph.app.stream(initial_state):
        print(s)

    # To get the final state:
    final_state = graph.app.invoke(initial_state)
    print("\nFinal Report:")
    print(final_state.get("final_report"))


