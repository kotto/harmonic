#!/usr/bin/env python3
"""
Test script for METHOD_2 compression workflow
"""
import requests
import json
import base64
from PIL import Image
import numpy as np
import io

# Create a simple test image
def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (640, 480), color='red')
    # Add some pattern
    pixels = img.load()
    for i in range(640):
        for j in range(480):
            pixels[i, j] = (i % 256, j % 256, (i + j) % 256)
    
    # Save to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

# Test the workflow
def test_workflow():
    base_url = 'http://localhost:5000'
    
    # Create test image
    print("Creating test image...")
    image_data = create_test_image()
    
    # Upload image
    print("Uploading image...")
    files = {'image': ('test_image.png', image_data, 'image/png')}
    response = requests.post(f'{base_url}/upload', files=files)
    
    if response.status_code != 200:
        print(f"Upload failed: {response.status_code}")
        print(response.text)
        return
    
    upload_result = response.json()
    print(f"Upload successful: {json.dumps(upload_result, indent=2)}")
    
    filename = upload_result['filename']
    
    # Compress image
    print("\nCompressing image...")
    compress_data = {
        'filename': filename,
        'quality': 'high'
    }
    response = requests.post(f'{base_url}/compress', json=compress_data)
    
    if response.status_code != 200:
        print(f"Compression failed: {response.status_code}")
        print(response.text)
        return
    
    compress_result = response.json()
    print(f"Compression successful: {json.dumps(compress_result, indent=2)}")
    
    session_id = compress_result['session_id']
    
    # Decompress image
    print("\nDecompressing image...")
    response = requests.get(f'{base_url}/decompress/{session_id}')
    
    if response.status_code != 200:
        print(f"Decompression failed: {response.status_code}")
        print(response.text)
        return
    
    decompress_result = response.json()
    print(f"Decompression successful!")
    print(f"  Width: {decompress_result['width']}")
    print(f"  Height: {decompress_result['height']}")
    print(f"  Quality: {decompress_result['quality']}")
    print(f"  Image data length: {len(decompress_result['image_data'])}")
    
    # Check if image data is valid
    if decompress_result['image_data'].startswith('data:image/png;base64,'):
        print("  Image data is valid PNG base64!")
    else:
        print("  WARNING: Image data format unexpected")

if __name__ == '__main__':
    test_workflow()
