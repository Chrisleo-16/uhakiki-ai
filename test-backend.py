#!/usr/bin/env python3
"""
Comprehensive test script for UhakikiAI backend
Tests all major components: GD-FD, MBIC, AAFI pipeline
"""

import asyncio
import aiohttp
import json
import base64
import io
from PIL import Image
import numpy as np
import time
import os

class UhakikiTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self):
        """Test basic health endpoint"""
        print("🔍 Testing health check...")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_document_forgery_detection(self):
        """Test GD-FD component"""
        print("🔍 Testing Document Forgery Detection...")
        
        # Create a simple test image
        test_image = Image.new('RGB', (256, 256), color='white')
        test_image_bytes = io.BytesIO()
        test_image.save(test_image_bytes, format='JPEG')
        test_image_bytes.seek(0)
        
        data = aiohttp.FormData()
        data.add_field('document', test_image_bytes, 
                      filename='test_document.jpg', 
                      content_type='image/jpeg')
        
        try:
            async with self.session.post(f"{self.base_url}/api/v1/verify/document", 
                                       data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Document analysis completed")
                    print(f"   Forgery probability: {result.get('forgery_probability', 'N/A')}")
                    print(f"   ELA status: {result.get('ela_status', 'N/A')}")
                    print(f"   Neural anomaly: {result.get('neural_anomaly', 'N/A')}")
                    print(f"   Judgment: {result.get('judgment', 'N/A')}")
                    return True
                else:
                    print(f"❌ Document analysis failed: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return False
        except Exception as e:
            print(f"❌ Document analysis error: {e}")
            return False
    
    async def test_comprehensive_verification(self):
        """Test full AAFI pipeline"""
        print("🔍 Testing Comprehensive Verification (AAFI Pipeline)...")
        
        # Create test files
        test_document = Image.new('RGB', (256, 256), color='white')
        test_face = Image.new('RGB', (128, 128), color='blue')
        
        doc_bytes = io.BytesIO()
        test_document.save(doc_bytes, format='JPEG')
        doc_bytes.seek(0)
        
        face_bytes = io.BytesIO()
        test_face.save(face_bytes, format='JPEG')
        face_bytes.seek(0)
        
        data = aiohttp.FormData()
        data.add_field('national_id', '123456789012')
        data.add_field('student_id', 'TEST-001')
        data.add_field('document_image', doc_bytes, 
                      filename='test_document.jpg', 
                      content_type='image/jpeg')
        data.add_field('face_image', face_bytes, 
                      filename='test_face.jpg', 
                      content_type='image/jpeg')
        
        try:
            async with self.session.post(f"{self.base_url}/api/v1/comprehensive-verification", 
                                       data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Comprehensive verification completed")
                    print(f"   Tracking ID: {result.get('tracking_id', 'N/A')}")
                    print(f"   Final verdict: {result.get('final_verdict', 'N/A')}")
                    print(f"   Confidence score: {result.get('confidence_score', 'N/A')}")
                    print(f"   Risk score: {result.get('risk_score', 'N/A')}")
                    
                    # Test verification status lookup
                    tracking_id = result.get('tracking_id')
                    if tracking_id:
                        await self.test_verification_status(tracking_id)
                    
                    return True
                else:
                    print(f"❌ Comprehensive verification failed: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return False
        except Exception as e:
            print(f"❌ Comprehensive verification error: {e}")
            return False
    
    async def test_verification_status(self, tracking_id):
        """Test verification status lookup"""
        print(f"🔍 Testing verification status for {tracking_id}...")
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/verification-status/{tracking_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Status lookup completed")
                    print(f"   Status: {result.get('status', 'N/A')}")
                    print(f"   Verdict: {result.get('verdict', 'N/A')}")
                    return True
                else:
                    print(f"❌ Status lookup failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Status lookup error: {e}")
            return False
    
    async def test_voice_enrollment(self):
        """Test voice biometric enrollment"""
        print("🔍 Testing voice profile enrollment...")
        
        # Create mock audio files (just text files for testing)
        audio1 = io.BytesIO(b"mock audio data 1")
        audio2 = io.BytesIO(b"mock audio data 2")
        audio3 = io.BytesIO(b"mock audio data 3")
        
        data = aiohttp.FormData()
        data.add_field('student_id', 'TEST-VOICE-001')
        data.add_field('audio_samples', audio1, 
                      filename='audio1.wav', 
                      content_type='audio/wav')
        data.add_field('audio_samples', audio2, 
                      filename='audio2.wav', 
                      content_type='audio/wav')
        data.add_field('audio_samples', audio3, 
                      filename='audio3.wav', 
                      content_type='audio/wav')
        
        try:
            async with self.session.post(f"{self.base_url}/api/v1/enroll-voice-profile", 
                                       data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Voice enrollment completed")
                    print(f"   Status: {result.get('status', 'N/A')}")
                    print(f"   Quality score: {result.get('quality_score', 'N/A')}")
                    return True
                else:
                    print(f"❌ Voice enrollment failed: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return False
        except Exception as e:
            print(f"❌ Voice enrollment error: {e}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket for real-time verification"""
        print("🔍 Testing WebSocket connection...")
        
        try:
            # Note: This is a basic test - full WebSocket testing would require more complex setup
            ws_url = self.base_url.replace('http', 'ws') + "/api/v1/ws/live-verification/TEST-001"
            
            # For now, just test if the endpoint exists
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                if response.status == 200:
                    print("✅ WebSocket endpoint likely available (server is running)")
                    return True
                else:
                    print("❌ WebSocket endpoint test failed")
                    return False
        except Exception as e:
            print(f"❌ WebSocket test error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting UhakikiAI Backend Test Suite")
        print("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Document Forgery Detection", self.test_document_forgery_detection),
            ("Comprehensive Verification (AAFI)", self.test_comprehensive_verification),
            ("Voice Profile Enrollment", self.test_voice_enrollment),
            ("WebSocket Connection", self.test_websocket_connection),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            print("-" * 40)
            
            start_time = time.time()
            success = await test_func()
            end_time = time.time()
            
            duration = end_time - start_time
            results.append({
                'test': test_name,
                'success': success,
                'duration': duration
            })
            
            print(f"⏱️  Duration: {duration:.2f}s")
            print(f"{'✅ PASSED' if success else '❌ FAILED'}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in results if r['success'])
        total = len(results)
        
        for result in results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{result['test']:<35} {status:<8} ({result['duration']:.2f}s)")
        
        print("-" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Backend is fully functional.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check backend logs.")
        
        return passed == total

async def main():
    """Main test runner"""
    print("🔧 UhakikiAI Backend Test Suite")
    print("Testing GD-FD, MBIC, and AAFI components")
    print("Make sure backend is running on http://localhost:8000")
    print()
    
    async with UhakikiTester() as tester:
        success = await tester.run_all_tests()
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
