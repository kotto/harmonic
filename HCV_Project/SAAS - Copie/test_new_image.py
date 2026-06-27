#!/usr/bin/env python3
"""
Test with a new image
"""
import requests
import json
from PIL import Image, ImageDraw
import io
import struct

# Create a test image with some content
img = Image.new('RGB', (320, 240), color='blue')
draw = ImageDraw.Draw(img)
draw.rectangle([50, 50, 270, 190], fill='red')
draw.text((100, 100), "TEST", fill='white')

buffer = io.BytesIO()
img.save(buffer, format='PNG')
image_data = buffer.getvalue()

# Upload
print("Uploading image...")
files = {'image': ('test_new.png', image_data, 'image/png')}
r = requests.post('http://localhost:5000/upload', files=files)
filename = r.json()['filename']
print(f"Uploaded: {filename}")

# Compress
print("Compressing...")
r = requests.post('http://localhost:5000/compress', json={'filename': filename, 'quality': 'medium'})
result = r.json()
session_id = result['session_id']
compressed_filename = result['metrics']['output_file']
print(f"Compressed: {compressed_filename}")

# Check file size
import os
file_size = os.path.getsize(compressed_filename)
print(f"File size: {file_size} bytes")

# Check PNG size
with open(compressed_filename, 'rb') as f:
    f.seek(0, 2)
    size = f.tell()
    f.seek(size - 4)
    png_size_bytes = f.read(4)
    if len(png_size_bytes) == 4:
        png_size = struct.unpack('<I', png_size_bytes)[0]
        print(f"PNG size from file: {png_size} bytes")
        if png_size > 100 and png_size < 10 * 1024 * 1024:
            print(f"✓ PNG size looks valid!")
        else:
            print(f"✗ PNG size looks invalid")
    else:
        print("✗ Could not read PNG size")

# Decompress
print("\nDecompressing...")
r = requests.get(f'http://localhost:5000/decompress/{session_id}')
if r.status_code == 200:
    result = r.json()
    print(f"✓ Decompression successful")
    print(f"  Image size: {result['width']}x{result['height']}")
else:
    print(f"✗ Decompression failed: {r.status_code}")
