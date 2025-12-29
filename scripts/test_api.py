#!/usr/bin/env python3
"""
Backend API Test Script for DeNovo
Tests all API endpoints and generates a report
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app

def main():
    print('=' * 60)
    print('DENOVO BACKEND API TEST')
    print('=' * 60)
    
    print('\n📡 Available Routes:')
    for rule in app.url_map.iter_rules():
        if 'static' not in rule.rule:
            methods = list(rule.methods - {'OPTIONS', 'HEAD'})
            print(f'  {rule.rule} {methods}')
    
    print('\n🧪 Testing Endpoints with Flask Test Client...')
    
    with app.test_client() as client:
        # Test health endpoint
        try:
            response = client.get('/api/health')
            if response.status_code == 200:
                print('  ✅ GET /api/health - OK')
            else:
                print(f'  ⚠️ GET /api/health - Status {response.status_code}')
        except Exception as e:
            print(f'  ❌ GET /api/health - {e}')
        
        # Test home page
        try:
            response = client.get('/')
            if response.status_code == 200:
                print('  ✅ GET / - OK')
            else:
                print(f'  ⚠️ GET / - Status {response.status_code}')
        except Exception as e:
            print(f'  ❌ GET / - {e}')
        
        # Test predict endpoint
        try:
            response = client.post('/api/predict', 
                json={'smiles': 'CCO'},
                content_type='application/json'
            )
            if response.status_code == 200:
                data = response.get_json()
                print('  ✅ POST /api/predict - OK')
                if 'predictions' in data:
                    print(f'      Predictions received: {list(data.get("predictions", {}).keys())[:3]}...')
            else:
                print(f'  ⚠️ POST /api/predict - Status {response.status_code}')
        except Exception as e:
            print(f'  ❌ POST /api/predict - {e}')
        
        # Test stats endpoint
        try:
            response = client.get('/api/stats')
            if response.status_code == 200:
                print('  ✅ GET /api/stats - OK')
            else:
                print(f'  ⚠️ GET /api/stats - Status {response.status_code}')
        except Exception as e:
            print(f'  ❌ GET /api/stats - {e}')
    
    print('\n' + '=' * 60)
    print('TEST COMPLETE')
    print('=' * 60)

if __name__ == '__main__':
    main()
