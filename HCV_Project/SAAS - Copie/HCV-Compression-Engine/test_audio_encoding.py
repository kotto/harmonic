#!/usr/bin/env python3
"""Test audio encoding in video files."""

import subprocess
import os
import sys
from pathlib import Path

def check_audio_in_file(filepath):
    """Check if a video file has audio tracks."""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=codec_type,codec_name,sample_rate,channels',
        '-of', 'default=noprint_wrappers=1:nokey=1:nokey=1',
        filepath
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            print(f"✓ Audio found in {filepath}:")
            print(f"  {result.stdout.strip()}")
            return True
        else:
            print(f"❌ No audio in {filepath}")
            return False
    except Exception as e:
        print(f"❌ Error checking audio: {e}")
        return False

def test_encode_with_audio():
    """Test encoding a video with audio preservation."""
    # Create a simple test video with audio using ffmpeg
    test_input = "/tmp/test_input.mp4"
    test_output = "/tmp/test_output.mp4"
    
    print("Creating test video with audio...")
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'color=c=blue:s=320x240:d=2',
        '-f', 'lavfi', '-i', 'sine=f=1000:d=2',
        '-pix_fmt', 'yuv420p',
        test_input
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        print(f"❌ Failed to create test video: {result.stderr[-200:]}")
        return
    
    print(f"✓ Test video created: {test_input}")
    check_audio_in_file(test_input)
    
    # Now test encoding with audio preservation
    print("\nTesting audio preservation with AAC...")
    cmd = [
        'ffmpeg', '-y', '-i', test_input,
        '-vf', 'scale=160:120:flags=lanczos',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        test_output
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"❌ Encoding failed: {result.stderr[-200:]}")
        return
    
    print(f"✓ Encoding completed")
    check_audio_in_file(test_output)
    
    # Cleanup
    try:
        os.unlink(test_input)
        os.unlink(test_output)
    except:
        pass

if __name__ == '__main__':
    print("=== Audio Encoding Test ===\n")
    test_encode_with_audio()
