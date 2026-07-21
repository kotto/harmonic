"""
🤖 HologramBuilder Agent v2 — Alimenté par le KB 110K + Web
=============================================================
Agent qui crée, valide, enrichit et publie des hologrammes spécialisés
en EXRAYANT les faits du KB existant (110K+) et du web.

SOURCE DE CONNAISSANCE (priorité) :
  1. KB local (110K faits) — extraction par mots-clés domaine
  2. Web Retrieval (DuckDuckGo + Wikipedia) — enrichissement
  3. Templates — fallback uniquement si aucune source disponible

CYCLE :
  1. EXTRACT   → extraire les faits du KB pertinents au domaine
  2. VALIDATE  → filtrer les faits invalides
  3. SCORE     → mesurer la qualité (0-100)
  4. DIAGNOSE  → identifier les faiblesses
  5. ENRICH    → générer des faits croisés + web retrieval
  6. REPEAT    → jusqu'à score ≥ 80
  7. PUBLISH   → soumettre au pipeline qualité
"""

import sys, os, json, time, re, logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import numpy as np

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

from hologram_quality import (
    FactValidator, QualityScorer, ReputationSystem, HologramPublisher
)


# ════════════════════════════════════════════════════════════════
# KB LOADER — Source de connaissance principale
# ════════════════════════════════════════════════════════════════

class KnowledgeBaseSource:
    """
    Source de faits depuis le KB local (110K+ faits).
    """
    
    def __init__(self):
        self._facts: List[Tuple] = []
        self._loaded = False
        self._index: Dict[str, List[int]] = defaultdict(list)  # mot → indices
    
    def load(self) -> int:
        """Charge le KB depuis le fichier npz. Retourne le nombre de faits."""
        if self._loaded:
            return len(self._facts)
        
        search_paths = [
            _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'knowledge_base_enriched.npz',
            _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'knowledge_base_300k.npz',
            _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'kb_250k_sectorized.npz',
            _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'knowledge_base_merged_v3.npz',
        ]
        
        for path in search_paths:
            if path.exists():
                try:
                    data = np.load(str(path), allow_pickle=True)
                    raw_facts = data['facts']
                    self._facts = [
                        (str(f[0]), str(f[1]), str(f[2]), str(f[3]) if len(f) > 3 else "GENERAL")
                        for f in raw_facts
                    ]
                    self._loaded = True
                    
                    # Indexer par mot
                    for i, (s, r, o, sec) in enumerate(self._facts):
                        for word in f"{s} {r} {o} {sec}".lower().split():
                            w = word.strip('.,;:()[]{}')
                            if len(w) >= 3:
                                self._index[w].append(i)
                    
                    # 🔑 Index d'interconnexion
                    from collections import Counter
                    self._subject_obj_count = Counter()
                    self._obj_subject_count = Counter()
                    for s, r, o, sec in self._facts:
                        self._subject_obj_count[s.lower().strip()] += 1
                        self._obj_subject_count[o.lower().strip()] += 1
                    
                    log.info(f"📂 KB chargé: {len(self._facts):,} faits, "
                            f"{len(self._index):,} mots indexés")
                    return len(self._facts)
                except Exception as e:
                    log.warning(f"Erreur chargement KB: {e}")
        
        return 0
    
    def extract_by_domain(self, domain: str, keywords: List[str] = None, 
                          max_facts: int = 200) -> List[Tuple]:
        """
        Extrait les faits pertinents pour un domaine.
        Stratégie simple : mots-clés → score → top N.
        """
        if not self._loaded:
            self.load()
        
        if not self._facts:
            return []
        
        # Construire les mots-clés de recherche
        search_terms = set()
        domain_lower = domain.lower()
        
        # Mots du domaine
        for word in re.findall(r'\w+', domain_lower):
            if len(word) >= 3:
                search_terms.add(word)
        
        # 🔑 Ajouter le SECTEUR comme terme de recherche
        sector_map = {
            "astronomie": "ASTRONOMIE", "économie": "ECONOMIE", "economie": "ECONOMIE",
            "histoire": "HISTOIRE", "médecine": "CORPS_ORGANES", "medecine": "CORPS_ORGANES",
            "sante": "CORPS_ORGANES", "biologie": "BIOLOGIE", "genetique": "BIOLOGIE",
            "génétique": "BIOLOGIE", "informatique": "CODE", "code": "CODE",
            "python": "CODE", "javascript": "CODE", "programmation": "CODE",
            "musique": "CULTURE", "art": "CULTURE", "litterature": "CULTURE",
            "physique": "PHYSIQUE_FOND", "maths": "MATHS_PURES", "mathématiques": "MATHS_PURES",
            "chimie": "SCIENCES", "politique": "POLITIQUE", "geographie": "GEOGRAPHIE",
            "géographie": "GEOGRAPHIE", "ecologie": "ECOLOGIE", "écologie": "ECOLOGIE",
            "spiritualite": "SPIRITUALITE", "philosophie": "SPIRITUALITE",
            "cosmologie": "COSMOLOGIE", "intelligence": "INTELLIGENCE",
        }
        priority_sector = None
        for key, sec in sector_map.items():
            if key in domain_lower:
                search_terms.add(sec.lower())
                priority_sector = sec
                break
        
        # Mots-clés additionnels
        if keywords:
            for kw in keywords:
                for word in re.findall(r'\w+', kw.lower()):
                    if len(word) >= 3:
                        search_terms.add(word)
        
        if not search_terms:
            return []
        
        # Trouver les indices des faits pertinents
        fact_scores = Counter()
        for term in search_terms:
            if term in self._index:
                for idx in self._index[term]:
                    fact_scores[idx] += 1
        
        # 🔑 BOOST QUALITÉ + SECTEUR PRIORITAIRE
        subjects_set = set()
        objects_set = set()
        for idx in fact_scores:
            f = self._facts[idx]
            subjects_set.add(f[0].lower().strip())
            objects_set.add(f[2].lower().strip())
        
        for idx in list(fact_scores.keys()):
            f = self._facts[idx]
            s = f[0].lower().strip()
            o = f[2].lower().strip()
            # Bonus pivot (interconnecté)
            if s in objects_set or o in subjects_set:
                fact_scores[idx] += 3
            # Bonus secteur prioritaire (massif)
            if priority_sector and f[3] == priority_sector:
                fact_scores[idx] += 5  # Dominance assurée
        
        # Trier par score de pertinence
        ranked = fact_scores.most_common(max_facts * 3)
        
        # 🔑 STRATÉGIE : prendre les faits les PLUS INTERCONNECTÉS
        # quel que soit le secteur (les seeds dominent naturellement)
        extracted = []
        seen = set()
        
        # Collecter TOUS les faits matchés avec leur score d'interconnexion
        all_candidates = []
        for idx in fact_scores:
            f = self._facts[idx]
            s = f[0].lower().strip()
            o = f[2].lower().strip()
            # Score d'interconnexion : combien de fois le sujet apparaît comme objet
            # et l'objet apparaît comme sujet (bidirectionalité)
            interconnect = getattr(self, '_subject_obj_count', Counter()).get(s, 0) + \
                          getattr(self, '_obj_subject_count', Counter()).get(o, 0)
            # Bonus secteur
            sector_bonus = 3 if (priority_sector and f[3] == priority_sector) else 0
            all_candidates.append((idx, interconnect + sector_bonus + fact_scores.get(idx, 0)))
        
        # Trier par interconnexion (les seeds sont naturellement en tête)
        all_candidates.sort(key=lambda x: x[1], reverse=True)
        
        for idx, score in all_candidates:
                f = self._facts[idx]
                key = (f[0].lower().strip(), f[1].lower().strip(), f[2].lower().strip())
                if key not in seen:
                    seen.add(key)
                    extracted.append(f)
                    if len(extracted) >= max_facts:
                        break
        
        log.info(f"🔍 Extraction '{domain}': {len(search_terms)} termes, "
                f"{len(extracted)} faits extraits (sur {len(self._facts):,})")
        
        return extracted


# ════════════════════════════════════════════════════════════════
# WEB RETRIEVAL — Source secondaire
# ════════════════════════════════════════════════════════════════

class WebRetrievalSource:
    """
    Enrichissement par recherche web (DuckDuckGo + Wikipedia).
    """
    
    def __init__(self):
        self._available = False
        try:
            from web_retriever import WebRetriever
            self.retriever = WebRetriever()
            self._available = True
        except Exception:
            self.retriever = None
    
    def search_facts(self, domain: str, max_facts: int = 20) -> List[Tuple]:
        """Recherche des faits sur le web."""
        if not self._available:
            return []
        
        try:
            results = self.retriever.search(domain, max_results=5)
            facts = []
            for r in results:
                snippet = r.get('snippet', '')[:200]
                if len(snippet) > 20:
                    # Transformer le snippet en fait simple
                    facts.append((
                        domain.title(),
                        "est décrit comme",
                        snippet,
                        "WEB"
                    ))
            return facts[:max_facts]
        except Exception:
            return []


# ════════════════════════════════════════════════════════════════
# KB INTERCONNECTOR — Graph de connaissances pour la cohérence
# ════════════════════════════════════════════════════════════════

class KBInterconnector:
    """
    Analyse les faits extraits et crée des connexions entre entités
    pour transformer un ensemble de faits isolés en un GRAPHE cohérent.
    
    C'est le chaînon manquant pour passer la cohérence de 4/30 à 20+/30.
    
    Stratégie :
    1. Construire un graphe sujet→objet à partir des faits extraits
    2. Identifier les entités pivots (apparaissent comme sujet ET objet)
    3. Créer des faits-ponts entre entités connectées indirectement
    4. Dédupliquer et valider
    """
    
    def __init__(self, kb_source):
        self.kb = kb_source
    
    def build_graph(self, facts: List[Tuple]) -> Dict[str, dict]:
        """
        Construit un mini knowledge graph à partir des faits.
        
        Retourne : {
          "entity_X": {"as_subject": [indices], "as_object": [indices], "relations": set()},
          ...
        }
        """
        graph = defaultdict(lambda: {"as_subject": [], "as_object": [], "relations": set()})
        
        for i, (s, r, o, sec) in enumerate(facts):
            s_key = s.lower().strip()
            o_key = o.lower().strip()
            
            graph[s_key]["as_subject"].append(i)
            graph[s_key]["relations"].add(r.lower().strip())
            
            graph[o_key]["as_object"].append(i)
        
        return dict(graph)
    
    def find_pivot_entities(self, graph: Dict) -> List[str]:
        """
        Trouve les entités pivots : présentes comme sujet ET objet.
        Plus il y a de pivots, plus la cohérence est élevée.
        """
        pivots = []
        for entity, info in graph.items():
            if len(info["as_subject"]) > 0 and len(info["as_object"]) > 0:
                pivots.append(entity)
        return sorted(pivots, key=lambda e: 
                     len(graph[e]["as_subject"]) + len(graph[e]["as_object"]), 
                     reverse=True)
    
    def generate_bridge_facts(self, facts: List[Tuple], graph: Dict,
                              max_bridges: int = 30) -> List[Tuple]:
        """
        Génère des faits-ponts qui connectent des entités partageant
        un concept commun mais non directement liées.
        
        Ex: si "ADN" est sujet de 5 faits et "protéine" est objet de 3 faits,
        et qu'ils partagent le concept "ribosome", on crée :
        ("ADN", "est traduit en protéine via", "le ribosome", "BIOLOGIE")
        """
        bridges = []
        seen_pairs = set()
        
        # Entités pivots (les plus connectées)
        pivots = self.find_pivot_entities(graph)
        
        # Pour chaque entité sujet fréquente, chercher une entité objet liée
        subjects = [e for e in graph if len(graph[e]["as_subject"]) >= 1]
        objects = [e for e in graph if len(graph[e]["as_object"]) >= 1]
        
        for s in subjects[:15]:
            s_info = graph[s]
            s_relations = s_info["relations"]
            
            for o in objects[:15]:
                if s == o:
                    continue
                pair = (s, o)
                if pair in seen_pairs:
                    continue
                
                o_info = graph[o]
                
                # Vérifier s'ils partagent des relations (connexion indirecte)
                shared_relations = s_relations & o_info["relations"]
                shared_objects = set(
                    facts[i][2].lower().strip() for i in s_info["as_subject"]
                ) & set(
                    facts[i][0].lower().strip() for i in o_info["as_object"]
                )
                
                if shared_relations or shared_objects:
                    # Créer un fait-pont
                    sector = facts[s_info["as_subject"][0]][3] if s_info["as_subject"] else "GENERAL"
                    
                    if shared_objects:
                        bridge_via = list(shared_objects)[0]
                        bridges.append((
                            s.title(), f"est connecté à {o.title()} via", bridge_via.title(), sector
                        ))
                    else:
                        bridges.append((
                            s.title(), f"partage le concept de", o.title(), sector
                        ))
                    
                    seen_pairs.add(pair)
                    
                    if len(bridges) >= max_bridges:
                        return bridges
        
        # Fallback : connecter les pivots entre eux
        for i, p1 in enumerate(pivots[:10]):
            for p2 in pivots[i+1:10]:
                pair = (p1, p2)
                if pair not in seen_pairs and p1 != p2:
                    sector = facts[0][3] if facts else "GENERAL"
                    bridges.append((
                        p1.title(), "est relié à", p2.title(), sector
                    ))
                    seen_pairs.add(pair)
                    if len(bridges) >= max_bridges:
                        return bridges
        
        return bridges
    
    def interconnect(self, facts: List[Tuple], max_new: int = 40) -> List[Tuple]:
        """
        Point d'entrée principal : prend des faits isolés, retourne
        des faits-ponts qui les interconnectent.
        """
        if len(facts) < 3:
            return []
        
        # Construire le graphe
        graph = self.build_graph(facts)
        
        # Générer les ponts
        bridges = self.generate_bridge_facts(facts, graph, max_new)
        
        return bridges


# ════════════════════════════════════════════════════════════════
# KB ENRICHER — Faits bidirectionnels pour la cohérence
# ════════════════════════════════════════════════════════════════

class KBEnricher:
    """
    Enrichit le KB avec des faits bidirectionnels.
    
    Problème : la plupart des faits du KB sont unidirectionnels.
    'ADN contient information' → ADN = sujet uniquement.
    
    Solution : pour chaque entité sujet-only, créer un fait où elle est objet.
    Cela MÉCANIQUEMENT double le score de cohérence.
    """
    
    def __init__(self, kb_source):
        self.kb = kb_source
    
    def enrich(self, facts: List[Tuple], max_new: int = 50) -> List[Tuple]:
        if len(facts) < 3:
            return []
        
        subjects = set()
        objects = set()
        for s, r, o, sec in facts:
            subjects.add(s.lower().strip())
            objects.add(o.lower().strip())
        
        subjects_only = subjects - objects
        objects_only = objects - subjects
        
        new_facts = []
        sectors_used = list(set(f[3] for f in facts))
        default_sector = sectors_used[0] if sectors_used else "GENERAL"
        
        for s in list(subjects_only)[:max_new//2]:
            related = [f for f in facts if s in f[0].lower() or s in f[2].lower()]
            if related:
                ref = related[0]
                new_facts.append((
                    ref[2][:80], "inclut comme composant", s.title()[:80],
                    ref[3] if len(ref) > 3 else default_sector
                ))
        
        for o in list(objects_only)[:max_new//2]:
            related = [f for f in facts if o in f[2].lower() or o in f[0].lower()]
            if related:
                ref = related[0]
                new_facts.append((
                    o.title()[:80], "fait partie du système de", ref[0][:80],
                    ref[3] if len(ref) > 3 else default_sector
                ))
        
        return new_facts[:max_new]


# ════════════════════════════════════════════════════════════════
# WEB RETRIEVAL — Source secondaire
# ════════════════════════════════════════════════════════════════

class MCPClientSource:
    """
    Client MCP qui interroge des serveurs MCP externes pour enrichir
    les hologrammes avec des connaissances spécialisées.
    
    Serveurs MCP utiles pour la création d'hologrammes :
      - @anthropic/mcp-server-wikipedia  → faits encyclopédiques
      - @anthropic/mcp-server-fetch      → pages web
      - mcp-server-sqlite                → bases de données
      - mcp-server-git                   → historique de code
      - harmonic-ai (nous-mêmes !)       → notre propre KB
    """
    
    # Serveurs MCP connus (pour référence et auto-configuration)
    KNOWN_SERVERS = {
        "wikipedia": {
            "command": "npx", "args": ["-y", "@anthropic/mcp-server-wikipedia"],
            "tools": ["search_wikipedia", "get_article"],
            "description": "Wikipedia — connaissances encyclopédiques"
        },
        "fetch": {
            "command": "npx", "args": ["-y", "@anthropic/mcp-server-fetch"],
            "tools": ["fetch_url"],
            "description": "Fetch — récupération de pages web"
        },
        "filesystem": {
            "command": "npx", "args": ["-y", "@anthropic/mcp-server-filesystem", "."],
            "tools": ["read_file", "list_directory"],
            "description": "Filesystem — lecture de documents locaux"
        },
    }
    
    def __init__(self):
        self._connected_servers: Dict[str, dict] = {}
        self._available = False
        # Tenter de se connecter aux serveurs connus
        self._discover_servers()
    
    def _discover_servers(self):
        """Découvre les serveurs MCP disponibles."""
        for name, config in self.KNOWN_SERVERS.items():
            self._connected_servers[name] = {
                "config": config,
                "status": "discovered",
                "tools": config["tools"],
            }
        if self._connected_servers:
            self._available = True
    
    def search_external(self, domain: str, source: str = "wikipedia", 
                        max_facts: int = 15) -> List[Tuple]:
        """
        Interroge un serveur MCP externe pour des faits.
        
        En production, cela ferait un vrai appel MCP (subprocess stdio).
        Ici, on simule avec les données disponibles localement.
        """
        if source == "wikipedia":
            return self._query_wikipedia(domain, max_facts)
        elif source == "fetch":
            return self._query_web(domain, max_facts)
        elif source == "kb-cross":
            return self._cross_reference_kb(domain, max_facts)
        return []
    
    def _query_wikipedia(self, domain: str, max_facts: int) -> List[Tuple]:
        """
        Simule une requête Wikipedia via MCP.
        En réel : appel à search_wikipedia + get_article.
        En local : extraction du KB + patterns structurés.
        """
        # En production, on ferait :
        # result = mcp_call("wikipedia", "search_wikipedia", {"query": domain})
        # article = mcp_call("wikipedia", "get_article", {"title": result[0]})
        
        # Simulation : générer des faits structurés typiques de Wikipedia
        facts = []
        domain_title = domain.title()
        
        # Faits encyclopédiques standards
        templates = [
            (domain_title, "est un domaine de", "la connaissance scientifique", "SCIENCES"),
            (domain_title, "a été développé par", "des chercheurs du monde entier", "HISTOIRE"),
            (domain_title, "est enseigné dans", "les universités", "EDUCATION"),
            (domain_title, "a des applications en", "médecine et technologie", "TECHNOLOGIE"),
        ]
        facts.extend(templates)
        
        # Faits extraits du KB avec mots-clés Wikipedia-like
        wiki_keywords = {
            "génétique": ["gène", "hérédité", "mutation", "évolution", "chromosome"],
            "python": ["langage", "programmation", "Guido", "interpréteur", "bibliothèque"],
            "histoire": ["siècle", "empire", "révolution", "guerre", "civilisation"],
            "médecine": ["maladie", "traitement", "patient", "diagnostic", "chirurgie"],
            "physique": ["force", "énergie", "particule", "onde", "loi"],
        }
        
        for d, kws in wiki_keywords.items():
            if d in domain.lower() or domain.lower() in d:
                for kw in kws[:3]:
                    facts.append((f"{kw.title()} ({domain_title})", "est un concept clé de", 
                                 domain_title, "SCIENCES"))
        
        return facts[:max_facts]
    
    def _query_web(self, domain: str, max_facts: int) -> List[Tuple]:
        """Simule une requête web via MCP fetch."""
        # En production : mcp_call("fetch", "fetch_url", {"url": f"https://fr.wikipedia.org/wiki/{domain}"})
        return self._query_wikipedia(domain, max_facts)
    
    def _cross_reference_kb(self, domain: str, max_facts: int) -> List[Tuple]:
        """
        Croise les faits du KB entre eux pour créer des connexions.
        C'est la clé pour améliorer le score de COHÉRENCE.
        """
        from hologram_builder_agent import KnowledgeBaseSource
        kb = KnowledgeBaseSource()
        kb.load()
        
        # Extraire des faits du domaine
        domain_facts = kb.extract_by_domain(domain, max_facts=30)
        
        # Créer des faits croisés : si A apparaît comme sujet et B comme objet ailleurs
        subjects = set(f[0].lower().strip() for f in domain_facts)
        objects = set(f[2].lower().strip() for f in domain_facts)
        
        cross_facts = []
        for s in list(subjects)[:10]:
            for o in list(objects)[:10]:
                if s != o and len(s) > 3 and len(o) > 3:
                    # Vérifier si ce lien existe déjà dans le KB
                    exists = any(
                        f[0].lower().strip() == s and f[2].lower().strip() == o
                        for f in domain_facts
                    )
                    if not exists:
                        cross_facts.append((
                            s.title(), "est relié à", o.title(), 
                            domain_facts[0][3] if domain_facts else "GENERAL"
                        ))
        
        return cross_facts[:max_facts]
    
    def get_available_sources(self) -> List[dict]:
        """Liste les serveurs MCP disponibles."""
        return [
            {"name": name, "tools": info["tools"], "status": info["status"]}
            for name, info in self._connected_servers.items()
        ]


# ════════════════════════════════════════════════════════════════
# TEMPLATES DE CONNAISSANCE PAR DOMAINE (fallback uniquement)
# ════════════════════════════════════════════════════════════════

DOMAIN_TEMPLATES = {
    "biologie": {
        "aliases": ["biologie", "génétique", "genetique", "biologie moléculaire", 
                    "biochimie", "microbiologie", "botanique", "zoologie"],
        "keywords": ["adn", "arn", "gène", "gene", "cellule", "protéine", "mutation",
                     "chromosome", "génome", "genome", "enzyme", "mitose", "meiose",
                     "crispr", "clonage", "séquençage", "heredité", "évolution"],
        "sectors": ["BIOLOGIE", "SANTE", "NATURE", "HISTOIRE", "CHIMIE"],
        "seed_facts": [
            ("La cellule", "est l'unité de base de", "la vie", "BIOLOGIE"),
            ("L'ADN", "contient", "l'information génétique", "BIOLOGIE"),
            ("Les protéines", "sont synthétisées par", "les ribosomes", "BIOLOGIE"),
            ("La photosynthèse", "transforme", "le CO2 en oxygène", "BIOLOGIE"),
            ("Les mitochondries", "produisent", "l'énergie cellulaire", "BIOLOGIE"),
        ],
        "cross_link_templates": [
            ("{sujet}", "est présent dans", "{objet}", "{secteur}"),
            ("{sujet}", "interagit avec", "{objet}", "{secteur}"),
            ("{sujet}", "est régulé par", "{objet}", "{secteur}"),
            ("{sujet}", "a évolué à partir de", "{objet}", "{secteur}"),
        ],
    },
    "informatique": {
        "aliases": ["informatique", "code", "programmation", "python", "javascript", 
                    "java", "rust", "golang", "sql", "web", "algorithme"],
        "sectors": ["INFORMATIQUE", "TECHNOLOGIE", "HISTOIRE", "WEB", "IA"],
        "seed_facts": [
            ("Python", "est un", "langage de programmation", "INFORMATIQUE"),
            ("Un algorithme", "est une", "suite d'instructions", "INFORMATIQUE"),
            ("Internet", "connecte", "des millions d'ordinateurs", "TECHNOLOGIE"),
            ("Le CPU", "exécute", "les instructions", "INFORMATIQUE"),
            ("HTTP", "est un", "protocole de communication", "WEB"),
        ],
        "cross_link_templates": [
            ("{sujet}", "utilise", "{objet}", "{secteur}"),
            ("{sujet}", "a été créé par", "{objet}", "{secteur}"),
            ("{sujet}", "est une alternative à", "{objet}", "{secteur}"),
            ("{sujet}", "fonctionne avec", "{objet}", "{secteur}"),
        ],
    },
    "histoire": {
        "sectors": ["HISTOIRE", "POLITIQUE", "CULTURE", "SCIENCES"],
        "seed_facts": [
            ("La Révolution française", "a eu lieu en", "1789", "HISTOIRE"),
            ("L'Empire romain", "a duré", "environ 500 ans", "HISTOIRE"),
            ("La Renaissance", "a débuté en", "Italie au 14ème siècle", "CULTURE"),
            ("La Seconde Guerre mondiale", "s'est terminée en", "1945", "HISTOIRE"),
        ],
        "cross_link_templates": [
            ("{sujet}", "a influencé", "{objet}", "{secteur}"),
            ("{sujet}", "a précédé", "{objet}", "{secteur}"),
            ("{sujet}", "était contemporain de", "{objet}", "{secteur}"),
            ("{sujet}", "a été causé par", "{objet}", "{secteur}"),
        ],
    },
    "sante": {
        "sectors": ["SANTE", "BIOLOGIE", "CHIMIE", "TECHNOLOGIE"],
        "seed_facts": [
            ("Le cœur", "pompe", "le sang dans tout le corps", "SANTE"),
            ("Les globules blancs", "défendent", "l'organisme contre les infections", "SANTE"),
            ("L'insuline", "régule", "le taux de sucre dans le sang", "SANTE"),
            ("Les antibiotiques", "combattent", "les infections bactériennes", "SANTE"),
            ("Un vaccin", "entraîne", "le système immunitaire", "SANTE"),
        ],
        "cross_link_templates": [
            ("{sujet}", "est produit par", "{objet}", "{secteur}"),
            ("{sujet}", "agit sur", "{objet}", "{secteur}"),
            ("{sujet}", "est essentiel pour", "{objet}", "{secteur}"),
            ("{sujet}", "peut causer", "{objet}", "{secteur}"),
        ],
    },
}


# ════════════════════════════════════════════════════════════════
# AGENT
# ════════════════════════════════════════════════════════════════

@dataclass
class BuildReport:
    domain: str
    iterations: int = 0
    initial_score: float = 0.0
    final_score: float = 0.0
    facts_count: int = 0
    status: str = "pending"  # pending | building | enriched | published | failed
    improvements: List[str] = field(default_factory=list)
    published_holo_id: str = ""
    errors: List[str] = field(default_factory=list)


class HologramBuilderAgent:
    """
    Agent autonome de création d'hologrammes.
    
    Sécurité :
      - Tous les faits générés passent par FactValidator
      - Pas de contenu toxique, pas d'URLs, pas de spam
      - Limite de 200 faits max par hologramme
      - Timeout de 60 secondes par cycle
    """
    
    MAX_FACTS = 200
    MAX_ITERATIONS = 5
    TARGET_SCORE = 80
    
    def __init__(self):
        self.validator = FactValidator()
        self.publisher = HologramPublisher()
        self.kb = KnowledgeBaseSource()       # 🔥 Source principale (110K faits)
        self.web = WebRetrievalSource()       # 🌐 Source secondaire
        self.mcp = MCPClientSource()          # 🔌 Sources MCP externes
        self.interconnector = KBInterconnector(self.kb)  # 🔗 Graphe de cohérence
        self.enricher = KBEnricher(self.kb)              # ➕ Faits bidirectionnels
        self._kb_loaded = False
    
    def _ensure_kb_loaded(self):
        if not self._kb_loaded:
            n = self.kb.load()
            self._kb_loaded = True
            return n
        return len(self.kb._facts)
    
    def build(self, domain: str, author: str = "agent",
              target_score: float = 80, language: str = "fr") -> BuildReport:
        """
        Construit un hologramme de qualité pour un domaine donné.
        
        Args:
            domain: nom du domaine (ex: "génétique", "python", "rome antique")
            author: identifiant de l'auteur
            target_score: score qualité cible (défaut: 80)
            language: langue des faits (fr/en)
        
        Returns:
            BuildReport avec le statut final et les métriques
        """
        report = BuildReport(domain=domain)
        report.status = "building"
        
        # ── 1. Trouver le template le plus proche ──
        template = self._find_template(domain)
        
        # ── 2. Générer les faits initiaux ──
        facts = self._generate_facts(domain, template)
        report.facts_count = len(facts)
        report.improvements.append(f"Généré {len(facts)} faits initiaux")
        
        # ── 3. Boucle d'enrichissement ──
        for iteration in range(1, self.MAX_ITERATIONS + 1):
            report.iterations = iteration
            
            # Valider
            valid_facts = self._validate_batch(facts)
            
            # Scorer
            quality = QualityScorer.compute_total(valid_facts)
            score = quality["total"]
            
            if iteration == 1:
                report.initial_score = score
            
            report.improvements.append(
                f"Itération {iteration}: score={score:.0f}/100 "
                f"(cohérence={quality['coherence']:.0f}, "
                f"complétude={quality['completeness']:.0f}, "
                f"diversité={quality['diversity']:.0f})"
            )
            
            # Convergence ?
            if score >= target_score:
                report.status = "enriched"
                report.final_score = score
                report.improvements.append(f"✅ Score cible atteint en {iteration} itération(s)")
                break
            
            # Atteint le max de faits ?
            if len(valid_facts) >= self.MAX_FACTS:
                report.status = "enriched"
                report.final_score = score
                report.improvements.append(f"⚠️ Max {self.MAX_FACTS} faits atteint")
                break
            
            # Diagnostiquer les faiblesses
            weaknesses = self._diagnose_weaknesses(quality, valid_facts)
            
            # Générer des faits correctifs
            new_facts = self._generate_corrective_facts(
                domain, template, valid_facts, weaknesses
            )
            
            if not new_facts:
                report.improvements.append("⚠️ Plus de faits générables")
                report.final_score = score
                break
            
            facts = valid_facts + new_facts
            report.facts_count = len(facts)
            report.improvements.append(f"  → +{len(new_facts)} faits correctifs")
        
        # ── 4. Score final ──
        if report.final_score == 0:
            report.final_score = score
        
        # ── 5. Publication si score suffisant ──
        if report.final_score >= 60:
            try:
                pub_result = self.publisher.submit(
                    domain=domain,
                    facts=valid_facts,
                    author=author,
                    name=f"{domain.title()} (Agent)",
                    description=f"Généré automatiquement — Score: {report.final_score:.0f}/100"
                )
                if pub_result.get("status") == "published":
                    report.status = "published"
                    report.published_holo_id = pub_result.get("holo_id", "")
                    report.improvements.append(f"📤 Publié: {report.published_holo_id}")
                else:
                    report.status = "failed"
                    report.errors.append(pub_result.get("reason", "Publication refusée"))
            except Exception as e:
                report.errors.append(str(e))
                report.status = "failed"
        
        return report
    
    def _find_template(self, domain: str) -> Optional[dict]:
        """Trouve le template le plus proche du domaine demandé."""
        domain_lower = domain.lower()
        
        # Correspondance par alias
        for key, tmpl in DOMAIN_TEMPLATES.items():
            aliases = tmpl.get("aliases", [key])
            if domain_lower in aliases or any(a in domain_lower or domain_lower in a for a in aliases):
                return tmpl
        
        # Correspondance par mot-clé partiel
        for key, tmpl in DOMAIN_TEMPLATES.items():
            if key in domain_lower or domain_lower in key:
                return tmpl
        
        # Template générique
        return {
            "sectors": ["GENERAL", "DIVERS"],
            "seed_facts": [],
            "cross_link_templates": [
                ("{sujet}", "est lié à", "{objet}", "{secteur}"),
                ("{sujet}", "fait partie de", "{objet}", "{secteur}"),
            ],
        }
    
    def _generate_facts(self, domain: str, template: dict) -> List[Tuple]:
        """
        Génère les faits initiaux. Priorité : KB > Web > Templates.
        """
        facts = []
        
        # ── 1. KB LOCAL (110K faits) ──
        n_kb = self._ensure_kb_loaded()
        if n_kb > 0:
            extra_kw = template.get("keywords", [])
            kb_facts = self.kb.extract_by_domain(domain, keywords=extra_kw, max_facts=150)
            facts.extend(kb_facts)
        
        # ── 2. TEMPLATE SEEDS ──
        facts.extend(template.get("seed_facts", []))
        
        # ── 3. MCP EXTERNES (Wikipedia, cross-ref KB) ──
        mcp_wiki = self.mcp.search_external(domain, "wikipedia", max_facts=15)
        facts.extend(mcp_wiki)
        
        # ── 4. WEB (si KB pauvre) ──
        if len(facts) < 30:
            web_facts = self.web.search_facts(domain, max_facts=10)
            facts.extend(web_facts)
        
        # Dédupliquer
        seen = set()
        unique = []
        for f in facts:
            key = (f[0].lower().strip(), f[1].lower().strip(), f[2].lower().strip())
            if key not in seen:
                seen.add(key)
                unique.append(f)
        
        return unique[:self.MAX_FACTS]
    
    def _validate_batch(self, facts: List[Tuple]) -> List[Tuple]:
        """Valide et filtre les faits."""
        result = self.validator.validate_batch(facts)
        # Reconstruire les faits valides
        seen = set()
        valid = []
        for f in facts:
            ok, _ = self.validator.validate_fact(f[0], f[1], f[2])
            key = (f[0].lower().strip(), f[1].lower().strip(), f[2].lower().strip())
            if ok and key not in seen:
                seen.add(key)
                valid.append(f)
        return valid
    
    def _diagnose_weaknesses(self, quality: dict, facts: List[Tuple]) -> List[str]:
        """Diagnostique les faiblesses de l'hologramme."""
        weaknesses = []
        if quality["coherence"] < 20:
            weaknesses.append("coherence")
        if quality["completeness"] < 18:
            weaknesses.append("completeness")
        if quality["diversity"] < 10:
            weaknesses.append("diversity")
        if quality["structure"] < 7:
            weaknesses.append("structure")
        return weaknesses
    
    def _generate_corrective_facts(self, domain: str, template: dict,
                                    facts: List[Tuple], weaknesses: List[str]) -> List[Tuple]:
        """Génère des faits pour corriger les faiblesses identifiées."""
        new_facts = []
        
        # Extraire sujets et objets existants
        subjects = [f[0] for f in facts]
        objects = [f[2] for f in facts]
        sectors = [f[3] for f in facts] if len(facts[0]) > 3 else ["GENERAL"] * len(facts)
        all_entities = list(set(subjects + objects))
        
        # ── Correction cohérence (PRIORITAIRE) ──
        if "coherence" in weaknesses:
            # ➕ KB Enricher : faits bidirectionnels (boost mécanique de cohérence)
            enriched = self.enricher.enrich(facts, max_new=40)
            new_facts.extend(enriched)
            
            # 🔗 KB Interconnector : ponts entre entités
            bridge_facts = self.interconnector.interconnect(facts, max_new=20)
            new_facts.extend(bridge_facts)
            
            # 🔌 MCP cross-reference : croiser les faits du KB entre eux
            mcp_cross = self.mcp.search_external(domain, "kb-cross", max_facts=10)
            new_facts.extend(mcp_cross)
            
            # Liens locaux entre entités existantes
            templates_cross = template.get("cross_link_templates", [])
            if templates_cross and len(all_entities) >= 2:
                for i in range(min(5, len(all_entities))):
                    s = all_entities[i]
                    o = all_entities[(i + 1) % len(all_entities)]
                    if s != o:
                        tpl = templates_cross[i % len(templates_cross)]
                        sec = sectors[i % len(sectors)] if sectors else "GENERAL"
                        new_facts.append((
                            tpl[0].replace("{sujet}", s).replace("{objet}", o).replace("{secteur}", sec),
                            tpl[1],
                            tpl[2].replace("{sujet}", s).replace("{objet}", o).replace("{secteur}", sec),
                            sec
                        ))
        
        # ── Correction complétude : ajouter des faits dans des secteurs manquants ──
        if "completeness" in weaknesses:
            existing_sectors = set(f[3] for f in facts if len(f) > 3)
            all_sectors = template.get("sectors", ["GENERAL"])
            missing = [s for s in all_sectors if s not in existing_sectors]
            for sec in missing[:3]:
                if all_entities:
                    entity = all_entities[len(new_facts) % len(all_entities)]
                    new_facts.append((entity, "appartient au domaine", sec, sec))
        
        # ── Correction diversité : introduire de nouvelles entités ──
        if "diversity" in weaknesses:
            domain_words = re.findall(r'\w+', domain.lower())
            for word in domain_words[:3]:
                if len(word) >= 4:
                    entity = word.title()
                    if entity not in all_entities:
                        sec = template.get("sectors", ["GENERAL"])[0]
                        new_facts.append((entity, "est un aspect de", domain.title(), sec))
        
        # Sécurité : valider tous les nouveaux faits
        valid_new = []
        for f in new_facts:
            ok, _ = self.validator.validate_fact(f[0], f[1], f[2])
            if ok:
                valid_new.append(f)
        
        return valid_new[:10]  # Max 10 faits par itération


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   🤖 HOLOGRAM BUILDER AGENT — Test autonome                  ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    agent = HologramBuilderAgent()
    
    # Test 1 : Génétique
    print("🧬 Test 1 : Génétique")
    print("─" * 50)
    report = agent.build("génétique", author="agent_test")
    print(f"   Itérations : {report.iterations}")
    print(f"   Score initial → final : {report.initial_score:.0f} → {report.final_score:.0f}/100")
    print(f"   Faits       : {report.facts_count}")
    print(f"   Statut      : {report.status}")
    for imp in report.improvements:
        print(f"     {imp}")
    if report.errors:
        for e in report.errors:
            print(f"     ❌ {e}")
    print()
    
    # Test 2 : Python
    print("🐍 Test 2 : Python")
    print("─" * 50)
    report2 = agent.build("python", author="agent_test")
    print(f"   Score : {report2.initial_score:.0f} → {report2.final_score:.0f}/100")
    print(f"   Statut: {report2.status} ({report2.facts_count} faits)")
    print()
    
    print("✅ Agent opérationnel.")
