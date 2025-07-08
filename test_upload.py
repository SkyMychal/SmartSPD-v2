#!/usr/bin/env python3
"""
Simple test script to upload a document to SmartSPD
"""
import requests
import json

# API endpoint
BASE_URL = "http://localhost:8001"

def test_upload():
    # Create a test document
    test_content = """
    WELCH STATE BANK
    BENEFIT PLAN SUMMARY
    
    Medical Coverage:
    - Deductible: $1,000 individual / $2,000 family
    - Coinsurance: 80% after deductible
    - Out-of-pocket maximum: $5,000 individual / $10,000 family
    
    Prescription Drugs:
    - Generic: $10 copay
    - Brand: $30 copay
    - Specialty: $50 copay
    
    Vision Coverage:
    - Annual eye exam: $0 copay
    - Frames allowance: $200 every 2 years
    """
    
    # Create test file
    with open('/tmp/welch_bps_test.txt', 'w') as f:
        f.write(test_content)
    
    # Test health endpoint first
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Try to upload document
    try:
        files = {'file': ('welch_bps_test.txt', open('/tmp/welch_bps_test.txt', 'rb'), 'text/plain')}
        data = {
            'tpa_id': 'test-tpa-123',
            'health_plan_id': 'test-plan-456',
            'document_type': 'bps'
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/documents/upload", files=files, data=data)
        print(f"Upload response: {response.status_code}")
        if response.status_code == 200:
            print(f"Upload successful: {response.json()}")
        else:
            print(f"Upload failed: {response.text}")
            
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    test_upload()