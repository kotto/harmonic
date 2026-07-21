"""
ALPHAFOLD — Démonstrations avec Protéines Réelles
====================================================
Validation sur 4 protéines modèles :
  - Trp-cage (1L2Y) : 20 résidus, mini-protéine, repliement μs
  - Villin headpiece (1VII) : 36 résidus, 3 hélices α
  - BPTI (5PTI) : 58 résidus, 3 ponts disulfure
  - Ubiquitin (1UBQ) : 76 résidus, α+β

Pour chaque protéine :
  1. Charge la séquence FASTA
  2. Lance le repliement ABC
  3. Sauve le PDB
  4. Calcule les métriques (si PDB de référence disponible)

Author: Univers-Holistique
"""

import math
import sys
import os
import time
import numpy as np
from typing import Dict, Optional

from .amino_acids import parse_sequence, get_harmonic_profile
from .backbone import HarmonicBackbone, ProteinStructure, compute_rama_score
from .harmonic_energy import HarmonicEnergy, EnergyBreakdown, compute_energy
from .abc_folder import ABCProteinFolder, FoldResult
from .structure_io import write_pdb, parse_pdb, compare_structures
from .visualization import structure_summary, ribbon_data, pymol_script

# ═══════════════════════════════════════════════════════════════════════════════
# SÉQUENCES DES PROTÉINES DE RÉFÉRENCE
# ═══════════════════════════════════════════════════════════════════════════════

DEMO_PROTEINS = {
    'trp_cage': {
        'name': 'Trp-cage (1L2Y)',
        'sequence': 'NLYIQWLKDGGPSSGRPPPS',  # 20 résidus
        'pdb_id': '1L2Y',
        'description': 'Mini-protéine 20 aa, repliement en ~4 μs. '
                       'Structure : hélice α N-ter + coude + hélice 3-10.',
        'expected_class': 'alpha',
    },
    'villin': {
        'name': 'Villin Headpiece (1VII)',
        'sequence': 'MLSDEDFKAVFGMTRSAFANLPLWKQQNLKKEKGLF',  # 36 résidus
        'pdb_id': '1VII',
        'description': 'Domaine de tête de villine, 36 aa. '
                       '3 hélices α formant un faisceau compact.',
        'expected_class': 'all-alpha',
    },
    'bpti': {
        'name': 'BPTI (5PTI)',
        'sequence': 'RPDFCLEPPYTGPCKARIIRYFYNAKAGLCQTFVYGGCRAKRNNFKSAEDCMRTCGGA',  # 58 résidus
        'pdb_id': '5PTI',
        'description': 'Inhibiteur de trypsine pancréatique bovine. '
                       '58 aa, 3 ponts disulfure, architecture α+β.',
        'expected_class': 'alpha/beta',
        'disulfide_pairs': [(4, 50), (12, 36), (28, 49)],  # indices 0-based
    },
    'ubiquitin': {
        'name': 'Ubiquitin (1UBQ)',
        'sequence': 'MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG',  # 76 résidus
        'pdb_id': '1UBQ',
        'description': 'Ubiquitine humaine, 76 aa. '
                       'Architecture α+β classique : feuillet β mixte + hélice α.',
        'expected_class': 'alpha/beta',
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def demo_protein(protein_key: str,
                 n_steps: int = 2000,
                 temperature: float = 300.0,
                 cooling_rate: float = 0.999,
                 output_dir: str = '.',
                 verbose: bool = True) -> Dict:
    """
    Exécute le repliement d'une protéine de démonstration.

    Args:
        protein_key: clé dans DEMO_PROTEINS ('trp_cage', 'villin', 'bpti', 'ubiquitin')
        n_steps: nombre de pas de simulation
        temperature: température initiale (K)
        cooling_rate: taux de refroidissement
        output_dir: répertoire de sortie pour les fichiers
        verbose: afficher la progression

    Returns:
        Dictionnaire avec les résultats
    """
    if protein_key not in DEMO_PROTEINS:
        raise ValueError(f"Protéine inconnue : {protein_key}. "
                        f"Choisir parmi {list(DEMO_PROTEINS.keys())}")

    info = DEMO_PROTEINS[protein_key]
    sequence = info['sequence']
    name = info['name']

    if verbose:
        print(f"\n{'='*60}")
        print(f"ALPHAFOLD — Démo : {name}")
        print(f"{'='*60}")
        print(f"Séquence : {sequence[:40]}{'...' if len(sequence) > 40 else ''}")
        print(f"Longueur : {len(sequence)} résidus")
        print(f"Description : {info['description']}")
        print(f"Classe attendue : {info['expected_class']}")

    # Profil harmonique
    profile = get_harmonic_profile(sequence)
    if verbose:
        print(f"\nProfil harmonique :")
        print(f"  φ moyen = {profile['phi_mean']:.4f}")
        print(f"  Charge nette = {profile['charge_net']}")
        print(f"  Hydrophobie moyenne = {profile['hydrophobic_mean']:.2f}")
        print(f"  Classe prédite = {profile['predicted_class']}")
        print(f"  Énergie harmonique = {profile['harmonic_energy_kcal_mol']:.2f} kcal/mol")

    # Repliement
    if verbose:
        print(f"\nRepliement ABC ({n_steps} pas, T₀={temperature}K)...")

    folder = ABCProteinFolder(sequence)

    try:
        result = folder.fold(
            n_steps=n_steps,
            temperature=temperature,
            cooling_rate=cooling_rate,
            learning_rate=1.0,
            abc_memory=64,
            record_every=max(1, n_steps // 20),
            verbose=verbose,
        )
    except KeyboardInterrupt:
        print("\n⚠ Interrompu par l'utilisateur")
        return {'status': 'interrupted', 'protein': name}

    if verbose:
        print(f"\nRésultat :")
        print(f"  Temps : {result.elapsed_time:.1f}s")
        print(f"  Étapes : {result.n_steps}")
        print(f"  Convergé : {result.converged}")
        print(f"  Énergie finale : {result.energy.total:.2f} kcal/mol")
        print(f"  Décomposition :")
        for k, v in result.energy.to_dict().items():
            if k != 'total':
                print(f"    {k}: {v:+.2f}")

    # Score Ramachandran
    rama = compute_rama_score(result.structure)
    if verbose:
        print(f"\nQualité Ramachandran :")
        print(f"  Score moyen : {rama['mean_score']:.3f}")
        print(f"  Outliers : {rama['n_outliers']}/{rama['n_evaluated']}")

    # Sauvegarder le PDB
    os.makedirs(output_dir, exist_ok=True)
    pdb_path = os.path.join(output_dir, f"alphafold_{protein_key}.pdb")
    write_pdb(result.structure, pdb_path,
              title=f"ALPHAFOLD {name} — Harmonic Deterministic")
    if verbose:
        print(f"\nPDB sauvegardé : {pdb_path}")

    # Script PyMOL
    pml_path = os.path.join(output_dir, f"alphafold_{protein_key}.pml")
    with open(pml_path, 'w') as f:
        f.write(pymol_script(result.structure))
    if verbose:
        print(f"Script PyMOL : {pml_path}")

    # Résumé structure
    if verbose:
        print(f"\n{structure_summary(result.structure)}")

    return {
        'status': 'completed',
        'protein': name,
        'sequence': sequence,
        'n_residues': len(sequence),
        'harmonic_profile': profile,
        'fold_result': result,
        'rama_score': rama,
        'pdb_path': pdb_path,
        'pml_path': pml_path,
        'energy_breakdown': result.energy.to_dict(),
    }


def demo_compare_with_pdb(protein_key: str, pdb_filepath: str,
                           n_steps: int = 2000,
                           output_dir: str = '.',
                           verbose: bool = True) -> Dict:
    """
    Compare la structure prédite avec une structure PDB expérimentale.

    Args:
        protein_key: clé dans DEMO_PROTEINS
        pdb_filepath: chemin vers le fichier PDB de référence
        n_steps: nombre de pas
        output_dir: répertoire de sortie
        verbose: affichage

    Returns:
        Dictionnaire avec métriques de comparaison
    """
    # Exécuter le repliement
    result = demo_protein(protein_key, n_steps=n_steps,
                         output_dir=output_dir, verbose=verbose)

    if result['status'] != 'completed':
        return result

    # Charger la structure de référence
    try:
        ref_structure = parse_pdb(pdb_filepath)
    except Exception as e:
        if verbose:
            print(f"\n⚠ Impossible de charger le PDB de référence : {e}")
        result['comparison'] = {'error': str(e)}
        return result

    # Comparer
    comparison = compare_structures(result['fold_result'].structure, ref_structure)

    if verbose:
        print(f"\n{'='*60}")
        print(f"Comparaison avec PDB de référence ({pdb_filepath})")
        print(f"  RMSD : {comparison['rmsd_angstrom']:.3f} Å")
        print(f"  TM-score : {comparison['tm_score']:.4f}")
        print(f"  GDT-TS : {comparison['gdt_ts']:.4f}")
        print(f"  Résidus comparés : {comparison['n_residues_compared']}")

    result['comparison'] = comparison
    result['reference_pdb'] = pdb_filepath

    return result


def run_all_demos(n_steps_per_protein: Optional[Dict[str, int]] = None,
                   output_dir: str = './alphafold_demo_output',
                   verbose: bool = True) -> Dict[str, Dict]:
    """
    Exécute toutes les démonstrations.

    Args:
        n_steps_per_protein: dict {protein_key: n_steps}, défaut auto-scalé
        output_dir: répertoire de sortie
        verbose: affichage

    Returns:
        Dictionnaire {protein_key: result}
    """
    # Nombre de pas par défaut (adapté à la taille)
    if n_steps_per_protein is None:
        n_steps_per_protein = {
            'trp_cage': 1500,
            'villin': 2000,
            'bpti': 2500,
            'ubiquitin': 3000,
        }

    results = {}
    total_start = time.time()

    for key in ['trp_cage', 'villin', 'bpti', 'ubiquitin']:
        n_steps = n_steps_per_protein.get(key, 2000)
        results[key] = demo_protein(
            key, n_steps=n_steps, output_dir=output_dir, verbose=verbose
        )

    total_time = time.time() - total_start

    # Résumé global
    if verbose:
        print(f"\n{'='*60}")
        print(f"RÉSUMÉ GLOBAL — {len(results)} protéines")
        print(f"Temps total : {total_time:.0f}s ({total_time/60:.1f} min)")
        print(f"{'='*60}")
        for key, res in results.items():
            if res['status'] == 'completed':
                info = DEMO_PROTEINS[key]
                e = res['fold_result'].energy
                rama = res['rama_score']
                print(f"\n{info['name']} ({info['expected_class']}):")
                print(f"  Énergie : {e.total:.1f} kcal/mol")
                print(f"  Rama : {rama['mean_score']:.3f} ({rama['n_outliers']} outliers)")
                print(f"  Temps : {res['fold_result'].elapsed_time:.0f}s")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Point d'entrée principal pour les démonstrations."""
    import argparse

    parser = argparse.ArgumentParser(
        description='ALPHAFOLD — Démonstrations de Repliement Harmonique')
    parser.add_argument('protein', nargs='?', default=None,
                       help='Protéine à replier (trp_cage, villin, bpti, ubiquitin, ou "all")')
    parser.add_argument('--steps', type=int, default=2000,
                       help='Nombre de pas de simulation')
    parser.add_argument('--temperature', type=float, default=300.0,
                       help='Température initiale (K)')
    parser.add_argument('--cooling', type=float, default=0.999,
                       help='Taux de refroidissement')
    parser.add_argument('--output', '-o', default='./alphafold_demo_output',
                       help='Répertoire de sortie')
    parser.add_argument('--compare', type=str, default=None,
                       help='Fichier PDB de référence pour comparaison')
    parser.add_argument('--quiet', action='store_true',
                       help='Mode silencieux')

    args = parser.parse_args()
    verbose = not args.quiet

    print("╔══════════════════════════════════════════════════════╗")
    print("║        ALPHAFOLD — Harmonic Deterministic           ║")
    print("║        Protein Folding Demonstrations               ║")
    print("╚══════════════════════════════════════════════════════╝")

    if args.protein is None or args.protein == 'all':
        run_all_demos(
            n_steps_per_protein=None,
            output_dir=args.output,
            verbose=verbose,
        )
    else:
        if args.compare:
            demo_compare_with_pdb(
                args.protein,
                args.compare,
                n_steps=args.steps,
                output_dir=args.output,
                verbose=verbose,
            )
        else:
            demo_protein(
                args.protein,
                n_steps=args.steps,
                temperature=args.temperature,
                cooling_rate=args.cooling,
                output_dir=args.output,
                verbose=verbose,
            )


if __name__ == '__main__':
    main()
