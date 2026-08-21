# Compilation du décodeur C hcv2_decoder

## Prérequis

- **zlib** : bibliothèque de compression (incluse dans MSVC, ou `libz-dev` sous Linux)
- **Compilateur C** : MSVC, GCC, Clang, ou Emscripten

## Instructions

### Windows — MSVC (Visual Studio 2022)

1. Ouvrir **Developer Command Prompt for VS 2022** (Démarrer → Visual Studio 2022 → Developer Command Prompt)
2. Se placer dans le dossier :
   ```
   cd E:\SAAS - Copie\engine\multimodal
   ```
3. Compiler :
   ```
   cl /O2 /LD hcv2_decoder.c /Fehcv2_decoder.dll /link zlib.lib
   ```

### Linux — GCC
```
cd engine/multimodal
gcc -O2 -shared -fPIC -o libhcv2_decoder.so hcv2_decoder.c -lz -lm
```

### WebAssembly — Emscripten
```
emcc -O2 -s WASM=1 -s EXPORTED_FUNCTIONS='[_hc_decode]' \
     -o hcv2_decoder.wasm hcv2_decoder.c
```

## Test avec Python (ctypes)
```python
import ctypes, numpy as np
lib = ctypes.CDLL('./hcv2_decoder.dll')
lib.hc_decode.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                          ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
lib.hc_decode.restype = ctypes.c_int

with open('photo.hcv2', 'rb') as f:
    blob = f.read()
out_w, out_h = ctypes.c_uint32(), ctypes.c_uint32()
out_buf = ctypes.create_string_buffer(100 * 1024 * 1024)  # 100 MB max
ret = lib.hc_decode(blob, len(blob), out_buf, ctypes.byref(out_w), ctypes.byref(out_h))
img = np.frombuffer(out_buf, dtype=np.uint8).reshape(out_h.value, out_w.value, 3)
```