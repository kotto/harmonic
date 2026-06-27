#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

# Utiliser une vraie video (pas fake_video.mp4 qui fait 15 octets!)
video_path = 'f:/FINAL/DEFINITIF/hcs_v2-P3/test_1080p_video.mp4'

print("=== Test Video Upscale Endpoint (avec vraie video) ===")
print("Fichier: " + video_path)

# Test avec scale_factor "2" (numerique, comme le frontend envoie maintenant)
print("\n[Test] scale_factor='2', temporal_coherence='true'")
try:
    with open(video_path, 'rb') as f:
        files = {'file': ('test_1080p_video.mp4', f, 'video/mp4')}
        data = {
            'scale_factor': '2',
            'energy_level': 'standard',
            'temporal_coherence': 'true'
        }
        response = requests.post('http://localhost:8009/api/v2/upscale/video-reference',
                                 files=files, data=data, timeout=120)
    print("  HTTP Status: " + str(response.status_code))
    result = response.json()
    print("  Success: " + str(result.get('success')))
    print("  scale_factor: " + str(result.get('scale_factor')))
    print("  original_resolution: " + str(result.get('original_resolution')))
    print("  target_resolution: " + str(result.get('target_resolution')))
    print("  total_frames: " + str(result.get('total_frames')))
    print("  processing_time: " + str(round(result.get('total_processing_time', 0), 2)) + "s")
    print("  temporal_coherence: " + str(result.get('temporal_coherence_enabled')))
    print("  output_mime: " + str(result.get('output_mime_type')))
    has_video = bool(result.get('upscaled_video_base64'))
    print("  Video base64 presente: " + str(has_video))
    if has_video:
        size_kb = len(result['upscaled_video_base64']) * 3 / 4 / 1024
        print("  Taille video upscalee: " + str(round(size_kb, 1)) + " KB")
        print("  file_size_mb: " + str(round(result.get('file_size_mb', 0), 2)) + " MB")
    if not result.get('success'):
        print("  ERREUR: " + str(result.get('detail', result.get('error', 'inconnue'))))

except Exception as e:
    print("  EXCEPTION: " + str(e))

print("\n=== Verification des codecs disponibles ===")
import cv2
fourcc_tests = [
    ('XVID', '.avi'), ('mp4v', '.mp4'), ('MJPG', '.avi'), ('avc1', '.mp4')
]
import tempfile, os
for codec, ext in fourcc_tests:
    try:
        tmp = tempfile.mktemp(suffix=ext)
        fourcc = cv2.VideoWriter_fourcc(*codec)
        w = cv2.VideoWriter(tmp, fourcc, 30, (320, 240))
        ok = w.isOpened()
        w.release()
        if os.path.exists(tmp):
            size = os.path.getsize(tmp)
            os.remove(tmp)
        else:
            size = 0
        print("  " + codec + " (" + ext + "): isOpened=" + str(ok) + " size=" + str(size))
    except Exception as e:
        print("  " + codec + ": ERREUR " + str(e))
