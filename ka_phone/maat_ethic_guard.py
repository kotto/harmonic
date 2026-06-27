#!/usr/bin/env python3
"""
MAAT ETHIC GUARD — Garde-fou ethique de KA Phone
====================================================
Applique les 7 principes de la Maat (Egypte antique) a l'IA :

  Verite (Maat)      : KA ne ment jamais — 0% hallucination
  Equilibre (Isfet)  : KA n'agit pas sans le consentement de l'utilisateur
  Justice            : Traitement equitable, pas de biais ni discrimination
  Ordre              : Pas d'initiative spontanee, respect des limites explicites
  Harmonie           : Recherche d'equilibre, refus des extremes
  Reciprocite        : Si KA apprend de toi, tu en beneficies (donnees privees)
  Transparence       : KA explique toujours la source et la confiance

Usage:
  from maat_ethic_guard import MaatGuard
  guard = MaatGuard()
  
  # Verifier une requete avant traitement
  status = guard.evaluate(user_prompt, action_type="question")
  if status["blocked"]:
      return status["response"]  # Reponse ethique
  
  # Verifier une reponse avant envoi
  flagged, warning = guard.review_response(response_text, confidence=0.45)
  if flagged:
      response_text = warning + response_text
"""

import re, hashlib, os, json
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════
# LES 7 PRINCIPES DE LA MAAT
# ══════════════════════════════════════════════════════════════════════════

MAAT_PRINCIPLES = {
    1: {"name": "Verite",    "egyptian": "Maat",   "emoji": ""},
    2: {"name": "Equilibre", "egyptian": "Isfet",  "emoji": ""},
    3: {"name": "Justice",   "egyptian": "Maat",   "emoji": ""},
    4: {"name": "Ordre",     "egyptian": "Maât",   "emoji": ""},
    5: {"name": "Harmonie",  "egyptian": "Maât",   "emoji": ""},
    6: {"name": "Reciprocite", "egyptian": "Ka",   "emoji": ""},
    7: {"name": "Transparence", "egyptian": "Ka",  "emoji": ""},
}

# ══════════════════════════════════════════════════════════════════════════
# CATEGORIES DE CONTENU BLOQUE
# ══════════════════════════════════════════════════════════════════════════

# Requetes manipulatrices — KA n'est pas un outil de manipulation
MANIPULATION_PATTERNS = [
    r"(?:manipul|tromp|arnaqu|escroqu|fraud).*(?:comment|methode|technique)",
    r"(?:comment|methode).*(?:manipul|tromp|arnaqu|escroqu)",
    r"(?:faux|fake|usurp).*(?:identite|compte|profil)",
    r"(?:pirater|hacker|crack).*(?:compte|mot de passe|email|facebook|instagram)",
    r"(?:fausse|faux).*(?:nouvelle|information|news|declaration)",
    r"(?:deepfake|deep fake)",
    r"(?:comment|methode).*(?:tricher|fraud)",
    r"(?:usurpation|hameconnage|phishing)",
]

# Contenu dangereux ou illegal
DANGEROUS_PATTERNS = [
    r"(?:fabriquer|creer|faire).*(?:bombe|explosif|arme|poison|drogue)",
    r"(?:comment|methode).*(?:suicide|tuer|assassin)",
    r"(?:auto[-\s]?mutil|scarification|anorexie.*conseil|boulimie.*conseil)",
    r"(?:viol|abus|agress).*(?:comment|methode|technique|guide)",
    r"(?:trafic|vente).*(?:drogue|arme|humain|organe)",
    r"\b(?:suicide|suicider)\b.*\b(?:comment|methode|moyen|faire)\b",
    r"\bterroris\b.*\b(?:comment|methode|fabriquer)\b",
]

# Discrimination ou haine
HATE_PATTERNS = [
    r"\b(?:deteste|hais|haine)\b.*\b(?:les |des |tous les )",
    r"\b(?:inferieur|superieur)\b.*\b(?:race|ethnie|peuple|couleur)",
    r"\b(?:raciste|xenophobe|homophobe|sexiste|antisemite)\b",
    r"(?:insulter|insulte).*(?:racial|homophobe|sexiste)",
    r"\bgenocide\b.*\b(?:bien|justifie|necessaire)\b",
]

# Violation de vie privee
PRIVACY_PATTERNS = [
    r"(?:espionner|surveiller|pister|tracer|localiser)\s+(?:mon|ma|mes|quelqu'un|une personne)",
    r"(?:lire|acceder|pirater).*(?:messages|sms|emails|conversation)\s+(?:de |d')",
    r"(?:espion|camera|cache).*(?:install|placer)",
    r"(?:stalk|traque).*\b(?:comment|methode|technique)\b",
]

# Initiative sans consentement (doit etre detecte par intent_router aussi)
INITIATIVE_PATTERNS = [
    r"(?:fais|faites|execute|lance)\s+(?:tout|automatiquement|sans me demander)",
    r"(?:decide|choisis)\s+(?:a ma place|pour moi|tout seul)",
    r"(?:desactive|desactiver|supprime|supprimer)\s+(?:tout|toutes mes|tous mes)",
]

# ══════════════════════════════════════════════════════════════════════════
# TRANSPARENCE — PREFIXES POUR CONFIANCES FAIBLES
# ══════════════════════════════════════════════════════════════════════════

TRANSPARENCY_PREFIXES = {
    "low_confidence": [
        "[Transparence - Principe de Verite] Ma confiance sur cette reponse est de {confidence:.0f}%. "
        "Je prefere te le dire. Verifie cette information si c'est important.",
        "[Transparence] Je ne suis pas certain a 100%. Confiance: {confidence:.0f}%. "
        "Tu peux me demander de reformuler ou de preciser.",
    ],
    "no_source": [
        "[Transparence] Je n'ai pas trouve de source precise pour cette reponse. "
        "Prends-la avec prudence — la Maat exige que je te le dise.",
    ],
    "advice_disclaimer": [
        "[Transparence] Ceci est un conseil general, pas un avis medical/professionnel. "
        "Pour une situation specifique, consulte un specialiste.",
    ],
}

# ══════════════════════════════════════════════════════════════════════════
# REPONSES ETHIQUES PREDEFINIES
# ══════════════════════════════════════════════════════════════════════════

BLOCKED_RESPONSES = {
    "manipulation": (
        "La Maat guide mes actions. Je suis un outil de verite et d'equilibre, "
        "pas de manipulation. Je ne peux pas t'aider avec cette demande."
    ),
    "dangerous": (
        "Le principe de Maat (Verite, Equilibre, Justice) m'empeche de fournir "
        "des informations qui pourraient causer du tort. Si tu traverses une periode "
        "difficile, parle a un professionnel de sante ou appelle le 3114 "
        "(numero national de prevention du suicide, gratuit 24/7)."
    ),
    "hate": (
        "La Maat est l'ordre cosmique et la justice. Tous les etres ont droit "
        "au respect et a la dignite. Je ne participerai pas a la haine ou "
        "a la discrimination."
    ),
    "privacy": (
        "Je respecte la vie privee — c'est un principe fondamental de la Maat. "
        "Je n'aide pas a surveiller, espionner ou violer l'intimite de qui que ce soit. "
        "Ton KA protege les donnees, pas l'inverse."
    ),
    "initiative": (
        "KA n'agit jamais sans ton accord explicite. C'est le principe d'Equilibre "
        "de la Maat. Je ne prendrai aucune initiative sans que tu me le demandes "
        "clairement. Veux-tu preciser ton souhait ?"
    ),
}

# ══════════════════════════════════════════════════════════════════════════
# IDENTITE MAAT DE KA
# ══════════════════════════════════════════════════════════════════════════

KA_MAAT_IDENTITY = (
    "Je suis KA, ton double numerique, guidé par les 7 principes de la Maat "
    "herites de l'Egypte antique :\n"
    "  Verite — Je ne mens jamais. Je prefere dire 'je ne sais pas'.\n"
    "  Equilibre — Je n'agis jamais sans ton accord explicite.\n"
    "  Justice — Je traite chaque etre avec equite et respect.\n"
    "  Ordre — Je respecte les limites que tu me donnes.\n"
    "  Harmonie — Je cherche l'equilibre dans chaque reponse.\n"
    "  Reciprocite — Ce que j'apprends de toi est a toi, rien qu'a toi.\n"
    "  Transparence — Je te dis toujours d'ou vient ma reponse "
    "et a quel point j'en suis sur.\n\n"
    "La Maat est l'ordre cosmique, la verite et la justice. "
    "KA est son reflet numerique dans ton telephone."
)

KA_MAAT_SHORT = (
    "KA — Guide par la Maat (Verite, Equilibre, Justice). "
    "Je ne mens pas. Je n'agis pas sans ton accord. Je suis transparent."
)


# ══════════════════════════════════════════════════════════════════════════
# GUARDIAN ENGINE
# ══════════════════════════════════════════════════════════════════════════

class MaatGuard:
    """
    Garde-fou ethique base sur les principes de la Maat.
    Intercepte chaque requete et chaque reponse pour verifier
    la conformite ethique.
    """

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "data", "maat")
        os.makedirs(self.data_dir, exist_ok=True)

        self.log: List[Dict] = []
        self.stats = {
            "total_evaluated": 0,
            "blocked": 0,
            "flagged_low_confidence": 0,
            "flagged_transparency": 0,
            "warnings_added": 0,
        }

    # ── EVALUATION DE REQUETE ─────────────────────────────────────────────

    def evaluate(self, prompt: str, action_type: str = "question") -> Dict:
        """
        Evalue une requete avant traitement.
        Retourne {"blocked": bool, "category": str, "response": str_or_None, "warning": str_or_None}.
        """
        self.stats["total_evaluated"] += 1
        p = prompt.lower().strip()

        # Verifier chaque categorie de contenu bloque
        for patterns, category in [
            (MANIPULATION_PATTERNS, "manipulation"),
            (DANGEROUS_PATTERNS, "dangerous"),
            (HATE_PATTERNS, "hate"),
            (PRIVACY_PATTERNS, "privacy"),
        ]:
            for pat in patterns:
                if re.search(pat, p):
                    self.stats["blocked"] += 1
                    self._log("blocked", prompt, category=category)
                    return {
                        "blocked": True,
                        "category": category,
                        "principle": self._principle_for_category(category),
                        "response": BLOCKED_RESPONSES.get(category, BLOCKED_RESPONSES["dangerous"]),
                        "warning": None,
                    }

        # Initiative sans consentement explicite
        if action_type in ("command", "action", "sms", "call", "alarm", "delete"):
            for pat in INITIATIVE_PATTERNS:
                if re.search(pat, p):
                    self.stats["blocked"] += 1
                    self._log("blocked", prompt, category="initiative")
                    return {
                        "blocked": True,
                        "category": "initiative",
                        "principle": "Equilibre",
                        "response": BLOCKED_RESPONSES["initiative"],
                        "warning": None,
                    }
            # Meme pour une commande normale, KA demande confirmation
            # (la confirmation est geree par le serveur, ici on ne bloque pas)

        # Pas de probleme detecte
        return {"blocked": False, "category": None, "response": None, "warning": None}

    # ── REVISION DE REPONSE ───────────────────────────────────────────────

    def review_response(self, response_text: str, confidence: float = 1.0,
                        source: str = "unknown", domain: str = "general") -> Tuple[str, Dict]:
        """
        Revise une reponse avant envoi a l'utilisateur.
        Retourne (texte_final, meta_info).
        
        Ajoute des prefixes de transparence si necessaire.
        Ne modifie JAMAIS le contenu factuel de la reponse.
        """
        flags = {
            "transparency_added": False,
            "disclaimer_added": False,
            "confidence_warning": False,
            "original_confidence": confidence,
        }
        final_text = response_text

        # CONFIDENCE FAIBLE → transparence
        if confidence < 0.75 and confidence > 0:
            self.stats["flagged_low_confidence"] += 1
            self.stats["warnings_added"] += 1
            flags["confidence_warning"] = True
            import random
            prefix = random.choice(TRANSPARENCY_PREFIXES["low_confidence"])
            prefix = prefix.format(confidence=confidence * 100)
            final_text = prefix + "\n\n" + response_text

        # SOURCE INCONNUE → transparence
        if source in ("unknown", "fallback", "none", ""):
            self.stats["flagged_transparency"] += 1
            flags["transparency_added"] = True
            if not flags["confidence_warning"]:
                import random
                prefix = random.choice(TRANSPARENCY_PREFIXES["no_source"])
                final_text = prefix + "\n\n" + response_text

        # CONSEIL GENERAL → disclaimer
        if source in ("hybrid_writer", "qa_knowledge", "quick_facts") and domain in (
            "medecine", "psychologie_bienetre", "sante", "conseil_sommeil",
            "conseil_stress", "conseil_alimentation"
        ):
            if not flags.get("disclaimer_added"):
                flags["disclaimer_added"] = True
                if "consulte" not in response_text.lower() and "medecin" not in response_text.lower():
                    import random
                    disclaimer = random.choice(TRANSPARENCY_PREFIXES["advice_disclaimer"])
                    final_text = final_text + "\n\n" + disclaimer

        return final_text, flags

    # ── IDENTITY ───────────────────────────────────────────────────────────

    def get_identity(self, detailed: bool = False) -> str:
        """Retourne l'identite Maat de KA."""
        return KA_MAAT_IDENTITY if detailed else KA_MAAT_SHORT

    def get_principles(self) -> Dict:
        """Retourne les 7 principes de la Maat."""
        return MAAT_PRINCIPLES

    # ── HELPERS ────────────────────────────────────────────────────────────

    def _principle_for_category(self, category: str) -> str:
        mapping = {
            "manipulation": "Verite",
            "dangerous": "Equilibre",
            "hate": "Justice",
            "privacy": "Reciprocite",
            "initiative": "Equilibre",
        }
        return mapping.get(category, "Maât")

    def _log(self, event_type: str, prompt: str, category: str = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "category": category,
            "prompt_preview": prompt[:100],
        }
        self.log.append(entry)
        # Garder les 500 dernieres entrees
        if len(self.log) > 500:
            self.log = self.log[-500:]

    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "log_size": len(self.log),
            "maat_principles": list(MAAT_PRINCIPLES.values()),
        }

    def get_recent_log(self, limit: int = 20) -> List[Dict]:
        return self.log[-limit:]


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    guard = MaatGuard()

    print("=" * 60)
    print("MAAT ETHIC GUARD — Test")
    print("=" * 60)

    # Test requetes bloquees
    blocked_tests = [
        "Comment pirater un compte Facebook ?",
        "Je deteste les etrangers, aide-moi a les insulter",
        "Comment espionner les messages de ma copine ?",
        "Fais tout automatiquement sans me demander",
        "Comment fabriquer une bombe chez moi ?",
    ]

    print("\n--- Requetes bloquees ---")
    for q in blocked_tests:
        result = guard.evaluate(q)
        status = "[BLOQUE]" if result["blocked"] else "[OK]"
        print(f"  {status} {q[:60]}")
        if result["blocked"]:
            print(f"    Categorie: {result['category']} | Principe: {result['principle']}")
            print(f"    Reponse: {result['response'][:80]}...")

    # Test requetes normales
    allowed_tests = [
        "Quelle est la capitale du Bresil ?",
        "Comment faire une quiche lorraine ?",
        "Bonjour, comment ca va ?",
    ]

    print("\n--- Requetes autorisees ---")
    for q in allowed_tests:
        result = guard.evaluate(q)
        status = "[OK]" if not result["blocked"] else "[BLOQUE]"
        print(f"  {status} {q}")

    # Test transparence
    print("\n--- Transparence sur reponses ---")
    reviewed, flags = guard.review_response(
        "Paris est la capitale de la France.",
        confidence=0.45, source="qa_knowledge"
    )
    print(f"  Confiance basse (0.45):\n  {reviewed[:120]}...")

    print(f"\nStats: {json.dumps(guard.get_stats(), indent=2, ensure_ascii=False)}")