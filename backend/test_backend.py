#!/usr/bin/env python3
"""
Test Backend Health and APIs
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"✅ Health Check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_endpoints():
    """Test endpoints list"""
    try:
        response = requests.get(f"{BASE_URL}/api/endpoints", timeout=5)
        print(f"✅ Endpoints: {response.status_code}")
        data = response.json()
        print(f"   Available endpoints: {data.get('count')}")
        for endpoint in data.get('endpoints', []):
            print(f"      - {endpoint}")
        return True
    except Exception as e:
        print(f"❌ Endpoints Failed: {e}")
        return False

def test_prediction():
    """Test single prediction"""
    try:
        payload = {
            "smiles": "CCO",
            "molecule_name": "Ethanol"
        }
        response = requests.post(
            f"{BASE_URL}/api/predict",
            json=payload,
            timeout=10
        )
        print(f"✅ Prediction Test: {response.status_code}")
        data = response.json()
        print(f"   Molecule: {data.get('smiles')}")
        print(f"   Overall: {data.get('overall_toxicity')}")
        print(f"   Toxic endpoints: {data.get('toxic_endpoints')}")
        return True
    except Exception as e:
        print(f"❌ Prediction Failed: {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        print(f"✅ Stats: {response.status_code}")
        data = response.json()
        print(f"   Total predictions: {data.get('total_predictions')}")
        print(f"   Success rate: {data.get('success_rate')}%")
        return True
    except Exception as e:
        print(f"❌ Stats Failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing MedToXAi Backend API")
    print("=" * 60)
    
    # Wait for server to be ready
    print("\n⏳ Waiting for server to start...")
    time.sleep(2)
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Endpoints List", test_endpoints),
        ("Statistics", test_stats),
        ("Prediction (Ethanol)", test_prediction),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔬 Testing: {test_name}")
        print("-" * 60)
        if test_func():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
