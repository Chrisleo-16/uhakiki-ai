#!/usr/bin/env python3
"""
Test Complete Signup Flow
Tests the entire signup process to identify issues.
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8000"

def test_complete_signup():
    """Test complete signup flow"""
    print("🔍 Testing Complete Signup Flow")
    print("=" * 50)
    
    # Step 1: Test Kenyan signup with National ID
    print("\n1️⃣ Testing Kenyan Signup (National ID)")
    signup_data = {
        "citizenship": "kenyan",
        "identificationType": "national_id",
        "identificationNumber": "98765432",
        "firstName": "John",
        "email": "john.doe@example.com",
        "password": "Test123456"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register/kenyan",
            headers={"Content-Type": "application/json"},
            json=signup_data
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"✅ Signup successful! Token: {token[:50]}...")
            
            # Step 2: Test token validation
            print("\n2️⃣ Testing Token Validation")
            profile_response = requests.get(
                f"{BACKEND_URL}/api/v1/user/profile",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            print(f"Profile Status: {profile_response.status_code}")
            print(f"Profile Data: {profile_response.json()}")
            
            # Step 3: Test signin
            print("\n3️⃣ Testing Signin")
            signin_data = {
                "username": "john.doe@example.com",
                "password": "Test123456"
            }
            
            signin_response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/signin",
                headers={"Content-Type": "application/json"},
                json=signin_data
            )
            
            print(f"Signin Status: {signin_response.status_code}")
            print(f"Signin Response: {signin_response.json()}")
            
        else:
            print(f"❌ Signup failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_milvus_storage():
    """Test if data is being stored in Milvus"""
    print("\n🔍 Testing Milvus Storage")
    print("=" * 50)
    
    try:
        # Check if we can connect to Milvus
        from app.db.milvus_client import get_collection, search_vault
        
        collection = get_collection()
        print(f"✅ Connected to collection: {collection.name}")
        print(f"📊 Total entities: {collection.num_entities}")
        
        # Search for user records
        results = search_vault("user registration", limit=10)
        print(f"🔍 Found {len(results)} user records")
        
        for i, (doc, score) in enumerate(results[:3], 1):
            print(f"\n   Record {i}:")
            print(f"   • Content: {doc.page_content[:100]}...")
            print(f"   • Email: {doc.metadata.get('email', 'N/A')}")
            print(f"   • User ID: {doc.metadata.get('user_id', 'N/A')}")
            print(f"   • Score: {score:.3f}")
            
    except Exception as e:
        print(f"❌ Milvus test failed: {e}")

def test_backend_endpoints():
    """Test all authentication endpoints"""
    print("\n🔍 Testing Backend Endpoints")
    print("=" * 50)
    
    endpoints = [
        ("/api/v1/health", "GET"),
        ("/api/v1/auth/register/kenyan", "POST"),
        ("/api/v1/auth/signin", "POST"),
        ("/api/v1/user/profile", "GET"),
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}")
            else:
                response = requests.post(f"{BACKEND_URL}{endpoint}", json={})
            
            print(f"✅ {method} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {method} {endpoint}: {e}")

def main():
    print("🚀 UHAKIKI-AI SIGNUP FLOW DIAGNOSTIC")
    print("=" * 60)
    
    # Test backend endpoints
    test_backend_endpoints()
    
    # Test complete signup flow
    test_complete_signup()
    
    # Test Milvus storage
    test_milvus_storage()
    
    print("\n" + "=" * 60)
    print("🏁 DIAGNOSTIC COMPLETE")
    print("=" * 60)
    
    print("\n💡 Issues Found:")
    print("1. Check if backend is running: curl http://localhost:8000/api/v1/health")
    print("2. Check if Milvus is connected: Look for connection errors")
    print("3. Check CORS settings: Browser console might show CORS errors")
    print("4. Check frontend form validation: Browser console logs")
    print("5. Check token storage: localStorage should contain authToken")

if __name__ == "__main__":
    main()
