
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
            separators=["\n\n", "\n", ".", " "]
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
            article_pattern = r"Article (\d+)\s+([^\n]+)"
            articles = re.finditer(article_pattern, text)

            for match in articles:
                article_num = match.group(1)
                article_title = match.group(2).strip()

                # Extract article content (simple approach)
                start_pos = match.end()
                next_article = re.search(r"Article \d+", text[start_pos:])
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
            paragraph_pattern = r"([A-Z]\d+)\)\s*([^\n]+)"
            paragraphs = re.finditer(paragraph_pattern, text)

            for match in paragraphs:
                para_num = match.group(1)
                para_title = match.group(2).strip()

                # Extract paragraph content
                start_pos = match.end()
                next_para = re.search(r"[A-Z]\d+\)", text[start_pos:])
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
