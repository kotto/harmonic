#!/usr/bin/env python3
"""
Download Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf (17.9GB)
Complete download for S3 transfer and AWS deployment
"""

import os
import requests
from pathlib import Path
import sys
from tqdm import tqdm

def download_qwen35():
    """Download complete Qwen3.5 model file"""
    
    # Configuration
    model_name = "Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf"
    target_dir = Path("E:/QWEN35_DEEPSEEK_TEST/models/")
    target_file = target_dir / model_name
    
    # HuggingFace URL
    base_url = "https://huggingface.co/Jackrong/Qwen3.5-9B-DeepSeek-V4-Flash-GGUF/resolve/main"
    model_url = f"{base_url}/{model_name}"
    
    # Expected file size (17.9GB)
    expected_size = 17.9 * 1024 * 1024 * 1024  # bytes
    
    print(f"🎯 Downloading: {model_name}")
    print(f"📁 Target: {target_file}")
    print(f"📊 Expected size: {expected_size / (1024**3):.1f} GB")
    print(f"🌐 Source: {model_url}")
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if file already exists and is complete
    if target_file.exists():
        current_size = target_file.stat().st_size
        print(f"📋 File exists: {current_size / (1024**3):.1f} GB")
        
        if current_size >= expected_size * 0.99:  # Allow 1% tolerance
            print("✅ File appears complete!")
            return str(target_file)
        else:
            print(f"⚠️  File incomplete: {current_size / (1024**3):.1f} GB / {expected_size / (1024**3):.1f} GB")
            
            # Check if we can resume
            if current_size > 0:
                print("🔄 Attempting resume download...")
                headers = {'Range': f'bytes={current_size}-'}
                mode = 'ab'
            else:
                print("🔄 Starting fresh download...")
                headers = {}
                mode = 'wb'
    else:
        print("🔄 Starting fresh download...")
        headers = {}
        mode = 'wb'
        current_size = 0
    
    try:
        # Start download with progress bar
        response = requests.get(model_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Get total size for progress bar
        total_size = int(response.headers.get('content-length', 0))
        if 'Range' in headers:
            total_size += current_size
        
        print(f"📊 Total size: {total_size / (1024**3):.1f} GB")
        
        # Download with progress
        with open(target_file, mode) as f:
            with tqdm(
                initial=current_size,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc=model_name[:20]
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        # Verify download
        final_size = target_file.stat().st_size
        print(f"\n📊 Downloaded: {final_size / (1024**3):.1f} GB")
        
        if final_size >= expected_size * 0.99:
            print("✅ Download completed successfully!")
            return str(target_file)
        else:
            print(f"❌ Download incomplete: {final_size / (1024**3):.1f} GB / {expected_size / (1024**3):.1f} GB")
            return None
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Qwen3.5 Complete Downloader")
    print("=" * 50)
    
    result = download_qwen35()
    
    if result:
        print(f"\n✅ SUCCESS: {result}")
        print("🎯 Ready for S3 transfer!")
    else:
        print("\n❌ FAILED: Download incomplete")
        sys.exit(1)
