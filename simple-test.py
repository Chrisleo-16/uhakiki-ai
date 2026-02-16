#!/usr/bin/env python3
"""
Simple test with proper image data
"""

import requests
import numpy as np
from PIL import Image
import io

def create_test_image():
    """Create a simple test image"""
    # Create a 224x224 white image
    data = np.full((224, 224, 3), 255, dtype=np.uint8)
    img = Image.fromarray(data)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_with_image():
    """Test with actual image data"""
    try:
        # Create test image
        img_data = create_test_image()
        
        # Send request
        url = "http://localhost:8000/api/v1/secure-ingest"
        files = {'document_image': ('test.jpg', img_data, 'image/jpeg')}
        data = {'national_id': 'TEST-999'}
        
        print("🚀 Sending test request...")
        response = requests.post(url, data=data, files=files)
        
        print(f"📡 Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Test successful!")
            return True
        else:
            print("❌ Test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_with_image()
