import os

files_to_fix = [
    r'f:\FINAL\DEFINITIF\hcs_v2-P3\android\app\src\main\java\com\hcs\harmonic\service\HCSVideoProcessor.java',
]

for path in files_to_fix:
    with open(path, 'rb') as f:
        raw = f.read()
    
    print(f"File: {os.path.basename(path)}")
    print(f"First 6 bytes: {raw[:6].hex()}")
    
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
        print("BOM stripped!")
    elif raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
        # UTF-16 BOM - decode and re-encode to UTF-8
        text = raw.decode('utf-16')
        raw = text.encode('utf-8')
        print("UTF-16 BOM stripped and converted to UTF-8!")
    else:
        print("No BOM found, but replacing anyway...")
    
    with open(path, 'wb') as f:
        f.write(raw)
    
    print(f"Saved OK, size: {len(raw)} bytes")
    print(f"First 6 bytes after: {raw[:6].hex()}")
