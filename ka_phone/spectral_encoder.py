#!/usr/bin/env python3
"""
KA-Next — SPECTRAL ENCODER (TF-IDF → Ondes)
===============================================
Remplace SHA-256 par un encodage spectral basé sur TF-IDF.
Le sémantique humain = signature spectrale émergente du corpus.

Principe :
  - Chaque mot significatif du corpus reçoit une FRÉQUENCE unique
  - Un texte est la SUPERPOSITION des fréquences de ses mots (spectre)
  - Deux textes sémantiquement proches ont des spectres qui interfèrent
    constructivement (forte résonance)

Ceci est le PONT entre le sens humain et les ondes de l'univers :
  "capitale Dakar" et "capitale Bamako" → spectres proches
  "roi" et "reine" → harmoniques communes dans le spectre

Usage :
  from spectral_encoder import SpectralEncoder
  enc = SpectralEncoder()
  enc.build_vocabulary(all_facts)  # Apprendre les fréquences du corpus
  kx, ky = enc.encode("La capitale du Senegal est Dakar")  # → coordonnées d'onde
"""

import math, hashlib, re
from typing import Dict, List, Tuple, Set
from collections import Counter

PHI = (1 + math.sqrt(5)) / 2


class SpectralEncoder:
    """
    Encodeur spectral : texte → onde (kx, ky) basé sur la distribution
    TF-IDF des mots dans le corpus.
    
    Propriétés :
      - Déterministe (même texte → même onde, pas d'aléatoire)
      - Sémantiquement cohérent (textes proches → ondes proches)
      - Basé sur des principes physiques (fréquences, harmoniques, spectres)
      - Pas de réseau de neurones, pas de boîte noire
    """

    def __init__(self, max_features: int = 4096):
        self.max_features = max_features
        self.word_to_freq: Dict[str, float] = {}  # mot → fréquence unique
        self.word_to_idf: Dict[str, float] = {}   # mot → poids IDF
        self.total_docs = 0
        self.vocab_built = False
        self.word_count = 0

    def build_vocabulary(self, documents: List[str]):
        """
        Construit le vocabulaire spectral à partir d'un corpus de documents.
        
        Pour chaque mot significatif :
          1. Calcul de sa fréquence globale (TF)
          2. Attribution d'une fréquence unique sur le cercle [0, 2π)
          3. Calcul du poids IDF (les mots rares ont plus de poids)
        """
        if not documents:
            return

        print(f"[SpectralEncoder] Construction du vocabulaire sur {len(documents)} documents...")

        # ── Étape 1 : Compter les occurrences ──
        word_doc_count = Counter()  # Dans combien de documents apparaît chaque mot
        word_total_count = Counter()  # Nombre total d'occurrences

        for doc in documents:
            words = self._extract_significant_words(doc)
            unique_words = set(words)
            for w in unique_words:
                word_doc_count[w] += 1
            for w in words:
                word_total_count[w] += 1

        self.total_docs = len(documents)

        # ── Étape 2 : Ordonner les mots par fréquence décroissante ──
        # Les mots les plus fréquents reçoivent les "basses fréquences"
        # Les mots rares reçoivent les "hautes fréquences"
        sorted_words = sorted(word_total_count.items(), key=lambda x: -x[1])

        # Limiter au max_features les plus fréquents
        sorted_words = sorted_words[:self.max_features]

        self.word_count = len(sorted_words)

        # ── Étape 3 : Attribuer une fréquence unique à chaque mot ──
        # On utilise φ (nombre d'or) pour garantir que les fréquences
        # sont maximalement décorrélées (distribution quasi-uniforme sur le cercle)
        for i, (word, count) in enumerate(sorted_words):
            # Fréquence normalisée entre 0 et 2π, distribuée par φ
            freq = (i * PHI * 2 * math.pi) % (2 * math.pi)
            self.word_to_freq[word] = freq

        # ── Étape 4 : Calculer les poids IDF ──
        # IDF = log(N / df) : les mots rares ont plus de poids
        for word in self.word_to_freq:
            df = word_doc_count.get(word, 1)
            self.word_to_idf[word] = math.log(self.total_docs / max(df, 1))

        self.vocab_built = True
        print(f"[SpectralEncoder] Vocabulaire : {self.word_count} mots, "
              f"frequences attribuees par phi")

    def encode(self, text: str, grid_size: int = 64) -> Tuple[float, float]:
        """
        Encode un texte en coordonnées d'onde (kx, ky).
        
        Algorithme :
          1. Extraire les mots significatifs du texte
          2. Pour chaque mot connu, récupérer sa fréquence θ_mot
          3. Calculer l'onde résultante comme la somme vectorielle
             des contributions de chaque mot, pondérée par IDF
          4. Convertir le vecteur résultant en (kx, ky)
        
        Mathématiquement :
          Ψ_texte = Σ_mot (IDF(mot) × e^(i × θ_mot))
          kx = Re(Ψ_texte) / grid_size × 20
          ky = Im(Ψ_texte) / grid_size × 20
        """
        if not self.vocab_built:
            # Fallback SHA-256 si le vocabulaire n'est pas construit
            return self._sha256_fallback(text)

        words = self._extract_significant_words(text)
        if not words:
            return self._sha256_fallback(text)

        # ── Sommer les contributions vectorielles ──
        real_sum = 0.0
        imag_sum = 0.0
        matched = 0

        for word in words:
            if word in self.word_to_freq:
                theta = self.word_to_freq[word]
                weight = self.word_to_idf.get(word, 1.0)
                # Chaque mot contribue comme un vecteur unitaire * poids
                real_sum += weight * math.cos(theta)
                imag_sum += weight * math.sin(theta)
                matched += 1

        if matched == 0:
            return self._sha256_fallback(text)

        # ── Normaliser ──
        # La magnitude est proportionnelle au nombre de mots reconnus
        magnitude = math.sqrt(real_sum ** 2 + imag_sum ** 2)
        if magnitude > 0:
            real_sum /= magnitude
            imag_sum /= magnitude

        # ── Convertir en coordonnées de grille ──
        # L'angle du vecteur résultant donne la position sur la grille
        kx = real_sum * (grid_size / 20) * 10
        ky = imag_sum * (grid_size / 20) * 10

        # S'assurer que les valeurs sont dans une plage raisonnable
        kx = max(-grid_size / 2, min(grid_size / 2, kx))
        ky = max(-grid_size / 2, min(grid_size / 2, ky))

        return kx, ky

    def _extract_significant_words(self, text: str) -> List[str]:
        """Extrait les mots significatifs (>3 lettres, pas de stop words)."""
        # Stop words français
        stop_words = {
            'dans', 'avec', 'pour', 'sur', 'sous', 'dont', 'cette', 'leur',
            'plus', 'tout', 'vous', 'nous', 'alors', 'dites', 'cela', 'comme',
            'bien', 'fait', 'peut', 'tres', 'sont', 'aux', 'une', 'est', 'les',
            'des', 'pas', 'que', 'qui', 'par', 'the', 'and', 'that', 'from',
            'have', 'with', 'what', 'when', 'this', 'they', 'your', 'will',
            'ces', 'elle', 'leur', 'leurs', 'aussi', 'etre', 'avoir', 'faire',
            'entre', 'dont', 'mais', 'donc', 'car', 'tout', 'tous', 'toute',
            'autres', 'autre', 'meme', 'cest', 'sont', 'ete', 'etait',
        }

        words = []
        for w in text.lower().split():
            w = w.strip('.,;:!?()[]{}"\'-').lower()
            if len(w) > 3 and w not in stop_words and not w.isdigit():
                words.append(w)

        return words

    def _sha256_fallback(self, text: str) -> Tuple[float, float]:
        """Fallback SHA-256 si le vocabulaire n'est pas construit."""
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % (64 * 100)) / 100.0
        ky = (int(h[16:32], 16) % (64 * 100)) / 100.0
        return (kx - 32) / 64 * 20, (ky - 32) / 64 * 20

    def encode_to_grid(self, text: str, grid_size: int = 64) -> Tuple[int, int]:
        """Encode et retourne la position sur la grille."""
        kx, ky = self.encode(text, grid_size)
        cx = int(kx * grid_size / 20 + grid_size / 2) % grid_size
        cy = int(ky * grid_size / 20 + grid_size / 2) % grid_size
        return cx, cy

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité sémantique entre deux textes
        via la distance cosinus de leurs ondes spectrales.
        """
        kx1, ky1 = self.encode(text1)
        kx2, ky2 = self.encode(text2)

        dot = kx1 * kx2 + ky1 * ky2
        norm1 = math.sqrt(kx1 ** 2 + ky1 ** 2)
        norm2 = math.sqrt(kx2 ** 2 + ky2 ** 2)

        if norm1 < 1e-10 or norm2 < 1e-10:
            return 0.0

        cos_sim = dot / (norm1 * norm2)
        return max(0.0, min(1.0, abs(cos_sim)))


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test de l'encodeur spectral
    corpus = [
        "La capitale du Senegal est Dakar",
        "La capitale de la France est Paris",
        "La capitale du Mali est Bamako",
        "La capitale de l'Ethiopie est Addis-Abeba",
        "Le Nil est le plus long fleuve du monde 6650 km",
        "Le mont Everest est le plus haut sommet 8849 metres",
        "La gravitation universelle de Newton 1687 F = G * m1 * m2 / r^2",
        "Einstein a publie la relativite generale en 1915",
        "La lumiere voyage a 299792458 metres par seconde",
        "Le Big Bang s'est produit il y a 13.8 milliards d'annees",
        "Stoicisme Zenon -300 : distinguer ce qui depend de nous",
        "Socrate -470 a -399 : Je sais que je ne sais rien",
        "La machine de Turing 1936 definit le calcul universel",
        "Python est un langage de programmation polyvalent",
        "Le football est le sport le plus populaire au monde",
        "Le coeur humain bat environ 100000 fois par jour",
        "La baleine bleue est le plus grand animal 30 metres",
        "Don Quichotte ecrit par Miguel de Cervantes en 1605",
    ]

    enc = SpectralEncoder(max_features=2048)
    enc.build_vocabulary(corpus)

    print(f"\n{'=' * 60}")
    print("  TEST — Encodeur Spectral TF-IDF")
    print(f"{'=' * 60}")
    print(f"  Vocabulaire : {enc.word_count} mots")

    # Test 1 : Même structure syntaxique → doivent être proches
    tests = [
        ("La capitale du Senegal est Dakar", "La capitale du Mali est Bamako",
         "Même structure (capitale X est Y) — attendu : similaire"),
        ("La capitale du Senegal est Dakar", "Le Nil est le plus long fleuve",
         "Sujets complètement différents — attendu : différent"),
        ("Stoicisme Zenon -300 : distinguer ce qui depend de nous",
         "Socrate -470 a -399 : Je sais que je ne sais rien",
         "Deux philosophies — attendu : modérément proche"),
        ("La lumiere voyage a 299792458 metres par seconde",
         "Einstein a publie la relativite generale en 1915",
         "Deux concepts de physique — attendu : modérément proche"),
        ("Python est un langage de programmation polyvalent",
         "Le football est le sport le plus populaire au monde",
         "Sujets totalement distincts — attendu : très différent"),
    ]

    print()
    for text1, text2, description in tests:
        sim = enc.similarity(text1, text2)
        kx1, ky1 = enc.encode(text1)
        kx2, ky2 = enc.encode(text2)
        print(f"  {description}")
        print(f"    Similarité : {sim:.3f}")
        print(f"    Onde 1 : ({kx1:.2f}, {ky1:.2f})")
        print(f"    Onde 2 : ({kx2:.2f}, {ky2:.2f})")
        print()

    print(f"{'=' * 60}")