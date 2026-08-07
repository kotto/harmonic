"""
Beam Search Ondulatoire — Interférence Multi-Chemin
=====================================================
Traduction ondulatoire du beam search des LLM :

  Beam Search → Interférence multi-chemin dans ℂ^512
  B hypothèses partielles → B trajectoires de phase
  Score = Σ log P(token) → Score = Re(ψ_chemin · conj(ψ_cible))
  Élagage → Interférence destructive (chemins en opposition de phase)

Principe : dans l'espace ondulatoire, explorer B chemins simultanément
n'est pas un surcoût — c'est la superposition naturelle. Les chemins
en phase se renforcent ; les chemins en opposition de phase s'annulent.

Author: Univers-Holistique
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

PHI = 1.618033988749895

# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WavePath:
    """Un chemin de phase dans l'espace ondulatoire."""
    tokens: List[str]                    # Mots sur ce chemin
    psi: np.ndarray                      # Vecteur d'onde accumulé
    coherence: float = 0.0               # Cohérence cumulée
    amplitude: float = 1.0               # Amplitude du chemin

    def __repr__(self) -> str:
        return f"WavePath({self.tokens}, coh={self.coherence:.3f})"


# ═══════════════════════════════════════════════════════════════════════════════
# RECHERCHE EN FAISCEAU ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveBeamSearch:
    """
    Recherche en faisceau par interférence ondulatoire.

    Contrairement au beam search des LLM qui évalue chaque hypothèse
    indépendamment, le WaveBeamSearch utilise l'interférence ENTRE chemins :

    - Chemins en phase → renforcement mutuel → amplitude augmentée
    - Chemins en opposition de phase → annulation → élimination naturelle
    - Chemins orthogonaux → coexistent sans interférer

    Usage:
        beams = WaveBeamSearch(vocab, beam_width=5)
        paths = beams.search(psi_context, max_steps=20)
        best = paths[0]  # chemin de plus forte amplitude
    """

    def __init__(self, vocabulary: Optional[Dict[str, np.ndarray]] = None,
                 beam_width: int = 5):
        """
        Args:
            vocabulary: {mot: psi_vector}
            beam_width: nombre de chemins parallèles (B)
        """
        self.vocabulary = vocabulary or {}
        self.beam_width = beam_width

    def search(self, psi_context: np.ndarray,
               max_steps: int = 20,
               interference_strength: float = 0.3) -> List[WavePath]:
        """
        Recherche en faisceau par interférence multi-chemin.

        Args:
            psi_context: vecteur d'onde du contexte initial
            max_steps: nombre maximal de tokens à générer
            interference_strength: force de l'interférence entre chemins (0-1)

        Returns:
            Chemins triés par amplitude décroissante
        """
        # Initialiser les B chemins avec les B meilleurs premiers mots
        scores = self._score_all(psi_context)
        top_b = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:self.beam_width]

        paths = []
        for word, score in top_b:
            psi_word = self.vocabulary[word]
            # psi_chemin = superposition du contexte et du mot
            psi_path = psi_context + psi_word
            psi_path = psi_path / np.linalg.norm(psi_path)
            paths.append(WavePath(
                tokens=[word],
                psi=psi_path,
                coherence=score,
                amplitude=abs(score),
            ))

        # Propagation pas à pas
        for step in range(1, max_steps):
            # Pour chaque chemin, scorer les extensions possibles
            candidates = []

            for path in paths:
                next_scores = self._score_all(path.psi)

                for word, score in list(sorted(next_scores.items(),
                                               key=lambda x: x[1], reverse=True))[:self.beam_width]:
                    psi_word = self.vocabulary[word]
                    psi_new = path.psi + psi_word
                    psi_new = psi_new / np.linalg.norm(psi_new)

                    # Cohérence du nouveau chemin
                    new_coherence = path.coherence + score
                    new_amplitude = abs(new_coherence)

                    candidates.append(WavePath(
                        tokens=path.tokens + [word],
                        psi=psi_new,
                        coherence=new_coherence,
                        amplitude=new_amplitude,
                    ))

            # Interférence entre chemins candidats
            candidates = self._apply_interference(candidates, interference_strength)

            # Garder les B meilleurs chemins par amplitude
            candidates.sort(key=lambda p: p.amplitude, reverse=True)
            paths = candidates[:self.beam_width]

            # Critère d'arrêt : cohérence qui décroît
            if paths and paths[0].coherence < step * 0.1:
                break

        return sorted(paths, key=lambda p: p.amplitude, reverse=True)

    def _score_all(self, psi: np.ndarray) -> Dict[str, float]:
        """Score de cohérence pour tous les mots."""
        scores = {}
        for word, psi_word in self.vocabulary.items():
            score = float(np.real(np.dot(psi, psi_word.conj())))
            scores[word] = score
        return scores

    def _apply_interference(self, paths: List[WavePath],
                            strength: float) -> List[WavePath]:
        """
        Applique l'interférence entre chemins.

        Deux chemins proches en phase se renforcent.
        Deux chemins en opposition de phase s'affaiblissent.
        """
        n = len(paths)
        if n <= 1:
            return paths

        for i in range(n):
            interference = 0.0
            for j in range(n):
                if i == j:
                    continue
                # Cohérence entre les chemins i et j
                cross = float(np.real(np.dot(paths[i].psi, paths[j].psi.conj())))
                interference += cross * strength

            # Ajuster l'amplitude par l'interférence
            paths[i].amplitude += interference
            paths[i].amplitude = max(0.0, paths[i].amplitude)  # pas d'amplitude négative

        return paths

    def best_sequence(self, psi_context: np.ndarray,
                      max_steps: int = 20) -> List[str]:
        """Retourne la meilleure séquence de mots."""
        paths = self.search(psi_context, max_steps)
        return paths[0].tokens if paths else []

    def best_text(self, psi_context: np.ndarray,
                  max_steps: int = 20) -> str:
        """Retourne le meilleur texte (mots séparés par des espaces)."""
        return " ".join(self.best_sequence(psi_context, max_steps))


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def interference_matrix(paths: List[WavePath]) -> np.ndarray:
    """
    Calcule la matrice d'interférence entre chemins.

    M[i,j] = Re(⟨ψ_i | ψ_j⟩)

    M[i,i] = 1 (auto-cohérence parfaite)
    M[i,j] → +1 : chemins en phase (renforcement)
    M[i,j] → -1 : chemins en opposition (annulation)
    M[i,j] → 0 : chemins décorrélés
    """
    n = len(paths)
    M = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            M[i, j] = float(np.real(np.dot(paths[i].psi, paths[j].psi.conj())))
    return M


def select_constructive(paths: List[WavePath],
                         threshold: float = 0.5) -> List[WavePath]:
    """
    Ne garde que les chemins constructivement interférents.

    Un chemin est conservé si sa cohérence moyenne avec les autres
    dépasse le seuil.
    """
    M = interference_matrix(paths)
    mean_coherence = M.mean(axis=1)
    return [p for i, p in enumerate(paths) if mean_coherence[i] >= threshold]


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide."""
    print("=" * 60)
    print("TEST : Beam Search Ondulatoire")
    print("=" * 60)

    # Vocabulaire test
    vocab = {}
    np.random.seed(42)
    for word in ["le", "chat", "dort", "sur", "le", "tapis", "rouge",
                 "le", "chien", "court", "dans", "le", "jardin", "vert"]:
        psi = np.random.randn(512) + 1j * np.random.randn(512)
        vocab[word] = psi / np.linalg.norm(psi)

    # Contexte : "le chat"
    psi_ctx = (vocab["le"] + vocab["chat"])
    psi_ctx = psi_ctx / np.linalg.norm(psi_ctx)

    beams = WaveBeamSearch(vocab, beam_width=3)
    paths = beams.search(psi_ctx, max_steps=5)

    print(f"\nBeam width = {beams.beam_width}")
    print(f"Nombre de chemins trouvés = {len(paths)}")
    for i, path in enumerate(paths):
        print(f"\n  Chemin {i+1}: {' '.join(path.tokens)}")
        print(f"    Cohérence: {path.coherence:.3f}  Amplitude: {path.amplitude:.3f}")

    # Matrice d'interférence
    if len(paths) >= 2:
        M = interference_matrix(paths)
        print(f"\nMatrice d'interférence ({len(paths)}×{len(paths)}):")
        for row in M:
            print(f"  {[f'{v:+.2f}' for v in row]}")

    # Meilleur texte
    best = beams.best_text(psi_ctx, max_steps=5)
    print(f"\nMeilleure séquence: « {best} »")

    print("\n✅ Tests passés !")


if __name__ == '__main__':
    _test()
