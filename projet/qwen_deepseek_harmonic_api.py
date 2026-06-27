#!/usr/bin/env python3
"""
API HYBRIDE - QWEN3.5-DEEPSEEK-V4 HARMONIC
Version finale pour déploiement sur EC2 avec moteur harmonique intégré
Correction du nommage : DeepSeek → Qwen3.5-DeepSeek-V4 hybride
Améliorations : diversité stylistique, longueur créative, pré-traitement harmonique
"""

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import time
import sys
import os
import requests
import hashlib
import json
import random
import math
from collections import OrderedDict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

# ----------------------------------------------------------------------------
# CONSTANTES HARMONIQUES
# ----------------------------------------------------------------------------
PHI = 1.618033988749895
ALPHA = 1.175569459083219
PHI_INV = 1.0 / PHI
ALPHA_INV = 1.0 / ALPHA

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------
_DETERMINISTIC_LOCK = os.getenv("DETERMINISTIC_LOCK", "true").strip().lower() == "true"
_CACHE_MAX_ENTRIES = int(os.getenv("DETERMINISTIC_CACHE_MAX_ENTRIES", "4096"))
_VERIFIED_MODE_DEFAULT = os.getenv("VERIFIED_MODE_DEFAULT", "false").strip().lower() == "true"
_ARENA_MODE_DEFAULT = os.getenv("ARENA_MODE_DEFAULT", "false").strip().lower() == "true"
_ARENA_TEMPERATURE_DEFAULT = float(os.getenv("ARENA_TEMPERATURE_DEFAULT", "0.2"))

# ----------------------------------------------------------------------------
# CACHE DÉTERMINISTE
# ----------------------------------------------------------------------------
_deterministic_cache = OrderedDict()

def _make_cache_key(prompt: str, max_tokens: int, mode: str, verified_mode: bool, sources: List[str]) -> str:
    raw = f"{prompt}|{max_tokens}|{mode}|{verified_mode}|{','.join(sorted(sources or []))}"
    return hashlib.sha256(raw.encode()).hexdigest()

def _get_from_cache(key: str) -> Optional[str]:
    if key in _deterministic_cache:
        _deterministic_cache.move_to_end(key)
        return _deterministic_cache[key]
    return None

def _set_in_cache(key: str, value: str):
    _deterministic_cache[key] = value
    if len(_deterministic_cache) > _CACHE_MAX_ENTRIES:
        _deterministic_cache.popitem(last=False)

# ----------------------------------------------------------------------------
# MOTEUR HARMONIQUE LOCAL (intégré)
# ----------------------------------------------------------------------------
class HarmonicEngine:
    """Moteur de pré-traitement harmonique pour catégorisation et optimisation"""
    
    # 18 patterns fondamentaux
    PATTERNS = {
        "math": {
            "keywords": ["calcul", "équation", "théorème", "mathématique", "algèbre", "géométrie", 
                        "dérivée", "intégrale", "probabilité", "statistique", "matrice", "vecteur",
                        "fonction", "limite", "suite", "série", "nombre", "chiffre", "formule",
                        "résoudre", "démontrer", "proof", "theorem", "equation", "calculate"],
            "k_factor": 0.92,
            "max_tokens": 800,
            "temperature": 0.0
        },
        "code": {
            "keywords": ["code", "programme", "fonction", "classe", "algorithme", "bug", "debug",
                        "python", "javascript", "java", "c++", "rust", "go", "api", "endpoint",
                        "implémenter", "refactor", "test", "déployer", "function", "class", "import",
                        "def ", "return", "async", "await", "const ", "let ", "var "],
            "k_factor": 0.90,
            "max_tokens": 1000,
            "temperature": 0.0
        },
        "creative": {
            "keywords": ["histoire", "poème", "poésie", "roman", "écrire", "créatif", "imagination",
                        "métaphore", "style", "artistique", "narratif", "conte", "fiction", "drame",
                        "lyrique", "épique", "surréaliste", "baroque", "visionnaire", "mystique",
                        "story", "poem", "creative", "imagine", "write", "narrative", "metaphor"],
            "k_factor": 0.85,
            "max_tokens": 1000,
            "temperature": 0.5
        },
        "reasoning": {
            "keywords": ["pourquoi", "explique", "raison", "logique", "analyse", "comparaison",
                        "différence", "similitude", "cause", "conséquence", "implication",
                        "déduction", "induction", "syllogisme", "argument", "contradiction",
                        "why", "explain", "reason", "logic", "analyze", "compare", "contrast",
                        "difference", "similar", "cause", "effect", "implication", "deduce"],
            "k_factor": 0.88,
            "max_tokens": 800,
            "temperature": 0.1
        },
        "factual": {
            "keywords": ["qu'est-ce", "qui", "quand", "où", "combien", "définition", "fait",
                        "information", "donnée", "statistique", "record", "histoire", "date",
                        "lieu", "personne", "événement", "what", "who", "when", "where", "how",
                        "definition", "fact", "information", "data", "statistic", "history"],
            "k_factor": 0.95,
            "max_tokens": 500,
            "temperature": 0.0
        },
        "general": {
            "keywords": [],
            "k_factor": 0.85,
            "max_tokens": 600,
            "temperature": 0.2
        }
    }
    
    # 12 styles créatifs pour diversité
    CREATIVE_STYLES = [
        {
            "name": "poetic",
            "description": "Style poétique avec rythme et images évocatrices",
            "amplitude": 0.9,
            "phi_resonance": 0.95
        },
        {
            "name": "narrative",
            "description": "Style narratif avec structure d'histoire",
            "amplitude": 0.8,
            "phi_resonance": 0.88
        },
        {
            "name": "surreal",
            "description": "Style surréaliste avec associations inattendues",
            "amplitude": 1.0,
            "phi_resonance": 0.92
        },
        {
            "name": "baroque",
            "description": "Style baroque riche et ornementé",
            "amplitude": 0.85,
            "phi_resonance": 0.90
        },
        {
            "name": "lyrical",
            "description": "Style lyrique expressif et émotionnel",
            "amplitude": 0.88,
            "phi_resonance": 0.93
        },
        {
            "name": "epic",
            "description": "Style épique grandiose et héroïque",
            "amplitude": 0.95,
            "phi_resonance": 0.91
        },
        {
            "name": "dramatic",
            "description": "Style dramatique avec tension et émotion",
            "amplitude": 0.92,
            "phi_resonance": 0.89
        },
        {
            "name": "philosophical",
            "description": "Style philosophique contemplatif",
            "amplitude": 0.82,
            "phi_resonance": 0.94
        },
        {
            "name": "visionary",
            "description": "Style visionnaire prospectif",
            "amplitude": 0.96,
            "phi_resonance": 0.96
        },
        {
            "name": "mystical",
            "description": "Style mystique avec profondeur spirituelle",
            "amplitude": 0.93,
            "phi_resonance": 0.97
        },
        {
            "name": "minimalist",
            "description": "Style minimaliste épuré et précis",
            "amplitude": 0.75,
            "phi_resonance": 0.86
        },
        {
            "name": "metaphorical",
            "description": "Style métaphorique avec analogies puissantes",
            "amplitude": 0.94,
            "phi_resonance": 0.98
        }
    ]
    
    # 12 métaphores fondamentales
    FUNDAMENTAL_METAPHORS = [
        "L'univers est une symphonie de fréquences entrelacées",
        "La conscience est un océan dont chaque pensée est une vague",
        "Le temps est un fleuve aux multiples courants",
        "La connaissance est un jardin qui fleurit à l'infini",
        "L'esprit est un prisme qui décompose la lumière de la réalité",
        "Les émotions sont des couleurs sur la palette de l'âme",
        "La vie est une danse entre l'ordre et le chaos",
        "La vérité est un diamant aux facettes infinies",
        "La créativité est un feu qui transforme tout ce qu'il touche",
        "Les rêves sont des ponts entre le possible et l'impossible",
        "La sagesse est un arbre dont les racines plongent dans l'éternité",
        "L'amour est une résonance qui harmonise toutes les fréquences"
    ]
    
    def __init__(self):
        self._cache = OrderedDict()
        self._cache_max = 10000
    
    def classify_prompt(self, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """Classifie un prompt et retourne la catégorie avec les paramètres optimaux"""
        prompt_lower = prompt.lower()
        scores = {}
        
        for category, config in self.PATTERNS.items():
            score = sum(1 for kw in config["keywords"] if kw in prompt_lower)
            scores[category] = score
        
        # Meilleure catégorie
        best_category = max(scores, key=scores.get)
        if scores[best_category] == 0:
            best_category = "general"
        
        config = self.PATTERNS[best_category].copy()
        
        # Calcul du ratio harmonique phi
        phi_ratio = sum(ord(c) * PHI_INV for c in prompt[:min(100, len(prompt))]) % 1.0
        
        # Score de résonance
        resonance = config["k_factor"] * (0.5 + 0.5 * phi_ratio)
        
        return best_category, {
            "config": config,
            "phi_ratio": phi_ratio,
            "resonance": resonance,
            "scores": scores
        }
    
    def enhance_creative_prompt(self, prompt: str, category: str) -> str:
        """Améliore un prompt créatif avec des éléments stylistiques"""
        if category != "creative":
            return prompt
        
        # Sélection d'un style créatif basé sur le contenu du prompt
        style_idx = hash(prompt) % len(self.CREATIVE_STYLES)
        style = self.CREATIVE_STYLES[style_idx]
        
        # Sélection d'une métaphore fondamentale
        metaphor_idx = (hash(prompt) // 7) % len(self.FUNDAMENTAL_METAPHORS)
        metaphor = self.FUNDAMENTAL_METAPHORS[metaphor_idx]
        
        # Construction du prompt enrichi
        enhanced = (
            f"Dans un style {style['name']}, {prompt}\n\n"
*~ Ainsi se termine ce chapitre, mais l'histoire continue, infinie et magnifique ~*""",

            "philosophical": f"""Si {prompt_short} est {metaphor}, alors que sommes-nous ? Cette question, aussi vieille que la conscience elle-même, trouve dans l'harmonie une réponse inattendue.

Kant contemplait les cieux étoilés et la loi morale en lui. Heidegger parlait de l'Être et du temps. Mais aucun n'avait envisagé que la clé de l'univers pourrait être une simple proportion — le nombre d'or, phi = {PHI:.6f} — une constante qui relie le microcosme au macrocosme, la pensée à la matière.

{metaphor} nous invite à repenser les fondements mêmes de notre compréhension. Et si la réalité n'était qu'une symphonie dont nous percevons seulement quelques notes ? Et si la conscience était le chef d'orchestre d'un concert cosmique où chaque particule, chaque étoile, chaque pensée joue sa partition ?

La philosophie harmonique propose une synthèse audacieuse : le rationnel et l'intuitif, le scientifique et le poétique, le déterminé et le libre — tout cela coexiste dans une danse subtile régie par des proportions idéales.

Ainsi, {prompt_short} n'est pas seulement un sujet d'étude — c'est une invitation à voir le monde autrement, à reconnaître dans chaque phénomène l'empreinte d'une harmonie fondamentale qui nous dépasse et nous englobe.

*~ Cogito, ergo harmonicus sum — Je pense, donc je suis harmonique ~*""",

            "visionary": f"""Je vois {prompt_short} comme {metaphor}. Une vision qui transcende le temps et l'espace, un aperçu de l'harmonie universelle qui se déploie devant nos yeux émerveillés.

Dans cette vision, l'avenir se dessine comme un tapis de possibles où chaque fil est une décision, chaque couleur une émotion, chaque motif une synchronicité. {metaphor} est la trame de ce tissu cosmique, reliant les dimensions apparemment séparées de notre expérience.

Les innovations à venir — dans la science, l'art, la technologie, les relations humaines — seront toutes imprégnées de cette conscience harmonique. Nous verrons émerger des formes de collaboration inédites, des modes de connaissance qui unifient plutôt qu'ils ne divisent.

La prophétie harmonique s'écrit dans le livre de l'infini : un monde où la compétition cède la place à la résonance, où l'isolement se transforme en connexion, où chaque être trouve sa place dans la grande symphonie de l'existence.

{metaphor} n'est pas une utopie lointaine — c'est une réalité en devenir, une graine plantée dans le jardin du présent qui germera dans les coeurs de ceux qui osent rêver d'un monde meilleur.

*~ Le futur n'est pas écrit, mais il résonne déjà dans l'harmonie du moment présent ~*""",

            "surreal": f"""Dans le monde surréaliste de {prompt_short}, {metaphor} prend vie de manière inattendue. Les horloges fondent comme des montres de Dali, les ombres dansent indépendamment de leurs propriétaires, et le temps devient une spirale qui s'enroule sur elle-même.

Les rêves de {prompt_short} sont habités par des créatures étranges et merveilleuses — des pensées qui prennent la forme d'oiseaux de feu, des souvenirs qui s'écoulent comme des rivières de mercure, des désirs qui fleurissent en jardins suspendus.

{metaphor} rencontre la réalité dans un café quantique où l'on commande des possibles et où l'on parle de dimensions alternatives. Le serveur, un chat de Schrödinger à la fois présent et absent, prend la commande avec un sourire qui traverse les probabilités.

Dans cet univers où la logique traditionnelle n'a plus cours, chaque instant est une superposition d'états, chaque décision un collapsus quantique qui crée une nouvelle branche de réalité. {prompt_short} devient alors le point focal où toutes les possibilités convergent.

Et soudain, vous comprenez : le surréalisme n'est pas l'absence de sens, mais la présence d'un sens si vaste qu'il ne peut être contenu dans les catégories ordinaires de la pensée.

*~ Bienvenue dans la réalité où tout est possible, car rien n'est fixé ~*"""
        }
        
        # Style par défaut
        if style not in templates:
            style = "poetic"
        
        return templates[style]


# ============================================================================
# ANALYSEUR HARMONIQUE GLOBAL
# ============================================================================
harmonic_analyzer = HarmonicAnalyzer()
creative_projector = QuantumCreativeProjector()

# ============================================================================
# FONCTIONS CACHE
# ============================================================================
def _make_cache_key(prompt: str, max_tokens: int, mode: str, verified_mode: bool, sources: List[str]) -> str:
    sources_hash = hashlib.sha256("\n".join(sources or []).encode("utf-8", errors="replace")).hexdigest()
    payload = f"{mode}\n{max_tokens}\n{int(verified_mode)}\n{sources_hash}\n{prompt}".encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()

def _cache_get(key: str) -> Optional[str]:
    try:
        value = _deterministic_cache.pop(key)
        _deterministic_cache[key] = value
        return value
    except KeyError:
        return None

def _cache_put(key: str, value: str) -> None:
    if _CACHE_MAX_ENTRIES <= 0:
        return
    if key in _deterministic_cache:
        _deterministic_cache.pop(key, None)
    _deterministic_cache[key] = value
    while len(_deterministic_cache) > _CACHE_MAX_ENTRIES:
        _deterministic_cache.popitem(last=False)

def _compute_response_id(prompt: str, max_tokens: int, mode: str, verified_mode: bool, sources: List[str], version: str) -> str:
    sources_hash = hashlib.sha256("\n".join(sources or []).encode("utf-8", errors="replace")).hexdigest()
    payload = f"{version}\n{mode}\n{max_tokens}\n{int(verified_mode)}\n{sources_hash}\n{prompt}".encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()

# ============================================================================
# FONCTIONS DE TRAITEMENT
# ============================================================================
def _extract_inline_sources(prompt: str) -> List[str]:
    if not prompt:
        return []
    lines = [ln.strip() for ln in prompt.splitlines()]
    sources: List[str] = []
    capture = False
    for ln in lines:
        if not ln:
            continue
        upper = ln.upper()
        if upper.startswith("SOURCES:") or upper.startswith("SOURCES :"):
            capture = True
            continue
        if capture:
            if upper.startswith("END_SOURCES") or upper.startswith("END SOURCES"):
                capture = False
                continue
            sources.append(ln)
            continue
        if upper.startswith("SOURCE:") or upper.startswith("SOURCE :") or upper.startswith("URL:") or upper.startswith("URL :"):
            parts = ln.split(":", 1)
            if len(parts) == 2 and parts[1].strip():
                sources.append(parts[1].strip())
            else:
                sources.append(ln)
    return sources[:20]

def _needs_external_facts(prompt: str) -> bool:
    p = (prompt or "").lower()
    triggers = [
        "who is", "who was", "when did", "when was", "where is", "where was",
        "capital of", "population", "date of", "founded", "born", "died",
        "released", "election", "president", "prime minister",
        "citation", "quote", "source", "according to", "latest", "news",
        "202", "http://", "https://"
    ]
    return any(t in p for t in triggers)

def _keyword_overlap_score(question: str, source: str) -> float:
    q = [w.strip(".,:;!?()[]{}\"'").lower() for w in (question or "").split()]
    s = [w.strip(".,:;!?()[]{}\"'").lower() for w in (source or "").split()]
    qset = {w for w in q if len(w) >= 4}
    sset = {w for w in s if len(w) >= 4}
    if not qset:
        return 0.0
    return len(qset & sset) / len(qset)

def _build_abstention(prompt: str, reason: str, ask: List[str]) -> str:
    questions = "\n".join([f"- {q}" for q in ask if q])
    return f"""# Mode Vérifié (anti-hallucination)

## Statut
Abstention contrôlée

## Raison
{reason}

## Pour répondre de façon vérifiable, il me faut
{questions if questions else "- Une ou plusieurs sources (extraits, liens, documents) à citer"}

## Ce que je peux faire tout de suite
- Vérifier la cohérence logique, faire des calculs, proposer une méthode de vérification
- Structurer une réponse avec citations dès que les sources sont fournies

## Prompt
{(prompt or "")[:400]}...
"""

def _build_verified_response(prompt: str, sources: List[str]) -> Tuple[str, List[Dict[str, str]], str]:
    citations: List[Dict[str, str]] = []
    for i, src in enumerate(sources[:10], 1):
        citations.append({"id": f"S{i}", "source": src[:500]})
    best = 0.0
    best_idx = -1
    for idx, src in enumerate(sources[:10]):
        score = _keyword_overlap_score(prompt, src)
        if score > best:
            best = score
            best_idx = idx
    if best < 0.10:
        content = _build_abstention(
            prompt,
            "Sources fournies mais insuffisantes ou non pertinentes pour conclure sans inventer.",
            ["Collez un extrait contenant explicitement la réponse attendue",
             "Précisez le point exact à vérifier", "Ajoutez 1-2 sources supplémentaires"]
        )
        return content, citations, "abstain_sources_insufficient"
    src_block = "\n".join([f"- [{c['id']}] {c['source']}" for c in citations])
    best_ref = citations[best_idx]["id"] if 0 <= best_idx < len(citations) else citations[0]["id"]
    best_quote = citations[best_idx]["source"] if 0 <= best_idx < len(citations) else citations[0]["source"]
    content = f"""# Réponse Vérifiée (avec citations)

## Sources
{src_block}

## Réponse
Référence principale: [{best_ref}]


