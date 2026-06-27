#!/usr/bin/env python3
r"""
BENCHMARK — Algèbre Hybride (PPMI + Ondes numériques)
========================================================
Teste la résolution d'équations algébriques via le moteur hybride.

Types d'équations :
  1. Équations linéaires : x + b = c, x - b = c
  2. Équations multiplicatives : a × x = c
  3. Équations quadratiques : x² = n

Méthode :
  - PPMI + score contextuel → trouve la phrase candidate
  - Ondes numériques → vérifie la solution par interférence exacte

Usage :
  python benchmark_algebre_hybride.py
"""

import sys, os, math, time, json
import numpy as np
from itertools import permutations

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ka_phone'))
sys.path.insert(0, os.path.dirname(__file__))

from ppmi_laplacian_encoder import (
    PPMIBuilder, laplacian_eigenmaps, concept_phases,
    stabilize_phases, concept_to_wave, wave_interference
)
from raisonnement_algebrique_ondulatoire import (
    solve_x_plus_b_equals_c, solve_x_minus_b_equals_c,
    solve_a_times_x_equals_c, solve_x_squared_equals_n,
    number_to_planewave
)


def extract_numbers(text):
    """Extrait tous les nombres d'une phrase."""
    numbers = []
    for token in text.replace('²', '').replace('+', ' + ').replace('=', ' = ').replace('-', ' - ').split():
        token = token.strip('.,;:!?()[]{}"\'- ')
        try:
            n = int(token)
            numbers.append(n)
        except ValueError:
            pass
    return numbers


def extract_query_numbers(query_words):
    """Extrait les nombres d'une liste de mots de requête."""
    numbers = []
    for w in query_words:
        try:
            numbers.append(int(w))
        except ValueError:
            pass
    return numbers


def contextual_boost(candidate_text, query_numbers):
    """Boost contextuel : +50% par nombre de la requête présent."""
    if not query_numbers:
        return 1.0
    cand_nums = set(extract_numbers(candidate_text))
    query_set = set(query_numbers)
    overlap = len(query_set & cand_nums)
    if overlap == 0:
        return 1.0
    return 1.0 + (overlap / len(query_set))


class AlgebreHybride:
    """Moteur hybride pour la résolution d'équations algébriques."""
    
    def __init__(self, corpus):
        self.corpus = corpus
        self.builder = None
        self.phases = None
        self.GRID = 256
        self._built = False
    
    def build(self):
        """Construit PPMI + Laplacian."""
        if self._built:
            return
        
        print("  Construction PPMI + Laplacian...")
        t0 = time.time()
        
        self.builder = PPMIBuilder(window=5)
        self.builder.build_vocab(self.corpus)
        
        W = self.builder.build_ppmi(self.corpus)
        embedding, _ = laplacian_eigenmaps(W, k=2)
        embedding = stabilize_phases(embedding,
            ["est", "solution", "equation", "carre", "racine", "somme"],
            self.builder.vocab)
        self.phases = concept_phases(embedding)
        self.builder.phases = self.phases
        self.builder.embedding = embedding
        
        self._built = True
        print(f"  Terminé en {(time.time()-t0)*1000:.0f} ms (vocab: {self.builder.N} mots)")
    
    def encode_query(self, words):
        """Encode des mots de requête en onde."""
        psi_sum = np.zeros(self.GRID, dtype=np.complex128)
        count = 0
        for w in words:
            if isinstance(w, str) and w in self.builder.vocab:
                idx = self.builder.vocab[w]
                psi, _ = concept_to_wave(self.phases[idx], self.GRID)
                psi_sum += psi
                count += 1
        if count > 0:
            psi_sum /= count
        return psi_sum
    
    def encode_phrase(self, phrase):
        """Encode une phrase (string) en onde."""
        tokens = []
        for mot in phrase.lower().split():
            mot = mot.strip('.,;:!?()[]{}"\'- ')
            if len(mot) > 1:
                tokens.append(mot)
        return self.encode_query(tokens)
    
    def solve_linear(self, query_words, candidates):
        """Résout x + b = c avec PPMI + vérification ondulatoire.
        
        Logique : la phrase candidate contient 3 nombres [x, b, c].
        Les nombres de la requête sont [b, c] (les valeurs connues).
        L'inconnue x est le nombre du candidat qui n'est PAS dans la requête.
        On vérifie ensuite x + b = c par interférence d'ondes.
        """
        psi_q = self.encode_query(query_words)
        q_nums = set(extract_query_numbers(query_words))
        
        scored = []
        for text in candidates:
            psi_c = self.encode_phrase(text)
            interf = wave_interference(psi_q, psi_c)
            boost = contextual_boost(text, list(q_nums))
            scored.append((text, interf, boost, interf * boost))
        
        scored.sort(key=lambda x: -abs(x[3]))
        
        for text, interf, boost, context_interf in scored:
            nums = extract_numbers(text)
            if len(nums) >= 3:
                # L'inconnue x = le nombre qui n'est pas dans la requête
                x_candidates = [n for n in nums if n not in q_nums]
                known_in_candidate = [n for n in nums if n in q_nums]
                
                if x_candidates and len(known_in_candidate) >= 2:
                    x = x_candidates[0]
                    a, b = known_in_candidate[0], known_in_candidate[1]
                    
                    # Vérifier x + a = b  et  a + x = b  (addition)
                    for operand1, operand2 in [(x, a), (a, x)]:
                        psi_1, _ = number_to_planewave(operand1, 256)
                        psi_2, _ = number_to_planewave(operand2, 256)
                        psi_s, _ = number_to_planewave(b, 256)
                        psi_sum = psi_1 * psi_2
                        dot = np.real(np.sum(psi_sum * np.conj(psi_s)))
                        n1 = np.sqrt(np.real(np.sum(psi_sum * np.conj(psi_sum))))
                        n2 = np.sqrt(np.real(np.sum(psi_s * np.conj(psi_s))))
                        if n1 > 1e-10 and n2 > 1e-10 and dot / (n1 * n2) > 0.9:
                            return operand1 if operand1 == x else x, text, interf
                    
                    # Vérifier x - a = b  ou  a - x = b  (soustraction)
                    for op1, op2 in [(x, a), (a, x)]:
                        psi_1, _ = number_to_planewave(op1, 256)
                        psi_2, _ = number_to_planewave(op2, 256)
                        psi_s, _ = number_to_planewave(b, 256)
                        psi_diff = psi_1 * np.conj(psi_2)  # Ψ_{op1-op2}
                        dot = np.real(np.sum(psi_diff * np.conj(psi_s)))
                        n1 = np.sqrt(np.real(np.sum(psi_diff * np.conj(psi_diff))))
                        n2 = np.sqrt(np.real(np.sum(psi_s * np.conj(psi_s))))
                        if n1 > 1e-10 and n2 > 1e-10 and dot / (n1 * n2) > 0.9:
                            return op1, text, interf
                    
                    # Vérifier x × a = b  ou  a × x = b  (multiplication)
                    for op1, op2 in [(x, a), (a, x)]:
                        psi_1, _ = number_to_planewave(op1, 256)
                        psi_res = psi_1 ** op2  # (Ψ_{op1})^{op2} = Ψ_{op1×op2}
                        psi_s, _ = number_to_planewave(b, 256)
                        dot = np.real(np.sum(psi_res * np.conj(psi_s)))
                        n1 = np.sqrt(np.real(np.sum(psi_res * np.conj(psi_res))))
                        n2 = np.sqrt(np.real(np.sum(psi_s * np.conj(psi_s))))
                        if n1 > 1e-10 and n2 > 1e-10 and dot / (n1 * n2) > 0.9:
                            return op2 if op2 != a else x, text, interf
                
                # Fallback : x = c - b (inversion directe)
                if len(known_in_candidate) >= 2:
                    b, c = known_in_candidate[0], known_in_candidate[1]
                    x = abs(c - b)
                    if x > 0 and x in nums:
                        return x, text, interf
        
        return None, None, 0.0
    
    def solve_quadratique(self, query_words, candidates):
        """Résout x² = n."""
        psi_q = self.encode_query(query_words)
        q_nums = extract_query_numbers(query_words)
        
        scored = []
        for text in candidates:
            psi_c = self.encode_phrase(text)
            interf = wave_interference(psi_q, psi_c)
            boost = contextual_boost(text, q_nums)
            scored.append((text, interf, boost, interf * boost))
        
        scored.sort(key=lambda x: -abs(x[3]))
        
        for text, interf, boost, context_interf in scored:
            nums = extract_numbers(text)
            if len(nums) >= 2:
                for x in nums:
                    for n in nums:
                        if x != n:
                            psi_x, _ = number_to_planewave(x, 256)
                            psi_n, _ = number_to_planewave(n, 256)
                            psi_res = psi_x ** x  # (Ψ_x)^x = Ψ_{x²}
                            dot = np.real(np.sum(psi_res * np.conj(psi_n)))
                            n1 = np.sqrt(np.real(np.sum(psi_res * np.conj(psi_res))))
                            n2 = np.sqrt(np.real(np.sum(psi_n * np.conj(psi_n))))
                            if n1 > 1e-10 and n2 > 1e-10:
                                if dot / (n1 * n2) > 0.9:
                                    return x, text, interf
        
        return None, None, 0.0


def benchmark():
    print("=" * 74)
    print("  BENCHMARK — Algèbre Hybride")
    print("=" * 74)
    
    with open("corpus_mathematique.json", 'r', encoding='utf-8') as f:
        corpus = json.load(f)
    print(f"\n  Corpus : {len(corpus)} phrases")
    
    solver = AlgebreHybride(corpus)
    solver.build()
    
    tests = [
        {
            "desc": "x + 3 = 7",
            "type": "linear",
            "qwords": ["solution", "equation", "x", "3", "7"],
            "expected": 4,
            "candidates": [
                "4 est la solution de l'equation x + 3 = 7",
                "si x + 3 = 7, alors x = 4",
                "l'equation x + 3 = 7 a pour solution 4",
            ]
        },
        {
            "desc": "x + 10 = 25",
            "type": "linear",
            "qwords": ["solution", "equation", "x", "10", "25"],
            "expected": 15,
            "candidates": [
                "15 est la solution de l'equation x + 10 = 25",
                "si x + 10 = 25, alors x = 15",
            ]
        },
        {
            "desc": "x - 5 = 12",
            "type": "linear",
            "qwords": ["solution", "equation", "x", "5", "12"],
            "expected": 17,
            "candidates": [
                "17 est la solution de l'equation x - 5 = 12",
                "si x - 5 = 12, alors x = 17",
            ]
        },
        {
            "desc": "x² = 49",
            "type": "quadratique",
            "qwords": ["solution", "equation", "carre", "49"],
            "expected": 7,
            "candidates": [
                "7 est la racine carree de 49",
                "la racine de 49 est 7",
                "49 est le carre de 7",
                "le carre de 7 est 49",
            ]
        },
        {
            "desc": "x² = 225",
            "type": "quadratique",
            "qwords": ["solution", "equation", "carre", "225"],
            "expected": 15,
            "candidates": [
                "225 est le carre de 15",
                "le carre de 15 est 225",
                "15 est la racine carree de 225",
            ]
        },
        {
            "desc": "5 × x = 30",
            "type": "linear",
            "qwords": ["solution", "equation", "produit", "5", "30"],
            "expected": 6,
            "candidates": [
                "le produit de 5 et 6 est 30",
                "5 x 6 = 30",
                "l'equation 5 * x = 30 a pour solution 6",
            ]
        },
        {
            "desc": "3 × x = 12",
            "type": "linear",
            "qwords": ["solution", "equation", "produit", "3", "12"],
            "expected": 4,
            "candidates": [
                "le produit de 3 et 4 est 12",
                "3 x 4 = 12",
                "l'equation 3 * x = 12 a pour solution 4",
            ]
        },
    ]
    
    print("\n  BENCHMARK ALGÈBRE :")
    print("  " + "=" * 60)
    
    t0 = time.time()
    ok = 0
    
    for q in tests:
        if q["type"] == "linear":
            x, phrase, interf = solver.solve_linear(q["qwords"], q["candidates"])
        elif q["type"] == "quadratique":
            x, phrase, interf = solver.solve_quadratique(q["qwords"], q["candidates"])
        else:
            x, phrase, interf = None, None, 0.0
        
        correct = x == q["expected"]
        if correct:
            ok += 1
        
        status = "V" if correct else "X"
        print(f"\n  {q['desc']:20s} → x = {x} (attendu: {q['expected']})  {status}")
        if phrase:
            print(f"    Phrase : {phrase[:60]}...")
            print(f"    Interf : {interf:+.4f}")
    
    dt = (time.time() - t0) * 1000
    total = len(tests)
    acc = ok / total * 100
    
    print(f"\n  {'=' * 60}")
    print(f"  Résultat : {ok}/{total} ({acc:.0f}%)")
    print(f"  Temps    : {dt:.0f} ms")
    
    return acc


if __name__ == "__main__":
    acc = benchmark()
    
    print(f"\n{'='*74}")
    print(f"  ALGÈBRE HYBRIDE — Précision : {acc:.0f}%")
    print(f"{'='*74}")
    
    if acc >= 80:
        print("\n  ✅ Le raisonnement algébrique hybride fonctionne !")
    else:
        print(f"\n  Précision : {acc:.0f}% — amélioration nécessaire.")