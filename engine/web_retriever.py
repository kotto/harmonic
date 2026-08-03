"""
Web Retriever — Connecte l'IA Harmonique à Internet
====================================================
Recherche web, Wikipedia, actualités — sans dépendance externe.

Sources :
  - DuckDuckGo Instant Answer API (gratuit, pas de clé)
  - DuckDuckGo Lite (HTML scraping minimal — résultats de recherche)
  - Wikipedia REST API (gratuit)
  - Tavily Search API (si clé configurée, recherche optimisée IA)
  - Brave Search API (si clé configurée)

Usage :
    from web_retriever import WebRetriever

    wr = WebRetriever()
    results = wr.search_web("Qui a gagné la coupe du monde 2026 ?")
    for r in results:
        print(r['title'], '-', r['snippet'][:80])

    wiki = wr.search_wikipedia("Alan Turing")
    print(wiki['summary'])

    news = wr.get_current_news("technologie")
    for n in news:
        print(n['title'])
"""

import json
import os
import re
import time
from html.parser import HTMLParser
from typing import Dict, List, Optional
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ── Cache simple (évite de re-fetch la même requête en < 5 min) ────────────────
_CACHE: Dict[str, tuple] = {}  # query → (timestamp, results)
_CACHE_TTL = 300  # secondes


def _cached(key: str) -> Optional[List[Dict]]:
    if key in _CACHE:
        ts, results = _CACHE[key]
        if time.time() - ts < _CACHE_TTL:
            return results
        del _CACHE[key]
    return None


def _cache_set(key: str, results: List[Dict]):
    _CACHE[key] = (time.time(), results)


# ── Extraction de texte HTML basique ───────────────────────────────────────────

class _TextExtractor(HTMLParser):
    """Extrait le texte brut d'un HTML, en ignorant scripts et styles."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript'):
            self.skip = False
        if tag in ('p', 'br', 'li', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr'):
            self.text_parts.append('\n')

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text:
                self.text_parts.append(text + ' ')

    def get_text(self) -> str:
        return ''.join(self.text_parts)


def _strip_html(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    text = parser.get_text()
    # Nettoie les espaces multiples
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def _clean_snippet(text: str, max_len: int = 300) -> str:
    """Nettoie et tronque un snippet de texte."""
    # Enlever les citations répétées et artefacts
    text = re.sub(r'\\u[\da-fA-F]{4}', '', text)
    text = re.sub(r'\\n', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    if len(text) > max_len:
        # Couper au dernier espace avant max_len
        text = text[:max_len].rsplit(' ', 1)[0] + '…'
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# WEB RETRIEVER
# ═══════════════════════════════════════════════════════════════════════════════

class WebRetriever:
    """
    Récupérateur d'informations web pour l'IA harmonique.

    Sources (par ordre de priorité) :
      1. Wikipedia — encyclopédie (quand une entité est reconnue)
      2. DuckDuckGo Instant Answer — réponses directes
      3. DuckDuckGo Lite — résultats de recherche web
      4. Tavily — recherche optimisée IA (si clé configurée)
      5. Brave Search — recherche web (si clé configurée)
    """

    def __init__(
        self,
        timeout: int = 10,
        user_agent: str = None,
        tavily_key: str = None,
        brave_key: str = None,
    ):
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.tavily_key = tavily_key or os.environ.get("TAVILY_API_KEY", "")
        self.brave_key = brave_key or os.environ.get("BRAVE_API_KEY", "")

    def _get(self, url: str, timeout: int = None) -> Optional[str]:
        """GET HTTP simple avec gestion d'erreurs."""
        req = Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urlopen(req, timeout=timeout or self.timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (URLError, HTTPError, OSError) as e:
            return None

    def _get_json(self, url: str, timeout: int = None) -> Optional[dict]:
        """GET HTTP + parse JSON."""
        text = self._get(url, timeout=timeout)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. WIKIPEDIA
    # ═══════════════════════════════════════════════════════════════════════════

    def search_wikipedia(self, query: str, lang: str = "auto") -> Optional[Dict]:
        """
        Recherche une entité sur Wikipedia et retourne titre + résumé.

        Retourne None si aucun résultat pertinent.
        """
        # Déterminer la langue
        if lang == "auto":
            # Détection simple : si la query contient des accents/caractères FR
            has_fr = bool(re.search(r'[éèêëàâîïôûùçÉÈÊËÀÂÎÏÔÛÙÇ]', query))
            wiki_lang = "fr" if has_fr else "en"
        else:
            wiki_lang = lang[:2]

        cache_key = f"wiki:{wiki_lang}:{query.lower().strip()}"
        cached = _cached(cache_key)
        if cached:
            return cached[0] if cached else None

        # Étape 1 : Recherche de la page la plus pertinente
        search_url = (
            f"https://{wiki_lang}.wikipedia.org/w/api.php"
            f"?action=query&list=search&srsearch={quote_plus(query)}"
            f"&srlimit=3&format=json&srprop=snippet"
        )
        data = self._get_json(search_url)
        if not data or "query" not in data:
            return None

        search_results = data["query"].get("search", [])
        if not search_results:
            return None

        # Prendre le premier résultat et récupérer l'extrait complet
        best = search_results[0]
        title = best["title"]
        snippet_html = best.get("snippet", "")

        # Étape 2 : Récupérer l'extrait d'introduction (intro seulement)
        extract_url = (
            f"https://{wiki_lang}.wikipedia.org/w/api.php"
            f"?action=query&prop=extracts&exintro=1&explaintext=1"
            f"&titles={quote_plus(title)}&format=json"
        )
        extract_data = self._get_json(extract_url)
        summary = ""
        if extract_data and "query" in extract_data:
            pages = extract_data["query"].get("pages", {})
            for page_id, page in pages.items():
                if page_id != "-1":
                    summary = page.get("extract", "")
                    break

        if not summary:
            summary = _strip_html(snippet_html)

        result = {
            "source": "wikipedia",
            "title": title,
            "url": f"https://{wiki_lang}.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}",
            "summary": _clean_snippet(summary, max_len=2000),
            "snippet": _clean_snippet(_strip_html(snippet_html), max_len=300),
            "language": wiki_lang,
        }

        _cache_set(cache_key, [result])
        return result

    def get_wikipedia_full(self, title: str, lang: str = "fr",
                           max_chars: int = 20000, retries: int = 3) -> Optional[str]:
        """
        Extrait COMPLET d'un article Wikipedia (toutes les sections, texte
        brut via explaintext). search_wikipedia ne renvoie que l'intro
        (exintro, ~2000 chars) — l'ingestion massive a besoin de l'article
        entier. Retries avec backoff pour les pannes réseau transitoires.
        """
        import time as _time
        for attempt in range(retries):
            try:
                url = (f"https://{lang[:2]}.wikipedia.org/w/api.php"
                       f"?action=query&prop=extracts&explaintext=1"
                       f"&titles={quote_plus(title)}&format=json&redirects=1")
                data = self._get_json(url)
                if data and "query" in data:
                    pages = data["query"].get("pages", {})
                    for page_id, page in pages.items():
                        if page_id != "-1":
                            text = page.get("extract", "")
                            if text:
                                return text[:max_chars]
            except Exception:
                pass
            if attempt < retries - 1:
                _time.sleep(0.4 * (attempt + 1))
        return None

    def search_wikipedia_multiple(self, query: str, lang: str = "auto", limit: int = 3) -> List[Dict]:
        """Retourne plusieurs résultats Wikipedia."""
        if lang == "auto":
            has_fr = bool(re.search(r'[éèêëàâîïôûùçÉÈÊËÀÂÎÏÔÛÙÇ]', query))
            wiki_lang = "fr" if has_fr else "en"
        else:
            wiki_lang = lang[:2]

        search_url = (
            f"https://{wiki_lang}.wikipedia.org/w/api.php"
            f"?action=query&list=search&srsearch={quote_plus(query)}"
            f"&srlimit={limit}&format=json&srprop=snippet"
        )
        data = self._get_json(search_url)
        if not data or "query" not in data:
            return []

        results = []
        for r in data["query"].get("search", [])[:limit]:
            results.append({
                "source": "wikipedia",
                "title": r["title"],
                "url": f"https://{wiki_lang}.wikipedia.org/wiki/{quote_plus(r['title'].replace(' ', '_'))}",
                "snippet": _clean_snippet(_strip_html(r.get("snippet", "")), max_len=300),
                "language": wiki_lang,
            })
        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. DUCKDUCKGO INSTANT ANSWER
    # ═══════════════════════════════════════════════════════════════════════════

    def search_duckduckgo_instant(self, query: str) -> Optional[Dict]:
        """
        DuckDuckGo Instant Answer API — réponses directes, abstract,
        related topics, infobox.
        """
        cache_key = f"ddg:instant:{query.lower().strip()}"
        cached = _cached(cache_key)
        if cached:
            return cached[0] if cached else None

        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        data = self._get_json(url, timeout=8)
        if not data:
            return None

        # Vérifier si on a un résultat pertinent
        abstract = data.get("AbstractText", "").strip()
        answer = data.get("Answer", "").strip()
        heading = data.get("Heading", "").strip()
        definition = data.get("Definition", "").strip()
        abstract_url = data.get("AbstractURL", "")
        infobox = data.get("Infobox", {})

        # Combiner les sources d'information
        content = answer or abstract or definition
        if not content and not heading:
            # Essayer les RelatedTopics
            related = data.get("RelatedTopics", [])
            if related:
                first = related[0]
                if isinstance(first, dict):
                    content = first.get("Text", "")
                    if not heading:
                        heading = first.get("FirstURL", "").rsplit("/", 1)[-1].replace("_", " ")

        if not content and not heading:
            return None

        result = {
            "source": "duckduckgo",
            "title": heading or query,
            "url": abstract_url or f"https://duckduckgo.com/?q={quote_plus(query)}",
            "summary": _clean_snippet(content, max_len=2000) if content else "",
            "snippet": _clean_snippet(content, max_len=300) if content else "",
            "answer": answer,
            "definition": definition,
            "infobox": {k: v for k, v in (infobox or {}).items() if v} if infobox else {},
        }

        _cache_set(cache_key, [result])
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. DUCKDUCKGO LITE (web search)
    # ═══════════════════════════════════════════════════════════════════════════

    def search_duckduckgo_web(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Recherche web via DuckDuckGo Lite (version HTML épurée).
        Retourne une liste de résultats : titre, snippet, URL.
        """
        cache_key = f"ddg:web:{query.lower().strip()}"
        cached = _cached(cache_key)
        if cached:
            return cached[:max_results]

        # DuckDuckGo Lite — HTML minimal, facile à parser
        url = "https://lite.duckduckgo.com/lite/?"
        params = urlencode({"q": query})
        html = self._get(url + params, timeout=10)
        if not html:
            return []

        results = self._parse_ddg_lite(html, max_results)
        _cache_set(cache_key, results)
        return results

    def _parse_ddg_lite(self, html: str, max_results: int = 5) -> List[Dict]:
        """Parse les résultats de DuckDuckGo Lite."""
        results = []

        # Pattern pour les résultats DDG Lite :
        # <a rel="nofollow" href="URL">TITRE</a>
        # <span class="link-text">HOST</span>
        # <span class="snippet">DESCRIPTION</span>
        # Les résultats sont dans des <tr> ou séparés par des <br>

        # Pattern 1: lignes avec lien + snippet
        # Format typique de DDG Lite :
        #   <a rel="nofollow" class="result-link" href="...">Titre</a>
        #   <span class="link-text">hostname</span>
        #   <span class="snippet">description...</span>

        link_pattern = re.compile(
            r'<a[^>]*?(?:rel=["\']nofollow["\'])[^>]*?href=["\']([^"\']+)["\'][^>]*?>(.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )
        snippet_pattern = re.compile(
            r'<span[^>]*?class=["\'](?:snippet|result-snippet)["\'][^>]*?>(.*?)</span>',
            re.IGNORECASE | re.DOTALL,
        )

        links = link_pattern.findall(html)
        snippets = snippet_pattern.findall(html)

        for i, (href, title) in enumerate(links):
            if len(results) >= max_results:
                break

            # Ignorer les liens internes DuckDuckGo
            if "duckduckgo.com" in href and "/lite/" not in href:
                continue
            if href.startswith("//"):
                href = "https:" + href

            title_clean = _strip_html(title).strip()
            if not title_clean or len(title_clean) < 3:
                continue

            snippet = ""
            if i < len(snippets):
                snippet = _strip_html(snippets[i]).strip()

            results.append({
                "source": "web",
                "title": title_clean,
                "url": href,
                "snippet": _clean_snippet(snippet, max_len=300),
            })

        # Fallback si le pattern ne matche pas (format alternatif DDG Lite)
        if not results:
            results = self._parse_ddg_lite_fallback(html, max_results)

        return results

    def _parse_ddg_lite_fallback(self, html: str, max_results: int = 5) -> List[Dict]:
        """Fallback : parse toutes les balises <a> avec href http."""
        results = []
        seen_urls = set()

        # Trouver tous les liens avec URL absolue
        link_pattern = re.compile(
            r'<a[^>]*?href=["\'](https?://[^"\']+?)["\'][^>]*?>(.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )

        for href, title in link_pattern.findall(html):
            if len(results) >= max_results:
                break
            if "duckduckgo.com" in href:
                continue
            if href in seen_urls:
                continue

            title_clean = _strip_html(title).strip()
            if not title_clean or len(title_clean) < 5:
                continue
            # Ignorer les URLs qui ne sont pas des pages de contenu
            if any(href.lower().endswith(ext) for ext in ('.css', '.js', '.ico', '.png', '.jpg', '.gif', '.svg', '.woff', '.ttf')):
                continue

            seen_urls.add(href)
            results.append({
                "source": "web",
                "title": title_clean,
                "url": href,
                "snippet": "",
            })

        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. TAVILY SEARCH (si clé configurée)
    # ═══════════════════════════════════════════════════════════════════════════

    def search_tavily(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Recherche via Tavily — optimisée pour l'IA (extraction de contenu).
        Nécessite TAVILY_API_KEY dans les variables d'environnement.
        Offre gratuite : 1000 requêtes/mois.
        """
        if not self.tavily_key:
            return []

        cache_key = f"tavily:{query.lower().strip()}"
        cached = _cached(cache_key)
        if cached:
            return cached[:max_results]

        url = "https://api.tavily.com/search"
        body = json.dumps({
            "api_key": self.tavily_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": True,
        }).encode("utf-8")

        req = Request(
            url,
            data=body,
            headers={
                "User-Agent": self.user_agent,
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError, OSError, json.JSONDecodeError):
            return []

        results = []
        # Ajouter la réponse courte de Tavily si présente
        if data.get("answer"):
            results.append({
                "source": "tavily",
                "title": f"Réponse : {query}",
                "url": "",
                "snippet": _clean_snippet(data["answer"], max_len=500),
                "summary": data["answer"],
            })

        for r in data.get("results", [])[:max_results]:
            results.append({
                "source": "tavily",
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": _clean_snippet(r.get("content", ""), max_len=300),
                "raw_content": r.get("raw_content", ""),
            })

        _cache_set(cache_key, results)
        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # 5. BRAVE SEARCH (si clé configurée)
    # ═══════════════════════════════════════════════════════════════════════════

    def search_brave(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Recherche via Brave Search API.
        Nécessite BRAVE_API_KEY. Offre gratuite : 2000 requêtes/mois.
        """
        if not self.brave_key:
            return []

        cache_key = f"brave:{query.lower().strip()}"
        cached = _cached(cache_key)
        if cached:
            return cached[:max_results]

        url = f"https://api.search.brave.com/res/v1/web/search?q={quote_plus(query)}&count={max_results}"
        req = Request(url, headers={
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_key,
        })
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError, OSError, json.JSONDecodeError):
            return []

        results = []
        for r in data.get("web", {}).get("results", [])[:max_results]:
            results.append({
                "source": "brave",
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": _clean_snippet(r.get("description", ""), max_len=300),
            })

        _cache_set(cache_key, results)
        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # 6. RECHERCHE UNIFIÉE
    # ═══════════════════════════════════════════════════════════════════════════

    def search_web(
        self,
        query: str,
        max_results: int = 5,
        include_wikipedia: bool = True,
        include_web: bool = True,
        prefer_wikipedia: bool = True,
    ) -> List[Dict]:
        """
        Recherche web unifiée — combine toutes les sources disponibles.

        Ordre de priorité :
          1. Wikipedia (si pertinent)
          2. DuckDuckGo Instant Answer
          3. Tavily (si clé configurée)
          4. Brave (si clé configurée)
          5. DuckDuckGo Web Search

        Retourne une liste de résultats, chaque résultat ayant :
          - source: str       ("wikipedia", "duckduckgo", "tavily", "brave", "web")
          - title: str
          - url: str
          - snippet: str      (extrait court, max 300 caractères)
          - summary: str      (optionnel, résumé long)
        """
        all_results = []

        # 1. Wikipedia (toujours en premier car le plus fiable)
        if include_wikipedia and prefer_wikipedia:
            wiki = self.search_wikipedia(query)
            if wiki:
                all_results.append(wiki)

        # 2. DuckDuckGo Instant Answer
        ddg_instant = self.search_duckduckgo_instant(query)
        if ddg_instant and ddg_instant.get("snippet"):
            # Éviter les doublons avec Wikipedia
            if not all_results or ddg_instant["title"].lower() != all_results[0]["title"].lower():
                all_results.append(ddg_instant)

        # 3. Tavily (si disponible)
        if self.tavily_key:
            tavily_results = self.search_tavily(query, max_results=max_results)
            for r in tavily_results:
                if len(all_results) >= max_results + 1:
                    break
                if not any(existing["url"] == r["url"] for existing in all_results if r["url"]):
                    all_results.append(r)

        # 4. Brave (si disponible)
        if self.brave_key:
            brave_results = self.search_brave(query, max_results=max_results)
            for r in brave_results:
                if len(all_results) >= max_results + 1:
                    break
                if not any(existing["url"] == r["url"] for existing in all_results if r["url"]):
                    all_results.append(r)

        # 5. DuckDuckGo Web (fallback gratuit)
        if include_web and len(all_results) < max_results:
            web_results = self.search_duckduckgo_web(query, max_results=max_results)
            for r in web_results:
                if len(all_results) >= max_results + 1:
                    break
                if not any(
                    existing.get("url") == r["url"]
                    for existing in all_results
                    if r["url"] and existing.get("url")
                ):
                    all_results.append(r)

        # Si Wikipedia n'a pas été cherché en premier, le faire en fallback
        if include_wikipedia and not prefer_wikipedia and len(all_results) < 2:
            wiki = self.search_wikipedia(query)
            if wiki and not any(
                existing.get("title", "").lower() == wiki["title"].lower()
                for existing in all_results
            ):
                all_results.insert(0, wiki)

        return all_results[:max_results]

    def search_quick(self, query: str) -> Optional[str]:
        """
        Recherche rapide — retourne le meilleur résumé textuel trouvé,
        ou None si rien de pertinent.
        """
        results = self.search_web(query, max_results=3)
        for r in results:
            # Prioriser les résumés longs
            summary = r.get("summary") or r.get("snippet") or ""
            if len(summary) > 50:
                return summary
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # 7. ACTUALITÉS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_current_news(self, topic: str = None, max_results: int = 5) -> List[Dict]:
        """
        Récupère les actualités récentes via DuckDuckGo (recherche avec
        filtre temporel implicite).

        Pour une meilleure couverture, configurer NEWSAPI_KEY ou utiliser
        Google News RSS.
        """
        query = f"news {topic}" if topic else "latest news"
        # Ajouter des termes qui favorisent les résultats récents
        query += " today"

        cache_key = f"news:{query.lower().strip()}"
        cached = _cached(cache_key)
        if cached:
            return cached[:max_results]

        # Utiliser DuckDuckGo web avec le mot-clé "news"
        url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
        html = self._get(url, timeout=10)
        if not html:
            return []

        results = self._parse_ddg_lite(html, max_results)
        # Marquer comme actualité
        for r in results:
            r["source"] = "news"

        _cache_set(cache_key, results)
        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # 8. FETCH URL
    # ═══════════════════════════════════════════════════════════════════════════

    def fetch_url(self, url: str, extract_text: bool = True) -> Optional[Dict]:
        """
        Récupère le contenu d'une URL.

        Retourne :
          - url: str
          - content_type: str
          - text: str (si extract_text=True, texte brut extrait du HTML)
          - raw_length: int
        """
        cache_key = f"fetch:{url}"
        cached = _cached(cache_key)
        if cached:
            return cached[0] if cached else None

        req = Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                content_type = resp.headers.get("Content-Type", "")
                if "text/html" in content_type or "text/plain" in content_type:
                    text = raw.decode("utf-8", errors="replace")
                    if extract_text and "text/html" in content_type:
                        text = _strip_html(text)
                        # Tronquer à 50K caractères
                        if len(text) > 50000:
                            text = text[:50000] + "…"
                    result = {
                        "url": url,
                        "content_type": content_type,
                        "text": text,
                        "raw_length": len(raw),
                    }
                    _cache_set(cache_key, [result])
                    return result
                else:
                    return {
                        "url": url,
                        "content_type": content_type,
                        "text": f"[Contenu binaire : {content_type}, {len(raw)} octets]",
                        "raw_length": len(raw),
                    }
        except (URLError, HTTPError, OSError) as e:
            return {"url": url, "error": str(e), "text": ""}

    # ── Wikipedia Full Article ───────────────────────────────────────────

    def fetch_wikipedia_full(self, title: str, lang: str = "fr") -> Optional[str]:
        """
        Récupère le contenu COMPLET d'un article Wikipedia (pas juste l'intro).

        Args:
            title: Titre exact de l'article Wikipedia
            lang: Code langue ('fr', 'en', ...)

        Returns:
            Texte complet de l'article (max 50000 caractères), ou None.
        """
        cache_key = f"wiki:full:{lang}:{title.lower().strip()}"
        cached = _cached(cache_key)
        if cached:
            return cached[0] if cached else None

        import urllib.request
        from urllib.parse import quote_plus

        url = (
            f"https://{lang}.wikipedia.org/w/api.php"
            f"?action=query&prop=extracts&explaintext=1"
            f"&titles={quote_plus(title)}&format=json"
        )

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": self.user_agent
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                import json as json_mod
                data = json_mod.loads(resp.read().decode('utf-8'))
        except Exception:
            return None

        if "query" in data and "pages" in data["query"]:
            pages = data["query"]["pages"]
            for page_id, page in pages.items():
                if page_id != "-1":
                    text = page.get("extract", "")
                    if text and len(text) > 100:
                        # Limiter à 50K caractères
                        if len(text) > 50000:
                            text = text[:50000] + "…"
                        _cache_set(cache_key, [text])
                        return text

        return None

    def search_wikipedia_links(self, title: str, lang: str = "fr") -> List[str]:
        """
        Récupère les titres des articles liés d'une page Wikipedia
        (liens internes, pas juste "Voir aussi").

        Args:
            title: Titre exact de l'article
            lang: Code langue

        Returns:
            Liste de titres d'articles liés (max 30).
        """
        cache_key = f"wiki:links:{lang}:{title.lower().strip()}"
        cached = _cached(cache_key)
        if cached:
            return list(cached)

        import urllib.request
        from urllib.parse import quote_plus

        url = (
            f"https://{lang}.wikipedia.org/w/api.php"
            f"?action=parse&page={quote_plus(title)}"
            f"&prop=links&format=json&pllimit=30"
        )

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": self.user_agent
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                import json as json_mod
                data = json_mod.loads(resp.read().decode('utf-8'))
        except Exception:
            return []

        links = []
        if "parse" in data and "links" in data["parse"]:
            for link in data["parse"]["links"]:
                linked_title = link.get("*", "")
                # Filtrer les namespaces non-articles (Aide:, Catégorie:, etc.)
                if (linked_title and
                    ":" not in linked_title and
                    linked_title != title):
                    links.append(linked_title)

        links = links[:30]
        _cache_set(cache_key, links)
        return links


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE CONVENANCE (pour import rapide)
# ═══════════════════════════════════════════════════════════════════════════════

_global_retriever: Optional[WebRetriever] = None


def _get_retriever() -> WebRetriever:
    global _global_retriever
    if _global_retriever is None:
        _global_retriever = WebRetriever()
    return _global_retriever


def search_web(query: str, max_results: int = 5) -> List[Dict]:
    """Recherche web rapide (utilise le retriever global)."""
    return _get_retriever().search_web(query, max_results=max_results)


def search_wikipedia(query: str, lang: str = "auto") -> Optional[Dict]:
    """Recherche Wikipedia rapide."""
    return _get_retriever().search_wikipedia(query, lang=lang)


def search_quick(query: str) -> Optional[str]:
    """Recherche rapide — retourne le meilleur résumé textuel."""
    return _get_retriever().search_quick(query)


def get_news(topic: str = None, max_results: int = 5) -> List[Dict]:
    """Actualités récentes."""
    return _get_retriever().get_current_news(topic=topic, max_results=max_results)


def fetch_url(url: str) -> Optional[Dict]:
    """Récupère le contenu d'une URL."""
    return _get_retriever().fetch_url(url)


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  WEB RETRIEVER — Test")
    print("=" * 60)

    wr = WebRetriever()

    # Test 1 : Wikipedia
    print("\n── Test Wikipedia ──")
    wiki = wr.search_wikipedia("Alan Turing")
    if wiki:
        print(f"  Titre : {wiki['title']}")
        print(f"  Résumé : {wiki['summary'][:200]}…")
    else:
        print("  ❌ Aucun résultat Wikipedia")

    # Test 2 : DuckDuckGo Instant
    print("\n── Test DuckDuckGo Instant ──")
    ddg = wr.search_duckduckgo_instant("What is quantum computing")
    if ddg:
        print(f"  Titre : {ddg['title']}")
        print(f"  Snippet : {ddg['snippet'][:150]}…")
    else:
        print("  ❌ Aucun résultat DDG Instant")

    # Test 3 : Recherche web
    print("\n── Test Recherche Web ──")
    web_results = wr.search_web("Python programming language latest version 2026", max_results=3)
    for i, r in enumerate(web_results):
        print(f"  {i+1}. [{r['source']}] {r['title']}")
        if r.get("snippet"):
            print(f"     {r['snippet'][:100]}…")

    # Test 4 : Actualités
    print("\n── Test Actualités ──")
    news = wr.get_current_news("technology", max_results=3)
    for i, n in enumerate(news):
        print(f"  {i+1}. {n['title']}")
        if n.get("snippet"):
            print(f"     {n['snippet'][:100]}…")

    print("\n✅ Tests terminés")
