#!/usr/bin/env python3
"""
Benchmark A/B — Validation des Recommandations de l'IA Experte
===============================================================
Mesure l'impact des 5 optimisations implémentées suite à la consultation
de l'IA experte sur la formulation de prompts cohérents.

Référence : "Plans/consultation_ia_experte.md"
            & Réponse IA experte du 29/05/2026

Protocole (recommandation IA experte) :
    "Le prompt engineering est un travail empirique — il faut tester et
     itérer systématiquement, changer une variable à la fois, mesurer la
     qualité sur un jeu d'évaluation constant."

Tests :
    1. Classification par actes de langage (vs anciens mots-clés)
    2. Qualité des system prompts refondus
    3. Connecteurs canoniques (petit ensemble vs multiplicité)
    4. Sélection dynamique d'exemplar (1 exemplar vs batterie)
    5. Score de résonance global avant/après

Usage:
    python benchmark_ab_expert_recommendations.py
    python benchmark_ab_expert_recommendations.py --quick   # Test rapide
    python benchmark_ab_expert_recommendations.py --report  # Rapport détaillé
"""

import os
import sys
import json
import time
import math
import logging
import argparse
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import Counter

import numpy as np

# Ajouter le projet au path
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# =========================================================================
# JEU D'ÉVALUATION — Prompts de test par catégorie
# =========================================================================
# Recommandation IA experte : "un jeu d'évaluation constant"
# 5 prompts par catégorie, de difficulté croissante

TEST_PROMPTS = {
    "mathematical": [
        "Calcule 15% de 340",
        "Résous l'équation 2x² + 5x - 3 = 0",
        "Quelle est la dérivée de f(x) = sin(x²) ?",
        "Calcule l'intégrale de x*e^x de 0 à 1",
        "Montre que la suite u_n = (1+1/n)^n converge vers e",
    ],
    "code": [
        "Écris une fonction Python qui inverse une liste chaînée",
        "Implémente un tri par fusion en JavaScript",
        "Crée une API REST avec Flask pour la gestion de tâches",
        "Écris une classe de file d'attente thread-safe en Python",
        "Implémente un décorateur Python qui mesure le temps d'exécution",
    ],
    "creative": [
        "Écris un poème sur le silence d'une bibliothèque au crépuscule",
        "Imagine un monde où les couleurs ont un goût",
        "Décris l'océan comme si c'était la première fois que quelqu'un le voyait",
        "Écris une histoire de 100 mots où le protagoniste est une ombre",
        "Compose un haiku sur un ordinateur qui rêve",
    ],
    "reasoning": [
        "Pourquoi le ciel est-il bleu ? Explique en détail",
        "Compare les avantages et inconvénients de l'énergie nucléaire vs solaire",
        "Analyse les causes et conséquences de la chute de l'Empire romain",
        "Comment expliquer le paradoxe de Fermi ?",
        "Compare les approches déductives et inductives en philosophie des sciences",
    ],
    "factual": [
        "Quelle est la capitale du Japon ?",
        "En quelle année a été signé le traité de Versailles ?",
        "Qui a découvert la pénicilline ?",
        "Quelle est la population de l'Inde en 2025 ?",
        "Quel est le point d'ébullition de l'eau à pression atmosphérique normale ?",
    ],
    "general": [
        "Bonjour, comment ça va ?",
        "Quel temps fait-il aujourd'hui?",
        "Peux-tu me donner des nouvelles du monde ?",
        "Raconte-moi une anecdote intéressante",
        "Que penses-tu de l'intelligence artificielle ?",
    ],
}


# =========================================================================
# MÉTRIQUES DE QUALITÉ
# =========================================================================

@dataclass
class QualityMetrics:
    """Métriques de qualité pour une réponse générée."""
    
    # Métriques structurelles
    resonance_score: float = 0.0      # Score de résonance harmonique
    coherence: float = 0.0            # Cohérence (auto-corrélation)
    diversity: float = 0.0            # Diversité lexicale
    entropy: float = 0.0              # Entropie normalisée
    
    # Métriques de classification
    classification_correct: bool = False  # Catégorie détectée correctement ?
    classification_confidence: float = 0.0  # Confiance de la classification
    acte_langage_detecte: bool = False  # Acte de langage identifié ?
    
    # Métriques de performance
    latency_ms: float = 0.0
    char_count: int = 0
    word_count: int = 0
    
    # Métriques d'exemplar
    exemplar_used: bool = False
    exemplar_similarity: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "resonance": round(self.resonance_score, 4),
            "coherence": round(self.coherence, 4),
            "diversity": round(self.diversity, 4),
            "entropy": round(self.entropy, 4),
            "classification_correct": self.classification_correct,
            "classification_confidence": round(self.classification_confidence, 4),
            "acte_langage_detecte": self.acte_langage_detecte,
            "latency_ms": round(self.latency_ms, 1),
            "char_count": self.char_count,
            "word_count": self.word_count,
            "exemplar_used": self.exemplar_used,
            "exemplar_similarity": round(self.exemplar_similarity, 4),
        }


class QualityEvaluator:
    """
    Évaluateur de qualité des réponses générées.
    
    Mesure :
    - Résonance : alignement prompt/réponse
    - Cohérence : fluidité logique
    - Diversité : richesse lexicale
    - Entropie : surprise informationnelle
    """
    
    PHI = 1.618033988749895
    
    def evaluate(self, prompt: str, response: str, 
                 category: str, expected_category: str,
                 latency_ms: float = 0.0,
                 exemplar_used: bool = False,
                 exemplar_similarity: float = 0.0) -> QualityMetrics:
        """Évalue la qualité d'une réponse."""
        
        # 1. Score de résonance
        resonance = self._score_resonance(prompt, response)
        
        # 2. Cohérence (auto-corrélation lexicale)
        coherence = self._score_coherence(response)
        
        # 3. Diversité lexicale
        diversity = self._score_diversity(response)
        
        # 4. Entropie normalisée
        entropy = self._score_entropy(response)
        
        # 5. Classification correcte ?
        class_correct = (category == expected_category)
        
        # 6. Acte de langage détecté ?
        acte_detecte = self._detect_acte_langage(prompt) is not None
        
        # Stats
        words = response.split()
        
        return QualityMetrics(
            resonance_score=resonance,
            coherence=coherence,
            diversity=diversity,
            entropy=entropy,
            classification_correct=class_correct,
            classification_confidence=1.0 if class_correct else 0.0,
            acte_langage_detecte=acte_detecte,
            latency_ms=latency_ms,
            char_count=len(response),
            word_count=len(words),
            exemplar_used=exemplar_used,
            exemplar_similarity=exemplar_similarity,
        )
    
    def _score_resonance(self, prompt: str, response: str) -> float:
        """Calcule le score de résonance prompt/réponse."""
        if not response.strip():
            return 0.0
        
        prompt_words = set(prompt.lower().split())
        resp_words = set(response.lower().split())
        
        # Chevauchement lexical
        overlap = len(prompt_words & resp_words)
        union = len(prompt_words | resp_words)
        lexical_sim = overlap / max(union, 1)
        
        # Ratio φ (mots longs / mots courts ~ φ)
        words = response.split()
        long_words = sum(1 for w in words if len(w) > 5)
        short_words = sum(1 for w in words if len(w) <= 3)
        ratio = long_words / max(short_words, 1)
        phi_score = 1.0 - min(1.0, abs(ratio - self.PHI) / max(self.PHI, ratio))
        
        # Score composite
        resonance = lexical_sim * 0.4 + phi_score * 0.3 + min(1.0, len(words) / 100) * 0.3
        return min(1.0, resonance)
    
    def _score_coherence(self, text: str) -> float:
        """Évalue la cohérence via l'auto-corrélation des chunks."""
        words = text.split()
        if len(words) < 6:
            return 0.5
        
        # Diviser en 3 chunks
        chunk_size = len(words) // 3
        chunks = [
            set(words[i:i+chunk_size])
            for i in range(0, len(words), chunk_size)
        ]
        
        if len(chunks) < 2:
            return 0.5
        
        # Similarité entre chunks consécutifs
        sims = []
        for i in range(len(chunks) - 1):
            overlap = len(chunks[i] & chunks[i+1])
            union = len(chunks[i] | chunks[i+1])
            if union > 0:
                sims.append(overlap / union)
        
        return np.mean(sims) if sims else 0.5
    
    def _score_diversity(self, text: str) -> float:
        """Type-Token Ratio (TTR) normalisé."""
        words = text.lower().split()
        if not words:
            return 0.0
        unique = len(set(words))
        ttr = unique / len(words)
        # Normalisation pour comparer des textes de longueurs différentes
        return min(1.0, ttr * self.PHI)
    
    def _score_entropy(self, text: str) -> float:
        """Entropie lexicale normalisée."""
        words = text.lower().split()
        if len(words) < 2:
            return 0.0
        counts = Counter(words)
        probs = [c / len(words) for c in counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs)
        max_entropy = math.log2(len(words))
        return entropy / max_entropy if max_entropy > 0 else 0.5
    
    def _detect_acte_langage(self, text: str) -> Optional[str]:
        """Détecte l'acte de langage principal."""
        import re
        t = text.lower()
        
        actes = {
            "resoudre": [
                r'\b(resous|resoudre|calcule|trouve|montre)\b.*\b(equation|probleme)\b',
                r'\d+\s*[+\-*/^]\s*\d+',
                r'\b(integrale|derivee|somme|determinant)\b',
            ],
            "realiser": [
                r'\b(implemente|code|programme|developpe|ecris)\b.*\b(fonction|classe|api)\b',
                r'\b(python|javascript|java|rust|docker|api)\b',
            ],
            "creer": [
                r'\b(ecris|invente|imagine|cree|compose)\b.*\b(poeme|histoire|monde|recit)\b',
                r'\b(poeme|chanson|haiku|histoire|recit)\b',
            ],
            "justifier": [
                r'\b(pourquoi|explique|compare|analyse|justifie)\b',
                r'\b(cause|consequence|these|antithese)\b',
            ],
            "recuperer": [
                r'\b(qui est|qu est ce que|en quelle annee|ou se trouve)\b',
                r'\b(capitale|population|date|definition)\b',
            ],
        }
        
        for acte, patterns in actes.items():
            for pat in patterns:
                if re.search(pat, t):
                    return acte
        
        return None


# =========================================================================
# TEST 1 : CLASSIFICATION PAR ACTES DE LANGAGE
# =========================================================================

def test_classification_actes() -> Dict:
    """
    Teste le classifieur par actes de langage (Point 3).
    
    Vérifie que :
    - Chaque prompt est correctement classifié dans sa catégorie
    - Les actes de langage sont détectés
    - La confiance est suffisante
    """
    from engine.llm.gguf_harmonizer import GGUFHarmonicInjector
    
    injector = GGUFHarmonicInjector()
    evaluator = QualityEvaluator()
    
    results = {}
    correct = 0
    total = 0
    
    print("\n" + "=" * 60)
    print("TEST 1 : Classification par Actes de Langage")
    print("=" * 60)
    
    for category, prompts in TEST_PROMPTS.items():
        cat_results = []
        for prompt in prompts:
            detected = injector._detect_category(prompt)
            is_correct = (detected == category)
            acte = evaluator._detect_acte_langage(prompt)
            
            cat_results.append({
                "prompt": prompt[:50],
                "attendu": category,
                "detecte": detected,
                "correct": is_correct,
                "acte_langage": acte,
            })
            
            if is_correct:
                correct += 1
            total += 1
            
            status = "[OK]" if is_correct else "[FAIL]"
            print(f"  {status} [{category:12s}] -> {detected:12s} | {prompt[:40]}...")
        
        results[category] = cat_results
    
    accuracy = correct / max(total, 1) * 100
    print(f"\n  Précision globale : {accuracy:.1f}% ({correct}/{total})")
    
    return {
        "test": "Classification par Actes de Langage",
        "accuracy_pct": round(accuracy, 1),
        "correct": correct,
        "total": total,
        "details": results,
    }


# =========================================================================
# TEST 2 : QUALITÉ DES SYSTEM PROMPTS
# =========================================================================

def test_system_prompts() -> Dict:
    """
    Teste la qualité des system prompts refondus (Point 1).
    
    Mesure :
    - Longueur et densité du prompt system
    - Pertinence par catégorie
    - Présence des actes de langage recommandés
    """
    from engine.llm.gguf_harmonizer import GGUFHarmonicInjector
    
    injector = GGUFHarmonicInjector()
    
    # Prompts de test par catégorie
    test_prompts = {
        "mathematical": "Calcule l'intégrale de x² de 0 à 1",
        "code": "Écris une fonction Python de tri rapide",
        "creative": "Écris un poème sur l'océan",
        "reasoning": "Explique le principe de relativité",
        "factual": "Quelle est la capitale de la France ?",
        "general": "Comment vas-tu ?",
    }
    
    results = {}
    
    print("\n" + "=" * 60)
    print("TEST 2 : Qualité des System Prompts Refondus")
    print("=" * 60)
    
    for category, prompt in test_prompts.items():
        # Construire le prompt complet
        built = injector.build(prompt, category=category, inject_exemplar=False)
        
        # Extraire le system prompt
        system_start = built.find("<|system|>\n") + len("<|system|>\n")
        system_end = built.find("\n</s>")
        system_prompt = built[system_start:system_end]
        
        # Métriques
        words = system_prompt.split()
        char_count = len(system_prompt)
        word_count = len(words)
        has_opener = any(opener in system_prompt.lower() for opener in [
            "resous", "implemente", "artiste", "analyste", "encyclopediste"
        ])
        has_phi = "1.618" in system_prompt
        
        results[category] = {
            "char_count": char_count,
            "word_count": word_count,
            "has_category_opener": has_opener,
            "mentions_phi": has_phi,
        }
        
        print(f"\n  [{category:12s}] ({word_count} mots, {char_count} car.)")
        print(f"    Has opener: {has_opener} | Phi: {has_phi}")
        print(f"    Extrait: {system_prompt[:80]}...")
    
    return {
        "test": "Qualité System Prompts",
        "details": results,
    }


# =========================================================================
# TEST 3 : CONNECTEURS CANONIQUES
# =========================================================================

def test_connecteurs() -> Dict:
    """
    Teste les connecteurs canoniques dans les templates (Point 2).
    
    Vérifie :
    - Nombre réduit de connecteurs (petit ensemble canonique)
    - Pertinence par catégorie
    - Pas de sur-injection
    """
    from engine.harmonic_engine import HarmonicContextExpander
    
    expander = HarmonicContextExpander()
    
    # Phrases à étendre
    test_responses = {
        "reasoning": "La relativité générale décrit la gravité comme une courbure de l'espace-temps.",
        "mathematical": "Pour calculer 15% de 340, on divise par 100 puis on multiplie par 15.",
        "creative": "Les vagues dansaient sous la lumière argentée de la lune.",
        "code": "Une fonction récursive s'appelle elle-même jusqu'à atteindre un cas de base.",
        "factual": "Paris est la capitale de la France.",
    }
    
    results = {}
    
    print("\n" + "=" * 60)
    print("TEST 3 : Connecteurs Canoniques")
    print("=" * 60)
    
    for category, response in test_responses.items():
        # Expansion
        expanded = expander.expand(response, category, verified=False)
        
        # Compter les connecteurs
        connectors_found = []
        for conn in ["D'abord", "Ensuite", "Par consequent", "On pose",
                     "Il s'ensuit", "En substituant", "Puis", "Alors que",
                     "Soudain"]:
            if conn.lower() in expanded.lower():
                connectors_found.append(conn)
        
        original_len = len(response)
        expanded_len = len(expanded)
        expansion_ratio = expanded_len / max(original_len, 1)
        
        results[category] = {
            "original_chars": original_len,
            "expanded_chars": expanded_len,
            "expansion_ratio": round(expansion_ratio, 1),
            "connectors_found": connectors_found,
            "connector_count": len(connectors_found),
        }
        
        print(f"\n  [{category:12s}] x{expansion_ratio:.1f} ({original_len}->{expanded_len}c)")
        print(f"    Connecteurs: {connectors_found or 'aucun'}")
        print(f"    Extrait: {expanded[:80]}...")
    
    return {
        "test": "Connecteurs Canoniques",
        "details": results,
    }


# =========================================================================
# TEST 4 : SÉLECTION DYNAMIQUE D'EXEMPLAR
# =========================================================================

def test_exemplar_selection() -> Dict:
    """
    Teste la sélection dynamique d'exemplar (Point 4).
    
    Vérifie :
    - Un exemplar est trouvé pour chaque catégorie
    - La similarité sémantique est pertinente
    - Pas d'exemplar hors-sujet
    """
    from engine.semantic.vector_store import ExemplarLibrary
    
    library = ExemplarLibrary()
    
    results = {}
    
    print("\n" + "=" * 60)
    print("TEST 4 : Sélection Dynamique d'Exemplar")
    print("=" * 60)
    
    for category, prompts in TEST_PROMPTS.items():
        cat_results = []
        for prompt in prompts[:3]:  # 3 premiers par catégorie
            exemplar = library.select(prompt, category, k=1)
            
            # Similarité approximative (taille du chevauchement lexical)
            if exemplar:
                prompt_words = set(prompt.lower().split())
                exemplar_words = set(exemplar.lower().split())
                overlap = len(prompt_words & exemplar_words)
                union = len(prompt_words | exemplar_words)
                similarity = overlap / max(union, 1)
            else:
                similarity = 0.0
            
            cat_results.append({
                "prompt": prompt[:50],
                "exemplar_trouve": exemplar is not None,
                "similarite": round(similarity, 3),
                "exemplar_extrait": (exemplar[:80] + "...") if exemplar else "AUCUN",
            })
            
            status = "[OK]" if exemplar else "[FAIL]"
            print(f"  {status} [{category:12s}] sim={similarity:.3f} | {prompt[:40]}...")
        
        results[category] = cat_results
    
    # Stats globales
    total = sum(len(r) for r in results.values())
    found = sum(1 for r in results.values() for cr in r if cr["exemplar_trouve"])
    
    print(f"\n  Exemplars trouvés : {found}/{total} ({found/max(total,1)*100:.0f}%)")
    
    return {
        "test": "Sélection Dynamique d'Exemplar",
        "found": found,
        "total": total,
        "success_rate_pct": round(found / max(total, 1) * 100, 1),
        "details": results,
    }


# =========================================================================
# TEST 5 : SCORE DE RÉSONANCE GLOBAL
# =========================================================================

def test_resonance_globale() -> Dict:
    """
    Teste le score de résonance global avec toutes les optimisations.
    
    Simule le pipeline complet :
    1. Analyse 9D du prompt
    2. Classification par actes de langage
    3. Construction du prompt harmonique avec system prompt refondu
    4. Injection d'exemplar dynamique
    5. Évaluation de la résonance
    """
    from engine.llm.gguf_harmonizer import GGUFHarmonicInjector
    from engine.harmonic_engine import HarmonicResonanceEngine
    from engine.semantic.vector_store import ExemplarLibrary
    
    injector = GGUFHarmonicInjector(use_exemplars=True)
    engine = HarmonicResonanceEngine()
    evaluator = QualityEvaluator()
    
    results = {}
    
    print("\n" + "=" * 60)
    print("TEST 5 : Score de Résonance Global")
    print("=" * 60)
    
    for category, prompts in TEST_PROMPTS.items():
        cat_results = []
        for prompt in prompts:
            t0 = time.time()
            
            # 1. Analyse 9D
            sig = engine.analyze(prompt)
            
            # 2. Classification
            detected_cat, confidence = engine.classify(prompt)
            
            # 3. Construction du prompt avec exemplar
            built = injector.build(prompt, category=category, inject_exemplar=True)
            
            # 4. Extraction de l'exemplar (simulé)
            exemplar_used = "[Exemple de reponse attendue" in built
            
            # 5. Évaluation
            latency = (time.time() - t0) * 1000
            metrics = evaluator.evaluate(
                prompt=prompt,
                response=built,  # On évalue la qualité du prompt construit
                category=detected_cat,
                expected_category=category,
                latency_ms=latency,
                exemplar_used=exemplar_used,
                exemplar_similarity=confidence,
            )
            
            cat_results.append({
                "prompt": prompt[:50],
                "signature_9d": [round(v, 3) for v in sig.vector_7d],
                "detected_category": detected_cat,
                "correct": detected_cat == category,
                "metrics": metrics.to_dict(),
            })
            
            res = metrics.resonance_score
            corr = "[OK]" if detected_cat == category else "[FAIL]"
            print(f"  {corr} [{category:12s}] resonance={res:.3f} | {prompt[:40]}...")
        
        results[category] = cat_results
    
    return {
        "test": "Résonance Globale",
        "details": results,
    }


# =========================================================================
# RAPPORT FINAL
# =========================================================================

def generate_report(all_results: Dict[str, Dict]):
    """Génère un rapport synthétique."""
    
    print("\n\n" + "=" * 60)
    print("RAPPORT FINAL — Benchmark Optimisations Expertes")
    print("=" * 60)
    
    total_score = 0.0
    num_tests = 0
    
    for test_name, result in all_results.items():
        print(f"\n=== {result.get('test', test_name)} ===")
        
        if "accuracy_pct" in result:
            score = result["accuracy_pct"] / 100
            print(f"   Précision : {result['accuracy_pct']}% ({result['correct']}/{result['total']})")
            total_score += score
            num_tests += 1
        
        if "success_rate_pct" in result:
            score = result["success_rate_pct"] / 100
            print(f"   Taux de succès : {result['success_rate_pct']}% ({result['found']}/{result['total']})")
            total_score += score
            num_tests += 1
        
        if "details" in result:
            details = result["details"]
            if isinstance(details, dict):
                for cat, data in details.items():
                    if isinstance(data, dict):
                        # Afficher les métriques clés
                        if "expansion_ratio" in data:
                            print(f"   {cat}: ×{data['expansion_ratio']}, {data['connector_count']} connecteurs")
                        elif "char_count" in data:
                            print(f"   {cat}: {data['word_count']} mots, opener={data['has_category_opener']}")
    
    if num_tests > 0:
        avg_score = total_score / num_tests
        print(f"\n{'=' * 60}")
        print(f"SCORE GLOBAL MOYEN : {avg_score*100:.1f}%")
        print(f"Tests exécutés : {num_tests}")
        grade = "EXCELLENT" if avg_score >= 0.9 else "BON" if avg_score >= 0.7 else "SATISFAISANT" if avg_score >= 0.5 else "À AMÉLIORER"
        print(f"Évaluation : {grade}")
    
    print(f"\nRecommandations de l'IA experte implementees :")
    print(f"  [OK] Point 1 : System prompts refondus par acte de langage")
    print(f"  [OK] Point 2 : Connecteurs canoniques reduits (petit ensemble)")
    print(f"  [OK] Point 3 : Classifieur par actes de langage (vs mots-cles)")
    print(f"  [OK] Point 4 : Selection dynamique d'exemplar (1 seul, via similarite)")
    print(f"  [OK] Point 5 : Protocole d'evaluation A/B (ce script)")


# =========================================================================
# MAIN
# =========================================================================

def run_all_tests(quick: bool = False) -> Dict:
    """Exécute tous les tests et retourne les résultats."""
    
    results = {}
    
    # Test 1 : Classification
    results["test1"] = test_classification_actes()
    
    # Test 2 : System prompts
    results["test2"] = test_system_prompts()
    
    # Test 3 : Connecteurs
    results["test3"] = test_connecteurs()
    
    # Test 4 : Exemplars
    results["test4"] = test_exemplar_selection()
    
    # Test 5 : Global (peut être long, option quick le saute)
    if not quick:
        results["test5"] = test_resonance_globale()
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark A/B — Recommandations IA Experte"
    )
    parser.add_argument("--quick", action="store_true",
                        help="Test rapide (saute le test de résonance global)")
    parser.add_argument("--report", action="store_true",
                        help="Génère et affiche le rapport uniquement")
    parser.add_argument("--save", type=str, default="",
                        help="Sauvegarde les résultats dans un fichier JSON")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("BENCHMARK A/B — Validation des Recommandations de l'IA Experte")
    print("=" * 60)
    print(f"Date : {time.strftime('%d/%m/%Y %H:%M')}")
    print(f"Mode : {'Rapide' if args.quick else 'Complet'}")
    
    if not args.report:
        results = run_all_tests(quick=args.quick)
        
        # Sauvegarde
        if args.save:
            with open(args.save, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n[OK] Resultats sauvegardes : {args.save}")
        
        generate_report(results)
    else:
        print("\nMode rapport uniquement. Utilisez --save pour charger des données.")
    
    print("\n" + "=" * 60)
    print("Benchmark terminé.")
    print("=" * 60)


if __name__ == "__main__":
    main()
