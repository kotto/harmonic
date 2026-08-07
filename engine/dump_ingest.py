"""
Dump Ingestion — Ingestion massive depuis dumps locaux
=======================================================
Trois modes complémentaires :

  1. LABEL RESOLVER — Résout les URIs Wikidata en labels humains
     Prend un shard existant, remplace les wd:Qxxx par leurs labels
     
  2. WIKIPEDIA XML — Stream un dump Wikipedia XML, extrait les articles,
     passe au bootstrapper pour extraction de triples
     
  3. WIKIDATA JSON — Stream un dump Wikidata JSONL (un objet par ligne),
     extrait les propriétés mappées aux secteurs harmoniques

Usage :
    python dump_ingest.py --resolve-labels --shard-dir data/kb_enriched
    python dump_ingest.py --wikipedia --dump path/to/frwiki.xml
    python dump_ingest.py --wikidata --dump path/to/wikidata.jsonl
"""

import json, os, sys, re, time, logging, gzip, urllib.request, urllib.parse
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional, Iterator
from xml.etree import ElementTree

import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "HarmonicAI/3.3 (research; contact@harmonic-ai.org)"

# ═══════════════════════════════════════════════════════════════════════════════
# MODE 1 : LABEL RESOLVER
# ═══════════════════════════════════════════════════════════════════════════════

class LabelResolver:
    """
    Résout les URIs Wikidata (wd:Qxxx) en labels humains.
    
    Approche :
      1. Scanner un shard existant pour collecter tous les Q-IDs
      2. Résoudre par lots de 50 via l'API Wikidata
      3. Remplacer les URIs par les labels dans le shard
      4. Ré-ingérer les faits corrigés
    """
    
    def __init__(self, cache_dir: str = 'data/label_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.label_cache: Dict[str, str] = {}
        self._load_cache()
    
    def _cache_path(self) -> Path:
        return self.cache_dir / 'label_cache.json'
    
    def _load_cache(self):
        path = self._cache_path()
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.label_cache = json.load(f)
                log.info(f"Cache de labels chargé: {len(self.label_cache):,} entrées")
            except Exception:
                self.label_cache = {}
    
    def _save_cache(self):
        with open(self._cache_path(), 'w', encoding='utf-8') as f:
            json.dump(self.label_cache, f, ensure_ascii=False)
    
    def _extract_qids(self, text: str) -> List[str]:
        """Extrait les Q-IDs d'un texte (ex: Q12345)."""
        return re.findall(r'Q\d+', text)
    
    def _extract_pids(self, text: str) -> List[str]:
        """Extrait les P-IDs d'un texte (ex: P31)."""
        return re.findall(r'P\d+', text)
    
    def collect_ids_from_shard(self, shard_path: str) -> Tuple[set, set]:
        """
        Scanner un shard pour collecter tous les Q-IDs et P-IDs non résolus.
        
        Returns:
            (qids_to_resolve, pids_to_resolve)
        """
        qids = set()
        pids = set()
        
        data = np.load(shard_path, allow_pickle=True)
        for arr_name in ['objects', 'subjects', 'relations']:
            if arr_name in data:
                for val in data[arr_name]:
                    text = str(val)
                    qids.update(self._extract_qids(text))
                    pids.update(self._extract_pids(text))
        
        # Filtrer ceux déjà en cache
        qids_new = {q for q in qids if q not in self.label_cache}
        pids_new = {p for p in pids if p not in self.label_cache}
        
        log.info(f"Q-IDs trouvés: {len(qids):,} (nouveaux: {len(qids_new):,})")
        log.info(f"P-IDs trouvés: {len(pids):,} (nouveaux: {len(pids_new):,})")
        
        return qids_new, pids_new
    
    def resolve_batch(self, ids: List[str], entity_type: str = 'Q') -> Dict[str, str]:
        """
        Résout un lot d'IDs Wikidata en labels.
        
        Args:
            ids: liste d'IDs (ex: ['Q12345', 'Q67890'])
            entity_type: 'Q' pour items, 'P' pour propriétés
        
        Returns:
            {id: label}
        """
        if not ids:
            return {}
        
        results = {}
        
        # Filtrer le cache
        uncached = [eid for eid in ids if eid not in self.label_cache]
        cached = {eid: self.label_cache[eid] for eid in ids if eid in self.label_cache}
        results.update(cached)
        
        if not uncached:
            return results
        
        # Résoudre par lots de 50
        batch_size = 50
        for i in range(0, len(uncached), batch_size):
            batch = uncached[i:i+batch_size]
            ids_param = '|'.join(batch)
            
            # Format: wbgetentities avec ids=Q12345|Q67890
            ids_param = '|'.join(batch)
            url = f"{WIKIDATA_API}?action=wbgetentities&ids={ids_param}&props=labels&languages=fr|en&format=json"
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                
                entities = data.get('entities', {})
                for eid, entity in entities.items():
                    labels = entity.get('labels', {})
                    # Préférer fr, puis en
                    label = None
                    for lang in ['fr', 'en']:
                        if lang in labels:
                            label = labels[lang].get('value', '')
                            if label:
                                break
                    # Fallback: n'importe quelle langue
                    if not label and labels:
                        first = next(iter(labels.values()))
                        label = first.get('value', eid)
                    
                    if label and label != eid:
                        results[eid] = label
                        self.label_cache[eid] = label
                
                time.sleep(0.3)  # Rate limit
                
            except Exception as e:
                log.warning(f"Erreur résolution lot {i}: {e}")
                # Marquer comme non résolu pour ne pas réessayer
                for eid in batch:
                    self.label_cache[eid] = eid
        
        self._save_cache()
        return results
    
    def apply_to_shard(self, shard_path: str, output_path: str = None) -> int:
        """
        Applique la résolution de labels à un shard existant.
        
        Returns:
            Nombre de remplacements effectués
        """
        if output_path is None:
            output_path = shard_path
        
        # Collecter les IDs à résoudre
        qids, pids = self.collect_ids_from_shard(shard_path)
        
        # Résoudre les Q-IDs
        all_ids = list(qids) + list(pids)
        if all_ids:
            log.info(f"Résolution de {len(all_ids):,} IDs...")
            resolved = self.resolve_batch(all_ids)
            log.info(f"  Résolus: {len(resolved):,}")
        else:
            log.info("Aucun ID à résoudre")
            return 0
        
        # Charger le shard
        data = np.load(shard_path, allow_pickle=True)
        
        # Créer de nouveaux tableaux avec les labels résolus
        replacements = 0
        new_data = {}
        
        for key in data.keys():
            arr = data[key]
            if arr.dtype == object:  # Tableau de chaînes
                new_arr = arr.copy()
                for i in range(len(new_arr)):
                    val = str(new_arr[i])
                    for qid, label in resolved.items():
                        if qid in val:
                            # Remplacer l'URI complète ou juste le Q-ID
                            old_val = val
                            val = val.replace(f'http://www.wikidata.org/entity/{qid}', label)
                            val = val.replace(f'http://www.wikidata.org/prop/{qid}', label)
                            val = val.replace(qid, label)
                            if val != old_val:
                                replacements += 1
                    new_arr[i] = val
                new_data[key] = new_arr
            else:
                new_data[key] = arr
        
        # Sauvegarder
        np.savez_compressed(output_path, **new_data)
        log.info(f"Shard mis à jour: {replacements} remplacements → {output_path}")
        
        return replacements


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 2 : WIKIPEDIA XML DUMP
# ═══════════════════════════════════════════════════════════════════════════════

class WikipediaDumpIngester:
    """
    Ingère un dump Wikipedia XML en streaming.
    
    Le dump Wikipedia est un fichier XML contenant tous les articles.
    Format typique : frwiki-20260701-pages-articles.xml (4 GB)
    
    Traitement streaming : lit page par page, extrait le texte,
    passe au bootstrapper pour extraction de triples.
    """
    
    # Tags Wikipedia à ignorer dans le texte
    _WIKI_REMOVALS = [
        (r'\{\{.*?\}\}', ''),           # Modèles {{...}}
        (r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1'),  # Liens [[...]]
        (r'<ref[^>]*>.*?</ref>', ''),   # Références
        (r'<!--.*?-->', ''),             # Commentaires
        (r'<[^>]+>', ''),                # HTML tags
        (r"''+", ''),                    # Italique/gras
        (r'={2,}\s*([^=]+)\s*={2,}', r'\1'),  # == Titres == → texte
        (r'\[https?://[^\]]+\]', ''),    # Liens externes
        (r'\*+\s*', ''),                 # Listes
        (r'#+\s*', ''),                  # Listes numérotées
    ]
    
    def __init__(self, kb=None):
        self.kb = kb
        self.stats = {'articles': 0, 'triples': 0, 'skipped': 0}
    
    def _clean_wikitext(self, text: str) -> str:
        """Nettoie le wikitext pour obtenir du texte lisible."""
        for pattern, repl in self._WIKI_REMOVALS:
            text = re.sub(pattern, repl, text, flags=re.DOTALL)
        # Nettoyer les espaces
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()
    
    def _extract_text_from_xml(self, xml_text: str) -> Optional[str]:
        """Extrait le texte principal d'un article Wikipedia."""
        # Chercher le contenu entre <text> et </text>
        match = re.search(r'<text[^>]*>(.*?)</text>', xml_text, re.DOTALL)
        if not match:
            return None
        
        raw = match.group(1)
        # Ignorer les redirections
        if raw.startswith('#REDIRECT') or raw.startswith('#REDIRECTION'):
            return None
        
        return self._clean_wikitext(raw)
    
    def _extract_title_from_xml(self, xml_text: str) -> Optional[str]:
        """Extrait le titre d'un article."""
        match = re.search(r'<title>(.*?)</title>', xml_text)
        return match.group(1) if match else None
    
    def ingest_file(self, dump_path: str, max_articles: int = None,
                    languages: List[str] = None) -> int:
        """
        Ingère un dump Wikipedia XML.
        
        Args:
            dump_path: chemin vers le fichier XML (ou .xml.gz)
            max_articles: nombre maximum d'articles à traiter (None = tous)
            languages: ['fr', 'en'] pour filtrer par langue
        
        Returns:
            Nombre de triples extraits
        """
        path = Path(dump_path)
        if not path.exists():
            log.error(f"Fichier introuvable: {dump_path}")
            return 0
        
        log.info(f"Ingestion Wikipedia: {dump_path}")
        log.info(f"  Taille: {path.stat().st_size / 1e9:.1f} GB")
        
        # Déterminer si c'est gzippé
        is_gz = path.suffix == '.gz'
        opener = gzip.open if is_gz else open
        
        total_triples = 0
        article_count = 0
        current_page = []
        in_page = False
        
        t0 = time.time()
        
        with opener(dump_path, 'rt', encoding='utf-8', errors='replace') as f:
            for line in f:
                if '<page>' in line:
                    in_page = True
                    current_page = [line]
                elif '</page>' in line:
                    current_page.append(line)
                    in_page = False
                    
                    # Traiter la page complète
                    page_xml = ''.join(current_page)
                    title = self._extract_title_from_xml(page_xml)
                    text = self._extract_text_from_xml(page_xml)
                    
                    if text and len(text) > 200:
                        # Extraire les triples
                        triples = self._extract_triples(title, text)
                        if triples and self.kb:
                            try:
                                from auto_sectorize import sectorize_batch
                                triples = sectorize_batch(triples, min_confidence=1.5)
                            except ImportError:
                                pass
                            self.kb.ingest_batch(triples)
                        
                        total_triples += len(triples)
                        article_count += 1
                        
                        if article_count % 1000 == 0:
                            elapsed = time.time() - t0
                            speed = article_count / elapsed
                            log.info(f"  {article_count:,} articles, {total_triples:,} triples "
                                    f"({speed:.0f} art/s)")
                    
                    if max_articles and article_count >= max_articles:
                        break
                    
                elif in_page:
                    current_page.append(line)
        
        elapsed = time.time() - t0
        self.stats['articles'] = article_count
        self.stats['triples'] = total_triples
        
        log.info(f"Ingestion terminée: {article_count:,} articles, "
                 f"{total_triples:,} triples en {elapsed:.0f}s "
                 f"({article_count/elapsed:.0f} art/s)")
        
        return total_triples
    
    def _extract_triples(self, title: str, text: str) -> List[Tuple[str, str, str, str]]:
        """
        Extrait les triples d'un article Wikipedia.
        Utilise le bootstrapper et des patterns spécifiques Wikipedia.
        """
        triples = []
        
        # 1. Via le bootstrapper (si disponible)
        try:
            from bootstrapper import extract_triples_enhanced
            extracted = extract_triples_enhanced(text)
            for s, r, o, sec in extracted:
                if len(s) >= 2 and len(r) >= 2 and len(o) >= 2:
                    triples.append((s, r, o, sec))
        except ImportError:
            pass
        
        # 2. Pattern : phrases définitoires (X est un/une Y)
        def_patterns = [
            (r"([A-ZÉÈÊËÀÂÄÔÖÎÏÛÜÇ][^.]+?)\s+est\s+(?:un|une|le|la|l')\s+([^.]+?)(?:\.|,|;|$)", 'est'),
            (r"([A-ZÉÈÊËÀÂÄÔÖÎÏÛÜÇ][^.]+?)\s+(?:a été|fut|était)\s+(?:un|une)\s+([^.]+?)(?:\.|,|;)", 'a été'),
        ]
        
        for pattern, relation in def_patterns:
            for match in re.finditer(pattern, text):
                sujet = match.group(1).strip()[:100]
                objet = match.group(2).strip()[:100]
                if len(sujet) > 3 and len(objet) > 3:
                    triples.append((sujet, relation, objet, 'GENERAL'))
        
        # 3. Infobox : patterns clé-valeur
        # {{Infobox ... | clé = valeur | ... }}
        infobox_match = re.search(r'\{\{Infobox[^}]*?\}\}', text, re.DOTALL)
        if infobox_match:
            infobox = infobox_match.group(0)
            for match in re.finditer(r'\|\s*(\w+(?:\s+\w+)*)\s*=\s*([^|\n}]+)', infobox):
                key = match.group(1).strip()
                val = match.group(2).strip()
                if len(key) > 2 and len(val) > 2:
                    triples.append((title, f'a pour {key}', val, 'GENERAL'))
        
        return triples


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 3 : WIKIDATA JSONL DUMP
# ═══════════════════════════════════════════════════════════════════════════════

class WikidataDumpIngester:
    """
    Ingère un dump Wikidata au format JSONL (un objet JSON par ligne).
    
    Le dump peut être obtenu via :
      wget https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.gz
    
    Ou un sous-ensemble extrait avec des outils comme wikidata-filter.
    """
    
    # Propriétés Wikidata à extraire (les plus utiles pour PageForge)
    TARGET_PROPERTIES = {
        'P31': 'est un',               # instance de
        'P279': 'est une sous-classe de',  # sous-classe de
        'P361': 'fait partie de',       # partie de
        'P17': 'est situé en',          # pays
        'P131': 'est situé dans',        # localisation admin
        'P36': 'a pour capitale',       # capitale
        'P1082': 'a une population de', # population
        'P2046': 'a une superficie de', # superficie
        'P569': 'est né en',            # date de naissance
        'P570': 'est mort en',          # date de mort
        'P571': 'a été créé en',        # date de création
        'P106': 'a pour profession',    # profession
        'P800': 'a pour œuvre notable', # œuvre notable
        'P61': 'a été découvert par',   # découvreur
        'P50': 'a pour auteur',         # auteur
        'P166': 'a reçu le prix',       # prix
        'P27': 'a pour citoyenneté',    # citoyenneté
        'P495': 'est originaire de',    # pays d'origine
        'P112': 'a été fondé par',      # fondateur
        'P452': 'opère dans',           # secteur
        'P159': 'a son siège à',        # siège
        'P780': 'a pour symptôme',      # symptôme
        'P2176': 'a pour traitement',   # traitement
        'P1086': 'a pour numéro atomique', # numéro atomique
        'P246': 'a pour symbole',       # symbole
        'P2067': 'a une masse de',      # masse
        'P2048': 'a une hauteur de',    # hauteur
        'P2043': 'a une longueur de',   # longueur
        'P403': 'a pour embouchure',    # embouchure
        'P625': 'a pour coordonnées',   # coordonnées
    }
    
    def __init__(self, kb=None):
        self.kb = kb
        self.stats = {'lines': 0, 'entities': 0, 'triples': 0}
    
    def _resolve_label(self, item: dict, lang: str = 'fr') -> Optional[str]:
        """Résout le label d'un item ou d'une propriété."""
        # Priorité : fr, puis en, puis n'importe quelle langue
        labels = item.get('labels', {})
        for l in [lang, 'en']:
            if l in labels:
                return labels[l].get('value', '')
        if labels:
            first = next(iter(labels.values()))
            return first.get('value', '')
        return None
    
    def _resolve_value(self, data_value: dict) -> Optional[str]:
        """Résout la valeur d'une claim (peut être un Q-ID, une quantité, une date...)."""
        val_type = data_value.get('type', '')
        val = data_value.get('value', '')
        
        if val_type == 'wikibase-entityid':
            # C'est une référence à une autre entité → on prend l'ID pour l'instant
            # (la résolution de label se fera plus tard)
            return f"Q{val.get('numeric-id', '')}"
        elif val_type == 'quantity':
            amount = val.get('amount', '')
            unit = val.get('unit', '')
            # Simplifier l'unité
            unit = unit.replace('http://www.wikidata.org/entity/', '')
            return f"{amount} {unit}".strip() if unit else str(amount)
        elif val_type == 'time':
            return val.get('time', '')[:10]  # Juste la date
        elif val_type == 'string':
            return str(val)
        elif val_type == 'monolingualtext':
            return val.get('text', '')
        else:
            return str(val)[:100]
    
    def ingest_file(self, dump_path: str, max_lines: int = None) -> int:
        """
        Ingère un dump Wikidata JSONL.
        
        Args:
            dump_path: chemin vers le fichier JSONL (.json ou .json.gz)
            max_lines: nombre maximum de lignes à traiter
        
        Returns:
            Nombre de triples extraits
        """
        path = Path(dump_path)
        if not path.exists():
            log.error(f"Fichier introuvable: {dump_path}")
            return 0
        
        is_gz = path.suffix == '.gz'
        opener = gzip.open if is_gz else open
        
        total_triples = 0
        t0 = time.time()
        
        with opener(dump_path, 'rt', encoding='utf-8', errors='replace') as f:
            # Si c'est un tableau JSON complet (commence par '['), parser différemment
            first_char = f.read(1)
            f.seek(0)
            
            if first_char == '[':
                # Format tableau JSON complet
                data = json.load(f)
                entities = data if isinstance(data, list) else []
            else:
                # Format JSONL (un objet par ligne)
                entities = []
                for line in f:
                    line = line.strip()
                    if not line or line in ('[', ']', ','):
                        continue
                    if line.endswith(','):
                        line = line[:-1]
                    try:
                        entities.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                    if max_lines and len(entities) >= max_lines:
                        break
        
        log.info(f"  {len(entities):,} entités chargées")
        
        for entity in entities[:max_lines]:
            self.stats['entities'] += 1
            
            # Label du sujet
            sujet = self._resolve_label(entity)
            if not sujet:
                continue
            
            # Claims (propriétés)
            claims = entity.get('claims', {})
            for prop_id, prop_claims in claims.items():
                if prop_id not in self.TARGET_PROPERTIES:
                    continue
                
                relation = self.TARGET_PROPERTIES[prop_id]
                
                for claim in prop_claims:
                    mainsnak = claim.get('mainsnak', {})
                    if mainsnak.get('snaktype') != 'value':
                        continue
                    
                    data_value = mainsnak.get('datavalue', {})
                    objet = self._resolve_value(data_value)
                    
                    if objet and len(objet) > 1:
                        secteur = 'GENERAL'
                        from wikidata_real_ingest import PROPERTY_SECTORS
                        secteur = PROPERTY_SECTORS.get(prop_id, 'GENERAL')
                        
                        total_triples += 1
                        self.stats['triples'] += 1
                        
                        if self.kb:
                            try:
                                from auto_sectorize import sectorize_batch
                                facts = sectorize_batch(
                                    [(sujet, relation, str(objet), secteur)],
                                    min_confidence=1.5
                                )
                                self.kb.ingest_batch(facts)
                            except ImportError:
                                self.kb.ingest_batch(
                                    [(sujet, relation, str(objet), secteur)]
                                )
            
            if self.stats['entities'] % 5000 == 0:
                elapsed = time.time() - t0
                log.info(f"  {self.stats['entities']:,} entités, "
                        f"{self.stats['triples']:,} triples "
                        f"({self.stats['entities']/elapsed:.0f} ent/s)")
        
        elapsed = time.time() - t0
        log.info(f"Ingestion terminée: {self.stats['entities']:,} entités, "
                 f"{self.stats['triples']:,} triples en {elapsed:.0f}s")
        
        return total_triples


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Dump Ingestion — KB Harmonique')
    
    # Mode
    parser.add_argument('--resolve-labels', action='store_true',
                       help='Résoudre les labels Wikidata dans un shard existant')
    parser.add_argument('--wikipedia', action='store_true',
                       help='Ingérer un dump Wikipedia XML')
    parser.add_argument('--wikidata', action='store_true',
                       help='Ingérer un dump Wikidata JSONL')
    
    # Options communes
    parser.add_argument('--dump', type=str, help='Chemin vers le fichier dump')
    parser.add_argument('--shard-dir', type=str, default='data/kb_enriched',
                       help='Répertoire des shards')
    parser.add_argument('--max', type=int, default=None,
                       help='Nombre maximum d\'articles/entités')
    parser.add_argument('--output', type=str, default=None,
                       help='Chemin de sortie (pour --resolve-labels)')
    
    args = parser.parse_args()
    
    from kb_scaler import ShardedKB
    kb = ShardedKB(shard_dir=args.shard_dir, max_active=3)
    
    if args.resolve_labels:
        resolver = LabelResolver()
        shard_path = args.dump or f'{args.shard_dir}/shard_0000.npz'
        if not os.path.exists(shard_path):
            print(f"ERROR: Shard introuvable: {shard_path}")
            sys.exit(1)
        resolver.apply_to_shard(shard_path, args.output)
    
    elif args.wikipedia:
        if not args.dump:
            print("ERROR: --dump requis pour le mode Wikipedia")
            sys.exit(1)
        ingester = WikipediaDumpIngester(kb=kb)
        ingester.ingest_file(args.dump, max_articles=args.max)
        kb.save_all()
    
    elif args.wikidata:
        if not args.dump:
            print("ERROR: --dump requis pour le mode Wikidata")
            sys.exit(1)
        ingester = WikidataDumpIngester(kb=kb)
        ingester.ingest_file(args.dump, max_lines=args.max)
        kb.save_all()
    
    else:
        print("Spécifiez un mode: --resolve-labels, --wikipedia, ou --wikidata")
        parser.print_help()
