#!/usr/bin/env python3
"""
Test suite for H264, H265, SDI 4:2:2, and YUV support
Validates all decoders and the complete pipeline
"""

import sys
import os
import tempfile
import numpy as np
import cv2
from pathlib import Path

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

try:
    from video_decoders import H264Decoder, SDI422Decoder, YUVDecoder
    print("✓ video_decoders imported successfully")
except ImportError as e:
    print(f"✗ Failed to import video_decoders: {e}")
    sys.exit(1)


def create_test_h264(output_path, width=320, height=240, fps=25, duration=1):
    """Create a test H264 video file"""
    print(f"\n📹 Creating test H264 video: {output_path}")
    
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    num_frames = fps * duration
    for i in range(num_frames):
        # Create a simple test pattern
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add gradient
        for y in range(height):
            frame[y, :] = [
                int(255 * y / height),
                int(255 * (1 - y / height)),
                int(255 * (i / num_frames))
            ]
        
        # Add circle
        cv2.circle(frame, (width//2, height//2), 30, (0, 255, 255), -1)
        
        out.write(frame)
    
    out.release()
    file_size = os.path.getsize(output_path)
    print(f"  ✓ Created: {file_size / 1024:.1f} KB")
    return output_path


def create_test_sdi_422(output_path, width=320, height=240, fps=25, duration=1, bit_depth=10):
    """Create a test SDI 4:2:2 raw file"""
    print(f"\n📡 Creating test SDI 4:2:2 video: {output_path}")
    
    num_frames = fps * duration
    frame_size = width * height * 2  # YUV 4:2:2
    
    with open(output_path, 'wb') as f:
        for frame_idx in range(num_frames):
            # Create YUV 4:2:2 data
            yuv_data = np.zeros((height, width, 2), dtype=np.uint8)
            
            # Y plane (luminance)
            for y in range(height):
                yuv_data[y, :, 0] = int(255 * y / height)
            
            # Cb/Cr planes (chrominance)
            for y in range(height):
                yuv_data[y, :, 1] = int(128 + 64 * np.sin(2 * np.pi * frame_idx / num_frames))
            
            f.write(yuv_data.tobytes())
    
    file_size = os.path.getsize(output_path)
    print(f"  ✓ Created: {file_size / 1024:.1f} KB")
    return output_path


def create_test_yuv_i420(output_path, width=320, height=240, fps=25, duration=1):
    """Create a test YUV I420 raw file"""
    print(f"\n🎨 Creating test YUV I420 video: {output_path}")
    
    num_frames = fps * duration
    frame_size = width * height * 3 // 2  # I420
    
    with open(output_path, 'wb') as f:
        for frame_idx in range(num_frames):
            # Y plane
            y_plane = np.zeros((height, width), dtype=np.uint8)
            for y in range(height):
                y_plane[y, :] = int(255 * y / height)
            
            # U plane (half resolution)
            u_plane = np.full((height // 2, width // 2), 128, dtype=np.uint8)
            
            # V plane (half resolution)
            v_plane = np.full((height // 2, width // 2), 128, dtype=np.uint8)
            
            f.write(y_plane.tobytes())
            f.write(u_plane.tobytes())
            f.write(v_plane.tobytes())
    
    file_size = os.path.getsize(output_path)
    print(f"  ✓ Created: {file_size / 1024:.1f} KB")
    return output_path


def test_h264_decoder():
    """Test H264 decoder"""
    print("\n" + "="*60)
    print("TEST 1: H264 Decoder")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, 'test.h264')
        create_test_h264(test_file, 320, 240, 25, 1)
        
        try:
            frames, fps_num, fps_den, width, height = H264Decoder.decode(test_file)
            
            print(f"  ✓ Decoded successfully")
            print(f"    - Frames: {len(frames)}")
            print(f"    - Resolution: {width}×{height}")
            print(f"    - FPS: {fps_num}/{fps_den}")
            print(f"    - Frame dtype: {frames[0].dtype}")
            print(f"    - Frame shape: {frames[0].shape}")
            
            # Validate
            assert len(frames) == 25, f"Expected 25 frames, got {len(frames)}"
            assert frames[0].shape == (240, 320, 3), f"Unexpected shape: {frames[0].shape}"
            assert frames[0].dtype == np.uint16, f"Expected uint16, got {frames[0].dtype}"
            
            print("  ✓ All validations passed")
            return True
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_sdi_422_decoder():
    """Test SDI 4:2:2 decoder"""
    print("\n" + "="*60)
    print("TEST 2: SDI 4:2:2 Decoder")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, 'test.sdi')
        create_test_sdi_422(test_file, 320, 240, 25, 1, 10)
        
        try:
            frames, fps_num, fps_den, width, height = SDI422Decoder.decode_raw_sdi(
                test_file, 320, 240, 25, 10
            )
            
            print(f"  ✓ Decoded successfully")
            print(f"    - Frames: {len(frames)}")
            print(f"    - Resolution: {width}×{height}")
            print(f"    - FPS: {fps_num}/{fps_den}")
            print(f"    - Frame dtype: {frames[0].dtype}")
            print(f"    - Frame shape: {frames[0].shape}")
            
            # Validate
            assert len(frames) == 25, f"Expected 25 frames, got {len(frames)}"
            assert frames[0].shape == (240, 320, 3), f"Unexpected shape: {frames[0].shape}"
            assert frames[0].dtype == np.uint16, f"Expected uint16, got {frames[0].dtype}"
            
            print("  ✓ All validations passed")
            return True
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_yuv_decoder():
    """Test YUV I420 decoder"""
    print("\n" + "="*60)
    print("TEST 3: YUV I420 Decoder")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, 'test.yuv')
        create_test_yuv_i420(test_file, 320, 240, 25, 1)
        
        try:
            frames, fps_num, fps_den, width, height = YUVDecoder.decode_i420(
                test_file, 320, 240, 25
            )
            
            print(f"  ✓ Decoded successfully")
            print(f"    - Frames: {len(frames)}")
            print(f"    - Resolution: {width}×{height}")
            print(f"    - FPS: {fps_num}/{fps_den}")
            print(f"    - Frame dtype: {frames[0].dtype}")
            print(f"    - Frame shape: {frames[0].shape}")
            
            # Validate
            assert len(frames) == 25, f"Expected 25 frames, got {len(frames)}"
            assert frames[0].shape == (240, 320, 3), f"Unexpected shape: {frames[0].shape}"
            assert frames[0].dtype == np.uint16, f"Expected uint16, got {frames[0].dtype}"
            
            print("  ✓ All validations passed")
            return True
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_hcv_engine_integration():
    """Test HCV engine integration"""
    print("\n" + "="*60)
    print("TEST 4: HCV Engine Integration")
    print("="*60)
    
    try:
        import json
        import subprocess
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test H264
            input_file = os.path.join(tmpdir, 'test.h264')
            output_file = os.path.join(tmpdir, 'test.hcv16')
            
            create_test_h264(input_file, 320, 240, 25, 1)
            
            # Run HCV engine
            print(f"  Running HCV engine...")
            result = subprocess.run([
                'python3', 'api/hcv_engine.py',
                '--input', input_file,
                '--output', output_file,
                '--mode', 'GRAIN_SYNTH',
                '--fps', '25/1',
                '--bits', '12'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"  ✗ HCV engine failed:")
                print(f"    stdout: {result.stdout}")
                print(f"    stderr: {result.stderr}")
                return False
            
            # Parse output
            try:
                output = json.loads(result.stdout)
                if 'error' in output:
                    print(f"  ✗ Error: {output['error']}")
                    return False
                
                print(f"  ✓ Encoding successful")
                print(f"    - Mode: {output.get('mode')}")
                print(f"    - Ratio: {output.get('ratio')}")
                print(f"    - Frames: {output.get('frames')}")
                print(f"    - File size: {output.get('fileSize')} bytes")
                
                # Validate output file exists
                assert os.path.exists(output_file), "Output file not created"
                print(f"  ✓ Output file created: {os.path.getsize(output_file)} bytes")
                
                return True
                
            except json.JSONDecodeError:
                print(f"  ✗ Failed to parse HCV engine output:")
                print(f"    {result.stdout}")
                return False
                
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("H264, H265, SDI 4:2:2, YUV Support Test Suite")
    print("="*60)
    
    results = {
        "H264 Decoder": test_h264_decoder(),
        "SDI 4:2:2 Decoder": test_sdi_422_decoder(),
        "YUV I420 Decoder": test_yuv_decoder(),
        "HCV Engine Integration": test_hcv_engine_integration(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
