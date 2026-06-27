#!/usr/bin/env python3
"""
QA MASSIVE GENERATOR — 100 000+ paires depuis Wikipedia dumps
===============================================================
Utilise l'API Wikipedia en streaming pour récupérer des articles
et générer automatiquement des paires question-réponse.

Sources :
  - Wikipedia FR (articles aléatoires + par catégories)
  - Wikidata FR (descriptions d'entités)
  - Génération synthétique (templates × faits extraits)

Usage :
  python ka_phone/generate_qa_massive.py                        # Objectif 100K
  python ka_phone/generate_qa_massive.py --target 50000         # Objectif perso
  python ka_phone/generate_qa_massive.py --quick                # Test 1000
  python ka_phone/generate_qa_massive.py --resume               # Reprendre
  python ka_phone/generate_qa_massive.py --status               # Progression
"""

import os, sys, json, time, re, random, urllib.request, urllib.parse, urllib.error
from typing import List, Dict, Optional, Iterator
from datetime import datetime
import argparse

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "qa_massive")
OUTPUT_FILE = os.path.join(DATA_DIR, "qa_massive_100k.json")
CHECKPOINT_FILE = os.path.join(DATA_DIR, "checkpoint_massive.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# TEMPLATES DE QUESTIONS (similaires à synthetic_qa_generator)
# ══════════════════════════════════════════════════════════════════════════

QUESTION_TEMPLATES = {
    "quoi": [
        "Qu'est-ce que {sujet} ?", "C'est quoi {sujet} ?",
        "Que signifie {sujet} ?", "Peux-tu expliquer {sujet} ?",
        "Explique-moi {sujet}", "Parle-moi de {sujet}",
    ],
    "qui": [
        "Qui est {sujet} ?", "Qui etait {sujet} ?",
        "Connais-tu {sujet} ?", "Qui est la personne nommee {sujet} ?",
        "Dis-moi qui est {sujet}", "Quelle est la biographie de {sujet} ?",
    ],
    "ou": [
        "Ou se trouve {sujet} ?", "Ou est {sujet} ?",
        "Quel pays abrite {sujet} ?", "Peux-tu me situer {sujet} ?",
        "Dans quelle region est {sujet} ?",
    ],
    "quand": [
        "Quand a eu lieu {sujet} ?", "A quelle date {sujet} ?",
        "En quelle annee {sujet} ?", "Quand est-ce que {sujet} ?",
    ],
    "comment": [
        "Comment fonctionne {sujet} ?", "Comment ca marche {sujet} ?",
        "Comment utiliser {sujet} ?", "Comment se passe {sujet} ?",
    ],
    "pourquoi": [
        "Pourquoi {sujet} est-il important ?", "Pourquoi {sujet} est-il celebre ?",
        "Quelle est l'importance de {sujet} ?", "En quoi {sujet} est-il significatif ?",
    ],
    "informel": [
        "Tu sais quoi sur {sujet} ?", "Des infos sur {sujet} ?",
        "Tu connais {sujet} ?", "Raconte-moi {sujet}",
        "{sujet}, ca te dit quelque chose ?",
    ],
}


# ══════════════════════════════════════════════════════════════════════════
# WIKIPEDIA STREAMING FETCHER
# ══════════════════════════════════════════════════════════════════════════

def fetch_random_wikipedia_articles(count: int = 500, langue: str = "fr", delay: float = 0.5) -> Iterator[Dict]:
    """Récupère des articles Wikipedia aléatoires via l'API."""
    url = f"https://{langue}.wikipedia.org/w/api.php"
    fetched = 0
    continuer_token = None

    while fetched < count:
        if fetched > 0 and fetched % 20 == 0:
            time.sleep(delay * 3)  # Pause plus longue tous les 20 articles
        else:
            time.sleep(delay)
        params = {
            "action": "query", "format": "json",
            "list": "random", "rnnamespace": "0",
            "rnlimit": min(20, count - fetched),
            "prop": "extracts", "exintro": 1, "explaintext": 1,
        }
        if continuer_token:
            params["rncontinue"] = continuer_token

        try:
            qs = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            full_url = f"{url}?{qs}"
            req = urllib.request.Request(full_url, headers={"User-Agent": "KA-QA-Generator/1.0 (contact: kaphone@example.com)"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            articles = data.get("query", {}).get("random", [])
            for art in articles:
                title = art.get("title", "")
                # Skip non-content pages
                if any(title.startswith(p) for p in ["Catégorie:", "Fichier:", "Modèle:",
                                                       "Wikipédia:", "Aide:", "Portail:",
                                                       "Projet:", "Discussion"]):
                    continue
                yield {"title": title, "method": "random"}
                fetched += 1
                if fetched >= count:
                    break
            if "continue" in data:
                continuer_token = data["continue"].get("rncontinue")
        except Exception as e:
            print(f"    Erreur fetch random: {e}")
            break


def fetch_article_extract(title: str, langue: str = "fr", max_chars: int = 500) -> Optional[str]:
    """Récupère l'extrait d'un article Wikipedia."""
    url = f"https://{langue}.wikipedia.org/w/api.php"
    params = {
        "action": "query", "format": "json",
        "titles": title, "prop": "extracts",
        "exintro": 1, "explaintext": 1, "redirects": 1,
    }
    try:
        qs = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        full_url = f"{url}?{qs}"
        req = urllib.request.Request(full_url, headers={"User-Agent": "KA-QA-Generator/1.0 (contact: kaphone@example.com)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        pages = data.get("query", {}).get("pages", {})
        for pid, pinfo in pages.items():
            if "missing" in pinfo:
                return None
            extract = pinfo.get("extract", "")
            # Nettoyer et tronquer
            extract = re.sub(r'\s+', ' ', extract).strip()
            if len(extract) > max_chars:
                # Couper à la dernière phrase avant max_chars
                cut = extract[:max_chars]
                last_dot = max(cut.rfind('.'), cut.rfind('!'), cut.rfind('?'))
                if last_dot > 100:
                    extract = extract[:last_dot + 1]
                else:
                    extract = extract[:max_chars] + "..."
            return extract if len(extract) > 40 else None
    except Exception:
        return None


def fetch_wikidata_descriptions(limit: int = 5000, langue: str = "fr") -> Iterator[Dict]:
    """Récupère des descriptions d'entités Wikidata via l'API Wikipedia."""
    url = f"https://{langue}.wikipedia.org/w/api.php"
    # Utiliser les catégories Wikipedia pour trouver du contenu structuré
    categories = [
        "Catégorie:Article_principal", "Catégorie:Portail",
        "Catégorie:Science", "Catégorie:Histoire", "Catégorie:Géographie",
        "Catégorie:Culture", "Catégorie:Technologie", "Catégorie:Médecine",
        "Catégorie:Sport", "Catégorie:Art", "Catégorie:Philosophie",
        "Catégorie:Économie", "Catégorie:Politique", "Catégorie:Biologie",
    ]

    fetched = 0
    for cat in categories:
        continuer_token = None
        while fetched < limit:
            params = {
                "action": "query", "format": "json",
                "list": "categorymembers", "cmtitle": cat,
                "cmlimit": "50", "cmtype": "page",
            }
            if continuer_token:
                params["cmcontinue"] = continuer_token

            try:
                qs = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
                full_url = f"{url}?{qs}"
                req = urllib.request.Request(full_url, headers={"User-Agent": "KA-QA-Generator/1.0 (contact: kaphone@example.com)"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())
                members = data.get("query", {}).get("categorymembers", [])

                for member in members:
                    title = member.get("title", "")
                    if title.startswith("Catégorie:") or title.startswith("Portail:") or title.startswith("Projet:"):
                        continue
                    yield {"title": title, "category": cat.replace("Catégorie:", ""), "method": "category"}
                    fetched += 1
                    if fetched >= limit:
                        break

                if "continue" in data:
                    continuer_token = data["continue"].get("cmcontinue")
                else:
                    break
            except Exception as e:
                print(f"    Erreur fetch category {cat}: {e}")
                break
        if fetched >= limit:
            break


# ══════════════════════════════════════════════════════════════════════════
# QA GENERATOR FROM ARTICLE EXTRACTS
# ══════════════════════════════════════════════════════════════════════════

def clean_title(title: str) -> str:
    """Nettoie un titre Wikipedia pour en faire un sujet lisible."""
    title = title.replace("_", " ")
    title = re.sub(r'\s*\([^)]+\)', '', title)
    return title.strip()


def generate_questions_from_title(title: str, count: int = 6) -> List[str]:
    """Génère des questions à partir d'un titre d'article."""
    sujet = clean_title(title)
    questions = []
    # 1 question par catégorie de template
    for cat, templates in QUESTION_TEMPLATES.items():
        tmpl = random.choice(templates)
        q = tmpl.format(sujet=sujet)
        if q not in questions:
            questions.append(q)
    # Ajouter quelques variantes aléatoires
    for _ in range(count - len(QUESTION_TEMPLATES)):
        cat = random.choice(list(QUESTION_TEMPLATES.keys()))
        tmpl = random.choice(QUESTION_TEMPLATES[cat])
        q = tmpl.format(sujet=sujet)
        if q not in questions:
            questions.append(q)
    return questions[:count]


def generate_qa_from_stream(article_stream: Iterator[Dict], total_target: int,
                            checkpoint: Dict, resume: bool = False) -> List[Dict]:
    """
    Génère des paires QA à partir d'un flux d'articles Wikipedia.

    Args:
        article_stream: Itérateur de {"title": str}
        total_target: Nombre total de QA visé
        checkpoint: Dict de progression
    """
    qa_pairs = checkpoint.get("qa_pairs", [])
    processed_titles = set(checkpoint.get("processed_titles", []))
    t0 = time.time()
    errors = 0
    new_qa = 0

    for art in article_stream:
        title = art["title"]
        if title in processed_titles:
            continue

        # Récupérer l'extrait
        extract = fetch_article_extract(title)
        if not extract or len(extract) < 40:
            errors += 1
            processed_titles.add(title)
            continue

        # Générer des questions
        questions = generate_questions_from_title(title)
        for q in questions:
            qa_pairs.append({
                "question": q,
                "answer": extract,
                "source": "wikipedia",
                "source_title": title,
                "generated": True,
            })
            new_qa += 1

        processed_titles.add(title)

        # Progression
        if len(processed_titles) % 200 == 0:
            dt = time.time() - t0
            v = len(processed_titles) / dt if dt > 0 else 0
            print(f"  [{len(processed_titles)} articles] {len(qa_pairs)} QA | "
                  f"{v:.1f} art/min | {errors} err | ETA: {(total_target - len(qa_pairs)) / (v * 6) if v > 0 else 0:.0f}min")

            # Checkpoint
            save_checkpoint(qa_pairs, list(processed_titles))

        if len(qa_pairs) >= total_target:
            break

    return qa_pairs


# ══════════════════════════════════════════════════════════════════════════
# CHECKPOINT
# ══════════════════════════════════════════════════════════════════════════

def load_checkpoint() -> Dict:
    if not os.path.exists(CHECKPOINT_FILE):
        return {"qa_pairs": [], "processed_titles": [], "started_at": datetime.now().isoformat()}
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(qa_pairs: List[Dict], processed_titles: List[str]):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "qa_pairs": qa_pairs,
            "processed_titles": processed_titles[-50000:],  # Keep last 50k
            "total_qa": len(qa_pairs),
            "last_saved": datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)
    # Save QA to output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="QA Massive Generator — 100K+ depuis Wikipedia")
    parser.add_argument("--target", type=int, default=100000, help="Nombre cible de QA (défaut: 100000)")
    parser.add_argument("--quick", action="store_true", help="Mode test (1000 QA)")
    parser.add_argument("--resume", action="store_true", help="Reprendre au checkpoint")
    parser.add_argument("--status", action="store_true", help="Voir la progression")
    parser.add_argument("--source", type=str, default="both",
                       help="Source: random, categories, both (défaut: both)")
    args = parser.parse_args()

    if args.status:
        cp = load_checkpoint()
        print(f"  QA générées    : {cp.get('total_qa', 0)}")
        print(f"  Articles traités : {len(cp.get('processed_titles', []))}")
        print(f"  Dernière sauvegarde : {cp.get('last_saved', 'jamais')}")
        print(f"  Fichier : {OUTPUT_FILE}")
        return

    target = 1000 if args.quick else args.target
    checkpoint = load_checkpoint() if args.resume else {"qa_pairs": [], "processed_titles": [], "started_at": datetime.now().isoformat()}

    existing_qa = len(checkpoint.get("qa_pairs", []))
    remaining = target - existing_qa
    if remaining <= 0:
        print(f"  Objectif déjà atteint : {existing_qa} QA existantes.")
        return

    # Nombre d'articles nécessaires (~6 questions par article)
    articles_needed = max(remaining // 6, 100)

    print(f"=" * 60)
    print(f"QA MASSIVE GENERATOR — Objectif: {target:,} QA depuis Wikipedia")
    print(f"=" * 60)
    print(f"  Existantes   : {existing_qa:,}")
    print(f"  Restantes    : {remaining:,}")
    print(f"  Articles visés : ~{articles_needed:,} (~6 QA/article)")
    print(f"  Source       : {args.source}")
    print(f"  Fichier      : {OUTPUT_FILE}")

    if args.source in ("random", "both"):
        print(f"\n  --- Source: Articles aléatoires Wikipedia FR ---")
        stream = fetch_random_wikipedia_articles(articles_needed)
        checkpoint["qa_pairs"] = generate_qa_from_stream(
            stream, target, checkpoint, resume=args.resume
        )

    if args.source in ("categories", "both"):
        remaining = target - len(checkpoint.get("qa_pairs", []))
        if remaining > 0:
            print(f"\n  --- Source: Catégories Wikipedia FR ---")
            stream = fetch_wikidata_descriptions(remaining // 5)
            checkpoint["qa_pairs"] = generate_qa_from_stream(
                stream, target, checkpoint, resume=True
            )

    qa_list = checkpoint.get("qa_pairs", [])
    print(f"\n{'=' * 60}")
    print(f"GENERATION TERMINEE")
    print(f"{'=' * 60}")
    print(f"  QA totales : {len(qa_list):,}")
    print(f"  Fichier    : {OUTPUT_FILE}")

    # Stats par source
    sources = {}
    for qa in qa_list:
        s = qa.get("source", "unknown")
        sources[s] = sources.get(s, 0) + 1
    for s, c in sorted(sources.items()):
        print(f"    - {s}: {c:,}")

    print(f"\n  Pour charger dans le serveur, ajouter dans unified_server.py :")
    print(f"  qa_massive_file = '{OUTPUT_FILE}'")

    save_checkpoint(qa_list, checkpoint.get("processed_titles", []))


if __name__ == "__main__":
    main()