
#!/usr/bin/env python3
"""
Script simple d'obfuscation Python
"""

import base64
import zlib

def obfuscate_code(input_file, output_file):
    """Obfusque un fichier Python"""
    with open(input_file, 'r') as f:
        code = f.read()
    
    # Compresser le code
    compressed = zlib.compress(code.encode())
    b64_compressed = base64.b64encode(compressed).decode()
    
    # Générer le code obfusqué
    obfuscated = f"""
import zlib
import base64
import types

# Code compressé et encodé
compressed_code = "{b64_compressed}"

# Fonction de décompression
def _execute():
    code_bytes = base64.b64decode(compressed_code)
    code_str = zlib.decompress(code_bytes).decode()
    exec(code_str)

if __name__ == "__main__":
    _execute()
"""
    
    with open(output_file, 'w') as f:
        f.write(obfuscated)
    
    print(f"Fichier obfusqué: {input_file} -> {output_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python simple_obfuscator.py <input.py> <output.py>")
        sys.exit(1)
    
    obfuscate_code(sys.argv[1], sys.argv[2])
