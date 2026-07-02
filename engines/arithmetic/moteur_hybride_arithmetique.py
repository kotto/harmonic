t#!/usr/bin/env python3
r"""
MOTEUR HYBRIDE V2 — PPMI (relations) + Ondes numériques (valeurs) + Score contextuel
========================================================================================
Combine le meilleur des deux mondes :
  - PPMI/Laplacian : structure relationnelle ("hypotenuse", "carre", "somme")
  - Ondes numériques : valeurs exactes via Ψ_n(x) = exp(i·n·φ·2π·x/L)
  - Score contextuel : pondération par les nombres de la requête

Principe :
  1. PPMI classe les phrases candidates par interférence
  2. Score contextuel : booste les candidats contenant les nombres de la requête
  3. Pour le meilleur candidat pondéré, on extrait les nombres
  4. On VÉRIFIE avec l'arithmétique ondulatoire
  5. Si vérifié → réponse confirmée
  6. Sinon → candidat suivant

Usage :
  python moteur_hybride_arithmetique.py
"""

import sys, os, math, time, json, re
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ka_phone'))

from ppmi_laplacian_encoder import (
    PPMIBuilder, laplacian_eigenmaps, concept_phases,
    stabilize_phases, concept_to_wave, wave_interference
)


# ═══════════════════════════════════════════════════════════════════════════════
# ONDES NUMÉRIQUES (Niveau 2 — Arithmétique)
# ═══════════════════════════════════════════════════════════════════════════════

def number_to_wave(n, grid_size=1024):
    """Ψ_n(x) = exp(i · n · φ · 2π · x / L)"""
    x = np.linspace(0, 1.0, grid_size)
    k0 = PHI * 2 * PI
    return np.exp(1j * n * k0 * x), x


def addition_verifier(a, b, expected, grid_size=1024):
    """Vérifie a + b = expected par multiplication d'ondes."""
    psi_a, _ = number_to_wave(a, grid_size)
    psi_b, _ = number_to_wave(b, grid_size)
    psi_result = psi_a * psi_b
    psi_expected, _ = number_to_wave(expected, grid_size)
    
    dot = np.real(np.sum(psi_result * np.conj(psi_expected)))
    n1 = np.sqrt(np.real(np.sum(psi_result * np.conj(psi_result))))
    n2 = np.sqrt(np.real(np.sum(psi_expected * np.conj(psi_expected))))
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    return dot / (n1 * n2)


def carre_verifier(a, expected, grid_size=1024):
    """Vérifie a² = expected."""
    psi_a, _ = number_to_wave(a, grid_size)
    psi_result = psi_a ** a
    psi_expected, _ = number_to_wave(expected, grid_size)
    
    dot = np.real(np.sum(psi_result * np.conj(psi_expected)))
    n1 = np.sqrt(np.real(np.sum(psi_result * np.conj(psi_result))))
    n2 = np.sqrt(np.real(np.sum(psi_expected * np.conj(psi_expected))))
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    return dot / (n1 * n2)


def pythagore_verifier(a, b, c, grid_size=1024):
    """Vérifie a² + b² = c²."""
    psi_a, _ = number_to_wave(a, grid_size)
    psi_b, _ = number_to_wave(b, grid_size)
    psi_a2 = psi_a ** a
    psi_b2 = psi_b ** b
    psi_sum = psi_a2 * psi_b2
    
    psi_c, _ = number_to_wave(c, grid_size)
    psi_c2 = psi_c ** c
    
    dot = np.real(np.sum(psi_sum * np.conj(psi_c2)))
    n1 = np.sqrt(np.real(np.sum(psi_sum * np.conj(psi_sum))))
    n2 = np.sqrt(np.real(np.sum(psi_c2 * np.conj(psi_c2))))
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    return dot / (n1 * n2)


def extract_numbers(text):
    """Extrait tous les nombres d'une phrase mathématique."""
    numbers = []
    for token in text.replace('²', '').replace('+', ' + ').replace('=', ' = ').replace('-', ' - ').split():
        token = token.strip('.,;:!?()[]{}"\'- ')
        try:
            n = int(token)
            if n >= 0:
                numbers.append(n)
        except ValueError:
            pass
    return numbers


def extract_context_numbers(query_words):
    """Extrait les nombres des mots de la requête."""
    numbers = []
    for w in query_words:
        try:
            numbers.append(int(w))
        except ValueError:
            pass
    return numbers


def compute_contextual_boost(candidate_text, query_numbers):
    """
    Calcule un boost contextuel basé sur la présence des nombres
    de la requête dans le candidat.
    
    Retourne un facteur multiplicatif entre 1.0 et 2.0.
    Plus il y a de nombres de la requête dans le candidat,
    plus le boost est élevé.
    """
    if not query_numbers:
        return 1.0
    
    candidate_numbers = set(extract_numbers(candidate_text))
    query_set = set(query_numbers)
    
    # Intersection : combien de nombres de la requête sont dans le candidat ?
    overlap = len(query_set & candidate_numbers)
    
    if overlap == 0:
        return 1.0  # Pas de boost
    
    # Boost proportionnel au taux de recouvrement
    # max 2.0 si tous les nombres sont présents
    boost = 1.0 + (overlap / len(query_set))
    return min(boost, 2.0)


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR HYBRIDE V2
# ═══════════════════════════════════════════════════════════════════════════════

class MoteurHybride:
    """
    Combine PPMI (relations) + Ondes numériques (valeurs) + Score contextuel.
    """
    
    def __init__(self, corpus):
        self.corpus = corpus
        self.builder = None
        self.phases = None
        self._built = False
    
    def build(self):
        """Construit PPMI + Laplacian Eigenmaps."""
        if self._built:
            return
        
        print("  Construction PPMI + Laplacian...")
        t0 = time.time()
        
        self.builder = PPMIBuilder(window=5)
        self.builder.build_vocab(self.corpus)
        
        W = self.builder.build_ppmi(self.corpus)
        embedding, _ = laplacian_eigenmaps(W, k=2)
        embedding = stabilize_phases(embedding,
            ["est", "plus", "carre", "racine", "solution", "equation", "somme", "hypotenuse"],
            self.builder.vocab)
        self.phases = concept_phases(embedding)
        self.builder.phases = self.phases
        self.builder.embedding = embedding
        
        self._built = True
        print(f"  Terminé en {(time.time()-t0)*1000:.0f} ms (vocab: {self.builder.N} mots)")
    
    def encode(self, words, GRID=256):
        """Encode une liste de mots en onde."""
        psi_sum = np.zeros(GRID, dtype=np.complex128)
        count = 0
        for w in words:
            if isinstance(w, str) and w in self.builder.vocab:
                idx = self.builder.vocab[w]
                psi, _ = concept_to_wave(self.phases[idx], GRID)
                psi_sum += psi
                count += 1
        if count > 0:
            psi_sum /= count
        return psi_sum
    
    def encode_phrase(self, phrase, GRID=256):
        """Tokenise puis encode une phrase."""
        tokens = []
        for mot in phrase.lower().split():
            mot = mot.strip('.,;:!?()[]{}"\'- ')
            if len(mot) > 1:
                tokens.append(mot)
        return self.encode(tokens, GRID), tokens
    
    def query_hybrid_v2(self, query_words, candidates, relation_type, GRID=256):
        """
        Requête hybride V2 avec score contextuel :
          1. PPMI → classement des candidats par interférence
          2. Score contextuel → boost des candidats avec les nombres de la requête
          3. Ondes numériques → vérification arithmétique
          4. Retourne le premier candidat VÉRIFIÉ
        
        relation_type : 'pythagore', 'carre', 'racine', 'equation', 'somme'
        """
        psi_q = self.encode(query_words, GRID)
        
        # Extraire les nombres de la requête pour le score contextuel
        query_numbers = extract_context_numbers(query_words)
        
        # Étape 1 : PPMI — classement par interférence
        scored = []
        for cand_text in candidates:
            psi_c, _ = self.encode_phrase(cand_text, GRID)
            interf = wave_interference(psi_q, psi_c)
            scored.append((cand_text, interf))
        
        # Étape 2 : Appliquer le score contextuel
        context_scored = []
        for cand_text, interf in scored:
            boost = compute_contextual_boost(cand_text, query_numbers)
            context_interf = interf * boost
            context_scored.append((cand_text, interf, boost, context_interf))
        
        # Trier par interférence contextuelle (avec boost)
        context_scored.sort(key=lambda x: -abs(x[3]))
        
        # Étape 3 : Vérification arithmétique
        for cand_text, interf, boost, context_interf in context_scored:
            numbers = extract_numbers(cand_text)
            
            if relation_type == 'pythagore' and len(numbers) >= 3:
                # Tester toutes les permutations : a²+b²=c² peut être dans n'importe quel ordre
                from itertools import permutations
                for a, b, c in permutations(numbers[:3], 3):
                    if pythagore_verifier(a, b, c, grid_size=256) > 0.9:
                        return c, cand_text, interf, boost
        
            elif relation_type == 'carre' and len(numbers) >= 2:
                # base² = carre ; tester les deux sens
                if carre_verifier(numbers[0], numbers[1], grid_size=256) > 0.9:
                    return numbers[1], cand_text, interf, boost
                if carre_verifier(numbers[1], numbers[0], grid_size=256) > 0.9:
                    return numbers[0], cand_text, interf, boost
        
            elif relation_type == 'racine' and len(numbers) >= 2:
                # racine de radicand = root ; tester les deux sens
                if carre_verifier(numbers[0], numbers[1], grid_size=256) > 0.9:
                    return numbers[0], cand_text, interf, boost
                if carre_verifier(numbers[1], numbers[0], grid_size=256) > 0.9:
                    return numbers[1], cand_text, interf, boost
        
            elif relation_type == 'equation' and len(numbers) >= 3:
                for i in range(len(numbers)):
                    for j in range(i+1, len(numbers)):
                        a, b = numbers[i], numbers[j]
                        for k in range(len(numbers)):
                            if k != i and k != j:
                                c = numbers[k]
                                if addition_verifier(a, b, c, grid_size=256) > 0.9:
                                    break
        
            elif relation_type == 'somme' and len(numbers) >= 3:
                for i in range(len(numbers)):
                    for j in range(i+1, len(numbers)):
                        a, b = numbers[i], numbers[j]
                        for k in range(len(numbers)):
                            if k != i and k != j:
                                c = numbers[k]
                                if addition_verifier(a, b, c, grid_size=256) > 0.9:
                                    return c, cand_text, interf, boost
        
        # Fallback : meilleur candidat sans vérification
        if context_scored:
            numbers = extract_numbers(context_scored[0][0])
            return numbers[-1] if numbers else None, context_scored[0][0], context_scored[0][1], context_scored[0][2]
        
        return None, None, 0.0, 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

def benchmark_hybrid():
    print("=" * 74)
    print("  MOTEUR HYBRIDE V2 — + Score Contextuel")
    print("=" * 74)
    
    with open("corpus_mathematique.json", 'r', encoding='utf-8') as f:
        corpus = json.load(f)
    print(f"\n  Corpus : {len(corpus)} phrases")
    
    moteur = MoteurHybride(corpus)
    moteur.build()
    
    tests = [
        {
            "desc": "Hypoténuse du triangle 3-4",
            "type": "pythagore",
            "qwords": ["hypotenuse", "triangle", "cotes", "3", "4"],
            "expected": 5,
            "candidates": [
                "5 est l'hypotenuse du triangle rectangle 3-4",
                "10 est l'hypotenuse du triangle rectangle 6-8",
                "13 est l'hypotenuse du triangle rectangle 5-12",
            ]
        },
        {
            "desc": "Carré de 12",
            "type": "carre",
            "qwords": ["carre", "12"],
            "expected": 144,
            "candidates": [
                "144 est le carre de 12",
                "100 est le carre de 10",
                "169 est le carre de 13",
            ]
        },
        {
            "desc": "Racine carrée de 49",
            "type": "racine",
            "qwords": ["racine", "carree", "49"],
            "expected": 7,
            "candidates": [
                "7 est la racine carree de 49",
                "la racine de 49 est 7",
                "8 est la racine carree de 64",
                "10 est la racine carree de 100",
            ]
        },
        {
            "desc": "Résoudre x + 3 = 7",
            "type": "equation",
            "qwords": ["solution", "equation", "x", "3", "7"],
            "expected": 4,
            "candidates": [
                "4 est la solution de l'equation x + 3 = 7",
                "si x + 3 = 7, alors x = 4",
                "5 est la solution de l'equation x + 2 = 7",
            ]
        },
        {
            "desc": "Somme de 15 et 27",
            "type": "somme",
            "qwords": ["somme", "15", "27"],
            "expected": 42,
            "candidates": [
                "la somme de 15 et 27 est 42",
                "15 + 27 = 42",
                "45 est la somme de 15 et 30",
            ]
        },
    ]
    
    print("\n  BENCHMARK HYBRIDE V2 :")
    print(f"  {'='*60}")
    
    t0 = time.time()
    ok_count = 0
    
    for q in tests:
        resultat, phrase, interf, boost = moteur.query_hybrid_v2(
            q["qwords"], q["candidates"], q["type"]
        )
        
        correct = resultat == q["expected"]
        if correct:
            ok_count += 1
        
        ok = "V" if correct else "X"
        print(f"\n  Q: {q['desc']}")
        print(f"     Phrase PPMI     : {phrase[:60]}..." if phrase else "     (aucune)")
        print(f"     Interference    : {interf:+.4f}" if interf else "")
        print(f"     Boost contextuel: x{boost:.2f}" if boost else "")
        print(f"     Verification #s : {resultat} (attendu: {q['expected']})  {ok}")
    
    dt = (time.time() - t0) * 1000
    total = len(tests)
    accuracy = ok_count / total * 100
    
    print(f"\n  {'='*60}")
    print(f"  Resultat hybride V2 : {ok_count}/{total} ({accuracy:.0f}%)")
    print(f"  Temps total         : {dt:.0f} ms")
    
    return accuracy


if __name__ == "__main__":
    accuracy = benchmark_hybrid()
    
    print("\n" + "=" * 74)
    print(f"  MOTEUR HYBRIDE V2 — Precision : {accuracy:.0f}%")
    print("=" * 74)
    
    if accuracy == 100:
        print("\n  🎯 PARFAIT ! 5/5 — Le score contextuel resout le probleme Pythagore.")
    elif accuracy >= 80:
        print(f"\n  ✅ {accuracy:.0f}% — Bonne amelioration.")
    else:
        print(f"\n  Precision : {accuracy:.0f}%")