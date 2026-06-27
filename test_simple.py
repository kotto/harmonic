#!/usr/bin/env python3
"""
Simple test for METHOD_2 compression
"""
import requests
import json
from PIL import Image
import io

# Create a simple test image
img = Image.new('RGB', (640, 480), color='red')
buffer = io.BytesIO()
img.save(buffer, format='PNG')
image_data = buffer.getvalue()

# Upload
print("Uploading image...")
files = {'image': ('test.png', image_data, 'image/png')}
r = requests.post('http://localhost:5000/upload', files=files)
print(f"Upload status: {r.status_code}")
if r.status_code == 200:
    result = r.json()
    print(f"Upload result: {json.dumps(result, indent=2)}")
    filename = result['filename']
    
    # Compress
    print("\nCompressing...")
    r = requests.post('http://localhost:5000/compress', json={'filename': filename, 'quality': 'high'})
    print(f"Compress status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
else:
    print(f"Error: {r.text}")
