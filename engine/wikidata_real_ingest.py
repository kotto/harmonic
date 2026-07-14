"""
Wikidata Real Ingestion — Remplace les synthétiques par des vrais faits
=========================================================================
Utilise SPARQL pour extraire des connaissances structurées de Wikidata
et les ingérer dans le ShardedKB.

CATÉGORIES CIBLÉES (haute qualité, haute densité) :
  1. Pays + capitales + populations + superficies + continents
  2. Éléments chimiques + numéros atomiques + symboles + masses
  3. Scientifiques + découvertes + dates
  4. Artistes + œuvres majeures
  5. Monuments + localisations + dates de construction
  6. Espèces biologiques + classifications
  7. Prix Nobel + lauréats
  8. Langues + pays + nombre de locuteurs

OBJECTIF : 500K+ faits réels pour remplacer les 500K synthétiques.
"""

import json, time, urllib.request, urllib.parse, urllib.error, sys, logging
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "HarmonicAI/3.3 (https://github.com/kotto/harmonic; research)"
BATCH_SIZE = 10000

# ═══════════════════════════════════════════════════════════════════════════════
# REQUÊTES SPARQL — 8 catégories
# ═══════════════════════════════════════════════════════════════════════════════

QUERIES = {
    # 1. Pays + capitales + populations + superficies + continents (~200 pays × 4 propriétés = 800 faits)
    'countries': """
        SELECT ?pays ?paysLabel ?capitale ?capitaleLabel ?population ?superficie ?continent ?continentLabel
        WHERE {
          ?pays wdt:P31 wd:Q3624078.  # État souverain
          OPTIONAL { ?pays wdt:P36 ?capitale. }
          OPTIONAL { ?pays wdt:P1082 ?population. }
          OPTIONAL { ?pays wdt:P2046 ?superficie. }
          OPTIONAL { ?pays wdt:P30 ?continent. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 300
    """,
    
    # 2. Éléments chimiques (~120 éléments × 5 propriétés = 600 faits)
    'chemical_elements': """
        SELECT ?element ?elementLabel ?numero ?symbole ?masse ?decouvreur ?decouvreurLabel ?annee
        WHERE {
          ?element wdt:P31 wd:Q11344.  # élément chimique
          OPTIONAL { ?element wdt:P1086 ?numero. }
          OPTIONAL { ?element wdt:P246 ?symbole. }
          OPTIONAL { ?element wdt:P2067 ?masse. }
          OPTIONAL { ?element wdt:P61 ?decouvreur. }
          OPTIONAL { ?element wdt:P575 ?annee. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 150
    """,
    
    # 3. Scientifiques + découvertes (~5000 faits) — LIMIT réduit pour éviter timeout
    'scientists': """
        SELECT ?personne ?personneLabel ?decouverte ?decouverteLabel ?dateNaissance ?dateMort ?pays ?paysLabel
        WHERE {
          ?personne wdt:P106 wd:Q1650915.
          ?personne wdt:P800 ?decouverte.   # seulement ceux avec découverte connue
          OPTIONAL { ?personne wdt:P569 ?dateNaissance. }
          OPTIONAL { ?personne wdt:P570 ?dateMort. }
          OPTIONAL { ?personne wdt:P27 ?pays. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 500
    """,
    
    # 4. Artistes + œuvres majeures (~3000 faits)
    'artists': """
        SELECT ?artiste ?artisteLabel ?oeuvre ?oeuvreLabel ?dateNaissance ?dateMort ?mouvement ?mouvementLabel
        WHERE {
          ?artiste wdt:P106 wd:Q483501.  # artiste
          OPTIONAL { ?artiste wdt:P800 ?oeuvre. }
          OPTIONAL { ?artiste wdt:P569 ?dateNaissance. }
          OPTIONAL { ?artiste wdt:P570 ?dateMort. }
          OPTIONAL { ?artiste wdt:P135 ?mouvement. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 2000
    """,
    
    # 5. Monuments + localisations (~5000 faits)
    'monuments': """
        SELECT ?monument ?monumentLabel ?pays ?paysLabel ?ville ?villeLabel ?dateConstruction ?hauteur
        WHERE {
          ?monument wdt:P31 wd:Q4989906.  # monument
          OPTIONAL { ?monument wdt:P17 ?pays. }
          OPTIONAL { ?monument wdt:P131 ?ville. }
          OPTIONAL { ?monument wdt:P571 ?dateConstruction. }
          OPTIONAL { ?monument wdt:P2048 ?hauteur. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 3000
    """,
    
    # 6. Espèces biologiques (~5000 faits)
    'species': """
        SELECT ?espece ?especeLabel ?genre ?genreLabel ?famille ?familleLabel ?ordre ?ordreLabel ?decouvreur ?decouvreurLabel
        WHERE {
          ?espece wdt:P105 wd:Q7432.  # espèce
          OPTIONAL { ?espece wdt:P171 ?genre. }
          OPTIONAL { ?espece wdt:P177 ?famille. }
          OPTIONAL { ?espece wdt:P178 ?ordre. }
          OPTIONAL { ?espece wdt:P61 ?decouvreur. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 3000
    """,
    
    # 7. Prix Nobel + lauréats (~2000 faits)
    'nobel': """
        SELECT ?laureat ?laureatLabel ?prix ?prixLabel ?annee ?motivation
        WHERE {
          ?laureat wdt:P166 wd:Q7191.  # Prix Nobel
          OPTIONAL { ?laureat wdt:P166 ?prix. }
          OPTIONAL { ?laureat wdt:P585 ?annee. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 2000
    """,
    
    # 8. Langues + pays (~1000 faits)
    'languages': """
        SELECT ?langue ?langueLabel ?pays ?paysLabel ?locuteurs ?famille ?familleLabel
        WHERE {
          ?langue wdt:P31 wd:Q34770.  # langue
          OPTIONAL { ?langue wdt:P17 ?pays. }
          OPTIONAL { ?langue wdt:P1098 ?locuteurs. }
          OPTIONAL { ?langue wdt:P279 ?famille. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
        }
        LIMIT 1000
    """,
}

# ═══════════════════════════════════════════════════════════════════════════════
# PARSING SPARQL → TRIPLETS
# ═══════════════════════════════════════════════════════════════════════════════

PROPERTY_SECTORS = {
    'P36': 'GEOGRAPHIE', 'P1082': 'GEOGRAPHIE', 'P2046': 'GEOGRAPHIE',
    'P30': 'GEOGRAPHIE', 'P17': 'GEOGRAPHIE', 'P131': 'GEOGRAPHIE',
    'P1086': 'SCIENCES', 'P246': 'SCIENCES', 'P2067': 'SCIENCES',
    'P569': 'HISTOIRE', 'P570': 'HISTOIRE', 'P571': 'HISTOIRE', 'P575': 'HISTOIRE',
    'P800': 'SCIENCES', 'P61': 'SCIENCES', 'P166': 'CULTURE',
    'P106': 'GENERAL', 'P135': 'CULTURE', 'P2048': 'GEOGRAPHIE',
    'P171': 'BIOLOGIE', 'P177': 'BIOLOGIE', 'P178': 'BIOLOGIE',
    'P105': 'BIOLOGIE', 'P1098': 'CULTURE', 'P279': 'GENERAL',
    'P585': 'HISTOIRE', 'P27': 'GEOGRAPHIE',
}

def parse_sparql_bindings(data: dict, query_name: str) -> List[Tuple[str, str, str, str]]:
    """Parse les résultats SPARQL en triplets (sujet, relation, objet, secteur)."""
    triples = []
    bindings = data.get('results', {}).get('bindings', [])
    
    for b in bindings:
        # Récupérer le sujet principal
        main_keys = [k for k in b if k.endswith('Label') and not k.startswith('_')]
        if not main_keys:
            continue
        
        # Le premier label est le sujet
        sujet_key = main_keys[0]
        sujet_label = b.get(sujet_key, {}).get('value', '')
        if not sujet_label:
            continue
        
        sujet = sujet_label
        
        # Pour chaque autre champ, créer un fait
        for key in b:
            if key == sujet_key:
                continue
            
            val = b[key].get('value', '')
            if not val or len(val) < 2:
                continue
            
            # Déterminer la relation (nom lisible)
            if key.endswith('Label'):
                prop_name = key.replace('Label', '')
                relation = prop_name.replace('_', ' ')
            else:
                relation = key.replace('_', ' ')
            
            # Secteur
            secteur = 'GENERAL'
            for pid, sec in PROPERTY_SECTORS.items():
                if pid.lower() in key.lower():
                    secteur = sec
                    break
            
            # Traduire les relations courantes
            relation_map = {
                'capitale': 'a pour capitale',
                'population': 'a une population de',
                'superficie': 'a une superficie de',
                'continent': 'est situé sur le continent',
                'numero': 'a pour numéro atomique',
                'symbole': 'a pour symbole chimique',
                'masse': 'a une masse atomique de',
                'decouvreur': 'a été découvert par',
                'annee': 'a été découvert en',
                'dateNaissance': 'est né en',
                'dateMort': 'est mort en',
                'pays': 'est situé en',
                'oeuvre': 'a créé',
                'mouvement': 'appartient au mouvement',
                'dateConstruction': 'a été construit en',
                'hauteur': 'a une hauteur de',
                'ville': 'est situé à',
                'genre': 'appartient au genre',
                'famille': 'appartient à la famille',
                'ordre': 'appartient à l\'ordre',
                'locuteurs': 'a pour nombre de locuteurs',
                'prix': 'a reçu le prix',
            }
            
            for kw, rel in relation_map.items():
                if kw in key.lower():
                    relation = rel
                    break
            
            triples.append((sujet, relation, str(val), secteur))
    
    return triples

# ═══════════════════════════════════════════════════════════════════════════════
# FETCH + INGEST
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_sparql(query: str, timeout: int = 60) -> dict:
    """Exécute une requête SPARQL."""
    url = f"{SPARQL_ENDPOINT}?format=json&query={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        log.error(f"SPARQL error: {e}")
        return {}

def ingest_all(kb, target: int = 500_000):
    """Ingère toutes les catégories Wikidata."""
    total = 0
    t0 = time.time()
    
    for name, query in QUERIES.items():
        if total >= target:
            break
        
        log.info(f"📡 SPARQL {name}...")
        
        try:
            data = fetch_sparql(query)
            triples = parse_sparql_bindings(data, name)
            
            if not triples:
                log.warning(f"  ⚠️ 0 triplets pour {name}")
                continue
            
            # Déduplication
            seen = set()
            unique = []
            for s, r, o, sec in triples:
                key = (s.lower().strip()[:60], r.lower().strip()[:60], str(o).lower().strip()[:80])
                if key not in seen:
                    seen.add(key)
                    unique.append((s, r, o, sec))
            
            # Ingérer
            kb.ingest_batch(unique)
            total += len(unique)
            
            log.info(f"  ✅ {name}: {len(triples):,} triplets → {len(unique):,} uniques "
                     f"(total: {total:,})")
        
        except Exception as e:
            log.error(f"  ❌ {name}: {e}")
        
        time.sleep(0.3)  # respecter le rate limit
    
    kb.save_all()
    elapsed = time.time() - t0
    log.info(f"🎉 Ingestion terminée: {total:,} faits en {elapsed:.0f}s "
             f"({total/elapsed:.0f}/s)")
    return total

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from kb_scaler import ShardedKB
    
    print("=" * 60)
    print("  WIKIDATA REAL INGESTION")
    print("  Remplace les 500K synthétiques par des vrais faits")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=int, default=500_000)
    parser.add_argument('--shard-dir', type=str, default='data/kb_shards_real')
    args = parser.parse_args()
    
    kb = ShardedKB(shard_dir=args.shard_dir, max_active=3)
    
    total = ingest_all(kb, target=args.target)
    
    print()
    print(f"  ✅ {total:,} faits réels ingérés")
    print(f"  📂 {kb.stats['shards']} shards, ~{kb.stats['estimated_ram_mb']} MB RAM")
    print(f"  📂 {args.shard_dir}")
    
    # Stats par secteur
    sectors = defaultdict(int)
    for shard in kb.shards.values():
        if shard._loaded:
            for f in shard.facts:
                sectors[f.secteur] += 1
        else:
            shard.load()
            for f in shard.facts:
                sectors[f.secteur] += 1
            shard.unload()
    
    print()
    print("  Distribution secteurs :")
    for sec, n in sorted(sectors.items(), key=lambda x: -x[1])[:10]:
        print(f"    {sec}: {n:,}")
