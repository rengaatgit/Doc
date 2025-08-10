# Create the RAG components - Document Processor and Vector Database
doc_processor_code = '''
"""
Document Processor for UCP600 and ISBP745
Processes PDF documents and creates embeddings for vector storage
"""

import os
import json
import re
from typing import List, Dict, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
import pandas as pd


class DocumentProcessor:
    def __init__(self, config: Dict):
        self.config = config
        self.embeddings = OpenAIEmbeddings(
            model=config["embedding_model"],
            api_key=config["openai_api_key"]
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
            separators=["\\n\\n", "\\n", ".", " "]
        )
    
    def process_ucp600(self, pdf_path: str) -> List[Dict]:
        """Process UCP600 PDF and extract articles with metadata"""
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        processed_docs = []
        current_article = None
        
        for doc in documents:
            text = doc.page_content
            
            # Extract articles using regex pattern
            article_pattern = r"Article (\\d+)\\s+([^\\n]+)"
            articles = re.finditer(article_pattern, text)
            
            for match in articles:
                article_num = match.group(1)
                article_title = match.group(2).strip()
                
                # Extract article content (simple approach)
                start_pos = match.end()
                next_article = re.search(r"Article \\d+", text[start_pos:])
                end_pos = next_article.start() + start_pos if next_article else len(text)
                
                article_content = text[start_pos:end_pos].strip()
                
                processed_docs.append({
                    "source": "UCP600",
                    "article_number": article_num,
                    "article_title": article_title,
                    "content": article_content,
                    "metadata": {
                        "type": "article",
                        "document": "UCP600",
                        "article": f"Article {article_num}",
                        "page": doc.metadata.get("page", 0)
                    }
                })
        
        return processed_docs
    
    def process_isbp745(self, pdf_path: str) -> List[Dict]:
        """Process ISBP745 PDF and extract paragraphs with metadata"""
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        processed_docs = []
        
        for doc in documents:
            text = doc.page_content
            
            # Extract ISBP paragraphs using regex pattern
            paragraph_pattern = r"([A-Z]\\d+)\\)\\s*([^\\n]+)"
            paragraphs = re.finditer(paragraph_pattern, text)
            
            for match in paragraphs:
                para_num = match.group(1)
                para_title = match.group(2).strip()
                
                # Extract paragraph content
                start_pos = match.end()
                next_para = re.search(r"[A-Z]\\d+\\)", text[start_pos:])
                end_pos = next_para.start() + start_pos if next_para else len(text)
                
                para_content = text[start_pos:end_pos].strip()
                
                processed_docs.append({
                    "source": "ISBP745",
                    "paragraph_number": para_num,
                    "paragraph_title": para_title,
                    "content": para_content,
                    "metadata": {
                        "type": "paragraph",
                        "document": "ISBP745",
                        "paragraph": para_num,
                        "page": doc.metadata.get("page", 0)
                    }
                })
        
        return processed_docs
    
    def process_mappings(self, mappings_df: pd.DataFrame) -> List[Dict]:
        """Process mappings data for quick reference"""
        mappings = []
        
        for _, row in mappings_df.iterrows():
            mappings.append({
                "lc_section": row["LC Section"],
                "ucp600_article": row["UCP600 Article"],
                "isbp745_section": row["ISBP745 Section"],
                "remarks": row["Remarks"],
                "metadata": {
                    "type": "mapping",
                    "source": "mappings"
                }
            })
        
        return mappings
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Split documents into smaller chunks for better retrieval"""
        chunked_docs = []
        
        for doc in documents:
            chunks = self.text_splitter.split_text(doc["content"])
            
            for i, chunk in enumerate(chunks):
                chunked_doc = doc.copy()
                chunked_doc["content"] = chunk
                chunked_doc["chunk_id"] = i
                chunked_doc["metadata"]["chunk"] = i
                chunked_docs.append(chunked_doc)
        
        return chunked_docs
'''

# Create Vector Database Manager
vector_db_code = '''
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
'''

# Save the files
with open('lc_validation_system/src/rag/document_processor.py', 'w') as f:
    f.write(doc_processor_code)

with open('lc_validation_system/src/rag/vector_database.py', 'w') as f:
    f.write(vector_db_code)

print("RAG components created:")
print("- src/rag/document_processor.py")
print("- src/rag/vector_database.py")