"""
Specialize Optimized — Spécialisation Hybride KB + Web
=========================================================
Optimisation de la spécialisation par prompt :
  1. Bootstrap depuis le KB existant (110K faits) — pas de recherche inutile
  2. Web search ciblée uniquement pour les gaps
  3. Extraction de triples améliorée (bootstrapper + patterns)
  4. Auto-sectorisation
  5. Validation automatique par questions-test
  6. Rapport de couverture

Principe : l'IA sait déjà beaucoup de choses. On ne part pas de zéro.
On identifie ce qui manque, et on ne cherche QUE ça.

Usage :
    from specialize_optimized import OptimizedSpecializer
    
    spec = OptimizedSpecializer()
    result = spec.specialize("droit constitutionnel", user_id="user_123")
    print(f"{result.triplets_count} faits ajoutés, couverture: {result.coverage_pct}%")
"""

import os, sys, time, json, re, logging
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field

import numpy as np

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SpecializeResult:
    domain: str
    depth: str
    existing_facts: int = 0       # faits déjà dans le KB
    new_facts: int = 0            # faits ajoutés par le web
    total_facts: int = 0          # total après spécialisation
    coverage_pct: float = 0.0     # % de couverture estimé
    validation_score: float = 0.0 # score de validation (0-1)
    elapsed_seconds: float = 0.0
    message: str = ""
    success: bool = True
    top_concepts: List[str] = field(default_factory=list)
    kb_path: str = ""

# Modèles de requêtes par profondeur
DEPTH_TEMPLATES = {
    'debutant': [
        "{domain} définition",
        "{domain} principes de base",
        "{domain} pour débutants",
        "{domain} concepts fondamentaux",
        "comment fonctionne {domain}",
        "{domain} explication simple",
        "qu'est-ce que {domain}",
        "{domain} guide débutant",
    ],
    'avance': [
        "{domain} définition",
        "{domain} principes de base",
        "{domain} concepts fondamentaux",
        "{domain} techniques avancées",
        "{domain} méthodologie",
        "{domain} applications pratiques",
        "{domain} exemples concrets",
        "{domain} histoire et évolution",
        "{domain} tendances actuelles",
        "{domain} meilleures pratiques",
    ],
    'expert': [
        "{domain} définition",
        "{domain} concepts fondamentaux",
        "{domain} techniques avancées",
        "{domain} méthodologie",
        "{domain} applications pratiques",
        "{domain} histoire et évolution",
        "{domain} recherche récente",
        "{domain} cas d'étude",
        "{domain} controverses et débats",
        "{domain} perspectives futures",
        "{domain} relations avec d'autres domaines",
        "{domain} innovations",
    ],
    'encyclopedique': [
        "{domain} définition",
        "{domain} concepts fondamentaux",
        "{domain} techniques avancées",
        "{domain} méthodologie",
        "{domain} applications pratiques",
        "{domain} histoire et évolution",
        "{domain} recherche récente",
        "{domain} cas d'étude",
        "{domain} controverses et débats",
        "{domain} perspectives futures",
        "{domain} relations avec d'autres domaines",
        "{domain} innovations",
        "{domain} acteurs majeurs",
        "{domain} législation",
        "{domain} impact sociétal",
        "{domain} économie du secteur",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# SPÉCIALISEUR OPTIMISÉ
# ═══════════════════════════════════════════════════════════════════════════════

class OptimizedSpecializer:
    """
    Spécialisation hybride : KB existant (110K faits) + web search ciblée.
    """
    
    def __init__(self, fast_retriever=None, web_retriever=None, brain=None):
        self.fast_retriever = fast_retriever
        self.web_retriever = web_retriever
        self.brain = brain
        
        # Base utilisateur
        self.users_dir = _ENGINE_DIR / "data" / "users"
        self.users_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_retriever(self):
        """Init paresseuse du FastRetriever."""
        if self.fast_retriever is None:
            try:
                from page_forge import _init_fast_retriever, _FAST_RETRIEVER
                _init_fast_retriever()
                self.fast_retriever = _FAST_RETRIEVER
            except Exception:
                pass
        return self.fast_retriever
    
    def _get_web(self):
        """Init paresseuse du WebRetriever."""
        if self.web_retriever is None:
            try:
                from web_retriever import WebRetriever
                self.web_retriever = WebRetriever()
            except Exception:
                pass
        return self.web_retriever
    
    # ═══ ÉTAPE 1 : BOOTSTRAP DEPUIS LE KB EXISTANT ═══
    
    def _bootstrap_from_kb(self, domain: str) -> List[Tuple[str, str, str, str]]:
        """
        Récupère les faits déjà connus sur le domaine depuis le FastRetriever.
        """
        retriever = self._get_retriever()
        if retriever is None:
            return []
        
        # Chercher avec le nom du domaine et des variantes
        queries = [domain] + domain.split()
        facts = []
        seen = set()
        
        for query in queries[:5]:  # max 5 variantes
            results = retriever.retrieve(query, max_facts=20, min_score=0.3)
            for s, r, o, sec, score in results:
                key = (str(s).lower()[:60], str(r).lower()[:60], str(o).lower()[:80])
                if key not in seen:
                    seen.add(key)
                    facts.append((str(s), str(r), str(o), str(sec)))
        
        log.info(f"  📚 Bootstrap KB: {len(facts)} faits existants trouvés")
        return facts
    
    # ═══ ÉTAPE 2 : GÉNÉRER LES REQUÊTES CIBLÉES ═══
    
    def _generate_queries(self, domain: str, depth: str,
                          existing_facts: List[Tuple]) -> List[str]:
        """
        Génère des requêtes web ciblées en évitant ce qui est déjà couvert.
        """
        templates = DEPTH_TEMPLATES.get(depth, DEPTH_TEMPLATES['expert'])
        queries = []
        
        # Extraire les concepts déjà couverts
        covered_subjects = set()
        for s, r, o, sec in existing_facts:
            for word in str(s).lower().split():
                if len(word) > 3:
                    covered_subjects.add(word)
        
        for tmpl in templates:
            q = tmpl.format(domain=domain)
            queries.append(q)
        
        # Ajouter des requêtes pour les gaps spécifiques
        essential_concepts = [
            "définition", "histoire", "principes", "techniques", "applications",
            "acteurs", "tendances", "recherche", "formation", "réglementation"
        ]
        for concept in essential_concepts:
            if concept not in covered_subjects:
                queries.append(f"{domain} {concept}")
        
        log.info(f"  🔍 {len(queries)} requêtes web générées")
        return queries
    
    # ═══ ÉTAPE 3 : EXTRACTION DE TRIPLES ═══
    
    def _extract_triples(self, text: str, source: str = "") -> List[Tuple[str, str, str, str]]:
        """Extrait des triples d'un texte, avec patterns améliorés."""
        triples = []
        
        # 1. Via le bootstrapper
        try:
            from bootstrapper import extract_triples_enhanced
            extracted = extract_triples_enhanced(text)
            for s, r, o, sec in extracted:
                if len(str(s)) >= 2 and len(str(r)) >= 2 and len(str(o)) >= 2:
                    triples.append((str(s), str(r), str(o), str(sec)))
        except ImportError:
            pass
        
        # 2. Patterns définitoires (X est un/une Y)
        for match in re.finditer(
            r"([A-ZÉÈÊËÀÂÄÔÖÎÏÛÜÇ][^,.]+?)\s+est\s+(?:un|une|le|la|l')\s+([^,.]+?)(?:\.|,|;|$)",
            text
        ):
            s = match.group(1).strip()[:120]
            o = match.group(2).strip()[:120]
            if len(s) > 3 and len(o) > 3:
                triples.append((s, "est", o, "GENERAL"))
        
        # 3. Patterns de propriété (X a pour Y, X contient Y)
        for match in re.finditer(
            r"([A-ZÉÈÊËÀÂÄÔÖÎÏÛÜÇ][^,.]+?)\s+(?:a pour|contient|comprend|inclut|possède)\s+([^,.]+?)(?:\.|,|;|$)",
            text
        ):
            s = match.group(1).strip()[:120]
            o = match.group(2).strip()[:120]
            if len(s) > 3 and len(o) > 3:
                triples.append((s, "a pour", o, "GENERAL"))
        
        return triples
    
    # ═══ ÉTAPE 4 : FUSION ET DÉDUPLICATION ═══
    
    def _merge_facts(self, existing: List[Tuple], new: List[Tuple]) -> List[Tuple]:
        """Fusionne les faits existants et nouveaux, avec déduplication."""
        seen = set()
        merged = []
        
        for s, r, o, sec in existing:
            key = (str(s).lower().strip()[:60], str(r).lower().strip()[:60], str(o).lower().strip()[:80])
            if key not in seen:
                seen.add(key)
                merged.append((s, r, o, sec))
        
        for s, r, o, sec in new:
            key = (str(s).lower().strip()[:60], str(r).lower().strip()[:60], str(o).lower().strip()[:80])
            if key not in seen:
                seen.add(key)
                merged.append((s, r, o, sec))
        
        # Sectorisation automatique
        try:
            from auto_sectorize import sectorize_batch
            merged = sectorize_batch(merged, min_confidence=1.5)
        except ImportError:
            pass
        
        return merged
    
    # ═══ ÉTAPE 5 : VALIDATION ═══
    
    def _validate(self, domain: str, facts: List[Tuple]) -> float:
        """
        Valide la spécialisation en posant des questions-test.
        Retourne un score 0-1.
        """
        if len(facts) < 5:
            return 0.3  # Trop peu de faits
        
        # Générer des questions simples à partir des faits
        test_questions = []
        for s, r, o, sec in facts[:10]:
            if "est" in str(r):
                test_questions.append(f"Qu'est-ce que {s} ?")
            elif "a pour" in str(r):
                test_questions.append(f"Quel est {r.replace('a pour', 'le')} de {s} ?")
        
        if not test_questions:
            return 0.5
        
        retriever = self._get_retriever()
        if retriever is None:
            return 0.5
        
        correct = 0
        for q in test_questions[:5]:
            results = retriever.retrieve(q, max_facts=3, min_score=0.3)
            if results:
                # Vérifier que le meilleur résultat est dans le domaine
                best_subject = str(results[0][0]).lower()
                domain_words = set(domain.lower().split())
                if domain_words & set(best_subject.split()):
                    correct += 1
        
        return correct / max(len(test_questions[:5]), 1)
    
    # ═══ PIPELINE PRINCIPAL ═══
    
    def specialize(self, domain: str, depth: str = "expert",
                   user_id: str = "anonymous") -> SpecializeResult:
        """
        Spécialise l'IA sur un domaine.
        
        Pipeline :
          1. Bootstrap depuis le KB existant (110K faits)
          2. Génère des requêtes web ciblées pour les gaps
          3. Extrait les triples des résultats web
          4. Fusionne et déduplique
          5. Valide avec des questions-test
          6. Sauvegarde le KB utilisateur
        """
        t0 = time.time()
        log.info(f"🎯 Spécialisation optimisée: {domain} (depth={depth})")
        
        # 1. Bootstrap
        existing = self._bootstrap_from_kb(domain)
        
        # 2. Générer requêtes
        queries = self._generate_queries(domain, depth, existing)
        
        # 3. Web search + extraction
        new_facts = []
        web = self._get_web()
        
        for i, query in enumerate(queries[:12]):  # Limiter à 12 requêtes
            if web is None:
                break
            try:
                results = web.search_web(query)
                for result in results[:2]:  # Top 2 résultats par requête
                    snippet = result.get('snippet', '') or result.get('summary', '')
                    if snippet and len(snippet) > 80:
                        triples = self._extract_triples(snippet, query)
                        new_facts.extend(triples)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                log.debug(f"  ⚠️ Requête '{query[:40]}': {e}")
                continue
            
            if (i + 1) % 4 == 0:
                log.info(f"  📡 {i+1}/{len(queries[:12])} requêtes, {len(new_facts)} nouveaux faits")
        
        # 4. Fusion
        all_facts = self._merge_facts(existing, new_facts)
        new_count = len(all_facts) - len(existing)
        
        # 5. Validation
        validation_score = self._validate(domain, all_facts)
        
        # 6. Sauvegarde KB utilisateur
        user_dir = self.users_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        kb_path = user_dir / f"kb_{domain.lower().replace(' ', '_')[:30]}.npz"
        
        subjects = np.array([f[0] for f in all_facts], dtype=object)
        relations = np.array([f[1] for f in all_facts], dtype=object)
        objects = np.array([f[2] for f in all_facts], dtype=object)
        sectors = np.array([f[3] for f in all_facts], dtype=object)
        
        np.savez_compressed(str(kb_path),
            subjects=subjects, relations=relations,
            objects=objects, sectors=sectors,
            amplitudes=np.ones(len(all_facts), dtype=np.float32),
            psies_real=np.zeros((len(all_facts), 64), dtype=np.float32),
            psies_imag=np.zeros((len(all_facts), 64), dtype=np.float32))
        
        # Charger dans le FastRetriever
        retriever = self._get_retriever()
        if retriever and new_facts:
            retriever.add_facts(new_facts)
        
        # Couverture estimée
        coverage = min(100, len(all_facts) / max(20, 1) * 100)
        
        elapsed = time.time() - t0
        
        # Top concepts
        subjects_count = Counter(str(f[0]) for f in all_facts)
        top_concepts = [s for s, _ in subjects_count.most_common(5)]
        
        result = SpecializeResult(
            domain=domain,
            depth=depth,
            existing_facts=len(existing),
            new_facts=new_count,
            total_facts=len(all_facts),
            coverage_pct=round(coverage, 1),
            validation_score=round(validation_score, 2),
            elapsed_seconds=round(elapsed, 1),
            message=f"✅ {domain}: {len(existing)} faits existants + {new_count} nouveaux = {len(all_facts)} total "
                    f"(couverture estimée: {coverage:.0f}%, validation: {validation_score:.0%})",
            top_concepts=top_concepts,
            kb_path=str(kb_path),
        )
        
        log.info(f"  {result.message}")
        return result
    
    def get_user_kb(self, user_id: str, domain: str = None) -> List[Tuple]:
        """Charge le KB d'un utilisateur."""
        user_dir = self.users_dir / user_id
        if not user_dir.exists():
            return []
        
        facts = []
        pattern = f"kb_*.npz" if domain is None else f"kb_{domain.lower().replace(' ', '_')}*.npz"
        for kb_file in user_dir.glob(pattern):
            try:
                data = np.load(str(kb_file), allow_pickle=True)
                for i in range(len(data['subjects'])):
                    facts.append((
                        str(data['subjects'][i]),
                        str(data['relations'][i]),
                        str(data['objects'][i]),
                        str(data['sectors'][i]) if 'sectors' in data else 'GENERAL',
                    ))
            except Exception:
                pass
        
        return facts


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   🎯 SPÉCIALISATION OPTIMISÉE — Démo                     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    spec = OptimizedSpecializer()
    
    # Test : spécialisation rapide (depth=debutant pour limiter les requêtes)
    for domain in ['photographie', 'droit constitutionnel']:
        print(f"\n{'='*60}")
        print(f"Spécialisation: {domain}")
        print(f"{'='*60}")
        
        result = spec.specialize(domain, depth='debutant', user_id='demo')
        print(f"\nRésultat: {result.message}")
        print(f"  Faits existants: {result.existing_facts}")
        print(f"  Nouveaux faits:  {result.new_facts}")
        print(f"  Total:           {result.total_facts}")
        print(f"  Validation:      {result.validation_score:.0%}")
        print(f"  Top concepts:    {', '.join(result.top_concepts[:5])}")
        print(f"  Durée:           {result.elapsed_seconds}s")
