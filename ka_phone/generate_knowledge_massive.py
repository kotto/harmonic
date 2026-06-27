#!/usr/bin/env python3
"""
KA-Next — GÉNÉRATION MASSIVE DE CONNAISSANCES
================================================
Utilise DeepSeek pour générer des faits par domaine.
Couvre les 12 domaines, avec priorité sur les plus faibles.

Usage :
  python generate_knowledge_massive.py --domain philosophy --count 500
  python generate_knowledge_massive.py --all --count 200
  python generate_knowledge_massive.py --list-domains
"""

import os, sys, time, json, requests
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, os.path.dirname(__file__))

BASE_DIR = Path(__file__).parent.parent
CORPUS_DIR = BASE_DIR / "data" / "corpus"
STATE_FILE = CORPUS_DIR / ".gen_state.json"
os.makedirs(CORPUS_DIR, exist_ok=True)

# Clé API DeepSeek
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

DOMAINS = {
    "philosophy": {
        "name": "Philosophie",
        "prompt_fr": "Génère exactement 10 faits sur la philosophie. Chaque fait doit être une phrase simple d'une ligne. Exemples : 'Le stoïcisme est une philosophie antique fondée par Zénon de Kition.', 'Socrate est considéré comme le père de la philosophie occidentale.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 5,
    },
    "mathematics": {
        "name": "Mathématiques",
        "prompt_fr": "Génère exactement 10 faits sur les mathématiques. Chaque fait doit être une phrase simple d'une ligne. Exemples : 'Le théorème de Pythagore établit que dans un triangle rectangle, a²+b²=c².', 'Le nombre pi est approximativement égal à 3.14159.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 5,
    },
    "science": {
        "name": "Science",
        "prompt_fr": "Génère exactement 10 faits sur les sciences (physique, chimie, biologie). Chaque fait doit être une phrase simple d'une ligne. Exemples : 'L'eau bout à 100 degrés Celsius au niveau de la mer.', 'La vitesse de la lumière dans le vide est d'environ 300 000 km/s.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 4,
    },
    "geography": {
        "name": "Géographie",
        "prompt_fr": "Génère exactement 10 faits sur la géographie mondiale. Chaque fait doit être une phrase simple d'une ligne. Exemples : 'La capitale du Japon est Tokyo.', 'Le fleuve Amazone est le plus long fleuve du monde.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 2,
    },
    "history": {
        "name": "Histoire",
        "prompt_fr": "Génère exactement 10 faits sur l'histoire mondiale. Chaque fait doit être une phrase simple d'une ligne. Exemples : 'La Révolution française a débuté en 1789.', 'La Seconde Guerre mondiale s'est terminée en 1945.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 2,
    },
    "technology": {
        "name": "Technologie",
        "prompt_fr": "Génère exactement 10 faits sur la technologie et l'informatique. Chaque fait doit être une phrase simple d'une ligne. Exemples : 'Le premier ordinateur personnel a été commercialisé en 1975.', 'Internet a été inventé dans les années 1960 par le département de la Défense américain.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 3,
    },
    "economics": {
        "name": "Économie",
        "prompt_fr": "Génère exactement 10 faits sur l'économie. Chaque fait doit être une phrase simple d'une ligne. Exemples : 'Le PIB mesure la valeur totale des biens et services produits par un pays.', 'La loi de l'offre et de la demande détermine les prix sur un marché.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 3,
    },
    "health": {
        "name": "Santé",
        "prompt_fr": "Génère exactement 10 faits sur la santé et la médecine. Chaque fait doit être une phrase simple d'une ligne. Exemples : 'La vitamine C aide à renforcer le système immunitaire.', 'Une alimentation équilibrée comprend des protéines, des glucides et des lipides.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 3,
    },
    "culture": {
        "name": "Culture",
        "prompt_fr": "Génère exactement 10 faits sur la culture mondiale (art, littérature, musique). Chaque fait doit être une phrase simple d'une ligne. Exemples : 'Mozart a composé plus de 600 œuvres dans sa vie.', 'Le tableau La Joconde a été peint par Léonard de Vinci.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 3,
    },
    "nature": {
        "name": "Nature",
        "prompt_fr": "Génère exactement 10 faits sur la nature et l'environnement. Chaque fait doit être une phrase simple d'une ligne. Exemples : 'Les abeilles sont essentielles à la pollinisation des plantes.', 'L'Amazonie produit environ 20% de l'oxygène mondial.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 3,
    },
    "sports": {
        "name": "Sports",
        "prompt_fr": "Génère exactement 10 faits sur les sports. Chaque fait doit être une phrase simple d'une ligne. Exemples : 'Le football est le sport le plus populaire au monde.', 'Les Jeux Olympiques modernes ont été créés en 1896.' Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 2,
    },
    "general": {
        "name": "Connaissances générales",
        "prompt_fr": "Génère exactement 10 faits de culture générale. Chaque fait doit être une phrase simple d'une ligne. Varie les sujets (sciences, histoire, géographie, arts, etc.). Réponds uniquement avec les faits, un par ligne, sans numérotation.",
        "priority": 2,
    },
}


def generate_facts(domain: str, count: int = 200) -> List[str]:
    """Génère des faits via DeepSeek API."""
    if not API_KEY or len(API_KEY) < 10:
        print(f"  [!] Pas de clé API DeepSeek")
        return []

    info = DOMAINS.get(domain)
    if not info:
        print(f"  [!] Domaine inconnu : {domain}")
        return []

    facts_set = set()

    for batch in range(0, count, 10):
        remaining = min(10, count - len(facts_set))
        if remaining <= 0:
            break

        prompt = f"Génère exactement {remaining} nouveaux faits différents. Chaque fait doit être une phrase simple d'une ligne. {info['prompt_fr'].split('Génère exactement 10 faits')[1].strip() if 'Génère exactement 10 faits' in info['prompt_fr'] else info['prompt_fr']}"

        try:
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "Tu es un générateur de connaissances factuelles. Réponds UNIQUEMENT avec les faits demandés, un par ligne, sans introduction ni conclusion."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7,
                },
                timeout=30,
            )

            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                for line in text.split("\n"):
                    line = line.strip().lstrip("0123456789.-)• ").strip()
                    if len(line) > 30 and len(line) < 300 and line not in facts_set:
                        facts_set.add(line)

            elif resp.status_code == 429:
                print(f"    Rate limit, attente 5s...")
                time.sleep(5)
            else:
                print(f"    Erreur API {resp.status_code}: {resp.text[:100]}")

        except Exception as e:
            print(f"    Erreur: {e}")

        # Checkpoint
        if batch % 50 == 0:
            state = {}
            if STATE_FILE.exists():
                with open(STATE_FILE) as f:
                    state = json.load(f)
            state[f"{domain}_gen_count"] = len(facts_set)
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
            print(f"    Progression: {len(facts_set)}/{count}")

        time.sleep(0.3)  # Rate limiting

    return list(facts_set)[:count]


def save_facts(domain: str, facts: List[str]):
    """Sauvegarde les faits dans un fichier corpus."""
    filepath = CORPUS_DIR / f"gen_{domain}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        for fact in facts:
            f.write(fact + "\n")

    size_kb = os.path.getsize(filepath) / 1024
    print(f"  Sauvegardé: {len(facts)} faits → {filepath} ({size_kb:.0f} KB)")


def main():
    import argparse
    p = argparse.ArgumentParser(description="Générateur massif de connaissances")
    p.add_argument("--domain", type=str, default=None, help="Domaine spécifique")
    p.add_argument("--all", action="store_true", help="Tous les domaines")
    p.add_argument("--count", type=int, default=200, help="Faits par domaine")
    p.add_argument("--list-domains", action="store_true", help="Lister les domaines")
    args = p.parse_args()

    if args.list_domains:
        print("Domaines disponibles :")
        for d, info in sorted(DOMAINS.items(), key=lambda x: -x[1]["priority"]):
            print(f"  {d:15s} ({info['name']}) — priorité {info['priority']}")
        return

    if not API_KEY or len(API_KEY) < 10:
        print("Clé API DeepSeek non trouvée. Vérifiez le fichier .env")
        return

    if args.domain:
        domains_to_gen = {args.domain: DOMAINS[args.domain]}
    elif args.all:
        # Trier par priorité (philo/maths d'abord)
        domains_to_gen = dict(sorted(DOMAINS.items(), key=lambda x: -x[1]["priority"]))
    else:
        p.print_help()
        return

    print("=" * 70)
    print("  GÉNÉRATION MASSIVE DE CONNAISSANCES")
    print("=" * 70)

    total = 0
    for domain, info in domains_to_gen.items():
        print(f"\n  [{info['name']}] Génération de {args.count} faits...")
        facts = generate_facts(domain, count=args.count)
        if facts:
            save_facts(domain, facts)
            total += len(facts)
        else:
            print(f"    Aucun fait généré")

    print(f"\n{'=' * 70}")
    print(f"  Total: {total} faits générés")
    print(f"  Prochaine étape: python ingest_massive_nx64.py")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()