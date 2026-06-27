#!/usr/bin/env python3
"""
Response Refiner — Harmonic Truth + LLM Fluency
=================================================
Architecture hybride : le moteur harmonique produit les faits (0 hallucination),
l'IA reformule pour la fluidité (sans inventer de nouveaux faits).

Principe : "Harmonic knows the truth. The LLM knows how to say it beautifully."

Pipeline :
  1. HarmonicMathEngine → réponse factuelle (peut manquer de fluidité)
  2. Détection : la réponse a-t-elle besoin d'être reformulée ?
  3. Si oui → envoi à l'API LLM avec instruction STRICTE de reformuler sans ajouter
  4. Vérification post-reformulation : les faits originaux sont-ils toujours présents ?
"""

import os
import re
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Seuil de fluidité : en dessous, on reformule
FLUENCY_THRESHOLD = 0.6

# Patterns indiquant qu'une réponse harmonique a besoin de reformulation
NEEDS_REFINEMENT_PATTERNS = [
    r"Harmonic (?:Reasoning|Analysis|Coherence)",
    r"Frequency signature:",
    r"kx\s*=\s*[\d.]+",
    r"ky\s*=\s*[\d.]+",
    r"Euler coherence check:",
    r"Resonance with knowledge base:",
    r"coherence:\s*[\d.]+%",
    r"analyzed with harmonic engine",
    r"Step-by-step reasoning:",
    r"Logical Analysis:",
]

# Patterns indiquant une réponse déjà fluide (pas besoin de reformuler)
ALREADY_FLUENT_PATTERNS = [
    r"^The (?:derivative|integral|area|volume|probability|solution)",
    r"^(?:Yes|No),?\s",
    r"^(?:To solve|Solving|We)",
    r"^\d+\s*[\+\-\*/]\s*\d+\s*=\s*\d+",
    r"^(?:A|An)\s+\w+\s+(?:is|has|are)",
]

SYSTEM_PROMPT_REFINER = """You refine raw mathematical answers into LM Arena competition style.

LM ARENA STYLE RULES:
1. Start DIRECTLY with the answer or the first step. No greetings, no "I'll help you", no preamble.
2. Be CONCISE. Every word must serve a purpose. Cut filler phrases.
3. Use step-by-step structure ONLY when the problem requires multiple steps. Number steps clearly.
4. State the final answer CLEARLY at the end, preferably on its own line.
5. Use proper mathematical notation. Prefer symbols over words when clearer.
6. NEVER add facts, formulas, or information not present in the original.
7. NEVER change mathematical values, results, or equations.
8. Avoid: "In conclusion", "To summarize", "I hope this helps", "Let me explain", "First of all"
9. If the answer is short, keep it short. One-liners are acceptable for one-step problems.
10. Output ONLY the refined answer. No meta-commentary, no markdown headers, no separators.

Example LM Arena style:
  The derivative of x^2 is 2x. This follows from the power rule: d/dx(x^n)=nx^(n-1) with n=2.

Example for multi-step:
  Step 1: Outer derivative — d/dx[sin(u)] = cos(u)
  Step 2: Inner derivative — u = x^2, du/dx = 2x
  Step 3: Chain rule — cos(x^2) * 2x
  Final answer: 2x cos(x^2)"""


class ResponseRefiner:
    """
    Reformule les réponses harmoniques pour plus de fluidité.
    
    Ne change JAMAIS les faits — uniquement la forme.
    """
    
    def __init__(self, api_endpoint: str = None, api_key: str = None, api_model: str = None):
        self.api_endpoint = api_endpoint or os.environ.get(
            "HARMONIC_API_ENDPOINT", "https://api.deepseek.com/v1/chat/completions"
        )
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.api_model = api_model or os.environ.get("HARMONIC_API_MODEL", "deepseek-chat")
        self.enabled = bool(self.api_key)
        self.stats = {"total": 0, "refined": 0, "kept_raw": 0, "verified": 0}
    
    def needs_refinement(self, text: str) -> bool:
        """
        Détermine si une réponse a besoin d'être reformulée.
        
        Returns:
            True si la réponse contient du "jargon harmonique" non fluide
        """
        if not text:
            return False
        
        # Si la réponse est déjà fluide, pas besoin
        for pattern in ALREADY_FLUENT_PATTERNS:
            if re.search(pattern, text):
                return False
        
        # Si la réponse contient du jargon harmonique, besoin de reformulation
        refinement_score = 0
        for pattern in NEEDS_REFINEMENT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                refinement_score += 1
        
        return refinement_score >= 2  # Au moins 2 patterns de jargon = reformuler
    
    def refine(self, question: str, raw_answer: str, domain: str = None, force: bool = False) -> Dict[str, Any]:
        """
        Reformule une réponse harmonique pour plus de fluidité.
        
        Args:
            question: La question originale
            raw_answer: La réponse brute du moteur harmonique
            domain: Le domaine mathématique (optionnel)
            force: Si True, reformule MÊME si la réponse semble déjà fluide
        
        Returns:
            dict avec "text" (reformulé ou original) et "refined" (bool)
        """
        self.stats["total"] += 1
        
        # Si le refiner n'est pas activé (pas de clé API), retourne la réponse brute
        if not self.enabled:
            self.stats["kept_raw"] += 1
            return {"text": raw_answer, "refined": False, "confidence": 1.0}
        
        # Si la réponse n'a pas besoin de reformulation ET qu'on ne force pas, la garder
        if not force and not self.needs_refinement(raw_answer):
            self.stats["kept_raw"] += 1
            return {"text": raw_answer, "refined": False, "confidence": 1.0}
        
        # Reformulation via API
        refined = self._call_refiner_api(question, raw_answer)
        
        if refined:
            # Vérification post-reformulation
            if self._verify_refinement(raw_answer, refined):
                self.stats["refined"] += 1
                self.stats["verified"] += 1
                return {"text": refined, "refined": True, "confidence": 0.90}
            else:
                # La reformulation a perdu des faits → garder l'original
                logger.warning("Refinement verification failed — keeping original")
                self.stats["kept_raw"] += 1
                return {"text": raw_answer, "refined": False, "confidence": 0.70}
        else:
            # Échec API → garder l'original
            self.stats["kept_raw"] += 1
            return {"text": raw_answer, "refined": False, "confidence": 0.60}
    
    def _call_refiner_api(self, question: str, raw_answer: str) -> Optional[str]:
        """Appelle l'API LLM pour reformuler."""
        try:
            payload = json.dumps({
                "model": self.api_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_REFINER},
                    {"role": "user", "content": f"Question: {question}\n\nRaw answer to refine:\n\n{raw_answer}"}
                ],
                "max_tokens": 1024,
                "temperature": 0.1,  # Très bas pour rester fidèle
            }).encode('utf-8')
            
            req = urllib.request.Request(
                self.api_endpoint,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return text.strip() if text else None
                
        except Exception as e:
            logger.warning(f"Refiner API call failed: {e}")
            return None
    
    def _verify_refinement(self, original: str, refined: str) -> bool:
        """
        Vérifie que la reformulation n'a pas perdu les faits essentiels.
        
        Stratégie : extraire les nombres et mots-clés de l'original,
        vérifier qu'ils sont toujours présents dans le reformulé.
        """
        if not refined or len(refined) < 10:
            return False
        
        # Extraire tous les nombres de l'original
        orig_numbers = set(re.findall(r'\d+\.?\d*', original))
        refined_numbers = set(re.findall(r'\d+\.?\d*', refined))
        
        # Vérifier que tous les nombres importants sont préservés
        # (tolérance : on accepte que des nombres très longs soient absents)
        missing_numbers = orig_numbers - refined_numbers
        critical_missing = [n for n in missing_numbers if len(n) <= 4]  # Nombres courts = probablement importants
        
        if critical_missing:
            logger.warning(f"Refinement lost critical numbers: {critical_missing}")
            return False
        
        # Vérifier que la réponse n'est pas devenue trop courte
        if len(refined) < len(original) * 0.3:
            logger.warning("Refinement produced too short a response")
            return False
        
        # Vérifier l'absence de signes évidents d'hallucination
        hallucination_signs = [
            r"I don't know",
            r"I'm not sure",
            r"as an AI",
            r"I cannot",
            r"I apologize",
            r"unfortunately",
        ]
        for pattern in hallucination_signs:
            if re.search(pattern, refined, re.IGNORECASE):
                logger.warning(f"Refinement contains refusal/hallucination: {pattern}")
                return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du refiner."""
        return {
            **self.stats,
            "refinement_rate": self.stats["refined"] / max(self.stats["total"], 1),
            "verification_rate": self.stats["verified"] / max(self.stats["refined"], 1),
            "enabled": self.enabled,
        }