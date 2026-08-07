"""Enregistrement rapide — voix de ChatGPT via micro."""
import sounddevice as sd
import numpy as np
import wave, os, time

OUTPUT = os.path.join(os.path.dirname(__file__), "output", "voix_chatgpt.wav")
SR = 44100
DURATION = 90

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
n_samples = int(DURATION * SR)
buf = np.zeros((n_samples, 1), dtype='float32')
pos = [0]

def cb(indata, frames, time_info, status):
    rem = n_samples - pos[0]
    n = min(frames, rem)
    if n > 0:
        buf[pos[0]:pos[0]+n, 0] = indata[:n, 0]
        pos[0] += n
    if pos[0] >= n_samples:
        raise sd.CallbackStop()

print("RECORDING ChatGPT - 90s - Lance le mode vocal !")
print()

stream = sd.InputStream(device=1, channels=1, samplerate=SR, callback=cb, dtype='float32')
with stream:
    for i in range(90):
        elapsed = i + 1
        pct = elapsed / 90 * 100
        status = "PARLE" if elapsed < 85 else "FIN"
        bar_len = 30
        filled = int(bar_len * elapsed / 90)
        bar = "|" + "=" * filled + "." * (bar_len - filled) + "|"
        print(f"\r{bar} {pct:5.1f}% {elapsed}s {status}   ", end="", flush=True)
        time.sleep(1)
        if pos[0] >= n_samples:
            break

print()
audio = buf[:pos[0], 0]
peak = max(0.0001, float(np.max(np.abs(audio))))
audio = audio / peak * 0.95
pcm = (audio * 32767).astype('<i2')
with wave.open(OUTPUT, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())

dur = len(audio) / SR
mb = os.path.getsize(OUTPUT) / 1024 / 1024
print(f"OK {dur:.1f}s {mb:.2f}MB {OUTPUT}")
