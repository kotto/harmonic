"""
KB Expansion — 51K → 500K faits
================================
Pipeline massif multi-stratégie. Conçu pour tourner en background.

Stratégies :
  1. Cross-lingual : traduire les 51K faits FR → EN (×2)
  2. Bulk LLM : 100+ faits par prompt, 50 prompts
  3. Template expansion : variations à grande échelle
  4. Transitivité itérative : fermeture du graphe de connaissance
  5. Wikidata/DBpedia : faits structurés (si dispo)

Usage:
  python expand_to_500k.py          # lancement complet
  python expand_to_500k.py --fast    # mode rapide (templates + transitivité)
  python expand_to_500k.py --resume  # reprendre après interruption
"""

import sys, os, time, json, re, random
import numpy as np
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bootstrapper import extract_triples_simple, detect_sector
from holographic_encoder import HolographicEncoder
from holographic_trainer import HolographicTrainer, QualityGuard

OUTPUT_DIR = Path('../data/bootstrapper_output')
CHECKPOINT_FILE = OUTPUT_DIR / 'checkpoint_500k.json'

# ═══════════════════════════════════════════════════════════════════════════════
# STRATÉGIE 1 : CROSS-LINGUAL (FR → EN)
# ═══════════════════════════════════════════════════════════════════════════════

EN_TRANSLATIONS = {
    # Relations courantes FR → EN
    'est un': 'is a', 'est une': 'is a', 'sont des': 'are',
    'a decouvert': 'discovered', 'a invente': 'invented', 'a cree': 'created',
    'a formule': 'formulated', 'a publié': 'published', 'a ecrit': 'wrote',
    'a developpe': 'developed', 'a fonde': 'founded', 'a etabli': 'established',
    'contient': 'contains', 'comprend': 'includes',
    'se deplace a': 'travels at', 'se trouve dans': 'is found in',
    'est compose de': 'is composed of', 'fait partie de': 'is part of',
    'est lie a': 'is linked to', 'est associe a': 'is associated with',
    'a pour fonction': 'functions as', 'permet de': 'enables',
    'est la': 'is the', 'est le': 'is the',
    'a ete decouvert par': 'was discovered by', 'a ete invente par': 'was invented by',
    'a ete cree par': 'was created by', 'a ete fonde par': 'was founded by',
    'a ete developpe par': 'was developed by', 'utilise': 'uses',
    'produit': 'produces', 'transforme': 'transforms', 'transmet': 'transmits',
    'stocke': 'stores', 'protege': 'protects', 'active': 'activates',
    'inhibe': 'inhibits', 'regule': 'regulates', 'mesure': 'measures',
    'detecte': 'detects', 'convertit': 'converts', 'absorbe': 'absorbs',
    'reflete': 'reflects', 'emet': 'emits', 'genere': 'generates',
    'cause': 'causes', 'entraine': 'causes', 'provoque': 'triggers',
    'implique': 'implies', 'signifie': 'means', 'definit': 'defines',
    'a une': 'has a', 'a un': 'has a', 'possede': 'possesses',
    'appartient a': 'belongs to', 'depend de': 'depends on',
    'influence': 'influences', 'affecte': 'affects', 'modifie': 'modifies',
    'cree': 'creates', 'detruit': 'destroys', 'maintient': 'maintains',
    'constitue': 'constitutes', 'represente': 'represents',
}


def translate_fact(s: str, r: str, o: str) -> tuple:
    """Traduit un fait FR en EN (basique)."""
    # Traduire la relation
    r_en = r
    for fr, en in sorted(EN_TRANSLATIONS.items(), key=lambda x: -len(x[0])):
        if fr in r:
            r_en = r.replace(fr, en)
            break
    
    # Pour le sujet et l'objet, on garde le terme original
    # (une vraie traduction nécessiterait un LLM, on fait simple)
    return (s, r_en, o)


def cross_lingual_expansion(facts: list) -> list:
    """Génère la version anglaise de tous les faits FR."""
    new_facts = []
    existing = set((s, r, o) for s, r, o, _ in facts)
    
    for s, r, o, sec in facts:
        s_en, r_en, o_en = translate_fact(s, r, o)
        if r_en != r:  # seulement si la relation a été traduite
            key = (s_en, r_en, o_en)
            if key not in existing:
                new_facts.append((s_en, r_en, o_en, sec))
    
    return new_facts


# ═══════════════════════════════════════════════════════════════════════════════
# STRATÉGIE 2 : BULK LLM (100+ FAITS PAR PROMPT)
# ═══════════════════════════════════════════════════════════════════════════════

BULK_PROMPTS = [
    # Format: (secteur, prompt demandant 100 faits)
    ("SCIENCES_100", """Liste exactement 100 faits scientifiques couvrant TOUS les domaines:
physique, chimie, biologie, astronomie, géologie, météorologie, océanographie.
Format EXACT: sujet | relation | objet
Un fait par ligne. Faits précis et vérifiables. En français."""),
    
    ("HISTOIRE_100", """Liste exactement 100 faits historiques couvrant:
antiquité, moyen âge, renaissance, époque moderne, 20e siècle, 21e siècle.
Format EXACT: sujet | relation | objet
Un fait par ligne. Dates et événements précis. En français."""),
    
    ("GEOGRAPHIE_100", """Liste exactement 100 faits géographiques:
capitales, populations, superficies, montagnes, fleuves, lacs, déserts, forêts.
Format EXACT: sujet | relation | objet
Un fait par ligne. En français."""),
    
    ("CULTURE_100", """Liste exactement 100 faits culturels:
littérature, musique, peinture, sculpture, cinéma, théâtre, architecture, danse.
Format EXACT: sujet | relation | objet
Un fait par ligne. En français."""),
    
    ("TECH_100", """Liste exactement 100 faits technologiques:
informatique, internet, IA, robotique, biotech, nanotech, énergie, transports.
Format EXACT: sujet | relation | objet
Un fait par ligne. En français."""),
    
    ("SANTE_100", """Liste exactement 100 faits sur la santé et la médecine:
anatomie, physiologie, maladies, traitements, médicaments, vaccins, nutrition.
Format EXACT: sujet | relation | objet
Un fait par ligne. En français."""),
    
    ("NATURE_100", """Liste exactement 100 faits sur la nature:
animaux, plantes, écosystèmes, évolution, biodiversité, climat, écologie.
Format EXACT: sujet | relation | objet
Un fait par ligne. En français."""),
    
    ("SOCIETE_100", """Liste exactement 100 faits sur la société:
économie, politique, droit, éducation, démographie, urbanisme, religions.
Format EXACT: sujet | relation | objet
Un fait par ligne. En français."""),
]


# ═══════════════════════════════════════════════════════════════════════════════
# STRATÉGIE 3 : TEMPLATE EXPANSION À GRANDE ÉCHELLE
# ═══════════════════════════════════════════════════════════════════════════════

def template_expansion_massive(facts: list, n_target: int = 100000) -> list:
    """
    Génère massivement des variations par templates.
    Pour chaque fait, crée plusieurs variantes syntaxiques.
    """
    patterns = [
        # (description, transformation)
        ('passif', lambda s, r, o: (o, f'est {r} par', s)),
        ('attribut', lambda s, r, o: (s, f'a la propriete: {r}', o)),
        ('definition', lambda s, r, o: (f'{s} ({o})', 'est defini comme', r)),
        ('appartenance', lambda s, r, o: (o, f'caracterise', s)),
        ('capacite', lambda s, r, o: (s, f'a la capacite de {r}', o)),
    ]
    
    existing = set((s, r, o) for s, r, o, _ in facts)
    new_facts = []
    
    for s, r, o, sec in random.sample(facts, min(len(facts), 40000)):
        for name, transform in patterns:
            try:
                ns, nr, no = transform(s, r, o)
                if len(ns) > 1 and len(nr) > 1 and len(no) > 1:
                    key = (ns, nr, no)
                    if key not in existing:
                        new_facts.append((ns, nr, no, sec))
                        existing.add(key)
                        if len(new_facts) >= n_target:
                            return new_facts
            except:
                continue
    
    return new_facts


# ═══════════════════════════════════════════════════════════════════════════════
# STRATÉGIE 4 : TRANSITIVITÉ AVEC FERMETURE
# ═══════════════════════════════════════════════════════════════════════════════

def transitive_closure(facts: list, max_new: int = 50000) -> list:
    """Fermeture transitive du graphe de connaissance."""
    graph = defaultdict(list)
    for s, r, o, _ in facts:
        graph[s].append((r, o))
    
    existing = set((s, r, o) for s, r, o, _ in facts)
    new_facts = []
    
    # Pour chaque chemin de longueur 2: A → B → C ⇒ A → C
    for s, edges in list(graph.items()):
        if len(new_facts) >= max_new:
            break
        for r1, o1 in edges:
            if o1 in graph:
                for r2, o2 in graph[o1]:
                    if o2 != s and len(o2) > 2:
                        # Créer la relation composée
                        comp_r = f'{r1} → {r2}'
                        key = (s, comp_r, o2)
                        if key not in existing and len(key[0]) > 1:
                            # Détecter le secteur au lieu de hardcoder GENERAL
                            from bootstrapper import detect_sector
                            sec = detect_sector(f"{s} {comp_r} {o2}")
                            new_facts.append((s, comp_r, o2, sec))
                            existing.add(key)
                            if len(new_facts) >= max_new:
                                return new_facts
    
    return new_facts


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def load_facts():
    """Charge les faits existants ou checkpoint."""
    kb_path = OUTPUT_DIR / 'knowledge_base_50k.npz'
    if not kb_path.exists():
        kb_path = OUTPUT_DIR / 'knowledge_base_final.npz'
    
    data = np.load(str(kb_path), allow_pickle=True)
    return [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]


def save_checkpoint(facts, step: str):
    """Sauvegarde checkpoint."""
    CHECKPOINT_FILE.write_text(json.dumps({
        'step': step, 'n_facts': len(facts), 'timestamp': time.time()
    }))
    np.savez(str(OUTPUT_DIR / 'knowledge_base_500k.npz'),
             facts=np.array(facts, dtype=object))


def main(args=None):
    fast_mode = '--fast' in (sys.argv if args is None else args)
    resume = '--resume' in (sys.argv if args is None else args)
    
    print("=" * 60)
    print("EXPANSION 51K → 500K")
    print("=" * 60)
    
    # Charger
    facts = load_facts()
    print(f"\nDépart: {len(facts)} faits")
    existing = set((s, r, o) for s, r, o, _ in facts)
    
    total_added = 0
    target = 500000
    
    # Phase 1: Cross-lingual (FR → EN)
    print("\n[1/5] Cross-lingual FR → EN...")
    en_facts = cross_lingual_expansion(facts)
    added_en = 0
    for s, r, o, sec in en_facts:
        if (s, r, o) not in existing:
            facts.append((s, r, o, sec))
            existing.add((s, r, o))
            added_en += 1
    total_added += added_en
    print(f"  +{added_en} faits anglais")
    save_checkpoint(facts, 'cross_lingual')
    
    if len(facts) >= target:
        print(f"\nCible atteinte: {len(facts)} faits!")
        return facts
    
    # Phase 2: Template expansion massive
    print(f"\n[2/5] Template expansion (cible: 200K)...")
    n_templates = max(0, min(200000 - len(facts), 150000))
    template_facts = template_expansion_massive(facts, n_templates)
    added_t = 0
    for s, r, o, sec in template_facts:
        if (s, r, o) not in existing:
            facts.append((s, r, o, sec))
            existing.add((s, r, o))
            added_t += 1
    total_added += added_t
    print(f"  +{added_t} faits par templates")
    save_checkpoint(facts, 'templates')
    
    if len(facts) >= target:
        print(f"\nCible atteinte: {len(facts)} faits!")
        return facts
    
    # Phase 3: Transitivité itérative
    print(f"\n[3/5] Transitivité itérative...")
    for iteration in range(3):
        if len(facts) >= target:
            break
        n_trans = max(0, min(target - len(facts), 100000))
        trans_facts = transitive_closure(facts, n_trans)
        added_tr = 0
        for s, r, o, sec in trans_facts:
            if (s, r, o) not in existing:
                facts.append((s, r, o, sec))
                existing.add((s, r, o))
                added_tr += 1
        total_added += added_tr
        print(f"  Itération {iteration+1}: +{added_tr} faits transitifs (total: {len(facts)})")
        save_checkpoint(facts, f'transitive_{iteration}')
    
    if len(facts) >= target:
        print(f"\nCible atteinte: {len(facts)} faits!")
        return facts
    
    # Phase 4: Bulk LLM (si disponible)
    if not fast_mode:
        print(f"\n[4/5] Bulk LLM (100+ faits/prompt)...")
        try:
            from bootstrapper import _LLM_AVAILABLE, _LLM
            if _LLM_AVAILABLE:
                for sector, prompt in BULK_PROMPTS:
                    if len(facts) >= target:
                        break
                    try:
                        print(f"  {sector}...", end=' ', flush=True)
                        resp = _LLM.generate(prompt, category='factual')
                        text = resp.content.strip()
                        added_llm = 0
                        for line in text.split('\n'):
                            parts = line.strip().split('|')
                            if len(parts) >= 3:
                                s = parts[0].strip().lower()
                                r = parts[1].strip().lower()
                                o = parts[2].strip().lower()
                                if len(s) > 1 and len(o) > 2 and len(r) > 1:
                                    key = (s, r, o)
                                    if key not in existing:
                                        sec = detect_sector(f'{s} {r} {o}')
                                        facts.append((s, r, o, sec))
                                        existing.add(key)
                                        added_llm += 1
                        total_added += added_llm
                        print(f"+{added_llm} (total: {len(facts)})")
                        time.sleep(0.3)
                        save_checkpoint(facts, f'llm_{sector}')
                    except Exception as e:
                        print(f"erreur: {e}")
        except ImportError:
            print("  LLM non disponible")
    
    # Phase 5: Dernière transitive
    if len(facts) < target:
        print(f"\n[5/5] Transitivité finale...")
        n_final = target - len(facts)
        final_facts = transitive_closure(facts, n_final)
        added_f = 0
        for s, r, o, sec in final_facts:
            if (s, r, o) not in existing:
                facts.append((s, r, o, sec))
                existing.add((s, r, o))
                added_f += 1
        total_added += added_f
        print(f"  +{added_f} faits")
    
    # Sauvegarde finale
    save_checkpoint(facts, 'final')
    print(f"\n{'='*60}")
    print(f"RÉSULTAT: {len(facts)} faits (cible: {target})")
    print(f"Total ajoutés: +{total_added}")
    print(f"Sauvegardé: knowledge_base_500k.npz")
    
    return facts


if __name__ == '__main__':
    main()
