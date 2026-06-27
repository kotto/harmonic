#!/usr/bin/env python
"""
Test script to verify the Flask app works
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("1. Importing Flask...")
    from flask import Flask
    print("   ✓ Flask imported")
    
    print("2. Importing app...")
    from app import app
    print("   ✓ App imported")
    
    print("3. Creating test client...")
    client = app.test_client()
    print("   ✓ Test client created")
    
    print("4. Testing / endpoint...")
    response = client.get('/')
    print(f"   Status: {response.status_code}")
    print(f"   Data: {response.get_json()}")
    
    print("5. Testing /health endpoint...")
    response = client.get('/health')
    print(f"   Status: {response.status_code}")
    print(f"   Data: {response.get_json()}")
    
    print("6. Testing /info endpoint...")
    response = client.get('/info')
    print(f"   Status: {response.status_code}")
    print(f"   Data: {response.get_json()}")
    
    print("\n✓ All tests passed!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
