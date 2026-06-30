"""
KB Expansion v2 — 21K → 50K via bulk LLM + transitivité
=========================================================
Génération massive de faits de qualité via Claude Haiku.
Batching: 10-20 sujets par prompt → 5-10 faits par sujet.
"""

import sys, os, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bootstrapper import extract_triples_simple, detect_sector, _LLM_AVAILABLE

if _LLM_AVAILABLE:
    from bootstrapper import _LLM

OUTPUT_DIR = Path('../data/bootstrapper_output')

# Domaines à renforcer avec prompts ciblés
EXPANSION_PROMPTS = [
    # Format: (secteur, prompt)
    ("PHYSIQUE_FOND", "Liste 20 faits sur la physique fondamentale: lumière, ondes, gravité, énergie, résonance, électromagnétisme, mécanique quantique. Format: sujet | relation | objet. Un par ligne. En français."),
    ("BIOLOGIE", "Liste 20 faits sur la biologie: ADN, cellules, évolution, protéines, enzymes, photosynthèse, respiration cellulaire, mitose. Format: sujet | relation | objet. Un par ligne. En français."),
    ("ASTRONOMIE", "Liste 20 faits sur l'astronomie: étoiles, planètes, galaxies, système solaire, trous noirs, supernovas, exoplanètes. Format: sujet | relation | objet. Un par ligne. En français."),
    ("ECOLOGIE", "Liste 20 faits sur l'écologie: climat, biodiversité, pollution, énergies renouvelables, écosystèmes, réchauffement climatique, développement durable. Format: sujet | relation | objet. Un par ligne. En français."),
    ("CONSCIENCE", "Liste 15 faits sur la conscience: perception, méditation, états modifiés, neuroscience, inconscient, attention, pleine conscience. Format: sujet | relation | objet. Un par ligne. En français."),
    ("HISTOIRE", "Liste 20 faits historiques: révolutions, découvertes, civilisations anciennes, guerres mondiales, inventions majeures. Format: sujet | relation | objet. Un par ligne. En français."),
    ("CULTURE", "Liste 15 faits sur l'art et la culture: musique, peinture, littérature, cinéma, théâtre, poésie, architecture. Format: sujet | relation | objet. Un par ligne. En français."),
    ("TECHNOLOGIE", "Liste 15 faits sur la technologie: internet, intelligence artificielle, ordinateurs, smartphones, robotique, blockchain. Format: sujet | relation | objet. Un par ligne. En français."),
    ("MATHS_PURES", "Liste 15 faits mathématiques: géométrie, nombres, théorèmes, algèbre, topologie, probabilités, logique. Format: sujet | relation | objet. Un par ligne. En français."),
    ("CORPS_ORGANES", "Liste 15 faits sur le corps humain: organes, systèmes, cœur, cerveau, poumons, foie, reins. Format: sujet | relation | objet. Un par ligne. En français."),
    ("EMOTION_POS", "Liste 10 faits sur les émotions positives: joie, amour, gratitude, sérennité, bonheur, compassion. Format: sujet | relation | objet. Un par ligne. En français."),
    ("NATURE_VEGET", "Liste 15 faits sur les plantes: photosynthèse, arbres, fleurs, racines, forêts, agriculture. Format: sujet | relation | objet. Un par ligne. En français."),
    ("NATURE_ANIM", "Liste 15 faits sur les animaux: espèces, évolution, comportement, migration, prédateurs, chaîne alimentaire. Format: sujet | relation | objet. Un par ligne. En français."),
    ("FUTUR", "Liste 10 faits prospectifs: intelligence artificielle future, exploration spatiale, transhumanisme, énergie du futur. Format: sujet | relation | objet. Un par ligne. En français."),
    ("SPIRITUALITE", "Liste 10 faits sur la spiritualité et les religions: méditation, traditions, croyances, pratiques. Format: sujet | relation | objet. Un par ligne. En français."),
    ("ECONOMIE", "Liste 10 faits économiques: marché, capitalisme, inflation, PIB, commerce international, monnaie. Format: sujet | relation | objet. Un par ligne. En français."),
    ("GEOGRAPHIE", "Liste 15 faits géographiques: continents, océans, montagnes, fleuves, climats, pays. Format: sujet | relation | objet. Un par ligne. En français."),
    ("POLITIQUE", "Liste 10 faits politiques: démocratie, justice, droits humains, systèmes politiques, relations internationales. Format: sujet | relation | objet. Un par ligne. En français."),
    ("LINGUISTIQUE", "Liste 10 faits linguistiques: langues, grammaire, phonétique, évolution du langage, sémantique. Format: sujet | relation | objet. Un par ligne. En français."),
    ("SANTE", "Liste 15 faits sur la santé: nutrition, maladies, système immunitaire, vaccins, hygiène, prévention. Format: sujet | relation | objet. Un par ligne. En français."),
]


def parse_llm_response(text: str, default_sector: str = "GENERAL") -> list:
    """Parse la réponse du LLM en liste de triplets."""
    triples = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('Voici') or line.startswith('Format'):
            continue
        parts = line.split('|')
        if len(parts) >= 3:
            s = parts[0].strip().lower()
            r = parts[1].strip().lower()
            o = parts[2].strip().lower()
            if len(s) > 1 and len(o) > 2 and len(r) > 1:
                sec = detect_sector(f"{s} {r} {o}")
                if sec == "GENERAL":
                    sec = default_sector
                triples.append((s, r, o, sec))
        elif len(parts) == 1 and len(line) > 20:
            # Essayer l'extraction simple
            simple = extract_triples_simple(line)
            for s, r, o, sec in simple:
                if sec == "GENERAL":
                    sec = default_sector
                triples.append((s, r, o, sec))
    return triples


def main():
    t0 = time.time()
    
    # Charger les faits existants
    kb_path = OUTPUT_DIR / 'knowledge_base_final.npz'
    data = np.load(str(kb_path), allow_pickle=True)
    facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
    existing = set((s, r, o) for s, r, o, _ in facts)
    
    print(f"Faits initiaux: {len(facts)}")
    print(f"LLM disponible: {bool(_LLM_AVAILABLE)}")
    
    if not _LLM_AVAILABLE:
        print("LLM non disponible. Utilisation de l'expansion par variations seulement.")
    
    total_added = 0
    
    # Phase 1: Bulk LLM
    if _LLM_AVAILABLE:
        print("\n=== PHASE 1: GÉNÉRATION LLM PAR DOMAINE ===")
        for sector, prompt in EXPANSION_PROMPTS:
            try:
                print(f"  {sector}...", end=' ', flush=True)
                resp = _LLM.generate(prompt, category="factual")
                text = resp.content.strip()
                
                if not text:
                    print("réponse vide")
                    continue
                
                triples = parse_llm_response(text, sector)
                added = 0
                for s, r, o, sec in triples:
                    if (s, r, o) not in existing:
                        facts.append((s, r, o, sec))
                        existing.add((s, r, o))
                        added += 1
                
                total_added += added
                print(f"+{added} faits")
                time.sleep(0.3)  # rate limiting
                
            except Exception as e:
                print(f"erreur: {e}")
    
    # Phase 2: Transitivité (A→B + B→C → A→C)
    print(f"\n=== PHASE 2: FERMETURE TRANSITIVE ===")
    # Construire le graphe sujet→objet
    graph = {}
    for s, r, o, _ in facts:
        if s not in graph:
            graph[s] = []
        graph[s].append((r, o))
    
    transitive_added = 0
    for s, edges in list(graph.items())[:10000]:
        for r1, o1 in edges:
            if o1 in graph:
                for r2, o2 in graph[o1]:
                    # Éviter les boucles
                    if o2 != s and len(o2) > 2:
                        new_fact = (s, f"{r1} puis {r2}", o2, "GENERAL")
                        key = (s, f"{r1} puis {r2}", o2)
                        if key not in existing:
                            facts.append(new_fact)
                            existing.add(key)
                            transitive_added += 1
    
    print(f"  +{transitive_added} faits transitifs")
    total_added += transitive_added
    
    # Phase 3: Variations passives
    print(f"\n=== PHASE 3: VARIATIONS PASSIVES ===")
    var_added = 0
    passive_patterns = [
        ('a decouvert', 'a ete decouvert par'),
        ('a invente', 'a ete invente par'),
        ('a cree', 'a ete cree par'),
        ('a formule', 'a ete formulee par'),
        ('est un', 'est une forme de'),
        ('est une', 'est un type de'),
    ]
    
    for s, r, o, sec in facts[:30000]:
        for active, passive in passive_patterns:
            if active in r:
                ns, nr, no = o, passive, s
                key = (ns, nr, no)
                if key not in existing and len(ns) > 1:
                    facts.append((ns, nr, no, sec))
                    existing.add(key)
                    var_added += 1
                break
    
    print(f"  +{var_added} variations")
    total_added += var_added
    
    # Sauvegarde
    print(f"\n{'='*50}")
    print(f"RÉSULTAT: {len(facts)} faits (cible: 50000)")
    print(f"  LLM: +{total_added - transitive_added - var_added}")
    print(f"  Transitivité: +{transitive_added}")
    print(f"  Variations: +{var_added}")
    print(f"  Total ajoutés: +{total_added}")
    print(f"  Temps: {time.time() - t0:.1f}s")
    
    output_path = OUTPUT_DIR / 'knowledge_base_50k.npz'
    kb_array = np.array(facts, dtype=object)
    np.savez(str(output_path), facts=kb_array)
    print(f"\nSauvegardé: {output_path}")
    
    return facts


if __name__ == '__main__':
    main()
