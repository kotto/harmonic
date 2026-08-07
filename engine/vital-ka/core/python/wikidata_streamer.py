"""
Wikidata Streamer — Ingestion massive temps réel (10M+ triplets)
==================================================================
Trois modes :
  1. DUMP  : parse un dump Wikidata JSON ligne par ligne (streaming)
  2. SPARQL: requêtes SPARQL par lots (100K entités par requête)
  3. API   : fetch entités populaires via REST API (top 100K+ Q-IDs)

Architecture streaming :
  · Parser ligne par ligne → jamais tout charger en mémoire
  · Buffer de 10K faits → flush vers ShardedKB
  · Multi-thread (1 parser + 1 ingester)
  · Barre de progression temps réel

Usage :
    python wikidata_streamer.py --mode dump --input latest-all.json --target 10M
    python wikidata_streamer.py --mode sparql --target 5M
    python wikidata_streamer.py --mode api --target 1M
"""

import json
import math
import os
import re
import sys
import time
import logging
import urllib.request
import urllib.parse
import urllib.error
import threading
import queue
from collections import defaultdict, Counter
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Iterator, Set

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

BUFFER_SIZE = 10_000          # faits par flush vers ShardedKB
API_BATCH_SIZE = 50           # entités par requête API
API_RATE_LIMIT = 0.15         # secondes entre requêtes (anonyme: 5/s, bot: 50/s)
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "HarmonicAI/3.2 (https://github.com/kotto/harmonic; research)"

# Secteurs mappés depuis les propriétés Wikidata
PID_TO_SECTOR = {
    17: 'GEOGRAPHIE', 31: 'GENERAL', 36: 'GEOGRAPHIE', 50: 'CREATION',
    57: 'CULTURE', 61: 'SCIENCES', 86: 'CULTURE', 131: 'GEOGRAPHIE',
    136: 'CULTURE', 170: 'CREATION', 175: 'CULTURE', 279: 'GENERAL',
    361: 'GENERAL', 495: 'CULTURE', 527: 'GENERAL', 569: 'HISTOIRE',
    570: 'HISTOIRE', 571: 'HISTOIRE', 580: 'HISTOIRE', 582: 'HISTOIRE',
    625: 'GEOGRAPHIE', 1082: 'GEOGRAPHIE', 1086: 'SCIENCES',
    2046: 'GEOGRAPHIE', 2054: 'SCIENCES', 2067: 'SCIENCES', 2076: 'SCIENCES',
}


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 1: DUMP STREAMING
# ═══════════════════════════════════════════════════════════════════════════════

class DumpStreamer:
    """Parse un dump Wikidata JSON en streaming (ligne par ligne)."""

    def __init__(self, kb, target_facts: int = 10_000_000):
        self.kb = kb
        self.target = target_facts
        self.count = 0
        self.skipped = 0
        self.buffer = []

    def stream(self, dump_path: str) -> int:
        """Stream le dump et ingère dans ShardedKB."""
        path = Path(dump_path)
        if not path.exists():
            log.error(f"Dump introuvable: {dump_path}")
            return 0

        file_size = path.stat().st_size
        log.info(f"Streaming dump: {dump_path} ({file_size/1e9:.1f} GB)")
        t0 = time.time()
        bytes_read = 0

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                bytes_read += len(line.encode('utf-8'))
                line = line.strip()
                if not line or line in ('[', ']', '[,', ',]'):
                    continue
                if line.endswith(','):
                    line = line[:-1]

                try:
                    obj = json.loads(line)
                    triples = self._extract(obj)
                    self.buffer.extend(triples)
                    self.count += len(triples)
                except (json.JSONDecodeError, KeyError):
                    self.skipped += 1
                    continue

                # Flush périodique
                if len(self.buffer) >= BUFFER_SIZE:
                    self._flush()

                # Log périodique
                if self.count > 0 and self.count % 500_000 == 0:
                    elapsed = time.time() - t0
                    rate = self.count / elapsed
                    pct = bytes_read / file_size * 100
                    log.info(f"Dump: {self.count:,} faits ({rate:.0f}/s) "
                             f"| {pct:.1f}% | shards: {self.kb.stats['shards']}")

                if self.count >= self.target:
                    break

        self._flush()  # flush final
        self.kb.save_all()

        elapsed = time.time() - t0
        log.info(f"Dump terminé: {self.count:,} faits en {elapsed:.0f}s "
                 f"({self.count/elapsed:.0f}/s) — {self.kb.stats['shards']} shards")
        return self.count

    def _extract(self, obj: dict) -> List[Tuple[str, str, str, str]]:
        """Extrait les triplets d'un objet Wikidata (format dump simplifié)."""
        triples = []
        item_label = (obj.get('itemLabel') or obj.get('item') or '').strip()
        if not item_label or len(item_label) < 2:
            return triples

        prop = (obj.get('propertyLabel') or obj.get('prop') or '').strip()
        value = (obj.get('valueLabel') or obj.get('value') or '').strip()
        pid = obj.get('propertyID') or obj.get('pid') or ''

        if prop and value:
            secteur = self._map_sector(pid, prop)
            triples.append((item_label, prop.lower(), value, secteur))

        # Champs additionnels
        extras = [
            ('instanceOfLabel', 'est une instance de', 'GENERAL'),
            ('subclassOfLabel', 'est une sous-classe de', 'GENERAL'),
            ('countryLabel', 'est situé en', 'GEOGRAPHIE'),
            ('continentLabel', 'est situé sur le continent', 'GEOGRAPHIE'),
            ('capitalLabel', 'a pour capitale', 'GEOGRAPHIE'),
            ('inceptionLabel', 'a été créé en', 'HISTOIRE'),
            ('discovererLabel', 'a été découvert par', 'SCIENCES'),
            ('creatorLabel', 'a été créé par', 'CREATION'),
            ('authorLabel', 'a pour auteur', 'CREATION'),
            ('populationLabel', 'a une population de', 'GEOGRAPHIE'),
        ]
        for field, rel, sec in extras:
            val = obj.get(field, '').strip()
            if val and len(val) > 1:
                triples.append((item_label, rel, val, sec))

        return triples

    def _map_sector(self, pid: str, prop_label: str) -> str:
        """Mappe PID ou label vers secteur harmonique."""
        try:
            pid_int = int(pid.replace('P', ''))
            if pid_int in PID_TO_SECTOR:
                return PID_TO_SECTOR[pid_int]
        except ValueError:
            pass
        prop_lower = prop_label.lower()
        for kw, sec in [
            ('pays', 'GEOGRAPHIE'), ('capitale', 'GEOGRAPHIE'), ('population', 'GEOGRAPHIE'),
            ('date', 'HISTOIRE'), ('naissance', 'HISTOIRE'), ('mort', 'HISTOIRE'),
            ('découverte', 'SCIENCES'), ('masse', 'SCIENCES'), ('température', 'SCIENCES'),
            ('auteur', 'CREATION'), ('créateur', 'CREATION'), ('compositeur', 'CULTURE'),
            ('réalisateur', 'CULTURE'), ('nombre', 'MATHS_PURES'), ('équation', 'MATHS_PURES'),
            ('espèce', 'BIOLOGIE'), ('genre', 'BIOLOGIE'),
        ]:
            if kw in prop_lower:
                return sec
        return 'GENERAL'

    def _flush(self):
        """Vide le buffer dans ShardedKB."""
        if self.buffer:
            self.kb.ingest_batch(self.buffer)
            self.buffer = []


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 2: SPARQL
# ═══════════════════════════════════════════════════════════════════════════════

class SPARQLStreamer:
    """Requêtes SPARQL par lots — extraction massive de triplets Wikidata."""

    QUERIES = {
        # Géographie : pays + capitales + populations
        'geography': """
            SELECT ?item ?itemLabel ?propertyLabel ?valueLabel WHERE {
              ?item wdt:P31 wd:Q6256.  # pays
              ?item ?prop ?value.
              ?property wikibase:directClaim ?prop.
              FILTER(?prop IN (wdt:P36, wdt:P1082, wdt:P2046, wdt:P30, wdt:P47))
              SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
            } LIMIT 50000
        """,
        # Sciences : éléments chimiques + propriétés
        'chemistry': """
            SELECT ?item ?itemLabel ?propertyLabel ?valueLabel WHERE {
              ?item wdt:P31 wd:Q11344.  # élément chimique
              ?item ?prop ?value.
              ?property wikibase:directClaim ?prop.
              FILTER(?prop IN (wdt:P1086, wdt:P246, wdt:P2054, wdt:P2076, wdt:P2067))
              SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
            } LIMIT 5000
        """,
        # Personnes célèbres
        'people': """
            SELECT ?item ?itemLabel ?propertyLabel ?valueLabel WHERE {
              ?item wdt:P31 wd:Q5.  # humain
              ?item wdt:P570 ?death.  # date de mort (personnes historiques)
              ?item ?prop ?value.
              ?property wikibase:directClaim ?prop.
              FILTER(?prop IN (wdt:P569, wdt:P19, wdt:P27, wdt:P106, wdt:P800))
              SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
            } LIMIT 100000
        """,
        # Créations culturelles
        'culture': """
            SELECT ?item ?itemLabel ?propertyLabel ?valueLabel WHERE {
              ?item wdt:P31 wd:Q11424.  # film
              ?item ?prop ?value.
              ?property wikibase:directClaim ?prop.
              FILTER(?prop IN (wdt:P57, wdt:P58, wdt:P577, wdt:P495, wdt:P136))
              SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
            } LIMIT 50000
        """,
    }

    def __init__(self, kb, target_facts: int = 5_000_000):
        self.kb = kb
        self.target = target_facts
        self.count = 0
        self.buffer = []

    def stream(self) -> int:
        """Exécute toutes les requêtes SPARQL."""
        log.info(f"SPARQL streaming: {len(self.QUERIES)} requêtes → target {self.target:,} faits")
        t0 = time.time()

        for name, query in self.QUERIES.items():
            if self.count >= self.target:
                break
            log.info(f"  SPARQL {name}...")
            triples = self._execute_query(query)
            self.buffer.extend(triples)
            self.count += len(triples)
            if len(self.buffer) >= BUFFER_SIZE:
                self._flush()
            log.info(f"    → {len(triples):,} faits (total: {self.count:,})")

        self._flush()
        self.kb.save_all()

        elapsed = time.time() - t0
        log.info(f"SPARQL terminé: {self.count:,} faits en {elapsed:.0f}s "
                 f"({self.count/elapsed:.0f}/s)")
        return self.count

    def _execute_query(self, query: str) -> List[Tuple[str, str, str, str]]:
        """Exécute une requête SPARQL et retourne les triplets."""
        url = f"{SPARQL_ENDPOINT}?format=json&query={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            log.warning(f"SPARQL error: {e}")
            return []

        triples = []
        for binding in data.get('results', {}).get('bindings', []):
            item = binding.get('itemLabel', {}).get('value', '')
            prop = binding.get('propertyLabel', {}).get('value', '')
            value = binding.get('valueLabel', {}).get('value', '')
            if item and prop and value:
                secteur = self._infer_sector(prop)
                triples.append((item, prop.lower(), value, secteur))
        return triples

    def _infer_sector(self, prop_label: str) -> str:
        prop_lower = prop_label.lower()
        for kw, sec in [('pays','GEOGRAPHIE'),('capitale','GEOGRAPHIE'),
            ('population','GEOGRAPHIE'),('date','HISTOIRE'),('masse','SCIENCES'),
            ('auteur','CREATION'),('réalisateur','CULTURE')]:
            if kw in prop_lower: return sec
        return 'GENERAL'

    def _flush(self):
        if self.buffer:
            self.kb.ingest_batch(self.buffer)
            self.buffer = []


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 3: API ENTITIES
# ═══════════════════════════════════════════════════════════════════════════════

class APIStreamer:
    """Fetch entités populaires via l'API Wikidata REST."""

    # Top 1000 Q-IDs par nombre de sitelinks (entités les plus importantes)
    TOP_QIDS_URL = "https://www.wikidata.org/w/api.php?action=query&list=mostlinked&format=json&mllimit=500"

    def __init__(self, kb, target_facts: int = 1_000_000):
        self.kb = kb
        self.target = target_facts
        self.count = 0
        self.buffer = []
        self.seen_qids: Set[str] = set()

    def stream(self) -> int:
        """Fetch les entités les plus liées et extrait leurs claims."""
        log.info(f"API streaming: target {self.target:,} faits")
        t0 = time.time()

        # Récupérer la liste des Q-IDs les plus importants
        qids = self._fetch_top_qids()
        log.info(f"  {len(qids)} Q-IDs à traiter")

        for i, qid in enumerate(qids):
            if self.count >= self.target:
                break

            triples = self._fetch_entity_triples(qid)
            self.buffer.extend(triples)
            self.count += len(triples)

            if len(self.buffer) >= BUFFER_SIZE:
                self._flush()

            if (i + 1) % 100 == 0:
                elapsed = time.time() - t0
                log.info(f"API: {i+1}/{len(qids)} entités → {self.count:,} faits "
                         f"({self.count/elapsed:.0f}/s)")
            time.sleep(API_RATE_LIMIT)

        self._flush()
        self.kb.save_all()
        return self.count

    def _fetch_top_qids(self, limit: int = 5000) -> List[str]:
        """Récupère les Q-IDs les plus liés."""
        qids = []
        for offset in range(0, limit, 500):
            url = f"{self.TOP_QIDS_URL}&mloffset={offset}"
            data = self._get_json(url)
            if data:
                for page in data.get('query', {}).get('mostlinked', []):
                    qid = page.get('title', '')
                    if qid.startswith('Q') and qid not in self.seen_qids:
                        qids.append(qid)
                        self.seen_qids.add(qid)
            time.sleep(0.5)
        return qids[:limit]

    def _fetch_entity_triples(self, qid: str) -> List[Tuple[str, str, str, str]]:
        """Fetch une entité et extrait ses claims."""
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        data = self._get_json(url)
        if not data:
            return []

        entities = data.get('entities', {})
        entity = entities.get(qid, {})
        labels = entity.get('labels', {})
        item_label = (labels.get('fr', {}).get('value') or
                      labels.get('en', {}).get('value') or qid)
        claims = entity.get('claims', {})

        triples = []
        for pid, claim_list in claims.items():
            prop_label = self._get_label(entities, pid)
            if not prop_label:
                continue

            for claim in claim_list:
                mainsnak = claim.get('mainsnak', {})
                if mainsnak.get('snaktype') != 'value':
                    continue
                datavalue = mainsnak.get('datavalue', {})
                value = datavalue.get('value', {})

                val_str = self._extract_value(value, entities)
                if val_str:
                    secteur = PID_TO_SECTOR.get(
                        int(pid.replace('P', '')), 'GENERAL'
                    )
                    triples.append((item_label, prop_label.lower(), val_str, secteur))

        return triples

    def _get_label(self, entities: dict, qid: str) -> Optional[str]:
        entity = entities.get(qid, {})
        labels = entity.get('labels', {})
        return labels.get('fr', {}).get('value') or labels.get('en', {}).get('value')

    def _extract_value(self, value: dict, entities: dict) -> Optional[str]:
        if isinstance(value, dict):
            if 'id' in value:
                return self._get_label(entities, value['id'])
            if 'amount' in value:
                unit = value.get('unit', '').split('/')[-1]
                amt = value['amount'].lstrip('+')
                return f"{amt} {unit}" if unit else amt
            if 'time' in value:
                return value['time'].lstrip('+').split('T')[0]
        return str(value) if value else None

    def _get_json(self, url: str) -> Optional[dict]:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception:
            return None

    def _flush(self):
        if self.buffer:
            self.kb.ingest_batch(self.buffer)
            self.buffer = []


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse, tempfile
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    parser = argparse.ArgumentParser(description="Wikidata Streamer — 10M+ faits")
    parser.add_argument('--mode', choices=['dump','sparql','api','synth'],
                        default='synth', help="Mode d'ingestion")
    parser.add_argument('--input', type=str, help="Chemin dump Wikidata JSON")
    parser.add_argument('--target', type=int, default=1_000_000,
                        help="Nombre cible de faits (défaut: 1M)")
    parser.add_argument('--shard-dir', type=str, default=None,
                        help="Répertoire des shards")
    args = parser.parse_args()

    from kb_scaler import ShardedKB

    shard_dir = args.shard_dir or str(Path(__file__).parent / 'data' / 'kb_shards')
    kb = ShardedKB(shard_dir=shard_dir, max_active=3)

    print("=" * 60)
    print(f"  WIKIDATA STREAMER — mode={args.mode}, target={args.target:,}")
    print("=" * 60)

    t0 = time.time()

    if args.mode == 'dump':
        if not args.input:
            print("  ❌ --input requis pour le mode dump")
            sys.exit(1)
        streamer = DumpStreamer(kb, target_facts=args.target)
        streamer.stream(args.input)

    elif args.mode == 'sparql':
        streamer = SPARQLStreamer(kb, target_facts=args.target)
        streamer.stream()

    elif args.mode == 'api':
        streamer = APIStreamer(kb, target_facts=args.target)
        streamer.stream()

    elif args.mode == 'synth':
        from wikidata_connector import generate_synthetic_facts
        print("  Génération synthétique...")
        t_gen = time.time()
        facts = list(generate_synthetic_facts(args.target))
        print(f"  {len(facts):,} faits générés en {time.time()-t_gen:.1f}s")
        print("  Ingestion dans ShardedKB...")
        kb.ingest_batch(facts)
        kb.save_all()

    elapsed = time.time() - t0
    stats = kb.stats
    print()
    print(f"  ✅ {stats['total_facts']:,} faits dans {stats['shards']} shards")
    print(f"  ⏱️  {elapsed:.0f}s ({stats['total_facts']/elapsed:.0f} faits/s)")
    print(f"  💾 RAM estimée: {stats['estimated_ram_mb']} MB")
    print(f"  📂 {shard_dir}")
