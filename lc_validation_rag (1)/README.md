
# LC Validation RAG Pipeline (Prototype)

This repository contains a prototype Retrieval-Augmented-Generation (RAG) pipeline and an **agent-based** validator
for verifying a Letter of Credit (LC) against relevant articles of **UCP 600** and paragraphs of **ISBP 745**.

**Stack (suggested):**
- Python 3.10+
- langgraph (or simple agent runner)
- llamaindex (for RAG ingestion)
- chroma (ChromaDB) as vector store
- OpenAI / gpt4o or other LLM endpoint
- embedding model of your choice (instruction-tuned or text-embedding-3-small)

> This ZIP contains a runnable *prototype* that does **not** call external APIs. It provides:
> - rule-based validation agents that run in parallel (asyncio)
> - stubs/placeholders where RAG components would be integrated
> - mermaid diagrams for architecture & data flow
> - mapping file (mapping.json) derived from the provided mappings.png
> - the supplied sampleLC.txt for testing

## How to use

1. Extract the zip.
2. Create a Python virtualenv and install any dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt  # optional; for real deployment only
   ```
3. Review `rag_stubs.py` and configure:
   - Embedder
   - Vector DB (Chroma) connection
   - LLM calls (gpt4o / OpenAI / other)
4. Run the prototype:
   ```bash
   python main.py --lc-file sampleLC.txt --mapping-file mapping.json
   ```
5. Output: `report_*.json` (validation summary) and `report_*_human.md` (human-readable summary).

