#!/usr/bin/env python3
r"""
BENCHMARK — Raisonnement multi-sauts mathématique avec PPMI
=============================================================
Utilise le corpus massif de 96K phrases mathématiques pour
tester le raisonnement multi-sauts par interférence PPMI.

Teste :
  1. "Quelle est l'hypoténuse d'un triangle de côtés 3 et 4 ?" → 5
  2. "Quelle est la racine carrée de 49 ?" → 7
  3. "Quel est le carré de 12 ?" → 144
  4. "Résoudre x + 3 = 7" → 4
  5. "La somme de 15 et 27" → 42

Usage :
  python benchmark_multihop_mathematique.py
"""

import sys, os, math, time, json
import numpy as np
from collections import Counter

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ka_phone'))

from ppmi_laplacian_encoder import (
    PPMIBuilder, laplacian_eigenmaps, concept_phases,
    stabilize_phases, concept_to_wave, wave_interference
)


def charger_corpus(fichier="corpus_mathematique.json"):
    """Charge le corpus tokenisé."""
    with open(fichier, 'r', encoding='utf-8') as f:
        return json.load(f)


def benchmark_multihop_math():
    print("=" * 74)
    print("  BENCHMARK — Raisonnement multi-sauts mathématique (PPMI)")
    print("=" * 74)
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAPE 1 : Charger le corpus
    # ═══════════════════════════════════════════════════════════════════
    print("\n  [1] Chargement du corpus mathématique...")
    t0 = time.time()
    corpus = charger_corpus()
    t1 = time.time()
    print(f"      {len(corpus)} phrases tokenisées ({(t1-t0)*1000:.0f} ms)")
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAPE 2 : Construire PPMI
    # ═══════════════════════════════════════════════════════════════════
    print("\n  [2] Construction PPMI + Laplacian Eigenmaps...")
    t0 = time.time()
    
    builder = PPMIBuilder(window=5)
    builder.build_vocab(corpus)
    print(f"      Vocabulaire : {builder.N} mots")
    
    W = builder.build_ppmi(corpus)
    nnz = W.nnz if hasattr(W, 'nnz') else np.count_nonzero(W)
    print(f"      PPMI : {W.shape}, {nnz} entrées non-nulles ({nnz/(builder.N*builder.N)*100:.2f}%)")
    
    # Laplacian Eigenmaps
    embedding, eigenvalues = laplacian_eigenmaps(W, k=2)
    embedding = stabilize_phases(embedding, 
        ["est", "plus", "carre", "racine", "solution", "equation", "somme", "hypotenuse"],
        builder.vocab)
    phases = concept_phases(embedding)
    builder.phases = phases
    builder.embedding = embedding
    
    t1 = time.time()
    print(f"      Terminé en {(t1-t0)*1000:.0f} ms")
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAPE 3 : Fonction d'encodage
    # ═══════════════════════════════════════════════════════════════════
    GRID = 256
    
    def encode_text(mots):
        """Encode une liste de mots (ou une phrase string) en onde."""
        if isinstance(mots, str):
            mots = mots.lower().split()
        psi_sum = np.zeros(GRID, dtype=np.complex128)
        count = 0
        for w in mots:
            if w in builder.vocab:
                idx = builder.vocab[w]
                psi, _ = concept_to_wave(phases[idx], GRID)
                psi_sum += psi
                count += 1
        if count > 0:
            psi_sum /= count
        return psi_sum
    
    def encode_phrase(phrase):
        """Tokenise puis encode une phrase."""
        tokens = []
        for mot in phrase.lower().split():
            mot = mot.strip('.,;:!?()[]{}"\'- ')
            if len(mot) > 1:
                tokens.append(mot)
        return encode_text(tokens), tokens
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAPE 4 : Définir les requêtes et les faits
    # ═══════════════════════════════════════════════════════════════════
    print("\n  [3] Benchmark multi-sauts mathématique")
    print("  " + "-" * 60)
    
    # Requêtes : (description, mots_requête, réponse_attendue, faits_candidats)
    queries = [
        {
            "desc": "Hypoténuse du triangle 3-4",
            "qwords": ["hypotenuse", "triangle", "cotes", "3", "4"],
            "expected": "5",
            "candidates": [
                "5 est l'hypotenuse du triangle rectangle 3-4",
                "6 est l'hypotenuse du triangle rectangle 5-6",
                "10 est l'hypotenuse du triangle rectangle 6-8",
                "13 est l'hypotenuse du triangle rectangle 5-12",
            ]
        },
        {
            "desc": "Racine carrée de 49",
            "qwords": ["racine", "carree", "49"],
            "expected": "7",
            "candidates": [
                "7 est la racine carree de 49",
                "la racine de 49 est 7",
                "8 est la racine carree de 64",
                "6 est la racine carree de 36",
                "10 est la racine carree de 100",
            ]
        },
        {
            "desc": "Carré de 12",
            "qwords": ["carre", "12"],
            "expected": "144",
            "candidates": [
                "144 est le carre de 12",
                "le carre de 12 est 144",
                "100 est le carre de 10",
                "169 est le carre de 13",
            ]
        },
        {
            "desc": "Résoudre x + 3 = 7",
            "qwords": ["solution", "equation", "x", "3", "7"],
            "expected": "4",
            "candidates": [
                "4 est la solution de l'equation x + 3 = 7",
                "si x + 3 = 7, alors x = 4",
                "5 est la solution de l'equation x + 2 = 7",
                "6 est la solution de l'equation x + 1 = 7",
            ]
        },
        {
            "desc": "Somme de 15 et 27",
            "qwords": ["somme", "15", "27"],
            "expected": "42",
            "candidates": [
                "la somme de 15 et 27 est 42",
                "15 + 27 = 42",
                "42 est la somme de 15 et 27",
                "45 est la somme de 15 et 30",
                "30 est la somme de 15 et 15",
            ]
        },
    ]
    
    t0 = time.time()
    ok_count = 0
    total = len(queries)
    
    for q in queries:
        psi_q = encode_text(q["qwords"])
        
        # Encoder les candidats
        cand_scores = []
        for cand_text in q["candidates"]:
            psi_c, _ = encode_phrase(cand_text)
            interf = wave_interference(psi_q, psi_c)
            cand_scores.append((cand_text, interf))
        
        cand_scores.sort(key=lambda x: -abs(x[1]))
        
        best_text, best_interf = cand_scores[0]
        # Extraire la réponse du meilleur candidat
        # Chercher un nombre dans le texte candidat
        best_val = None
        for mot in best_text.split():
            try:
                best_val = str(int(mot))
                break
            except ValueError:
                pass
        
        correct = best_val == q["expected"]
        if correct:
            ok_count += 1
        
        ok = "✓" if correct else "✗"
        print(f"\n    Q: {q['desc']}")
        print(f"       Meilleur candidat : {best_text[:70]}...")
        print(f"       Interférence      : {best_interf:+.4f}")
        print(f"       Réponse           : {best_val} (attendu: {q['expected']})  {ok}")
    
    dt = (time.time() - t0) * 1000
    accuracy = ok_count / total * 100
    
    print(f"\n  ─────────────────────────────────────")
    print(f"  Résultat : {ok_count}/{total} corrects ({accuracy:.0f}%)")
    print(f"  Temps total : {dt:.0f} ms")
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAPE 5 : Analyse de co-occurrence
    # ═══════════════════════════════════════════════════════════════════
    print("\n  [4] Analyse de co-occurrence (validation PPMI)")
    print("  " + "-" * 60)
    
    # Vérifier que "hypotenuse" et "triangle" co-occurrent fortement
    for mot in ["hypotenuse", "triangle", "carre", "racine", "solution", "equation", "somme"]:
        if mot in builder.vocab:
            idx = builder.vocab[mot]
            t = math.degrees(phases[idx])
            print(f"    {mot:15s} → θ = {t:6.1f}°")
    
    return accuracy


if __name__ == "__main__":
    accuracy = benchmark_multihop_math()
    
    print("\n" + "=" * 74)
    print(f"  BENCHMARK TERMINÉ — Précision multi-sauts : {accuracy:.0f}%")
    print("=" * 74)
    
    if accuracy >= 80:
        print("\n  ✅ Le raisonnement multi-sauts fonctionne avec le corpus massif !")
        print("     Le PPMI capture correctement les relations mathématiques.")
    elif accuracy >= 40:
        print("\n  ⚠️  Partiellement fonctionnel — le corpus est riche mais")
        print("     l'interférence simple (cos θ) ne suffit pas pour tous les cas.")
        print("     → utiliser spectral_hop() avec score de résolution.")
    else:
        print("\n  ❌ Le PPMI seul ne suffit pas — les fréquences sont trop")
        print("     mélangées. Il faut le score de résolution (local^α × global^(1-α))")
        print("     ou un routage par type de relation (hologrammes spécialisés).")