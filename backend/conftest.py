"""
pytest configuration for UhakikiAI backend tests
"""

import sys
import os
import unittest.mock as mock

# Add the backend folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Mock torch to avoid GPU requirements and scipy conflicts
mock_torch = mock.patch("torch.cuda.is_available", return_value=False)
mock_torch.start()

# Mock torch.Tensor to prevent scipy conflicts
mock_tensor = mock.patch("torch.Tensor", mock.MagicMock())
mock_tensor.start()

# Mock torch module completely to prevent scipy conflicts
mock_torch_module = mock.patch.dict('sys.modules', {
    'torch': mock.MagicMock(),
    'torch.nn': mock.MagicMock(),
    'torch.nn.functional': mock.MagicMock(),
    'torchvision': mock.MagicMock(),
    'torchvision.transforms': mock.MagicMock(),
    'torch.device': mock.MagicMock(return_value='cpu'),
})

# Create a proper mock for RADAutoencoder
mock_rad_autoencoder = mock.MagicMock()
mock_rad_autoencoder.to = mock.MagicMock(return_value=mock_rad_autoencoder)
mock_rad_autoencoder.load_state_dict = mock.MagicMock()
mock_rad_autoencoder.eval = mock.MagicMock()

# Add the mock to sys.modules
sys.modules['app.logic.rad_model'] = mock.MagicMock()
sys.modules['app.logic.rad_model'].RADAutoencoder = mock.MagicMock(return_value=mock_rad_autoencoder)

mock_torch_module.start()

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
    'sklearn': mock.MagicMock(),
    'sklearn.preprocessing': mock.MagicMock(),
    'sklearn.metrics': mock.MagicMock(),
    'sklearn.metrics.pairwise': mock.MagicMock(),
    'sklearn.ensemble': mock.MagicMock(),
    'sklearn.ensemble.IsolationForest': mock.MagicMock(),
    'scipy': mock.MagicMock(),
    'scipy.stats': mock.MagicMock(),
    'scipy.signal': mock.MagicMock(),
    'scipy.io': mock.MagicMock(),
    'scipy.spatial': mock.MagicMock(),
    'scipy.spatial.distance': mock.MagicMock(),
    'scipy.ndimage': mock.MagicMock(),
    'scipy.spatial.distance': mock.MagicMock(),
    'cv2': mock.MagicMock(),
    'numpy': mock.MagicMock(__version__='1.24.0'),
    'pandas': mock.MagicMock(),
    'pandas.compat': mock.MagicMock(),
    'pandas.compat.numpy': mock.MagicMock(),
    'pandas.compat.numpy.is_numpy_dev': False,
    'PIL': mock.MagicMock(),
    'PIL.Image': mock.MagicMock(),
    'PIL.ImageChops': mock.MagicMock(),
    'pytesseract': mock.MagicMock(),
    'librosa': mock.MagicMock(),
    'librosa.feature': mock.MagicMock(),
    'librosa.beat': mock.MagicMock(),
})
mock_langchain.start()
