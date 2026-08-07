# -*- coding: utf-8 -*-
"""Extrait les noms propres des 100 questions (mots capitalisés, hors stopwords)."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
from benchmark_gsm8k import load_gsm8k

STOP = {'the', 'a', 'an', 'if', 'how', 'what', 'when', 'why', 'and', 'but',
        'or', 'for', 'of', 'in', 'on', 'at', 'to', 'his', 'her', 'their',
        'its', 'from', 'with', 'then', 'than', 'there', 'are', 'is', 'was',
        'it', 'he', 'she', 'they', 'as', 'so', 'do', 'does', 'did', 'you'}
names = set()
for p in load_gsm8k()[:100]:
    for m in re.finditer(r'\b([A-Z][a-z]+)\b', p['question']):
        w = m.group(1).lower()
        if w not in STOP and len(w) > 1:
            names.add(w)
print(len(names), 'noms :')
print(sorted(names))
