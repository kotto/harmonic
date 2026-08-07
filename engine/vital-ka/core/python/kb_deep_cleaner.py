"""
KB Deep Cleaner — Nettoyage profond des artefacts de concaténation
====================================================================
Détecte et répare les faits corrompus par l'expansion transitive :
  - " puis " → sépare en deux faits distincts
  - " → "   → sépare en deux faits distincts
  - " >> "  → supprime la partie corrompue
  - Préfixes numériques : "10. tokyo" → "tokyo"
  - Parenthèses d'années : "(1503-1519)" → supprimé
  - Relations/objets trop longs ou vides → filtrés

Usage:
  python kb_deep_cleaner.py
  python kb_deep_cleaner.py --input data/bootstrapper_output/knowledge_base_100k.npz
"""

import sys, os, re, time, argparse
from pathlib import Path
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))


# ═══════════════════════════════════════════════════════════════════════════════
# PATTERNS DE CORRUPTION
# ═══════════════════════════════════════════════════════════════════════════════

# Marqueurs de concaténation dans les relations
_CONCAT_MARKERS = [
    (r'\s+puis\s+', ' puis '),           # Français : "vient de puis signifie"
    (r'\s+→\s+', ' → '),                 # Flèche : "high praise from → called"
    (r'\s+>>\s+', ' >> '),               # Double flèche
    (r'\s+à pour\s+', ' à pour '),       # "capitale à pour capitale" (corruption)
    (r'\s+de puis\s+', ' de puis '),     # "capitale de puis headed"
]

# Patterns de nettoyage
_CLEAN_PATTERNS = [
    (r'^\d+[\.\)]\s*', ''),              # "10. tokyo" → "tokyo"
    (r'\s*\(\d{4}[\-\–]\d{4}\)\s*', ' '),  # "(1503-1519)" → " "
    (r'\s*\(\d{4}\)\s*', ' '),           # "(1928)" → " "
    (r'\s*\(\d{1,2}\s*(?:jan|fév|feb|mar|avr|apr|mai|may|juin|jun|juil|jul|août|aug|sept|sep|oct|nov|déc|dec)[^)]*\)\s*', ' '),  # dates
    (r'\s+', ' '),                        # Espaces multiples → un seul
]

# Sujets triviaux à filtrer (étendus)
_TRIVIAL_SUBJECTS = {
    'he', 'she', 'they', 'it', 'this', 'that', 'these', 'those',
    'one', 'two', 'three', 'first', 'second', 'third',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
    'also', 'later', 'however', 'thus', 'therefore', 'then',
    'various', 'several', 'many', 'some', 'other', 'another',
    'part', 'parts', 'form', 'forms', 'type', 'types',
    'number', 'numbers', 'list', 'lists',
    'example', 'examples', 'case', 'cases',
    'member', 'members', 'group', 'groups',
    'year', 'years', 'time', 'times',
    'way', 'ways', 'kind', 'kinds',
    'thing', 'things', 'stuff',
    'people', 'person', 'persons',
    'man', 'woman', 'child', 'children',
    'day', 'days', 'month', 'months',
    'place', 'places', 'area', 'areas',
    'lot', 'lots', 'bit', 'bits',
    'use', 'uses', 'using', 'used',
    'term', 'terms', 'word', 'words', 'name', 'names',
    'end', 'ends', 'beginning', 'start',
    'fact', 'facts', 'detail', 'details',
    'datum', 'data', 'information',
    'history', 'culture', 'science', 'art',
}


def clean_text(text: str) -> str:
    """Nettoie un texte (sujet, relation, ou objet)."""
    text = text.strip()
    for pattern, replacement in _CLEAN_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text.strip()


def split_concat_fact(s: str, r: str, o: str, sec: str) -> list:
    """
    Détecte et sépare les faits concaténés.

    Si la relation contient un marqueur de concaténation, on essaie de
    produire deux faits séparés en coupant à ce marqueur.

    Returns:
        liste de faits (peut être vide, 1 élément, ou 2 éléments)
    """
    # Vérifier chaque marqueur
    for regex, marker in _CONCAT_MARKERS:
        match = re.search(regex, r)
        if match:
            # Couper la relation en deux
            r1 = r[:match.start()].strip()
            r2 = r[match.end():].strip()

            # Essayer de produire deux faits
            facts = []
            if r1 and len(r1) >= 2:
                facts.append((clean_text(s), clean_text(r1), clean_text(o), sec))
            if r2 and len(r2) >= 2:
                # Le deuxième fait peut avoir un objet différent
                # (l'objet original reste attaché au premier)
                facts.append((clean_text(s), clean_text(r2), clean_text(o), sec))
            return facts if facts else [(clean_text(s), clean_text(r), clean_text(o), sec)]

    # Vérifier aussi dans l'objet
    for regex, marker in _CONCAT_MARKERS:
        match = re.search(regex, o)
        if match:
            o1 = o[:match.start()].strip()
            o2 = o[match.end():].strip()
            facts = []
            if o1 and len(o1) >= 2:
                facts.append((clean_text(s), clean_text(r), clean_text(o1), sec))
            if o2 and len(o2) >= 2:
                facts.append((clean_text(s), clean_text(r), clean_text(o2), sec))
            return facts if facts else [(clean_text(s), clean_text(r), clean_text(o), sec)]

    # Pas de concaténation → retourner le fait nettoyé
    return [(clean_text(s), clean_text(r), clean_text(o), sec)]


def is_valid_fact(s: str, r: str, o: str, sec: str) -> bool:
    """
    Vérifie si un fait est valide (pas de bruit).

    Critères :
      - Sujet >= 2 caractères
      - Objet >= 3 caractères
      - Sujet pas dans la liste triviale
      - Relation >= 2 caractères et < 150 caractères
      - Objet < 300 caractères
      - Sujet != Objet (pas de boucle)
      - Sujet pas un nombre pur
      - Objet pas juste une ponctuation
    """
    s = s.strip()
    r = r.strip()
    o = o.strip()

    if len(s) < 2:
        return False
    if len(o) < 3:
        return False
    if len(r) < 2:
        return False
    if len(r) > 150:
        return False
    if len(o) > 300:
        return False

    if s.lower() in _TRIVIAL_SUBJECTS:
        return False

    if s.lower() == o.lower():
        return False

    if re.match(r'^[\d\s\.\,\-\+]+$', s):
        return False

    if re.match(r'^[\s\.\,\;\:\!\?]+$', o):
        return False

    # Objet qui n'est que des stopwords
    obj_words = [w for w in o.lower().split() if len(w) > 2]
    if len(obj_words) == 0:
        return False

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def deep_clean_kb(input_path: str, output_path: str = None, verbose: bool = True):
    """Nettoie profondément la KB."""

    input_path = Path(input_path)
    if not input_path.exists():
        print(f"Fichier introuvable : {input_path}")
        return

    data = np.load(str(input_path), allow_pickle=True)
    raw_facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3])) for f in data['facts']]
    n_original = len(raw_facts)

    if verbose:
        print("=" * 70)
        print("KB DEEP CLEANER — Nettoyage des artefacts de concaténation")
        print("=" * 70)
        print(f"\nChargé : {n_original:,} faits")

    # Phase 1 : Séparer les faits concaténés
    phase1_facts = []
    concat_found = 0
    splits_created = 0
    for s, r, o, sec in raw_facts:
        split_facts = split_concat_fact(s, r, o, sec)
        if len(split_facts) > 1:
            concat_found += 1
            splits_created += len(split_facts) - 1
        phase1_facts.extend(split_facts)

    if verbose:
        print(f"🔧 Concaténations détectées : {concat_found:,}")
        print(f"   → {splits_created:,} nouveaux faits créés par séparation")
        print(f"   → {len(phase1_facts):,} faits après phase 1")

    # Phase 2 : Nettoyer chaque champ
    phase2_facts = []
    for s, r, o, sec in phase1_facts:
        s = clean_text(s)
        r = clean_text(r)
        o = clean_text(o)
        phase2_facts.append((s, r, o, sec))

    if verbose:
        # Compter les préfixes numériques retirés
        num_prefix_removed = sum(1 for s, _, _, _ in phase2_facts
                                 if re.match(r'^\d+[\.\)]\s', s) is None
                                 and any(re.match(r'^\d+[\.\)]\s', orig_s)
                                        for orig_s, _, _, _ in phase1_facts
                                        if orig_s == s))
        print(f"🔤 Préfixes numériques nettoyés : estimés nombreux")

    # Phase 3 : Filtrer les faits invalides
    phase3_facts = []
    removed = 0
    for s, r, o, sec in phase2_facts:
        if is_valid_fact(s, r, o, sec):
            phase3_facts.append((s, r, o, sec))
        else:
            removed += 1

    if verbose:
        print(f"🧹 Faits invalides filtrés : {removed:,}")
        print(f"   → {len(phase3_facts):,} faits après phase 3")

    # Phase 4 : Dédoublonner
    seen = set()
    phase4_facts = []
    dups = 0
    for s, r, o, sec in phase3_facts:
        key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
        if key not in seen:
            seen.add(key)
            phase4_facts.append((s, r, o, sec))
        else:
            dups += 1

    if verbose:
        print(f"📋 Doublons retirés : {dups:,}")
        print(f"   → {len(phase4_facts):,} faits finaux")

    # Statistiques finales
    n_final = len(phase4_facts)
    retention = n_final / n_original * 100

    if verbose:
        print(f"\n{'='*70}")
        print(f"RÉSULTAT : {n_original:,} → {n_final:,} faits")
        print(f"Retenus  : {retention:.1f}%")
        print(f"Créés    : {splits_created:,} (par séparation)")
        print(f"Filtrés  : {removed:,} (invalides)")
        print(f"Dédoubl. : {dups:,}")
        print(f"{'='*70}")

    # Sauvegarde
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_deep_clean.npz"
    output_path = Path(output_path)

    facts_array = np.array(phase4_facts, dtype=object)
    np.savez(str(output_path), facts=facts_array)
    print(f"\n💾 Sauvegardé : {output_path}")

    return phase4_facts


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nettoie profondément la KB des artefacts de concaténation")
    parser.add_argument('--input', type=str,
                       default='data/bootstrapper_output/knowledge_base_100k.npz',
                       help='Fichier .npz d\'entrée')
    parser.add_argument('--output', type=str, default=None,
                       help='Fichier .npz de sortie')
    parser.add_argument('--quiet', action='store_true', help='Mode silencieux')
    args = parser.parse_args()

    deep_clean_kb(args.input, args.output, verbose=not args.quiet)
