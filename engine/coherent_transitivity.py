"""
Transitivité Validée par Cohérence de Phase
============================================
Remplace la fermeture transitive brute par une validation ondulatoire :
chaque chaîne A→B→C est testée — la similarité de phase entre le contexte
[A + relation] et la cible [C] doit dépasser un seuil.

Résultat : des faits propres directement, sans post-filtrage.
"""

import sys, time
import numpy as np
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holographic_encoder import HolographicEncoder, build_holographic_waves
from holographic_trainer import HolographicTrainer, build_test_pairs


def coherent_transitive_closure(facts, encoder, max_new=50000, sim_threshold=0.15):
    """
    Fermeture transitive validée par cohérence de phase.
    
    Pour A → B → C :
      ψ_ctx = moyenne(encode(A) + encode(mots de r1) + encode(mots de r2))
      cohérence = Re(⟨ψ_ctx | ψ_C⟩) × 0.6 + Re(⟨ψ_A | ψ_C⟩) × 0.4
      Si cohérence ≥ threshold → accepté
    """
    graph = defaultdict(list)
    for s, r, o, _ in facts:
        graph[s].append((r, o))
    
    existing = set((s, r, o) for s, r, o, _ in facts)
    new_facts = []
    
    # Cache de vecteurs
    word_vec = {}
    def gv(w):
        if w not in word_vec and w in encoder.word_vectors:
            word_vec[w] = encoder.word_vectors[w]
        return word_vec.get(w)
    
    for s, edges in list(graph.items()):
        if len(new_facts) >= max_new:
            break
        vs = gv(s)
        if vs is None:
            continue
        
        for r1, o1 in edges:
            if o1 not in graph:
                continue
            vo1 = gv(o1)
            if vo1 is None:
                continue
            
            for r2, o2 in graph[o1]:
                if o2 == s or len(o2) < 2:
                    continue
                vo2 = gv(o2)
                if vo2 is None:
                    continue
                
                comp_r = f'{r1} → {r2}'
                key = (s, comp_r, o2)
                if key in existing:
                    continue
                
                # Encoder le contexte
                ctx_vecs = [vs]
                for w in comp_r.split():
                    w = w.strip('→ ')
                    vw = gv(w)
                    if vw is not None:
                        ctx_vecs.append(vw)
                
                if len(ctx_vecs) < 2:
                    continue
                
                psi_ctx = sum(ctx_vecs) / len(ctx_vecs)
                norm = np.sqrt(np.sum(np.abs(psi_ctx)**2))
                if norm < 1e-10:
                    continue
                psi_ctx /= norm
                
                # Similarité contexte ↔ cible
                sim_ctx = float(np.real(np.dot(psi_ctx, np.conj(vo2))))
                
                # Similarité directe source ↔ cible
                sim_dir = float(np.real(np.dot(vs, np.conj(vo2))))
                
                coherence = sim_ctx * 0.6 + sim_dir * 0.4
                
                if coherence >= sim_threshold:
                    from bootstrapper import detect_sector
                    sec = detect_sector(f"{s} {comp_r} {o2}")
                    new_facts.append((s, comp_r, o2, sec))
                    existing.add(key)
                    
                    if len(new_facts) >= max_new:
                        return new_facts
    
    return new_facts


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=== Transitivité Validée par Cohérence de Phase ===")
    
    # Charger les faits propres
    data = np.load('../data/bootstrapper_output/knowledge_base_50k.npz', allow_pickle=True)
    facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
    print(f"Base: {len(facts):,} faits")
    
    # Encoder et entraîner
    encoder = HolographicEncoder(dim=384)
    for s, r, o, _ in facts:
        for w in f'{s} {r} {o}'.split():
            w = w.strip('.,!?;:')
            if len(w) >= 2:
                encoder.encode_word(w)
    
    trainer = HolographicTrainer(encoder, lr=0.3)
    trainer.train_optimized(facts, epochs=5, lr_start=0.5, lr_end=0.05,
                            repulsion_strength=0.03, verbose=False)
    print(f"Entraîné: {encoder.vocab_size:,} mots")
    
    # Transitivité cohérente vs brute
    print("\n[1] Transitivité brute (sans validation):")
    from expand_to_500k import transitive_closure
    t0 = time.time()
    raw = transitive_closure(facts, max_new=20000)
    print(f"  +{len(raw)} faits en {time.time()-t0:.1f}s")
    # Vérifier la qualité: longueur moyenne des relations
    raw_r_len = np.mean([len(r) for _, r, _, _ in raw])
    print(f"  Longueur moyenne relation: {raw_r_len:.0f} chars")
    
    print("\n[2] Transitivité cohérente (validée par phase):")
    t0 = time.time()
    coherent = coherent_transitive_closure(facts, encoder, max_new=20000, sim_threshold=0.15)
    print(f"  +{len(coherent)} faits en {time.time()-t0:.1f}s")
    coh_r_len = np.mean([len(r) for _, r, _, _ in coherent]) if coherent else 0
    print(f"  Longueur moyenne relation: {coh_r_len:.0f} chars")
    
    # Qualité: combien de chaînes dégénérées?
    raw_degen = sum(1 for _, r, _, _ in raw if '→ →' in r)
    coh_degen = sum(1 for _, r, _, _ in coherent if '→ →' in r)
    print(f"\n  Chaînes dégénérées: {raw_degen}/{len(raw)} (brut) vs {coh_degen}/{len(coherent)} (cohérent)")
    
    # Tester plusieurs seuils
    print("\n[3] Impact du seuil de cohérence:")
    for threshold in [0.05, 0.10, 0.15, 0.20, 0.25]:
        sample = coherent_transitive_closure(facts, encoder, max_new=5000, sim_threshold=threshold)
        degen = sum(1 for _, r, _, _ in sample if '→ →' in r)
        avg_len = np.mean([len(r) for _, r, _, _ in sample]) if sample else 0
        print(f"  seuil={threshold:.2f} → {len(sample):5d} faits, {degen} dégénérés, r_len={avg_len:.0f}")
