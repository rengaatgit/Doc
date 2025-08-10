
import os
from dotenv import load_dotenv

from src.rag_pipeline import RAGPipeline
from src.agent_graph import LCValidationGraph
from llama_index.llms.openai import OpenAI

def main():
    load_dotenv()

    # Initialize RAG Pipeline
    rag_pipeline = RAGPipeline(data_dir="./data", persist_dir="./chroma_db")
    docs = rag_pipeline.load_documents()
    rag_pipeline.create_and_persist_index(docs)
    query_engine = rag_pipeline.get_query_engine()

    # Initialize LLM
    llm = OpenAI(model="gpt-4o")

    # Initialize and run the LC Validation Graph
    graph = LCValidationGraph(llm, query_engine)

    # Load sample LC content
    lc_file_path = "./data/sampleLC.txt"
    if not os.path.exists(lc_file_path):
        print(f"Error: Sample LC file not found at {lc_file_path}")
        return

    with open(lc_file_path, "r") as f:
        sample_lc_content = f.read()

    initial_state = {"lc_content": sample_lc_content, "parsed_lc_sections": {}, "validation_results": []}

    print("\nStarting LC Validation Process...")
    for s in graph.app.stream(initial_state):
        print(s)

    final_state = graph.app.invoke(initial_state)
    print("\nFinal Validation Report:")
    print(final_state.get("final_report"))

if __name__ == "__main__":
    main()


