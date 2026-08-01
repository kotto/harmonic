"""
HARMOFOLD — Validation Option C : Scan du Paysage Énergétique
==============================================================
Démontre que la fonction d'énergie harmonique possède INTRINSÈQUEMENT
plusieurs minima locaux — condition nécessaire au fold-switching.

Stratégie (v2 — relaxation locale) :
  1. Construire un peptide en plusieurs conformations idéalisées
     (α-hélice, β-étendu, PPII, α-gauche, harmonique initiale)
  2. Pour CHAQUE conformation, effectuer une descente de gradient
     (sans bruit, sans mémoire ABC) pour trouver le minimum local
     le plus proche → conformation « relaxée »
  3. Comparer les conformations relaxées par RMSD :
     si deux conformations de départ différentes convergent vers
     des structures distinctes (RMSD > 2 Å), le paysage est MULTI-STABLE
  4. Mesurer la barrière énergétique entre les minima distincts
     (interpolation linéaire des angles φ/ψ)

C'est le test le plus propre : on sonde les bassins d'attraction
de la fonction d'énergie avec des points de départ variés.

Zéro donnée externe. Zéro dynamique stochastique.

Author: Univers-Holistique
"""

import math
import sys
import os
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alphafold.amino_acids import (
    PHI, PI, parse_sequence, get_amino_acid, get_harmonic_profile,
)
from alphafold.backbone import HarmonicBackbone, ProteinStructure, rmsd
from alphafold.harmonic_energy import HarmonicEnergy, compute_energy, EnergyBreakdown
from alphafold.peptide_geometry import get_optimal_angles, RAMACHANDRAN_REGIONS


# ═══════════════════════════════════════════════════════════════════════════════
# PEPTIDES DE TEST
# ═══════════════════════════════════════════════════════════════════════════════

DEMO_PEPTIDES = {
    "trp_cage": "NLYIQWLKDGGPSSGRPPPS",   # 20 aa
    "designed": "AKLVAK",                    # 6 aa
    "polyala":  "AAAAAA",                    # 6 aa
    "polyval":  "VVVVVV",                    # 6 aa
}


# ═══════════════════════════════════════════════════════════════════════════════
# CONFORMATIONS DE DÉPART (points de sonde dans l'espace φ/ψ)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Conformation:
    """Une conformation candidate avec ses angles φ/ψ."""
    name: str
    phi: np.ndarray      # degrés, longueur N
    psi: np.ndarray      # degrés, longueur N


def build_starting_conformations(sequence: str) -> List[Conformation]:
    """
    Construit l'ensemble des conformations de départ pour sonder le paysage.
    
    Inclut :
      - Hélice α canonique (φ=-57°, ψ=-47°)
      - Brin β canonique (φ=-135°, ψ=+135°)
      - PPII canonique (φ=-75°, ψ=+150°)
      - α-gauche canonique (φ=+60°, ψ=+45°)
      - Harmonique initiale (φ/ψ optimaux par résidu)
      - 3 conformations aléatoires (exploration non biaisée)
    """
    n = len(sequence)
    amino_acids = parse_sequence(sequence)
    
    confs = [
        Conformation("α-hélice", np.full(n, -57.0), np.full(n, -47.0)),
        Conformation("β-étendu", np.full(n, -135.0), np.full(n, 135.0)),
        Conformation("PPII", np.full(n, -75.0), np.full(n, 150.0)),
    ]
    
    if n <= 12:
        confs.append(Conformation("α-gauche", np.full(n, 60.0), np.full(n, 45.0)))
    
    # Harmonique initiale (angles optimaux par résidu)
    phi_h, psi_h = [], []
    for aa in amino_acids:
        optima = get_optimal_angles(aa)
        if aa.helix_propensity > aa.sheet_propensity and aa.helix_propensity > 0.5:
            best = optima.get('αR', (-63.0, -43.0))
        elif aa.sheet_propensity > 0.5:
            best = optima.get('β', (-119.0, 133.0))
        else:
            best = optima.get('PPII', (-75.0, 150.0))
        phi_h.append(best[0])
        psi_h.append(best[1])
    confs.append(Conformation("harmonique", np.array(phi_h), np.array(psi_h)))
    
    # Conformations aléatoires (graines fixes pour reproductibilité)
    for seed in range(3):
        rng = np.random.RandomState(seed * 42 + 7)
        # Échantillonner dans les régions Ramachandran autorisées
        phi_r = rng.uniform(-150, -30, n)  # majoritairement région négative
        psi_r = rng.uniform(-60, 160, n)
        confs.append(Conformation(f"aléatoire-{seed+1}", phi_r, psi_r))
    
    return confs


# ═══════════════════════════════════════════════════════════════════════════════
# RELAXATION LOCALE (descente de gradient)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RelaxedMinimum:
    """Résultat d'une relaxation locale."""
    start_name: str
    phi_initial: np.ndarray
    psi_initial: np.ndarray
    phi_final: np.ndarray
    psi_final: np.ndarray
    energy_initial: float
    energy_final: float
    energy_breakdown: Dict[str, float]
    n_steps: int
    converged: bool
    gradient_norm_final: float
    
    @property
    def delta_energy(self) -> float:
        return self.energy_initial - self.energy_final


def relax_conformation(
    backbone: HarmonicBackbone,
    conf: Conformation,
    learning_rate: float = 2.0,
    max_steps: int = 200,
    convergence_threshold: float = 1e-3,
    delta_grad: float = 2.0,
    verbose: bool = False,
) -> RelaxedMinimum:
    """
    Relaxe une conformation vers le minimum local le plus proche
    par descente de gradient (sans bruit, sans mémoire ABC).
    
    Algorithme : gradient descent pur sur E(φ,ψ)
      φ ← φ - η · ∂E/∂φ
      ψ ← ψ - η · ∂E/∂ψ
    
    Args:
        backbone: constructeur de squelette
        conf: conformation de départ
        learning_rate: pas d'apprentissage (degrés²/kcal)
        max_steps: nombre maximum d'itérations
        convergence_threshold: seuil sur la norme du gradient
        delta_grad: perturbation pour le gradient numérique (degrés)
        verbose: afficher la progression
    
    Returns:
        RelaxedMinimum avec la conformation relaxée
    """
    n = backbone.n
    phi = conf.phi.copy().astype(float)
    psi = conf.psi.copy().astype(float)
    
    # Énergie initiale
    struct = backbone.build_from_angles(phi.tolist(), psi.tolist())
    e_initial = compute_energy(struct).total
    
    for step in range(max_steps):
        # Construire la structure actuelle
        struct = backbone.build_from_angles(phi.tolist(), psi.tolist())
        e_current = compute_energy(struct).total
        
        # Gradient numérique (même méthode que abc_folder.py)
        grad_phi, grad_psi = _numerical_gradient(
            backbone, struct, phi, psi, delta=delta_grad
        )
        
        grad_norm = np.sqrt(np.sum(grad_phi**2) + np.sum(grad_psi**2))
        
        if grad_norm < convergence_threshold:
            break
        
        # Descente de gradient avec line search simple
        eta = learning_rate / max(1.0, grad_norm)  # normaliser le pas
        
        phi_new = phi - eta * grad_phi
        psi_new = psi - eta * grad_psi
        
        # Contraindre
        phi_new = np.clip(phi_new, -180.0, 180.0)
        psi_new = np.clip(psi_new, -180.0, 180.0)
        
        # Vérifier que l'énergie diminue
        try:
            struct_new = backbone.build_from_angles(phi_new.tolist(), psi_new.tolist())
            e_new = compute_energy(struct_new).total
        except Exception:
            break
        
        if e_new >= e_current:
            # Réduire le pas et réessayer
            eta *= 0.5
            phi_new = phi - eta * grad_phi
            psi_new = psi - eta * grad_psi
            phi_new = np.clip(phi_new, -180.0, 180.0)
            psi_new = np.clip(psi_new, -180.0, 180.0)
            
            try:
                struct_new = backbone.build_from_angles(phi_new.tolist(), psi_new.tolist())
                e_new = compute_energy(struct_new).total
            except Exception:
                break
            
            if e_new >= e_current:
                # Le gradient numérique est trop bruité, on arrête
                break
        
        phi = phi_new
        psi = psi_new
    
    # Énergie finale
    struct_final = backbone.build_from_angles(phi.tolist(), psi.tolist())
    eb_final = compute_energy(struct_final)
    e_final = eb_final.total
    
    # Norme du gradient final
    grad_phi_f, grad_psi_f = _numerical_gradient(
        backbone, struct_final, phi, psi, delta=delta_grad
    )
    grad_norm_final = float(np.sqrt(np.sum(grad_phi_f**2) + np.sum(grad_psi_f**2)))
    
    return RelaxedMinimum(
        start_name=conf.name,
        phi_initial=conf.phi.copy(),
        psi_initial=conf.psi.copy(),
        phi_final=phi,
        psi_final=psi,
        energy_initial=round(e_initial, 3),
        energy_final=round(e_final, 3),
        energy_breakdown=eb_final.to_dict(),
        n_steps=step + 1,
        converged=grad_norm_final < convergence_threshold,
        gradient_norm_final=round(grad_norm_final, 4),
    )


def _numerical_gradient(
    backbone: HarmonicBackbone,
    structure: ProteinStructure,
    phi: np.ndarray,
    psi: np.ndarray,
    delta: float = 2.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Gradient numérique ∂E/∂φ_i et ∂E/∂ψ_i.
    
    Même algorithme que ABCProteinFolder._numerical_gradient().
    """
    n = backbone.n
    grad_phi = np.zeros(n)
    grad_psi = np.zeros(n)
    E0 = compute_energy(structure).total
    
    for i in range(n):
        # ∂E/∂φ_i
        phi_plus = phi.copy(); phi_plus[i] += delta
        try:
            sp = backbone.build_from_angles(phi_plus.tolist(), psi.tolist())
            Ep = compute_energy(sp).total
        except Exception:
            Ep = E0 + 100.0
        
        phi_minus = phi.copy(); phi_minus[i] -= delta
        try:
            sm = backbone.build_from_angles(phi_minus.tolist(), psi.tolist())
            Em = compute_energy(sm).total
        except Exception:
            Em = E0 + 100.0
        
        grad_phi[i] = (Ep - Em) / (2.0 * delta)
        
        # ∂E/∂ψ_i
        psi_plus = psi.copy(); psi_plus[i] += delta
        try:
            sp = backbone.build_from_angles(phi.tolist(), psi_plus.tolist())
            Ep = compute_energy(sp).total
        except Exception:
            Ep = E0 + 100.0
        
        psi_minus = psi.copy(); psi_minus[i] -= delta
        try:
            sm = backbone.build_from_angles(phi.tolist(), psi_minus.tolist())
            Em = compute_energy(sm).total
        except Exception:
            Em = E0 + 100.0
        
        grad_psi[i] = (Ep - Em) / (2.0 * delta)
    
    # Normaliser
    grad_norm = np.sqrt(np.sum(grad_phi**2) + np.sum(grad_psi**2))
    if grad_norm > 10.0:
        grad_phi *= 10.0 / grad_norm
        grad_psi *= 10.0 / grad_norm
    
    return grad_phi, grad_psi


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSE DU PAYSAGE ÉNERGÉTIQUE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LandscapeResult:
    """Résultat complet de l'analyse du paysage."""
    sequence: str
    n_residues: int
    minima: List[RelaxedMinimum]
    distinct_minima: List[List[int]]   # groupes d'indices de minima similaires
    barriers: List[Dict]
    is_multistable: bool
    n_distinct_states: int
    summary_text: str


def cluster_minima_by_rmsd(
    backbone: HarmonicBackbone,
    minima: List[RelaxedMinimum],
    rmsd_threshold: float = 2.5,
) -> List[List[int]]:
    """
    Regroupe les minima par similarité structurale (RMSD).
    
    Deux conformations sont considérées comme le « même » état
    si leur RMSD Cα < rmsd_threshold.
    """
    n = len(minima)
    # Matrice de RMSD
    rmsd_mat = np.zeros((n, n))
    structures = []
    for m in minima:
        struct = backbone.build_from_angles(m.phi_final.tolist(), m.psi_final.tolist())
        structures.append(struct)
    
    for i in range(n):
        for j in range(i+1, n):
            r = rmsd(structures[i].ca_trace, structures[j].ca_trace)
            rmsd_mat[i, j] = r
            rmsd_mat[j, i] = r
    
    # Clustering simple : regroupement par liaison (single-linkage)
    visited = [False] * n
    clusters = []
    
    for i in range(n):
        if visited[i]:
            continue
        cluster = [i]
        visited[i] = True
        # BFS pour trouver tous les minima connectés
        queue = [i]
        while queue:
            cur = queue.pop(0)
            for j in range(n):
                if not visited[j] and rmsd_mat[cur, j] < rmsd_threshold:
                    visited[j] = True
                    cluster.append(j)
                    queue.append(j)
        clusters.append(cluster)
    
    return clusters


def compute_barrier(
    backbone: HarmonicBackbone,
    min_a: RelaxedMinimum,
    min_b: RelaxedMinimum,
    n_steps: int = 60,
) -> Dict:
    """
    Barrière énergétique par interpolation linéaire des angles φ/ψ.
    """
    e_a, e_b = min_a.energy_final, min_b.energy_final
    path_energies = []
    path_rmsd_a = []
    
    struct_a = backbone.build_from_angles(min_a.phi_final.tolist(), min_a.psi_final.tolist())
    
    for i in range(n_steps + 1):
        t = i / n_steps
        phi_t = min_a.phi_final + t * (min_b.phi_final - min_a.phi_final)
        psi_t = min_a.psi_final + t * (min_b.psi_final - min_b.psi_final)
        phi_t = np.clip(phi_t, -180.0, 180.0)
        psi_t = np.clip(psi_t, -180.0, 180.0)
        
        try:
            struct_t = backbone.build_from_angles(phi_t.tolist(), psi_t.tolist())
            e_t = compute_energy(struct_t).total
            r_t = rmsd(struct_t.ca_trace, struct_a.ca_trace)
        except Exception:
            e_t = 1e6
            r_t = 99.0
        
        path_energies.append(round(e_t, 3))
        path_rmsd_a.append(round(float(r_t), 3))
    
    saddle = max(path_energies)
    base = min(e_a, e_b)
    barrier = saddle - base
    
    return {
        'from': min_a.start_name,
        'to': min_b.start_name,
        'e_from': round(e_a, 3),
        'e_to': round(e_b, 3),
        'barrier_kcal_mol': round(barrier, 3),
        'saddle_energy': round(saddle, 3),
        'path_energies': path_energies,
        'path_rmsd_a': path_rmsd_a,
    }


def analyze_landscape(
    sequence: str,
    peptide_name: str = "peptide",
    learning_rate: float = 2.0,
    max_relax_steps: int = 200,
    rmsd_threshold: float = 2.5,
    verbose: bool = True,
) -> LandscapeResult:
    """
    Analyse complète du paysage énergétique harmonique.
    
    1. Génère les conformations de départ
    2. Relaxe chaque conformation par descente de gradient
    3. Cluster les minima relaxés par RMSD
    4. Calcule les barrières entre états distincts
    5. Détermine si le paysage est multi-stable
    """
    backbone = HarmonicBackbone(sequence)
    n = backbone.n
    
    # 1. Conformations de départ
    starting_confs = build_starting_conformations(sequence)
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"ANALYSE DU PAYSAGE ÉNERGÉTIQUE — {peptide_name}")
        print(f"Séquence : {sequence} ({n} résidus)")
        print(f"Conformations de départ : {len(starting_confs)}")
        print(f"{'='*70}")
    
    # 2. Relaxation
    minima = []
    for i, conf in enumerate(starting_confs):
        if verbose:
            print(f"\n  [{i+1}/{len(starting_confs)}] Relaxation : {conf.name}...", end=" ")
        
        result = relax_conformation(
            backbone, conf,
            learning_rate=learning_rate,
            max_steps=max_relax_steps,
            verbose=False,
        )
        minima.append(result)
        
        if verbose:
            delta = result.delta_energy
            status = "✓ convergé" if result.converged else f"⏸ arrêté (|∇E|={result.gradient_norm_final:.2f})"
            print(f"E: {result.energy_initial:.1f} → {result.energy_final:.1f} kcal/mol "
                  f"(Δ={delta:+.1f}), {result.n_steps} étapes, {status}")
    
    # 3. Clustering
    clusters = cluster_minima_by_rmsd(backbone, minima, rmsd_threshold)
    
    if verbose:
        print(f"\n{'─'*70}")
        print(f"CLUSTERING PAR RMSD (seuil = {rmsd_threshold} Å)")
        print(f"{'─'*70}")
        
        for ci, cluster in enumerate(clusters):
            rep = cluster[0]  # représentant (plus basse énergie)
            rep_idx = min(cluster, key=lambda i: minima[i].energy_final)
            rep_min = minima[rep_idx]
            
            members = [minima[i].start_name for i in cluster]
            energies = [minima[i].energy_final for i in cluster]
            
            print(f"\n  État {ci+1} ({len(cluster)} conformation(s)) :")
            print(f"    Énergie : {min(energies):.1f} kcal/mol (min), {max(energies):.1f} (max)")
            print(f"    Membres : {', '.join(members)}")
            print(f"    φ moyens : {[round(float(x), 1) for x in rep_min.phi_final[:5]]}{'...' if n > 5 else ''}")
            print(f"    ψ moyens : {[round(float(x), 1) for x in rep_min.psi_final[:5]]}{'...' if n > 5 else ''}")
    
    # 4. Barrières entre états distincts
    barriers = []
    if len(clusters) >= 2:
        if verbose:
            print(f"\n{'─'*70}")
            print(f"BARRIÈRES ÉNERGÉTIQUES ENTRE ÉTATS DISTINCTS")
            print(f"{'─'*70}")
        
        for ci in range(len(clusters)):
            for cj in range(ci + 1, len(clusters)):
                # Représentant de chaque cluster (plus basse énergie)
                rep_i = min(clusters[ci], key=lambda i: minima[i].energy_final)
                rep_j = min(clusters[cj], key=lambda i: minima[i].energy_final)
                
                barrier = compute_barrier(backbone, minima[rep_i], minima[rep_j])
                barriers.append(barrier)
                
                if verbose:
                    print(f"\n  {minima[rep_i].start_name} ↔ {minima[rep_j].start_name}")
                    print(f"    Énergies : {barrier['e_from']:.1f} ↔ {barrier['e_to']:.1f} kcal/mol")
                    print(f"    Barrière : {barrier['barrier_kcal_mol']:.1f} kcal/mol")
    
    # 5. Diagnostic
    n_distinct = len(clusters)
    is_multistable = n_distinct >= 2
    
    # Filtrer : un état n'est significatif que si son énergie n'est pas absurde
    # (ex: conformational states with > 1000 kcal/mol are steric clashes, not real minima)
    valid_clusters = []
    for cluster in clusters:
        best_e = min(minima[i].energy_final for i in cluster)
        if best_e < 500:  # seuil raisonnable
            valid_clusters.append(cluster)
    
    n_valid = len(valid_clusters)
    is_multistable = n_valid >= 2
    
    summary_lines = [
        f"",
        f"{'='*70}",
        f"RÉSULTAT",
        f"{'='*70}",
        f"  États distincts trouvés : {n_distinct} (dont {n_valid} énergétiquement plausibles)",
        f"  Multi-stable : {'✅ OUI' if is_multistable else '❌ NON'}",
        f"  Fold-switching possible : {'✅ OUI' if is_multistable else '❌ NON'}",
    ]
    
    if is_multistable:
        best_per_cluster = []
        for cluster in valid_clusters:
            best_i = min(cluster, key=lambda i: minima[i].energy_final)
            best_per_cluster.append(minima[best_i])
        best_per_cluster.sort(key=lambda m: m.energy_final)
        
        summary_lines.append(f"  États (ordre croissant d'énergie) :")
        for i, m in enumerate(best_per_cluster):
            summary_lines.append(f"    #{i+1} : E={m.energy_final:.1f} kcal/mol "
                               f"(départ: {m.start_name}, {m.n_steps} étapes)")
        
        if barriers:
            valid_barriers = [b for b in barriers if b['barrier_kcal_mol'] < 500]
            if valid_barriers:
                bar_min = min(b['barrier_kcal_mol'] for b in valid_barriers)
                bar_max = max(b['barrier_kcal_mol'] for b in valid_barriers)
                summary_lines.append(f"  Barrières : {bar_min:.1f} à {bar_max:.1f} kcal/mol")
    
    summary_text = "\n".join(summary_lines)
    if verbose:
        print(summary_text)
    
    return LandscapeResult(
        sequence=sequence,
        n_residues=n,
        minima=minima,
        distinct_minima=clusters,
        barriers=barriers,
        is_multistable=is_multistable,
        n_distinct_states=n_valid,
        summary_text=summary_text,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE HAUT NIVEAU
# ═══════════════════════════════════════════════════════════════════════════════

def scan_all(save_dir: str = "./energy_landscape_results") -> Dict[str, LandscapeResult]:
    """Analyse tous les peptides de démonstration."""
    os.makedirs(save_dir, exist_ok=True)
    results = {}
    
    for name, seq in DEMO_PEPTIDES.items():
        results[name] = analyze_landscape(seq, peptide_name=name, verbose=True)
    
    # Résumé global
    print(f"\n{'█'*70}")
    print(f"█  RÉSUMÉ GLOBAL")
    print(f"█  Peptides testés : {len(results)}")
    print(f"{'█'*70}")
    
    for name, res in results.items():
        status = "✅ MULTI-STABLE" if res.is_multistable else "❌ MONO-STABLE"
        print(f"  {name:15s} : {res.n_distinct_states} état(s) distinct(s), {status}")
    
    # Sauvegarde JSON
    for name, res in results.items():
        json_path = os.path.join(save_dir, f"landscape_{name}.json")
        json_data = {
            'sequence': res.sequence,
            'n_residues': res.n_residues,
            'is_multistable': res.is_multistable,
            'n_distinct_states': res.n_distinct_states,
            'minima': [
                {
                    'start_name': m.start_name,
                    'energy_initial': m.energy_initial,
                    'energy_final': m.energy_final,
                    'delta_energy': m.delta_energy,
                    'n_steps': m.n_steps,
                    'converged': m.converged,
                    'gradient_norm_final': m.gradient_norm_final,
                    'phi_final_mean': round(float(np.mean(m.phi_final)), 1),
                    'psi_final_mean': round(float(np.mean(m.psi_final)), 1),
                }
                for m in res.minima
            ],
            'barriers': res.barriers,
            'summary': res.summary_text,
        }
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='HARMOFOLD — Scan du Paysage Énergétique (Validation Option C)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--sequence', '-s', type=str, default=None,
                       help='Séquence unique à analyser')
    parser.add_argument('--all', '-a', action='store_true', default=True,
                       help='Analyser tous les peptides de démonstration (défaut)')
    parser.add_argument('--save-dir', '-o', type=str, default='./energy_landscape_results',
                       help='Répertoire de sortie')
    parser.add_argument('--lr', type=float, default=2.0,
                       help='Learning rate pour la relaxation (défaut: 2.0)')
    parser.add_argument('--max-steps', type=int, default=200,
                       help='Max steps de relaxation (défaut: 200)')
    parser.add_argument('--rmsd-threshold', type=float, default=2.5,
                       help='Seuil RMSD pour clustering (Å, défaut: 2.5)')
    
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  HARMOFOLD — Validation Option C (v2)                      ║")
    print("║  Scan du Paysage Énergétique par Relaxation Locale         ║")
    print("║  Détection de MULTI-STABILITÉ intrinsèque                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    if args.sequence:
        result = analyze_landscape(
            args.sequence, peptide_name="custom",
            learning_rate=args.lr, max_relax_steps=args.max_steps,
            rmsd_threshold=args.rmsd_threshold, verbose=True,
        )
    else:
        scan_all(save_dir=args.save_dir)


if __name__ == '__main__':
    main()
