#!/usr/bin/env python3
"""
Test decompression for METHOD_2
"""
import requests
import json
from PIL import Image
import io
import base64

# Create a simple test image
img = Image.new('RGB', (640, 480), color='red')
buffer = io.BytesIO()
img.save(buffer, format='PNG')
image_data = buffer.getvalue()

# Upload
print("Uploading image...")
files = {'image': ('test.png', image_data, 'image/png')}
r = requests.post('http://localhost:5000/upload', files=files)
filename = r.json()['filename']

# Compress
print("Compressing...")
r = requests.post('http://localhost:5000/compress', json={'filename': filename, 'quality': 'high'})
session_id = r.json()['session_id']
print(f"Session ID: {session_id}")

# Decompress
print("Decompressing...")
r = requests.get(f'http://localhost:5000/decompress/{session_id}')
print(f"Decompress status: {r.status_code}")
if r.status_code == 200:
    result = r.json()
    print(f"Success: {result['success']}")
    print(f"Width: {result['width']}, Height: {result['height']}")
    print(f"Quality: {result['quality']}")
    print(f"Image data length: {len(result['image_data'])}")
    
    # Check if it's valid base64
    if result['image_data'].startswith('data:image/png;base64,'):
        print("✓ Image data is valid PNG base64!")
        # Try to decode it
        base64_str = result['image_data'].replace('data:image/png;base64,', '')
        try:
            img_bytes = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(img_bytes))
            print(f"✓ Successfully decoded image: {img.size} {img.mode}")
        except Exception as e:
            print(f"✗ Error decoding image: {e}")
    else:
        print("✗ Image data format unexpected")
else:
    print(f"Error: {r.text}")
