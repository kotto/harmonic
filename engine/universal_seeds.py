"""
🌐 Universal Seed Generator — Tout domaine, zéro template
============================================================
Génère un hologramme de qualité pour N'IMPORTE QUEL domaine
en extrayant et interconnectant les entités du KB existant.

PLUS BESOIN de définir manuellement les entités.
Le KB 358K est la source unique de connaissance.

Usage:
  gen = UniversalSeedGenerator(kb)
  facts = gen.generate("jardinage urbain")
  # → 500+ faits interconnectés, cohérence > 15/30
"""

import sys, os, time, re, hashlib, random
from pathlib import Path
from typing import List, Tuple, Dict, Set
from collections import Counter, defaultdict
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

PHI = 1.618033988749895

class UniversalSeedGenerator:
    """
    Générateur universel : extrait les entités du KB,
    construit la hiérarchie automatiquement, génère les faits.
    """
    
    def __init__(self, kb_source):
        self.kb = kb_source
        self._entity_cache: Dict[str, List[Tuple]] = {}
    
    def generate(self, domain: str, max_facts: int = 500) -> List[Tuple]:
        """
        Génère des faits interconnectés pour n'importe quel domaine.
        
        Étapes :
        1. Extraire les entités du KB pertinentes au domaine
        2. Construire une hiérarchie automatique
        3. Générer les faits bidirectionnels
        4. Ajouter des connexions croisées (φ-diversité)
        """
        t0 = time.time()
        facts = []
        seen = set()
        
        def add(s, r, o, sec="EXTRACTED"):
            key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
            if key not in seen:
                seen.add(key)
                facts.append((s[:120], r[:120], o[:120], sec))
        
        def add_bidirectional(s, r, o, inv_r, sec="EXTRACTED"):
            add(s, r, o, sec)
            add(o, inv_r, s, sec)
        
        # ── 1. Extraire les entités du KB ──
        entities = self._extract_entities(domain, max_entities=60)
        if not entities:
            return []
        
        # ── 2. Construire une hiérarchie automatique ──
        # Grouper les entités par similarité sémantique (mots communs)
        hierarchy = self._build_auto_hierarchy(entities, domain)
        
        # ── 3. Générer les faits hiérarchiques ──
        for category, members in hierarchy.items():
            for member in members:
                add_bidirectional(member, "est un type de", category, 
                                 "a pour sous-type", "EXTRACTED")
        
        # ── 4. Générer les faits de relation ──
        # Extraire les relations réelles du KB pour ces entités
        kb_relations = self._extract_relations(entities)
        
        for s, r, o in kb_relations[:100]:
            add(s, r, o, "KB")
        
        # ── 5. Connexions φ-croisées ──
        all_entities = list(set(
            [e for cat, members in hierarchy.items() for e in members] + entities
        ))
        
        phi_step = max(1, int(len(all_entities) * 0.382))
        relations_pool = [
            "est relié à", "interagit avec", "influence", "est connecté à",
            "partage des propriétés avec", "est associé à", "dépend de",
            "contribue à", "fait partie du système de", "est en relation avec"
        ]
        
        for i, e1 in enumerate(all_entities[:50]):
            e2 = all_entities[(i + phi_step) % len(all_entities)]
            if e1 != e2:
                rel = relations_pool[(i * int(PHI * 100)) % len(relations_pool)]
                add(e1, rel, e2, "PHI_CROSS")
                # Inverse
                inv_rel = relations_pool[((i+1) * int(PHI * 100)) % len(relations_pool)]
                if inv_rel != rel:
                    add(e2, inv_rel, e1, "PHI_CROSS")
        
        # ── 6. Connexions Fibonacci (φ-naturelles) ──
        fib = [1, 2, 3, 5, 8, 13, 21]
        for offset in fib:
            for i in range(len(all_entities[:40])):
                j = (i + offset) % len(all_entities[:40])
                if i < j:
                    e1, e2 = all_entities[i], all_entities[j]
                    rel = relations_pool[offset % len(relations_pool)]
                    add(e1, rel, e2, "FIB")
        
        elapsed = time.time() - t0
        print(f"  🌐 Universal: {len(facts)} faits pour '{domain}' en {elapsed:.2f}s "
              f"({len(entities)} entités, {len(hierarchy)} catégories)")
        
        return facts[:max_facts]
    
    def _extract_entities(self, domain: str, max_entities: int = 60) -> List[str]:
        """Extrait les entités pertinentes du KB."""
        if not self.kb._facts:
            self.kb.load()
        
        # Chercher par mots-clés dans le KB
        search_terms = set()
        for word in re.findall(r'\w+', domain.lower()):
            if len(word) >= 3:
                search_terms.add(word)
        
        if not search_terms:
            return []
        
        # Trouver les faits pertinents
        fact_scores = Counter()
        for term in search_terms:
            if term in self.kb._index:
                for idx in self.kb._index[term]:
                    fact_scores[idx] += 1
        
        # Extraire les entités uniques (sujets + objets)
        entities = []
        seen_entities = set()
        for idx, score in fact_scores.most_common(500):
            f = self.kb._facts[idx]
            for entity in [f[0], f[2]]:
                e_clean = entity.lower().strip()
                if e_clean not in seen_entities and len(e_clean) >= 3:
                    seen_entities.add(e_clean)
                    entities.append(entity.strip()[:80])
                    if len(entities) >= max_entities:
                        break
            if len(entities) >= max_entities:
                break
        
        # Si pas assez d'entités, ajouter les mots du domaine eux-mêmes
        if len(entities) < 5:
            for word in re.findall(r'\w+', domain):
                if len(word) >= 3 and word.lower() not in seen_entities:
                    entities.append(word.title())
        
        return entities
    
    def _build_auto_hierarchy(self, entities: List[str], domain: str) -> Dict[str, List[str]]:
        """
        Construit une hiérarchie automatique en groupant les entités
        par similarité (mots communs, préfixes partagés).
        """
        hierarchy = defaultdict(list)
        
        # Stratégie 1 : grouper par premier mot commun
        for e in entities:
            words = e.lower().split()
            if len(words) >= 2:
                # Le premier mot comme catégorie potentielle
                cat = words[0].title()
                if len(cat) >= 3:
                    hierarchy[cat].append(e)
            else:
                # Mot seul → catégorie = première lettre ou mot complet
                hierarchy[domain.title()].append(e)
        
        # Nettoyer : fusionner les catégories avec < 2 membres
        small_cats = [cat for cat, members in hierarchy.items() if len(members) < 2]
        for cat in small_cats:
            members = hierarchy.pop(cat)
            for m in members:
                hierarchy[domain.title()].append(m)
        
        # Limiter à 10 catégories max
        if len(hierarchy) > 10:
            # Garder les plus grandes
            sorted_cats = sorted(hierarchy.items(), key=lambda x: len(x[1]), reverse=True)
            hierarchy = dict(sorted_cats[:10])
        
        return dict(hierarchy)
    
    def _extract_relations(self, entities: List[str]) -> List[Tuple[str, str, str]]:
        """Extrait les relations réelles entre ces entités depuis le KB."""
        entity_set = set(e.lower().strip() for e in entities)
        relations = []
        
        for f in self.kb._facts[:50000]:  # Limiter la recherche
            s = f[0].lower().strip()
            o = f[2].lower().strip()
            if s in entity_set or o in entity_set:
                relations.append((f[0][:80], f[1][:80], f[2][:80]))
                if len(relations) >= 200:
                    break
        
        return relations


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from hologram_builder_agent import KnowledgeBaseSource, QualityScorer
    
    kb = KnowledgeBaseSource()
    kb.load()
    print(f"KB: {len(kb._facts):,} faits\n")
    
    gen = UniversalSeedGenerator(kb)
    
    # Test sur 3 domaines jamais vus
    test_domains = [
        "jardinage urbain",
        "philosophie stoïcienne", 
        "cuisine moléculaire",
    ]
    
    for domain in test_domains:
        print(f"🧪 {domain}:")
        facts = gen.generate(domain, max_facts=300)
        if facts:
            q = QualityScorer.compute_total(facts)
            print(f"  ✅ {len(facts)} faits | coh {q['coherence']:.0f}/30 | "
                  f"div {q['diversity']:.0f}/15 | score {q['total']:.0f}/100 | grade {q['grade']}")
            # Afficher 3 échantillons
            for f in facts[:3]:
                print(f"    • {f[0][:40]} | {f[1][:25]} | {f[2][:40]}")
        else:
            print(f"  ❌ Aucune entité trouvée dans le KB")
        print()
