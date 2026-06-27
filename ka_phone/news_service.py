#!/usr/bin/env python3
"""
NEWS SERVICE — Actualites en temps reel pour KA Phone
========================================================
Recupere les titres d'actualite via des flux RSS publics (gratuits, legaux)
et les injecte dans QuickFacts pour reponse immediate.

Sources :
  - France24 (RSS flash actus)
  - Google News FR (scraping RSS)
  - Euronews FR
  - Wikinews FR

Fonctionnement :
  1. fetch_news() → telecharge les titres RSS
  2. format_facts() → les convertit en format QuickFacts
  3. Injection temporaire dans le pipeline de reponse

Usage :
  from news_service import NewsService
  news = NewsService()
  headlines = news.fetch_headlines()  # Liste de titres
  answer = news.get_news_summary()    # Resume formate

Integration dans unified_server :
  if prompt match "actualite|news|dernieres nouvelles" → news_service
"""

import os, sys, json, re, time, urllib.request, urllib.error, xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "news")
CACHE_FILE = os.path.join(DATA_DIR, "news_cache.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# SOURCES RSS
# ══════════════════════════════════════════════════════════════════════════

RSS_SOURCES = [
    {
        "name": "France24",
        "url": "https://www.france24.com/fr/rss",
        "language": "fr",
    },
    {
        "name": "Euronews FR",
        "url": "https://fr.euronews.com/rss",
        "language": "fr",
    },
    {
        "name": "Le Monde (titres)",
        "url": "https://www.lemonde.fr/rss/en_continu.xml",
        "language": "fr",
    },
    {
        "name": "Wikinews FR",
        "url": "https://fr.wikinews.org/w/api.php?action=feedrecentchanges&feedformat=rss",
        "language": "fr",
    },
    {
        "name": "RFI Monde",
        "url": "https://www.rfi.fr/fr/monde/rss",
        "language": "fr",
    },
]


class NewsService:
    """Service d'actualites pour KA Phone."""

    def __init__(self, cache_ttl_minutes: int = 60):
        self.cache_ttl = cache_ttl_minutes
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        if not os.path.exists(CACHE_FILE):
            return {"headlines": [], "fetched_at": None}
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"headlines": [], "fetched_at": None}

    def _save_cache(self, headlines: List[Dict]):
        self.cache = {
            "headlines": headlines,
            "fetched_at": datetime.now().isoformat(),
        }
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _is_cache_valid(self) -> bool:
        if not self.cache.get("fetched_at"):
            return False
        fetched = datetime.fromisoformat(self.cache["fetched_at"])
        return (datetime.now() - fetched) < timedelta(minutes=self.cache_ttl)

    def fetch_headlines(self, max_per_source: int = 10, force_refresh: bool = False) -> List[Dict]:
        """
        Recupere les titres d'actualite depuis les flux RSS.
        Utilise le cache si disponible et non expire.

        Retourne une liste de {"title": str, "source": str, "url": str, "date": str}
        """
        if not force_refresh and self._is_cache_valid():
            return self.cache.get("headlines", [])

        all_headlines = []

        for source in RSS_SOURCES:
            try:
                req = urllib.request.Request(
                    source["url"],
                    headers={"User-Agent": "KA-Phone-News/1.0", "Accept": "application/rss+xml, text/xml"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content = resp.read().decode("utf-8", errors="ignore")

                # Parser RSS
                root = ET.fromstring(content)

                # Gérer les deux formats RSS
                items = []
                for item in root.iter("item"):
                    title_el = item.find("title")
                    link_el = item.find("link")
                    pubdate_el = item.find("pubDate")

                    title = title_el.text.strip() if title_el is not None and title_el.text else ""
                    link = link_el.text.strip() if link_el is not None and link_el.text else ""
                    pubdate = pubdate_el.text.strip() if pubdate_el is not None and pubdate_el.text else ""

                    if title and len(title) > 10:
                        # Nettoyer le titre
                        title = re.sub(r'\s+', ' ', title).strip()
                        items.append({
                            "title": title,
                            "url": link,
                            "source_name": source["name"],
                            "date": pubdate,
                        })

                # Prendre les N premiers
                all_headlines.extend(items[:max_per_source])

            except Exception as e:
                print(f"  [News] Erreur RSS {source['name']}: {str(e)[:80]}")
                continue

        # Deduplication simple
        seen_titles = set()
        unique = []
        for h in all_headlines:
            title_clean = re.sub(r'[^a-z0-9]', '', h["title"].lower())[:40]
            if title_clean not in seen_titles:
                seen_titles.add(title_clean)
                unique.append(h)

        # Limiter a 30 titres
        unique = unique[:30]

        self._save_cache(unique)
        return unique

    def get_news_summary(self, force_refresh: bool = False) -> str:
        """
        Retourne un resume formate de l'actualite pour reponse utilisateur.

        Exemple : "Voici les dernieres actualites : ..."
        """
        headlines = self.fetch_headlines(force_refresh=force_refresh)

        if not headlines:
            return ("Je n'ai pas pu recuperer les actualites pour le moment. "
                    "Verifie ta connexion internet et reessaie dans quelques minutes.")

        # Grouper par source
        summary_parts = ["Voici les dernieres actualites :\n"]
        for h in headlines[:15]:
            source_tag = f"[{h['source_name']}]"
            summary_parts.append(f"  {source_tag} {h['title']}")

        if len(headlines) > 15:
            summary_parts.append(f"  ... et {len(headlines) - 15} autres titres.")

        cache_time = self.cache.get("fetched_at", "inconnue")
        summary_parts.append(f"\n(Actualise : {cache_time[:16]})")

        return "\n".join(summary_parts)

    def answer_news_query(self, prompt: str) -> Tuple[Optional[str], float]:
        """
        Repond a une question sur l'actualite.
        Retourne (reponse, confiance) ou (None, 0) si la question ne concerne pas l'actualite.
        """
        p = prompt.lower().strip()

        # Patterns de demande d'actualite
        news_patterns = [
            r'\b(?:actualite|actualites|news|nouvelle|nouvelles|info|infos)\b.*\b(?:aujourd|jour|semaine|recent|dernier)',
            r'\b(?:dernieres?|recentes?)\b.*\b(?:actualite|news|nouvelle|info)',
            r'\bque se passe[-\s]t[-\s]il\b',
            r'\bque s[\'e]est[-\s]il passe\b',
            r'\b(?:quoi de neuf|quelles sont les news|les news|les infos)\b',
            r'\b(?:breaking|flash).*(?:info|actu|news)',
            r'\b(?:resume|resumer).*(?:actualite|actu|news)',
            r'\b(?:titre|titres).*(?:presse|journaux|actualite|actu)',
        ]

        is_news_query = any(re.search(pat, p) for pat in news_patterns)

        if not is_news_query:
            return None, 0.0

        # Chercher un sujet specifique
        specific_topics = {
            r'\b(?:guerre|conflit|guerre en)\b': None,
            r'\b(?:election|president|politique)\b': None,
            r'\b(?:sport|football|tennis|rugby|olympique)\b': None,
            r'\b(?:economie|economique|bourse|crise)\b': None,
            r'\b(?:technologie|tech|ia|intelligence artificielle)\b': None,
            r'\b(?:sante|sante|virus|pandemie|covid)\b': None,
            r'\b(?:france)\b': None,
            r'\b(?:europe|ue|union europeenne)\b': None,
            r'\b(?:etats[-\s]unis|usa|amerique|trump|biden)\b': None,
            r'\b(?:afrique)\b': None,
            r'\b(?:chine|russe|russie|ukraine)\b': None,
        }

        search_topic = None
        for pattern, _ in specific_topics.items():
            if re.search(pattern, p):
                # Extraire le mot-cle du pattern
                topic_match = re.search(r'\\b\((?:\?:)?([^)]+)\)', pattern)
                if topic_match:
                    search_topic = topic_match.group(1)
                break

        headlines = self.fetch_headlines()

        if not headlines:
            return ("Je n'ai pas pu recuperer les actualites. "
                    "Cela peut etre du a un probleme de connexion. Reessaie plus tard."), 0.3

        if search_topic:
            # Filtrer par sujet
            filtered = [h for h in headlines
                       if re.search(search_topic, h["title"], re.IGNORECASE)]
            if filtered:
                response = f"Actualites sur ce sujet :\n"
                for h in filtered[:5]:
                    response += f"  [{h['source_name']}] {h['title']}\n"
                return response, 0.75
            else:
                return (f"Je n'ai pas trouve d'actualites recentes sur ce sujet. "
                       f"Voici les titres du jour :\n" + self.get_news_summary()), 0.50

        # Resume general
        return self.get_news_summary(), 0.80


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    svc = NewsService()
    print("Test News Service")
    print("=" * 40)

    print("\n--- Fetch headlines ---")
    headlines = svc.fetch_headlines(force_refresh=True)
    print(f"  Recuperes : {len(headlines)} titres")
    for h in headlines[:5]:
        print(f"    [{h['source_name']}] {h['title'][:80]}")

    print("\n--- News summary ---")
    summary = svc.get_news_summary(force_refresh=True)
    print(summary[:300])

    print("\n--- Query: 'Quoi de neuf aujourd'hui ?' ---")
    answer, conf = svc.answer_news_query("Quoi de neuf aujourd'hui ?")
    if answer:
        print(f"  (confiance: {conf:.2f})")
        print(f"  {answer[:200]}")
    else:
        print("  Pas une question d'actualite")