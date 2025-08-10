
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from chromadb import PersistentClient

class RAGPipeline:
    def __init__(self, data_dir="../data", persist_dir="./chroma_db"):
        self.data_dir = data_dir
        self.persist_dir = persist_dir
        self.client = PersistentClient(path=self.persist_dir)
        Settings.embed_model = OpenAIEmbedding()
        Settings.llm = OpenAI(model="gpt-4o")

    def load_documents(self):
        print(f"Loading documents from {self.data_dir}")
        reader = SimpleDirectoryReader(self.data_dir)
        documents = reader.load_data()
        print(f"Loaded {len(documents)} documents.")
        return documents

    def create_and_persist_index(self, documents):
        print("Creating and persisting index...")
        index = VectorStoreIndex.from_documents(documents, service_context=Settings)
        index.storage_context.persist(persist_dir=self.persist_dir)
        print("Index created and persisted.")
        return index

    def get_query_engine(self):
        print("Loading index from persistence and creating query engine...")
        # In a real scenario, you'd load the index from the persisted directory
        # For this example, we'll re-create it if not already loaded
        documents = self.load_documents()
        index = self.create_and_persist_index(documents)
        query_engine = index.as_query_engine()
        print("Query engine ready.")
        return query_engine

if __name__ == "__main__":
    # This part is for testing the RAG pipeline independently
    rag_pipeline = RAGPipeline()
    docs = rag_pipeline.load_documents()
    index = rag_pipeline.create_and_persist_index(docs)
    query_engine = rag_pipeline.get_query_engine()

    # Example query
    response = query_engine.query("What is UCP600 Article 1 about?")
    print(response)


