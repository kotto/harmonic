#!/usr/bin/env python3
"""
GÉNÉRATEUR DE PAIRES QA DEPUIS WIKIPEDIA
===========================================
Extrait automatiquement des paires question-réponse à partir
des articles Wikipedia déjà ingérés dans MGH ou via l'API.

Fonctionnement :
  1. Récupère un article Wikipedia FR via l'API
  2. Extrait les titres de section → questions naturelles
  3. Le premier paragraphe de chaque section → réponse
  4. Vérifie la cohérence (score heuristique)
  5. Sauvegarde en format JSON pour la knowledge base

Usage :
  python ka_phone/generate_qa_from_wikipedia.py --articles 5000  # 5000 articles
  python ka_phone/generate_qa_from_wikipedia.py --quick           # Test (10 articles)
  python ka_phone/generate_qa_from_wikipedia.py --domain cuisine  # Domaine spécifique
  python ka_phone/generate_qa_from_wikipedia.py --resume          # Reprendre
  python ka_phone/generate_qa_from_wikipedia.py --status          # Voir progression
"""

import os, sys, time, json, argparse, re, hashlib, urllib.request, urllib.parse, urllib.error
from typing import Dict, List, Optional, Tuple, Iterator
from datetime import datetime

import numpy as np

# ══════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "qa")
QA_OUTPUT_FILE = os.path.join(DATA_DIR, "qa_generaliste.json")
QA_CHECKPOINT_FILE = os.path.join(DATA_DIR, "qa_checkpoint.json")
HOLOGRAM_SIZE = 256

# Importer les listes d'articles depuis ingest_real_french
sys.path.insert(0, os.path.dirname(__file__))
try:
    from ingest_real_french import WIKIPEDIA_ARTICLES
except ImportError:
    WIKIPEDIA_ARTICLES = {}

# ══════════════════════════════════════════════════════════════════════════
# QUESTION GENERATORS — Transforme un titre en question
# ══════════════════════════════════════════════════════════════════════════

# Templates de questions par domaine
DOMAIN_QUESTION_TEMPLATES = {
    "cuisine_gastronomie": [
        "Qu'est-ce que {concept} ?",
        "Comment préparer {concept} ?",
        "Quels sont les ingrédients de {concept} ?",
        "D'où vient {concept} ?",
        "Comment faire {concept} ?",
        "Quelle est l'histoire de {concept} ?",
    ],
    "sport_loisirs": [
        "Qu'est-ce que {concept} ?",
        "Comment se joue {concept} ?",
        "Quelles sont les règles de {concept} ?",
        "Qui a inventé {concept} ?",
        "Quels sont les bienfaits de {concept} ?",
    ],
    "musique_arts": [
        "Qu'est-ce que {concept} ?",
        "Qui est {concept} ?",
        "Quelle est l'œuvre principale de {concept} ?",
        "Quand est né {concept} ?",
        "Pourquoi {concept} est-il célèbre ?",
    ],
    "psychologie_bienetre": [
        "Qu'est-ce que {concept} ?",
        "Comment gérer {concept} ?",
        "Quelles sont les causes de {concept} ?",
        "Comment améliorer {concept} ?",
        "Qu'est-ce que le trouble de {concept} ?",
    ],
    "voyage_tourisme": [
        "Où se trouve {concept} ?",
        "Quand visiter {concept} ?",
        "Que voir à {concept} ?",
        "Comment aller à {concept} ?",
        "Quelle est la population de {concept} ?",
    ],
    "vie_pratique": [
        "Comment fonctionne {concept} ?",
        "Qu'est-ce que {concept} ?",
        "Comment réparer {concept} ?",
        "Quels sont les types de {concept} ?",
        "Comment choisir {concept} ?",
    ],
    "animaux_nature": [
        "Qu'est-ce qu'un {concept} ?",
        "Où vit {concept} ?",
        "Que mange {concept} ?",
        "Combien de temps vit {concept} ?",
        "Quelles sont les caractéristiques de {concept} ?",
    ],
    "economie_finances": [
        "Qu'est-ce que {concept} ?",
        "Comment fonctionne {concept} ?",
        "Quelle est la définition de {concept} ?",
        "Pourquoi {concept} est-il important ?",
        "Comment calculer {concept} ?",
    ],
    "education_apprentissage": [
        "Qu'est-ce que {concept} ?",
        "Comment apprendre {concept} ?",
        "Quelle est la méthode {concept} ?",
        "Quels sont les niveaux de {concept} ?",
    ],
    "egypte_ancienne": [
        "Qu'est-ce que {concept} ?",
        "Qui est {concept} ?",
        "Quand a régné {concept} ?",
        "Quelle est la signification de {concept} ?",
        "Où se trouve {concept} ?",
    ],
    "pop_culture": [
        "Qu'est-ce que {concept} ?",
        "Qui a créé {concept} ?",
        "Quand est sorti {concept} ?",
        "Quel est le synopsis de {concept} ?",
        "Pourquoi {concept} est-il populaire ?",
    ],
    "sciences": [
        "Qu'est-ce que {concept} ?",
        "Comment fonctionne {concept} ?",
        "Qui a découvert {concept} ?",
        "Quelles sont les applications de {concept} ?",
    ],
    "médecine": [
        "Qu'est-ce que {concept} ?",
        "Quels sont les symptômes de {concept} ?",
        "Comment traite-t-on {concept} ?",
        "Quelles sont les causes de {concept} ?",
    ],
    "histoire": [
        "Qu'est-ce que {concept} ?",
        "Quand a eu lieu {concept} ?",
        "Qui était {concept} ?",
        "Quelle a été l'importance de {concept} ?",
    ],
    "géographie": [
        "Où se trouve {concept} ?",
        "Quelle est la capitale de {concept} ?",
        "Quelle est la superficie de {concept} ?",
        "Quels pays bordent {concept} ?",
    ],
}

# Templates par défaut
DEFAULT_QUESTION_TEMPLATES = [
    "Qu'est-ce que {concept} ?",
    "Pouvez-vous expliquer {concept} ?",
    "Que signifie {concept} ?",
    "Qu'est-ce que c'est que {concept} ?",
]


def clean_concept_name(title: str) -> str:
    """Nettoie un titre Wikipedia pour en faire un nom lisible."""
    # Remplacer les underscores par des espaces
    name = title.replace("_", " ")
    # Enlever les suffixes entre parenthèses
    name = re.sub(r'\s*\([^)]+\)', '', name)
    return name.strip()


def generate_question(title: str, domain: str) -> str:
    """Génère une question naturelle à partir d'un titre d'article."""
    import random
    concept = clean_concept_name(title)
    templates = DOMAIN_QUESTION_TEMPLATES.get(domain, DEFAULT_QUESTION_TEMPLATES)
    template = random.choice(templates)
    return template.format(concept=concept)


# ══════════════════════════════════════════════════════════════════════════
# WIKIPEDIA EXTRACTOR
# ══════════════════════════════════════════════════════════════════════════

def fetch_wikipedia_sections(title: str, langue: str = "fr") -> List[Dict]:
    """
    Récupère les sections d'un article Wikipedia avec leurs titres et contenus.
    Retourne une liste de {heading, content}.
    """
    url = f"https://{langue}.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "format": "json",
        "page": title,
        "prop": "sections",
        "redirects": 1,
    }

    try:
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        req = urllib.request.Request(full_url, headers={"User-Agent": "KA-Phone-QA/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []

    sections_data = data.get("parse", {}).get("sections", [])
    if not sections_data:
        return []

    results = []
    for section in sections_data:
        heading = section.get("line", "").strip()
        index = section.get("index", "")
        if not heading or heading in ["Notes et références", "Voir aussi", "Liens externes",
                                        "Bibliographie", "Annexes", "Références"]:
            continue

        # Récupérer le contenu de cette section
        content = fetch_wikipedia_section_content(title, index, langue)
        if content and len(content) > 40:
            # Prendre le premier paragraphe
            first_para = content.split('\n\n')[0] if '\n\n' in content else content
            first_para = first_para.strip()[:500]  # Limiter à 500 caractères
            if len(first_para) > 20:
                results.append({
                    "heading": heading,
                    "content": first_para,
                })

    return results


def fetch_wikipedia_section_content(title: str, section_index: str, langue: str = "fr") -> str:
    """Récupère le contenu d'une section spécifique."""
    url = f"https://{langue}.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "format": "json",
        "page": title,
        "prop": "text",
        "section": section_index,
        "redirects": 1,
        "disableeditsection": 1,
    }

    try:
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        req = urllib.request.Request(full_url, headers={"User-Agent": "KA-Phone-QA/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        text = data.get("parse", {}).get("text", {}).get("*", "")
        # Nettoyer HTML basique
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\[\d+\]', '', text)  # Citations
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    except Exception:
        return ""


def fetch_wikipedia_intro(title: str, langue: str = "fr") -> str:
    """Récupère l'introduction d'un article Wikipedia."""
    url = f"https://{langue}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "redirects": 1,
    }

    try:
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        req = urllib.request.Request(full_url, headers={"User-Agent": "KA-Phone-QA/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        pages = data.get("query", {}).get("pages", {})
        for pid, pinfo in pages.items():
            if "missing" in pinfo:
                return ""
            return pinfo.get("extract", "").strip()[:800]
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════════════
# QA SCORING — Cohérence et qualité
# ══════════════════════════════════════════════════════════════════════════

def score_qa_quality(question: str, answer: str) -> float:
    """
    Évalue la qualité d'une paire QA.
    Retourne un score entre 0 et 1.
    """
    score = 1.0

    # Pénaliser les réponses trop courtes
    if len(answer) < 20:
        score *= 0.3
    elif len(answer) < 40:
        score *= 0.6

    # Pénaliser les réponses trop longues (probablement pas une bonne réponse)
    if len(answer) > 500:
        score *= 0.7

    # Vérifier que la réponse contient des mots-clés de la question
    q_words = set(re.findall(r'[a-zéèêëàâîïôûùç]+', question.lower()))
    a_words = set(re.findall(r'[a-zéèêëàâîïôûùç]+', answer.lower()))
    overlap = q_words & a_words
    if len(q_words) > 2 and len(overlap) < 1:
        score *= 0.5

    # Pénaliser si la réponse commence par une question
    if answer.strip().endswith('?'):
        score *= 0.4

    # Bonus si la réponse contient des chiffres (faits)
    if re.search(r'\d', answer):
        score *= 1.1

    return min(1.0, score)


def generate_holographic_signature(text: str) -> Tuple[float, float]:
    """Génère une signature holographique (kx, ky) pour un texte."""
    h = hashlib.sha256(text.encode()[:200]).hexdigest()
    kx = (int(h[:16], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
    ky = (int(h[16:32], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
    kx = (kx - HOLOGRAM_SIZE / 2) / HOLOGRAM_SIZE * 20
    ky = (ky - HOLOGRAM_SIZE / 2) / HOLOGRAM_SIZE * 20
    return kx, ky


# ══════════════════════════════════════════════════════════════════════════
# MAIN QA GENERATOR
# ══════════════════════════════════════════════════════════════════════════

def generate_qa_from_articles(
    articles: List[Tuple[str, str]],
    output_file: str = QA_OUTPUT_FILE,
    checkpoint_file: str = QA_CHECKPOINT_FILE,
    min_quality: float = 0.5,
    resume: bool = False,
) -> Dict:
    """
    Génère des paires QA à partir d'une liste d'articles Wikipedia.

    Args:
        articles: Liste de (titre, domaine)
        output_file: Fichier JSON de sortie
        checkpoint_file: Fichier checkpoint
        min_quality: Score minimum pour conserver une QA
        resume: Reprendre au checkpoint

    Returns:
        Stats de génération
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    # Charger existant
    qa_pairs = []
    completed_articles = set()
    if resume and os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            qa_pairs = json.load(f)
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                cp = json.load(f)
                completed_articles = set(cp.get("completed", []))

    print(f"\n{'=' * 60}")
    print(f"GÉNÉRATION DE PAIRES QA — {len(articles)} articles")
    print(f"{'=' * 60}")
    print(f"  Existantes : {len(qa_pairs)} paires déjà générées")
    print(f"  Complétés  : {len(completed_articles)} articles déjà traités")
    print(f"  Qualité min: {min_quality}")

    t0 = time.time()
    new_qa = 0
    articles_processed = 0
    articles_skipped = 0
    errors = 0

    for i, (titre, domaine) in enumerate(articles):
        if titre in completed_articles:
            articles_skipped += 1
            continue

        # Récupérer l'intro + sections
        intro = fetch_wikipedia_intro(titre)
        sections = fetch_wikipedia_sections(titre)

        article_qa_count = 0

        # QA depuis l'intro
        if intro and len(intro) > 30:
            question = generate_question(titre, domaine)
            quality = score_qa_quality(question, intro)
            if quality >= min_quality:
                kx, ky = generate_holographic_signature(titre)
                qa_pairs.append({
                    "question": question,
                    "answer": intro,
                    "domain": domaine,
                    "source_article": titre,
                    "section": "introduction",
                    "quality": round(quality, 3),
                    "kx": round(kx, 3),
                    "ky": round(ky, 3),
                })
                new_qa += 1
                article_qa_count += 1

        # QA depuis les sections
        for section in sections:
            heading = section["heading"]
            content = section["content"]
            if len(content) < 30:
                continue

            # Générer une question à partir du titre de section
            section_question = f"Que dire sur {clean_concept_name(heading)} concernant {clean_concept_name(titre)} ?"
            quality = score_qa_quality(section_question, content)
            if quality >= min_quality:
                kx, ky = generate_holographic_signature(f"{titre}_{heading}")
                qa_pairs.append({
                    "question": section_question,
                    "answer": content,
                    "domain": domaine,
                    "source_article": titre,
                    "section": heading,
                    "quality": round(quality, 3),
                    "kx": round(kx, 3),
                    "ky": round(ky, 3),
                })
                new_qa += 1
                article_qa_count += 1

        articles_processed += 1

        # Progression
        if (i + 1) % 50 == 0:
            dt = time.time() - t0
            v = (i + 1) / dt if dt > 0 else 0
            print(f"  [{i+1}/{len(articles)}] {new_qa} nouvelles QA | "
                  f"{article_qa_count} QA/article | {v:.1f} art/min | "
                  f"Total: {len(qa_pairs)} paires")

            # Sauvegarde checkpoint
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump({"completed": list(completed_articles) + [t for t, d in articles[:i+1]]}, f)

    # Sauvegarde finale
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump({"completed": [t for t, d in articles]}, f)

    dt = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"✅ GÉNÉRATION TERMINÉE")
    print(f"{'=' * 60}")
    print(f"  Articles traités   : {articles_processed}")
    print(f"  Articles sautés    : {articles_skipped}")
    print(f"  Erreurs            : {errors}")
    print(f"  Nouvelles QA       : {new_qa}")
    print(f"  QA totales         : {len(qa_pairs)}")
    print(f"  Durée              : {dt/60:.1f} min")
    print(f"  Fichier            : {output_file}")

    # Stats par domaine
    domain_count = {}
    for qa in qa_pairs:
        d = qa.get("domain", "unknown")
        domain_count[d] = domain_count.get(d, 0) + 1
    print(f"\n  Par domaine :")
    for d, c in sorted(domain_count.items(), key=lambda x: -x[1]):
        print(f"    - {d}: {c} QA")

    return {
        "articles_processed": articles_processed,
        "articles_skipped": articles_skipped,
        "errors": errors,
        "new_qa": new_qa,
        "total_qa": len(qa_pairs),
        "duration_min": dt / 60,
        "output_file": output_file,
    }


# ══════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Générateur de paires QA depuis Wikipedia — KA Phone",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python ka_phone/generate_qa_from_wikipedia.py --articles 5000
  python ka_phone/generate_qa_from_wikipedia.py --quick
  python ka_phone/generate_qa_from_wikipedia.py --domain cuisine_gastronomie
  python ka_phone/generate_qa_from_wikipedia.py --resume
  python ka_phone/generate_qa_from_wikipedia.py --status
        """
    )

    parser.add_argument("--articles", type=int, default=5000,
                       help="Nombre d'articles à traiter (défaut: 5000)")
    parser.add_argument("--quick", action="store_true",
                       help="Mode rapide (10 articles)")
    parser.add_argument("--domain", type=str, default=None,
                       help="Domaine spécifique (ex: cuisine_gastronomie, sport_loisirs)")
    parser.add_argument("--resume", action="store_true",
                       help="Reprendre au checkpoint")
    parser.add_argument("--status", action="store_true",
                       help="Voir l'état de la génération")
    parser.add_argument("--min-quality", type=float, default=0.5,
                       help="Score minimum de qualité (défaut: 0.5)")
    parser.add_argument("--output", type=str, default=None,
                       help="Fichier de sortie (défaut: data/qa/qa_generaliste.json)")

    args = parser.parse_args()

    # Status
    if args.status:
        show_qa_status()
        return

    # Collecter les articles
    if WIKIPEDIA_ARTICLES:
        all_articles = []
        for domaine, titres in WIKIPEDIA_ARTICLES.items():
            if args.domain and args.domain != domaine:
                continue
            all_articles.extend([(t, domaine) for t in titres])
    else:
        print("  ⚠️ Aucune liste d'articles trouvée.")
        print("  Assurez-vous que ingest_real_french.py est accessible.")
        return

    import random
    random.shuffle(all_articles)

    n = 10 if args.quick else min(args.articles, len(all_articles))
    selected = all_articles[:n]

    print(f"\n  📚 {n} articles sélectionnés sur {len(all_articles)} disponibles")
    if args.domain:
        print(f"  🏷️  Domaine : {args.domain}")

    output = args.output or QA_OUTPUT_FILE

    # Générer
    result = generate_qa_from_articles(
        articles=selected,
        output_file=output,
        min_quality=args.min_quality,
        resume=args.resume,
    )

    print(f"\n  ✅ Fichier QA : {output}")
    print(f"  📊 Utilisable avec :")
    print(f"     python -c \"from lm_arena.semantic_matcher import HybridMatcher; m = HybridMatcher(); m.load_qa('{output}')\"")


def show_qa_status():
    """Affiche l'état de la génération QA."""
    print(f"\n{'=' * 50}")
    print(f"STATUT QA — GÉNÉRALISATION KA PHONE")
    print(f"{'=' * 50}")

    if os.path.exists(QA_OUTPUT_FILE):
        with open(QA_OUTPUT_FILE, 'r', encoding='utf-8') as f:
            qa_list = json.load(f)
        print(f"  QA générées : {len(qa_list)} paires")

        domain_count = {}
        for qa in qa_list:
            d = qa.get("domain", "unknown")
            domain_count[d] = domain_count.get(d, 0) + 1
        print(f"  Domaines :")
        for d, c in sorted(domain_count.items(), key=lambda x: -x[1])[:15]:
            print(f"    - {d}: {c}")

        # Qualité moyenne
        qualities = [qa.get("quality", 0) for qa in qa_list]
        if qualities:
            print(f"  Qualité moyenne : {sum(qualities)/len(qualities):.3f}")
            print(f"  Qualité médiane : {sorted(qualities)[len(qualities)//2]:.3f}")
    else:
        print("  Aucune QA générée pour le moment.")
        print("  Lancez : python ka_phone/generate_qa_from_wikipedia.py")


if __name__ == "__main__":
    main()