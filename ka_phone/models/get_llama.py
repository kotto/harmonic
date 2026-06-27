#!/usr/bin/env python3
"""Télécharge et extrait llama-server.exe pour servir le modèle Phi-3-mini via API HTTP."""
import requests, zipfile, io, os, shutil

os.chdir(os.path.dirname(__file__))

URL = 'https://github.com/ggerganov/llama.cpp/releases/download/b9581/llama-b9581-bin-win-cpu-x64.zip'
print(f"Downloading {URL}...")
r = requests.get(URL, timeout=120)
z = zipfile.ZipFile(io.BytesIO(r.content))
print(f"Downloaded {len(r.content)/1024/1024:.0f} Mo\n")

# Extraire llama-server.exe (API HTTP) ET llama-cli.exe (CLI)
for target in ['llama-server.exe', 'llama-cli.exe']:
    for f in z.filelist:
        if os.path.basename(f.filename).lower() == target.lower():
            data = z.read(f)
            with open(target, 'wb') as out:
                out.write(data)
            size_mb = len(data) / 1024 / 1024
            print(f"Extracted: {target} ({size_mb:.1f} Mo)")
            break

# Vérifier
for f in ['llama-server.exe', 'llama-cli.exe']:
    if os.path.exists(f):
        print(f"  ✅ {f}")
    else:
        print(f"  ❌ {f} NOT FOUND")