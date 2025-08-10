
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
