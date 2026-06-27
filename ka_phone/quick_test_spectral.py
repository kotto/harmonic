import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from holographic_ensemble import HolographicEnsemble

ensemble = HolographicEnsemble()
ensemble.build_all(force_rebuild=False)

print("=== Spectral Encoders ===")
for did, holo in ensemble.holograms.items():
    if holo.spectral_encoder:
        print(f"  {did:15s}: {holo.spectral_encoder.word_count:4d} mots, {holo.n_ingested:4d} faits")

print("\n=== Tests rapides ===")
for q in ["Quelle est la capitale du Senegal ?", "Qui a decouvert l'ADN ?", "Quand a debute la Revolution francaise ?"]:
    r = ensemble.query(q)
    print(f"Q: {q}")
    print(f"  R: {r['text'][:200]}")
    print(f"  Source: {r.get('source','?')} | {r.get('temps_ms',0)}ms | confiance={r.get('confidence','?')}")
    print()