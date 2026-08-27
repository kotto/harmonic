"""
🌊 pack_generator.py — Générateur de Packs de Connaissance
===========================================================
Génère massivement des packs de connaissance via le LLM Oracle,
les valide, les écrit dans knowledge/ au format OKF, et compile
les hologrammes.

Stratégie « chaînes TV » : l'utilisateur choisit 3-5 packs parmi
les 20 disponibles. Chaque pack = hologramme dédié (~2 Mo, ~100-300
concepts). Seuls les packs sélectionnés sont téléchargés sur le
téléphone.

Pipeline pour un pack :
  1. Charger la spécification du pack (sous-domaines, nb concepts)
  2. Pour chaque sous-domaine, appeler le LLM avec un prompt structuré
  3. Parser la réponse → extraire les triplets (sujet|relation|objet)
  4. Valider : format, contradictions, cohérence
  5. Écrire les fichiers .md dans knowledge/<domain>/
  6. Compiler l'hologramme
  7. Mesurer le taux de rappel sur des questions de test

Usage :
  python -m ka_server.services.pack_generator --list           # lister les packs
  python -m ka_server.services.pack_generator --pack medecine   # générer un pack
  python -m ka_server.services.pack_generator --all             # générer tous les packs
  python -m ka_server.services.pack_generator --pack medecine --no-llm  # régénérer sans LLM
"""

import json
import logging
import re
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ENGINE_DIR))

WIKI_DIR = _ENGINE_DIR / 'knowledge'
PACKS_DIR = _ENGINE_DIR / 'data' / 'packs'
PACKS_DIR.mkdir(parents=True, exist_ok=True)

# ── Endpoint LLM Oracle Cloud ─────────────────────────────
_PHI_API = "http://158.178.215.219:8080"


# ═══════════════════════════════════════════════════════════
# SPÉCIFICATIONS DES PACKS
# ═══════════════════════════════════════════════════════════

PACKS = {
    'physique': {
        'name': 'Physique & Sciences',
        'icon': '⚛️',
        'n_concepts': 150,
        'subdomains': [
            ('mecanique', 'Mécanique classique : forces, mouvement, lois de Newton, travail, énergie, gravitation'),
            ('thermodynamique', 'Thermodynamique : chaleur, température, entropie, gaz, changements d\'état'),
            ('electromagnetisme', 'Électromagnétisme : électricité, magnétisme, ondes, Maxwell, lumière'),
            ('optique', 'Optique : réflexion, réfraction, lentilles, lasers, fibre optique, couleur'),
            ('quantique', 'Physique quantique : atome, particules, incertitude, dualité onde-corpuscule, spin'),
            ('relativite', 'Relativité : restreinte, générale, espace-temps, trous noirs, dilatation du temps'),
            ('nucleaire', 'Physique nucléaire : fission, fusion, radioactivité, réacteurs, particules'),
            ('acoustique', 'Acoustique : son, fréquence, résonance, décibels, ultrasons, musique'),
            ('unites', 'Grandeurs et unités : mètre, kilogramme, seconde, ampère, mole, constantes fondamentales'),
        ],
    },
    'astronomie': {
        'name': 'Astronomie & Espace',
        'icon': '🪐',
        'n_concepts': 120,
        'subdomains': [
            ('systeme_solaire', 'Système solaire : planètes, soleil, lunes, astéroïdes, comètes, orbites'),
            ('etoiles', 'Étoiles : types, cycle de vie, supernova, naines, géantes, classification'),
            ('galaxies', 'Galaxies : Voie lactée, Andromède, types, amas, matière noire, cosmologie'),
            ('cosmologie', 'Cosmologie : Big Bang, expansion, univers, fond diffus, inflation'),
            ('observation', 'Observation : télescopes, sondes, satellites, ISS, Hubble, James Webb'),
            ('exoplanetes', 'Exoplanètes : découverte, types, habitabilité, zones, Trappist'),
            ('astronautique', 'Astronautique : fusées, stations, missions, Apollo, SpaceX, Artemis'),
        ],
    },
    'medecine': {
        'name': 'Médecine & Santé',
        'icon': '🏥',
        'n_concepts': 200,
        'subdomains': [
            ('cardiologie', 'Cardiologie : cœur, circulation, tension, infarctus, AVC, artères'),
            ('pneumologie', 'Pneumologie : poumons, respiration, asthme, BPCO, pneumonie, COVID'),
            ('neurologie', 'Neurologie : cerveau, neurones, AVC, Alzheimer, Parkinson, migraine'),
            ('gastroenterologie', 'Gastro-entérologie : digestion, foie, estomac, intestins, ulcères'),
            ('endocrinologie', 'Endocrinologie : hormones, thyroïde, diabète, insuline, métabolisme'),
            ('oncologie', 'Oncologie : cancers, tumeurs, chimiothérapie, radiothérapie, prévention'),
            ('infectiologie', 'Infectiologie : virus, bactéries, antibiotiques, vaccins, épidémies'),
            ('pediatrie', 'Pédiatrie : développement, vaccination, maladies infantiles, croissance'),
            ('psychiatrie', 'Psychiatrie : dépression, anxiété, bipolarité, schizophrénie, TCC'),
            ('pharmacologie', 'Pharmacologie : médicaments, principes actifs, effets secondaires, dosage'),
        ],
    },
    'biologie': {
        'name': 'Biologie & Nature',
        'icon': '🧬',
        'n_concepts': 150,
        'subdomains': [
            ('genetique', 'Génétique : ADN, gènes, chromosomes, hérédité, mutations, CRISPR'),
            ('cellulaire', 'Biologie cellulaire : cellule, organites, membrane, mitose, apoptose'),
            ('evolution', 'Évolution : Darwin, sélection naturelle, espèces, fossiles, phylogénie'),
            ('ecologie', 'Écologie : écosystèmes, biodiversité, chaîne alimentaire, climat'),
            ('botanique', 'Botanique : plantes, photosynthèse, fleurs, arbres, classification'),
            ('zoologie', 'Zoologie : mammifères, oiseaux, reptiles, insectes, comportement animal'),
            ('microbiologie', 'Microbiologie : bactéries, virus, champignons, protistes, microbiote'),
            ('anatomie', 'Anatomie : organes, systèmes, squelette, muscles, peau, sens'),
        ],
    },
    'chimie': {
        'name': 'Chimie',
        'icon': '🧪',
        'n_concepts': 120,
        'subdomains': [
            ('elements', 'Éléments : tableau périodique, atomes, isotopes, métaux, gaz rares'),
            ('liaisons', 'Liaisons chimiques : covalente, ionique, hydrogène, van der Waals, métallique'),
            ('reactions', 'Réactions : oxydoréduction, acide-base, précipitation, combustion, catalyse'),
            ('organique', 'Chimie organique : alcanes, alcools, acides, esters, polymères, pétrole'),
            ('chimie_physique', 'Chimie physique : cinétique, thermochimie, électrochimie, solutions'),
            ('biochimie', 'Biochimie : protéines, glucides, lipides, enzymes, métabolisme, vitamines'),
        ],
    },
    'histoire': {
        'name': 'Histoire & Civilisations',
        'icon': '📜',
        'n_concepts': 180,
        'subdomains': [
            ('antiquite', 'Antiquité : Égypte, Grèce, Rome, Mésopotamie, Chine, Perse, Mayas'),
            ('moyen_age', 'Moyen Âge : féodalité, croisades, royaumes, Église, chevaliers, Vikings'),
            ('renaissance', 'Renaissance : humanisme, arts, sciences, réforme, grandes découvertes'),
            ('temps_modernes', 'Temps modernes : monarchies, Lumières, révolutions, colonies, industrie'),
            ('contemporain', 'Époque contemporaine : guerres mondiales, décolonisation, guerre froide, mondialisation'),
            ('france', 'Histoire de France : rois, républiques, révolutions, guerres, personnages'),
            ('grands_personnages', 'Grands personnages : conquérants, scientifiques, artistes, penseurs'),
        ],
    },
    'informatique': {
        'name': 'Informatique & Programmation',
        'icon': '💻',
        'n_concepts': 150,
        'subdomains': [
            ('fondements', 'Fondements : algorithmes, structures de données, complexité, logique'),
            ('langages', 'Langages : Python, Java, JavaScript, C, C++, Rust, Go, TypeScript'),
            ('web', 'Web : HTML, CSS, HTTP, navigateurs, serveurs, API, frameworks'),
            ('donnees', 'Données : bases de données, SQL, NoSQL, Big Data, data mining'),
            ('ia_ml', 'IA et Machine Learning : réseaux de neurones, deep learning, NLP, vision'),
            ('reseau', 'Réseaux : TCP/IP, DNS, routage, sécurité, cloud, IoT'),
            ('systeme', 'Systèmes : OS, Linux, noyau, processus, mémoire, fichiers, threads'),
            ('genie_logiciel', 'Génie logiciel : tests, Git, CI/CD, DevOps, architecture, agile'),
        ],
    },
    'geographie': {
        'name': 'Géographie & Voyages',
        'icon': '🌍',
        'n_concepts': 150,
        'subdomains': [
            ('pays_monde', 'Pays du monde : capitales, populations, langues, monnaies, drapeaux'),
            ('reliefs', 'Reliefs : montagnes, fleuves, mers, déserts, îles, volcans, cascades'),
            ('climats', 'Climats : zones, températures, saisons, phénomènes, réchauffement'),
            ('villes', 'Grandes villes : mégalopoles, capitales culturelles, architecture, histoire'),
            ('europe', 'Europe : pays, Union européenne, institutions, culture, économie'),
            ('afrique', 'Afrique : pays, régions, ressources, défis, diversité culturelle'),
            ('asie', 'Asie : Chine, Inde, Japon, économies, cultures, religions'),
            ('ameriques', 'Amériques : États-Unis, Canada, Brésil, Amérique latine, diversité'),
        ],
    },
    'philosophie': {
        'name': 'Philosophie & Pensée',
        'icon': '🧠',
        'n_concepts': 120,
        'subdomains': [
            ('antique', 'Philosophie antique : Socrate, Platon, Aristote, stoïcisme, épicurisme'),
            ('moderne', 'Philosophie moderne : Descartes, Kant, Rousseau, Hegel, Nietzsche'),
            ('contemporaine', 'Philosophie contemporaine : Sartre, Camus, Foucault, Derrida, Arendt'),
            ('ethique', 'Éthique et morale : utilitarisme, déontologie, vertu, bioéthique, justice'),
            ('politique', 'Philosophie politique : démocratie, liberté, contrat social, État, droits'),
            ('epistemologie', 'Épistémologie : connaissance, science, vérité, paradigme, méthode'),
            ('metaphysique', 'Métaphysique : être, temps, conscience, libre arbitre, identité'),
        ],
    },
    'art': {
        'name': 'Arts & Culture',
        'icon': '🎨',
        'n_concepts': 120,
        'subdomains': [
            ('peinture', 'Peinture : mouvements, artistes, techniques, chefs-d\'œuvre, musées'),
            ('musique', 'Musique : classique, jazz, rock, compositeurs, instruments, genres'),
            ('litterature', 'Littérature : romans, poésie, auteurs, courants, prix Nobel'),
            ('cinema', 'Cinéma : réalisateurs, films, genres, festivals, Oscar, Nouvelle Vague'),
            ('architecture', 'Architecture : styles, monuments, architectes, urbanisme, patrimoine'),
            ('theatre', 'Théâtre : pièces, dramaturges, mise en scène, genres, comédie, tragédie'),
        ],
    },
    'technologie': {
        'name': 'Technologie & Innovation',
        'icon': '🔧',
        'n_concepts': 120,
        'subdomains': [
            ('inventions', 'Grandes inventions : roue, imprimerie, électricité, moteur, radio, téléphone'),
            ('robotique', 'Robotique : robots, automatisation, drones, cobots, robotique médicale'),
            ('energie', 'Énergie : solaire, éolien, nucléaire, hydraulique, fossile, transition'),
            ('transport', 'Transports : voiture, train, avion, bateau, fusée, hyperloop, Tesla'),
            ('materiaux', 'Matériaux : métaux, polymères, composites, nanomatériaux, biomatériaux'),
            ('telecom', 'Télécommunications : 5G, fibre, satellite, Bluetooth, Wi-Fi, radio'),
        ],
    },
    'mathematiques': {
        'name': 'Mathématiques',
        'icon': '📐',
        'n_concepts': 100,
        'subdomains': [
            ('algebre', 'Algèbre : équations, polynômes, matrices, vecteurs, groupes, corps'),
            ('analyse', 'Analyse : dérivées, intégrales, limites, suites, fonctions, séries'),
            ('geometrie', 'Géométrie : triangles, cercles, espaces, topologie, fractales, angles'),
            ('probabilites', 'Probabilités et statistiques : moyenne, variance, loi normale, tests'),
            ('theorie_nombres', 'Théorie des nombres : premiers, divisibilité, cryptographie, RSA'),
            ('logique', 'Logique et fondements : ensembles, axiomes, théorèmes, Gödel, calculabilité'),
        ],
    },
    'cuisine': {
        'name': 'Cuisine & Gastronomie',
        'icon': '🍳',
        'n_concepts': 100,
        'subdomains': [
            ('techniques', 'Techniques culinaires : découpes, cuissons, sauces, pâtisserie, fermentation'),
            ('ingredients', 'Ingrédients : épices, herbes, légumes, viandes, poissons, fromages'),
            ('cuisines_monde', 'Cuisines du monde : française, italienne, japonaise, indienne, mexicaine'),
            ('gastronomie', 'Gastronomie : chefs, étoiles, restaurants, vins, accords, terroir'),
            ('nutrition', 'Nutrition : vitamines, minéraux, équilibre, régimes, allergies, bienfaits'),
        ],
    },
    'sport': {
        'name': 'Sports & Loisirs',
        'icon': '⚽',
        'n_concepts': 100,
        'subdomains': [
            ('football', 'Football : clubs, compétitions, joueurs, règles, Coupe du Monde'),
            ('sports_collectifs', 'Sports collectifs : basket, rugby, volley, handball, hockey, baseball'),
            ('sports_individuels', 'Sports individuels : tennis, athlétisme, natation, cyclisme, boxe'),
            ('jeux_olympiques', 'Jeux Olympiques : histoire, disciplines, records, médailles, athlètes'),
            ('echecs', 'Échecs et jeux de réflexion : règles, stratégies, champions, ouverture'),
        ],
    },
    'economie': {
        'name': 'Économie & Finance',
        'icon': '💰',
        'n_concepts': 120,
        'subdomains': [
            ('microeconomie', 'Microéconomie : offre, demande, marché, prix, concurrence, élasticité'),
            ('macroeconomie', 'Macroéconomie : PIB, inflation, chômage, croissance, politique monétaire'),
            ('finance', 'Finance : banque, bourse, investissement, actions, obligations, risques'),
            ('cryptomonnaies', 'Cryptomonnaies : Bitcoin, blockchain, minage, wallet, DeFi, NFT'),
            ('entreprise', 'Entreprise : management, marketing, stratégie, RH, comptabilité, fiscalité'),
        ],
    },
    'religion': {
        'name': 'Religions & Spiritualités',
        'icon': '🕊️',
        'n_concepts': 100,
        'subdomains': [
            ('christianisme', 'Christianisme : Bible, Jésus, Église, sacrements, fêtes, dénominations'),
            ('islam', 'Islam : Coran, Mahomet, piliers, sunnites, chiites, soufisme, ramadan'),
            ('judaisme', 'Judaïsme : Torah, Talmud, fêtes, traditions, synagogue, diaspora'),
            ('bouddhisme', 'Bouddhisme : Bouddha, Dharma, méditation, nirvana, reincarnation'),
            ('hindouisme', 'Hindouisme : dieux, védas, karma, yoga, castes, fêtes'),
            ('mythologie', 'Mythologies : grecque, nordique, égyptienne, mythes, dieux, légendes'),
        ],
    },
    'droit': {
        'name': 'Droit & Justice',
        'icon': '⚖️',
        'n_concepts': 100,
        'subdomains': [
            ('droit_civil', 'Droit civil : contrats, responsabilité, famille, propriété, obligations'),
            ('droit_penal', 'Droit pénal : infractions, peines, procédure, crimes, délits, contraventions'),
            ('droit_travail', 'Droit du travail : contrat, salaire, licenciement, syndicats, prud\'hommes'),
            ('droit_constitutionnel', 'Droit constitutionnel : Constitution, séparation des pouvoirs, lois, droits'),
            ('droit_international', 'Droit international : traités, ONU, droits humains, CPI, diplomatie'),
        ],
    },
    'linguistique': {
        'name': 'Langues & Linguistique',
        'icon': '🗣️',
        'n_concepts': 80,
        'subdomains': [
            ('francais', 'Langue française : grammaire, conjugaison, orthographe, expressions, régions'),
            ('linguistique', 'Linguistique : phonétique, syntaxe, sémantique, morphologie, sociolinguistique'),
            ('langues_monde', 'Langues du monde : familles, groupes, langues parlées, écritures, disparition'),
            ('apprentissage', 'Apprentissage des langues : méthodes, immersion, polyglottes, outils'),
        ],
    },
    'psychologie': {
        'name': 'Psychologie & Développement',
        'icon': '🧘',
        'n_concepts': 100,
        'subdomains': [
            ('cognition', 'Psychologie cognitive : mémoire, attention, perception, apprentissage, langage'),
            ('clinique', 'Psychologie clinique : troubles, thérapies, TCC, psychanalyse, évaluation'),
            ('sociale', 'Psychologie sociale : groupes, influence, stéréotypes, conformisme, émotions'),
            ('developpement', 'Psychologie du développement : Piaget, attachement, enfance, adolescence'),
            ('neurosciences', 'Neurosciences : cerveau, plasticité, neurotransmetteurs, imagerie, conscience'),
        ],
    },
    'ecologie': {
        'name': 'Écologie & Environnement',
        'icon': '🌱',
        'n_concepts': 80,
        'subdomains': [
            ('climat', 'Climat et réchauffement : CO2, effet de serre, GIEC, COP, accords de Paris'),
            ('biodiversite', 'Biodiversité : espèces menacées, extinction, conservation, réserves naturelles'),
            ('pollution', 'Pollution : air, eau, sol, plastique, microplastiques, déchets, recyclage'),
            ('energies_renouvelables', 'Énergies renouvelables : solaire, éolien, hydraulique, géothermie, biomasse'),
            ('developpement_durable', 'Développement durable : ODD, économie circulaire, empreinte, sobriété'),
        ],
    },
}


# ═══════════════════════════════════════════════════════════
# GÉNÉRATION VIA LLM
# ═══════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Tu es un générateur de connaissances pour l'assistant personnel KA.
Ta mission : générer des concepts et leurs faits dans un domaine spécifique.

RÈGLES STRICTES :
1. Chaque concept = 3 à 5 faits au format : sujet | relation | objet
2. Les relations doivent être des verbes au présent (est une, a, cause, se trouve dans, etc.)
3. N'invente RIEN — utilise uniquement des faits largement connus et vérifiables
4. Sujet et objet doivent être des groupes nominaux précis
5. PAS de commentaires, PAS de texte avant/après
6. Les faits doivent être en français, sans accents (pour compatibilité pipeline)

FORMAT DE SORTIE EXIGÉ (exemple) :
concept: coeur
- coeur | est un | organe musculaire qui pompe le sang
- coeur | est compose de | quatre cavites
- coeur | bat environ | 100 000 fois par jour
- coeur | pompe | le sang dans tout le corps

concept: artere
- artere | est un | vaisseau sanguin qui transporte le sang du coeur
- artere | a des parois | epaisses et elastiques
- artere | se divise en | arterioles et capillaires

Génère 15 à 25 concepts par réponse. Chaque concept doit avoir 3 à 5 faits."""


def _call_llm(prompt: str, timeout: int = 120) -> Optional[str]:
    """Appelle le LLM Oracle Cloud."""
    import json as _json
    import urllib.request as _ur

    system = SYSTEM_PROMPT
    payload = _json.dumps({"question": prompt, "system": system}).encode()

    # Essayer /phi/query, puis /query
    for endpoint in ["/phi/query", "/query"]:
        url = _PHI_API + endpoint
        try:
            req = _ur.Request(url, data=payload,
                             headers={"Content-Type": "application/json"})
            with _ur.urlopen(req, timeout=timeout) as resp:
                data = _json.loads(resp.read().decode())
                answer = data.get("answer", "")
                if answer and len(answer) > 50:
                    return answer
        except Exception as e:
            log.debug(f"LLM {endpoint} failed: {e}")
            continue
    return None


def build_prompt(subdomain_id: str, subdomain_desc: str) -> str:
    """Construit le prompt pour un sous-domaine."""
    return f"""Génère des concepts et leurs faits sur le thème suivant :

THÈME : {subdomain_desc}

Génère 15 à 25 concepts (idéalement 20), chacun avec 3 à 5 faits.
Couvre les aspects les plus importants du thème.

Format EXIGÉ :
concept: nom_du_concept
- sujet | relation | objet
- sujet | relation | objet
...

concept: nom_suivant
- ..."""


# ═══════════════════════════════════════════════════════════
# PARSEUR DE RÉPONSE LLM
# ═══════════════════════════════════════════════════════════

def parse_llm_response(response: str) -> List[Dict]:
    """
    Parse la réponse du LLM en liste de concepts.
    Chaque concept : {id, title, domain, facts: [(s,r,o)]}
    """
    concepts = []
    current_concept = None

    for line in response.splitlines():
        line = line.strip()
        if not line:
            continue

        # Ligne "concept: nom"
        m = re.match(r'^concept\s*:\s*(.+)$', line, re.IGNORECASE)
        if m:
            if current_concept:
                concepts.append(current_concept)
            cid = m.group(1).strip().lower()
            cid = re.sub(r'[^a-z0-9_àâäéèêëîïôöùûüçœ]', '_', cid)
            cid = re.sub(r'_+', '_', cid).strip('_')
            current_concept = {
                'id': cid,
                'title': m.group(1).strip().capitalize(),
                'facts': [],
            }
            continue

        # Ligne "- sujet | relation | objet"
        line_clean = line.lstrip('-*•').strip()
        if '|' in line_clean and current_concept:
            parts = [p.strip() for p in line_clean.split('|')]
            if len(parts) >= 3 and parts[0] and parts[1] and parts[2]:
                # Nettoyer : enlever les accents, les guillemets
                s = _clean_text(parts[0])
                r = _clean_text(parts[1])
                o = _clean_text(parts[2])
                if s and r and o:
                    current_concept['facts'].append((s, r, o))

    # Dernier concept
    if current_concept:
        concepts.append(current_concept)

    return concepts


def _clean_text(text: str) -> str:
    """Nettoie un texte pour le format OKF : sans accents, sans guillemets."""
    t = text.strip().strip('"\'«»""')
    # Enlever les accents
    t = unicodedata.normalize('NFD', t)
    t = t.encode('ascii', 'ignore').decode('ascii')
    # Normaliser les espaces
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


# ═══════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════

def validate_concepts(concepts: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """
    Valide les concepts générés. Retourne (concepts_valides, erreurs).
    """
    valid = []
    errors = []
    seen_facts = set()

    for c in concepts:
        # Vérifier l'ID
        if not c['id'] or len(c['id']) < 2:
            errors.append(f"Concept sans ID valide: {c['title'][:30]}")
            continue

        # Vérifier les faits
        if len(c['facts']) < 2:
            errors.append(f"'{c['id']}': trop peu de faits ({len(c['facts'])})")
            continue

        # Vérifier les doublons
        clean_facts = []
        for s, r, o in c['facts']:
            key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
            if key in seen_facts:
                continue
            seen_facts.add(key)
            # Vérifier que les champs ne sont pas vides
            if len(s) < 2 or len(r) < 2 or len(o) < 2:
                continue
            clean_facts.append((s, r, o))

        if len(clean_facts) < 2:
            errors.append(f"'{c['id']}': {len(clean_facts)} faits valides après déduplication")
            continue

        c['facts'] = clean_facts
        valid.append(c)

    return valid, errors


# ═══════════════════════════════════════════════════════════
# ÉCRITURE + COMPILATION
# ═══════════════════════════════════════════════════════════

def write_concepts(domain: str, concepts: List[Dict]) -> int:
    """Écrit les concepts dans des fichiers .md dans knowledge/<domain>/."""
    domain_dir = WIKI_DIR / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    n_written = 0

    for c in concepts:
        facts_lines = [f"- {s} | {r} | {o}" for s, r, o in c['facts']]
        md_content = f"""---
id: {c['id']}
domain: {domain}
title: {c['title']}
type: concept
---

# {c['title']}

{chr(10).join(facts_lines)}
"""
        filepath = domain_dir / f"{c['id']}.md"
        filepath.write_text(md_content, encoding='utf-8')
        n_written += 1

    return n_written


def compile_domain(domain: str) -> dict:
    """Compile un domaine en hologramme."""
    from ka_server.services.okf_compiler import compile_wiki
    report = compile_wiki(action=f'pack|{domain}')
    # Trouver les stats du domaine
    for d, r in report['results'].items():
        if d == domain:
            return r
    return {}


# ═══════════════════════════════════════════════════════════
# GÉNÉRATION D'UN PACK
# ═══════════════════════════════════════════════════════════

def generate_pack(pack_id: str, use_llm: bool = True, force: bool = False) -> dict:
    """
    Génère un pack complet : LLM → validation → .md → compilation.

    Args:
        pack_id: identifiant du pack (clé dans PACKS)
        use_llm: True = appelle le LLM, False = compile seulement
        force: True = régénère même si existe

    Returns:
        dict avec les résultats
    """
    if pack_id not in PACKS:
        return {'success': False, 'error': f"Pack '{pack_id}' inconnu"}

    pack = PACKS[pack_id]
    log.info(f"📦 Génération du pack: {pack['icon']} {pack['name']}")

    # Vérifier si le pack existe déjà
    if not force:
        existing_md = list((WIKI_DIR / pack_id).glob('*.md')) if (WIKI_DIR / pack_id).exists() else []
        if existing_md and not use_llm:
            log.info(f"   ⏭️  {len(existing_md)} fichiers existent, recompile seulement")
            report = compile_domain(pack_id)
            return {'success': True, 'pack_id': pack_id, 'generated': 0, 'compiled': report}

    all_concepts = []
    all_errors = []
    total_llm_time = 0

    # Pour chaque sous-domaine
    for sub_id, sub_desc in pack['subdomains']:
        if not use_llm:
            log.info(f"   ⏭️  {sub_id}: skipping LLM")
            continue

        log.info(f"   ☁️  LLM: {sub_id}...")
        prompt = build_prompt(sub_id, sub_desc)
        t0 = time.time()

        # Le LLM peut générer 15-25 concepts par appel, on fait 1-2 appels
        response = _call_llm(prompt)
        dt = time.time() - t0
        total_llm_time += dt

        if not response:
            log.warning(f"   ⚠️  LLM n'a pas répondu pour {sub_id}")
            all_errors.append(f"{sub_id}: LLM indisponible")
            continue

        # Parser
        concepts = parse_llm_response(response)
        valid, errors = validate_concepts(concepts)

        all_errors.extend(errors)
        all_concepts.extend(valid)

        log.info(f"   ✅ {sub_id}: {len(concepts)} concepts extraits, "
                 f"{len(valid)} valides, en {dt:.0f}s")

    # Écrire les fichiers .md
    if all_concepts:
        log.info(f"   📝 Écriture de {len(all_concepts)} concepts dans knowledge/{pack_id}/...")
        n_written = write_concepts(pack_id, all_concepts)
        log.info(f"   ✅ {n_written} fichiers écrits")
    else:
        log.warning(f"   ⚠️  Aucun concept généré pour {pack_id}")

    # Compiler
    log.info(f"   🔄 Compilation...")
    report = compile_domain(pack_id)

    # Sauvegarder les métadonnées du pack
    meta = {
        'pack_id': pack_id,
        'name': pack['name'],
        'icon': pack['icon'],
        'generated_at': time.time(),
        'n_concepts': len(all_concepts),
        'n_errors': len(all_errors),
        'llm_time_s': round(total_llm_time, 1),
        'errors': all_errors[:20],
        'compiled': report.get('facts', 0) if report else 0,
    }
    meta_path = PACKS_DIR / f'{pack_id}.json'
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    return {
        'success': True,
        'pack_id': pack_id,
        'generated': len(all_concepts),
        'errors': len(all_errors),
        'llm_time_s': round(total_llm_time, 1),
        'compiled': report,
    }


# ═══════════════════════════════════════════════════════════
# MESURE DE QUALITÉ
# ═══════════════════════════════════════════════════════════

def test_recall(pack_id: str, n_test: int = 10) -> dict:
    """
    Teste le rappel holographique sur un pack.
    Retourne le taux de réussite.
    """
    from hologram_store import HologramStore
    store = HologramStore()
    holo_id = f'okf_{pack_id}'

    # Prendre les n premiers concepts du pack et les utiliser comme questions
    domain_dir = WIKI_DIR / pack_id
    if not domain_dir.exists():
        return {'success': False, 'error': f"Domaine {pack_id} introuvable"}

    concepts = []
    for f in sorted(domain_dir.glob('*.md'))[:n_test]:
        text = f.read_text(encoding='utf-8')
        title_match = re.search(r'^title:\s*(.+)$', text, re.MULTILINE)
        if title_match:
            concepts.append(title_match.group(1).strip().strip('"\''))

    if not concepts:
        return {'success': False, 'error': 'Aucun concept trouvé'}

    correct = 0
    total = min(len(concepts), n_test)

    for concept in concepts[:n_test]:
        # Construire une question simple
        q = f"c'est quoi {concept.lower()[:40]}"
        r = store.recall(holo_id, q, top_k=1)
        if r and r[0][4] > 0.5:
            correct += 1

    return {
        'success': True,
        'pack_id': pack_id,
        'tested': total,
        'correct': correct,
        'score': round(100 * correct / max(total, 1), 1),
    }


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def cmd_list():
    """Liste tous les packs disponibles avec leur statut."""
    print(f"\n📦 PACKS DE CONNAISSANCE DISPONIBLES ({len(PACKS)} packs)\n")

    for pid, pack in sorted(PACKS.items()):
        meta_path = PACKS_DIR / f'{pid}.json'
        if meta_path.exists():
            meta = json.load(open(meta_path, encoding='utf-8'))
            status = f"✅ {meta.get('n_concepts', 0)} concepts"
            if meta.get('compiled', 0):
                status += f", {meta['compiled']} faits compilés"
        else:
            status = "⬜ Non généré"

        print(f"  {pack['icon']} {pid:20s} {pack['name']:30s} {status}")


def cmd_generate(pack_id: str, use_llm: bool = True, force: bool = False):
    """Génère un pack et affiche le résultat."""
    print(f"\n📦 Génération du pack « {pack_id} »...\n")
    result = generate_pack(pack_id, use_llm=use_llm, force=force)

    if result.get('success'):
        print(f"  ✅ Concepts générés : {result.get('generated', 0)}")
        print(f"  ⚠️  Erreurs : {result.get('errors', 0)}")
        print(f"  ☁️  Temps LLM : {result.get('llm_time_s', 0):.0f}s")
        compiled = result.get('compiled', {})
        if compiled:
            print(f"  🔄 Faits compilés : {compiled.get('facts', 0)}")

        # Test de rappel
        print(f"\n  🔮 Test de rappel...")
        recall = test_recall(pack_id)
        if recall.get('success'):
            print(f"  ✅ Rappel : {recall['correct']}/{recall['tested']} ({recall['score']}%)")
        else:
            print(f"  ⚠️  Test non disponible : {recall.get('error', '')}")

        print(f"\n  ✅ Pack terminé.")
    else:
        print(f"  ❌ Échec : {result.get('error', 'inconnu')}")


def cmd_generate_all(use_llm: bool = True):
    """Génère tous les packs non encore générés."""
    results = {}
    for pid in sorted(PACKS.keys()):
        meta_path = PACKS_DIR / f'{pid}.json'
        if meta_path.exists() and not use_llm:
            print(f"\n⏭️  {pid}: déjà généré. Passe.")
            continue

        print(f"\n{'=' * 60}")
        print(f"📦 {PACKS[pid]['icon']} {PACKS[pid]['name']} ({pid})")
        print(f"{'=' * 60}")

        result = generate_pack(pid, use_llm=use_llm)
        results[pid] = result

        # Pause entre les packs (éviter de saturer le LLM)
        if use_llm:
            print(f"   💤 Pause 2s...")
            time.sleep(2)

    # Résumé
    print(f"\n\n{'=' * 60}")
    print(f"📊 RÉSUMÉ DE LA GÉNÉRATION")
    print(f"{'=' * 60}")
    total_concepts = 0
    total_errors = 0
    total_llm = 0
    for pid, r in results.items():
        if r.get('success'):
            n = r.get('generated', 0)
            e = r.get('errors', 0)
            llm = r.get('llm_time_s', 0)
            total_concepts += n
            total_errors += e
            total_llm += llm
            icon = PACKS.get(pid, {}).get('icon', '')
            print(f"  {icon} {pid:20s} {n:>4d} concepts, {e} erreurs, {llm:.0f}s LLM")
        else:
            print(f"  ❌ {pid:20s} {r.get('error', '?')}")

    print(f"  {'─' * 50}")
    print(f"  TOTAL{'':18s} {total_concepts:>4d} concepts, {total_errors} erreurs, {total_llm:.0f}s LLM")


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    if '--list' in sys.argv:
        cmd_list()
        return

    if '--pack' in sys.argv:
        idx = sys.argv.index('--pack')
        pack_id = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ''
        use_llm = '--no-llm' not in sys.argv
        force = '--force' in sys.argv
        if pack_id:
            cmd_generate(pack_id, use_llm=use_llm, force=force)
        else:
            print("Usage: --pack <pack_id> [--no-llm] [--force]")
        return

    if '--all' in sys.argv:
        use_llm = '--no-llm' not in sys.argv
        cmd_generate_all(use_llm=use_llm)
        return

    # Aide
    print("""🌊 PACK GENERATOR — Génération massive de packs de connaissance

Commandes :
  --list                        Lister les packs disponibles
  --pack <id>                   Générer un pack spécifique
  --all                         Générer tous les packs
  --all --no-llm                Recompiler sans appeler le LLM
  --pack <id> --no-llm          Recompiler un pack existant

Exemples :
  python -m ka_server.services.pack_generator --list
  python -m ka_server.services.pack_generator --pack medecine
  python -m ka_server.services.pack_generator --all
""")


if __name__ == '__main__':
    main()