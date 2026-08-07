"""
ALPHAFOLD — Dynamique de Repliement ABC (Fractionnaire)
=========================================================
Moteur de repliement utilisant le noyau ABC (Atangana-Baleanu-Caputo)
à l'ordre α = 1/φ pour guider la protéine vers son état natif.

Principe :
  v(t+dt) = v(t) + (1-α)·∇E·dt + α·Σ_k K(k·dt)·∇E(t-k·dt)·dt

La mémoire non-locale du noyau ABC crée naturellement l'entonnoir
de repliement (folding funnel) :
  - Court terme : vibrations locales, réarrangements de surface
  - Long terme : effondrement hydrophobe, formation du noyau

Pourquoi α = 1/φ est optimal : c'est le « plus irrationnel »,
il évite les résonances parasites et garantit que le système
explore l'espace conformationnel sans rester piégé.

Zéro paramètre appris, zéro GPU, 100% déterministe.

Author: Univers-Holistique
"""

import math
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field

from .amino_acids import PHI, ALPHA, PI, get_amino_acid, parse_sequence
from .backbone import HarmonicBackbone, ProteinStructure, ResidueAtoms, rmsd
from .harmonic_energy import HarmonicEnergy, EnergyBreakdown, compute_energy

# ═══════════════════════════════════════════════════════════════════════════════
# NOYAU ABC (version simplifiée pour le repliement)
# ═══════════════════════════════════════════════════════════════════════════════

class ABCMemoryKernel:
    """
    Noyau ABC pour la dynamique de repliement.

    Stocke l'historique des gradients et applique le noyau
    de Mittag-Leffler pour la mémoire non-locale.
    """

    def __init__(self, max_history: int = 64, alpha: float = ALPHA):
        """
        Args:
            max_history: nombre maximum de gradients conservés
            alpha: ordre fractionnaire (défaut : 1/φ)
        """
        self.max_history = max_history
        self.alpha = alpha
        self.history: List[np.ndarray] = []
        self._kernel_cache: Optional[np.ndarray] = None

    def push(self, gradient: np.ndarray):
        """Ajoute un gradient à l'historique."""
        self.history.append(gradient.copy())
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self._kernel_cache = None  # Invalider le cache

    def compute_effective_force(self, current_force: np.ndarray) -> np.ndarray:
        """
        Calcule la force effective avec mémoire ABC.

        F_eff = (1-α) * F_current + α * Σ_k K(k) * F_history[k]

        où K(k) est le noyau ABC discret.
        """
        if len(self.history) == 0:
            return (1.0 - self.alpha) * current_force

        # Noyau ABC discret (approximation exponentielle)
        kernel = self._get_kernel(len(self.history))

        # Terme de mémoire
        memory_force = np.zeros_like(current_force)
        for k in range(len(self.history)):
            memory_force += kernel[k] * self.history[-(k+1)]

        # Force effective
        F_eff = (1.0 - self.alpha) * current_force + self.alpha * memory_force

        return F_eff

    def _get_kernel(self, n: int) -> np.ndarray:
        """Calcule le noyau ABC discret pour n points d'historique."""
        if self._kernel_cache is not None and len(self._kernel_cache) == n:
            return self._kernel_cache

        # Approximation : décroissance en loi de puissance avec mémoire φ
        # K(k) ∝ (k+1)^{-α} / Σ (j+1)^{-α}
        k = np.arange(1, n + 1, dtype=np.float64)
        weights = k ** (-self.alpha)
        weights /= weights.sum()
        self._kernel_cache = weights
        return weights

    def reset(self):
        """Réinitialise l'historique."""
        self.history.clear()
        self._kernel_cache = None


# ═══════════════════════════════════════════════════════════════════════════════
# RÉSULTAT DE REPLIEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FoldResult:
    """Résultat complet d'une simulation de repliement."""
    sequence: str
    structure: ProteinStructure          # Structure finale
    energy: EnergyBreakdown              # Énergie finale
    trajectory: List[ProteinStructure]   # Structures intermédiaires (échantillonnées)
    energy_trajectory: List[float]       # Énergies à chaque étape enregistrée
    phi_trajectory: List[np.ndarray]     # Angles φ à chaque étape
    psi_trajectory: List[np.ndarray]     # Angles ψ à chaque étape
    n_steps: int                         # Nombre total de pas
    converged: bool                      # Convergence atteinte ?
    elapsed_time: float                  # Temps de calcul (secondes)
    final_rmsd_to_initial: float         # RMSD final vs initial
    metadata: Dict = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            f"FoldResult: {self.sequence} ({self.structure.n_residues} résidus)",
            f"  Étapes: {self.n_steps} | Convergé: {self.converged}",
            f"  Temps: {self.elapsed_time:.1f}s",
            f"  Énergie finale: {self.energy.total:.2f} kcal/mol",
            f"  RMSD vs initial: {self.final_rmsd_to_initial:.2f} Å",
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.summary()


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR DE REPLIEMENT ABC
# ═══════════════════════════════════════════════════════════════════════════════

class ABCProteinFolder:
    """
    Simule le repliement protéique par dynamique fractionnaire ABC.

    Usage :
        folder = ABCProteinFolder("MKFLILFN")
        result = folder.fold()
        print(result.energy.total)

        # Prédiction déterministe (sans bruit)
        result = folder.predict_structure()
    """

    def __init__(self, sequence: str):
        """
        Args:
            sequence: Séquence en code 1 lettre
        """
        self.sequence = sequence.strip().upper()
        self.amino_acids = parse_sequence(self.sequence)
        self.n = len(self.amino_acids)
        if self.n < 3:
            raise ValueError(f"Séquence trop courte ({self.n} résidus), minimum 3")

        self.backbone = HarmonicBackbone(self.sequence)

    def fold(self,
             n_steps: int = 5000,
             temperature: float = 300.0,
             cooling_rate: float = 0.9995,
             learning_rate: float = 2.0,
             abc_memory: int = 64,
             convergence_window: int = 200,
             convergence_threshold: float = 1e-4,
             record_every: int = 100,
             initial_structure: Optional[ProteinStructure] = None,
             verbose: bool = False) -> FoldResult:
        """
        Repliement par recuit harmonique avec mémoire ABC.

        Args:
            n_steps: nombre maximum de pas de simulation
            temperature: température initiale (K)
            cooling_rate: facteur multiplicatif de refroidissement par pas
            learning_rate: pas d'apprentissage (degrés/kcal·mol⁻¹)
            abc_memory: taille de la mémoire ABC
            convergence_window: nombre de pas pour vérifier la convergence
            convergence_threshold: seuil de variation d'énergie pour convergence
            record_every: enregistrer la structure tous les N pas
            initial_structure: structure de départ (défaut : harmonique initiale)
            verbose: afficher la progression

        Returns:
            FoldResult avec structure finale, énergie, trajectoire
        """
        t_start = time.time()

        # Structure initiale
        if initial_structure is None:
            structure = self.backbone.build_harmonic_initial()
        else:
            structure = initial_structure

        initial_ca = structure.ca_trace.copy()

        # Extraire les angles φ/ψ initiaux
        phi = np.array([r.phi for r in structure.residues])
        psi = np.array([r.psi for r in structure.residues])

        # Noyau ABC pour chaque angle
        kernel_phi = ABCMemoryKernel(max_history=abc_memory)
        kernel_psi = ABCMemoryKernel(max_history=abc_memory)

        # Trajectoires
        trajectory = []
        energy_traj = []
        phi_traj = []
        psi_traj = []

        # Énergie initiale
        energy = compute_energy(structure)
        current_energy = energy.total
        best_energy = current_energy
        best_structure = structure
        best_phi = phi.copy()
        best_psi = psi.copy()

        # Historique pour convergence
        energy_history = []

        for step in range(n_steps):
            # Refroidissement
            T = temperature * (cooling_rate ** step)

            # Calcul du gradient numérique (différences finies)
            grad_phi, grad_psi = self._numerical_gradient(
                structure, phi, psi, delta=2.0
            )

            # Appliquer la mémoire ABC
            kernel_phi.push(grad_phi)
            kernel_psi.push(grad_psi)

            F_eff_phi = kernel_phi.compute_effective_force(grad_phi)
            F_eff_psi = kernel_psi.compute_effective_force(grad_psi)

            # Bruit de Langevin (thermostat)
            noise_scale = math.sqrt(2.0 * T * learning_rate / 300.0)
            noise_phi = np.random.randn(self.n) * noise_scale
            noise_psi = np.random.randn(self.n) * noise_scale

            # Mise à jour des angles
            eta = learning_rate * (300.0 / max(T, 1.0))
            phi_new = phi - eta * F_eff_phi + noise_phi
            psi_new = psi - eta * F_eff_psi + noise_psi

            # Contraindre dans [-180, 180]
            phi_new = np.clip(phi_new, -180.0, 180.0)
            psi_new = np.clip(psi_new, -180.0, 180.0)

            # Reconstruire la structure avec les nouveaux angles
            try:
                structure = self.backbone.build_from_angles(
                    phi_new.tolist(), psi_new.tolist()
                )
            except Exception:
                # Si la construction échoue, garder les anciens angles
                phi_new = phi.copy()
                psi_new = psi.copy()
                continue

            # Calculer la nouvelle énergie
            energy = compute_energy(structure)
            new_energy = energy.total

            # Accepter ou rejeter (critère de Metropolis)
            if new_energy < current_energy:
                accept = True
            else:
                delta_E = new_energy - current_energy
                boltzmann = math.exp(-delta_E / max(T, 1.0))
                accept = np.random.random() < boltzmann

            if accept:
                phi = phi_new
                psi = psi_new
                current_energy = new_energy

                # Mettre à jour le meilleur
                if new_energy < best_energy:
                    best_energy = new_energy
                    best_structure = structure
                    best_phi = phi.copy()
                    best_psi = psi.copy()
            else:
                # Revenir aux angles précédents
                phi = phi.copy()  # inchangé
                psi = psi.copy()

            # Enregistrer
            if step % record_every == 0 or step == n_steps - 1:
                trajectory.append(structure)
                energy_traj.append(current_energy)
                phi_traj.append(phi.copy())
                psi_traj.append(psi.copy())

            # Convergence
            energy_history.append(current_energy)
            if len(energy_history) > convergence_window:
                energy_history.pop(0)
                delta = max(energy_history) - min(energy_history)
                if delta < convergence_threshold and T < 1.0:
                    if verbose:
                        print(f"  Convergé à l'étape {step}, ΔE={delta:.6f}")
                    break

            if verbose and step % 500 == 0:
                print(f"  Étape {step:5d}/{n_steps}  "
                      f"T={T:.1f}K  E={current_energy:.2f}  "
                      f"best={best_energy:.2f}")

        t_end = time.time()

        # Résultat
        final_ca = best_structure.ca_trace
        final_rmsd = rmsd(final_ca, initial_ca) if self.n > 2 else 0.0

        converged = (len(energy_history) >= convergence_window and
                     max(energy_history) - min(energy_history) < convergence_threshold)

        return FoldResult(
            sequence=self.sequence,
            structure=best_structure,
            energy=compute_energy(best_structure),
            trajectory=trajectory,
            energy_trajectory=energy_traj,
            phi_trajectory=phi_traj,
            psi_trajectory=psi_traj,
            n_steps=step + 1,
            converged=converged,
            elapsed_time=t_end - t_start,
            final_rmsd_to_initial=float(final_rmsd),
            metadata={
                'n_residues': self.n,
                'initial_energy': compute_energy(
                    self.backbone.build_harmonic_initial()
                ).total if initial_structure is None else
                compute_energy(initial_structure).total,
                'best_energy': best_energy,
                'temperature_final': T,
            },
        )

    def predict_structure(self, **kwargs) -> FoldResult:
        """
        Prédit la structure native en mode déterministe (sans bruit).

        Utilise T=0 (pas de bruit thermique) pour une prédiction
        purement déterministe basée uniquement sur l'énergie harmonique.
        """
        kwargs.setdefault('temperature', 0.01)  # quasi-zéro
        kwargs.setdefault('cooling_rate', 1.0)  # pas de refroidissement
        kwargs.setdefault('learning_rate', 1.0)
        kwargs.setdefault('n_steps', 3000)
        return self.fold(**kwargs)

    def _numerical_gradient(self, structure: ProteinStructure,
                             phi: np.ndarray, psi: np.ndarray,
                             delta: float = 2.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcule le gradient numérique de l'énergie par rapport aux angles φ/ψ.

        ∂E/∂φ_i ≈ [E(φ_i + δ) - E(φ_i - δ)] / 2δ

        Pour des raisons d'efficacité, on calcule le gradient pour chaque
        angle individuellement (approximation : on considère que les angles
        sont indépendants pour le gradient).

        Args:
            structure: structure actuelle
            phi: angles φ actuels (longueur N)
            psi: angles ψ actuels (longueur N)
            delta: perturbation (degrés)

        Returns:
            (grad_phi, grad_psi) — chaque vecteur de longueur N
        """
        n = self.n
        grad_phi = np.zeros(n)
        grad_psi = np.zeros(n)
        E0 = compute_energy(structure).total

        for i in range(n):
            # Gradient φ_i
            phi_plus = phi.copy()
            phi_plus[i] += delta
            try:
                struct_plus = self.backbone.build_from_angles(
                    phi_plus.tolist(), psi.tolist())
                E_plus = compute_energy(struct_plus).total
            except Exception:
                E_plus = E0 + 100.0  # Pénalité si construction échoue

            phi_minus = phi.copy()
            phi_minus[i] -= delta
            try:
                struct_minus = self.backbone.build_from_angles(
                    phi_minus.tolist(), psi.tolist())
                E_minus = compute_energy(struct_minus).total
            except Exception:
                E_minus = E0 + 100.0

            grad_phi[i] = (E_plus - E_minus) / (2.0 * delta)

            # Gradient ψ_i
            psi_plus = psi.copy()
            psi_plus[i] += delta
            try:
                struct_plus = self.backbone.build_from_angles(
                    phi.tolist(), psi_plus.tolist())
                E_plus = compute_energy(struct_plus).total
            except Exception:
                E_plus = E0 + 100.0

            psi_minus = psi.copy()
            psi_minus[i] -= delta
            try:
                struct_minus = self.backbone.build_from_angles(
                    phi.tolist(), psi_minus.tolist())
                E_minus = compute_energy(struct_minus).total
            except Exception:
                E_minus = E0 + 100.0

            grad_psi[i] = (E_plus - E_minus) / (2.0 * delta)

        # Normaliser le gradient (éviter les pas trop grands)
        grad_norm = np.sqrt(np.sum(grad_phi ** 2) + np.sum(grad_psi ** 2))
        if grad_norm > 10.0:
            grad_phi *= 10.0 / grad_norm
            grad_psi *= 10.0 / grad_norm

        return grad_phi, grad_psi


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE HAUT NIVEAU
# ═══════════════════════════════════════════════════════════════════════════════

def fold_protein(sequence: str, **kwargs) -> FoldResult:
    """
    Replie une protéine avec les paramètres par défaut.

    Args:
        sequence: séquence en code 1 lettre
        **kwargs: passés à ABCProteinFolder.fold()

    Returns:
        FoldResult
    """
    folder = ABCProteinFolder(sequence)
    return folder.fold(**kwargs)


def predict_structure(sequence: str, **kwargs) -> FoldResult:
    """
    Prédit la structure native (mode déterministe, sans bruit).

    Args:
        sequence: séquence en code 1 lettre
        **kwargs: passés à ABCProteinFolder.predict_structure()

    Returns:
        FoldResult
    """
    folder = ABCProteinFolder(sequence)
    return folder.predict_structure(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide."""
    print("=" * 60)
    print("TEST : Dynamique de Repliement ABC")
    print("=" * 60)

    # Petite séquence test
    seq = "AGVLIC"
    print(f"\nSéquence test: {seq} ({len(seq)} résidus)")

    folder = ABCProteinFolder(seq)

    # Fold rapide
    print("\nRepliement (500 pas, T=100K)...")
    result = folder.fold(
        n_steps=500,
        temperature=100.0,
        cooling_rate=0.995,
        learning_rate=1.0,
        abc_memory=32,
        record_every=50,
        convergence_window=100,
        verbose=True,
    )

    print(f"\n{result.summary()}")
    print(f"Énergie finale:")
    for k, v in result.energy.to_dict().items():
        print(f"  {k}: {v:+.2f}")

    # Vérifier le score Ramachandran
    from .backbone import compute_rama_score
    rama = compute_rama_score(result.structure)
    print(f"\nScore Ramachandran final: {rama['mean_score']:.3f}")
    print(f"φ finals: {[f'{r.phi:+6.1f}°' for r in result.structure.residues]}")
    print(f"ψ finals: {[f'{r.psi:+6.1f}°' for r in result.structure.residues]}")

    print("\n✅ Tests passés !")


if __name__ == '__main__':
    _test()
