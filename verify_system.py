#!/usr/bin/env python3
"""
System Verification Script for Uhakiki-AI
Tests all backend components before frontend integration.

Usage:
    python verify_system.py
"""

import os
import sys
import requests
import subprocess
import time
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_test(test_name, status, details=""):
    status_icon = "✅" if status else "❌"
    print(f"  {status_icon} {test_name}")
    if details:
        print(f"     {details}")

def check_files_exist():
    """Check if all required model files exist."""
    print_section("📁 File System Check")
    
    required_files = [
        "backend/models/rad_autoencoder_kenyan.pth",
        "backend/models/kenyan_threshold_config.json", 
        "backend/models/document_classifier.pkl",
        "backend/models/biometric_verifier.pkl",
        "backend/models/fraud_detector.h5"
    ]
    
    all_exist = True
    for file_path in required_files:
        exists = Path(file_path).exists()
        print_test(f"{file_path}", exists, 
                  "✅ Found" if exists else "❌ Missing")
        if not exists:
            all_exist = False
    
    return all_exist

def check_model_loading():
    """Test if all models can be loaded."""
    print_section("🧠 Model Loading Test")
    
    try:
        # Add backend to path
        sys.path.append("backend")
        
        from models.model_loader import ModelManager
        model_manager = ModelManager()
        
        # Test RAD model
        rad_model = model_manager.load_rad_autoencoder()
        print_test("RAD Autoencoder", rad_model is not None)
        
        # Test biometric verifier
        bio_verifier = model_manager.load_biometric_verifier()
        print_test("Biometric Verifier", bio_verifier is not None)
        
        # Test fraud detector
        fraud_detector = model_manager.load_fraud_detector()
        print_test("Fraud Detector", fraud_detector is not None)
        
        return True
        
    except Exception as e:
        print_test("Model Loading", False, str(e))
        return False

def check_image_processing():
    """Test image processing with actual model."""
    print_section("🖼️  Image Processing Test")
    
    try:
        import torch
        import numpy as np
        from PIL import Image
        
        # Test with one of your existing images
        test_image = "backend/data/forensics/original/IMG_20250924_121136_884~2.jpg"
        
        if not Path(test_image).exists():
            print_test("Test Image", False, f"{test_image} not found")
            return False
        
        # Load and preprocess
        image = Image.open(test_image).convert('L')  # Grayscale for 1-channel model
        image = image.resize((224, 224))
        
        image_array = np.array(image) / 255.0
        image_tensor = torch.from_numpy(image_array).float()
        image_tensor = image_tensor.unsqueeze(0).unsqueeze(0)  # [1, 1, 224, 224]
        
        print_test("Image Preprocessing", True, 
                  f"Shape: {image_tensor.shape}")
        
        # Test model prediction
        sys.path.append("backend")
        from models.model_loader import ModelManager
        model_manager = ModelManager()
        
        mse_score, is_forged = model_manager.predict_document_authenticity(image_tensor)
        
        print_test("Model Prediction", True,
                  f"MSE: {mse_score:.6f}, Forged: {is_forged}")
        
        return True
        
    except Exception as e:
        print_test("Image Processing", False, str(e))
        return False

def check_api_endpoints():
    """Test if API server is running and endpoints work."""
    print_section("🌐 API Endpoint Test")
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print_test("API Server", True, "Health check passed")
            server_running = True
        else:
            print_test("API Server", False, f"Status: {response.status_code}")
            server_running = False
    except requests.exceptions.ConnectionError:
        print_test("API Server", False, "Server not running on localhost:8000")
        return False
    except Exception as e:
        print_test("API Server", False, str(e))
        return False
    
    # Test document scan endpoint (if server is running)
    if server_running:
        try:
            test_image = "backend/data/forensics/original/IMG_20250924_121136_884~2.jpg"
            with open(test_image, 'rb') as f:
                files = {'file': ('test.jpg', f, 'image/jpeg')}
                data = {
                    'document_type': 'national_id',
                    'country': 'kenya'
                }
                
                response = requests.post(
                    "http://localhost:8000/api/v1/document/verify",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print_test("Document Scan API", True,
                              f"Authenticity: {result.get('authenticity', 'N/A')}")
                else:
                    print_test("Document Scan API", False, 
                              f"Status: {response.status_code}")
                    
        except Exception as e:
            print_test("Document Scan API", False, str(e))
    
    return server_running

def start_api_server():
    """Start the API server for testing."""
    print_section("🚀 Starting API Server")
    
    try:
        print("Starting uvicorn server...")
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "backend.main:app",
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("Waiting for server to start...")
        time.sleep(5)  # Give server time to start
        
        # Check if server started successfully
        try:
            response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
            if response.status_code == 200:
                print_test("API Server Start", True, "Server running on localhost:8000")
                return server_process
            else:
                print_test("API Server Start", False, "Health check failed")
                server_process.terminate()
                return None
        except:
            print_test("API Server Start", False, "Server not responding")
            server_process.terminate()
            return None
            
    except Exception as e:
        print_test("API Server Start", False, str(e))
        return None

def main():
    print("🔍 Uhakiki-AI System Verification")
    print("Testing all components before frontend integration...")
    
    # Run all checks
    checks = {
        "Files": check_files_exist(),
        "Model Loading": check_model_loading(),
        "Image Processing": check_image_processing()
    }
    
    # Check if API server is already running
    api_running = check_api_endpoints()
    
    # Start API server if not running
    if not api_running:
        server_process = start_api_server()
        if server_process:
            # Test endpoints after starting server
            check_api_endpoints()
            
            print_section("📋 Summary")
            print("\n✅ System is READY for frontend integration!")
            print("🌐 API Server running on: http://localhost:8000")
            print("📚 API Documentation: http://localhost:8000/docs")
            print("\n🎯 Next Steps:")
            print("   1. Connect frontend to http://localhost:8000")
            print("   2. Test document upload and analysis")
            print("   3. Verify OCR and detail extraction")
            
            print("\n⚠️  Press Ctrl+C to stop the server")
            try:
                server_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Server stopped")
    else:
        print_section("📋 Summary")
        if all(checks.values()):
            print("✅ All checks passed! System is ready.")
        else:
            print("❌ Some checks failed. Please fix issues above.")
            failed_checks = [k for k, v in checks.items() if not v]
            print(f"Failed: {', '.join(failed_checks)}")

if __name__ == "__main__":
    main()
