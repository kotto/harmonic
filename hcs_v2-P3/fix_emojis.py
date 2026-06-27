#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corrige les emojis dans core/harmonic_upscaler.py"""
import sys
import os

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

TARGET = r"f:\FINAL\DEFINITIF\hcs_v2-P3\core\harmonic_upscaler.py"

print(f"Lecture: {TARGET}")
with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Taille initiale: {len(content)} chars")

# Comptage avant
orig_count = 0
for c in content:
    if ord(c) > 127:
        orig_count += 1
print(f"Caracteres non-ASCII avant: {orig_count}")

# Remplacement exhaustif de tous les emojis/caracteres speciaux non-ASCII
# par leurs equivalents ASCII
replacements = {
    '\u2705': '[OK]',       # ✅ Check mark
    '\u274c': '[KO]',       # ❌ Cross mark
    '\U0001f680': '>>>',    # 🚀 Rocket
    '\u26a1': '~~',         # ⚡ Lightning
    '\U0001f3a8': '[CLR]',  # 🎨 Artist palette
    '\U0001f3af': '[TGT]',  # 🎯 Bullseye
    '\U0001f4ca': '[STS]',  # 📊 Bar chart
    '\U0001f4f8': '[IMG]',  # 📸 Camera
    '\U0001f9ea': '[TST]',  # 🧪 Test tube
    '\u2192': '->',         # → Arrow right
    '\U0001f4e6': '[PKG]',  # 📦 Package
    '\U0001f4bb': '[PC]',   # 💻 Laptop
    '\U0001f527': '[FIX]',  # 🔧 Wrench
    '\U0001f4dd': '[DOC]',  # 📝 Memo
    '\u2728': '**',         # ✨ Sparkles
    '\U0001f4a1': '[!]',    # 💡 Bulb
    '\U0001f6a8': '[!]',    # 🚨 Siren
    '\u26a0': '[WARN]',     # ⚠ Warning
    '\U0001f501': '[LOOP]', # 🔁 Repeat
    '\U0001f4c8': '[UP]',   # 📈 Chart up
    '\U0001f525': '[HOT]',  # 🔥 Fire
}

count = 0
for emoji, rep in replacements.items():
    n = content.count(emoji)
    if n > 0:
        print(f"  {repr(emoji)} -> '{rep}' ({n}x)")
        content = content.replace(emoji, rep)
        count += n

print(f"Total remplacements: {count}")

# Verification finale: aucun caractere hors latin-1
remaining = [(i, c) for i, c in enumerate(content) if ord(c) > 255]
if remaining:
    print(f"ATTENTION: {len(remaining)} caracteres non-latin1 restants:")
    for idx, ch in remaining[:10]:
        ctx = content[max(0,idx-30):idx+30].replace('\n',' ')
        print(f"  pos {idx}: U+{ord(ch):04X} | ...{ctx}...")
else:
    print("Aucun caractere problematique restant.")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nFichier sauvegarde: {os.path.getsize(TARGET)} bytes")
print("DONE")
