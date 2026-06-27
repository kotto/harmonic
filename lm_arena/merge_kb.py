import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from knowledge_base import PRE_COMPUTED as KB1
try:
    from knowledge_base_v2 import PRE_COMPUTED as KB2
except ImportError:
    KB2 = {}

merged = dict(KB1)
for k, v in KB2.items():
    if k not in merged:
        merged[k] = v

out_path = os.path.join(os.path.dirname(__file__), "knowledge_base_full.py")
with open(out_path, "w", encoding="utf-8") as f:
    f.write('#!/usr/bin/env python3\n')
    f.write(f'"""Knowledge Base Full — {len(merged)} entries"""\n')
    f.write('import math\n')
    f.write('PHI = 1.618033988749895\n')
    f.write('PI = math.pi\n')
    f.write('E = math.e\n\n')
    f.write('PRE_COMPUTED = {\n')
    for key, value in sorted(merged.items()):
        text = value["text"].replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        f.write(f'    "{key}": {{\n')
        f.write(f'        "text": "{text}",\n')
        f.write(f'        "coherence": {value["coherence"]},\n')
        f.write(f'        "domain": "{value["domain"]}"\n')
        f.write(f'    }},\n')
    f.write('}\n\n')
    f.write('PRE_COMPUTED_NORMALIZED = {k.lower().strip(): v for k, v in PRE_COMPUTED.items()}\n')

print(f"Merged KB: KB1={len(KB1)} + KB2={len(KB2)} = {len(merged)} unique entries -> {out_path}")

domains = {}
for k, v in merged.items():
    d = v["domain"]
    domains[d] = domains.get(d, 0) + 1
for d, c in sorted(domains.items(), key=lambda x: -x[1]):
    print(f"  {d}: {c}")