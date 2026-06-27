#!/usr/bin/env python3
"""
Test d'intégration du WaveLogicEngine avec le SpectralEncoder de l'ensemble
holographique pour des interférences sémantiques (pas SHA-256).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from holographic_ensemble import HolographicEnsemble
from wave_logic_engine import WaveLogicEngine

ensemble = HolographicEnsemble()
ensemble.build_all(force_rebuild=False)

wle = WaveLogicEngine(ensemble)

# Test avec le SpectralEncoder de l'ensemble geography
geo_holo = ensemble.holograms.get("geography")
if geo_holo and geo_holo.spectral_encoder:
    enc = geo_holo.spectral_encoder
    print("=== Test similarité spectrale (SpectralEncoder) ===")
    pairs = [
        ("Socrate", "mortel"),
        ("Socrate", "philosophe"),
        ("capitale", "Dakar"),
        ("capitale", "fromage"),
        ("Paris", "France"),
        ("Sénégal", "Dakar"),
    ]
    for w1, w2 in pairs:
        sim = enc.similarity(w1, w2)
        print(f"  '{w1}' ↔ '{w2}' : {sim:.3f}")

    print("\n=== Déduction avec SpectralEncoder ===")
    # Encoder les prémisses via le SpectralEncoder
    for premise in ["Tous les hommes sont mortels", "Socrate est un homme"]:
        kx, ky = enc.encode(premise)
        print(f"  '{premise}' → ({kx:.2f}, {ky:.2f})")
    
    q_kx, q_ky = enc.encode("Socrate est-il mortel ?")
    for premise in ["Tous les hommes sont mortels", "Socrate est un homme"]:
        p_kx, p_ky = enc.encode(premise)
        dot = q_kx * p_kx + q_ky * p_ky
        print(f"  Interférence avec '{premise[:40]}' : {dot:+.3f}")