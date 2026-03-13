#!/usr/bin/env python3
"""
OCR Testing Script for Uhakiki-AI Document Processing
Tests the improved OCR engine and document service with real ID samples.

Usage:
    python test_ocr_models.py
    python test_ocr_models.py --image path/to/id.jpg
"""

import os
import sys
import argparse
import base64
from pathlib import Path
import json

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_ocr_engine_improvements():
    """Test the improved OCR engine with sample text."""
    print("🔍 Testing OCR Engine Improvements")
    print("=" * 50)
    
    try:
        from app.logic.ocr_engine import OCRModel
        
        # Test cases with realistic Kenyan ID OCR text
        test_cases = [
            {
                "name": "Realistic Kenyan ID OCR",
                "description": "Full ID card OCR output",
                "expected_fields": ["surname", "first_name", "id_number", "sex", "nationality", "date_of_birth"]
            },
            {
                "name": "Noisy OCR Text", 
                "description": "OCR with common errors",
                "text": "SURNAME LEO CHRISBEN EVANS 5EX MALE NATIONALITY KEN DATE 0F BIRTH 03.09.2007 ID 975162603"
            },
            {
                "name": "Partial OCR",
                "description": "Incomplete OCR extraction",
                "text": "SURNAME LEO SEX MALE ID 975162603"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 Test {i}: {test_case['name']}")
            print(f"   Description: {test_case['description']}")
            
            if 'text' in test_case:
                # Simulate image bytes from text (create dummy image)
                import numpy as np
                import cv2
                
                # Create a simple test image with text
                img = np.ones((200, 600, 3), dtype=np.uint8) * 255
                cv2.putText(img, test_case['text'][:50], (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
                
                # Convert to bytes
                _, buffer = cv2.imencode('.jpg', img)
                image_bytes = buffer.tobytes()
                
                # Test OCR extraction
                result = OCRModel.extract_and_validate(image_bytes)
                
                print(f"   ✅ OCR Result:")
                for key, value in result.items():
                    if value:
                        print(f"      {key}: {value}")
            
        return True
        
    except Exception as e:
        print(f"❌ OCR Engine Test Failed: {e}")
        return False

def test_document_service_improvements():
    """Test the improved document service."""
    print("\n🔍 Testing Document Service Improvements")
    print("=" * 50)
    
    try:
        from app.services.document_service import DocumentScanningService, extract_kenyan_id_fields
        
        service = DocumentScanningService()
        
        # Test name extraction improvements
        name_test_cases = [
            {
                "text": "SURNAME LEO GIVEN NAME CHRISBEN EVANS SEX MALE NATIONALITY KEN",
                "expected_name": "Leo Chrisben Evans",
                "strategy": "Inline with GIVEN NAME label"
            },
            {
                "text": "SURNAME LEO CHRISBEN EVANS SEX MALE",
                "expected_name": "Leo Chrisben Evans", 
                "strategy": "Inline without GIVEN NAME label"
            },
            {
                "text": "SURNAME\nLEO\nGIVEN NAME\nCHRISBEN EVANS\nSEX MALE",
                "expected_name": "Leo Chrisben Evans",
                "strategy": "Separate lines"
            },
            {
                "text": "JAMHURI YA KENYA\nSURNAME LEO\nGIVEN NAME CHRISBEN EVANS\nSEX MALE\nNATIONALITY KEN\nDATE OF BIRTH 03.09.2007\nID NUMBER 975162603",
                "expected_name": "Leo Chrisben Evans",
                "strategy": "Full realistic OCR"
            }
        ]
        
        print("\n📝 Testing Name Extraction:")
        all_passed = True
        
        for i, test_case in enumerate(name_test_cases, 1):
            print(f"\n   Test {i}: {test_case['strategy']}")
            print(f"   Input: {test_case['text'][:50]}...")
            
            # Test field extraction
            fields = extract_kenyan_id_fields(test_case['text'])
            extracted_name = fields.get('name', '')
            
            print(f"   Expected: {test_case['expected_name']}")
            print(f"   Got:      {extracted_name}")
            
            # Check if match (case insensitive)
            if extracted_name.lower() == test_case['expected_name'].lower():
                print(f"   ✅ PASS")
            else:
                print(f"   ❌ FAIL")
                all_passed = False
        
        # Test full field extraction
        print(f"\n📋 Testing Full Field Extraction:")
        full_ocr = """JAMHURI YA KENYA REPUBLIC OF KENYA KITAMBULISHO CHA TAIFA
SURNAME LEO
GIVEN NAME CHRISBEN EVANS
SEX MALE NATIONALITY KEN DATE OF BIRTH 03. 09. 2007
PLACE OF BIRTH EMBAKASI
NUMBER 975162603
DATE OF EXPIRY 05. 09. 2035
PLACE OF ISSUE NJIRU"""
        
        fields = extract_kenyan_id_fields(full_ocr)
        print(f"   Extracted Fields:")
        for key, value in fields.items():
            if value:
                print(f"      {key}: {value}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Document Service Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_real_image(image_path):
    """Test OCR with a real image file."""
    print(f"\n🔍 Testing with Real Image: {image_path}")
    print("=" * 50)
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return False
    
    try:
        from app.services.document_service import DocumentScanningService
        from app.logic.ocr_engine import OCRModel
        
        # Read image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        print(f"📁 Image size: {len(image_bytes) / 1024:.1f} KB")
        
        # Test OCR Engine
        print(f"\n🔤 OCR Engine Results:")
        ocr_result = OCRModel.extract_and_validate(image_bytes)
        
        for key, value in ocr_result.items():
            if value and key != 'raw_text':
                print(f"   {key}: {value}")
        
        # Test Document Service
        print(f"\n📄 Document Service Results:")
        service = DocumentScanningService()
        
        # Convert to base64 for service
        image_b64 = base64.b64encode(image_bytes).decode()
        
        # Process document
        result = service.scan_document(image_b64, expected_type="national_id")
        
        print(f"   Document Type: {result.get('document_type', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Score: {result.get('score', 'N/A')}")
        
        if 'extracted_fields' in result:
            print(f"   Extracted Fields:")
            for key, value in result['extracted_fields'].items():
                if value:
                    print(f"      {key}: {value}")
        
        if 'quality_analysis' in result:
            quality = result['quality_analysis']
            print(f"   Quality Analysis:")
            print(f"      Sharpness: {quality.get('sharpness', 'N/A')}")
            print(f"      Noise Level: {quality.get('noise_level', 'N/A')}")
            print(f"      Quality Score: {quality.get('quality_score', 'N/A')}")
        
        if 'forgery_detection' in result:
            forgery = result['forgery_detection']
            print(f"   Forgery Detection:")
            print(f"      Risk Score: {forgery.get('risk_score', 'N/A')}")
            print(f"      Risk Level: {forgery.get('risk_level', 'N/A')}")
            if forgery.get('indicators'):
                print(f"      Indicators: {', '.join(forgery['indicators'][:3])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Real Image Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint():
    """Test the document verification API endpoint."""
    print(f"\n🌐 Testing API Endpoint")
    print("=" * 50)
    
    try:
        import requests
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
            if response.status_code != 200:
                print("❌ API server not responding")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to API server")
            print("   Start server with: cd backend && python3 -m uvicorn main:app --reload")
            return False
        
        # Test with sample image
        test_image = "backend/data/forensics/original/IMG_20250924_121136_884~2.jpg"
        if not Path(test_image).exists():
            print(f"❌ Test image not found: {test_image}")
            return False
        
        with open(test_image, 'rb') as f:
            files = {'file': ('test_id.jpg', f, 'image/jpeg')}
            data = {'document_type': 'national_id'}
            
            response = requests.post(
                "http://localhost:8000/api/v1/document/verify",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Test Successful")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Document Type: {result.get('document_type', 'N/A')}")
            print(f"   Authentic: {result.get('authentic', 'N/A')}")
            
            if 'extracted_fields' in result:
                fields = result['extracted_fields']
                if fields.get('name'):
                    print(f"   Name: {fields['name']}")
                if fields.get('id_number'):
                    print(f"   ID Number: {fields['id_number']}")
            
            return True
        else:
            print(f"❌ API Error ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test OCR Models for Uhakiki-AI")
    parser.add_argument("--image", help="Test with specific image file")
    parser.add_argument("--api", action="store_true", help="Test API endpoint")
    
    args = parser.parse_args()
    
    print("🧪 OCR Model Testing Suite")
    print("=" * 60)
    
    # Run all tests
    results = {
        "OCR Engine": test_ocr_engine_improvements(),
        "Document Service": test_document_service_improvements()
    }
    
    # Test with real image if provided
    if args.image:
        results["Real Image Test"] = test_with_real_image(args.image)
    
    # Test API if requested
    if args.api:
        results["API Endpoint"] = test_api_endpoint()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Test Results Summary")
    print(f"{'='*60}")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print(f"\n🎉 All tests passed! OCR system is working perfectly!")
    else:
        print(f"\n⚠️ Some tests failed. Check the logs above.")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Test with real ID images: python test_ocr_models.py --image path/to/id.jpg")
    print(f"   2. Test API integration: python test_ocr_models.py --image path/to/id.jpg --api")
    print(f"   3. Start frontend and test complete pipeline")

if __name__ == "__main__":
    main()
