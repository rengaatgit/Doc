# Create comprehensive README.md

readme_content = '''
# LC Validation System

A comprehensive AI-powered system for validating Letters of Credit (LC) against UCP600 rules and ISBP745 banking practices using Retrieval Augmented Generation (RAG) and multi-agent architecture.

## 🏗️ Architecture

The system uses a sophisticated multi-agent architecture with the following components:

### Core Components
- **RAG Pipeline**: Processes UCP600 and ISBP745 documents for knowledge retrieval
- **Vector Database**: ChromaDB for efficient similarity search
- **LC Parser**: Extracts structured data from LC documents
- **Validation Agents**: Specialized agents for different validation aspects
- **LangGraph Orchestrator**: Coordinates parallel agent execution

### Validation Agents
1. **Credit Type Agent**: Validates LC structure and irrevocability
2. **Date Validation Agent**: Checks all date requirements and sequences
3. **Amount Validation Agent**: Validates currency and amount specifications
4. **Document Requirements Agent**: Verifies document requirements
5. **Shipping Terms Agent**: Validates shipping and transport terms
6. **Bank Details Agent**: Checks bank and party information

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- UCP600 and ISBP745 documents (PDFs)

### Installation

1. **Clone/Extract the system**
```bash
# If you have the zip file, extract it
unzip lc_validation_system.zip
cd lc_validation_system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup environment**
```bash
# Copy and configure environment file
cp .env.template .env

# Edit .env file and add your OpenAI API key
# OPENAI_API_KEY=your_openai_api_key_here
```

4. **Initialize data**
```bash
# Setup data directory and files
python init_data.py
```

5. **Run the system**
```bash
# Validate the sample LC
python main.py

# Or run example usage
python example_usage.py
```

## 📊 System Architecture

### Logical Architecture
```mermaid
graph TD
    A[LC Document Input] --> B[LC Parser]
    B --> C[Validation Router]
    C --> D[Agent Orchestrator - LangGraph]
    
    D --> E1[Credit Type Agent]
    D --> E2[Date Validation Agent]
    D --> E3[Bank Details Agent]
    D --> E4[Amount Validation Agent]
    D --> E5[Document Requirements Agent]
    D --> E6[Shipping Terms Agent]
    
    E1 --> F[RAG Knowledge Base]
    E2 --> F
    E3 --> F
    E4 --> F
    E5 --> F
    E6 --> F
    
    F --> G1[UCP600 Vector Store]
    F --> G2[ISBP745 Vector Store]
    F --> G3[Mappings Store]
    
    E1 --> H[Results Aggregator]
    E2 --> H
    E3 --> H
    E4 --> H
    E5 --> H
    E6 --> H
    
    H --> I[Validation Report Generator]
    I --> J[Final Validation Report]
```

### Data Flow
```mermaid
graph TD
    A[Input LC Document] --> B[Text Preprocessing]
    B --> C[LC Section Extraction]
    C --> D[Mapping Resolution]
    
    D --> E[Parallel Agent Processing]
    
    E --> F1[Agent 1: Query Vector DB]
    E --> F2[Agent 2: Query Vector DB]  
    E --> F3[Agent 3: Query Vector DB]
    E --> F4[Agent N: Query Vector DB]
    
    F1 --> G1[UCP600 Rules Retrieval]
    F2 --> G2[ISBP745 Guidelines Retrieval]
    F3 --> G3[Compliance Checking]
    F4 --> G4[Validation Logic]
    
    G1 --> H[LLM Analysis]
    G2 --> H
    G3 --> H
    G4 --> H
    
    H --> I[Validation Results]
    I --> J[Aggregation & Scoring]
    J --> K[Report Generation]
    K --> L[JSON/PDF Output]
```

## 🔧 Configuration

### settings.json
```json
{
  "openai_api_key": "your_key_here",
  "model_name": "gpt-4o",
  "embedding_model": "text-embedding-3-small",
  "chroma_db_path": "./data/chroma_db",
  "max_tokens": 4000,
  "temperature": 0.1,
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "top_k_retrieval": 5,
  "validation_confidence_threshold": 0.8,
  "parallel_agent_limit": 8
}
```

## 📖 Usage Examples

### Basic Validation
```python
import asyncio
from main import LCValidationSystem

async def validate_lc():
    system = LCValidationSystem()
    
    # Validate from file
    result = await system.validate_lc_file("sample_lc.txt")
    
    # Print summary
    system.print_validation_summary(result)
    
    # Save report
    system.save_validation_report(result, "validation_report.json")

asyncio.run(validate_lc())
```

### Batch Validation
```python
async def batch_validate():
    system = LCValidationSystem()
    lc_files = ["lc1.txt", "lc2.txt", "lc3.txt"]
    
    results = []
    for lc_file in lc_files:
        result = await system.validate_lc_file(lc_file)
        results.append(result)
    
    return results
```

### Custom Agent Development
```python
from src.agents.base_agent import BaseValidationAgent

class CustomValidationAgent(BaseValidationAgent):
    def get_validation_focus(self):
        return ["custom_section"]
    
    def create_validation_prompt(self, lc_data, context):
        return f"Validate custom aspect: {lc_data.custom_field}"
```

## 📁 Project Structure

```
lc_validation_system/
├── main.py                     # Main application entry point
├── init_data.py               # Data initialization script
├── example_usage.py           # Example usage demonstrations
├── requirements.txt           # Python dependencies
├── config/
│   └── settings.json         # System configuration
├── src/
│   ├── agents/               # Validation agents
│   │   ├── base_agent.py     # Base agent class
│   │   ├── credit_type_agent.py
│   │   ├── date_validation_agent.py
│   │   ├── amount_validation_agent.py
│   │   ├── document_requirements_agent.py
│   │   ├── shipping_terms_agent.py
│   │   └── bank_details_agent.py
│   ├── rag/                  # RAG components
│   │   ├── document_processor.py
│   │   └── vector_database.py
│   ├── parsers/              # Document parsers
│   │   └── lc_parser.py
│   └── orchestrator.py       # LangGraph orchestrator
├── data/                     # Data files (populated by init_data.py)
├── tests/                    # Test files
├── docs/                     # Documentation
│   ├── logical_architecture.md
│   └── data_flow.md
└── README.md                 # This file
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

Or run specific tests:
```bash
python tests/test_lc_parser.py
```

## 📊 Validation Output

The system generates comprehensive validation reports in JSON format:

```json
{
  "lc_number": "LC2025-0001",
  "validation_timestamp": "2025-01-15T10:30:00",
  "overall_status": "completed",
  "compliance_summary": {
    "overall_compliant": true,
    "compliant_agents": 6,
    "total_agents": 6,
    "confidence_score": 0.87
  },
  "agents_summary": {
    "credit_type": {
      "compliant": true,
      "confidence": 0.95,
      "issues_count": 0,
      "recommendations_count": 1
    }
  },
  "total_issues": 2,
  "total_recommendations": 5,
  "detailed_results": { ... }
}
```

## 🔍 Validation Criteria

The system validates LCs against:

### UCP600 Articles
- Article 1: Application of UCP
- Article 2: Definitions
- Article 3: Interpretations
- Article 6: Availability, Expiry Date and Place for Presentation
- Article 7: Issuing Bank Undertaking
- Article 14: Standard for Examination of Documents
- Article 18: Commercial Invoice
- Article 20: Bill of Lading
- Article 28: Insurance Document and Coverage
- Article 30: Tolerance in Credit Amount
- Article 31: Partial Drawings or Shipments

### ISBP745 Practices
- Section A: General Principles (A1-A41)
- Section B: Drafts and Calculation of Maturity Date (B1-B18)
- Section C: Invoices (C1-C15)
- Section E: Bill of Lading (E1-E28)
- Section K: Insurance Document and Coverage (K1-K23)
- Section M: Packing List (M1-M6)

## 🛠️ Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   - Ensure your API key is correctly set in `.env` file
   - Verify the key has sufficient credits

2. **Vector Database Initialization Fails**
   - Check that UCP600 and ISBP745 PDF files are in `data/` directory
   - Ensure you have write permissions for the database directory

3. **Agent Validation Errors**
   - Check network connectivity for OpenAI API calls
   - Verify document parsing completed successfully

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Considerations

- API keys are stored in environment variables
- No sensitive LC data is logged
- Vector database is stored locally
- All processing happens on your infrastructure

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- International Chamber of Commerce (ICC) for UCP600 and ISBP745 standards
- LangChain and LangGraph for AI orchestration
- ChromaDB for vector storage
- OpenAI for language model capabilities

## 📞 Support

For support or questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the example usage scripts

---

**Note**: This system is designed for educational and professional development purposes. Always consult with qualified trade finance professionals for production use cases.
'''

# Create a simple test file
test_file_content = '''
"""
Simple test file for LC Validation System
"""

import unittest
import asyncio
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parsers.lc_parser import LCParser, LCData


class TestLCParser(unittest.TestCase):
    """Test cases for LC Parser"""
    
    def setUp(self):
        self.parser = LCParser()
        self.sample_lc_text = """
        IRREVOCABLE DOCUMENTARY LETTER OF CREDIT
        Subject to UCP 600
        
        LC Number: LC2025-TEST
        Date of Issue: January 15, 2025
        Amount: USD 100,000
        Expiry Date: March 15, 2025
        
        Issuing Bank:
        Test Bank Ltd.
        123 Test Street
        
        Applicant:
        Test Importer Inc.
        456 Import Avenue
        
        Beneficiary:
        Test Exporter S.A.
        789 Export Road
        
        Available by sight draft
        Port of Loading: Test Port A
        Port of Discharge: Test Port B
        Goods: Test Goods, 1000 units
        
        Partial Shipments: Allowed
        Transshipment: Not Allowed
        """
    
    def test_parse_basic_fields(self):
        """Test parsing of basic LC fields"""
        lc_data = self.parser.parse_lc_document(self.sample_lc_text)
        
        self.assertEqual(lc_data.lc_number, "LC2025-TEST")
        self.assertEqual(lc_data.currency, "USD")
        self.assertEqual(lc_data.amount, "100,000")
        self.assertEqual(lc_data.port_of_loading, "Test Port A")
        self.assertEqual(lc_data.port_of_discharge, "Test Port B")
    
    def test_parse_parties(self):
        """Test parsing of party information"""
        lc_data = self.parser.parse_lc_document(self.sample_lc_text)
        
        self.assertIn("Test Bank Ltd.", lc_data.issuing_bank['name'])
        self.assertIn("Test Importer Inc.", lc_data.applicant['name'])
        self.assertIn("Test Exporter S.A.", lc_data.beneficiary['name'])
    
    def test_parse_boolean_fields(self):
        """Test parsing of boolean fields"""
        lc_data = self.parser.parse_lc_document(self.sample_lc_text)
        
        self.assertTrue(lc_data.partial_shipments)
        self.assertFalse(lc_data.transshipment_allowed)
    
    def test_lc_data_structure(self):
        """Test that LCData structure is properly created"""
        lc_data = self.parser.parse_lc_document(self.sample_lc_text)
        
        self.assertIsInstance(lc_data, LCData)
        self.assertIsInstance(lc_data.documents_required, list)
        self.assertIsInstance(lc_data.special_conditions, list)


class TestSystemIntegration(unittest.TestCase):
    """Integration tests for the system components"""
    
    def test_config_loading(self):
        """Test that configuration can be loaded"""
        from main import LCValidationSystem
        
        # Test with default config path
        try:
            system = LCValidationSystem()
            self.assertIsNotNone(system.config)
        except FileNotFoundError:
            # Config file might not exist in test environment
            self.skipTest("Config file not found")
    
    @patch('main.LCValidationSystem._load_environment')
    def test_system_initialization(self, mock_load_env):
        """Test system initialization without actual files"""
        from main import LCValidationSystem
        
        mock_load_env.return_value = None
        
        # Mock config
        with patch('builtins.open'), patch('json.load') as mock_json:
            mock_json.return_value = {
                "openai_api_key": "test_key",
                "model_name": "gpt-4o",
                "embedding_model": "text-embedding-3-small",
                "chroma_db_path": "./test_db",
                "temperature": 0.1,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "top_k_retrieval": 5
            }
            
            system = LCValidationSystem()
            self.assertIsNotNone(system.doc_processor)
            self.assertIsNotNone(system.lc_parser)


def run_async_test(coro):
    """Helper function to run async tests"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == '__main__':
    # Run the tests
    unittest.main()
'''

# Save README.md and test file
with open('lc_validation_system/README.md', 'w') as f:
    f.write(readme_content)

with open('lc_validation_system/tests/test_basic.py', 'w') as f:
    f.write(test_file_content)

print("Final files created:")
print("- README.md")
print("- tests/test_basic.py")