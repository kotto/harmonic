import os
import cv2
from test_hcv_sdi_b3_simd_final_improved import ImprovedHCVSDIB3

print('=== HCV 10 frames ===')
tester = ImprovedHCVSDIB3(max_frames=10, gop_size=1)
results = tester.run()
print('RESULTS:', results)

print('\n=== Direct H264 10 frames ===')
cap = cv2.VideoCapture('B3.mp4')
frames = []
for i in range(10):
    ret, frame = cap.read()
    if not ret:
        break
    frames.append(frame)
cap.release()
print('frames read', len(frames))
if len(frames) == 0:
    raise SystemExit('no frames')

h, w = frames[0].shape[:2]
fourcc = cv2.VideoWriter_fourcc(*'avc1')
out_path = 'tmp_h264_10frames.mp4'
out = cv2.VideoWriter(out_path, fourcc, 25.0, (w, h))
print('writer opened', out.isOpened())
for f in frames:
    out.write(f)
out.release()
if os.path.exists(out_path):
    print('h264 size', os.path.getsize(out_path), 'bytes', os.path.getsize(out_path)/1024/1024, 'MB')
else:
    print('h264 output missing')
