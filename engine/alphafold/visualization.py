"""
ALPHAFOLD — Visualisation 3D des Structures Protéiques
========================================================
Modes de visualisation :
  - Ruban : backbone coloré par score φ (rouge=haut → bleu=bas)
  - Champ : densité |ψ|² sur grille 2D
  - Export : PDB, PNG, données pour PyMOL/ChimeraX

Author: Univers-Holistique
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional

from .amino_acids import PHI, HarmonicAminoAcid
from .backbone import ProteinStructure, ResidueAtoms


# ═══════════════════════════════════════════════════════════════════════════════
# PALETTE DE COULEURS HARMONIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def phi_color(phi_score: float) -> Tuple[float, float, float]:
    """
    Convertit un score φ en couleur RGB.

    Haut φ (0.65-0.72) → Rouge (feuillet β)
    Milieu φ (0.48-0.59) → Vert/Jaune (mixte)
    Bas φ (0.33-0.45) → Bleu (hélice α)
    """
    # Normaliser φ_score dans [0.33, 0.72] → [0, 1]
    t = (phi_score - 0.33) / (0.72 - 0.33)
    t = max(0.0, min(1.0, t))

    # Rouge à haute φ, Bleu à basse φ
    if t < 0.5:
        # Bleu → Cyan
        s = t * 2.0
        return (0.2 * s, 0.6 * s, 0.4 + 0.6 * s)
    else:
        # Jaune → Rouge
        s = (t - 0.5) * 2.0
        return (0.2 + 0.8 * s, 0.6 * (1.0 - s), 0.2 * (1.0 - s))


def residue_color(res: ResidueAtoms) -> str:
    """Retourne une couleur hexadécimale pour un résidu basée sur son φ_score."""
    r, g, b = phi_color(res.aa.phi_score)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


# ═══════════════════════════════════════════════════════════════════════════════
# MODE RUBAN
# ═══════════════════════════════════════════════════════════════════════════════

def ribbon_data(structure: ProteinStructure) -> Dict:
    """
    Génère les données pour un rendu en ruban du backbone.

    Returns:
        Dictionnaire avec :
        - 'ca_positions': positions Cα (N×3)
        - 'colors': couleurs hex pour chaque résidu
        - 'phi_scores': scores φ
        - 'secondary': prédiction de structure secondaire simplifiée
        - 'ribbon_guide': points de contrôle pour le spline du ruban
    """
    ca_pos = []
    colors = []
    phi_scores = []
    secondary = []

    for res in structure.residues:
        ca_pos.append(res.CA.tolist())
        colors.append(residue_color(res))
        phi_scores.append(res.aa.phi_score)

        # Prédiction simplifiée de SS
        if res.aa.helix_propensity > 0.6 and -100 < res.phi < -30 and -100 < res.psi < 0:
            secondary.append('H')  # Hélice
        elif res.aa.sheet_propensity > 0.6 and -180 < res.phi < -60 and 90 < res.psi < 180:
            secondary.append('E')  # Feuillet
        else:
            secondary.append('C')  # Coude/Boucle

    # Points de guidage du ruban (O passant par chaque peptide)
    ribbon_guide = []
    for res in structure.residues:
        # Point au niveau du plan peptidique (milieu entre C et O)
        guide = (res.C + res.O) / 2.0
        ribbon_guide.append(guide.tolist())

    return {
        'ca_positions': ca_pos,
        'colors': colors,
        'phi_scores': phi_scores,
        'secondary': ''.join(secondary),
        'ribbon_guide': ribbon_guide,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MODE CHAMP (DENSITÉ D'ONDE)
# ═══════════════════════════════════════════════════════════════════════════════

def wave_field_slice(structure: ProteinStructure,
                     plane: str = 'xy',
                     resolution: int = 200,
                     width: float = 30.0) -> np.ndarray:
    """
    Calcule la densité d'onde |ψ|² sur une coupe 2D.

    Chaque atome lourd contribue par une gaussienne centrée,
    pondérée par son score φ. Le résultat est une carte de densité
    électronique effective basée sur la résonance harmonique.

    Args:
        structure: ProteinStructure
        plane: plan de coupe ('xy', 'xz', 'yz')
        resolution: nombre de points par dimension
        width: largeur de la zone (Å)

    Returns:
        Matrice 2D numpy de densité
    """
    # Centre de masse
    all_pos = []
    for res in structure.residues:
        for pos in res.all_atoms().values():
            all_pos.append(pos)
    all_pos = np.array(all_pos)
    cm = all_pos.mean(axis=0)

    # Grille
    x = np.linspace(cm[0] - width/2, cm[0] + width/2, resolution)
    y = np.linspace(cm[1] - width/2, cm[1] + width/2, resolution)
    z_center = cm[2]

    if plane == 'xy':
        X, Y = np.meshgrid(x, y)
        Z = np.full_like(X, z_center)
    elif plane == 'xz':
        X, Z = np.meshgrid(x, np.linspace(cm[2] - width/2, cm[2] + width/2, resolution))
        Y = np.full_like(X, cm[1])
    else:  # 'yz'
        Y, Z = np.meshgrid(y, np.linspace(cm[2] - width/2, cm[2] + width/2, resolution))
        X = np.full_like(Y, cm[0])

    # Calculer la densité
    density = np.zeros((resolution, resolution))

    for res in structure.residues:
        phi = res.aa.phi_score
        for name, pos in res.all_atoms().items():
            # Rayon effectif basé sur l'élément
            if name[0] == 'C':
                sigma = 0.8
            elif name[0] == 'N':
                sigma = 0.7
            elif name[0] == 'O':
                sigma = 0.65
            elif name[0] == 'S':
                sigma = 1.0
            else:
                sigma = 0.8

            # Contribution gaussienne
            dx = X - pos[0]
            dy = Y - pos[1]
            dz = Z - pos[2]
            r2 = dx**2 + dy**2 + dz**2
            density += phi * np.exp(-r2 / (2.0 * sigma**2))

    return density


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT PYMOL
# ═══════════════════════════════════════════════════════════════════════════════

def pymol_script(structure: ProteinStructure) -> str:
    """
    Génère un script PyMOL pour visualiser la structure avec
    les couleurs harmoniques.

    Args:
        structure: ProteinStructure

    Returns:
        Script PyMOL sous forme de chaîne
    """
    lines = [
        "# ALPHAFOLD Harmonic Visualization Script for PyMOL",
        f"# Sequence: {structure.sequence}",
        f"# Residues: {structure.n_residues}",
        "",
        "delete all",
        "bg_color white",
        "",
    ]

    # Colorer par score φ
    lines.append("# Colors by phi score (red=high phi/beta, blue=low phi/helix)")
    for res in structure.residues:
        r, g, b = phi_color(res.aa.phi_score)
        res_id = res.index + 1
        lines.append(f"color rgb[{r:.3f},{g:.3f},{b:.3f}], resi {res_id}")

    lines.extend([
        "",
        "# Display settings",
        "show cartoon",
        "set cartoon_oval_length, 0.7",
        "set cartoon_oval_width, 0.3",
        "set ray_trace_mode, 1",
        "set ray_trace_gain, 0.2",
        "",
        "# Label key residues",
    ])

    # Label résidus avec φ extrêmes
    for res in structure.residues:
        if res.aa.phi_score > 0.65 or res.aa.phi_score < 0.40:
            lines.append(f"label resi {res.index+1} and name CA, '{res.aa.code3}'")

    lines.extend([
        "",
        "zoom complete",
        "ray 800,600",
    ])

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# RÉSUMÉ DE VISUALISATION
# ═══════════════════════════════════════════════════════════════════════════════

def structure_summary(structure: ProteinStructure) -> str:
    """Génère un résumé textuel de la structure pour affichage console."""
    lines = [
        f"╔══════════════════════════════════════════════════════════╗",
        f"║  ALPHAFOLD — Structure Proteique                         ║",
        f"╠══════════════════════════════════════════════════════════╣",
        f"║  Sequence: {structure.sequence:<44s} ║",
        f"║  Residus:  {structure.n_residues:<4d}                                         ║",
    ]

    # Résumé des angles
    phis = [r.phi for r in structure.residues if r.phi != 0.0]
    psis = [r.psi for r in structure.residues if r.psi != 0.0]
    phi_mean = np.mean(phis) if phis else 0
    psi_mean = np.mean(psis) if psis else 0

    lines.append(f"║  φ moyen:  {phi_mean:+6.1f}°                                     ║")
    lines.append(f"║  ψ moyen:  {psi_mean:+6.1f}°                                     ║")

    # Contenu en SS
    ss_count = {'H': 0, 'E': 0, 'C': 0}
    for res in structure.residues:
        if res.aa.helix_propensity > 0.6:
            ss_count['H'] += 1
        elif res.aa.sheet_propensity > 0.6:
            ss_count['E'] += 1
        else:
            ss_count['C'] += 1

    lines.append(f"║  Helix: {ss_count['H']:3d}  Sheet: {ss_count['E']:3d}  Loop: {ss_count['C']:3d}                   ║")
    lines.append(f"╚══════════════════════════════════════════════════════════╝")

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _test():
    """Test rapide."""
    from .backbone import HarmonicBackbone

    print("=" * 60)
    print("TEST : Visualisation")
    print("=" * 60)

    bb = HarmonicBackbone("AGVLIC")
    struct = bb.build_harmonic_initial()

    # Ruban
    rd = ribbon_data(struct)
    print(f"\nRuban: {len(rd['ca_positions'])} résidus")
    print(f"Structure secondaire: {rd['secondary']}")

    # Couleurs
    for res in struct.residues:
        print(f"  {res.aa.code3}: φ={res.aa.phi_score:.2f} → {residue_color(res)}")

    # Champ d'onde
    field = wave_field_slice(struct, 'xy', resolution=50, width=20.0)
    print(f"\nChamp d'onde: {field.shape}, max={field.max():.3f}")

    # Résumé
    print(f"\n{structure_summary(struct)}")

    # Script PyMOL (extrait)
    script = pymol_script(struct)
    print(f"\nScript PyMOL: {len(script)} caractères")
    print(script[:300] + "...")

    print("\n✅ Tests passés !")


if __name__ == '__main__':
    _test()
