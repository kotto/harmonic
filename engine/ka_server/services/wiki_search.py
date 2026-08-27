"""
🌊 wiki_search.py — Moteur de recherche textuelle pour le wiki OKF
==================================================================
Implémente un moteur de recherche BM25-like sur les fichiers markdown
du wiki. Complémentaire au rappel ψ : la recherche texte sert à la
découverte et à la navigation, le rappel ψ sert à la récupération
précise.

Usage :
  from ka_server.services.wiki_search import WikiSearch

  ws = WikiSearch()
  ws.index()  # ou ws.load()
  results = ws.search("capitale de la France", top_k=5)

CLI :
  python -m ka_server.services.wiki_search --search "lumière onde"
  python -m ka_server.services.wiki_search --reindex
"""

import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
WIKI_DIR = _ENGINE_DIR / 'knowledge'
INDEX_PATH = _ENGINE_DIR / 'data' / 'wiki_search_index.json'
STOPWORDS = {
    'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'est', 'sont',
    'a', 'dans', 'sur', 'pour', 'par', 'avec', 'sans', 'se', 'ce', 'que',
    'qui', 'où', 'ou', 'ne', 'pas', 'plus', 'très', 'il', 'elle', 'on',
    'nous', 'vous', 'ils', 'elles', 'au', 'aux', 'en', 'vers', 'chez',
    'ca', 'cela', 'cette', 'ces', 'cet', 'mon', 'ton', 'son', 'sa',
}


class WikiSearch:
    """
    Moteur de recherche BM25-like pour le wiki OKF.
    
    - Indexe le contenu textuel de chaque fichier
    - Scoring BM25 (saturation de fréquence, longueur de document)
    - Persistance JSON pour rechargement rapide
    """

    K1 = 1.2  # paramètre BM25 de saturation de fréquence
    B = 0.75  # paramètre BM25 de normalisation de longueur

    def __init__(self):
        self._docs: Dict[str, dict] = {}       # doc_id → {path, text, words, domain, title}
        self._doc_freq: Dict[str, float] = {}  # mot → df (nb docs contenant le mot)
        self._avg_doc_len = 0.0
        self._n_docs = 0
        self._vocab: Dict[str, list] = {}      # mot → [(doc_id, tf), ...]
        self._indexed = False

    # ── INDEXATION ──────────────────────────────────────────

    def index(self):
        """Parcourt et indexe tous les fichiers .md du wiki."""
        self._docs = {}
        self._vocab = {}
        self._doc_freq = {}

        md_files = sorted(WIKI_DIR.rglob('*.md'))
        md_files = [f for f in md_files if f.name not in (
            'README.md', 'index.md', 'log.md', '.schema.json')]
        md_files = [f for f in md_files if 'raw' not in f.parts]

        total_words = 0
        doc_lens = []

        for f in md_files:
            text = f.read_text(encoding='utf-8')
            # Retirer le frontmatter
            body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, flags=re.DOTALL)
            words = self._tokenize(body)

            doc_id = f.stem
            # Extraire le titre
            title = f.stem
            title_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()

            # Déterminer le domaine (nom du dossier parent)
            domain = f.parent.name

            self._docs[doc_id] = {
                'path': str(f.relative_to(WIKI_DIR)),
                'title': title,
                'domain': domain,
                'words': words,
                'word_count': len(words),
            }
            doc_lens.append(len(words))
            total_words += len(words)

            # Indexer les mots
            for w in set(words):
                self._vocab.setdefault(w, []).append(doc_id)

        self._n_docs = len(self._docs)
        self._avg_doc_len = total_words / max(self._n_docs, 1)

        # Calculer les fréquences documentaires
        for w, doc_ids in self._vocab.items():
            self._doc_freq[w] = len(doc_ids)

        self._indexed = True

    def _tokenize(self, text: str) -> List[str]:
        """Tokenise un texte en mots (minuscules, sans accents)."""
        tokens = re.findall(r"[a-zàâäéèêëîïôöùûüçœæ]+", text.lower())
        return [t for t in tokens if len(t) >= 2 and t not in STOPWORDS]

    # ── RECHERCHE ───────────────────────────────────────────

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float, dict]]:
        """
        Recherche les documents les plus pertinents pour une requête.
        
        Returns:
            Liste de (doc_id, score_bm25, infos_doc)
        """
        if not self._indexed:
            self.index()

        query_words = self._tokenize(query)
        if not query_words:
            return []

        # Compter les occurrences des mots de la requête dans chaque doc
        q_word_counts = Counter(query_words)

        scores = {}
        for q_word, q_count in q_word_counts.items():
            if q_word not in self._vocab:
                continue

            # IDF
            df = self._doc_freq.get(q_word, 1)
            idf = math.log((self._n_docs - df + 0.5) / (df + 0.5) + 1.0)

            # Parcourir les docs contenant ce mot
            for doc_id in self._vocab[q_word]:
                doc = self._docs[doc_id]
                tf = doc['words'].count(q_word)  # fréquence dans le document
                doc_len = doc['word_count']

                # BM25 score component
                numerator = tf * (self.K1 + 1.0)
                denominator = tf + self.K1 * (1.0 - self.B + self.B * doc_len / self._avg_doc_len)
                score_component = idf * numerator / denominator

                scores[doc_id] = scores.get(doc_id, 0.0) + score_component

        # Bonus pour le domaine (si la requête contient le nom du domaine)
        for doc_id in list(scores.keys()):
            doc = self._docs[doc_id]
            domain_words = self._tokenize(doc['domain'])
            if any(w in query_words for w in domain_words):
                scores[doc_id] *= 1.2

        # Trier
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [(doc_id, score, self._docs[doc_id]) for doc_id, score in ranked[:top_k]]

    # ── PERSISTANCE ─────────────────────────────────────────

    def save(self):
        """Sauvegarde l'index JSON."""
        data = {
            'docs': self._docs,
            'doc_freq': self._doc_freq,
            'avg_doc_len': self._avg_doc_len,
            'n_docs': self._n_docs,
            'vocab_words': {k: v for k, v in self._vocab.items()},
        }
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

    def load(self) -> bool:
        """Charge un index sauvegardé."""
        if not INDEX_PATH.exists():
            return False
        try:
            with open(INDEX_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._docs = data['docs']
            self._doc_freq = data['doc_freq']
            self._avg_doc_len = data['avg_doc_len']
            self._n_docs = data['n_docs']
            self._vocab = data['vocab_words']
            self._indexed = True
            return True
        except Exception:
            return False

    # ── STATS ───────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            'indexed': self._indexed,
            'documents': self._n_docs,
            'vocabulary': len(self._vocab),
            'avg_doc_len': round(self._avg_doc_len, 1),
        }

    def __repr__(self) -> str:
        return f"WikiSearch({self._n_docs} docs, {len(self._vocab)} mots)"


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    ws = WikiSearch()

    if '--reindex' in sys.argv:
        t0 = time.time()
        ws.index()
        ws.save()
        print(f"Indexation : {ws._n_docs} documents en {time.time()-t0:.2f}s")

    if '--search' in sys.argv:
        idx = sys.argv.index('--search')
        if idx + 1 < len(sys.argv):
            query = ' '.join(sys.argv[idx + 1:])
            if not ws.load():
                ws.index()
            t0 = time.time()
            results = ws.search(query, top_k=5)
            dt = (time.time() - t0) * 1000
            print(f"Recherche : « {query} » ({dt:.0f} ms)\n")
            for doc_id, score, info in results:
                print(f"  [{score:.3f}] [{info['domain']}] {info['title']}")
                print(f"          {info['path']}")
            if not results:
                print("  Aucun résultat.")
        else:
            print("Usage: --search \"votre requête\"")