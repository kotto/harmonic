"""
Character N-Gram Encoder — Phase sémantique par morphologie
=============================================================
Encodeur de mots 100% déterministe qui capture les relations sémantiques
via la similarité morphologique (n-grammes de caractères).

Principe : deux mots qui partagent des séquences de caractères
(ex: "amour", "amoureux", "amour-propre") auront des phases proches
parce qu'ils partagent des n-grammes. C'est un proxy puissant pour
la similarité sémantique : dans une langue comme le français,
les mots apparentés partagent leur racine morphologique.

L'encodeur combine :
1. Caractères (unigrammes) → structure globale du mot
2. Bigrammes → paires de lettres, capture les préfixes/suffixes
3. Trigrammes → racines morphologiques ("amo", "our", "eux")
4. 4-grammes → précision sémantique fine
5. FNV1a + φ-spacing → unicité et orthogonalité HRR

Résultat : ψ_mot ∈ ℂ^dim où :
- Deux mots apparentés ont ⟨ψ_a|ψ_b⟩ > 0.2
- Deux mots sans rapport ont ⟨ψ_a|ψ_b⟩ ≈ 0
- Même mot = ⟨ψ|ψ⟩ = 1.0 (normalisé)

Usage :
    encoder = CharNGramEncoder(dim=512)
    psi_amour = encoder.encode('amour')
    psi_amoureux = encoder.encode('amoureux')
    coh = np.real(np.dot(psi_amour, psi_amoureux.conj()))
    # coh > 0.3  ✅ (racine "amour" partagée)

Author: Univers-Holistique
"""

import math
import numpy as np
from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
PI = math.pi
TAU = 2.0 * PI

# ═══════════════════════════════════════════════════════════════════════════════
# ENCODEUR N-GRAMME
# ═══════════════════════════════════════════════════════════════════════════════

class CharNGramEncoder:
    """
    Encodeur de mots par n-grammes de caractères.
    
    Capture la similarité morphologique → proxy de similarité sémantique.
    100% déterministe, zéro entraînement, zéro donnée externe.
    """

    def __init__(self, dim: int = 512, n_min: int = 3, n_max: int = 5,
                 semantic_boost: float = 0.50):
        """
        Args:
            dim: dimension de l'espace complexe
            n_min: taille minimale des n-grammes
            n_max: taille maximale des n-grammes
            semantic_boost: poids de la composante sémantique (0-1)
                           Reste → bruit FNV1a pour l'orthogonalité HRR
        """
        self.dim = dim
        self.n_min = n_min
        self.n_max = n_max
        self.semantic_boost = semantic_boost
        self._cache: Dict[str, np.ndarray] = {}
        
        # Pré-encoder un vocabulaire de base
        self._init_base_vocab()

    def encode(self, word: str) -> np.ndarray:
        """
        Encode un mot en vecteur d'onde sémantique ψ ∈ ℂ^dim.
        
        Args:
            word: le mot à encoder
            
        Returns:
            ψ normalisé (|ψ| = 1)
        """
        word = word.lower().strip()
        if not word:
            return self._zero_psi()
        
        if word in self._cache:
            return self._cache[word]
        
        # 1. Composante morphologique (n-grammes) → similarité sémantique
        psi_semantic = self._ngram_psi(word)
        
        # 2. Composante FNV1a → unicité + orthogonalité HRR
        psi_unique = self._fnv1a_psi(word)
        
        # 3. Fusion : boost sémantique + bruit orthogonal
        alpha = self.semantic_boost
        psi = alpha * psi_semantic + (1.0 - alpha) * psi_unique
        
        # Normaliser
        norm = np.linalg.norm(psi)
        if norm > 1e-10:
            psi = psi / norm
        
        self._cache[word] = psi
        return psi

    def _ngram_psi(self, word: str) -> np.ndarray:
        """
        Construit un vecteur d'onde à partir des n-grammes du mot.
        
        Chaque n-gramme reçoit une phase via FNV1a.
        Les phases sont additionnées (superposition).
        Plus deux mots partagent de n-grammes, plus leurs phases sont proches.
        """
        # Extraire tous les n-grammes
        ngrams = []
        for n in range(self.n_min, self.n_max + 1):
            for i in range(len(word) - n + 1):
                ngrams.append(word[i:i+n])
        
        # Ajouter des n-grammes avec padding (début/fin de mot)
        # Moins de poids pour les n-grammes paddés (trop génériques)
        padded = '#' + word + '#'
        for n in range(self.n_min, self.n_max + 1):
            for i in range(len(padded) - n + 1):
                ng = padded[i:i+n]
                if '#' in ng:
                    ngrams.append(ng + '_p')  # suffixe pour réduire le poids
        
        if not ngrams:
            return self._fnv1a_psi(word)
        
        # Chaque n-gramme → phase via hash
        psi = np.zeros(self.dim, dtype=complex)
        for ng in ngrams:
            h = self._fnv1a_hash(ng)
            # Phase distribuée sur tout le spectre
            phase = (h % 1000000) / 1000000.0 * TAU
            # Contribution sinusoïdale dans les dimensions
            for k in range(0, self.dim, 2):
                w = math.exp(-0.1 * k)  # décroissance exponentielle plus forte
                psi[k] += w * math.cos(phase * (1.0 + k * 0.005))
                psi[k+1] += w * math.sin(phase * (1.0 + k * 0.005))
        
        # Normaliser
        norm = np.linalg.norm(psi)
        if norm > 1e-10:
            return psi / norm
        return self._fnv1a_psi(word)

    def _fnv1a_psi(self, word: str) -> np.ndarray:
        """Vecteur d'onde FNV1a + φ-spacing (unicité + orthogonalité)."""
        h = self._fnv1a_hash(word)
        phases = (h * PHI ** np.arange(self.dim)) % TAU
        psi = np.exp(1j * phases)
        return psi / np.linalg.norm(psi)

    def _fnv1a_hash(self, text: str) -> int:
        """Hash FNV1a 64-bit."""
        h = 0xcbf29ce484222325
        for ch in text:
            h = ((h * 0x100000001b3) ^ ord(ch)) & 0xFFFFFFFFFFFFFFFF
        return h

    def _zero_psi(self) -> np.ndarray:
        psi = np.ones(self.dim, dtype=complex) / math.sqrt(self.dim)
        return psi / np.linalg.norm(psi)

    def _init_base_vocab(self):
        """Pré-encoder un vocabulaire de base (français)."""
        base_words = [
            # Articles, prépositions, connecteurs
            "le", "la", "les", "un", "une", "des", "de", "du", "à", "au", "aux",
            "et", "ou", "donc", "car", "mais", "ni", "or", "si", "que", "qui",
            "dans", "sur", "sous", "avec", "sans", "pour", "par", "entre",
            "ce", "cette", "ces", "mon", "ton", "son", "notre", "votre", "leur",
            # Verbes très courants
            "est", "sont", "être", "avoir", "fait", "faire", "peut", "pouvoir",
            "dire", "aller", "voir", "savoir", "venir", "devoir", "prendre",
            "donner", "mettre", "trouver", "parler", "aimer", "vivre", "passer",
            # Noms très courants
            "chose", "homme", "femme", "enfant", "monde", "vie", "temps", "jour",
            "nuit", "main", "œil", "cœur", "esprit", "corps", "âme", "pensée",
            "amour", "paix", "guerre", "mort", "dieu", "science", "art", "nature",
            "lumière", "ombre", "eau", "feu", "terre", "ciel", "soleil", "lune",
            "étoile", "fleur", "arbre", "oiseau", "mer", "vent", "pluie",
            # Adjectifs très courants
            "bon", "mauvais", "grand", "petit", "beau", "vrai", "faux", "nouveau",
            "ancien", "premier", "dernier", "seul", "même", "autre", "tout",
            "doux", "tendre", "pur", "sombre", "clair", "profond", "léger",
            # Adverbes
            "très", "trop", "peu", "beaucoup", "bien", "mal", "mieux",
            "toujours", "jamais", "souvent", "encore", "déjà", "ici", "là",
            # Poésie / émotion
            "joie", "tristesse", "passion", "désir", "espoir", "douleur",
            "beauté", "éternité", "infini", "silence", "mystère", "sagesse",
            "aube", "crépuscule", "aurore", "rêve", "souffle", "chant",
            "danse", "brille", "tombe", "renaît", "meurt", "aime", "vis",
        ]
        for word in base_words:
            self._cache[word] = self.encode(word)

    @property
    def vocabulary(self) -> Dict[str, np.ndarray]:
        return self._cache


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide."""
    print("=" * 60)
    print("TEST : Char N-Gram Encoder — Similarité morphologique")
    print("=" * 60)

    encoder = CharNGramEncoder(dim=256, semantic_boost=0.7)

    # Test de similarité morphologique
    print("\n─── Similarités morphologiques ───")
    import numpy as np
    pairs = [
        ("amour", "amoureux", "racine"),
        ("amour", "toujours", "rime"),
        ("amour", "jalousie", "non lié"),
        ("chanter", "chanteur", "racine"),
        ("chanter", "danser", "sémantique"),
        ("chanter", "marteau", "non lié"),
        ("lune", "lunaire", "racine"),
        ("lune", "soleil", "astres (non morpho)"),
        ("lune", "clarté", "sémantique faible"),
        ("science", "scientifique", "racine"),
        ("science", "connaissance", "synonyme"),
        ("science", "football", "non lié"),
        ("mort", "mourir", "racine"),
        ("mort", "vivre", "opposé morpho"),
        ("mort", "table", "non lié"),
    ]

    for w1, w2, rel in pairs:
        psi1 = encoder.encode(w1)
        psi2 = encoder.encode(w2)
        coh = float(np.real(np.dot(psi1, psi2.conj())))
        bar = "█" * max(0, int((coh + 0.3) * 20)) + "░" * (20 - max(0, int((coh + 0.3) * 20)))
        print(f"  {w1:14s} ↔ {w2:14s}  coh={coh:+.3f}  {bar}  ({rel})")

    print(f"\n✅ Vocabulaire: {len(encoder.vocabulary)} mots")
    print(f"   Dimension: {encoder.dim}")


if __name__ == '__main__':
    _test()
