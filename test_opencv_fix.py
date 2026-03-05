#!/usr/bin/env python3
"""
Test OpenCV grayscale image handling fixes
"""

import cv2
import numpy as np
from PIL import Image
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_grayscale_handling():
    """Test that our fixes handle grayscale images properly"""
    print("🧪 Testing OpenCV grayscale image handling fixes...")
    
    # Test 1: Create a grayscale image
    print("\n1. Testing grayscale image handling...")
    gray_image = np.zeros((100, 100), dtype=np.uint8)
    gray_image[25:75, 25:75] = 255  # White square in center
    
    try:
        # Test document service quality analysis
        from app.services.document_service import document_service
        result = document_service.analyze_document_quality(gray_image)
        print("✅ Document service handles grayscale images correctly")
        print(f"   Quality score: {result.get('quality_score', 'N/A')}")
    except Exception as e:
        print(f"❌ Document service error: {e}")
    
    try:
        # Test biometric service face detection
        from app.services.biometric_service import biometric_service
        face_detected, face_region = biometric_service.detect_face(gray_image)
        print("✅ Biometric service handles grayscale images correctly")
        print(f"   Face detected: {face_detected}")
    except Exception as e:
        print(f"❌ Biometric service error: {e}")
    
    # Test 2: Create an RGB image
    print("\n2. Testing RGB image handling...")
    rgb_image = np.zeros((100, 100, 3), dtype=np.uint8)
    rgb_image[25:75, 25:75] = [255, 255, 255]  # White square in center
    
    try:
        result = document_service.analyze_document_quality(rgb_image)
        print("✅ Document service handles RGB images correctly")
        print(f"   Quality score: {result.get('quality_score', 'N/A')}")
    except Exception as e:
        print(f"❌ Document service RGB error: {e}")
    
    try:
        face_detected, face_region = biometric_service.detect_face(rgb_image)
        print("✅ Biometric service handles RGB images correctly")
        print(f"   Face detected: {face_detected}")
    except Exception as e:
        print(f"❌ Biometric service RGB error: {e}")
    
    # Test 3: Test with actual image file
    print("\n3. Testing with actual image file...")
    image_path = "/home/cb-fx/uhakiki-ai/backend/data/forensics/original/IMG_20250924_121136_884~2.jpg"
    
    if os.path.exists(image_path):
        try:
            # Load with PIL and convert to different formats
            pil_image = Image.open(image_path)
            
            # Test as RGB
            rgb_pil = pil_image.convert('RGB')
            rgb_array = np.array(rgb_pil)
            result = document_service.analyze_document_quality(rgb_array)
            print("✅ Actual RGB image processed successfully")
            
            # Test as grayscale
            gray_pil = pil_image.convert('L')
            gray_array = np.array(gray_pil)
            result = document_service.analyze_document_quality(gray_array)
            print("✅ Actual grayscale image processed successfully")
            
        except Exception as e:
            print(f"❌ Actual image test error: {e}")
    else:
        print("⚠️ Test image not found")
    
    print("\n🏁 OpenCV grayscale handling test completed!")

if __name__ == "__main__":
    test_grayscale_handling()
