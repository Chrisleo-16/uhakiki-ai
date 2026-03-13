#!/usr/bin/env python3
"""
Test Pipeline for Uhakiki-AI Document Verification
Tests the complete pipeline with both direct model access and API calls.

Usage:
    python test_pipeline.py --image path/to/id.jpg --api
    python test_pipeline.py --image path/to/id.jpg --direct
    python test_pipeline.py --image path/to/id.jpg
"""

import os
import sys
import argparse
import requests
import json
import torch
import numpy as np
from pathlib import Path
from PIL import Image

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


def setup_model():
    """Setup the RAD model for direct testing."""
    try:
        from models.model_loader import ModelManager
        model_manager = ModelManager()
        model = model_manager.load_rad_autoencoder()
        print("✅ RAD model loaded successfully")
        return model, model_manager
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None, None


def preprocess_image(image_path: Path, model_manager=None) -> torch.Tensor:
    """
    Preprocess image for the RAD model.
    The model expects a tensor shaped [1, channels, 224, 224].
    """
    try:
        # Model expects 1-channel grayscale (from training output: "in_channels": 1)
        image = Image.open(image_path).convert('L')  # Convert to grayscale
        print(f"📷 Original image size: {image.size}")

        image = image.resize((224, 224))
        print(f"📷 Resized to: {image.size}")
        print(f"📷 Converted to grayscale (1-channel)")

        image_array = np.array(image) / 255.0
        image_tensor = torch.from_numpy(image_array).float()
        
        # For 1-channel input: [224, 224] -> [1, 224, 224]
        image_tensor = image_tensor.unsqueeze(0)
        
        # Add batch dimension: [1, 224, 224] -> [1, 1, 224, 224]
        image_tensor = image_tensor.unsqueeze(0)
        
        print(f"📷 Final tensor shape: {image_tensor.shape}")
        return image_tensor
    except Exception as e:
        print(f"❌ Error preprocessing image: {e}")
        return None


def test_direct_model(image_path: Path, model, model_manager):
    """Test the model directly without API."""
    try:
        print("\n🔍 Testing Direct Model Access")
        print("=" * 50)
        
        # Preprocess image
        image_tensor = preprocess_image(image_path, model_manager)
        if image_tensor is None:
            return False
            
        # Get prediction
        mse_score, is_forged = model_manager.predict_document_authenticity(image_tensor)
        
        print(f"📊 Analysis Results:")
        print(f"   - MSE Score: {mse_score:.6f}")
        print(f"   - Is Forged: {is_forged}")
        print(f"   - Is Authentic: {not is_forged}")
        print(f"   - Confidence: {'High' if abs(mse_score - 0.025) > 0.01 else 'Medium'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct model test failed: {e}")
        return False


def test_api_call(image_path: Path):
    """Test the API endpoint."""
    try:
        print("\n🌐 Testing API Endpoint")
        print("=" * 50)
        
        # Start the server first
        print("🚀 Starting server...")
        import subprocess
        import time
        
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "backend.main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for server to start
        time.sleep(3)
        
        try:
            # Test health endpoint
            health_response = requests.get("http://localhost:8000/health", timeout=5)
            if health_response.status_code == 200:
                print("✅ Server is running")
            else:
                print(f"⚠️ Server health check: {health_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            server_process.terminate()
            return False
        
        # Prepare image for upload
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            data = {
                'document_type': 'national_id',
                'country': 'kenya'
            }
            
            # Call the API
            response = requests.post(
                "http://localhost:8000/api/v1/documents/scan",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 API Analysis Results:")
            print(f"   - Document Type: {result.get('document_type', 'N/A')}")
            print(f"   - Authenticity: {result.get('authenticity', 'N/A')}")
            print(f"   - Confidence: {result.get('confidence', 'N/A')}")
            print(f"   - Risk Score: {result.get('risk_score', 'N/A')}")
            print(f"   - Processing Time: {result.get('processing_time', 'N/A')}")
            return True
        else:
            print(f"❌ API Error ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False
    finally:
        # Clean up server
        if 'server_process' in locals():
            server_process.terminate()


def main():
    parser = argparse.ArgumentParser(description="Test Uhakiki-AI Document Verification Pipeline")
    parser.add_argument("--image", required=True, help="Path to test image")
    parser.add_argument("--api", action="store_true", help="Test API endpoint")
    parser.add_argument("--direct", action="store_true", help="Test direct model access")
    
    args = parser.parse_args()
    
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"❌ Image file not found: {image_path}")
        return
    
    print(f"🎯 Testing image: {image_path}")
    print(f"📁 File size: {image_path.stat().st_size / 1024:.1f} KB")
    
    success = True
    
    # Test direct model access
    if args.direct or not args.api:
        model, model_manager = setup_model()
        if model and model_manager:
            success &= test_direct_model(image_path, model, model_manager)
        else:
            success = False
            print("⚠️ Skipping direct model test")
    
    # Test API endpoint
    if args.api or not args.direct:
        success &= test_api_call(image_path)
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
    else:
        print("❌ Some tests failed. Check the logs above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
