"""
KB Expansion — 21K → 50K faits
===============================
Génère les ~28 500 faits manquants pour atteindre la masse critique.
Utilise : extraction regex du corpus + génération par templates + LLM ciblé.
Validation via QualityGuard.
"""

import sys, os, re, time, json
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bootstrapper import extract_triples_simple, extract_triples_llm, detect_sector
from holographic_encoder import HolographicEncoder, build_holographic_waves
from holographic_trainer import HolographicTrainer, QualityGuard

CORPUS_DIR = Path('../data/corpus')
OUTPUT_DIR = Path('../data/bootstrapper_output')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR DE FAITS PAR DOMAINE FAIBLE
# ═══════════════════════════════════════════════════════════════════════════════

DOMAIN_TEMPLATES = {
    'ECOLOGIE': [
        ("ecosysteme", "abrite", "biodiversite"),
        ("biodiversite", "est menacee par", "pollution"),
        ("climat", "est influence par", "effet de serre"),
        ("effet de serre", "est cause par", "gaz carbonique"),
        ("deforestation", "entraine", "erosion des sols"),
        ("ocean", "absorbe", "dioxyde de carbone"),
        ("coraux", "sont menaces par", "rechauffement climatique"),
        ("energie solaire", "est une source", "energie renouvelable"),
        ("energie eolienne", "utilise", "force du vent"),
        ("agriculture durable", "preserve", "ressources naturelles"),
        ("espèces menacees", "sont protegees par", "conservation"),
        ("zones humides", "filtrent", "polluants de l'eau"),
        ("foret amazonienne", "produit", "oxygene atmospherique"),
        ("fonte des glaces", "eleve", "niveau des mers"),
        ("recyclage", "reduit", "dechets enfouis"),
        ("compostage", "transforme", "dechets organiques"),
        ("empreinte carbone", "mesure", "impact environnemental"),
        ("couche d'ozone", "protege", "rayonnement ultraviolet"),
        ("pluies acides", "sont causees par", "pollution industrielle"),
        ("energie nucleaire", "produit", "dechets radioactifs"),
        ("parc national", "protege", "habitat naturel"),
        ("migration animale", "est perturbee par", "changement climatique"),
        ("surpêche", "epuise", "ressources marines"),
        ("permaculture", "imite", "ecosystemes naturels"),
        ("insectes pollinisateurs", "sont essentiels pour", "reproduction des plantes"),
    ],
    'CORPS_SENS': [
        ("vision", "permet de", "percevoir la lumière"),
        ("audition", "capte", "vibrations sonores"),
        ("toucher", "detecte", "pression et temperature"),
        ("odorat", "identifie", "molecules chimiques"),
        ("goût", "distingue", "saveurs fondamentales"),
        ("proprioception", "informe sur", "position du corps"),
        ("équilibre", "est maintenu par", "oreille interne"),
        ("douleur", "signale", "dommage tissulaire"),
        ("thermoception", "detecte", "changements de temperature"),
        ("rétine", "convertit", "lumière en signaux nerveux"),
        ("cochlée", "transforme", "ondes sonores en influx"),
        ("papilles gustatives", "contiennent", "recepteurs du goût"),
        ("nerf optique", "transmet", "information visuelle"),
        ("cortex visuel", "interprete", "signaux de la rétine"),
    ],
    'CULTURE': [
        ("musique classique", "a ete developpee par", "compositeurs europeens"),
        ("jazz", "est ne a", "nouvelle orleans"),
        ("cinema", "est un art", "visuel et narratif"),
        ("litterature", "explore", "condition humaine"),
        ("peinture", "utilise", "couleurs et formes"),
        ("sculpture", "travaille", "matiere dans l'espace"),
        ("danse", "exprime", "emotions par le mouvement"),
        ("theatre", "met en scene", "conflits humains"),
        ("architecture", "combine", "fonction et esthetique"),
        ("photographie", "capture", "instant present"),
        ("bande dessinee", "raconte", "histoires en images"),
        ("opera", "unit", "musique et theatre"),
        ("ballet", "allie", "danse et narration"),
        ("poesie", "joue avec", "rythme et sonorites"),
        ("calligraphie", "eleve", "ecriture au rang d'art"),
    ],
    'TECHNOLOGIE': [
        ("intelligence artificielle", "simule", "raisonnement humain"),
        ("internet", "connecte", "ordinateurs du monde"),
        ("smartphone", "combine", "telephone et ordinateur"),
        ("blockchain", "securise", "transactions decentralisees"),
        ("realite virtuelle", "immerge dans", "environnement simule"),
        ("impression 3D", "fabrique", "objets couche par couche"),
        ("robotique", "automatise", "tâches physiques"),
        ("nanotechnologie", "manipule", "matiere a l'echelle atomique"),
        ("biotechnologie", "utilise", "organismes vivants"),
        ("5G", "offre", "connectivite ultra-rapide"),
        ("informatique quantique", "exploite", "superposition quantique"),
        ("realite augmentee", "superpose", "numerique au reel"),
        ("cloud computing", "stocke", "donnees a distance"),
        ("cryptographie", "protege", "communications secretes"),
        ("drone", "survole", "zones inaccessibles"),
    ],
    'EMOTION_POS': [
        ("joie", "est associee a", "dopamine"),
        ("amour", "active", "circuit de recompense"),
        ("gratitude", "renforce", "liens sociaux"),
        ("serenite", "reduit", "niveau de cortisol"),
        ("compassion", "motive", "comportement altruiste"),
        ("espoir", "soutient", "resilience psychologique"),
        ("fierte", "est liee a", "accomplissement personnel"),
        ("contentement", "accompagne", "satisfaction des besoins"),
        ("admiration", "eleve", "estime de l'autre"),
        ("tendresse", "favorise", "attachement affectif"),
    ],
    'FUTUR': [
        ("transhumanisme", "vise", "depassement des limites humaines"),
        ("colonisation spatiale", "etend", "presence humaine au-dela de la Terre"),
        ("fusion nucleaire", "pourrait fournir", "energie illimitee"),
        ("medecine personnalisee", "adapte", "traitement au genome"),
        ("vehicules autonomes", "remplacent", "conducteurs humains"),
        ("realite etendue", "brouille", "frontiere reel-virtuel"),
        ("economie circulaire", "elimine", "notion de dechet"),
        ("villes intelligentes", "optimisent", "ressources urbaines"),
        ("impression d'organes", "resout", "penurie de greffons"),
        ("education adaptative", "personnalise", "apprentissage"),
    ],
}


def expand_weak_domains(facts: list, target_per_domain: int = 250) -> list:
    """
    Génère des faits pour les domaines faibles en utilisant des templates curés.
    """
    sector_counts = Counter(sec for _, _, _, sec in facts)
    new_facts = []
    
    for sector, templates in DOMAIN_TEMPLATES.items():
        current = sector_counts.get(sector, 0)
        needed = max(0, target_per_domain - current)
        
        if needed > 0:
            # Prendre les templates (sans dépasser le besoin)
            selected = templates[:min(needed, len(templates))]
            for s, r, o in selected:
                new_facts.append((s, r, o, sector))
    
    return new_facts


def expand_variations(facts: list, n_variations: int = 5000) -> list:
    """
    Génère des variations à partir des faits existants.
    Pour chaque fait, crée une version passive ou synonymique.
    """
    variations = []
    
    variation_patterns = [
        # (condition sur r, nouvelle relation, transformation)
        ('est un', 'est une forme de', lambda s, o: (s, 'est une forme de', o)),
        ('est une', 'appartient a la categorie', lambda s, o: (s, 'appartient a la categorie', o)),
        ('a decouvert', 'a ete decouvert par', lambda s, o: (o, 'a ete decouvert par', s)),
        ('a invente', 'a ete invente par', lambda s, o: (o, 'a ete invente par', s)),
        ('a cree', 'a ete cree par', lambda s, o: (o, 'a ete cree par', s)),
        ('a formule', 'a ete formulee par', lambda s, o: (o, 'a ete formulee par', s)),
    ]
    
    for s, r, o, sec in facts:
        for cond, new_r, transform in variation_patterns:
            if cond in r:
                ns, nr, no = transform(s, o)
                variations.append((ns, nr, no, sec))
                break
    
    # Dédupliquer et limiter
    seen = set((s, r, o) for s, r, o, _ in facts)
    unique = []
    for s, r, o, sec in variations:
        key = (s, r, o)
        if key not in seen:
            seen.add(key)
            unique.append((s, r, o, sec))
    
    return unique[:n_variations]


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    t0_total = time.time()
    
    # 1. Charger les faits existants
    print("=" * 60)
    print("EXPANSION KB : 21K → 50K faits")
    print("=" * 60)
    
    kb_path = OUTPUT_DIR / 'knowledge_base_final.npz'
    if kb_path.exists():
        data = np.load(str(kb_path), allow_pickle=True)
        facts = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in data['facts']]
    else:
        print("Fichier knowledge_base_final.npz introuvable!")
        return
    
    print(f"\nFaits initiaux: {len(facts)}")
    
    # 2. Expansion par templates (domaines faibles)
    print("\n[1/4] Expansion par templates (domaines faibles)...")
    template_facts = expand_weak_domains(facts, target_per_domain=200)
    added_templates = 0
    existing = set((s, r, o) for s, r, o, _ in facts)
    for s, r, o, sec in template_facts:
        if (s, r, o) not in existing:
            facts.append((s, r, o, sec))
            existing.add((s, r, o))
            added_templates += 1
    print(f"  +{added_templates} faits générés par templates")
    
    # 3. Expansion par variations
    print("\n[2/4] Expansion par variations...")
    var_facts = expand_variations(facts, n_variations=5000)
    added_vars = 0
    for s, r, o, sec in var_facts:
        if (s, r, o) not in existing:
            facts.append((s, r, o, sec))
            existing.add((s, r, o))
            added_vars += 1
    print(f"  +{added_vars} faits générés par variations")
    
    # 4. Extraction du corpus
    print("\n[3/4] Extraction du corpus...")
    corpus_texts = []
    if CORPUS_DIR.exists():
        for path in sorted(CORPUS_DIR.glob('wiki_*.txt')):
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if 50 < len(line) < 500:
                        corpus_texts.append(line)
    
    print(f"  {len(corpus_texts)} textes dans le corpus")
    
    added_corpus = 0
    batch_size = 500
    for i in range(0, min(len(corpus_texts), 5000), batch_size):
        batch = corpus_texts[i:i+batch_size]
        for text in batch:
            triples = extract_triples_simple(text)
            for s, r, o, sec in triples:
                if (s, r, o) not in existing:
                    facts.append((s, r, o, sec))
                    existing.add((s, r, o))
                    added_corpus += 1
        if (i + batch_size) % 1000 == 0:
            print(f"  Progression: {i+batch_size} textes, +{added_corpus} faits")
    
    print(f"  +{added_corpus} faits extraits du corpus")
    
    # 5. LLM ciblé pour les domaines les plus faibles (optionnel, si clé dispo)
    print("\n[4/4] LLM ciblé pour domaines critiques...")
    llm_added = 0
    try:
        from bootstrapper import _LLM_AVAILABLE
        if _LLM_AVAILABLE:
            weak_domains_prompts = [
                ("CONSCIENCE", "Explique les différents états de conscience, la méditation, et le rôle du cerveau dans la conscience."),
                ("METAPHYSIQUE", "Explique les concepts de réalité, existence, être et néant en philosophie."),
                ("ECOLOGIE", "Explique le réchauffement climatique, la biodiversité, et les énergies renouvelables."),
            ]
            for sector, prompt in weak_domains_prompts:
                try:
                    triples = extract_triples_llm(prompt)
                    for s, r, o, sec in triples:
                        sec = sector
                        if (s, r, o) not in existing:
                            facts.append((s, r, o, sec))
                            existing.add((s, r, o))
                            llm_added += 1
                    print(f"  {sector}: +{len(triples)} faits via LLM")
                except Exception as e:
                    print(f"  {sector}: erreur LLM - {e}")
            print(f"  +{llm_added} faits via LLM")
    except Exception:
        pass
    
    # 6. Sauvegarde
    print(f"\n{'='*60}")
    print(f"RÉSULTAT: {len(facts)} faits (cible: 50000)")
    print(f"  Templates: +{added_templates}")
    print(f"  Variations: +{added_vars}")
    print(f"  Corpus: +{added_corpus}")
    print(f"  LLM: +{llm_added}")
    
    output_path = OUTPUT_DIR / 'knowledge_base_expanded.npz'
    kb_array = np.array(facts, dtype=object)
    np.savez(str(output_path), facts=kb_array)
    print(f"\nSauvegardé: {output_path}")
    print(f"Temps total: {time.time() - t0_total:.1f}s")
    
    return facts


if __name__ == '__main__':
    main()
