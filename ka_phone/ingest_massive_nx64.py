#!/usr/bin/env python3
"""
KA-Next — INGESTION MASSIVE N×64×64
=======================================
Ingère toutes les sources de connaissances disponibles dans
l'ensemble holographique 12×64×64.

Sources :
  1. Corpus enrichi (UNESCO, sciences, philo, géo, etc.) — 429 faits
  2. QuickFacts — 1030 faits
  3. Fichiers texte locaux (*.txt, *.md) — variable
  4. Wikipedia FR dump (si disponible) — optionnel

Usage :
  python ingest_massive_nx64.py              # Ingestion complète
  python ingest_massive_nx64.py --audit      # Audit seulement
  python ingest_massive_nx64.py --corpus DIR # Ajouter un dossier
"""

import sys, os, math, json, time, hashlib, re, glob
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np

PHI = (1 + math.sqrt(5)) / 2

# ═══════════════════════════════════════════════════════════════════
# CORPUS UNESCO ENRICHI (Histoire Générale de l'Afrique, 8 volumes)
# ═══════════════════════════════════════════════════════════════════

UNESCO_CORPUS = [
    # Volume 1 — Préhistoire africaine
    "L'Afrique est le berceau de l'humanité. Les plus anciens fossiles d'Homo sapiens ont été découverts en Éthiopie, à Omo Kibish (195 000 ans) et au Maroc, à Jebel Irhoud (300 000 ans).",
    "La vallée du Rift africain a préservé les traces des premiers hominidés : Australopithecus afarensis (Lucy, 3.2 millions d'années), Homo habilis et Homo erectus.",
    "L'art rupestre du Tassili n'Ajjer en Algérie (12 000 ans) témoigne d'un Sahara autrefois verdoyant, peuplé de pasteurs avant la désertification.",
    "Les industries lithiques oldowayennes et acheuléennes en Afrique comptent parmi les plus anciennes technologies humaines connues.",

    # Volume 2 — Afrique ancienne
    "La civilisation de l'Égypte ancienne (Kemet) est africaine, née dans la vallée du Nil vers -3150 avec l'unification par le pharaon Narmer.",
    "Le royaume de Kouch (Nubie, Soudan actuel) a régné sur l'Égypte pendant la 25e dynastie, celle des pharaons noirs, de -747 à -656.",
    "Méroé, capitale du royaume de Kouch, possédait une industrie sidérurgique avancée et sa propre écriture méroïtique, encore non entièrement déchiffrée.",
    "L'Éthiopie antique, avec le royaume d'Axoum (-100 à +700), était une puissance commerciale majeure reliée à l'Inde et à Rome, adoptant le christianisme dès 330.",

    # Volume 3 — VIIe-XIe siècles
    "L'empire du Ghana (Wagadou, -300 à +1200) contrôlait le commerce transsaharien de l'or et du sel. Il fut décrit par Al-Bakri en 1068 comme le pays de l'or.",
    "L'empire du Kanem-Bornou (700-1900) autour du lac Tchad a duré 1200 ans, l'un des plus longs empires de l'histoire.",
    "Les cités-États swahilies (Kilwa, Mombasa, Zanzibar, 800-1500) étaient des plaques tournantes du commerce de l'océan Indien, reliant l'Afrique à la Chine et l'Inde.",
    "La Grande Mosquée de Djenné au Mali, construite en terre crue, est le plus grand bâtiment en banco du monde, inscrit au patrimoine mondial de l'UNESCO.",

    # Volume 4 — XIIe-XVIe siècles
    "L'empire du Mali (1230-1670), fondé par Soundiata Keita, était le plus riche empire du monde médiéval. Le pèlerinage de Mansa Moussa à La Mecque en 1324 redistribua tant d'or qu'il déstabilisa l'économie égyptienne.",
    "L'université de Sankoré à Tombouctou, avec 25 000 étudiants au 14e siècle, enseignait l'astronomie, les mathématiques, la médecine et le droit.",
    "Les manuscrits de Tombouctou, plus de 700 000 documents, couvrent tous les domaines du savoir et témoignent d'une tradition écrite africaine millénaire.",
    "L'empire Songhaï (1464-1591), dirigé par Askia Mohammed, étendit le contrôle sur le commerce transsaharien avec une administration centralisée.",
    "Le royaume du Kongo (1390-1914) entretenait des relations diplomatiques avec le Portugal et le Vatican dès 1482.",
    "Le Grand Zimbabwe (1100-1450), capitale d'un empire commercial minier, possède des constructions en pierre sans mortier atteignant 11 mètres de haut.",

    # Volume 5 — XVIe-XVIIIe siècles
    "Le royaume du Bénin (1180-1897) produisait des bronzes d'une maîtrise technique exceptionnelle, reconnus parmi les plus grandes œuvres d'art mondiales.",
    "L'empire Ashanti (1701-1901, Ghana actuel) possédait une organisation politique sophistiquée avec un trône d'or sacré et un système de poids en or.",
    "Le royaume du Dahomey (1600-1904, Bénin actuel) était connu pour son armée d'amazones, des guerrières d'élite entièrement féminines.",
    "La traite transatlantique a déporté 12 à 15 millions d'Africains entre 1500 et 1866. La reine Nzinga du royaume de Ndongo (Angola) mena la résistance.",
    "Les marrons, esclaves fugitifs, ont établi des communautés libres comme Palmares au Brésil (80 000 habitants, 1605-1694).",

    # Volume 6 — XIXe siècle
    "L'empire de Sokoto (1804-1903, Nigeria actuel), califat islamique réformiste fondé par Usman dan Fodio, disposait d'un système éducatif étendu.",
    "Le royaume Zoulou (1816-1897) dirigé par Chaka a révolutionné l'art militaire africain avec la formation en cornes de buffle (impondo zankomo).",
    "L'Éthiopie a vaincu l'Italie à la bataille d'Adoua en 1896, devenant le seul pays africain à résister avec succès à la colonisation européenne.",
    "Le roi Behanzin du Dahomey et Samori Touré (empire Wassoulou) ont mené des résistances majeures contre la colonisation française.",

    # Volume 7 — Afrique coloniale
    "La conférence de Berlin (1884-1885) a partagé l'Afrique entre puissances européennes sans aucune participation africaine, redessinant arbitrairement les frontières.",
    "Les mouvements panafricains de Marcus Garvey et W.E.B. Du Bois, et la négritude d'Aimé Césaire et Léopold Sédar Senghor, ont jeté les bases des indépendances.",

    # Volume 8 — Depuis 1935
    "Le Ghana fut le premier pays d'Afrique subsaharienne indépendant en 1957, dirigé par Kwame Nkrumah, figure majeure du panafricanisme.",
    "L'Organisation de l'Unité Africaine (OUA) fut fondée en 1963 à Addis-Abeba, remplacée par l'Union Africaine en 2002 avec la Zone de Libre-Échange Continentale (ZLECAf).",
    "La renaissance africaine du XXIe siècle inclut la tech (Silicon Savannah au Kenya), le cinéma (Nollywood, 2e industrie mondiale en volume) et une classe moyenne croissante.",
    "Cheikh Anta Diop (1923-1986) a démontré scientifiquement l'origine africaine de l'Égypte ancienne dans Nations nègres et culture (1954).",
]

# ═══════════════════════════════════════════════════════════════════
# CORPUS SCIENTIFIQUE
# ═══════════════════════════════════════════════════════════════════

SCIENCE_CORPUS = [
    "La gravitation universelle de Newton (1687) : F = G × m1 × m2 / r². La constante G vaut 6.674 × 10⁻¹¹ N·m²/kg².",
    "Einstein a publié la relativité restreinte en 1905 (E = mc²) et la relativité générale en 1915, décrivant la gravité comme une courbure de l'espace-temps.",
    "Le Big Bang s'est produit il y a 13.8 milliards d'années. L'univers est composé de 68% d'énergie noire, 27% de matière noire, et 5% de matière ordinaire.",
    "La mécanique quantique décrit le monde subatomique. Le principe d'incertitude de Heisenberg : Δx × Δp ≥ ℏ/2.",
    "Max Planck introduisit le quantum d'action h = 6.626 × 10⁻³⁴ J·s en 1900, fondant la physique quantique.",
    "Charles Darwin publia L'Origine des espèces en 1859, établissant l'évolution par sélection naturelle.",
    "L'ADN fut découvert par James Watson et Francis Crick en 1953, avec les travaux essentiels de Rosalind Franklin.",
    "Dmitri Mendeleïev publia le tableau périodique en 1869, organisant les 118 éléments connus par propriétés chimiques.",
    "L'eau (H₂O) est le solvant universel de la vie. Sa molécule polaire permet les liaisons hydrogène essentielles à la biochimie.",
    "La tectonique des plaques, théorisée par Alfred Wegener en 1912, explique la dérive des continents et les séismes.",
    "La photosynthèse : 6 CO₂ + 6 H₂O + lumière → C₆H₁₂O₆ + 6 O₂. Les plantes convertissent l'énergie solaire en énergie chimique.",
    "Les quatre lois de la thermodynamique : conservation de l'énergie, entropie croissante, zéro absolu inaccessible, et entropie nulle à 0K.",
    "Ludwig Boltzmann relia l'entropie S à la probabilité thermodynamique W : S = k · log(W), où k = 1.38 × 10⁻²³ J/K.",
    "La vitesse de la lumière dans le vide est exactement c = 299 792 458 m/s, constante fondamentale de la physique.",
    "Le système solaire compte 8 planètes. La Terre est la seule connue à abriter la vie, à 150 millions de km du Soleil.",
    "Le boson de Higgs, prédit en 1964, fut confirmé expérimentalement au CERN en 2012, complétant le Modèle Standard.",
    "Les ondes gravitationnelles, prédites par Einstein en 1916, furent détectées pour la première fois en 2015 par LIGO.",
    "La supraconductivité fut découverte par Heike Kamerlingh Onnes en 1911 : certains matériaux ont une résistance nulle sous une température critique.",
    "Le cycle du carbone relie l'atmosphère, les océans, la biosphère et la lithosphère, régulant le climat terrestre.",
    "L'effet de serre est causé par le CO₂, le CH₄ et la vapeur d'eau qui piègent le rayonnement infrarouge dans l'atmosphère.",
]

# ═══════════════════════════════════════════════════════════════════
# CORPUS PHILOSOPHIQUE ET SAGESSES
# ═══════════════════════════════════════════════════════════════════

PHILOSOPHY_CORPUS = [
    "La Maât égyptienne représente l'ordre cosmique, la vérité, la justice et l'équilibre. Ses 42 lois, antérieures aux 10 commandements, fondent une éthique universelle.",
    "L'Ubuntu bantou : Je suis parce que nous sommes. Cette philosophie de l'interconnexion humaine fonde la solidarité et la communauté.",
    "Le stoïcisme, fondé par Zénon de Kition vers -300, enseigne à distinguer ce qui dépend de nous de ce qui n'en dépend pas, menant à la sérénité.",
    "Socrate (-470 à -399) pratiquait la maïeutique, l'art d'accoucher les esprits par le dialogue. Il déclarait : Je sais que je ne sais rien.",
    "Platon (-427 à -347) élabora la théorie des Formes et l'allégorie de la caverne, fondement de la métaphysique occidentale.",
    "Aristote (-384 à -322) développa l'éthique de la vertu et le syllogisme, posant les bases de la logique formelle.",
    "Descartes (1596-1650) formula le Cogito ergo sum (Je pense, donc je suis) et le dualisme corps-esprit.",
    "Kant (1724-1804) proposa l'impératif catégorique : Agis selon la maxime qui peut être érigée en loi universelle.",
    "Nietzsche (1844-1900) annonça la mort de Dieu et développa les concepts de volonté de puissance et de surhomme.",
    "Sartre (1905-1980) affirma que l'existence précède l'essence et que l'homme est condamné à être libre.",
]


# ═══════════════════════════════════════════════════════════════════
# INGESTION ENGINE
# ═══════════════════════════════════════════════════════════════════

def ingest_massive():
    """Ingère toutes les sources disponibles dans l'ensemble N×64×64."""
    from holographic_ensemble import HolographicEnsemble, Hologram64, DOMAIN_DEFINITIONS, DATA_DIR

    print("=" * 70)
    print("  INGESTION MASSIVE N×64×64")
    print("=" * 70)

    # ── 1. PRESERVER les faits existants avant de reconstruire ──
    from holographic_ensemble import HolographicEnsemble, Hologram64, DOMAIN_DEFINITIONS as DD_EXISTING
    saved_facts = {}
    try:
        existing_ensemble = HolographicEnsemble()
        existing_ensemble.build_all(force_rebuild=False)
        for did, holo in existing_ensemble.holograms.items():
            if hasattr(holo, 'fact_texts') and holo.fact_texts:
                saved_facts[did] = list(holo.fact_texts)
                print(f"  [{did}] {len(saved_facts[did])} faits existants preserves")
    except Exception as e:
        print(f"  Pas d'ensemble existant: {e}")
    
    # Nettoyer les fichiers avant reconstruction
    print("Ancien ensemble nettoye.")
    for f in glob.glob(str(DATA_DIR / "*.npy")):
        try: os.remove(f)
        except: pass
    for f in glob.glob(str(DATA_DIR / "*.json")):
        try: os.remove(f)
        except: pass

    # ── 2. Préparer le vocabulaire du SpectralEncoder ──
    from spectral_encoder import SpectralEncoder

    # ── 3. Construire l'ensemble enrichi ──
    from expand_ensemble import (
        ENRICHED_GEOGRAPHY, ENRICHED_HISTORY, ENRICHED_SCIENCE,
        ENRICHED_MATHEMATICS, ENRICHED_PHILOSOPHY, ENRICHED_TECHNOLOGY,
        ENRICHED_GENERAL,
        NEW_CULTURE, NEW_ECONOMICS, NEW_HEALTH, NEW_NATURE, NEW_SPORTS
    )

    # Fusionner les corpus enrichis avec les corpus additionnels
    DOMAIN_DEFINITIONS["geography"]["facts"] = ENRICHED_GEOGRAPHY
    DOMAIN_DEFINITIONS["history"]["facts"] = ENRICHED_HISTORY + UNESCO_CORPUS[:10]
    DOMAIN_DEFINITIONS["science"]["facts"] = ENRICHED_SCIENCE + SCIENCE_CORPUS
    DOMAIN_DEFINITIONS["mathematics"]["facts"] = ENRICHED_MATHEMATICS
    DOMAIN_DEFINITIONS["philosophy"]["facts"] = ENRICHED_PHILOSOPHY + PHILOSOPHY_CORPUS
    DOMAIN_DEFINITIONS["technology"]["facts"] = ENRICHED_TECHNOLOGY
    DOMAIN_DEFINITIONS["general"]["facts"] = ENRICHED_GENERAL + UNESCO_CORPUS[10:20]

    # Ajouter les nouveaux domaines
    new_domains = {
        "culture": {"name": "Culture & Arts", "color": "#E91E63", "salt": "cult_domain_phi_1",
                     "description": "Littérature, musique, cinéma, arts", "facts": NEW_CULTURE + UNESCO_CORPUS[20:25]},
        "economics": {"name": "Économie & Finance", "color": "#FF9800", "salt": "econ_domain_phi_1",
                       "description": "PIB, commerce, finance", "facts": NEW_ECONOMICS},
        "health": {"name": "Santé & Médecine", "color": "#F44336", "salt": "hlth_domain_phi_1",
                    "description": "Anatomie, maladies, traitements", "facts": NEW_HEALTH},
        "nature": {"name": "Nature & Environnement", "color": "#8BC34A", "salt": "natr_domain_phi_1",
                    "description": "Animaux, écosystèmes, climat", "facts": NEW_NATURE},
        "sports": {"name": "Sports & Loisirs", "color": "#03A9F4", "salt": "sprt_domain_phi_1",
                    "description": "Disciplines sportives, records", "facts": NEW_SPORTS},
    }
    for did, info in new_domains.items():
        DOMAIN_DEFINITIONS[did] = info
    
    # AJOUTER les faits existants aux definitions (merge additif)
    for did, facts in saved_facts.items():
        if did in DOMAIN_DEFINITIONS and facts:
            existing_set = set(DOMAIN_DEFINITIONS[did]["facts"])
            new_count = 0
            for f in facts:
                if f not in existing_set:
                    DOMAIN_DEFINITIONS[did]["facts"].append(f)
                    existing_set.add(f)
                    new_count += 1
            if new_count > 0:
                print(f"  [{did}] {new_count} faits existants rajoutes au corpus")

    domains = list(DOMAIN_DEFINITIONS.keys())

    # ── 4. Construire les hologrammes ──
    ensemble = HolographicEnsemble(domains=domains)
    ensemble.build_all(force_rebuild=True)

    print(f"\nDomaines construits : {len(domains)}")
    total_facts = sum(len(DOMAIN_DEFINITIONS[d]["facts"]) for d in domains)
    print(f"Faits de corpus     : {total_facts}")

    # ── 5. Ingérer QuickFacts ──
    qf_result = ensemble.ingest_quickfacts()
    print(f"QuickFacts ingérés  : {qf_result.get('total', 0)}")

    # ── 6. Ingérer les fichiers texte locaux ──
    corpus_dir = os.path.join(os.path.dirname(__file__), "..", "data", "corpus")
    if os.path.isdir(corpus_dir):
        txt_files = glob.glob(os.path.join(corpus_dir, "*.txt")) + glob.glob(os.path.join(corpus_dir, "*.md"))
        print(f"\nFichiers corpus trouvés : {len(txt_files)}")
        for txt_file in txt_files:
            try:
                fname = os.path.basename(txt_file)
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content) if len(s.strip()) > 30]
                
                # Router vers le domaine correspondant
                domain = "general"
                for d in ensemble.domains:
                    if d in fname.lower():
                        domain = d
                        break
                
                target_holo = ensemble.holograms.get(domain, ensemble.holograms.get("general"))
                n_before = target_holo.n_ingested
                for sentence in sentences:  # PLUS DE LIMITE — tout ingérer
                    target_holo.ingest(sentence, amplitude=0.04)
                n_added = target_holo.n_ingested - n_before
                print(f"  {fname:25s}: {len(sentences):6d} phrases -> [{domain}] {n_added} ajoutes (total {target_holo.n_ingested})")
            except Exception as e:
                print(f"  [!] {txt_file} : {e}")

    # ── 7. Audit final ──
    ensemble.audit_all()

    # Sauvegarder
    for holo in ensemble.holograms.values():
        holo.save()

    print(f"\n{'=' * 70}")
    print("  INGESTION MASSIVE TERMINÉE")
    print(f"  Domaines : {len(domains)}")
    total = sum(h.n_ingested for h in ensemble.holograms.values())
    print(f"  Total faits ingérés : {total}")
    print(f"  Énergie totale : {sum(h.energy for h in ensemble.holograms.values()):.0f}")
    print(f"{'=' * 70}")

    return ensemble


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Ingestion massive Nx64x64")
    p.add_argument("--audit", action="store_true", help="Auditer sans ingérer")
    p.add_argument("--corpus", type=str, default=None, help="Dossier à ingérer")

    args = p.parse_args()

    if args.audit:
        from holographic_ensemble import HolographicEnsemble
        e = HolographicEnsemble()
        e.build_all(force_rebuild=False)
        e.audit_all()
    else:
        ensemble = ingest_massive()