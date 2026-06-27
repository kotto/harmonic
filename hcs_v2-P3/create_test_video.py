#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import cv2
import numpy as np
import requests
import os

# Creer une video test de 5 secondes (150 frames a 30fps)
output_path = 'test_video_5s.mp4'
fps = 30
total_frames = 150  # 5 secondes
width, height = 640, 360

print("Creation video test 5s (" + str(total_frames) + " frames, " + str(width) + "x" + str(height) + ")...")
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(output_path.replace('.mp4', '.avi'), fourcc, fps, (width, height))

for i in range(total_frames):
    # Frame avec progression de couleur (rouge vers bleu)
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    progress = i / total_frames
    frame[:, :, 2] = int(255 * progress)       # Rouge augmente
    frame[:, :, 0] = int(255 * (1 - progress)) # Bleu diminue
    frame[:, :, 1] = int(128 * np.sin(i * 0.1) + 128)  # Vert oscille
    
    # Numero de frame en texte
    cv2.putText(frame, 'Frame ' + str(i+1) + '/' + str(total_frames), 
                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, 'HCS V2 TEST', 
                (20, height-30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    out.write(frame)

out.release()
avi_path = output_path.replace('.mp4', '.avi')
print("Video creee: " + avi_path)

# Verifier les proprietes
cap = cv2.VideoCapture(avi_path)
fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps_check = cap.get(cv2.CAP_PROP_FPS)
cap.release()
size_kb = os.path.getsize(avi_path) / 1024
print("Verification: " + str(fc) + " frames, " + str(fps_check) + " fps, " + str(round(size_kb,1)) + " KB")

# Tester l'upscale avec cette video
print("\n=== Test Upscale (toutes les frames) ===")
with open(avi_path, 'rb') as f:
    files = {'file': ('test_video_5s.avi', f, 'video/avi')}
    data = {'scale_factor': '2', 'energy_level': 'standard', 'temporal_coherence': 'true'}
    response = requests.post('http://localhost:8009/api/v2/upscale/video-reference',
                             files=files, data=data, timeout=120)

result = response.json()
print("HTTP Status: " + str(response.status_code))
print("Success: " + str(result.get('success')))
print("total_frames traites: " + str(result.get('total_frames')))
print("original: " + str(result.get('original_resolution')))
print("target: " + str(result.get('target_resolution')))
print("processing_time: " + str(round(result.get('total_processing_time', 0), 2)) + "s")

if result.get('total_frames') == total_frames:
    print("\n>>> SUCCES: TOUTES LES " + str(total_frames) + " FRAMES ONT ETE TRAITEES <<<")
elif result.get('success'):
    processed = result.get('total_frames', 0)
    print("\n>>> ATTENTION: " + str(processed) + "/" + str(total_frames) + " frames traitees <<<")
else:
    print("\n>>> ERREUR: " + str(result.get('detail', 'inconnue')))

# Nettoyer
os.remove(avi_path)
