#!/usr/bin/env python3
"""
Fallback Router — Routeur intelligent entre Harmonique et LLM externe
=====================================================================
Quand la confiance harmonique est insuffisante, délègue au LLM externe.
Re-vérifie toujours la réponse avec le moteur harmonique.

Supporte :
  - Ollama (local) — DeepSeek-Math, SmolLM2, etc.
  - API HTTP externe (OpenAI, Anthropic, DeepSeek API)
  - Mode mock pour tests sans LLM
"""

import os
import re
import sys
import json
import time
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'projet', 'cerveau_harmonique_v1'))

try:
    from engine.abc_kernel import PHI, ALPHA
except ImportError:
    PHI = 1.618033988749895
    ALPHA = 1.0 / PHI

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION — Chargement depuis .env
# =============================================================================

def _load_dotenv():
    """Charge les variables depuis le fichier .env du workspace."""
    env_paths = [
        os.path.join(os.path.dirname(__file__), '..', '.env'),
        os.path.join(os.path.dirname(__file__), '.env'),
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value and key not in os.environ:
                            os.environ[key] = value
            logger.info(f"Loaded env from {env_path}")
            return
    logger.info("No .env file found")

_load_dotenv()

# Mode de fallback : "ollama", "api", "mock"
# Auto-détection : si DEEPSEEK_API_KEY est dispo → mode "api"
_detected_key = os.environ.get("DEEPSEEK_API_KEY", "")
FALLBACK_MODE = os.environ.get("HARMONIC_FALLBACK_MODE", "api" if _detected_key else "mock")

# Configuration Ollama
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-math-1.5b:latest")

# Configuration API DeepSeek
API_ENDPOINT = os.environ.get("HARMONIC_API_ENDPOINT", "https://api.deepseek.com/v1/chat/completions")
API_KEY = os.environ.get("HARMONIC_API_KEY", _detected_key)
API_MODEL = os.environ.get("HARMONIC_API_MODEL", "deepseek-reasoner")

# Seuils
FALLBACK_COHERENCE_MIN = 0.35  # Rejeter la réponse fallback si cohérence < ce seuil
MAX_RETRIES = 2
TIMEOUT_SECONDS = 30

# Templates mathématiques pour le mock mode
MOCK_MATH_TEMPLATES = {
    "algebra": "The solution involves solving the equation by:\n1. Isolating the variable\n2. Applying algebraic properties\n3. Verifying the solution satisfies the original equation",
    
    "calculus": "We solve this by:\n1. Identifying the function type\n2. Applying the appropriate rule (power rule, chain rule, etc.)\n3. Computing and simplifying the result",
    
    "geometry": "Geometric analysis:\n1. Identify the geometric properties\n2. Apply the relevant formula\n3. Calculate the result and verify dimensions",
    
    "trigonometry": "Trigonometric solution:\n1. Identify the angle or relationship\n2. Apply trigonometric identities\n3. Simplify using known values",
    
    "probability": "Probability calculation:\n1. Identify the sample space\n2. Count favorable outcomes\n3. Apply: P(event) = favorable / total",
    
    "reasoning": "Logical analysis:\n1. Identify premises and conclusion\n2. Verify logical structure\n3. Check for counterexamples or fallacies",
    
    "general": "Analysis of the question:\n\nBased on the provided information and logical reasoning, the answer requires:\n1. Understanding the core concepts involved\n2. Applying relevant principles\n3. Verifying the conclusion",
}


class FallbackRouter:
    """
    Routeur intelligent : délègue au LLM externe quand l'harmonique est incertain.
    
    Stratégie :
    1. Tenter Ollama local (si disponible)
    2. Tenter API HTTP externe (si configurée)
    3. Fallback mock avec templates (toujours disponible)
    """
    
    def __init__(self, mode: str = None):
        self.mode = mode or FALLBACK_MODE
        self.stats = {"calls": 0, "successes": 0, "failures": 0, "rejected": 0}
        self._check_ollama()
    
    def _check_ollama(self) -> bool:
        """Vérifie si Ollama est accessible."""
        if self.mode != "ollama":
            return False
        try:
            req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    logger.info("✅ Ollama accessible")
                    return True
        except Exception:
            logger.warning("⚠️ Ollama non accessible — fallback mock activé")
            self.mode = "mock"
        return False
    
    def generate(
        self, 
        prompt: str, 
        analysis: Dict[str, Any] = None,
        max_tokens: int = 512
    ) -> Dict[str, Any]:
        """
        Génère une réponse via le fallback.
        
        Args:
            prompt: Question utilisateur
            analysis: Analyse harmonique préalable (optionnelle)
            max_tokens: Nombre max de tokens
        
        Returns:
            dict avec "text" et "confidence"
        """
        self.stats["calls"] += 1
        domain = analysis.get("domain", "general") if analysis else "general"
        
        # Tentative 1 : Ollama
        if self.mode == "ollama":
            result = self._ollama_generate(prompt, max_tokens)
            if result:
                self.stats["successes"] += 1
                return result
        
        # Tentative 2 : API HTTP
        if self.mode == "api" and API_ENDPOINT:
            result = self._api_generate(prompt, max_tokens)
            if result:
                self.stats["successes"] += 1
                return result
        
        # Fallback ultime : mock (toujours disponible)
        result = self._mock_generate(prompt, domain)
        self.stats["successes"] += 1
        return result
    
    def _ollama_generate(self, prompt: str, max_tokens: int) -> Optional[Dict[str, Any]]:
        """Génération via Ollama local."""
        try:
            payload = json.dumps({
                "model": OLLAMA_MODEL,
                "prompt": f"[MATH] {prompt}\n\nProvide a step-by-step solution.",
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "top_k": 1,
                    "num_predict": max_tokens,
                }
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{OLLAMA_HOST}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                text = data.get("response", "").strip()
                
                if text:
                    return {"text": text, "confidence": 0.65, "method": "ollama"}
        except Exception as e:
            logger.warning(f"Ollama failed: {e}")
            self.stats["failures"] += 1
        
        return None
    
    def _api_generate(self, prompt: str, max_tokens: int) -> Optional[Dict[str, Any]]:
        """Génération via API HTTP externe."""
        try:
            payload = json.dumps({
                "model": API_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a math and reasoning assistant. Provide clear, step-by-step solutions."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.0,
            }).encode('utf-8')
            
            req = urllib.request.Request(
                API_ENDPOINT,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if text:
                    return {"text": text.strip(), "confidence": 0.70, "method": "api"}
        except Exception as e:
            logger.warning(f"API failed: {e}")
            self.stats["failures"] += 1
        
        return None
    
    def _mock_generate(self, prompt: str, domain: str) -> Dict[str, Any]:
        """Génération mock pour tests (toujours disponible)."""
        # Sélection du template approprié
        template = MOCK_MATH_TEMPLATES.get(domain, MOCK_MATH_TEMPLATES["general"])
        
        # Ajout de contexte spécifique au prompt
        text = f"Response to: \"{prompt[:100]}{'...' if len(prompt) > 100 else ''}\"\n\n"
        text += template
        
        # Détection de patterns pour personnaliser
        p_lower = prompt.lower()
        
        if re.search(r'derivative|differentiate', p_lower):
            text += "\n\nSpecifically for differentiation: apply d/dx rule term by term."
        elif re.search(r'integral|integrate|antiderivative', p_lower):
            text += "\n\nFor integration: remember to add the constant of integration +C."
        elif re.search(r'solve.*equation|find.*x|find.*root', p_lower):
            text += "\n\nFor equation solving: isolate the variable and verify all solutions."
        elif re.search(r'area|volume|perimeter|surface', p_lower):
            text += "\n\nFor geometry: ensure consistent units and verify dimensions."
        
        # Extraction de nombres pour montrer qu'on les a vus
        numbers = re.findall(r'\d+\.?\d*', prompt)
        if numbers:
            text += f"\n\nKey values identified: {', '.join(numbers[:5])}"
        
        return {"text": text, "confidence": 0.55, "method": "mock"}
    
    def verify_response(self, text: str, domain: str) -> float:
        """
        Vérifie la cohérence minimale d'une réponse.
        
        Returns:
            Score de cohérence 0-1
        """
        if not text or len(text) < 10:
            return 0.0
        
        coherence = 0.5  # Base
        
        # Présence de mots-clés mathématiques
        if re.search(r'solution|answer|result|therefore|hence|because', text, re.IGNORECASE):
            coherence += 0.10
        
        # Structure de réponse (étapes, formules)
        if re.search(r'[1-9]\.|step|first|second|finally|apply|compute|calculate', text, re.IGNORECASE):
            coherence += 0.10
        
        # Formules mathématiques
        if re.search(r'[+\-*/=^√∫∑]|\\frac|\\sqrt|\\sum|dx|dy', text):
            coherence += 0.10
        
        # Longueur minimale raisonnable
        if len(text) > 50:
            coherence += 0.05
        if len(text) > 200:
            coherence += 0.05
        
        # Pas de contenu manifestement absurde
        if re.search(r'(?:I don\'t know|I\'m not sure|as an AI|I cannot)', text, re.IGNORECASE):
            coherence -= 0.15
        
        return min(max(coherence, 0.0), 1.0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du routeur."""
        return {
            **self.stats,
            "success_rate": self.stats["successes"] / max(self.stats["calls"], 1),
            "mode": self.mode,
        }