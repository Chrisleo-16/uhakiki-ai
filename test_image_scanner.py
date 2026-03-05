#!/usr/bin/env python3
"""
AI Image Scanner for Uhakiki-AI
Tests the RAD model on the specific image to get exact names and avoid frontend errors.
"""

import os
import sys
import torch
import numpy as np
from PIL import Image
import cv2
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def setup_model():
    """Setup the RAD model for image scanning"""
    try:
        from models.model_loader import ModelManager
        model_manager = ModelManager()
        model = model_manager.load_rad_autoencoder()
        print("✅ RAD model loaded successfully")
        return model, model_manager
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None, None

def preprocess_image(image_path):
    """Preprocess image for RAD model"""
    try:
        # Load and convert to RGB (not grayscale)
        image = Image.open(image_path).convert('RGB')  # Convert to RGB
        print(f"📷 Original image size: {image.size}")
        
        # Resize to 224x224
        image = image.resize((224, 224))
        print(f"📷 Resized to: {image.size}")
        
        # Convert to tensor and normalize
        image_array = np.array(image) / 255.0  # Normalize to 0-1
        image_tensor = torch.from_numpy(image_array).float()
        
        # Rearrange dimensions: [224, 224, 3] -> [3, 224, 224]
        image_tensor = image_tensor.permute(2, 0, 1)
        
        # Add batch dimension: [3, 224, 224] -> [1, 3, 224, 224]
        image_tensor = image_tensor.unsqueeze(0)
        
        print(f"📷 Final tensor shape: {image_tensor.shape}")
        return image_tensor
        
    except Exception as e:
        print(f"❌ Failed to preprocess image: {e}")
        return None

def scan_image_with_model(image_path, model, model_manager):
    """Scan image with RAD model to get exact results"""
    try:
        print(f"\n🔍 Scanning image: {image_path}")
        
        # Preprocess image
        image_tensor = preprocess_image(image_path)
        if image_tensor is None:
            return None
        
        # Run model prediction
        print("🤖 Running RAD model prediction...")
        mse_score, is_forged = model_manager.predict_document_authenticity(image_tensor)
        
        # Calculate confidence
        confidence = max(0, (1 - mse_score) * 100)
        
        results = {
            "image_path": str(image_path),
            "mse_score": float(mse_score),
            "is_forged": bool(is_forged),
            "confidence": float(confidence),
            "status": "FORGED" if is_forged else "AUTHENTIC",
            "message": "Document appears to be forged" if is_forged else "Document verified successfully"
        }
        
        print(f"📊 Results:")
        print(f"   • MSE Score: {mse_score:.6f}")
        print(f"   • Is Forged: {is_forged}")
        print(f"   • Confidence: {confidence:.2f}%")
        print(f"   • Status: {results['status']}")
        
        return results
        
    except Exception as e:
        print(f"❌ Failed to scan image: {e}")
        return None

def test_api_endpoint(image_path):
    """Test the API endpoint directly"""
    try:
        import requests
        
        # Prepare image for upload
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post('http://localhost:8000/api/v1/document/verify', files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Test Successful:")
            print(f"   • Authentic: {result.get('authentic')}")
            print(f"   • Confidence: {result.get('confidence'):.2f}%")
            print(f"   • MSE Score: {result.get('mse_score'):.6f}")
            print(f"   • Message: {result.get('message')}")
            return result
        else:
            print(f"❌ API Test Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ API Test Error: {e}")
        return None

def main():
    """Main function to test image scanning"""
    print("🚀 UHAKIKI-AI IMAGE SCANNER")
    print("=" * 50)
    
    # Image path
    image_path = Path("/home/cb-fx/uhakiki-ai/backend/data/forensics/original/IMG_20250924_121136_884~2.jpg")
    
    # Check if image exists
    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"📸 Found image: {image_path}")
    print(f"📏 Image size: {image_path.stat().st_size} bytes")
    
    # Setup model
    print("\n🤖 Setting up AI model...")
    model, model_manager = setup_model()
    
    if model is None:
        print("❌ Cannot proceed without model")
        return
    
    # Scan image
    print("\n🔍 Starting image scan...")
    results = scan_image_with_model(image_path, model, model_manager)
    
    if results:
        print(f"\n✅ Scan completed successfully!")
        print(f"📋 Final Results:")
        for key, value in results.items():
            print(f"   • {key}: {value}")
        
        # Test API endpoint
        print(f"\n🌐 Testing API endpoint...")
        api_results = test_api_endpoint(image_path)
        
        if api_results:
            print(f"✅ API test passed!")
        else:
            print(f"⚠️ API test failed, but model scan worked")
    
    print(f"\n🏁 SCAN COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()
