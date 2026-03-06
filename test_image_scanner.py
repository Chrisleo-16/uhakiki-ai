#!/usr/bin/env python3
"""
AI Image Scanner for Uhakiki-AI
Tests the RAD model on a specific image to get exact names and avoid frontend errors.
"""

import os
import sys
import torch
import numpy as np
from PIL import Image
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


def setup_model():
    """Setup the RAD model for image scanning."""
    try:
        from models.model_loader import ModelManager
        model_manager = ModelManager()
        model         = model_manager.load_rad_autoencoder()
        print("✅ RAD model loaded successfully")
        return model, model_manager
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None, None


def preprocess_image(image_path: Path) -> torch.Tensor:
    """
    Preprocess image for the RAD model.

    The model expects a 3-channel RGB tensor shaped [1, 3, 224, 224].
    We always convert to RGB via PIL so we're safe with grayscale or RGBA
    source images – no raw cv2 channel gymnastics needed here.
    """
    try:
        # PIL .convert('RGB') handles: L (gray), RGBA, P (palette), CMYK, etc.
        image = Image.open(image_path).convert('RGB')
        print(f"📷 Original image size : {image.size}")

        image = image.resize((224, 224))
        print(f"📷 Resized to          : {image.size}")

        image_array  = np.array(image) / 255.0                          # [224,224,3] float64
        image_tensor = torch.from_numpy(image_array).float()            # [224,224,3]
        image_tensor = image_tensor.permute(2, 0, 1)                    # [3,224,224]
        image_tensor = image_tensor.unsqueeze(0)                        # [1,3,224,224]

        print(f"📷 Final tensor shape  : {image_tensor.shape}")
        return image_tensor

    except Exception as e:
        print(f"❌ Failed to preprocess image: {e}")
        return None


def scan_image_with_model(image_path: Path, model, model_manager) -> dict:
    """Scan image with RAD model and return results dict."""
    try:
        print(f"\n🔍 Scanning image: {image_path}")

        image_tensor = preprocess_image(image_path)
        if image_tensor is None:
            return None

        print("🤖 Running RAD model prediction...")
        mse_score, is_forged = model_manager.predict_document_authenticity(image_tensor)

        confidence = max(0.0, (1.0 - mse_score) * 100)

        results = {
            "image_path": str(image_path),
            "mse_score":  float(mse_score),
            "is_forged":  bool(is_forged),
            "confidence": float(confidence),
            "status":     "FORGED" if is_forged else "AUTHENTIC",
            "message": (
                "Document appears to be forged"
                if is_forged
                else "Document verified successfully"
            ),
        }

        print("📊 Results:")
        print(f"   • MSE Score : {mse_score:.6f}")
        print(f"   • Is Forged : {is_forged}")
        print(f"   • Confidence: {confidence:.2f}%")
        print(f"   • Status    : {results['status']}")

        return results

    except Exception as e:
        print(f"❌ Failed to scan image: {e}")
        return None


def test_api_endpoint(image_path: Path) -> dict:
    """Test the /api/v1/document/verify endpoint directly."""
    try:
        import requests

        with open(image_path, 'rb') as f:
            response = requests.post(
                'http://localhost:8000/api/v1/document/verify',
                files={'file': f},
            )

        if response.status_code == 200:
            result = response.json()
            print("✅ API Test Successful:")
            print(f"   • Authentic  : {result.get('authentic')}")
            print(f"   • Confidence : {result.get('confidence', 0):.2f}%")
            print(f"   • MSE Score  : {result.get('mse_score', 0):.6f}")
            print(f"   • Message    : {result.get('message')}")
            return result
        else:
            print(f"❌ API Test Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ API Test Error: {e}")
        return None


def main():
    print("🚀 UHAKIKI-AI IMAGE SCANNER")
    print("=" * 50)

    image_path = Path(
        "/home/cb-fx/uhakiki-ai/backend/data/forensics/original"
        "/IMG_20250924_121136_884~2.jpg"
    )

    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return

    print(f"📸 Found image : {image_path}")
    print(f"📏 File size   : {image_path.stat().st_size} bytes")

    print("\n🤖 Setting up AI model...")
    model, model_manager = setup_model()

    if model is None:
        print("❌ Cannot proceed without model")
        return

    print("\n🔍 Starting image scan...")
    results = scan_image_with_model(image_path, model, model_manager)

    if results:
        print("\n✅ Scan completed successfully!")
        print("📋 Final Results:")
        for key, value in results.items():
            print(f"   • {key}: {value}")

        print("\n🌐 Testing API endpoint...")
        api_results = test_api_endpoint(image_path)

        if api_results:
            print("✅ API test passed!")
        else:
            print("⚠️ API test failed, but model scan worked")

    print("\n🏁 SCAN COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    main()