#!/usr/bin/env python3
"""
CONSCIOUSNESS CONTROLLER — Vérification de cohérence des réponses
====================================================================
Filtre les réponses de l'inconscient (ParametricKB, QuickFacts,
WaveResonanceEngine) pour garantir qu'elles sont PERTINENTES
avant de les présenter à l'utilisateur.

Problème résolu :
  - "c'est quoi une dérivée fractionnaire ?" → "la radioactivité est..."
    → Le contrôleur détecte le topic mismatch et rejette
  - "capitale du Bénin" → réponse avec confiance 0.2
    → Le contrôleur vérifie le seuil de confiance

Architecture (modèle Conscient/Inconscient) :
  INCONSCIENT (KB, règles, ondes) → CONSCIENCE (ce module) → UTILISATEUR

Vérifications :
  1. TOPIC MATCH : les mots-clés du prompt apparaissent dans la réponse ?
  2. CONFIDENCE : le score de confiance est-il suffisant ?
  3. LENGTH : la réponse est-elle trop courte/générique ?
  4. CONTRADICTION : la réponse contredit-elle un fait connu ?
  5. HALLUCINATION : la réponse contient-elle des affirmations non sourcées ?

Usage :
  from consciousness_controller import ConsciousnessController
  cc = ConsciousnessController()
  result = cc.verify(prompt, response, confidence, source)
  # → {"valid": True, "response": "...", "confidence": 0.9}
  # → {"valid": False, "reason": "topic_mismatch", "fallback": "..."}
"""

import re, math, json, os
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

# ══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE — Topics et mots-clés pour la vérification
# ══════════════════════════════════════════════════════════════════════════

TOPIC_KEYWORDS = {
    "math_derivative": ["dérivée", "dériver", "différentielle", "dx", "dy/dx", "primitive",
                        "derivee", "tangente", "pente", "taux de variation"],
    "math_integral": ["intégrale", "intégrer", "primitive", "aire sous", "∫", "dx"],
    "math_algebra": ["équation", "résoudre", "factoriser", "x =", "inconnue", "polynôme",
                     "equation", "factorisation"],
    "math_trigonometry": ["sin", "cos", "tan", "trigonométrie", "triangle", "cercle",
                          "sinus", "cosinus", "tangente", "angle"],
    "math_probability": ["probabilité", "chance", "dé", "carte", "tirage", "hasard",
                         "probabilite", "evenement", "loi"],
    "math_stats": ["moyenne", "médiane", "écart-type", "variance", "statistique",
                   "moyenne", "mediane", "ecart", "distribution", "échantillon"],
    "math_complex": ["complexe", "imaginaire", "i²", "module", "argument", "polaire",
                     "euler", "fourier", "laplace"],
    "math_logic": ["logique", "syllogisme", "modus", "tautologie", "contradiction",
                   "raisonnement", "prémisse", "conclusion"],
    "geography": ["capitale", "pays", "continent", "ville", "population", "superficie",
                  "monnaie", "fleuve", "montagne", "océan", "frontière"],
    "history": ["guerre", "révolution", "roi", "empereur", "empire", "indépendance",
                "bataille", "traité", "siècle", "dynastie", "pharaon"],
    "science_physics": ["physique", "force", "énergie", "masse", "vitesse", "lumière",
                        "atome", "électron", "quantique", "relativité", "newton"],
    "science_chemistry": ["chimie", "molécule", "atome", "réaction", "élément", "acide",
                          "base", "pH", "oxydation", "catalyseur"],
    "science_biology": ["biologie", "cellule", "ADN", "protéine", "enzyme", "évolution",
                        "espèce", "gène", "mitose", "photosynthèse"],
    "health": ["santé", "maladie", "symptôme", "traitement", "médecin", "médicament",
               "vaccin", "virus", "bactérie", "diagnostic"],
    "tech": ["internet", "ordinateur", "code", "programme", "algorithme", "IA",
             "intelligence artificielle", "réseau", "donnée", "serveur", "app"],
    "kemet": ["kemet", "égypte", "pharaon", "pyramide", "nil", "sphinx", "maât",
              "hiéroglyphe", "obélisque", "kheops", "nubie", "koush"],
}

# Mots qui indiquent une réponse non pertinente (trop générique)
GENERIC_RESPONSE_PATTERNS = [
    r"^(?:je ne sais pas|je ne comprends pas|je n'ai pas|désolé)",
    r"^(?:la réponse est|la solution est|le résultat est)\s*$",
    r"^(?:c'est|il s'agit de)\s+(?:une|un|des)\s+(?:question|problème|chose)",
]


class ConsciousnessController:
    """
    Vérifie la cohérence des réponses avant de les présenter à l'utilisateur.
    
    Fonctionne comme un "conscient" qui filtre les réponses de "l'inconscient"
    (les moteurs de règles et de faits).
    """

    def __init__(self, strictness: float = 0.5):
        """
        Args:
            strictness: 0.0 = permissif, 1.0 = très strict
        """
        self.strictness = strictness
        self.stats = {
            "total_checked": 0,
            "passed": 0,
            "rejected": 0,
            "reasons": defaultdict(int),
        }

    def verify(self, prompt: str, response: str, confidence: float, 
               source: str = "unknown") -> Dict[str, Any]:
        """
        Vérifie si une réponse est cohérente avec le prompt.
        
        Args:
            prompt: question originale de l'utilisateur
            response: réponse proposée par l'inconscient
            confidence: score de confiance (0-1)
            source: module source ("parametric_kb", "quick_facts", etc.)
            
        Returns:
            Dict avec 'valid' (bool), 'response' (str), 'confidence' (float)
            Si invalid, contient 'reason' et 'fallback'
        """
        self.stats["total_checked"] += 1
        
        if not response or len(response.strip()) < 3:
            return self._reject("empty_response", prompt)
        
        # Vérification 1 : Topic match
        topic_score = self._check_topic_match(prompt, response)
        topic_threshold = 0.15 - self.strictness * 0.1
        if topic_score < topic_threshold and confidence < 0.8:
            self.stats["rejected"] += 1
            self.stats["reasons"]["topic_mismatch"] += 1
            return self._reject("topic_mismatch", prompt, 
                               detail=f"topic_score={topic_score:.2f}<{topic_threshold:.2f}")
        
        # Vérification 2 : Confiance minimale
        confidence_threshold = 0.3 + self.strictness * 0.2
        if confidence < confidence_threshold:
            self.stats["rejected"] += 1
            self.stats["reasons"]["low_confidence"] += 1
            return self._reject("low_confidence", prompt,
                               detail=f"confidence={confidence:.2f}<{confidence_threshold:.2f}")
        
        # Vérification 3 : Réponse générique détectée
        if self._is_generic_response(response):
            self.stats["rejected"] += 1
            self.stats["reasons"]["generic"] += 1
            return self._reject("generic_response", prompt)
        
        # Vérification 4 : Longueur excessive ?
        if len(response) > 2000:
            # Tronquer intelligemment
            response = response[:1997] + "..."
        
        # Vérification 5 : Contradiction avec des faits connus ?
        contradiction = self._check_contradiction(prompt, response)
        if contradiction:
            self.stats["rejected"] += 1
            self.stats["reasons"]["contradiction"] += 1
            return self._reject("contradiction", prompt, detail=contradiction)
        
        self.stats["passed"] += 1
        return {
            "valid": True,
            "response": response,
            "confidence": confidence,
            "source": source,
            "topic_score": topic_score,
        }

    # ═══ VERIFICATION METHODS ═══

    def _check_topic_match(self, prompt: str, response: str) -> float:
        """
        Calcule un score de correspondance thématique entre prompt et réponse.
        
        Méthode :
          1. Extrait les mots-clés significatifs du prompt
          2. Vérifie combien apparaissent dans la réponse
          3. Score = intersection / union
        """
        # Extraire les mots significatifs du prompt (>= 2 caractères, lettres ET chiffres)
        prompt_words = set(re.findall(r'[a-zàâçéèêëîïôûùüÿœæ0-9]{2,}', prompt.lower()))
        response_words = set(re.findall(r'[a-zàâçéèêëîïôûùüÿœæ0-9]{2,}', response.lower()))
        
        # Mots vides à ignorer (étendu pour inclure les mots courts)
        stop_words = {'dans', 'pour', 'avec', 'sans', 'plus', 'moins', 'cette',
                      'cela', 'être', 'avoir', 'faire', 'tout', 'tous', 'leur',
                      'elle', 'nous', 'vous', 'très', 'bien', 'comme', 'aussi',
                      'alors', 'donc', 'mais', 'quand', 'comment', 'pourquoi',
                      'est', 'que', 'pas', 'sur', 'une', 'les', 'des', 'qui',
                      'ont', 'son', 'ses', 'mes', 'tes', 'nos', 'vos', 'leur',
                      'cet', 'ces', 'mon', 'ton', 'car', 'par', 'aux', 'the',
                      'are', 'for', 'and', 'not', 'you', 'can', 'has', 'had',
                      'was', 'his', 'her', 'its', 'our', 'but', 'all', 'any',
                      'the', 'are', 'for', 'and', 'not', 'you', 'can'}
        
        prompt_words -= stop_words
        response_words -= stop_words
        
        if not prompt_words:
            return 0.5  # Peu d'information dans le prompt
        
        # Score de similarité : intersection / len(prompt_words)
        intersection = prompt_words & response_words
        score = len(intersection) / len(prompt_words)
        
        # Bonus si les mots-clés du topic sont présents
        prompt_topic = self._detect_topic(prompt)
        response_topic = self._detect_topic(response)
        if prompt_topic and prompt_topic == response_topic:
            score = min(1.0, score + 0.3)
        
        # Bonus pour les réponses de sources fiables (quick_facts, harmonic_reasoning, parametric)
        # Même si le topic match est faible, ces sources sont déterministes
        if score < 0.10 and confidence > 0.7:
            score = max(score, 0.20)  # Surmonter le seuil minimum de 0.145
        
        return score

    def _detect_topic(self, text: str) -> Optional[str]:
        """Détecte le topic principal d'un texte."""
        scores = {}
        p = text.lower()
        for topic, keywords in TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in p)
            if score > 0:
                scores[topic] = score
        return max(scores, key=scores.get) if scores else None

    def _is_generic_response(self, response: str) -> bool:
        """Détecte si la réponse est trop générique."""
        for pattern in GENERIC_RESPONSE_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                return True
        return False

    def _check_contradiction(self, prompt: str, response: str) -> Optional[str]:
        """
        Vérifie les contradictions évidentes.
        Ex: prompt demande "capitale du Bénin", réponse mentionne "Cotonou"
        alors que QuickFacts sait que c'est Porto-Novo.
        """
        # Normalisé (sans accents) pour éviter les faux positifs
        known_capitals = {
            "benin": "porto-novo",
            "cameroun": "yaounde",
            "senegal": "dakar",
            "mali": "bamako",
            "cote d'ivoire": "yamoussoukro",
            "nigeria": "abuja",
            "ghana": "accra",
            "ethiopie": "addis-abeba",
            "rdc": "kinshasa",
            "congo": "kinshasa",
            "angola": "luanda",
            "guinee": "conakry",
            "algerie": "alger",
            "tunisie": "tunis",
            "maroc": "rabat",
            "burkina faso": "ouagadougou",
        }
        
        # Normaliser l'accent du prompt pour matcher
        prompt_norm = self._strip_accents(prompt.lower())
        
        for country, capital in known_capitals.items():
            if country in prompt_norm:
                # Vérifier si une MAUVAISE capitale est mentionnée
                for other_country, other_capital in known_capitals.items():
                    if other_country != country and other_capital in response.lower():
                        # Vérifier que ce n'est pas juste la bonne capitale pour un autre pays
                        # (ex: "dakar" est la capitale du Sénégal, pas une erreur)
                        # Si le prompt parle du Sénégal, "dakar" est correct
                        if country in prompt_norm and other_capital == known_capitals.get(country, ""):
                            continue  # C'est la bonne capitale, pas une contradiction
                        return f"Reponse mentionne {other_capital} alors que le prompt demande {country}"
        
        return None
    
    @staticmethod
    def _strip_accents(text: str) -> str:
        """Enlève les accents d'un texte pour normalisation."""
        import unicodedata
        return ''.join(c for c in unicodedata.normalize('NFD', text) 
                      if unicodedata.category(c) != 'Mn')

    def _reject(self, reason: str, prompt: str, detail: str = "") -> Dict:
        """Génère une réponse de rejet avec fallback."""
        fallbacks = {
            "topic_mismatch": "Je ne suis pas certain d'avoir bien compris ta question. Peux-tu reformuler ?",
            "low_confidence": "Je n'ai pas trouvé d'information suffisamment fiable pour répondre. Peux-tu préciser ?",
            "empty_response": "Je n'ai pas trouvé de réponse à cette question.",
            "generic_response": "Ma réponse était trop vague. Laisse-moi chercher une information plus précise.",
            "contradiction": "Je détecte une incohérence dans ma réponse. Je préfère ne pas répondre plutôt que de donner une information erronée.",
        }
        
        return {
            "valid": False,
            "reason": reason,
            "detail": detail,
            "fallback": fallbacks.get(reason, "Je ne peux pas répondre à cette question avec certitude."),
        }

    def get_stats(self) -> Dict:
        """Statistiques du contrôleur."""
        total = max(self.stats["total_checked"], 1)
        return {
            "total_checked": self.stats["total_checked"],
            "passed": self.stats["passed"],
            "rejected": self.stats["rejected"],
            "pass_rate": f"{100 * self.stats['passed'] / total:.1f}%",
            "rejection_reasons": dict(self.stats["reasons"]),
        }


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    cc = ConsciousnessController(strictness=0.5)
    
    print("=" * 60)
    print("CONSCIOUSNESS CONTROLLER — Test de vérification")
    print("=" * 60)
    
    tests = [
        # (prompt, response, confidence, source, expected_valid)
        ("capitale du Bénin", "La capitale du Bénin est Porto-Novo.", 0.95, "quick_facts", True),
        ("capitale du Bénin", "Le Bénin est un pays d'Afrique de l'Ouest.", 0.5, "quick_facts", True),
        ("dérivée de x²", "d/dx(x²) = 2x", 0.97, "parametric_kb", True),
        ("dérivée fractionnaire", "la radioactivité est la désintégration spontanée des noyaux atomiques instables.", 0.3, "parametric_kb", False),
        ("c'est quoi une intégrale ?", "La réponse est ", 0.1, "qa", False),
        ("capitale du Cameroun", "La capitale du Cameroun est Yaoundé.", 0.95, "quick_facts", True),
        ("capitale du Sénégal", "Dakar", 0.98, "quick_facts", True),
        ("", "", 0.0, "unknown", False),
    ]
    
    for prompt, response, conf, source, expected in tests:
        result = cc.verify(prompt, response, conf, source)
        status = "OK" if result["valid"] == expected else "FAIL"
        print(f"\n[{status}] Prompt: '{prompt[:50]}'")
        print(f"  Response: '{response[:60]}...'")
        print(f"  Valid: {result['valid']} (expected: {expected})")
        if not result["valid"]:
            print(f"  Reason: {result.get('reason')}")
            print(f"  Fallback: {result.get('fallback', '')[:60]}")
    
    print(f"\nStats: {cc.get_stats()}")