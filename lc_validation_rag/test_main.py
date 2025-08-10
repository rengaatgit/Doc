
import unittest
import os
from unittest.mock import patch, MagicMock

# Adjust the path to import main correctly
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from main import main

class TestLCValidation(unittest.TestCase):

    @patch('main.RAGPipeline')
    @patch('main.OpenAI')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='Test LC Content')
    def test_main_execution(self, mock_open, mock_openai, mock_rag_pipeline):
        # Mock RAGPipeline methods
        mock_rag_instance = MagicMock()
        mock_rag_pipeline.return_value = mock_rag_instance
        mock_rag_instance.load_documents.return_value = []
        mock_rag_instance.create_and_persist_index.return_value = None
        mock_rag_instance.get_query_engine.return_value = MagicMock()

        # Mock OpenAI LLM
        mock_llm_instance = MagicMock()
        mock_openai.return_value = mock_llm_instance

        # Mock LCValidationGraph stream and invoke
        with patch('main.LCValidationGraph') as mock_lc_validation_graph:
            mock_graph_instance = MagicMock()
            mock_lc_validation_graph.return_value = mock_graph_instance
            mock_graph_instance.app.stream.return_value = [{'step1': 'output1'}, {'step2': 'output2'}]
            mock_graph_instance.app.invoke.return_value = {'final_report': 'Mocked Final Report'}

            # Execute the main function
            main()

            # Assertions to check if methods were called as expected
            mock_rag_pipeline.assert_called_once()
            mock_rag_instance.load_documents.assert_called_once()
            mock_rag_instance.create_and_persist_index.assert_called_once_with([])
            mock_rag_instance.get_query_engine.assert_called_once()
            mock_openai.assert_called_once_with(model='gpt-4o')
            mock_lc_validation_graph.assert_called_once_with(mock_llm_instance, mock_rag_instance.get_query_engine.return_value)
            mock_open.assert_called_once_with('./data/sampleLC.txt', 'r')
            mock_graph_instance.app.stream.assert_called_once()
            mock_graph_instance.app.invoke.assert_called_once()

if __name__ == '__main__':
    unittest.main()


