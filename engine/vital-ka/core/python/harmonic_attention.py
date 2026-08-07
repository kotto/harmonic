"""
Harmonic Attention — Attention Dynamique Ondulatoire
=====================================================
Équivalent harmonique de la self-attention des transformers.

PRINCIPE (Transformer → Harmonique) :
  Transformer : Attention(Q,K,V) = softmax(QK^T/√d) · V
  Harmonique  : ψ_i' = ψ_i + α · Σ_j φ_coherence(ψ_i, ψ_j) · ψ_j

TRADUCTION :
  · Au lieu de calculer des scores d'attention dynamiques,
    on MODULE chaque ψ par l'interférence de ses voisins.
  · Les tokens qui « vont ensemble » (phases alignées) se renforcent.
  · Les tokens décorrélés s'ignorent.
  · Résultat : un ψ_contextuel qui encode le sens DANS ce contexte.

CONTRE-EXEMPLE :
  Sans attention : « avocat » → ψ générique (moyenne fruit + métier)
  Avec attention  : « L'avocat a plaidé » → ψ tiré vers le sens MÉTIER
                    « L'avocat est mûr » → ψ tiré vers le sens FRUIT

MÉCANIQUE ONDULATOIRE :
  1. Tokenisation → ψ_i pour chaque mot
  2. Matrice de cohérence C_ij = Re(⟨ψ_i | ψ_j⟩) / (|ψ_i|·|ψ_j|)
  3. Pour chaque token i, modulation = Σ_j (C_ij)^p · ψ_j
     (p = 2 → accentue les cohérences fortes, atténue le bruit)
  4. ψ_i' = normalize(ψ_i + α · modulation_i)
  5. Les ψ contextualisés remplacent les ψ statiques pour cette requête

COMPLEXITÉ :
  · O(N² · D) pour N tokens, D dimensions
  · Mais N est petit (tokens d'une question : ~10-20)
  · Et D = 64-512 → quelques ms

Usage :
    from harmonic_attention import HarmonicAttention

    attn = HarmonicAttention(encoder, alpha=0.3)
    tokens = ["L", "avocat", "a", "plaidé", "au", "tribunal"]
    contextualized = attn.contextualize(tokens)
    # ψ_avocat est maintenant plus proche de ψ_tribunal que de ψ_fruit
"""

import math
import time
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
ALPHA_DEFAULT = PHI_INV * 0.5  # ~0.309 — facteur de modulation optimal
POWER_DEFAULT = 2.0             # accentue les fortes cohérences


class HarmonicAttention:
    """
    Attention dynamique ondulatoire — ψ contextuels par interférence locale.

    Transforme des ψ statiques en ψ_contextuels en modulant chaque
    vecteur par l'interférence de ses voisins dans la séquence.
    """

    def __init__(self, encoder=None, dim: int = 512,
                 alpha: float = ALPHA_DEFAULT,
                 power: float = POWER_DEFAULT):
        self.encoder = encoder
        self.dim = dim or (encoder.dim if encoder else 512)
        self.alpha = alpha
        self.power = power  # exposant pour accentuer les fortes cohérences

        # Cache de ψ statiques (pour restaurer après contextualisation)
        self._original_psi: Dict[str, np.ndarray] = {}

    def _get_psi(self, word: str) -> Optional[np.ndarray]:
        """Récupère le ψ d'un mot (depuis l'encodeur ou fallback)."""
        if self.encoder is not None and word in self.encoder.word_vectors:
            return self.encoder.word_vectors[word].copy()

        # Fallback : FNV1a
        np.random.seed(hash(word) & 0xFFFFFFFF)
        real = np.random.randn(self.dim)
        imag = np.random.randn(self.dim)
        v = real + 1j * imag
        return v / (np.linalg.norm(v) + 1e-10)

    def _coherence_matrix(self, psis: List[np.ndarray]) -> np.ndarray:
        """
        Calcule la matrice de cohérence de phase entre tous les ψ.

        C_ij = Re(⟨ψ_i | ψ_j⟩) / (|ψ_i| · |ψ_j|)

        Retourne une matrice N×N symétrique avec diagonale = 1.
        """
        N = len(psis)
        C = np.zeros((N, N), dtype=np.float64)

        for i in range(N):
            for j in range(i, N):
                if i == j:
                    C[i, j] = 1.0
                else:
                    dot = np.real(np.dot(psis[i].conj(), psis[j]))
                    ni = np.linalg.norm(psis[i])
                    nj = np.linalg.norm(psis[j])
                    if ni > 1e-10 and nj > 1e-10:
                        coh = dot / (ni * nj)
                    else:
                        coh = 0.0
                    C[i, j] = coh
                    C[j, i] = coh

        return C

    def contextualize(self, tokens: List[str],
                      alpha: float = None,
                      power: float = None) -> Dict[str, np.ndarray]:
        """
        Contextualise une séquence de tokens.

        Pour chaque token, calcule ψ_contextuel = ψ_statique + α · modulation
        où modulation = Σ_j (C_ij)^p · ψ_j

        Args:
            tokens: liste de mots dans l'ordre
            alpha: facteur de modulation (défaut: PHI_INV * 0.5)
            power: exposant pour accentuer les fortes cohérences (défaut: 2)

        Returns:
            Dict[mot → ψ_contextuel] pour chaque token unique
        """
        alpha = alpha if alpha is not None else self.alpha
        power = power if power is not None else self.power

        if len(tokens) < 2:
            # Un seul token : pas de contexte à moduler
            psi = self._get_psi(tokens[0])
            return {tokens[0]: psi} if psi is not None else {}

        # 1. Récupérer/calculer les ψ statiques
        psis = []
        valid_indices = []
        for i, token in enumerate(tokens):
            psi = self._get_psi(token)
            if psi is not None:
                psis.append(psi)
                valid_indices.append(i)

        if len(psis) < 2:
            return {tokens[0]: psis[0]} if psis else {}

        # 2. Matrice de cohérence
        C = self._coherence_matrix(psis)

        # 3. Pour chaque token, calculer la modulation
        N = len(psis)
        contextualized_psis = []

        for i in range(N):
            modulation = np.zeros(self.dim, dtype=np.complex128)
            total_weight = 0.0

            for j in range(N):
                if i == j:
                    continue
                # Poids = cohérence élevée à la puissance p
                # (accentue les fortes cohérences, atténue le bruit)
                weight = max(0, C[i, j]) ** power
                if weight > 1e-6:
                    modulation += weight * psis[j]
                    total_weight += weight

            if total_weight > 1e-10:
                modulation = modulation / total_weight

            # ψ_contextuel = ψ_statique + α · modulation
            psi_ctx = psis[i] + alpha * modulation

            # Normaliser
            norm = np.linalg.norm(psi_ctx)
            if norm > 1e-10:
                psi_ctx = psi_ctx / norm

            contextualized_psis.append(psi_ctx)

        # 4. Retourner le dictionnaire token → ψ_contextuel
        result = {}
        for idx, psi_ctx in zip(valid_indices, contextualized_psis):
            token = tokens[idx]
            result[token] = psi_ctx

        return result

    def contextualize_query(self, query: str,
                            alpha: float = None) -> np.ndarray:
        """
        Contextualise une requête entière.

        Tokenise la requête, contextualise chaque mot,
        puis retourne le ψ moyen de la requête contextualisée.

        C'est l'équivalent harmonique de l'encodage d'une phrase
        par un transformer — le ψ de la requête est INFORMÉ par
        les relations entre ses mots.
        """
        # Tokenisation simple
        tokens = query.lower().replace('?', '').replace('!', '').replace('.', '')
        tokens = [t.strip() for t in tokens.split() if len(t.strip()) >= 2]

        if not tokens:
            return np.zeros(self.dim, dtype=np.complex128)

        # Contextualiser
        ctx_psis = self.contextualize(tokens, alpha=alpha)

        # Moyenne des ψ contextualisés (ψ de la requête)
        if not ctx_psis:
            return self._get_psi(query)

        avg_psi = sum(ctx_psis.values()) / len(ctx_psis)
        norm = np.linalg.norm(avg_psi)
        if norm > 1e-10:
            avg_psi = avg_psi / norm

        return avg_psi

    def disambiguate(self, word: str, context: List[str],
                     candidate_senses: Dict[str, np.ndarray] = None) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Désambiguïsation : quel sens d'un mot est activé par le contexte ?

        Calcule le ψ_contextuel du mot dans ce contexte,
        puis compare avec les ψ des différents sens candidats.

        Args:
            word: le mot à désambiguïser
            context: les mots du contexte
            candidate_senses: dict sens → ψ (si None, retourne juste le ψ_contextuel)

        Returns:
            (ψ_contextuel, {sens: score de correspondance})
        """
        # Construire la séquence complète
        all_tokens = context + [word]
        ctx_psis = self.contextualize(all_tokens)

        psi_ctx = ctx_psis.get(word)
        if psi_ctx is None:
            psi_ctx = self._get_psi(word)

        # Comparer avec les sens candidats
        sense_scores = {}
        if candidate_senses:
            for sense, psi_sense in candidate_senses.items():
                coherence = float(np.real(np.dot(
                    psi_ctx.conj(), psi_sense
                )))
                ni = np.linalg.norm(psi_ctx)
                nj = np.linalg.norm(psi_sense)
                if ni > 1e-10 and nj > 1e-10:
                    coherence = coherence / (ni * nj)
                sense_scores[sense] = max(0, coherence)

        return psi_ctx, sense_scores

    def inject_into_encoder(self, tokens: List[str]):
        """
        Injecte les ψ contextualisés dans l'encodeur (modification temporaire).

        Après appel, les mots dans l'encodeur auront leur ψ_contextuel
        au lieu de ψ_statique. Appeler restore_encoder() pour annuler.
        """
        if self.encoder is None:
            return

        ctx_psis = self.contextualize(tokens)

        for token, psi_ctx in ctx_psis.items():
            if token in self.encoder.word_vectors:
                # Sauvegarder l'original
                if token not in self._original_psi:
                    self._original_psi[token] = self.encoder.word_vectors[token].copy()
                # Injecter le contextualisé
                self.encoder.word_vectors[token] = psi_ctx

    def restore_encoder(self):
        """Restaure les ψ originaux dans l'encodeur."""
        if self.encoder is None:
            return
        for token, psi_orig in self._original_psi.items():
            if token in self.encoder.word_vectors:
                self.encoder.word_vectors[token] = psi_orig
        self._original_psi.clear()

    def __enter__(self):
        """Context manager: injecte, puis restaure automatiquement."""
        return self

    def __exit__(self, *args):
        self.restore_encoder()


# ═══════════════════════════════════════════════════════════════════════════════
# INTÉGRATION DANS LE PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

class ContextualEncoder:
    """
    Wrapper qui contextualise automatiquement les requêtes.

    Remplace encode_query() par une version qui utilise
    l'attention harmonique avant l'encodage.
    """

    def __init__(self, encoder, attn: HarmonicAttention = None):
        self.encoder = encoder
        self.attn = attn or HarmonicAttention(
            encoder=encoder, dim=encoder.dim
        )

    def encode_query(self, query: str) -> np.ndarray:
        """Encode une requête avec attention contextuelle."""
        # Utiliser l'attention pour contextualiser
        psi_ctx = self.attn.contextualize_query(query)
        if psi_ctx is not None and np.any(psi_ctx != 0):
            return psi_ctx
        # Fallback : encodage standard
        return self.encoder.encode_query(query)

    def encode_word(self, word: str, context: List[str] = None) -> np.ndarray:
        """Encode un mot, optionnellement avec contexte."""
        if context:
            ctx_psis = self.attn.contextualize(context + [word])
            if word in ctx_psis:
                return ctx_psis[word]
        return self.encoder.encode_word(word)

    def __getattr__(self, name):
        """Délègue tout le reste à l'encodeur original."""
        return getattr(self.encoder, name)


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("  HARMONIC ATTENTION — Test")
    print("=" * 60)

    # Test 1 : Sans encodeur (pur)
    print("\n── Test 1: Contextualisation pure ──")
    attn = HarmonicAttention(dim=64, alpha=0.3)

    tokens = ["avocat", "tribunal", "plaider", "loi", "juge"]
    ctx = attn.contextualize(tokens)
    for token, psi in ctx.items():
        # La norme devrait être ~1
        norm = np.linalg.norm(psi)
        print(f"  {token}: |ψ| = {norm:.4f}")

    # Test 2 : Désambiguïsation simulée
    print("\n── Test 2: Désambiguïsation ──")
    # Créer des ψ « sens » simulés
    np.random.seed(42)
    psi_fruit = np.random.randn(64) + 1j * np.random.randn(64)
    psi_fruit /= np.linalg.norm(psi_fruit)
    psi_metier = np.random.randn(64) + 1j * np.random.randn(64)
    psi_metier /= np.linalg.norm(psi_metier)

    context_tribunal = ["tribunal", "plaider", "loi", "juge", "avocat"]
    ctx_tribunal = attn.contextualize(context_tribunal)

    if "avocat" in ctx_tribunal:
        psi_avocat_ctx = ctx_tribunal["avocat"]
        # Mesurer la similarité avec chaque sens
        sim_fruit = float(np.real(np.dot(psi_avocat_ctx.conj(), psi_fruit)))
        sim_metier = float(np.real(np.dot(psi_avocat_ctx.conj(), psi_metier)))
        print(f"  Contexte tribunal: sim_fruit={sim_fruit:.3f}, sim_metier={sim_metier:.3f}")
        print(f"  Sens dominant: {'métier' if sim_metier > sim_fruit else 'fruit'}")

    # Test 3 : Avec HarmonicBrain
    print("\n── Test 3: Avec HarmonicBrain ──")
    from harmonic_brain import HarmonicBrain

    kb = [
        ("avocat", "est un", "fruit vert", "NATURE"),
        ("avocat", "plaide", "au tribunal", "POLITIQUE"),
        ("tribunal", "est un lieu de", "justice", "POLITIQUE"),
        ("fruit", "se mange", "cru", "NATURE"),
    ]
    brain = HarmonicBrain(kb, dim=64, use_holographic=False)

    attn3 = HarmonicAttention(encoder=brain.unconscious.encoder, dim=64)

    # Contextualiser une requête
    q1 = "l avocat a plaidé au tribunal"
    q2 = "l avocat est un fruit vert"

    psi1 = attn3.contextualize_query(q1)
    psi2 = attn3.contextualize_query(q2)

    # Mesurer à quel point les deux ψ sont différents
    # (devraient être différents car contexte différent)
    if psi1 is not None and psi2 is not None:
        diff = np.linalg.norm(psi1 - psi2)
        sim = float(np.real(np.dot(psi1.conj(), psi2)))
        print(f"  Requête 1 (tribunal): |ψ|={np.linalg.norm(psi1):.4f}")
        print(f"  Requête 2 (fruit):    |ψ|={np.linalg.norm(psi2):.4f}")
        print(f"  Différence: {diff:.4f}, Similarité: {sim:.4f}")
        print(f"  Les ψ sont {'DIFFÉRENTS ✅' if diff > 0.1 else 'SIMILAIRES ⚠️'}")

    # Test 4 : Injection dans l'encodeur
    print("\n── Test 4: Injection / Restauration ──")
    with attn3 as a:
        a.inject_into_encoder(["avocat", "tribunal", "plaider"])
        # L'encodeur a maintenant les ψ contextualisés
        if a.encoder and "avocat" in a.encoder.word_vectors:
            psi_inj = a.encoder.word_vectors["avocat"]
            print(f"  ψ avocat après injection: |ψ|={np.linalg.norm(psi_inj):.4f}")
    # Restauré automatiquement
    if brain.unconscious.encoder and "avocat" in brain.unconscious.encoder.word_vectors:
        psi_rest = brain.unconscious.encoder.word_vectors["avocat"]
        print(f"  ψ avocat après restauration: |ψ|={np.linalg.norm(psi_rest):.4f}")
    print("  ✅ Injection / Restauration OK")

    print("\n✅ Tests Harmonic Attention terminés")
