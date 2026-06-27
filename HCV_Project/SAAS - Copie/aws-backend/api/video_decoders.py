#!/usr/bin/env python3
"""
Video Decoders for H264, H265, SDI 4:2:2, and YUV formats
Converts to RGB uint16 for HCV16 processing
"""

import cv2
import numpy as np
import struct
import os
from pathlib import Path


class H264Decoder:
    """Decode H264/H265 video files to RGB frames"""
    
    @staticmethod
    def decode(input_path, target_fps=None):
        """
        Decode H264/H265 video to RGB uint16 frames
        
        Args:
            input_path: Path to H264/H265 file
            target_fps: Optional target FPS (for resampling)
            
        Returns:
            frames: List of RGB uint16 arrays (H, W, 3)
            fps_num, fps_den: Frame rate
            width, height: Video dimensions
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open H264/H265 file: {input_path}")
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Parse FPS as fraction
        fps_num = int(fps * 1000)
        fps_den = 1000
        from math import gcd
        g = gcd(fps_num, fps_den)
        fps_num //= g
        fps_den //= g
        
        frames = []
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # OpenCV reads as BGR uint8, convert to RGB uint16
            # Upscale to 12-bit range (0-4095) for broadcast compatibility
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_uint16 = rgb.astype(np.uint16) << 4  # 8-bit → 12-bit
            
            frames.append(rgb_uint16)
            frame_idx += 1
        
        cap.release()
        
        if not frames:
            raise ValueError(f"No frames decoded from {input_path}")
        
        return frames, fps_num, fps_den, width, height


class SDI422Decoder:
    """Decode SDI 4:2:2 YUV data to RGB frames"""
    
    @staticmethod
    def decode_raw_sdi(input_path, width, height, fps=25, bit_depth=10):
        """
        Decode raw SDI 4:2:2 YUV data
        
        SDI 4:2:2 format: Y0 Cb Y1 Cr (10-bit packed)
        Each pixel pair: 5 bytes = 40 bits = 2×10-bit Y + 10-bit Cb + 10-bit Cr
        
        Args:
            input_path: Path to raw SDI file
            width: Frame width (must be even)
            height: Frame height
            fps: Frames per second
            bit_depth: 10 or 12 bits
            
        Returns:
            frames: List of RGB uint16 arrays
            fps_num, fps_den: Frame rate
        """
        if width % 2 != 0:
            raise ValueError("SDI 4:2:2 width must be even")
        
        file_size = os.path.getsize(input_path)
        
        # Calculate frame size in bytes
        # 4:2:2 = 2 bytes Y per pixel + 1 byte Cb + 1 byte Cr = 4 bytes per 2 pixels
        bytes_per_frame = (width * height * 2)  # YUV 4:2:2
        
        num_frames = file_size // bytes_per_frame
        if num_frames == 0:
            raise ValueError(f"File too small for {width}x{height} SDI frames")
        
        frames = []
        
        with open(input_path, 'rb') as f:
            for frame_idx in range(num_frames):
                # Read YUV 4:2:2 data
                yuv_data = f.read(bytes_per_frame)
                if len(yuv_data) < bytes_per_frame:
                    break
                
                # Unpack YUV 4:2:2
                frame_yuv = SDI422Decoder._unpack_yuv422(yuv_data, width, height, bit_depth)
                
                # Convert YUV to RGB
                frame_rgb = SDI422Decoder._yuv_to_rgb(frame_yuv, bit_depth)
                
                frames.append(frame_rgb)
        
        fps_num = int(fps * 1000)
        fps_den = 1000
        from math import gcd
        g = gcd(fps_num, fps_den)
        fps_num //= g
        fps_den //= g
        
        return frames, fps_num, fps_den, width, height
    
    @staticmethod
    def _unpack_yuv422(data, width, height, bit_depth=10):
        """Unpack YUV 4:2:2 packed data to separate Y, U, V planes"""
        
        if bit_depth == 10:
            # 10-bit packed: 4 pixels = 5 bytes
            # Y0 Y1 Y2 Y3 Cb0 Cr0 Cb2 Cr2
            frame = np.zeros((height, width, 3), dtype=np.uint16)
            
            data_array = np.frombuffer(data, dtype=np.uint8)
            
            for y in range(height):
                for x in range(0, width, 4):
                    # Read 5 bytes for 4 pixels
                    idx = (y * width + x) // 4 * 5
                    if idx + 5 > len(data_array):
                        break
                    
                    b0, b1, b2, b3, b4 = data_array[idx:idx+5]
                    
                    # Unpack 10-bit values
                    y0 = ((b0 << 2) | (b1 >> 6)) & 0x3FF
                    y1 = ((b1 << 4) | (b2 >> 4)) & 0x3FF
                    y2 = ((b2 << 6) | (b3 >> 2)) & 0x3FF
                    y3 = ((b3 << 8) | b4) & 0x3FF
                    
                    cb = ((b1 >> 4) & 0x3) | ((b2 & 0xF) << 2)
                    cr = ((b3 & 0x3) << 8) | b4
                    
                    # Upscale to 12-bit
                    frame[y, x, 0] = y0 << 2
                    frame[y, x, 1] = cb << 2
                    frame[y, x, 2] = cr << 2
                    
                    if x + 1 < width:
                        frame[y, x+1, 0] = y1 << 2
                        frame[y, x+1, 1] = cb << 2
                        frame[y, x+1, 2] = cr << 2
                    
                    if x + 2 < width:
                        frame[y, x+2, 0] = y2 << 2
                        frame[y, x+2, 1] = cb << 2
                        frame[y, x+2, 2] = cr << 2
                    
                    if x + 3 < width:
                        frame[y, x+3, 0] = y3 << 2
                        frame[y, x+3, 1] = cb << 2
                        frame[y, x+3, 2] = cr << 2
        
        elif bit_depth == 12:
            # 12-bit: 2 pixels = 3 bytes
            frame = np.zeros((height, width, 3), dtype=np.uint16)
            data_array = np.frombuffer(data, dtype=np.uint8)
            
            for y in range(height):
                for x in range(0, width, 2):
                    idx = (y * width + x) // 2 * 3
                    if idx + 3 > len(data_array):
                        break
                    
                    b0, b1, b2 = data_array[idx:idx+3]
                    
                    y0 = (b0 << 4) | (b1 >> 4)
                    y1 = ((b1 & 0xF) << 8) | b2
                    cb = (b1 >> 2) & 0x3FF
                    cr = ((b2 & 0x3) << 8) | b0
                    
                    frame[y, x, 0] = y0
                    frame[y, x, 1] = cb
                    frame[y, x, 2] = cr
                    
                    if x + 1 < width:
                        frame[y, x+1, 0] = y1
                        frame[y, x+1, 1] = cb
                        frame[y, x+1, 2] = cr
        
        return frame
    
    @staticmethod
    def _yuv_to_rgb(yuv_frame, bit_depth=10):
        """Convert YUV 4:2:2 to RGB using BT.709 color space"""
        
        # BT.709 conversion matrix (for 10/12-bit)
        # Y' = 0.2126*R + 0.7152*G + 0.0722*B
        # Cb = -0.1146*R - 0.3854*G + 0.5*B + 0.5
        # Cr = 0.5*R - 0.4542*G - 0.0458*B + 0.5
        
        maxval = (1 << bit_depth) - 1
        
        # Inverse matrix (YUV → RGB)
        y = yuv_frame[:, :, 0].astype(np.float32)
        cb = yuv_frame[:, :, 1].astype(np.float32)
        cr = yuv_frame[:, :, 2].astype(np.float32)
        
        # Normalize to [-0.5, 0.5]
        cb = (cb / maxval) - 0.5
        cr = (cr / maxval) - 0.5
        y = y / maxval
        
        # BT.709 inverse
        r = y + 1.5748 * cr
        g = y - 0.1873 * cb - 0.4681 * cr
        b = y + 1.8556 * cb
        
        # Clip and scale back
        rgb = np.stack([r, g, b], axis=2)
        rgb = np.clip(rgb * maxval, 0, maxval).astype(np.uint16)
        
        return rgb


class YUVDecoder:
    """Decode raw YUV files (I420, NV12, YUV422, etc.)"""
    
    @staticmethod
    def decode_i420(input_path, width, height, fps=25):
        """Decode I420 (YUV 4:2:0) raw video"""
        
        frame_size = width * height * 3 // 2  # Y + U + V
        file_size = os.path.getsize(input_path)
        num_frames = file_size // frame_size
        
        frames = []
        
        with open(input_path, 'rb') as f:
            for _ in range(num_frames):
                # Read Y plane
                y_data = np.frombuffer(f.read(width * height), dtype=np.uint8)
                y_plane = y_data.reshape((height, width))
                
                # Read U plane (half resolution)
                u_data = np.frombuffer(f.read(width * height // 4), dtype=np.uint8)
                u_plane = u_data.reshape((height // 2, width // 2))
                
                # Read V plane
                v_data = np.frombuffer(f.read(width * height // 4), dtype=np.uint8)
                v_plane = v_data.reshape((height // 2, width // 2))
                
                # Upsample U and V to full resolution
                u_full = cv2.resize(u_plane, (width, height), interpolation=cv2.INTER_LINEAR)
                v_full = cv2.resize(v_plane, (width, height), interpolation=cv2.INTER_LINEAR)
                
                # Convert YUV to RGB
                yuv = np.stack([y_plane, u_full, v_full], axis=2)
                rgb = cv2.cvtColor(yuv.astype(np.uint8), cv2.COLOR_YUV2RGB)
                
                # Upscale to 12-bit
                rgb_uint16 = rgb.astype(np.uint16) << 4
                frames.append(rgb_uint16)
        
        fps_num = int(fps * 1000)
        fps_den = 1000
        from math import gcd
        g = gcd(fps_num, fps_den)
        fps_num //= g
        fps_den //= g
        
        return frames, fps_num, fps_den, width, height


def detect_and_decode(input_path, **kwargs):
    """
    Auto-detect format and decode video
    
    Args:
        input_path: Path to video file
        **kwargs: Format-specific parameters (width, height, fps, bit_depth)
        
    Returns:
        frames, fps_num, fps_den, width, height
    """
    ext = Path(input_path).suffix.lower()
    
    if ext in ['.h264', '.h265', '.hevc', '.mp4', '.mov', '.avi', '.ts', '.mxf']:
        return H264Decoder.decode(input_path, kwargs.get('target_fps'))
    
    elif ext == '.sdi':
        width = kwargs.get('width', 1920)
        height = kwargs.get('height', 1080)
        fps = kwargs.get('fps', 25)
        bit_depth = kwargs.get('bit_depth', 10)
        return SDI422Decoder.decode_raw_sdi(input_path, width, height, fps, bit_depth)
    
    elif ext == '.yuv':
        width = kwargs.get('width', 1920)
        height = kwargs.get('height', 1080)
        fps = kwargs.get('fps', 25)
        return YUVDecoder.decode_i420(input_path, width, height, fps)
    
    else:
        raise ValueError(f"Unsupported format: {ext}")
