
"""
Vector Database Manager using ChromaDB
Manages embeddings and similarity search for UCP600/ISBP745 content
"""

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
import json
import uuid


class VectorDatabaseManager:
    def __init__(self, config: Dict):
        self.config = config
        self.client = chromadb.PersistentClient(path=config["chroma_db_path"])

        # Initialize embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=config["openai_api_key"],
            model_name=config["embedding_model"]
        )

        # Create collections
        self.ucp600_collection = self.client.get_or_create_collection(
            name="ucp600_rules",
            embedding_function=self.embedding_function,
            metadata={"description": "UCP600 Articles and Rules"}
        )

        self.isbp745_collection = self.client.get_or_create_collection(
            name="isbp745_practices",
            embedding_function=self.embedding_function,
            metadata={"description": "ISBP745 Banking Practices"}
        )

        self.mappings_collection = self.client.get_or_create_collection(
            name="lc_mappings",
            embedding_function=self.embedding_function,
            metadata={"description": "LC to UCP600/ISBP745 Mappings"}
        )

    def add_documents_to_collection(self, documents: List[Dict], collection_name: str):
        """Add processed documents to specified collection"""
        collection = getattr(self, f"{collection_name}_collection")

        ids = [str(uuid.uuid4()) for _ in documents]
        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]

        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

    def search_similar_content(
        self, 
        query: str, 
        collection_name: str, 
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar content in specified collection"""
        collection = getattr(self, f"{collection_name}_collection")

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filters
        )

        search_results = []
        for i in range(len(results["ids"][0])):
            search_results.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        return search_results

    def get_relevant_rules(self, lc_section: str, query_text: str) -> Dict[str, List[Dict]]:
        """Get relevant rules from both UCP600 and ISBP745 for specific LC section"""
        results = {
            "ucp600_rules": self.search_similar_content(
                query=query_text,
                collection_name="ucp600",
                top_k=self.config["top_k_retrieval"]
            ),
            "isbp745_practices": self.search_similar_content(
                query=query_text,
                collection_name="isbp745",
                top_k=self.config["top_k_retrieval"]
            ),
            "relevant_mappings": self.search_similar_content(
                query=lc_section,
                collection_name="lc_mappings",
                top_k=3
            )
        }

        return results

    def initialize_database(self, ucp600_docs: List[Dict], isbp745_docs: List[Dict], mappings: List[Dict]):
        """Initialize the vector database with processed documents"""
        print("Adding UCP600 documents to vector database...")
        self.add_documents_to_collection(ucp600_docs, "ucp600")

        print("Adding ISBP745 documents to vector database...")
        self.add_documents_to_collection(isbp745_docs, "isbp745")

        print("Adding mappings to vector database...")
        self.add_documents_to_collection(mappings, "lc_mappings")

        print("Vector database initialization completed!")
