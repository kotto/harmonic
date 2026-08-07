"""
Enrichment Pipeline — Orchestrateur d'enrichissement massif du KB
===================================================================
Coordonne toutes les sources d'enrichissement en un pipeline unifié.

SOURCES :
  Niveau 1 — Wikidata SPARQL (25 catégories, 100K+ faits)
  Niveau 2 — Wikipedia Mass Extraction (20K articles, 500K faits)
  Niveau 3 — Web Crawl Ciblé (santé, sciences, 50K+ faits)
  Niveau 4 — Enrichissement Curé (200 sujets)
  Niveau 5 — Auto-apprentissage Continu

PIPELINE :
  Source → Extraction → Sectorisation → Déduplication → Filtrage Qualité → ShardedKB

Usage :
    from enrichment_pipeline import EnrichmentPipeline

    pipeline = EnrichmentPipeline(shard_dir='data/kb_enriched')
    
    # Pipeline complet
    pipeline.run_full(target_facts=500_000)
    
    # Niveau spécifique
    pipeline.run_wikidata()
    pipeline.run_wikipedia(max_articles=5000)
    pipeline.run_web_crawl(domains=['sante', 'sciences'])
    
    # Rapport
    pipeline.report()
"""

import json, os, sys, time, logging
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field

import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineStats:
    """Statistiques du pipeline d'enrichissement."""
    wikidata_fetched: int = 0
    wikidata_ingested: int = 0
    wikipedia_articles: int = 0
    wikipedia_facts: int = 0
    web_crawl_pages: int = 0
    web_crawl_facts: int = 0
    curated_topics: int = 0
    total_ingested: int = 0
    total_deduplicated: int = 0
    total_filtered_out: int = 0
    sectors: Counter = field(default_factory=Counter)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def elapsed_minutes(self) -> float:
        return (self.end_time - self.start_time) / 60.0 if self.end_time else 0.0

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "  📊 PIPELINE STATISTICS",
            "=" * 60,
            f"  Wikidata      : {self.wikidata_fetched:,} fetched → {self.wikidata_ingested:,} ingested",
            f"  Wikipedia     : {self.wikipedia_articles:,} articles → {self.wikipedia_facts:,} facts",
            f"  Web Crawl     : {self.web_crawl_pages:,} pages → {self.web_crawl_facts:,} facts",
            f"  Curated       : {self.curated_topics:,} topics",
            f"  ─────────────────────────────────",
            f"  Total ingested: {self.total_ingested:,}",
            f"  Deduplicated  : {self.total_deduplicated:,}",
            f"  Filtered out  : {self.total_filtered_out:,}",
            f"  ⏱️  Duration    : {self.elapsed_minutes:.1f} min",
        ]
        if self.sectors:
            lines.append("  ─────────────────────────────────")
            for sector, count in self.sectors.most_common(10):
                pct = 100 * count / max(self.total_ingested, 1)
                lines.append(f"  {sector:20s}: {count:>8,} ({pct:5.1f}%)")
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class EnrichmentPipeline:
    """
    Orchestrateur d'enrichissement massif du KB harmonique.

    Coordonne Wikidata SPARQL, Wikipedia, web crawl, et enrichissement curé
    en un pipeline unifié avec sectorisation et filtrage qualité.
    """

    def __init__(self, shard_dir: str = 'data/kb_enriched',
                 max_active_shards: int = 3):
        self.shard_dir = Path(shard_dir)
        self.shard_dir.mkdir(parents=True, exist_ok=True)

        self.kb = None
        self.stats = PipelineStats()

        # Initialiser le ShardedKB (lazy)
        self._init_kb(max_active_shards)

    def _init_kb(self, max_active: int):
        """Initialise le ShardedKB."""
        try:
            from kb_scaler import ShardedKB
            self.kb = ShardedKB(
                shard_dir=str(self.shard_dir),
                max_active=max_active,
            )
            log.info(f"ShardedKB initialisé: {self.shard_dir}")
        except Exception as e:
            log.warning(f"ShardedKB non disponible: {e}")
            self.kb = None

    # ═══════════════════════════════════════════════════════════════════════════
    # NIVEAU 1 : WIKIDATA SPARQL
    # ═══════════════════════════════════════════════════════════════════════════

    def run_wikidata(self, target: int = 100_000, categories: Optional[List[str]] = None) -> int:
        """
        Exécute l'ingestion Wikidata SPARQL (25 catégories).

        Args:
            target: nombre maximum de faits à ingérer
            categories: liste de noms de catégories (None = toutes)

        Returns:
            Nombre de faits ingérés
        """
        log.info(f"📡 Niveau 1 — Wikidata SPARQL (target: {target:,})")

        if not self.kb:
            log.error("ShardedKB non initialisé")
            return 0

        try:
            from wikidata_real_ingest import ingest_all, QUERIES
        except ImportError:
            log.error("wikidata_real_ingest.py non trouvé")
            return 0

        # Filtrer les catégories si spécifié
        if categories:
            import wikidata_real_ingest as wri
            original_queries = dict(wri.QUERIES)
            wri.QUERIES = {k: v for k, v in original_queries.items() if k in categories}

        try:
            count = ingest_all(self.kb, target=target)
            self.stats.wikidata_fetched = count
            self.stats.wikidata_ingested = count
            self.stats.total_ingested += count
            log.info(f"✅ Wikidata: {count:,} faits ingérés")
        finally:
            if categories:
                import wikidata_real_ingest as wri
                wri.QUERIES = original_queries

        return count

    # ═══════════════════════════════════════════════════════════════════════════
    # NIVEAU 2 : WIKIPEDIA MASS EXTRACTION
    # ═══════════════════════════════════════════════════════════════════════════

    def run_wikipedia(self, max_articles: int = 5000, languages: List[str] = None) -> int:
        """
        Extrait des faits depuis les articles Wikipedia les plus consultés.

        Args:
            max_articles: nombre maximum d'articles à traiter
            languages: ['fr', 'en'] (défaut: les deux)

        Returns:
            Nombre de faits ingérés
        """
        if languages is None:
            languages = ['fr', 'en']

        log.info(f"📚 Niveau 2 — Wikipedia ({max_articles:,} articles, langues: {languages})")

        if not self.kb:
            log.error("ShardedKB non initialisé")
            return 0

        total_facts = 0

        for lang in languages:
            log.info(f"  Traitement Wikipedia {lang.upper()}...")
            facts = self._extract_wikipedia_facts(lang, max_articles // len(languages))
            if facts:
                sectorized = self._sectorize_and_filter(facts)
                self.kb.ingest_batch(sectorized)
                total_facts += len(sectorized)
                self.stats.wikipedia_facts += len(sectorized)
                log.info(f"  ✅ Wikipedia {lang}: {len(sectorized):,} faits")

        self.stats.wikipedia_articles = max_articles
        self.stats.total_ingested += total_facts
        return total_facts

    def _extract_wikipedia_facts(self, lang: str, max_articles: int) -> List[Tuple[str, str, str, str]]:
        """
        Extrait des faits depuis Wikipedia via l'API.
        Utilise le bootstrapper pour l'extraction de triples.
        """
        facts = []

        try:
            from bootstrapper import extract_triples_enhanced
            from web_retriever import WebRetriever
            web = WebRetriever()
        except ImportError:
            log.warning("Bootstrapper ou WebRetriever non disponible")
            return facts

        # Récupérer les articles les plus consultés (via Wikipedia API)
        wiki_api = f"https://{lang}.wikipedia.org/w/api.php"
        import urllib.request, urllib.parse

        # Récupérer les titres des articles populaires
        params = urllib.parse.urlencode({
            'action': 'query',
            'format': 'json',
            'list': 'mostviewed',
            'pvimlimit': min(max_articles, 500),
        })

        try:
            url = f"{wiki_api}?{params}"
            req = urllib.request.Request(url, headers={'User-Agent': 'HarmonicAI/3.3'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                articles = data.get('query', {}).get('mostviewed', [])
        except Exception as e:
            log.warning(f"Wikipedia API error: {e}")
            articles = []

        if not articles:
            # Fallback: utiliser les articles prédéfinis
            fallback_titles = {
                'fr': [
                    'France', 'Paris', 'Seconde_Guerre_mondiale', 'Napoléon_Ier',
                    'Révolution_française', 'Louis_XIV', 'Histoire_de_France',
                    'Soleil', 'Terre', 'Lune', 'Eau', 'Air', 'Feu',
                    'Albert_Einstein', 'Isaac_Newton', 'Marie_Curie', 'Galilée',
                    'ADN', 'Évolution_(biologie)', 'Cellule_(biologie)',
                    'Cœur', 'Cerveau', 'Poumon', 'Cancer', 'Diabète',
                    'Internet', 'Ordinateur', 'Intelligence_artificielle',
                    'Philosophie', 'Art', 'Musique', 'Littérature_française',
                ],
                'en': [
                    'Earth', 'Sun', 'Moon', 'Water', 'Air',
                    'Albert_Einstein', 'Isaac_Newton', 'Marie_Curie', 'Galileo_Galilei',
                    'DNA', 'Evolution', 'Cell_(biology)',
                    'Heart', 'Brain', 'Lung', 'Cancer', 'Diabetes',
                    'Internet', 'Computer', 'Artificial_intelligence',
                    'Philosophy', 'Art', 'Music', 'Literature',
                    'World_War_II', 'Napoleon', 'French_Revolution',
                ],
            }
            articles = [{'title': t} for t in fallback_titles.get(lang, fallback_titles['en'])[:max_articles]]

        log.info(f"    {len(articles)} articles à traiter")

        for i, article in enumerate(articles[:max_articles]):
            title = article.get('title', '')
            if not title:
                continue

            try:
                # Récupérer le contenu de l'article
                params = urllib.parse.urlencode({
                    'action': 'query',
                    'format': 'json',
                    'titles': title,
                    'prop': 'extracts',
                    'exintro': 1,
                    'explaintext': 1,
                })
                url = f"{wiki_api}?{params}"
                req = urllib.request.Request(url, headers={'User-Agent': 'HarmonicAI/3.3'})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    pages = data.get('query', {}).get('pages', {})
                    for page_id, page_data in pages.items():
                        extract = page_data.get('extract', '')
                        if extract and len(extract) > 100:
                            # Extraire les triples
                            triples = extract_triples_enhanced(extract)
                            for s, r, o, sec in triples:
                                if len(s) >= 2 and len(r) >= 2 and len(o) >= 2:
                                    facts.append((s, r, o, sec))

            except Exception:
                pass

            if (i + 1) % 100 == 0:
                log.info(f"    {i+1}/{len(articles)} articles traités, {len(facts)} faits")

        return facts

    # ═══════════════════════════════════════════════════════════════════════════
    # NIVEAU 3 : WEB CRAWL CIBLÉ
    # ═══════════════════════════════════════════════════════════════════════════

    def run_web_crawl(self, domains: List[str] = None, max_pages: int = 100) -> int:
        """
        Crawl web ciblé sur des domaines prioritaires.

        Args:
            domains: ['sante', 'sciences', 'technologie', 'histoire', 'culture']
            max_pages: nombre max de pages à crawler par domaine

        Returns:
            Nombre de faits ingérés
        """
        if domains is None:
            domains = ['sante', 'sciences']

        log.info(f"🌐 Niveau 3 — Web Crawl ({domains}, {max_pages} pages/domaine)")

        # Requêtes de recherche par domaine
        domain_queries = {
            'sante': [
                'maladie symptômes traitement',
                'vaccin découverte histoire',
                'anatomie humaine organes',
                'cancer recherche traitement',
                'diabète causes complications',
                'système immunitaire fonctionnement',
                'antibiotique découverte résistance',
                'pandémie histoire santé publique',
                'cœur fonctionnement cardiovasculaire',
                'cerveau neurosciences fonctionnement',
            ],
            'sciences': [
                'physique quantique explication',
                'relativité Einstein explication',
                'évolution Darwin théorie',
                'ADN structure découverte',
                'tableau périodique éléments',
                'photosynthèse explication simple',
                'big bang univers origine',
                'tectonique plaques terre',
                'énergie renouvelable types',
                'particule élémentaire physique',
            ],
            'technologie': [
                'intelligence artificielle définition',
                'internet histoire fonctionnement',
                'ordinateur quantique explication',
                'blockchain technologie explication',
                'smartphone histoire évolution',
                'robotique applications avenir',
            ],
            'histoire': [
                'révolution française causes',
                'empire romain chute',
                'renaissance italienne art',
                'guerre mondiale causes conséquences',
                'civilisation égypte antique',
                'découverte amérique Christophe Colomb',
            ],
            'culture': [
                'impressionnisme peinture histoire',
                'jazz musique origine',
                'littérature française grands auteurs',
                'cinéma histoire évolution',
                'philosophie grecque antique',
                'architecture gothique caractéristiques',
            ],
        }

        total_facts = 0

        for domain in domains:
            queries = domain_queries.get(domain, domain_queries['sciences'])[:max_pages // 10]
            log.info(f"  Domaine: {domain} ({len(queries)} requêtes)")

            domain_facts = []
            for query in queries:
                try:
                    from web_retriever import WebRetriever
                    web = WebRetriever()
                    results = web.search_web(query)

                    for result in results[:3]:  # top 3 résultats par requête
                        snippet = result.get('snippet', '') or result.get('summary', '')
                        if snippet and len(snippet) > 100:
                            try:
                                from bootstrapper import extract_triples_enhanced
                                triples = extract_triples_enhanced(snippet)
                                for s, r, o, sec in triples:
                                    if len(s) >= 2 and len(r) >= 2 and len(o) >= 2:
                                        domain_facts.append((s, r, o, sec))
                            except Exception:
                                pass

                    time.sleep(0.5)  # respecter les rate limits
                except Exception as e:
                    log.warning(f"    Erreur requête '{query}': {e}")

            if domain_facts:
                sectorized = self._sectorize_and_filter(domain_facts)
                self.kb.ingest_batch(sectorized)
                total_facts += len(sectorized)
                self.stats.web_crawl_facts += len(sectorized)
                log.info(f"    ✅ {domain}: {len(sectorized):,} faits")

            self.stats.web_crawl_pages += len(queries) * 3

        self.stats.total_ingested += total_facts
        return total_facts

    # ═══════════════════════════════════════════════════════════════════════════
    # PIPELINE COMPLET
    # ═══════════════════════════════════════════════════════════════════════════

    def run_full(self, target_facts: int = 500_000,
                 include_wikidata: bool = True,
                 include_wikipedia: bool = True,
                 include_web_crawl: bool = False) -> PipelineStats:
        """
        Exécute le pipeline d'enrichissement complet.

        Args:
            target_facts: objectif de faits totaux
            include_wikidata: inclure le niveau Wikidata
            include_wikipedia: inclure le niveau Wikipedia
            include_web_crawl: inclure le niveau web crawl

        Returns:
            PipelineStats avec toutes les métriques
        """
        self.stats.start_time = time.time()
        log.info(f"🚀 Pipeline d'enrichissement — Objectif: {target_facts:,} faits")
        log.info(f"   Wikidata: {include_wikidata}, Wikipedia: {include_wikipedia}, "
                 f"Web Crawl: {include_web_crawl}")

        remaining = target_facts

        # Niveau 1 : Wikidata SPARQL (le plus rentable)
        if include_wikidata and remaining > 0:
            wikidata_target = min(remaining, 150_000)
            count = self.run_wikidata(target=wikidata_target)
            remaining -= count

        # Niveau 2 : Wikipedia Mass Extraction
        if include_wikipedia and remaining > 0:
            articles = min(max(100, int(remaining / 25)), 10_000)  # ~25 faits/article
            count = self.run_wikipedia(max_articles=articles)
            remaining -= count

        # Niveau 3 : Web Crawl
        if include_web_crawl and remaining > 0:
            count = self.run_web_crawl(domains=['sante', 'sciences'], max_pages=50)
            remaining -= count

        # Sauvegarde finale
        if self.kb:
            try:
                self.kb.save_all()
            except Exception:
                pass

        # Mettre à jour les stats des secteurs
        self._update_sector_stats()

        self.stats.end_time = time.time()
        log.info(f"\n{self.stats.summary()}")

        return self.stats

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════════

    def _sectorize_and_filter(self, facts: List[Tuple[str, str, str, str]]) -> List[Tuple[str, str, str, str]]:
        """
        Sectorise et filtre un lot de faits.

        Étapes :
          1. Sectorisation automatique (remplace GENERAL)
          2. Déduplication (même sujet + relation + objet)
          3. Filtre qualité (longueur minimale, stopwords)
        """
        if not facts:
            return []

        # 1. Sectorisation
        try:
            from auto_sectorize import sectorize_batch
            facts = sectorize_batch(facts, min_confidence=1.5)
        except ImportError:
            pass

        # 2. Déduplication
        seen = set()
        unique = []
        for fact in facts:
            s, r, o, sec = fact
            key = (s.lower().strip()[:80], r.lower().strip()[:80],
                   str(o).lower().strip()[:100])
            if key not in seen:
                seen.add(key)
                unique.append(fact)

        dedup_count = len(facts) - len(unique)
        self.stats.total_deduplicated += dedup_count

        # 3. Filtre qualité
        stopwords = {'le', 'la', 'les', 'de', 'des', 'un', 'une', 'et', 'est',
                     'a', 'the', 'is', 'are', 'of', 'in', 'on', 'at', 'to'}
        filtered = []
        for fact in unique:
            s, r, o, sec = fact
            # Vérifier la longueur minimale
            if len(s.strip()) < 2 or len(r.strip()) < 2 or len(str(o).strip()) < 2:
                self.stats.total_filtered_out += 1
                continue
            # Vérifier que la relation n'est pas un stopword seul
            if r.lower().strip() in stopwords:
                self.stats.total_filtered_out += 1
                continue
            # Vérifier que le sujet et l'objet ne sont pas identiques
            if s.lower().strip() == str(o).lower().strip():
                self.stats.total_filtered_out += 1
                continue
            filtered.append(fact)

        return filtered

    def _update_sector_stats(self):
        """Met à jour les statistiques de distribution des secteurs."""
        if not self.kb:
            return

        try:
            sectors = Counter()
            for shard in self.kb.shards.values():
                try:
                    if hasattr(shard, '_loaded') and not shard._loaded:
                        shard.load()
                    for fact in shard.facts:
                        if hasattr(fact, 'secteur'):
                            sectors[fact.secteur] += 1
                    if hasattr(shard, 'unload'):
                        shard.unload()
                except Exception:
                    pass
            self.stats.sectors = sectors
        except Exception:
            pass

    def report(self) -> str:
        """Génère un rapport complet de l'état du pipeline."""
        self._update_sector_stats()
        return self.stats.summary()

    def estimate_kb_coverage(self, topics: List[str]) -> Dict[str, int]:
        """
        Estime la couverture du KB pour une liste de topics.

        Returns:
            {topic: nombre_de_faits_pertinents}
        """
        coverage = {}
        for topic in topics:
            count = 0
            topic_lower = topic.lower()
            if self.kb:
                try:
                    results = self.kb.retrieve(topic, top_k=100)
                    for r in results:
                        if hasattr(r, 'sujet') and topic_lower in r.sujet.lower():
                            count += 1
                except Exception:
                    pass
            coverage[topic] = count
        return coverage


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Enrichment Pipeline — KB Massif')
    parser.add_argument('--target', type=int, default=100_000,
                       help='Nombre de faits cible')
    parser.add_argument('--shard-dir', type=str, default='data/kb_enriched',
                       help='Répertoire des shards')
    parser.add_argument('--wikidata-only', action='store_true',
                       help='Niveau 1 uniquement (Wikidata)')
    parser.add_argument('--wikipedia-only', action='store_true',
                       help='Niveau 2 uniquement (Wikipedia)')
    parser.add_argument('--full', action='store_true',
                       help='Pipeline complet')
    parser.add_argument('--report', action='store_true',
                       help='Afficher uniquement le rapport')

    args = parser.parse_args()

    pipeline = EnrichmentPipeline(shard_dir=args.shard_dir)

    if args.report:
        print(pipeline.report())
    elif args.wikidata_only:
        pipeline.run_wikidata(target=args.target)
    elif args.wikipedia_only:
        pipeline.run_wikipedia(max_articles=args.target // 25)
    elif args.full:
        pipeline.run_full(target_facts=args.target)
    else:
        # Par défaut : Wikidata d'abord
        print("=" * 60)
        print("  ENRICHMENT PIPELINE")
        print("=" * 60)
        print(f"  Target: {args.target:,} faits")
        print(f"  Shards: {args.shard_dir}")
        print()
        pipeline.run_full(target_facts=args.target)
