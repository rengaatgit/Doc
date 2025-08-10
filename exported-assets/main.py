
"""
Main LC Validation Application
Entry point for the LC validation system
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any
import pandas as pd

from src.rag.document_processor import DocumentProcessor
from src.rag.vector_database import VectorDatabaseManager
from src.parsers.lc_parser import LCParser
from src.orchestrator import LCValidationOrchestrator


class LCValidationSystem:
    """Main LC validation system class"""

    def __init__(self, config_path: str = "config/settings.json"):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Load environment variables
        self._load_environment()

        # Initialize components
        self.doc_processor = DocumentProcessor(self.config)
        self.vector_db = VectorDatabaseManager(self.config)
        self.lc_parser = LCParser()
        self.orchestrator = LCValidationOrchestrator(self.config, self.vector_db)

        self.initialized = False

    def _load_environment(self):
        """Load environment variables"""
        from dotenv import load_dotenv
        load_dotenv()

        # Override config with environment variables
        self.config["openai_api_key"] = os.getenv("OPENAI_API_KEY", self.config["openai_api_key"])
        self.config["chroma_db_path"] = os.getenv("CHROMA_DB_PATH", self.config["chroma_db_path"])

    async def initialize_system(self, force_rebuild: bool = False):
        """Initialize the system with knowledge base"""
        print("🔧 Initializing LC Validation System...")

        # Check if database already exists
        db_path = Path(self.config["chroma_db_path"])
        if db_path.exists() and not force_rebuild:
            print("📚 Vector database already exists, skipping initialization")
            self.initialized = True
            return

        print("📄 Processing UCP600 and ISBP745 documents...")

        # Process documents (assuming they exist in data folder)
        ucp600_path = "data/UCP600-1.pdf"
        isbp745_path = "data/isbp-745.pdf" 
        mappings_path = "data/mappings.xlsx"

        if not all(Path(p).exists() for p in [ucp600_path, isbp745_path, mappings_path]):
            print("⚠️  Warning: Some data files are missing. Please ensure UCP600, ISBP745, and mappings files are in the data folder.")
            return

        try:
            # Process documents
            ucp600_docs = self.doc_processor.process_ucp600(ucp600_path)
            isbp745_docs = self.doc_processor.process_isbp745(isbp745_path)

            # Load and process mappings
            mappings_df = pd.read_excel(mappings_path, sheet_name=0)
            mappings = self.doc_processor.process_mappings(mappings_df)

            # Chunk documents for better retrieval
            print("✂️  Chunking documents for optimal retrieval...")
            ucp600_chunked = self.doc_processor.chunk_documents(ucp600_docs)
            isbp745_chunked = self.doc_processor.chunk_documents(isbp745_docs)

            # Initialize vector database
            print("🗃️  Initializing vector database...")
            self.vector_db.initialize_database(ucp600_chunked, isbp745_chunked, mappings)

            self.initialized = True
            print("✅ System initialization completed!")

        except Exception as e:
            print(f"❌ System initialization failed: {str(e)}")
            raise

    async def validate_lc_file(self, lc_file_path: str) -> Dict[str, Any]:
        """Validate LC from file"""
        if not self.initialized:
            await self.initialize_system()

        # Read LC file
        with open(lc_file_path, 'r', encoding='utf-8') as f:
            lc_text = f.read()

        return await self.validate_lc_text(lc_text)

    async def validate_lc_text(self, lc_text: str) -> Dict[str, Any]:
        """Validate LC from text content"""
        if not self.initialized:
            await self.initialize_system()

        print("\n📝 Parsing LC document...")
        lc_data = self.lc_parser.parse_lc_document(lc_text)

        print(f"Parsed LC: {lc_data.lc_number}")
        print(f"Issuing Bank: {lc_data.issuing_bank['name']}")
        print(f"Amount: {lc_data.currency} {lc_data.amount}")

        # Validate using orchestrator
        print("\n🔍 Starting validation process...")
        validation_result = await self.orchestrator.validate_lc(lc_data)

        return validation_result

    def save_validation_report(self, validation_result: Dict[str, Any], output_path: str):
        """Save validation report to file"""
        with open(output_path, 'w') as f:
            json.dump(validation_result, f, indent=2, default=str)
        print(f"📄 Validation report saved to: {output_path}")

    def print_validation_summary(self, validation_result: Dict[str, Any]):
        """Print a summary of validation results"""
        print("\n" + "="*60)
        print("📋 LC VALIDATION SUMMARY")
        print("="*60)

        lc_number = validation_result.get("lc_number", "Unknown")
        print(f"LC Number: {lc_number}")

        compliance = validation_result.get("compliance_summary", {})
        overall_compliant = compliance.get("overall_compliant", False)
        confidence_score = compliance.get("confidence_score", 0.0)

        status_emoji = "✅" if overall_compliant else "❌"
        print(f"Overall Status: {status_emoji} {'COMPLIANT' if overall_compliant else 'NON-COMPLIANT'}")
        print(f"Confidence Score: {confidence_score:.2f}")

        compliant_agents = compliance.get("compliant_agents", 0)
        total_agents = compliance.get("total_agents", 0)
        print(f"Compliant Agents: {compliant_agents}/{total_agents}")

        total_issues = validation_result.get("total_issues", 0)
        total_recommendations = validation_result.get("total_recommendations", 0)
        print(f"Issues Found: {total_issues}")
        print(f"Recommendations: {total_recommendations}")

        print("\nAgent Results:")
        agents_summary = validation_result.get("agents_summary", {})
        for agent_name, summary in agents_summary.items():
            status = "✅" if summary.get("compliant", False) else "❌"
            confidence = summary.get("confidence", 0.0)
            issues = summary.get("issues_count", 0)
            print(f"  {status} {agent_name}: {confidence:.2f} confidence, {issues} issues")

        print("="*60)


async def main():
    """Main application entry point"""
    print("🏦 LC Validation System")
    print("=" * 40)

    # Initialize system
    system = LCValidationSystem()

    try:
        # Initialize system (will skip if already done)
        await system.initialize_system()

        # Validate sample LC
        sample_lc_path = "sampleLC.txt"
        if Path(sample_lc_path).exists():
            print(f"\n🔍 Validating sample LC: {sample_lc_path}")
            result = await system.validate_lc_file(sample_lc_path)

            # Print summary
            system.print_validation_summary(result)

            # Save detailed report
            output_path = f"validation_report_{result['lc_number']}_{result['validation_timestamp'][:10]}.json"
            system.save_validation_report(result, output_path)

        else:
            print(f"❌ Sample LC file not found: {sample_lc_path}")

    except Exception as e:
        print(f"❌ Application error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
