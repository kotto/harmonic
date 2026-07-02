"""
Ingestion Massive Nocturne — 50K → 200K+ faits
===============================================
Utilise Claude Haiku pour générer des faits ciblés par domaine.
Checkpoints toutes les 5000 lignes. Reprend en cas d'interruption.

Usage:
  python ingest_overnight.py              # utiliser la KB existante
  python ingest_overnight.py --resume     # reprendre après interruption
  python ingest_overnight.py --target 200000  # cible personnalisée
"""

import sys, os, time, json, random
import numpy as np
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bootstrapper import extract_triples_simple, detect_sector

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

TARGET_FACTS = 200000
CHECKPOINT_EVERY = 2000
BATCH_SIZE = 30  # faits par prompt LLM
RATE_LIMIT = 0.3  # secondes entre appels
OUTPUT_DIR = Path('../data/bootstrapper_output')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = OUTPUT_DIR / 'checkpoint_overnight.json'
OUTPUT_FILE = OUTPUT_DIR / 'knowledge_base_overnight.npz'

# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS PAR DOMAINE (chaque prompt génère 30 faits)
# ═══════════════════════════════════════════════════════════════════════════════

DOMAIN_PROMPTS = [
    # Sciences
    ("PHYSIQUE", "Liste 30 faits de physique: mécanique classique, thermodynamique, électromagnétisme, relativité, physique quantique, physique nucléaire. Format EXACT: sujet | relation | objet. Un par ligne. En français. Faits précis."),
    ("CHIMIE", "Liste 30 faits de chimie: éléments, réactions, liaisons, équilibres, catalyse, tableau périodique, chimie organique. Format: sujet | relation | objet. Un par ligne. En français."),
    ("BIOLOGIE", "Liste 30 faits de biologie: cellules, ADN, protéines, enzymes, évolution, génétique, microbiologie. Format: sujet | relation | objet. Un par ligne. En français."),
    ("ASTRONOMIE", "Liste 30 faits d'astronomie: étoiles, galaxies, planètes, lune, soleil, trous noirs, exoplanètes, constellations. Format: sujet | relation | objet. Un par ligne. En français."),
    ("GEOLOGIE", "Liste 30 faits de géologie: roches, minéraux, tectonique, volcans, séismes, ères géologiques, fossiles. Format: sujet | relation | objet. Un par ligne. En français."),
    ("CLIMAT", "Liste 30 faits sur le climat et la météo: atmosphère, précipitations, vents, saisons, changement climatique. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Histoire & Géographie
    ("HISTOIRE_ANTIQUE", "Liste 30 faits sur l'antiquité: Égypte, Grèce, Rome, Mésopotamie, Chine ancienne, empires. Format: sujet | relation | objet. Un par ligne. En français."),
    ("HISTOIRE_MODERNE", "Liste 30 faits historiques: Moyen Âge, Renaissance, Révolutions, guerres mondiales, 20e siècle. Format: sujet | relation | objet. Un par ligne. En français."),
    ("GEOGRAPHIE", "Liste 30 faits géographiques: pays, capitales, fleuves, montagnes, océans, déserts, populations. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Culture
    ("LITTERATURE", "Liste 30 faits de littérature: auteurs célèbres, œuvres majeures, prix Nobel, genres littéraires. Format: sujet | relation | objet. Un par ligne. En français."),
    ("MUSIQUE", "Liste 30 faits musicaux: compositeurs, instruments, genres, théorie musicale, histoire de la musique. Format: sujet | relation | objet. Un par ligne. En français."),
    ("CINEMA", "Liste 30 faits de cinéma: réalisateurs, acteurs, films célèbres, techniques, histoire du cinéma. Format: sujet | relation | objet. Un par ligne. En français."),
    ("ART", "Liste 30 faits artistiques: peinture, sculpture, architecture, mouvements artistiques, musées. Format: sujet | relation | objet. Un par ligne. En français."),
    ("PHILOSOPHIE", "Liste 30 faits philosophiques: penseurs, concepts, écoles, éthique, métaphysique, logique. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Société
    ("ECONOMIE", "Liste 30 faits économiques: marchés, monnaies, théories, institutions, commerce, développement. Format: sujet | relation | objet. Un par ligne. En français."),
    ("POLITIQUE", "Liste 30 faits politiques: systèmes, institutions, droits, relations internationales, constitutions. Format: sujet | relation | objet. Un par ligne. En français."),
    ("DROIT", "Liste 30 faits juridiques: lois, codes, tribunaux, procédures, droits fondamentaux. Format: sujet | relation | objet. Un par ligne. En français."),
    ("SOCIOLOGIE", "Liste 30 faits sociologiques: structures sociales, démographie, urbanisation, inégalités, cultures. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Technologie
    ("INFORMATIQUE", "Liste 30 faits informatiques: ordinateurs, langages, algorithmes, internet, bases de données. Format: sujet | relation | objet. Un par ligne. En français."),
    ("IA", "Liste 30 faits sur l'intelligence artificielle: machine learning, deep learning, réseaux de neurones, NLP, vision. Format: sujet | relation | objet. Un par ligne. En français."),
    ("ROBOTIQUE", "Liste 20 faits de robotique: robots industriels, drones, automatisation, capteurs. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Santé & Corps
    ("MEDECINE", "Liste 30 faits médicaux: maladies, traitements, vaccins, chirurgie, diagnostic, prévention. Format: sujet | relation | objet. Un par ligne. En français."),
    ("ANATOMIE", "Liste 30 faits anatomiques: organes, systèmes, squelette, muscles, système nerveux. Format: sujet | relation | objet. Un par ligne. En français."),
    ("NUTRITION", "Liste 20 faits nutritionnels: aliments, vitamines, minéraux, régimes, métabolisme. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Nature
    ("BOTANIQUE", "Liste 30 faits botaniques: plantes, arbres, fleurs, fruits, légumes, photosynthèse. Format: sujet | relation | objet. Un par ligne. En français."),
    ("ZOOLOGIE", "Liste 30 faits zoologiques: animaux, espèces, comportement, habitats, évolution. Format: sujet | relation | objet. Un par ligne. En français."),
    ("ECOLOGIE", "Liste 30 faits écologiques: écosystèmes, biodiversité, pollution, conservation, climat. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Spiritualité & Conscience
    ("SPIRITUALITE", "Liste 30 faits sur les religions et spiritualités: traditions, pratiques, croyances, textes sacrés. Format: sujet | relation | objet. Un par ligne. En français."),
    ("PSYCHOLOGIE", "Liste 30 faits psychologiques: comportement, cognition, émotions, développement, troubles. Format: sujet | relation | objet. Un par ligne. En français."),
    ("NEUROSCIENCE", "Liste 30 faits neuroscientifiques: cerveau, neurones, synapses, mémoire, perception. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Pratique
    ("SPORT", "Liste 20 faits sportifs: disciplines, records, athlètes, compétitions, règles. Format: sujet | relation | objet. Un par ligne. En français."),
    ("CUISINE", "Liste 20 faits culinaires: gastronomie, techniques, ingrédients, plats, traditions. Format: sujet | relation | objet. Un par ligne. En français."),
    ("TRANSPORT", "Liste 20 faits sur les transports: voitures, trains, avions, bateaux, infrastructures. Format: sujet | relation | objet. Un par ligne. En français."),
    ("ARCHITECTURE", "Liste 20 faits architecturaux: bâtiments célèbres, styles, matériaux, architectes. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Langues
    ("LINGUISTIQUE", "Liste 20 faits linguistiques: langues, grammaire, phonétique, étymologie, familles de langues. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Plus de sciences (2e passe)
    ("PHYSIQUE_2", "Liste 30 faits de physique: optique, acoustique, mécanique des fluides, physique des particules, astrophysique. Format: sujet | relation | objet. Un par ligne. En français."),
    ("BIOLOGIE_2", "Liste 30 faits de biologie: immunologie, physiologie, écologie comportementale, biologie marine. Format: sujet | relation | objet. Un par ligne. En français."),
    ("MATHS", "Liste 30 faits mathématiques: nombres, géométrie, algèbre, analyse, probabilités, statistiques. Format: sujet | relation | objet. Un par ligne. En français."),
    
    # Plus d'histoire & géo (2e passe)
    ("HISTOIRE_SCIENCE", "Liste 30 faits sur l'histoire des sciences: découvertes, scientifiques, inventions, prix Nobel. Format: sujet | relation | objet. Un par ligne. En français."),
    ("GEOGRAPHIE_2", "Liste 30 faits géographiques: climats, ressources naturelles, démographie, frontières. Format: sujet | relation | objet. Un par ligne. En français."),
]


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def load_llm():
    """Charge le client LLM."""
    try:
        from bootstrapper import _LLM_AVAILABLE, _LLM
        if _LLM_AVAILABLE:
            return _LLM
    except Exception:
        pass
    return None


def parse_facts(text, default_sector="GENERAL"):
    """Parse la réponse LLM en liste de faits."""
    facts = []
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
                facts.append((s, r, o, sec))
    return facts


def save_checkpoint(facts, processed, added):
    """Sauvegarde checkpoint + KB partielle."""
    CHECKPOINT_FILE.write_text(json.dumps({
        'processed': processed,
        'total_facts': len(facts),
        'added': added,
        'timestamp': time.time(),
    }))
    np.savez(str(OUTPUT_FILE), facts=np.array(facts, dtype=object))


def main():
    target = TARGET_FACTS
    for arg in sys.argv[1:]:
        if arg.startswith('--target='):
            target = int(arg.split('=')[1])
    
    resume = '--resume' in sys.argv
    
    print("=" * 60)
    print(f"INGESTION MASSIVE NOCTURNE → {target:,} faits")
    print("=" * 60)
    
    # Charger LLM
    llm = load_llm()
    if not llm:
        print("❌ LLM non disponible. Arrêt.")
        return
    print(f"✅ LLM: disponible")
    
    # Charger les faits existants
    kb_path = OUTPUT_DIR / 'knowledge_base_50k.npz'
    if resume and OUTPUT_FILE.exists():
        data = np.load(str(OUTPUT_FILE), allow_pickle=True)
        facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
        print(f"📂 Reprise: {len(facts):,} faits")
    elif kb_path.exists():
        data = np.load(str(kb_path), allow_pickle=True)
        facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
        print(f"📂 Base 50K: {len(facts):,} faits")
    else:
        print("❌ Base 50K introuvable")
        return
    
    existing = set((s, r, o) for s, r, o, _ in facts)
    start_count = len(facts)
    total_added = 0
    processed = 0
    
    # Faire plusieurs passes si nécessaire
    max_passes = 3
    for pass_num in range(max_passes):
        if len(facts) >= target:
            break
        
        print(f"\n{'='*60}")
        print(f"PASSE {pass_num + 1}/{max_passes} — {len(facts):,} / {target:,} faits")
        print(f"{'='*60}")
        
        # Mélanger les prompts pour diversité
        prompts = list(DOMAIN_PROMPTS)
        random.shuffle(prompts)
        
        for sector, prompt in prompts:
            if len(facts) >= target:
                break
            
            try:
                print(f"  {sector}...", end=' ', flush=True)
                resp = llm.generate(prompt, category="factual")
                text = resp.content.strip()
                
                if not text:
                    print("vide")
                    continue
                
                batch = parse_facts(text, sector)
                added = 0
                for s, r, o, sec in batch:
                    if (s, r, o) not in existing:
                        facts.append((s, r, o, sec))
                        existing.add((s, r, o))
                        added += 1
                
                total_added += added
                processed += 1
                
                pct = len(facts) / target * 100
                print(f"+{added} ({len(facts):,} total, {pct:.1f}%)")
                
                # Checkpoint
                if processed % 5 == 0:
                    save_checkpoint(facts, processed, total_added)
                    print(f"    💾 Checkpoint: {len(facts):,} faits")
                
                time.sleep(RATE_LIMIT)
                
            except Exception as e:
                print(f"erreur: {e}")
                time.sleep(2)  # attendre un peu en cas d'erreur
    
    # Sauvegarde finale
    save_checkpoint(facts, processed, total_added)
    
    print(f"\n{'='*60}")
    print(f"TERMINÉ")
    print(f"  Départ: {start_count:,} faits")
    print(f"  Ajoutés: {total_added:,}")
    print(f"  Final: {len(facts):,} faits")
    print(f"  Sauvegardé: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
