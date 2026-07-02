"""
Resonance Filter — Filtrage Ondulatoire de la Base de Connaissance
====================================================================
Filtre la KB par CENTRALITÉ DE RÉSONANCE : un fait est gardé si
ses mots-clés résonnent avec beaucoup d'autres mots (concept central),
pas s'ils sont isolés (bruit).

Principe ondulatoire :
  Chaque mot a une phase θ sur S¹ (via SpectralEmbedding).
  Deux mots sont "proches" si |θ(a) - θ(b)| < 30°.
  Un mot a une centralité élevée s'il a beaucoup de voisins proches.
  Un fait est valide si tous ses mots ont une centralité suffisante.

Usage :
  from resonance_filter import filter_kb
  clean_kb = filter_kb(knowledge_base, min_centrality=5)
"""

import sys, math, logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Set
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
log = logging.getLogger(__name__)

PHI = 1.618033988749895
TAU = 2.0 * math.pi


# ═══════════════════════════════════════════════════════════════════════════════
# FILTRE DE RÉSONANCE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_centrality(phases: Dict[str, float],
                       angle_threshold: float = 30.0) -> Dict[str, int]:
    """
    Calcule la centralité de résonance de chaque mot.
    
    La centralité d'un mot = nombre d'autres mots dont la phase
    est à moins de angle_threshold degrés.
    
    Un mot central est un "hub" sémantique (ex: "lumiere").
    Un mot isolé est probablement du bruit.
    
    Args:
        phases: {mot: phase_en_radians}
        angle_threshold: seuil angulaire en degrés
    
    Returns:
        {mot: centralite}
    """
    threshold_rad = math.radians(angle_threshold)
    
    # Trier les mots par phase pour un calcul O(N log N)
    word_phase_pairs = sorted(phases.items(), key=lambda x: x[1])
    n = len(word_phase_pairs)
    
    if n < 10:
        return {w: n for w, _ in word_phase_pairs}
    
    centrality = {}
    
    for i, (word, phase_i) in enumerate(word_phase_pairs):
        count = 0
        
        # Voisins à droite (phase croissante)
        for j in range(i + 1, min(i + n//2, n)):
            d_phase = abs(word_phase_pairs[j][1] - phase_i)
            if d_phase > math.pi:
                d_phase = TAU - d_phase
            if d_phase < threshold_rad:
                count += 1
            else:
                break  # trié → on peut s'arrêter
        
        # Voisins à gauche (phase décroissante, wrap-around)
        for j in range(i - 1, max(i - n//2, -1), -1):
            d_phase = abs(word_phase_pairs[j][1] - phase_i)
            if d_phase > math.pi:
                d_phase = TAU - d_phase
            if d_phase < threshold_rad:
                count += 1
            else:
                break
        
        centrality[word] = count
    
    return centrality


def filter_kb(knowledge_base: List[Tuple[str, str, str, str]],
              min_centrality: int = 3,
              phases: Dict[str, float] = None,
              angle_threshold: float = 30.0) -> Tuple[List, Dict]:
    """
    Filtre la KB par centralité de résonance.
    
    Un fait est gardé si :
      1. Son sujet a une centralité >= min_centrality, ET
      2. Au moins un mot de sa relation/objet a centralité >= 1
    
    Args:
        knowledge_base: liste de (sujet, relation, objet, secteur)
        min_centrality: centralité minimale du sujet
        phases: phases des mots (si None, charge depuis SpectralEmbedding)
        angle_threshold: seuil angulaire en degrés
    
    Returns:
        (faits_filtrés, stats)
    """
    # Charger les phases si pas fournies
    if phases is None:
        try:
            from spectral_embedding import _SPECTRAL
            if _SPECTRAL and _SPECTRAL.is_ready:
                phases = _SPECTRAL.phases
            else:
                log.warning("SpectralEmbedding non disponible, filtrage impossible")
                return knowledge_base, {'error': 'no_phases'}
        except Exception:
            return knowledge_base, {'error': 'no_phases'}
    
    if not phases:
        return knowledge_base, {'error': 'empty_phases'}
    
    # Calculer la centralité
    log.info(f"Calcul de la centralité pour {len(phases)} mots...")
    centrality = compute_centrality(phases, angle_threshold)
    
    # Statistiques de centralité
    cent_values = list(centrality.values())
    if cent_values:
        log.info(f"  Centralité moyenne: {np.mean(cent_values):.1f}")
        log.info(f"  Centralité médiane: {np.median(cent_values):.1f}")
        log.info(f"  Mots avec centralité >= {min_centrality}: "
                 f"{sum(1 for c in cent_values if c >= min_centrality)}")
    
    # Filtrer
    kept = []
    rejected = []
    reasons = Counter()
    
    for s, r, o, sec in knowledge_base:
        s_lower = s.lower().strip()
        cent_s = centrality.get(s_lower, 0)
        
        if cent_s < min_centrality:
            rejected.append((s, r, o, sec))
            reasons[f'sujet_centralite_{cent_s}'] += 1
            continue
        
        # Vérifier la relation/objet
        obj_words = set(o.lower().split())
        rel_words = set(r.lower().split())
        
        has_support = False
        for w in obj_words | rel_words:
            if centrality.get(w, 0) >= 1:
                has_support = True
                break
        
        if has_support:
            kept.append((s, r, o, sec))
        else:
            rejected.append((s, r, o, sec))
            reasons['objet_isole'] += 1
    
    n_total = len(knowledge_base)
    n_kept = len(kept)
    
    stats = {
        'total': n_total,
        'kept': n_kept,
        'rejected': len(rejected),
        'retention': round(n_kept / max(n_total, 1) * 100, 1),
        'min_centrality': min_centrality,
        'angle_threshold': angle_threshold,
        'reasons': dict(reasons.most_common(10)),
    }
    
    log.info(f"  {n_total:,} → {n_kept:,} faits ({stats['retention']}% gardés)")
    
    return kept, stats


def score_facts_by_resonance(knowledge_base: List[Tuple],
                              phases: Dict[str, float] = None) -> List[Tuple]:
    """
    Score chaque fait par résonance (sans filtrer).
    
    Retourne les faits avec leur score de qualité [0, 1].
    Utile pour le diagnostic.
    """
    if phases is None:
        try:
            from spectral_embedding import _SPECTRAL
            if _SPECTRAL and _SPECTRAL.is_ready:
                phases = _SPECTRAL.phases
        except Exception:
            pass
    
    if not phases:
        return [(s, r, o, sec, 0.5) for s, r, o, sec in knowledge_base]
    
    centrality = compute_centrality(phases)
    max_cent = max(centrality.values()) if centrality else 100
    
    scored = []
    for s, r, o, sec in knowledge_base:
        cent_s = centrality.get(s.lower().strip(), 0)
        score = min(1.0, cent_s / max(max_cent, 1))
        scored.append((s, r, o, sec, score))
    
    return scored


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    print("=" * 65)
    print("RESONANCE FILTER — Filtrage ondulatoire de la KB")
    print("=" * 65)
    
    # Charger les phases
    try:
        from spectral_embedding import _SPECTRAL
        if _SPECTRAL and _SPECTRAL.is_ready:
            phases = _SPECTRAL.phases
        else:
            phases = {}
    except Exception:
        phases = {}
    
    if not phases:
        print("  Phases non disponibles. Construire d'abord avec spectral_embedding.")
        return
    
    # Charger la KB
    data = np.load('data/bootstrapper_output/knowledge_base_50k.npz', allow_pickle=True)
    kb = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
    
    print(f"\n  KB chargée : {len(kb):,} faits")
    
    # Filtrer
    import time
    t0 = time.time()
    cleaned, stats = filter_kb(kb, min_centrality=3, phases=phases)
    dt = time.time() - t0
    
    print(f"\n  Résultat ({dt:.1f}s) :")
    print(f"    {stats['total']:,} → {stats['kept']:,} faits ({stats['retention']}%)")
    print(f"    {stats['rejected']:,} rejetés")
    
    if 'reasons' in stats and stats['reasons']:
        print(f"\n  Raisons de rejet :")
        for reason, count in stats['reasons'].items():
            print(f"    {reason:30s} {count:>8,}")
    
    # Afficher quelques exemples de faits rejetés
    print(f"\n  Exemples de faits REJETÉS (bruit) :")
    for s, r, o, sec in kb:
        if (s, r, o, sec) not in cleaned:
            print(f"    ✗ {s:30s} {r:20s} {o[:50]}")
            if sum(1 for x in kb if (x[0], x[1], x[2], x[3]) not in cleaned) > 5:
                break
    
    # Sauvegarder
    if cleaned:
        out_path = Path('data/bootstrapper_output/knowledge_base_resonance.npz')
        facts_array = np.array(cleaned, dtype=object)
        np.savez(str(out_path), facts=facts_array)
        print(f"\n  💾 Sauvegardé : {out_path}")


if __name__ == '__main__':
    demo()
