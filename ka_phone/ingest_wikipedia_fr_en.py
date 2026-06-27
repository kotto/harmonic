#!/usr/bin/env python3
"""
KA-Next — INGESTION WIKIPEDIA + RESTCOUNTRIES (FR + EN)
==========================================================
Ingère Wikipedia FR/EN via HuggingFace streaming + RestCountries API.
Reprise automatique en cas d'incident.

Usage :
  python ingest_wikipedia_fr_en.py
  python ingest_wikipedia_fr_en.py --articles 2000
  python ingest_wikipedia_fr_en.py --skip-wiki
"""

import os, sys, time, json, re, math
sys.path.insert(0, os.path.dirname(__file__))

BASE_DIR = os.path.dirname(__file__)
CORPUS_DIR = os.path.join(BASE_DIR, "..", "data", "corpus")
STATE_FILE = os.path.join(CORPUS_DIR, ".ingestion_state.json")
os.makedirs(CORPUS_DIR, exist_ok=True)

# Reprise
state = {}
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        state = json.load(f)
    print(f"  Reprise : {state.get('progress','0')}")


def ingest_restcountries(lang="fr"):
    """250 pays via API RestCountries."""
    import urllib.request
    url = "https://restcountries.com/v3.1/all?fields=name,capital,region,subregion,population"
    print(f"\n{'='*60}")
    print(f"  RESTCOUNTRIES ({lang.upper()})")
    print(f"{'='*60}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KA-Next/3.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = json.loads(r.read().decode())
            if isinstance(raw, dict):
                countries = raw.get("data", raw.get("countries", []))
            else:
                countries = raw
    except Exception as e:
        print(f"  [!] Indisponible: {e}")
        return 0

    fp = os.path.join(CORPUS_DIR, f"countries_{lang}.txt")
    count = 0
    with open(fp, "w", encoding="utf-8") as f:
        for c in countries:
            if isinstance(c, str): continue
            n = c.get("name",{}).get("common","") if isinstance(c.get("name"), dict) else ""
            if not n: n = c.get("cca3","")
            cap = (c.get("capital") or [""])[0] if c.get("capital") else ""
            reg = (c.get("subregion","") or c.get("region","")).capitalize()
            pop = c.get("population",0) or 0
            if not n: continue
            count += 1
            if lang == "fr":
                f.write(f"{n} est un pays de {reg}.\n")
                if cap != "N/A": f.write(f"La capitale de {n} est {cap}.\n")
                f.write(f"Population de {n} : {pop:,} habitants.\n".replace(","," "))
            else:
                f.write(f"{n} is a country in {reg}.\n")
                if cap != "N/A": f.write(f"The capital of {n} is {cap}.\n")
                f.write(f"Population of {n}: {pop:,}.\n".replace(","," "))
    return len(countries)

def ingest_wiki(lang, max_articles=200):
    """Ingère Wikipedia via streaming HuggingFace."""
    import re
    print(f"\n{'='*60}")
    print(f"  WIKIPEDIA {lang.upper()} ({max_articles} articles)")
    print(f"{'='*60}")
    try:
        from datasets import load_dataset
    except ImportError:
        print("  [!] pip install datasets")
        return 0

    kw = {
        "fr": {"geography": ["capitale","pays","ville","fleuve","rivière"],
               "history": ["siècle","guerre","roi","empereur","révolution","bataille"],
               "science": ["physique","chimie","biologie","mathématique","astronomie"],
               "philosophy": ["philosophie","éthique","morale","pensée","concept"]},
        "en": {"geography": ["capital","country","city","river","ocean"],
               "history": ["century","war","king","emperor","revolution","battle"],
               "science": ["physics","chemistry","biology","mathematics","astronomy"],
               "philosophy": ["philosophy","ethics","moral","thought","concept"]},
    }
    dom_kw = kw.get(lang, kw["en"])
    
    def route(s):
        s = s.lower()
        best_d, best_sc = "general", 0
        for d, kws in dom_kw.items():
            sc = sum(1 for k in kws if k in s)
            if sc > best_sc: best_sc, best_d = sc, d
        return best_d

    files = {}
    counts = {}
    for d in list(dom_kw) + ["general"]:
        counts[d] = 0
        files[d] = open(os.path.join(CORPUS_DIR, f"wiki_{lang}_{d}.txt"), "a", encoding="utf-8")

    try:
        ds = load_dataset("wikimedia/wikipedia", f"20231101.{lang}", streaming=True, split="train", trust_remote_code=True)
    except Exception as e:
        print(f"  [!] Streaming: {e}")
        for fh in files.values(): fh.close()
        return 0

    total = 0
    article_count = 0
    for article in ds:
        text = article.get("text","")
        if not text or len(text) < 200: continue
        sentences = re.split(r'(?<=[.!?])\s+', text[:3000])
        for sent in sentences:
            sent = re.sub(r'\s+',' ',sent.strip())
            if not (30 <= len(sent) <= 500): continue
            d = route(sent)
            files[d].write(sent + "\n")
            counts[d] += 1
            total += 1
        article_count += 1
        if article_count % 50 == 0:
            print(f"  [{lang.upper()}] {article_count}/{max_articles} articles, {total} phrases")
            # Sauvegarde checkpoint tous les 50 articles
            state[f"{lang}_articles_done"] = article_count
            state[f"{lang}_phrases_total"] = total
            with open(STATE_FILE, "w") as f: json.dump(state, f)
        if article_count >= max_articles: break

    for fh in files.values(): fh.close()
    state["progress"] = f"{lang}: {article_count} articles, {total} phrases"
    with open(STATE_FILE, "w") as f: json.dump(state, f)

    print(f"  [{lang.upper()}] Terminé: {total} phrases")
    for d, cnt in sorted(counts.items(), key=lambda x:-x[1]):
        if cnt:
            fp = os.path.join(CORPUS_DIR, f"wiki_{lang}_{d}.txt")
            print(f"    {d:15s}: {cnt:6d} phrases ({os.path.getsize(fp)/1024:.0f} KB)")
    return total

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--articles", type=int, default=200)
    p.add_argument("--skip-wiki", action="store_true")
    p.add_argument("--skip-countries", action="store_true")
    args = p.parse_args()

    print("=" * 60)
    print("  KA-Next — INGESTION WIKIPEDIA + RESTCOUNTRIES")
    print("=" * 60)

    total = 0
    if not args.skip_countries:
        total += ingest_restcountries("fr")
        total += ingest_restcountries("en")
    if not args.skip_wiki:
        total += ingest_wiki("fr", max_articles=args.articles)
        total += ingest_wiki("en", max_articles=args.articles)

    print(f"\n{'='*60}")
    print(f"  Total phrases: {total:,}")
    print(f"{'='*60}")
    print("  python ingest_massive_nx64.py")
    return total

if __name__ == "__main__":
    main()