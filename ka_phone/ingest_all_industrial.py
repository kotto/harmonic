#!/usr/bin/env python3
"""
KA-Enterprise — PIPELINE D'INGESTION INDUSTRIELLE TOUS DOMAINES
====================================================================
Applique l'approche industrielle à TOUS les 12 hologrammes :
  1. Dataset HuggingFace (streaming, pas de téléchargement complet)
  2. API publiques gratuites
  3. Génération DeepSeek (faits ciblés)
  4. Fichiers locaux (corpus + wiki + gen)

USAGE :
  python ingest_all_industrial.py                # Tous les domaines
  python ingest_all_industrial.py --domain geo   # Géographie uniquement
  python ingest_all_industrial.py --benchmark    # Benchmark final

SOURCES PAR DOMAINE :
  geography   : RestCountries API + Wikipedia Geo + DeepSeek
  history     : Wikipedia History + DeepSeek
  science     : Wikipedia Science + DeepSeek
  mathematics : Wikipedia Math + DeepSeek
  philosophy  : Wikipedia Philo + DeepSeek
  technology  : Wikipedia Tech + DeepSeek
  medical     : MedQuAD + OpenFDA + DeepSeek
  juridique   : Wikipedia Law + DeepSeek
  finance     : DeepSeek
  culture     : DeepSeek
  nature      : DeepSeek
  sports      : DeepSeek
"""

import os, sys, json, time, re, glob, hashlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from ka_enterprise import EnterpriseHologram

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "corpus")
os.makedirs(CORPUS_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION DES DOMAINES
# ═══════════════════════════════════════════════════════════════════

DOMAINS_CONFIG = {
    "geography": {
        "name": "Géographie",
        "api_fn": "_ingest_restcountries",
        "wiki_fn": "_ingest_wiki_stream",
        "wiki_langs": ["fr", "en"],
        "keywords": ["capitale", "pays", "ville", "fleuve", "montagne", "région", "continent",
                     "océan", "population", "km²", "habitant", "situé", "département"],
        "deepseek_prompt": "Génère exactement 10 faits sur la géographie mondiale (capitales, pays, fleuves, montagnes, populations, superficies, régions). Variété maximale : Afrique, Asie, Europe, Amériques, Océanie.",
    },
    "history": {
        "name": "Histoire",
        "wiki_langs": ["fr", "en"],
        "keywords": ["siècle", "guerre", "roi", "empereur", "révolution", "bataille",
                     "empire", "dynastie", "né en", "mort en", "ancien", "fondé", "civilisation"],
        "deepseek_prompt": "Génère exactement 10 faits sur l'histoire mondiale (événements, dates, personnages, civilisations, guerres, révolutions, traités). Variété maximale.",
    },
    "science": {
        "name": "Science",
        "wiki_langs": ["fr", "en"],
        "keywords": ["physique", "chimie", "biologie", "mathématique", "astronomie",
                     "découverte", "théorie", "équation", "élément", "atome", "cellule",
                     "science", "scientifique", "expérience", "loi"],
        "deepseek_prompt": "Génère exactement 10 faits scientifiques factuels (physique, chimie, biologie, astronomie). Variété maximale.",
    },
    "mathematics": {
        "name": "Mathématiques",
        "wiki_langs": ["fr", "en"],
        "keywords": ["théorème", "équation", "nombre", "géométrie", "algèbre", "calcul",
                     "probabilité", "statistique", "fonction", "mathématique", "dérivée", "intégrale"],
        "deepseek_prompt": "Génère exactement 10 faits sur les mathématiques (théorèmes, nombres, géométrie, algèbre, calcul, probabilités, grands mathématiciens).",
    },
    "philosophy": {
        "name": "Philosophie",
        "wiki_langs": ["fr", "en"],
        "keywords": ["philosophie", "éthique", "morale", "pensée", "concept",
                     "socrate", "platon", "kant", "conscience", "raison", "métaphysique"],
        "deepseek_prompt": "Génère exactement 10 faits sur la philosophie (courants, auteurs, concepts, éthique, métaphysique, logique).",
    },
    "technology": {
        "name": "Technologie",
        "wiki_langs": ["fr", "en"],
        "keywords": ["ordinateur", "internet", "logiciel", "algorithme", "programme",
                     "donnée", "réseau", "code", "système", "intelligence artificielle", "machine"],
        "deepseek_prompt": "Génère exactement 10 faits sur la technologie et l'informatique (matériel, logiciel, internet, IA, réseaux).",
    },
    "juridique": {
        "name": "Droit",
        "keywords": ["loi", "droit", "contrat", "code civil", "code pénal", "tribunal",
                     "constitution", "jurisprudence", "avocat", "jugement", "article"],
        "deepseek_prompt": "Génère exactement 10 faits juridiques (lois, codes, articles, jurisprudence, droits fondamentaux).",
    },
    "finance": {
        "name": "Finance",
        "keywords": ["bilan", "bourse", "investissement", "PIB", "inflation", "banque",
                     "marché", "action", "obligation", "taux", "dividende", "capital"],
        "deepseek_prompt": "Génère exactement 10 faits sur la finance et l'économie (marchés, banques, PIB, inflation, bourses mondiales).",
    },
    "culture": {
        "name": "Culture",
        "keywords": ["art", "musique", "littérature", "cinéma", "peinture", "sculpture",
                     "théâtre", "opéra", "danse", "poésie", "roman", "festival"],
        "deepseek_prompt": "Génère exactement 10 faits sur la culture mondiale (art, littérature, musique, cinéma). Variété maximale.",
    },
    "nature": {
        "name": "Nature",
        "keywords": ["animal", "plante", "écosystème", "forêt", "océan", "espèce",
                     "biodiversité", "climat", "environnement", "pollution", "conservation"],
        "deepseek_prompt": "Génère exactement 10 faits sur la nature et l'environnement (espèces, écosystèmes, climat, biodiversité).",
    },
    "sports": {
        "name": "Sports",
        "keywords": ["sport", "football", "basket", "tennis", "olympique", "champion",
                     "record", "athlète", "compétition", "coupe du monde", "tournoi"],
        "deepseek_prompt": "Génère exactement 10 faits sur les sports (disciplines, records, compétitions, JO, coupes du monde).",
    },
}


# ═══════════════════════════════════════════════════════════════════
# INGESTION : RESTCOUNTRIES API (Géographie)
# ═══════════════════════════════════════════════════════════════════

def _ingest_restcountries(holo: EnterpriseHologram) -> int:
    """250 pays via API RestCountries."""
    import urllib.request
    url = "https://restcountries.com/v3.1/all?fields=name,capital,region,subregion,population,area,languages"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KA-Ingest/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = json.loads(r.read().decode())
            countries = raw if isinstance(raw, list) else raw.get("data", [])
    except Exception as e:
        print(f"    [!] API RestCountries : {e}")
        return 0

    total = 0
    if not countries:
        return 0
    for c in countries:
        if isinstance(c, str): continue
        n = c.get("name", {}).get("common", "") if isinstance(c.get("name"), dict) else ""
        if not n: continue
        cap = (c.get("capital") or [""])[0] if c.get("capital") else ""
        reg = (c.get("subregion", "") or c.get("region", "")).capitalize()
        pop = c.get("population", 0) or 0
        area = c.get("area", 0) or 0

        holo.ingest_text(f"{n} est un pays situé en {reg}.", source_file="restcountries.txt")
        total += 1
        if cap: holo.ingest_text(f"La capitale de {n} est {cap}.", source_file="restcountries.txt"); total += 1
        if pop: holo.ingest_text(f"{n} compte environ {pop:,} habitants.".replace(","," "), source_file="restcountries.txt"); total += 1
        if area: holo.ingest_text(f"La superficie de {n} est d'environ {area:,} km².".replace(","," "), source_file="restcountries.txt"); total += 1
    return total


# ═══════════════════════════════════════════════════════════════════
# INGESTION : WIKIPEDIA STREAMING (HuggingFace)
# ═══════════════════════════════════════════════════════════════════

def _ingest_wiki_stream(holo: EnterpriseHologram, domain: str, lang: str, max_articles: int = 50) -> int:
    """Ingère Wikipedia via HuggingFace streaming filtré par mots-clés."""
    try:
        from datasets import load_dataset
    except ImportError:
        return 0

    config = DOMAINS_CONFIG.get(domain, {})
    keywords = config.get("keywords", [])

    try:
        ds = load_dataset("wikimedia/wikipedia", f"20231101.{lang}", streaming=True, split="train", trust_remote_code=True)
    except:
        return 0

    total = 0
    article_count = 0
    for article in ds:
        text = article.get("text", "")
        if not text or len(text) < 200: continue
        sentences = re.split(r'(?<=[.!?])\s+', text[:3000])
        for sent in sentences:
            sent = re.sub(r'\s+', ' ', sent.strip())
            if not (30 <= len(sent) <= 500): continue
            if any(kw in sent.lower() for kw in keywords):
                holo.ingest_text(sent, source_file=f"wiki_{lang}_{domain}.txt", amplitude=0.03)
                total += 1
        article_count += 1
        if article_count >= max_articles: break
    return total


# ═══════════════════════════════════════════════════════════════════
# INGESTION : DEEPSEEK GÉNÉRATION
# ═══════════════════════════════════════════════════════════════════

def _ingest_deepseek(holo: EnterpriseHologram, domain: str, count: int = 100) -> int:
    """Génère des faits via DeepSeek API."""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key: return 0

    import requests
    config = DOMAINS_CONFIG.get(domain, {})
    prompt = config.get("deepseek_prompt", f"Génère exactement 10 faits sur {domain}.")

    total = 0
    for batch in range(0, count, 10):
        try:
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "Tu es un générateur de connaissances factuelles. Réponds UNIQUEMENT avec les faits demandés, un par ligne, sans numérotation ni introduction."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 400, "temperature": 0.5,
                },
                timeout=20,
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                for line in text.split("\n"):
                    line = line.strip().lstrip("0123456789.-)• ").strip()
                    if len(line) > 30:
                        holo.ingest_text(line, source_file=f"deepseek_{domain}.txt", amplitude=0.03)
                        total += 1
            time.sleep(0.3)
        except: break
    return total


# ═══════════════════════════════════════════════════════════════════
# INGESTION : FICHIERS LOCAUX
# ═══════════════════════════════════════════════════════════════════

def _ingest_local(holo: EnterpriseHologram, domain: str) -> int:
    """Ingère les fichiers corpus locaux filtrés par mots-clés."""
    config = DOMAINS_CONFIG.get(domain, {})
    keywords = config.get("keywords", [])

    patterns = [
        os.path.join(CORPUS_DIR, f"corpus_{domain}*.txt"),
        os.path.join(CORPUS_DIR, f"wiki_*_{domain}*.txt"),
        os.path.join(CORPUS_DIR, f"gen_{domain}*.txt"),
        os.path.join(CORPUS_DIR, "corpus_all.txt"),
    ]

    total = 0
    seen = set()
    for pattern in patterns:
        for fp in glob.glob(pattern):
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        h = hash(line)
                        if h in seen or len(line) < 30: continue
                        seen.add(h)
                        if any(kw in line.lower() for kw in keywords):
                            holo.ingest_text(line, source_file=os.path.basename(fp), amplitude=0.03)
                            total += 1
            except: pass
    return total


# ═══════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description="Pipeline d'ingestion industrielle tous domaines")
    p.add_argument("--domain", type=str, default=None, help="Domaine spécifique")
    p.add_argument("--benchmark", action="store_true", help="Benchmark après ingestion")
    p.add_argument("--wiki-articles", type=int, default=50, help="Articles Wikipedia par langue")
    p.add_argument("--deepseek-count", type=int, default=100, help="Faits DeepSeek par domaine")
    args = p.parse_args()

    print("=" * 70)
    print("  PIPELINE D'INGESTION INDUSTRIELLE — TOUS DOMAINES")
    print("=" * 70)

    domains_to_process = [args.domain] if args.domain else list(DOMAINS_CONFIG.keys())

    grand_total = 0
    for domain in domains_to_process:
        config = DOMAINS_CONFIG.get(domain)
        if not config: continue

        print(f"\n{'─' * 70}")
        print(f"  [{config.get('name', domain)}] — Ingestion industrielle")
        print(f"{'─' * 70}")

        holo = EnterpriseHologram(domain=domain, company_name="KA-Knowledge-Base")

        # Source 1 : API (si configurée)
        if config.get("api_fn"):
            fn = globals().get(config["api_fn"])
            if fn:
                n = fn(holo) or 0
                if n > 0:
                    print(f"  API          : {n:>8} faits")

        # Source 2 : Wikipedia streaming (si configuré)
        for lang in config.get("wiki_langs", []):
            n = _ingest_wiki_stream(holo, domain, lang, max_articles=args.wiki_articles)
            if n > 0:
                print(f"  Wikipedia {lang} : {n:>8} faits")

        # Source 3 : DeepSeek
        n = _ingest_deepseek(holo, domain, count=args.deepseek_count)
        if n > 0:
            print(f"  DeepSeek     : {n:>8} faits")

        # Source 4 : Fichiers locaux
        n = _ingest_local(holo, domain)
        if n > 0:
            print(f"  Fichiers locaux : {n:>6} faits")

        grand_total += holo.total_ingested
        print(f"  → Total [{domain}] : {holo.total_ingested:,} faits | Énergie : {holo.energy:.2f}")

    print(f"\n{'=' * 70}")
    print(f"  INGESTION TERMINÉE — {len(domains_to_process)} domaines")
    print(f"  Total tous domaines : {grand_total:,} faits")
    print(f"{'=' * 70}")

    if args.benchmark:
        print("\n" + "=" * 70)
        print("  BENCHMARK (1 question par domaine)")
        print("=" * 70)
        for domain in domains_to_process:
            config = DOMAINS_CONFIG.get(domain, {})
            kw = config.get("keywords", [domain])[0]
            q = f"Qu'est-ce que {kw} ?"
            holo = EnterpriseHologram(domain=domain, company_name="KA-Knowledge-Base")
            results = holo.query(q, k=1)
            score = results[0]['score'] if results else 0
            print(f"  [{domain:15s}] {q[:50]:50s} → Score: {score:.3f}")

    print(f"\n  Pour lancer avec l'hologramme principal :")
    print(f"    python ka_next_v3.py --serve")

if __name__ == "__main__":
    main()