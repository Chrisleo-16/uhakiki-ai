"""
pytest configuration for UhakikiAI backend tests
"""

import sys
import os
import unittest.mock as mock

# Add the backend folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Mock torch to avoid GPU requirements
mock_torch = mock.patch("torch.cuda.is_available", return_value=False)
mock_torch.start()

# Mock PIL to avoid image processing requirements
mock_pil = mock.patch("PIL.Image.open")
mock_pil.start()

# Mock external dependencies that might not be available
mock_langchain = mock.patch.dict('sys.modules', {
    'langchain_milvus': mock.MagicMock(),
    'langchain_huggingface': mock.MagicMock(),
    'pymilvus': mock.MagicMock(),
    'crewai': mock.MagicMock(),
    'transformers': mock.MagicMock(),
})
mock_langchain.start()
