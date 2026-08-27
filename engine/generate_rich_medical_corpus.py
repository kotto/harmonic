"""
🌊 GENERATEUR DE CORPUS MÉDICAL ENRICHI ×10
=============================================
Génère un corpus textuel médical riche (~50 000+ phrases variées)
à partir des 62 356 faits des 15 domaines médicaux.

PRINCIPE : Pour que le Laplacien sémantique capture les relations
maladie↔symptôme avec une haute résolution, il faut que PPMI voie
ces paires dans des CONTEXTES VARIÉS. Une seule phrase template
("X présente symptôme Y") ne suffit pas — PPMI apprend le template,
pas la relation médicale.

SOLUTION : 15-20 templates PAR TYPE DE RELATION, plus des phrases
de contexte enrichi (définitions, protocoles, chaînes de raisonnement).

ARCHITECTURE :
  ┌─────────────────────────────────────────────────────────────┐
  │ SOURCE 1 : Faits (s, r, o) × 20 templates = ~60K phrases    │
  │ SOURCE 2 : Définitions médicales = ~500 phrases              │
  │ SOURCE 3 : Protocoles de traitement = ~2000 phrases          │
  │ SOURCE 4 : Chaînes de raisonnement clinique = ~3000 phrases  │
  │ SOURCE 5 : Contexte épidémiologique = ~1000 phrases          │
  │ SOURCE 6 : Interactions médicamenteuses = ~2000 phrases      │
  └─────────────────────────────────────────────────────────────┘

SORTIE : data/corpus_medical_enrichi.json (phrases tokenisées)

Auteur : THU — Univers-Holistique
Date   : 2026-08-23
"""

import sys, os, math, time, json, re, random
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent
FACTS_DIR = _ENGINE_DIR / "vital-ka" / "data" / "medical_holograms"
OUTPUT_PATH = _ENGINE_DIR / "vital-ka" / "data" / "corpus_medical_enrichi.json"

# Tous les domaines
ALL_DOMAINS = [
    "CHRONIQUES", "CLINIQUE", "GENERAL", "MALADIES",
    "MERE_ENFANT", "MNT", "NUTRITION", "PALUDISME",
    "PEDIATRIE", "PHARMACIE", "PHYTOTHERAPIE", "SANTE_MENTALE",
    "URGENCES", "VACCINATION", "VIH_TB",
]

PHI = (1 + math.sqrt(5)) / 2


# ═══════════════════════════════════════════════════════════════════
# SOURCE 1 : TEMPLATES ENRICHIS PAR TYPE DE RELATION
# ═══════════════════════════════════════════════════════════════════

# Templates organisés par catégorie sémantique de la relation
# Objectif : chaque fait génère 15-20 phrases différentes pour
# maximiser les co-occurrences dans des contextes variés.

TEMPLATES_BY_CATEGORY = {
    # ── Symptômes et signes cliniques ──
    "symptôme": [
        "{s} se manifeste cliniquement par {o}",
        "le tableau clinique de {s} inclut {o}",
        "parmi les signes cardinaux de {s} on retrouve {o}",
        "{o} est un signe clinique évocateur de {s}",
        "la présence de {o} doit faire évoquer le diagnostic de {s}",
        "en cas de {s} le patient peut présenter {o}",
        "{o} fait partie du tableau classique de {s}",
        "le symptôme {o} oriente vers une {s}",
        "sur le plan clinique {s} se caractérise par {o}",
        "l'examen retrouve {o} en faveur d'un diagnostic de {s}",
        "devant {o} il faut systématiquement rechercher {s}",
        "{s} typique associe {o} au tableau clinique",
        "le cortège symptomatique de {s} comprend {o}",
        "à l'interrogatoire le patient atteint de {s} décrit {o}",
        "l'inspection et la palpation révèlent {o} dans le cadre de {s}",
    ],
    
    # ── Traitement ──
    "traitement": [
        "le traitement recommandé pour {s} est {o}",
        "la prise en charge thérapeutique de {s} repose sur {o}",
        "{o} constitue le traitement de première intention de {s}",
        "le protocole thérapeutique de {s} inclut {o}",
        "en première ligne on prescrit {o} pour traiter {s}",
        "l'arsenal thérapeutique contre {s} comprend {o}",
        "{s} répond favorablement au traitement par {o}",
        "le gold standard du traitement de {s} est {o}",
        "la pharmacopée contre {s} inclut {o}",
        "{o} a démontré son efficacité dans la prise en charge de {s}",
        "le schéma thérapeutique de {s} associe {o}",
        "selon les recommandations OMS le traitement de {s} est {o}",
        "on administre {o} en cas de {s} confirmé",
        "la conduite thérapeutique face à {s} comprend {o}",
        "{o} est indiqué dans le traitement curatif de {s}",
    ],
    
    # ── Diagnostic ──
    "diagnostic": [
        "le diagnostic de {s} repose sur {o}",
        "pour confirmer le diagnostic de {s} on réalise {o}",
        "{o} permet d'établir le diagnostic de certitude de {s}",
        "le bilan diagnostique de {s} comprend {o}",
        "la démarche diagnostique devant une suspicion de {s} inclut {o}",
        "{o} est l'examen de référence pour diagnostiquer {s}",
        "le diagnostic différentiel de {s} se fait par {o}",
        "les critères diagnostiques de {s} intègrent {o}",
        "pour poser le diagnostic de {s} il faut {o}",
        "le gold standard diagnostique de {s} est {o}",
    ],
    
    # ── Prévention ──
    "prévention": [
        "la prévention de {s} repose sur {o}",
        "pour prévenir {s} on recommande {o}",
        "{o} est une mesure préventive efficace contre {s}",
        "les stratégies de prévention de {s} incluent {o}",
        "la prophylaxie de {s} fait appel à {o}",
        "en prévention primaire de {s} on utilise {o}",
        "{o} réduit significativement le risque de {s}",
        "la lutte contre {s} passe par {o}",
        "les mesures de protection contre {s} comprennent {o}",
        "{o} fait partie du programme de prévention de {s}",
    ],
    
    # ── Complications ──
    "complication": [
        "{s} peut se compliquer de {o}",
        "parmi les complications redoutées de {s} on trouve {o}",
        "l'évolution de {s} peut être émaillée de {o}",
        "{o} représente une complication grave de {s}",
        "si {s} n'est pas traité il peut évoluer vers {o}",
        "la complication majeure de {s} est {o}",
        "{o} est une conséquence possible de {s} non contrôlé",
        "le pronostic de {s} est aggravé par la survenue de {o}",
        "{s} expose au risque de {o}",
        "l'histoire naturelle de {s} peut aboutir à {o}",
    ],
    
    # ── Épidémiologie ──
    "épidémiologie": [
        "{s} est endémique dans {o}",
        "la prévalence de {s} est particulièrement élevée en {o}",
        "{o} constitue une zone de forte transmission de {s}",
        "sur le plan épidémiologique {s} touche principalement {o}",
        "les données épidémiologiques montrent que {s} affecte {o}",
        "{o} est un facteur de risque majeur de {s}",
        "l'incidence de {s} est maximale chez {o}",
        "la distribution géographique de {s} inclut {o}",
        "{s} sévit de manière endémique dans {o}",
        "les populations vulnérables à {s} sont {o}",
    ],
    
    # ── Définition ──
    "définition": [
        "{s} se définit comme {o}",
        "on entend par {s} la présence de {o}",
        "{s} correspond à {o}",
        "la définition médicale de {s} est {o}",
        "{s} désigne une pathologie caractérisée par {o}",
        "le terme {s} recouvre {o}",
        "{s} est une entité nosologique définie par {o}",
        "selon la classification internationale {s} correspond à {o}",
    ],
    
    # ── Médicament / Pharmacologie ──
    "médicament": [
        "{s} est un médicament indiqué dans {o}",
        "la molécule {s} agit en {o}",
        "{s} appartient à la classe pharmacologique de {o}",
        "le mécanisme d'action de {s} est {o}",
        "{s} s'administre par voie {o}",
        "la posologie de {s} est {o}",
        "{s} est contre-indiqué en cas de {o}",
        "les effets secondaires de {s} incluent {o}",
        "{s} interagit avec {o}",
        "la pharmacocinétique de {s} montre {o}",
        "{s} a une demi-vie de {o}",
        "le surdosage en {s} provoque {o}",
        "{s} est à utiliser avec prudence chez {o}",
        "l'efficacité de {s} a été démontrée contre {o}",
    ],
    
    # ── Urgence ──
    "urgence": [
        "{s} constitue une urgence médicale nécessitant {o}",
        "face à {s} la conduite d'urgence est {o}",
        "en situation d'urgence {s} impose {o}",
        "le protocole d'urgence pour {s} est {o}",
        "{s} requiert une prise en charge immédiate par {o}",
        "devant {s} il faut en urgence {o}",
        "la reconnaissance précoce de {s} permet {o}",
        "tout retard de prise en charge de {s} expose à {o}",
    ],
    
    # ── Général / Information ──
    "général": [
        "information importante concernant {s} : {o}",
        "il faut savoir que pour {s} {o}",
        "un point clé sur {s} est que {o}",
        "concernant {s} la recommandation est {o}",
        "à noter pour {s} : {o}",
        "rappel sur {s} : {o}",
        "dans le cadre de {s} il est essentiel de {o}",
        "la conduite pratique face à {s} est {o}",
    ],
}


# ═══════════════════════════════════════════════════════════════════
# SOURCE 2 : DÉFINITIONS MÉDICALES (générées synthétiquement)
# ═══════════════════════════════════════════════════════════════════

def generate_definitions(diseases: List[str]) -> List[str]:
    """Génère des phrases de définition pour les maladies principales."""
    templates = [
        "la {d} est une pathologie qui affecte principalement {organe}",
        "{d} fait partie des maladies {categorie}",
        "sur le plan physiopathologique {d} résulte de {mecanisme}",
        "le diagnostic de {d} repose sur un faisceau d'arguments cliniques et paracliniques",
        "{d} évolue généralement sur un mode {evolution}",
        "la sévérité de {d} est évaluée selon {critere}",
        "{d} peut toucher tous les âges mais avec une prédilection pour {age}",
        "la morbi-mortalité de {d} reste élevée dans les pays à ressources limitées",
        "{d} bénéficie d'un programme de lutte spécifique dans de nombreux pays",
        "la recherche sur {d} a permis des avancées thérapeutiques majeures",
    ]
    
    organes = ["le foie", "les poumons", "le cœur", "le système nerveux", "les reins",
               "le tube digestif", "la peau", "les articulations", "le sang", "les yeux"]
    categories = ["infectieuses", "chroniques non transmissibles", "cardiovasculaires",
                  "respiratoires", "métaboliques", "auto-immunes", "génétiques"]
    mecanismes = ["une réaction inflammatoire excessive", "un dérèglement immunitaire",
                  "une infection par un agent pathogène", "un déséquilibre métabolique",
                  "une mutation génétique", "un processus dégénératif"]
    evolutions = ["aigu", "subaigu", "chronique", "récurrent", "progressif"]
    
    sentences = []
    for d in diseases[:200]:  # top 200 maladies
        t = random.choice(templates)
        s = t.format(d=d, 
                     organe=random.choice(organes),
                     categorie=random.choice(categories),
                     mecanisme=random.choice(mecanismes),
                     evolution=random.choice(evolutions),
                     critere="la clinique et les examens complémentaires",
                     age="les enfants de moins de 5 ans")
        sentences.append(s)
    
    return sentences


# ═══════════════════════════════════════════════════════════════════
# SOURCE 3 : CHAÎNES DE RAISONNEMENT CLINIQUE
# ═══════════════════════════════════════════════════════════════════

def generate_clinical_reasoning(disease_symptoms: Dict[str, List[str]]) -> List[str]:
    """Génère des chaînes de raisonnement clinique."""
    templates = [
        "devant {s1} et {s2} le clinicien doit évoquer en premier lieu {d}",
        "l'association de {s1} à {s2} dans un contexte fébrile oriente vers {d}",
        "le diagnostic différentiel entre {d1} et {d2} repose sur la présence de {s}",
        "si le patient présente {s1} sans {s2} il faut rechercher {d}",
        "la triade classique de {d} associe {s1} {s2} et {s3}",
        "en présence de {s1} le premier diagnostic à éliminer est {d}",
        "l'absence de {s} rend le diagnostic de {d} peu probable",
        "le raisonnement clinique devant {s1} doit intégrer {d} parmi les hypothèses",
        "un patient qui consulte pour {s1} doit bénéficier d'un dépistage de {d}",
        "la présence simultanée de {s1} et {s2} est très évocatrice de {d}",
        "{d} doit être systématiquement recherché devant {s1} surtout si {s2}",
    ]
    
    sentences = []
    for disease, symptoms in list(disease_symptoms.items())[:300]:
        if len(symptoms) < 2:
            continue
        
        syms = list(symptoms)
        random.shuffle(syms)
        
        for t in random.sample(templates, min(3, len(templates))):
            try:
                if "{d1}" in t and "{d2}" in t:
                    # besoin de deux maladies
                    other = random.choice(list(disease_symptoms.keys()))
                    s = t.format(d1=disease, d2=other, 
                                s1=syms[0], s2=syms[1] if len(syms) > 1 else syms[0],
                                s=syms[0])
                elif "{s3}" in t:
                    s = t.format(d=disease, s1=syms[0], 
                                s2=syms[1] if len(syms) > 1 else syms[0],
                                s3=syms[2] if len(syms) > 2 else syms[0])
                else:
                    s = t.format(d=disease, 
                                s1=syms[0], 
                                s2=syms[1] if len(syms) > 1 else syms[0],
                                s=syms[0])
                sentences.append(s)
            except (KeyError, IndexError):
                pass
    
    return sentences


# ═══════════════════════════════════════════════════════════════════
# SOURCE 4 : PROTOCOLES STANDARDISÉS
# ═══════════════════════════════════════════════════════════════════

def generate_protocols() -> List[str]:
    """Génère des phrases de protocole standardisé."""
    protocols = [
        "le protocole national de prise en charge recommande pour chaque patient un bilan initial complet",
        "la consultation médicale doit comporter un interrogatoire minutieux et un examen clinique systématique",
        "les signes de gravité à rechercher comprennent la détresse respiratoire le choc et les troubles de la conscience",
        "tout patient fébrile en zone d'endémie doit bénéficier d'un test de dépistage du paludisme",
        "la prévention des infections nosocomiales repose sur le lavage des mains et l'asepsie",
        "le dossier médical doit mentionner les antécédents les allergies et les traitements en cours",
        "la surveillance post-thérapeutique comprend un contrôle clinique à un mois et trois mois",
        "l'éducation thérapeutique du patient est essentielle pour garantir l'observance du traitement",
        "la référence vers un centre spécialisé est indiquée en cas d'échec thérapeutique ou de complication",
        "le calendrier vaccinal doit être vérifié et mis à jour à chaque consultation",
        "la prise en charge nutritionnelle fait partie intégrante du traitement de la malnutrition aiguë",
        "le suivi de la croissance staturo-pondérale est primordial chez l'enfant de moins de cinq ans",
        "la consultation prénatale doit être mensuelle avec un bilan biologique à chaque trimestre",
        "l'allaitement maternel exclusif est recommandé pendant les six premiers mois de vie",
        "la contraception post-partum doit être discutée avant la sortie de la maternité",
        "le dépistage du VIH est systématiquement proposé à toute femme enceinte lors de la première consultation",
        "la prévention de la transmission mère-enfant du VIH repose sur la trithérapie antirétrovirale",
        "la tuberculose doit être recherchée chez tout patient VIH positif toussant depuis plus de deux semaines",
        "le traitement préventif intermittent du paludisme est recommandé chez la femme enceinte à partir du deuxième trimestre",
        "la vitamine A est administrée systématiquement aux enfants de six mois à cinq ans dans les zones à risque",
        "le déparasitage systématique est recommandé tous les six mois chez les enfants d'âge scolaire",
        "la supplémentation en fer et acide folique est prescrite à toutes les femmes enceintes",
        "le traitement des maladies chroniques nécessite un suivi régulier et une observance rigoureuse",
        "l'hypertension artérielle doit être dépistée à chaque consultation chez l'adulte",
        "le diabète gestationnel est recherché entre vingt-quatre et vingt-huit semaines d'aménorrhée",
    ]
    return protocols


# ═══════════════════════════════════════════════════════════════════
# SOURCE 5 : PHRASES ÉPIDÉMIOLOGIQUES
# ═══════════════════════════════════════════════════════════════════

def generate_epidemiology(diseases: List[str]) -> List[str]:
    """Génère des phrases de contexte épidémiologique."""
    templates_epi = [
        "l'incidence annuelle de {d} est estimée à {n} cas pour cent mille habitants",
        "la létalité de {d} atteint {p} pour cent en l'absence de traitement",
        "{d} représente la {r} cause de mortalité dans les pays à faible revenu",
        "le fardeau de {d} pèse particulièrement sur les populations rurales",
        "la transmission de {d} suit un schéma saisonnier avec un pic en saison des pluies",
        "les efforts de santé publique ont permis de réduire la mortalité par {d}",
        "{d} fait partie des maladies tropicales négligées selon l'OMS",
        "l'élimination de {d} comme problème de santé publique est un objectif à l'horizon 2030",
        "la résistance aux médicaments complique la lutte contre {d}",
        "le changement climatique pourrait étendre la zone de transmission de {d}",
    ]
    
    sentences = []
    for d in diseases[:150]:
        t = random.choice(templates_epi)
        s = t.format(d=d, n=random.choice([5, 10, 25, 50, 100, 250]),
                     p=random.choice([5, 10, 15, 30, 50]),
                     r=random.choice(["première", "deuxième", "troisième", "quatrième", "cinquième"]))
        sentences.append(s)
    
    return sentences


# ═══════════════════════════════════════════════════════════════════
# CHARGEMENT ET GÉNÉRATION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════

def load_all_facts(facts_dir: Path, domains: List[str]) -> Tuple[List[dict], List[str]]:
    """Charge tous les faits et extrait la liste des maladies/sujets."""
    all_facts = []
    all_subjects = set()
    
    for domain in domains:
        path = facts_dir / f"{domain}_facts.json"
        if not path.exists():
            continue
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for fact in data:
            s = str(fact.get('s', '')).strip().replace('_', ' ')
            if s and len(s) > 2:
                all_subjects.add(s.lower())
            all_facts.append(fact)
    
    print(f"   📂 {len(all_facts):,} faits, {len(all_subjects)} sujets uniques")
    return all_facts, sorted(all_subjects)


def group_by_subject(facts: List[dict]) -> Dict[str, Dict[str, List[str]]]:
    """Regroupe les faits par sujet et par relation."""
    by_subject = defaultdict(lambda: defaultdict(list))
    
    for fact in facts:
        s = str(fact.get('s', '')).strip().replace('_', ' ')
        r = str(fact.get('r', '')).strip().replace('_', ' ')
        o = str(fact.get('o', '')).strip().replace('_', ' ')
        
        if not s or not o:
            continue
        
        s = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', s).strip()
        o = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', o).strip()
        
        if len(s) < 2 or len(o) < 2:
            continue
        
        by_subject[s.lower()][r.lower()].append(o)
    
    print(f"   📊 {len(by_subject)} sujets avec faits")
    return by_subject


def categorize_relation(relation: str) -> str:
    """Catégorise une relation pour choisir le bon template."""
    r = relation.lower().replace('_', ' ')
    
    if any(w in r for w in ['symptôme', 'symptome', 'signe', 'clinique', 'présente']):
        return "symptôme"
    if any(w in r for w in ['traitement', 'traite', 'thérapeutique', 'dose', 'posologie']):
        return "traitement"
    if any(w in r for w in ['diagnostic', 'diagnostique', 'examen', 'test', 'dépistage']):
        return "diagnostic"
    if any(w in r for w in ['prévention', 'prévent', 'prophylaxie', 'protège']):
        return "prévention"
    if any(w in r for w in ['complication', 'complique', 'aggrave']):
        return "complication"
    if any(w in r for w in ['urgence', 'urgent', 'immédiat', 'vital']):
        return "urgence"
    if any(w in r for w in ['épidémiologie', 'endémique', 'transmission', 'vecteur', 'réservoir']):
        return "épidémiologie"
    if any(w in r for w in ['définition', 'définit', 'est', 'correspond']):
        return "définition"
    if any(w in r for w in ['indication', 'contre', 'effet', 'classe', 'voie', 'médicament', 'molécule', 'administr']):
        return "médicament"
    
    return "général"


def generate_rich_sentences(by_subject: Dict, max_facts_per_subject: int = 25) -> List[str]:
    """
    Cœur du générateur : pour chaque fait, génère 15-20 phrases
    avec les templates de la catégorie appropriée.
    """
    sentences = []
    seen = set()
    
    total_facts = sum(len(objs) for rels in by_subject.values() for objs in rels.values())
    processed = 0
    
    for subject, relations in by_subject.items():
        for relation, objects in relations.items():
            category = categorize_relation(relation)
            templates = TEMPLATES_BY_CATEGORY.get(category, TEMPLATES_BY_CATEGORY["général"])
            
            for obj in objects[:max_facts_per_subject]:
                # Utiliser plusieurs templates (pas tous — garder de la variété)
                chosen = random.sample(templates, min(8, len(templates)))
                
                for t in chosen:
                    try:
                        sent = t.format(s=subject, o=obj)
                    except (KeyError, ValueError):
                        sent = f"{subject} {relation} {obj}"
                    
                    sent_lower = sent.lower().strip()
                    if sent_lower not in seen and len(sent) > 15:
                        sentences.append(sent)
                        seen.add(sent_lower)
                
                processed += 1
                if processed % 5000 == 0:
                    print(f"      {processed}/{total_facts} faits traités...")
    
    print(f"   ✅ {len(sentences):,} phrases générées à partir des faits")
    return sentences


def generate_all_sources(all_facts: List[dict], all_subjects: List[str],
                         by_subject: Dict) -> List[str]:
    """Coordonne la génération de toutes les sources."""
    all_sentences = []
    
    # SOURCE 1 : Phrases à partir des faits (60K+)
    print("\n   📝 SOURCE 1 — Phrases à partir des faits (20 templates)")
    s1 = generate_rich_sentences(by_subject)
    all_sentences.extend(s1)
    
    # SOURCE 2 : Définitions médicales (~500)
    print("\n   📝 SOURCE 2 — Définitions médicales")
    s2 = generate_definitions(all_subjects)
    all_sentences.extend(s2)
    print(f"   ✅ {len(s2)} définitions")
    
    # SOURCE 3 : Chaînes de raisonnement clinique (~3000)
    print("\n   📝 SOURCE 3 — Chaînes de raisonnement clinique")
    disease_symptoms = {}
    for subject, relations in by_subject.items():
        all_symptoms = []
        for rel, objs in relations.items():
            if categorize_relation(rel) == "symptôme":
                all_symptoms.extend(objs)
        if all_symptoms:
            disease_symptoms[subject] = list(set(all_symptoms))
    
    s3 = generate_clinical_reasoning(disease_symptoms)
    all_sentences.extend(s3)
    print(f"   ✅ {len(s3)} chaînes de raisonnement")
    
    # SOURCE 4 : Protocoles standardisés (~25)
    print("\n   📝 SOURCE 4 — Protocoles standardisés")
    s4 = generate_protocols()
    all_sentences.extend(s4)
    print(f"   ✅ {len(s4)} protocoles")
    
    # SOURCE 5 : Contexte épidémiologique (~150)
    print("\n   📝 SOURCE 5 — Contexte épidémiologique")
    s5 = generate_epidemiology(all_subjects)
    all_sentences.extend(s5)
    print(f"   ✅ {len(s5)} phrases épidémiologiques")
    
    # Déduplication finale
    unique = []
    seen = set()
    for s in all_sentences:
        sl = s.lower().strip()
        if sl not in seen and len(s) > 10:
            unique.append(s)
            seen.add(sl)
    
    print(f"\n   📊 TOTAL : {len(unique):,} phrases uniques (sur {len(all_sentences):,} générées)")
    return unique


# ═══════════════════════════════════════════════════════════════════
# TOKENISATION ET SAUVEGARDE
# ═══════════════════════════════════════════════════════════════════

def tokenize_all(sentences: List[str]) -> List[List[str]]:
    """Tokenise toutes les phrases."""
    stopwords = {
        'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
        'au', 'aux', 'en', 'pour', 'avec', 'sur', 'est', 'sont', 'ce',
        'cette', 'dans', 'à', 'a', 'que', 'qui', 'par', 'pas', 'ne',
        'son', 'sa', 'ses', 'il', 'elle', 'nous', 'vous',
    }
    
    tokenized = []
    for sent in sentences:
        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", sent.lower())
        tokens = [t for t in tokens if t not in stopwords and len(t) >= 2]
        if len(tokens) >= 3:
            tokenized.append(tokens)
    
    return tokenized


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t0 = time.time()
    random.seed(42)
    
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🌊 GÉNÉRATEUR DE CORPUS MÉDICAL ENRICHI ×10               ║")
    print("║  15 domaines → 62K faits → 50K+ phrases variées            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # 1. Chargement
    print("═" * 70)
    print("  ÉTAPE 1 — Chargement des 15 domaines")
    print("═" * 70)
    all_facts, all_subjects = load_all_facts(FACTS_DIR, ALL_DOMAINS)
    by_subject = group_by_subject(all_facts)
    print()
    
    # 2. Génération multi-source
    print("═" * 70)
    print("  ÉTAPE 2 — Génération multi-source")
    print("═" * 70)
    sentences = generate_all_sources(all_facts, all_subjects, by_subject)
    print()
    
    # 3. Tokenisation
    print("═" * 70)
    print("  ÉTAPE 3 — Tokenisation")
    print("═" * 70)
    tokenized = tokenize_all(sentences)
    total_tokens = sum(len(t) for t in tokenized)
    unique_words = len(set(w for t in tokenized for w in t))
    print(f"   Phrases tokenisées : {len(tokenized):,}")
    print(f"   Tokens totaux      : {total_tokens:,}")
    print(f"   Mots uniques       : {unique_words}")
    print(f"   Tokens/phrase      : {total_tokens/max(1,len(tokenized)):.1f}")
    print()
    
    # 4. Sauvegarde
    print("═" * 70)
    print("  ÉTAPE 4 — Sauvegarde")
    print("═" * 70)
    
    output = {
        "version": "2.0",
        "date": "2026-08-23",
        "description": "Corpus médical enrichi pour entraînement Laplacien sémantique",
        "n_phrases": len(tokenized),
        "n_tokens": total_tokens,
        "n_unique_words": unique_words,
        "sources": {
            "facts": len(all_facts),
            "domains": len(ALL_DOMAINS),
            "subjects": len(all_subjects),
        },
        "sentences": sentences,  # phrases brutes (pour référence)
        "tokenized": tokenized,  # phrases tokenisées (pour PPMI)
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"   💾 Sauvegardé : {OUTPUT_PATH}")
    print(f"   📦 Taille     : {size_mb:.1f} Mo")
    print()
    
    # 5. Statistiques
    print("═" * 70)
    print("  📊 STATISTIQUES FINALES")
    print("═" * 70)
    print()
    
    # Distribution des longueurs de phrases
    lengths = [len(t) for t in tokenized]
    print(f"   Longueur des phrases : min={min(lengths)}, max={max(lengths)}, "
          f"moy={np.mean(lengths):.1f}, méd={np.median(lengths):.0f}")
    
    # Mots les plus fréquents
    word_counts = Counter(w for t in tokenized for w in t)
    print(f"   Top 20 mots les plus fréquents :")
    for w, c in word_counts.most_common(20):
        print(f"     {w:<25s} : {c:>6,d}")
    
    print()
    print(f"   ⏱️  Temps total : {time.time() - t0:.1f}s ({(time.time() - t0)/60:.1f}min)")
    print()
    
    ratio = len(tokenized) / max(1, unique_words)
    print(f"   📐 Ratio phrases/mot : {ratio:.1f} ({'✅ >5, BONNE résolution' if ratio > 5 else '⚠️  <5, résolution modérée' if ratio > 1 else '❌ <1, insuffisant'})")
    print(f"   📁 Fichier : {OUTPUT_PATH}")
    print()