# Build du plugin FFmpeg HCV2 Decoder

## Compilation

### Linux (gcc)
```bash
cd plugins/
gcc -O2 -DBUILD_CLI -o ff_hcv2dec ff_hcv2dec.c -lz -lm
./ff_hcv2dec input.hcv2 output.ppm
```

### Windows (MSVC)
```cmd
cd plugins\
cl /O2 /DBUILD_CLI ff_hcv2dec.c /link zlib.lib
ff_hcv2dec.exe input.hcv2 output.ppm
```

### WebAssembly (Emscripten)
```bash
cd plugins/
emcc -O2 -DBUILD_CLI -s USE_ZLIB=1 -o ff_hcv2dec.js ff_hcv2dec.c
```

## Intégration FFmpeg

Copier le binaire dans le PATH :
```bash
sudo cp ff_hcv2dec /usr/local/bin/
```

Utiliser dans un pipeline FFmpeg via `ffmpeg -i` :
```bash
# Décoder un .hcv2 en image
ffmpeg -i input.hcv2 output.png

# Décoder en vidéo
ffmpeg -i input.hcv2 -c:v libx264 output.mp4

# Décoder en DPX (pour pipeline pro)
ffmpeg -i input.hcv2 frame_%04d.dpx

# Concaténer des frames .hcv2 en vidéo
ffmpeg -f concat -i <(for f in segments/*.hcv2; do echo "file $f"; done) -c:v libx264 output.mp4
```

## Intégration DaVinci Resolve

**Via script** : DaVinci Resolve peut exécuter des scripts Python qui appellent `ff_hcv2dec` :
```python
# resolve_hcv2.py — DaVinci Resolve script
import subprocess, sys
subprocess.run(['ff_hcv2dec', sys.argv[1], sys.argv[2]])
```

**Via FFmpeg** : Resolve supporte FFmpeg comme moteur de transcodage :
- `File → Media Management → Transcode → Custom → hcv2`

## Intégration Premiere Pro

**Via Adobe Media Encoder** : peut appeler des scripts externes via `After Effects` → `Render Queue` → `Output Module` → `Post-Render Action` → `Execute Command`.

**Via FFmpeg** : `File → Import → hcv2` (après association de l'extension à FFmpeg).

## Intégration Avid Media Composer

**Via commande** : `Tools → Console → rescan` + `Import → hcv2`.

**Via FFmpeg** : Avid accepte les fichiers MXF générés par FFmpeg :
```bash
ffmpeg -i input.hcv2 -c:v dnxhd -b:v 36M -pix_fmt yuv422p output.mxf
```

## Tests

```bash
# Tester le décodeur CLI
./ff_hcv2dec test.hcv2 test.ppm
identify test.ppm  # ImageMagick

# Tester le pipeline FFmpeg
ffmpeg -i test.hcv2 test.png
ffprobe test.hcv2  # Informations

# Tester des fichiers corrompus
./ff_hcv2dec /dev/random test.ppm  # doit échouer proprement
```