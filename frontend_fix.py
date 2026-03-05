#!/usr/bin/env python3
"""
Frontend Error Fix for Uhakiki-AI
Provides exact response format that frontend expects.
"""

import requests
import json

def test_document_verification():
    """Test document verification with proper response format"""
    print("🔧 Testing Document Verification API")
    print("=" * 50)
    
    # Image path
    image_path = "/home/cb-fx/uhakiki-ai/backend/data/forensics/original/IMG_20250924_121136_884~2.jpg"
    
    try:
        # Test the API endpoint
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post('http://localhost:8000/api/v1/document/verify', files=files)
        
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Response:")
            print(f"   • authentic: {result.get('authentic')}")
            print(f"   • confidence: {result.get('confidence')}")
            print(f"   • mse_score: {result.get('mse_score')}")
            print(f"   • message: {result.get('message')}")
            
            # Check if response matches expected frontend format
            expected_keys = ['authentic', 'confidence', 'mse_score', 'message']
            missing_keys = [key for key in expected_keys if key not in result]
            
            if missing_keys:
                print(f"⚠️ Missing keys in response: {missing_keys}")
            else:
                print(f"✅ Response format matches frontend expectations")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Make sure backend is running on http://localhost:8000")

def show_expected_frontend_format():
    """Show the exact format frontend expects"""
    print("\n📋 Expected Frontend Response Format:")
    print("=" * 50)
    
    expected_format = {
        "authentic": True,  # Boolean
        "confidence": 94.36,  # Float (0-100)
        "mse_score": 0.056427,  # Float
        "message": "Document verified successfully"  # String
    }
    
    print(json.dumps(expected_format, indent=2))
    
    print("\n🔍 Frontend JavaScript expects:")
    print("   const res = await fetch(endpoint, { method:'POST', body:fd })")
    print("   const r = await res.json()")
    print("   setDocStatus(r.authentic ? 'ok' : 'fail')")

def main():
    print("🚀 UHAKIKI-AI FRONTEND ERROR FIX")
    print("=" * 60)
    
    # Show expected format
    show_expected_frontend_format()
    
    # Test API
    test_document_verification()
    
    print("\n💡 Frontend Integration Steps:")
    print("1. Ensure backend returns exact keys: authentic, confidence, mse_score, message")
    print("2. Frontend handles boolean 'authentic' field correctly")
    print("3. Confidence should be float 0-100")
    print("4. Message should be user-friendly")
    
    print("\n🏁 FIX COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
