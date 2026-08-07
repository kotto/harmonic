#!/usr/bin/env python3
"""
purify_holograms.py — Séparation sectorielle des hologrammes (Wave-Native)
=========================================================================

Équivalence harmonique : MoE → Gate par Cohérence (LLM #32)
- Chaque hologramme pur = sous-espace quasi-orthogonal
- Routage : max Re(⟨ψ_Q | ψ_domaine⟩) précis
- H pur → résonance forte sur son domaine, faible hors domaine

Usage:
    python purify_holograms.py --source official_medecine --output-dir data/hologram_store
    python purify_holograms.py --source official_medecine --dry-run
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Optional, Any

import numpy as np

# Setup
_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

from hologram_store import HologramStore, HologramMeta, OFFICIAL_DOMAINS, STORE_DIR, HOLOGRAM_FORMAT_VERSION
from holographic_encoder import (
    HolographicEncoder, _circular_convolve, _fnv1a_hash, PHI, TAU,
    hologram_to_transport, hologram_from_transport
)

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DES SECTEURS PURS POUR MÉDECINE
# ═══════════════════════════════════════════════════════════════════════════════

# Secteurs réellement médicaux : whitelist stricte. Les faits techniques/maths
# (transformation de Fourier, cpu) ou végétaux (fleur) portent des secteurs
# hors médecine (MATHS_APPLI, TECHNOLOGIE, NATURE_VEGET...) — leur texte peut
# contenir des mots-clés trompeurs (« traitement du signal », « traitement
# d'un ordinateur ») qui les faisaient fuir dans pharmacologie.
MEDICAL_SECTOR_WHITELIST = {'BIOLOGIE', 'CORPS_ORGANES', 'CORPS_SANTE', 'SANTE'}

PURE_MEDICAL_SECTORS = {
    'med_anatomie': {
        'name': 'Anatomie & Organes',
        'icon': '🫀',
        'sectors': ['CORPS_ORGANES', 'CORPS_SANTE'],
        'keywords': ['coeur', 'cerveau', 'poumon', 'foie', 'rein', 'estomac', 'intestin',
                     'artere', 'veine', 'capillaire', 'aorte', 'bronche', 'alveole',
                     'os', 'muscle', 'peau', 'squelette', 'colonne', 'crane', 'rate',
                     'thymus', 'thyroide', 'hypophyse', 'surrenale', 'larynx', 'pharynx',
                     'oesophage', 'vessicule', 'pancréas', 'diaphragme', 'trachee',
                     'valvule', 'alveole', 'bronche', 'diaphragme'],
        # NB: « sang » et « globule » sont retirés des mots-clés : ils fuient
        # la biologie cellulaire (globule blanc, insuline...) dans l'anatomie.
        # Les faits sanguins (CORPS_ORGANES) entrent via le secteur.
        'exclude_keywords': ['ribosome', 'chloroplaste', 'lysosome', 'cytosquelette',
                             'centrosome', 'chromosome', 'homeostasie', 'lymphocyte',
                             'insuline', 'apoptose', 'necrose', 'adn', 'gene',
                             'mitochondrie', 'vacuole', 'paroi', 'flagelle',
                             'transformation de fourier', 'ordinateur'],
        'description': 'Anatomie des organes, systèmes corporels, structures',
        'benchmark_questions': [
            "Anatomie du coeur humain",
            "Fonction du foie",
            "Structure du poumon",
            "Role des reins",
            "Anatomie du cerveau",
        ],
    },
    'med_biologie_cell': {
        'name': 'Biologie Cellulaire & Moléculaire',
        'icon': '🔬',
        'sectors': ['BIOLOGIE'],
        'keywords': ['cellule', 'mitochondrie', 'noyau', 'adn', 'arn', 'proteine', 'gene',
                     'chromosome', 'genome', 'ribosome', 'lysosome', 'golgi',
                     'reticulum', 'membrane', 'cil', 'flagelle', 'centrosome', 'peroxysome',
                     'vacuole', 'paroi', 'jonction', 'clonage', 'fermentation', 'metabolisme',
                     'anaerobie', 'homeostasie', 'apoptose', 'necrose', 'virologie',
                     'photosynthese', 'chloroplaste', 'globule', 'lymphocyte', 'anticorps',
                     'immunite', 'allergie', 'inflammation', 'stem', 'embryon', 'regeneration',
                     'cancer', 'vieillissement', 'longevite', 'neurotransmetteur', 'acetylcholine',
                     'endorphine', 'insuline', 'recepteur', 'epidemie', 'symbiose', 'cicatrisation',
                     'plaquette', 'hormone', 'adn', 'selection', 'evolution'],
        'exclude_keywords': ['coeur', 'cerveau', 'poumon', 'foie', 'rein', 'estomac', 'intestin',
                             'artere', 'veine', 'sang', 'os', 'muscle', 'peau', 'squelette',
                             'rate', 'thymus', 'thyroide', 'larynx', 'pharynx', 'oesophage',
                             'vessicule', 'pancréas', 'diaphragme', 'trachee', 'bronche', 'valvule'],
        'description': 'Biologie cellulaire, génétique, molécules, processus fondamentaux',
        'benchmark_questions': [
            "Structure de l'ADN",
            "Fonction des mitochondries",
            "Cycle cellulaire",
            "Synthese des proteines",
            "Reponse immunitaire",
        ],
    },
    'med_pathologie': {
        'name': 'Pathologie & Maladies',
        'icon': '🦠',
        'sectors': ['SANTE', 'CORPS_SANTE'],
        'keywords': ['maladie', 'symptome', 'diagnostic', 'cancer', 'diabete', 'hypertension',
                     'infarctus', 'infection', 'virus', 'bacterie', 'paludisme', 'grippe',
                     'tuberculose', 'hepatite', 'sida', 'epidemie', 'pandemie', 'pathologie',
                     'tumeur', 'metastase', 'inflammation', 'autoimmune', 'degenerative',
                     'cardiovasculaire', 'respiratoire', 'neurologique', 'digestif', 'renal',
                     'endocrinien', 'hematologique', 'dermatologique', 'psychiatrique'],
        'description': 'Maladies, symptomes, diagnostics, epidemiologie',
        'benchmark_questions': [
            "Symptomes du diabete",
            "Diagnostic de l'hypertension",
            "Traitement du paludisme",
            "Cancer du poumon",
            "Maladies cardiovasculaires",
        ],
    },
    'med_pharmacologie': {
        'name': 'Pharmacologie & Traitements',
        'icon': '💊',
        'sectors': ['SANTE', 'CORPS_SANTE'],
        'keywords': ['medicament', 'traitement', 'vaccin', 'therapie', 'chirurgie', 'operation',
                     'antibiotique', 'antiviral', 'analgesique', 'anesthesique', 'vaccination',
                     'immunisation', 'posologie', 'effet secondaire', 'interaction', 'contre-indication',
                     'paracetamol', 'ibuprofene', 'amoxicilline', 'insuline', 'corticoide',
                     'antidepresseur', 'anticoagulant', 'beta-bloquant', 'diuretic', 'statine',
                     'chimiotherapie', 'radiotherapie', 'immunotherapie', 'gene therapy',
                     'greffe', 'transplantation', 'dialyse', 'prosthese', 'pacemaker'],
        'description': 'Medicaments, vaccins, protocoles therapeutiques, chirurgie',
        'benchmark_questions': [
            "Traitement de l'hypertension",
            "Vaccin contre la grippe",
            "Antibiotiques resistance",
            "Chimiotherapie effets",
            "Interaction medicamenteuse",
        ],
    },
    'med_histoire_sante': {
        'name': 'Histoire de la Médecine & Santé Publique',
        'icon': '📜',
        'sectors': ['HISTOIRE', 'PASSE', 'POLITIQUE'],
        'extra_sectors': ['PASSE', 'POLITIQUE', 'HISTOIRE'],  # seuls admis hors whitelist médicale
        'keywords': ['pasteur', 'history', 'histoire', 'decouverte', 'inventeur', 'nobel',
                     'sante publique', 'epidemiologie', 'vaccination obligatoire', 'hygiene',
                     'hopital', 'medecin', 'infirmier', 'pharmacien', 'oms', 'organisation mondiale',
                     'politique sante', 'couverture maladie', 'assurance', 'prevention', 'depistage',
                     'campagne', 'eradiquer', 'variole', 'polio', 'rougeole', 'coqueluche'],
        'description': 'Histoire medicale, decouvertes, sante publique, politiques',
        'benchmark_questions': [
            "Decouverte de Pasteur",
            "Histoire de la vaccination",
            "Eradication variole",
            "Sante publique France",
            "Prix Nobel medecine",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# CALCUL DE COHÉRENCE / PURITÉ (Auto-évaluation harmonique)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_hologram_purity(hologram_memory: np.ndarray,
                            psi_subjects: np.ndarray,
                            psi_relations: np.ndarray,
                            psi_objects: np.ndarray) -> Dict[str, float]:
    """
    Calcule la pureté harmonique d'un hologramme.
    
    Équivalence: Benchmark → Cohérence Interne (LLM #28)
    - Au lieu de F1 externe, mesurer auto-corréation H vs ψ_faits
    - Purity = mean_coherence / (std_coherence + eps)  (signal/bruit)
    
    Returns:
        dict avec mean_coherence, min_coherence, std_coherence, purity
    """
    n_facts = len(psi_subjects)
    coherence_scores = []
    
    for i in range(n_facts):
        # Reconstituer ψ_fait = ψ_s ⊛ ψ_r ⊛ ψ_o
        psi_fact = _circular_convolve(
            _circular_convolve(psi_subjects[i], psi_relations[i]),
            psi_objects[i]
        )
        # Cohérence = Re(⟨H | ψ_fait⟩) normalisée
        coh = np.real(np.dot(hologram_memory, np.conj(psi_fact)))
        coherence_scores.append(coh)
    
    coherence_scores = np.array(coherence_scores)
    
    mean_coh = float(np.mean(coherence_scores))
    min_coh = float(np.min(coherence_scores))
    std_coh = float(np.std(coherence_scores))
    purity = mean_coh / (std_coh + 1e-8)
    
    return {
        'mean_coherence': mean_coh,
        'min_coherence': min_coh,
        'std_coherence': std_coh,
        'purity': float(purity),
        'n_facts': n_facts,
    }


def compute_cross_purity(hologram_memory: np.ndarray,
                         other_hologram_memories: Dict[str, np.ndarray]) -> Dict[str, float]:
    """
    Mesure l'orthogonalité inter-domaines (cross-talk).
    Idéal: Re(⟨H_i | H_j⟩) ≈ 0 pour i ≠ j
    """
    cross_scores = {}
    for name, other_H in other_hologram_memories.items():
        if name == 'self':
            continue
        score = float(np.real(np.dot(hologram_memory, np.conj(other_H))))
        cross_scores[name] = score
    return cross_scores


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE DE PURIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def load_source_hologram(holo_id: str, store: HologramStore) -> Tuple[List[Tuple], Dict]:
    """Charge un hologramme source (faits + ψ)."""
    facts, psi_data = store.download(holo_id)
    if not facts:
        raise ValueError(f"Hologramme {holo_id} introuvable ou vide")
    return facts, psi_data


def filter_facts_for_sector(facts: List[Tuple],
                            sector_config: Dict) -> List[Tuple]:
    """Filtre les faits selon secteurs + mots-clés du secteur pur."""
    sectors = set(s.upper() for s in sector_config['sectors'])
    keywords = [kw.lower() for kw in sector_config['keywords']]
    exclude_keywords = [kw.lower() for kw in sector_config.get('exclude_keywords', [])]
    extra_sectors = set(s.upper() for s in sector_config.get('extra_sectors', []))
    
    filtered = []
    for s, r, o, sec in facts:
        sec_upper = str(sec).upper()
        text = f"{s} {r} {o}".lower()
        
        sector_match = any(s_target in sec_upper for s_target in sectors)
        # Mots-clés courts (≤3 lettres, ex. « os ») en frontière de mot —
        # sinon « os » matche symbiose / photosynthese. Longs : préfixe de
        # mot (globule → globules, bronche → bronches).
        keyword_match = any(_keyword_in_text(kw, text) for kw in keywords)
        exclude_match = any(_keyword_in_text(kw, text) for kw in exclude_keywords)
        
        # 🚫 Whitelist sectorielle stricte : un fait hors médecine (secteur
        # MATHS_APPLI, TECHNOLOGIE, NATURE_VEGET...) ne peut pas entrer,
        # même si son texte contient un mot-clé trompeur (« traitement »).
        sector_allowed = (sec_upper in MEDICAL_SECTOR_WHITELIST
                          or sec_upper in extra_sectors)
        
        if (sector_match or keyword_match) and sector_allowed and not exclude_match:
            filtered.append((s, r, o, sec))
    
    return filtered


def _keyword_in_text(kw: str, text: str) -> bool:
    """Mot-clé en frontière de mot (préfixe pour les mots longs ≥4 lettres)."""
    import re as _re
    if len(kw) < 4:
        return _re.search(rf'\b{_re.escape(kw)}\b', text) is not None
    return _re.search(rf'\b{_re.escape(kw)}\w*', text) is not None


def deduplicate_facts(facts: List[Tuple]) -> List[Tuple]:
    """Dédoublonnage canonique (sujet, relation, objet tronqués)."""
    seen = set()
    canonical = []
    for s, r, o, sec in facts:
        key = (s.lower()[:60], r.lower()[:60], o.lower()[:80])
        if key not in seen:
            seen.add(key)
            canonical.append((s, r, o, sec))
    return canonical


def build_pure_hologram(holo_id: str,
                        sector_config: Dict,
                        facts: List[Tuple],
                        encoder: HolographicEncoder) -> Tuple[Dict, Dict]:
    """
    Construit un hologramme pur wave-native.
    
    Returns:
        (metadata, psi_data) prêts pour sauvegarde NPZ
    """
    # 1. Filtrage sectoriel
    filtered = filter_facts_for_sector(facts, sector_config)
    log.info(f"  {holo_id}: {len(filtered)} faits après filtrage sectoriel")
    
    # 2. Dédoublonnage
    canonical = deduplicate_facts(filtered)
    log.info(f"  {holo_id}: {len(canonical)} faits après dédoublonnage")
    
    if not canonical:
        raise ValueError(f"Aucun fait pour {holo_id}")
    
    # 3. Encodage ψ via HolographicEncoder
    # Pré-encoder les mots uniques
    word_set = set()
    for s, r, o, _ in canonical:
        for w in s.split() + r.split() + o.split():
            w = w.strip('.,!?;:')
            if len(w) >= 2:
                word_set.add(w)
    
    for w in word_set:
        encoder.encode_word(w)
    
    # 4. Binding HRR : ψ_fait = ψ_s ⊛ ψ_r ⊛ ψ_o
    psi_facts = []
    psi_subjects = []
    psi_relations = []
    psi_objects = []
    amplitudes = []
    
    for s, r, o, sec in canonical:
        psi_s = encoder.encode_word(s)
        psi_r = encoder.encode_word(r)
        psi_o = encoder.encode_word(o)
        
        psi_fact = _circular_convolve(_circular_convolve(psi_s, psi_r), psi_o)
        
        psi_facts.append(psi_fact)
        psi_subjects.append(psi_s)
        psi_relations.append(psi_r)
        psi_objects.append(psi_o)
        amplitudes.append(1.0)
    
    # 5. Mémoire holographique H = Σ ψ_fait (normalisée)
    hologram_memory = np.sum(psi_facts, axis=0)
    hologram_memory = hologram_memory / np.sqrt(len(psi_facts))
    
    # 6. Top concepts
    subj_count = Counter(str(f[0]).lower() for f in canonical)
    top_concepts = [s for s, _ in subj_count.most_common(10)]
    
    # 7. Calcul pureté (auto-évaluation)
    purity_metrics = compute_hologram_purity(
        hologram_memory,
        np.array(psi_subjects),
        np.array(psi_relations),
        np.array(psi_objects)
    )
    
    # 8. Métadonnées
    metadata = {
        'id': holo_id,
        'name': sector_config['name'],
        'domain': holo_id.replace('med_', 'medecine_'),
        'icon': sector_config['icon'],
        'description': sector_config['description'],
        'sectors': sector_config['sectors'],
        'keywords': sector_config['keywords'],
        'facts_count': len(canonical),
        'quality_score': 0.5,  # sera mis à jour après benchmark
        'author': 'KA-Purifier',
        'type': 'official_pure',
        'benchmark_questions': sector_config.get('benchmark_questions', []),
        'purity_metrics': purity_metrics,
    }
    
    psi_data = {
        'hologram_memory': hologram_memory,
        'psi_subjects': np.array(psi_subjects),
        'psi_relations': np.array(psi_relations),
        'psi_objects': np.array(psi_objects),
        'amplitudes': np.array(amplitudes, dtype=np.float32),
        'version': HOLOGRAM_FORMAT_VERSION,
        'kb_hash': 'pure_build',
    }
    
    return metadata, psi_data


def save_hologram_npz(holo_id: str, canonical_facts: List[Tuple],
                      psi_data: Dict, metadata: Dict, output_dir: Path):
    """Sauvegarde hologramme en format NPZ wave-native."""
    holo_path = output_dir / f'{holo_id}.npz'
    
    subjects = np.array([f[0] for f in canonical_facts], dtype=object)
    relations = np.array([f[1] for f in canonical_facts], dtype=object)
    objects = np.array([f[2] for f in canonical_facts], dtype=object)
    sectors = np.array([f[3] for f in canonical_facts], dtype=object)
    
    np.savez_compressed(
        str(holo_path),
        subjects=subjects,
        relations=relations,
        objects=objects,
        sectors=sectors,
        hologram_memory=psi_data['hologram_memory'],
        psi_subjects=psi_data['psi_subjects'],
        psi_relations=psi_data['psi_relations'],
        psi_objects=psi_data['psi_objects'],
        amplitudes=psi_data['amplitudes'],
        version=psi_data['version'],
        kb_hash=psi_data['kb_hash'],
        domain=metadata.get('domain', ''),
        created_at=metadata.get('created_at', 0),
    )
    
    log.info(f"  💾 Sauvé: {holo_path} ({len(canonical_facts)} faits)")
    return holo_path


def update_registry(store: HologramStore, holo_id: str, metadata: Dict):
    """Met à jour le registre JSON du store."""
    import time
    from hologram_store import HologramMeta
    
    meta = HologramMeta(
        id=holo_id,
        name=metadata['name'],
        domain=metadata['domain'],
        icon=metadata['icon'],
        description=metadata['description'],
        sectors=metadata['sectors'],
        top_concepts=metadata.get('keywords', []),
        facts_count=metadata['facts_count'],
        quality_score=metadata.get('quality_score', 0.5),
        author=metadata['author'],
        type=metadata['type'],
        created_at=time.time(),
        benchmark_questions=len(metadata.get('benchmark_questions', [])),
        version=metadata.get('version', HOLOGRAM_FORMAT_VERSION),
        kb_hash=metadata.get('kb_hash', ''),
    )
    
    store._registry[holo_id] = meta
    store._save_registry()
    log.info(f"  📝 Registre mis à jour: {holo_id}")


def run_cross_purity_check(output_dir: Path, holo_ids: List[str]):
    """Vérifie l'orthogonalité entre hologrammes purs."""
    log.info("\n🔍 Vérification cross-purity (orthogonalité inter-domaines)...")
    
    memories = {}
    for holo_id in holo_ids:
        holo_path = output_dir / f'{holo_id}.npz'
        if holo_path.exists():
            data = np.load(str(holo_path))
            memories[holo_id] = data['hologram_memory']
    
    print("\n" + "="*70)
    print("MATRICE CROSS-PURITY (Re(⟨H_i | H_j⟩) - diagonal = auto)")
    print("="*70)
    
    holo_list = list(memories.keys())
    # Header
    print(f"{'':>18}", end="")
    for h in holo_list:
        print(f"{h[4:18]:>12}", end="")
    print()
    
    for h1 in holo_list:
        print(f"{h1[4:18]:>18}", end="")
        for h2 in holo_list:
            score = float(np.real(np.dot(memories[h1], np.conj(memories[h2]))))
            print(f"{score:>12.4f}", end="")
        print()
    
    print("\n🎯 Idéal: diagonale ~1.0, hors-diagonale ≈ 0.0")


def main():
    parser = argparse.ArgumentParser(
        description='Purify holograms into sectoral pure subspaces (Wave-Native)'
    )
    parser.add_argument('--source', default='official_medecine',
                        help='Source hologram ID to purify')
    parser.add_argument('--output-dir', default=str(STORE_DIR),
                        help='Output directory for pure holograms')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without saving')
    parser.add_argument('--config', default=None,
                        help='JSON config for pure sectors (default: medical)')
    parser.add_argument('--verify', action='store_true',
                        help='Run cross-purity check after build')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load sector config
    if args.config:
        with open(args.config) as f:
            pure_sectors = json.load(f)
    else:
        pure_sectors = PURE_MEDICAL_SECTORS
    
    # Initialize
    store = HologramStore()
    encoder = HolographicEncoder()
    
    # Load source
    log.info(f"🔄 Chargement hologramme source: {args.source}")
    facts, psi_data = load_source_hologram(args.source, store)
    log.info(f"   {len(facts)} faits source, ψ keys: {list(psi_data.keys())}")
    
    # Build each pure hologram
    built_holo_ids = []
    
    for holo_id, sector_config in pure_sectors.items():
        log.info(f"\n🏗️  Construction: {holo_id} ({sector_config['name']})")
        
        try:
            metadata, new_psi_data = build_pure_hologram(
                holo_id, sector_config, facts, encoder
            )
            
            # Re-filter to get canonical facts for saving
            filtered = filter_facts_for_sector(facts, sector_config)
            canonical = deduplicate_facts(filtered)
            
            # Pureté
            purity = metadata['purity_metrics']
            log.info(f"   Pureté: {purity['purity']:.2f} "
                     f"(mean_coh={purity['mean_coherence']:.4f}, "
                     f"std={purity['std_coherence']:.4f})")
            
            if args.dry_run:
                log.info(f"   [DRY-RUN] Serait sauvé: {len(canonical)} faits")
                continue
            
            # Save NPZ
            save_hologram_npz(holo_id, canonical, new_psi_data, metadata, output_dir)
            
            # Update registry
            update_registry(store, holo_id, metadata)
            
            built_holo_ids.append(holo_id)
            
        except Exception as e:
            log.error(f"   ❌ Erreur {holo_id}: {e}")
    
    # Cross-purity check
    if args.verify and not args.dry_run:
        run_cross_purity_check(output_dir, built_holo_ids)
    
    # Summary
    print("\n" + "="*70)
    print("RÉSUMÉ PURIFICATION")
    print("="*70)
    print(f"Source: {args.source} ({len(facts)} faits)")
    print(f"Cibles: {len(pure_sectors)} hologrammes purs")
    print(f"Construits: {len(built_holo_ids)}")
    for h in built_holo_ids:
        print(f"  ✅ {h}")
    if args.dry_run:
        print("\n[DRY-RUN] Aucune sauvegarde effectuée")
    print("="*70)


if __name__ == '__main__':
    main()