#!/usr/bin/env python3
"""smoke_memory_first_medical.py — vérifie le chat mémoire-d'abord sur le corpus KA."""
import sys
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

from ka_server.services.memory_first import ask

print("--- LE CHAT MÉMOIRE-D'ABORD — questions médicales réelles ---")
for q in ['arret cardiaque', 'paludisme', 'hemorragie', 'la tuberculose',
          'comment reconnaitre une fracture ?', 'quel est le traitement du paludisme ?',
          'recette de pizza']:
    r = ask(q)
    if r['refused']:
        print(f'{q!r:46s} -> ❌ REFUS ({r["reason"][:50]})')
    else:
        prov = r['provenance'][0]
        print(f'{q!r:46s} -> ✅ {r["answer"][:66]}…')
        print(f'{"":48s}   source: {prov["source"][:48]} · conf: {r["confidence"]}')
