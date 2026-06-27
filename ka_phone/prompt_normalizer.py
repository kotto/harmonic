#!/usr/bin/env python3
"""
PROMPT NORMALIZER — Preprocessing intelligent des questions
==============================================================
Verifie, corrige et adapte chaque prompt avant qu'il n'entre
dans le pipeline KA Phone.

4 niveaux de normalisation :
  1. SYNTAXIQUE : correction typos, accents, ponctuation, espaces
  2. SÉMANTIQUE : expansion abréviations, normalisation chiffres/dates
  3. DOMAINE : adaptation du format au systeme (questions implicites)
  4. QUALITÉ : rejet des prompts vides, gibberish, trop courts, injection

Usage :
  from prompt_normalizer import PromptNormalizer
  pn = PromptNormalizer()
  clean, flags, score = pn.normalize("c koi la capital du bresil ?")
  # → ("Quelle est la capitale du Bresil ?", {"corrected": True, ...}, 0.95)
"""

import re, hashlib, json, os
from typing import Tuple, Dict, Optional, List
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════
# 1. CORRECTIONS SYNTAXIQUES
# ══════════════════════════════════════════════════════════════════════════

# Mots mal orthographiés fréquents → correction
TYPO_CORRECTIONS = {
    # SMS / langage texto
    "c": "c'est", "c koi": "qu'est-ce que", "c quoi": "qu'est-ce que",
    "koi": "quoi", "keske": "qu'est-ce que", "kesk": "qu'est-ce que",
    "pk": "pourquoi", "pourkoi": "pourquoi", "prk": "pourquoi",
    "j": "je", "t": "tu", "m": "me", "l": "le", "d": "de",
    "s": "sais", "g": "j'ai", "jsuis": "je suis", "chuis": "je suis",
    "t ki": "tu es qui", "c ki": "qui est",
    "jveux": "je veux", "jvoudrais": "je voudrais",
    "stp": "s'il te plait", "svp": "s'il vous plait",
    "mdr": "", "lol": "", "ptdr": "", "tg": "",
    "wsh": "bonjour", "wesh": "bonjour", "yo": "bonjour",
    "askip": "apparemment", "jcrois": "je crois",
    "pq": "pourquoi", "pcq": "parce que", "prcq": "parce que",
    "nn": "non", "ouais": "oui", "ouep": "oui", "yep": "oui",
    "tjr": "toujours", "tjs": "toujours", "tjr": "toujours",
    "bcp": "beaucoup", "vrm": "vraiment", "vrmt": "vraiment",
    "dsl": "desole", "deso": "desole", "dsl": "desole",
    "jsp": "je ne sais pas", "jspr": "j'espere",
    "tt": "tout", "ts": "tous", "tte": "toute",
    "mm": "meme", "qd": "quand", "kan": "quand",
    "kel": "quel", "kelle": "quelle", "kes": "qu'est-ce que",
    "pr": "pour", "pr le": "pour le", "pr la": "pour la",
    # Mots courants avec accents
    "etre": "etre", "etait": "etait", "etaient": "etaient",
    "deja": "deja", "ou": "ou", "a": "a", "ca": "ca",
    "voila": "voila", "voici": "voici",
    # Fautes d'orthographe courantes
    "language": "langage", "language": "langage",
    "gouvernement": "gouvernement", "gouvernemental": "gouvernemental",
    "developpement": "developpement",
    "apparament": "apparemment", "aparament": "apparemment",
    "evidament": "evidemment", "evidemment": "evidemment",
    "notament": "notamment",
}

# Patterns de correction : (regex, replacement)
SYNTAX_RULES_FR = [
    # Espaces avant/apres ponctuation
    (r'\s+([,.])(?!\d)', r'\1 '),           # espace apres virgule/point
    (r'\s+([!?])', r' \1'),                   # espace avant !?
    (r'\s{2,}', ' '),                         # espaces multiples → 1
    # Doubles ponctuations
    (r'[!?]{2,}', lambda m: m.group(0)[0]),  # !!! → !
    (r'\.{3,}', '...'),                        # .... → ...
    # Majuscule en debut de phrase
    (r'^([a-z])', lambda m: m.group(1).upper()),
    # Point en fin de phrase si absent (pour questions sans ?)
    (r'([^.!?])$', r'\1.'),
]

# Mots vides en fin de question (bruit)
TRAILING_NOISE = [
    r'\s*(?:s[\'i]l te plai[ts]?|s[\'i]l vous plai[ts]?|stp|svp|please|merci|thanks|thx)\s*[.!]*\s*$',
    r'\s*(?:hein|quoi|non\?|ok\?|tu vois|tu comprends)\s*[.!]*\s*$',
]


# ══════════════════════════════════════════════════════════════════════════
# 2. NORMALISATION SÉMANTIQUE
# ══════════════════════════════════════════════════════════════════════════

# Abréviations → forme complète
ABBREVIATIONS = {
    r'\bM\.\s': 'Monsieur ', r'\bMme\s': 'Madame ', r'\bMlle\s': 'Mademoiselle ',
    r'\bDr\s': 'Docteur ', r'\bPr\s': 'Professeur ',
    r'\betc\b': 'et cetera', r'\bex\b': 'exemple',
    r'\benv\.?\s': 'environ ', r'\bapprox\.?\s': 'approximativement ',
    r'\bnot\.?\s': 'notamment ', r'\bcf\.?\s': 'confer ',
    r'\bvs\b': 'versus', r'\baka\b': 'aussi connu comme',
    r'\bmin\b': 'minimum', r'\bmax\b': 'maximum',
}

# Normalisation numérique
def normalize_numbers(text: str) -> str:
    """Convertit les formats numeriques en texte lisible."""
    # "4e" → "quatrième" (garde si suivi de "dynastie" ou "siecle")
    text = re.sub(r'(\d+)e(?=\s+(?:dynastie|siecle|republique|armee|division|chaine|dimension))',
                  lambda m: _number_to_ordinal(int(m.group(1))), text)
    # "quatrième" → "4eme" (notre KB utilise ce format)
    # (on garde les deux formes pour le matching)
    return text


def _number_to_ordinal(n: int) -> str:
    ordinals = {
        1: "premiere", 2: "deuxieme", 3: "troisieme", 4: "quatrieme",
        5: "cinquieme", 6: "sixieme", 7: "septieme", 8: "huitieme",
        9: "neuvieme", 10: "dixieme", 11: "onzieme", 12: "douzieme",
        13: "treizieme", 14: "quatorzieme", 15: "quinzieme",
        16: "seizieme", 17: "dix-septieme", 18: "dix-huitieme",
        19: "dix-neuvieme", 20: "vingtieme", 21: "vingt-et-unieme",
        25: "vingt-cinquieme", 30: "trentieme", 40: "quarantieme",
        50: "cinquantieme", 100: "centieme",
    }
    return ordinals.get(n, f"{n}eme")


# ══════════════════════════════════════════════════════════════════════════
# 3. ADAPTATION DOMAINE
# ══════════════════════════════════════════════════════════════════════════

# Questions implicites → questions explicites
IMPLICIT_TO_EXPLICIT = [
    # "parle-moi de X" → "qu'est-ce que X ?"
    (r'^(?:parle[-\s]moi|parlez[-\s]moi|dis[-\s]moi|dites[-\s]moi|raconte[-\s]moi)\s+(?:de\s+)?(.+)',
     r'Qu\'est-ce que \1 ?'),
    # "je voudrais savoir X" → "X ?"
    (r'^(?:je voudrais|j[\'e]aimerais|je veux|je souhaite)\s+(?:savoir|connaitre|comprendre)\s+(.+)',
     r'\1 ?'),
    # "explique X" → "Qu'est-ce que X ?"
    (r'^(?:explique[sz]?[-\s]moi|explique[sz]?)\s+(.+)',
     r'Qu\'est-ce que \1 ?'),
    # "tu peux me dire X" → "X ?"
    (r'^(?:tu peux|peux[-\s]tu|tu pourrais|pourrais[-\s]tu)\s+(?:me\s+)?(?:dire|expliquer|donner)\s+(.+)',
     r'\1 ?'),
    # "c'est quoi X" → "Qu'est-ce que X ?"
    (r'^(?:c[\'e]est quoi)\s+(.+)', r'Qu\'est-ce que \1 ?'),
    # "donne-moi X" → "Qu'est-ce que X ?"
    (r'^(?:donne[-\s]moi|donnez[-\s]moi)\s+(?:des?\s+)?(?:informations?|infos?)\s+(?:sur\s+)?(.+)',
     r'Qu\'est-ce que \1 ?'),
    # "que sais-tu sur X" → "Qu'est-ce que X ?"
    (r'^(?:que\s+sais[-\s]tu|qu[\'e]est[-\s]ce\s+que\s+tu\s+sais)\s+(?:sur\s+|de\s+|a\s+propos\s+de\s+)?(.+)',
     r'Qu\'est-ce que \1 ?'),
]


# ══════════════════════════════════════════════════════════════════════════
# 4. QUALITÉ — Filtres de rejet
# ══════════════════════════════════════════════════════════════════════════

# Patterns de prompts invalides
REJECT_PATTERNS = [
    # Trop court (< 3 caractères significatifs)
    (r'^[^a-zA-Z0-9]*$', "characters_non_alpha"),
    # Injection / code
    (r'[{}\[\]<>]|\b(?:SELECT|DROP|DELETE|INSERT|UPDATE|WHERE|FROM|JOIN)\b', "potential_injection"),
    (r'\b(?:function|var |const |let |console\.log|eval\(|require\(|import )', "code_like"),
    # Gibberish (ratio consonnes > 80%)
    (None, "ratio_check"),  # Special: checked in code
    # URLs seules
    (r'^(?:https?://|www\.)\S+$', "url_only"),
    # Trop long (>2000 chars)
    (None, "too_long"),  # Special: checked in code
]

# Qualité minimale de prompt
MIN_SIGNIFICANT_CHARS = 3
MIN_ALPHA_RATIO = 0.4  # Au moins 40% de lettres
MAX_PROMPT_LENGTH = 2000


# ══════════════════════════════════════════════════════════════════════════
# NORMALIZER ENGINE
# ══════════════════════════════════════════════════════════════════════════

class PromptNormalizer:
    """
    Normalise et verifie chaque prompt avant traitement.
    
    Retourne (prompt_nettoye, flags, quality_score)
    """

    def __init__(self):
        self.stats = {
            "total_processed": 0,
            "corrected": 0,
            "rejected": 0,
            "adapted": 0,
            "shortened": 0,
        }

    def normalize(self, prompt: str) -> Tuple[str, Dict, float]:
        """
        Point d'entree principal.
        
        Args:
            prompt: Le prompt brut de l'utilisateur
            
        Returns:
            (clean_prompt, flags_dict, quality_score)
        """
        self.stats["total_processed"] += 1
        flags = {
            "original": prompt[:100],
            "corrected": False,
            "typos_fixed": 0,
            "abbreviations_expanded": 0,
            "implicit_to_explicit": False,
            "trailing_noise_removed": False,
            "length_before": len(prompt),
            "length_after": 0,
            "rejected": False,
            "reject_reason": None,
            "quality_score": 1.0,
            "language": "fr",
        }

        # Étape 0 : Nettoyage basique
        clean = prompt.strip()
        clean = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', clean)  # Caractères de contrôle

        # Étape 1 : Contrôle qualité — rejet rapide
        reject_result = self._quality_check(clean)
        if reject_result:
            flags["rejected"] = True
            flags["reject_reason"] = reject_result
            flags["quality_score"] = 0.0
            self.stats["rejected"] += 1
            return "", flags, 0.0

        # Étape 2 : Retirer le bruit de fin
        clean, trailing_removed = self._remove_trailing_noise(clean)
        if trailing_removed:
            flags["trailing_noise_removed"] = True
            self.stats["corrected"] += 1

        # Étape 3 : Correction de typos SMS
        clean, typos_fixed = self._fix_typos(clean)
        if typos_fixed > 0:
            flags["typos_fixed"] = typos_fixed
            flags["corrected"] = True
            self.stats["corrected"] += 1

        # Étape 3.5 : Normalisation des accents (bresil→brésil, ocean→océan, etc.)
        clean, accents_normalized = self._normalize_accents(clean)
        if accents_normalized:
            flags["accents_normalized"] = True
            flags["corrected"] = True
            self.stats["corrected"] += 1

        # Étape 4 : Syntaxe (ponctuation, espaces, majuscule)
        clean = self._fix_syntax(clean)
        if clean != prompt:
            flags["corrected"] = True

        # Étape 5 : Expansion des abréviations
        clean, abbrev_expanded = self._expand_abbreviations(clean)
        if abbrev_expanded > 0:
            flags["abbreviations_expanded"] = abbrev_expanded
            self.stats["corrected"] += 1

        # Étape 6 : Normalisation numérique
        clean = normalize_numbers(clean)

        # Étape 7 : Questions implicites → explicites
        clean, implicit_converted = self._convert_implicit(clean)
        if implicit_converted:
            flags["implicit_to_explicit"] = True
            self.stats["adapted"] += 1

        # Étape 8 : Détection de langue
        flags["language"] = self._detect_language(clean)

        # Étape 9 : Score de qualité
        flags["length_after"] = len(clean)
        quality = self._compute_quality(clean, flags)
        flags["quality_score"] = quality

        return clean, flags, quality

    def _quality_check(self, prompt: str) -> Optional[str]:
        """Vérifie si le prompt doit être rejeté."""
        if not prompt or len(prompt.strip()) < 1:
            return "empty"

        # Trop long
        if len(prompt) > MAX_PROMPT_LENGTH:
            return "too_long"

        # Que des caractères non-alpha
        alpha_chars = sum(1 for c in prompt if c.isalpha())
        if alpha_chars < MIN_SIGNIFICANT_CHARS:
            return "too_short"

        # Ratio alpha trop bas
        total_significant = sum(1 for c in prompt if c.isalpha() or c.isspace() or c.isdigit())
        if total_significant > 0:
            alpha_ratio = alpha_chars / total_significant
            if alpha_ratio < MIN_ALPHA_RATIO and len(prompt) < 30:
                return "gibberish"

        # Patterns de rejet
        for pattern, reason in REJECT_PATTERNS:
            if pattern is None:
                continue
            if re.search(pattern, prompt, re.IGNORECASE):
                return reason

        # URL seule
        if re.match(r'^(?:https?://|www\.)\S+$', prompt):
            return "url_only"

        return None  # OK

    def _remove_trailing_noise(self, prompt: str) -> Tuple[str, bool]:
        """Retire les mots parasites en fin de phrase."""
        original = prompt
        for pattern in TRAILING_NOISE:
            prompt = re.sub(pattern, '', prompt, flags=re.IGNORECASE)
        prompt = prompt.strip()
        return prompt, prompt != original

    def _fix_typos(self, prompt: str) -> Tuple[str, int]:
        """
        Corrige les erreurs de frappe courantes (SMS, texto).
        Retourne (texte_corrige, nombre_de_corrections).
        """
        words = prompt.split()
        corrected = []
        typos_fixed = 0

        i = 0
        while i < len(words):
            w = words[i]
            wl = w.lower()

            # Chercher des multi-mots d'abord (ex: "c koi" → "qu'est-ce que")
            combined_2 = f"{wl} {words[i+1].lower()}" if i + 1 < len(words) else None
            combined_3 = f"{combined_2} {words[i+2].lower()}" if combined_2 and i + 2 < len(words) else None

            # Check 3 mots
            if combined_3 and combined_3 in TYPO_CORRECTIONS:
                replacement = TYPO_CORRECTIONS[combined_3]
                if replacement:
                    corrected.append(replacement)
                typos_fixed += 1
                i += 3
                continue

            # Check 2 mots
            if combined_2 and combined_2 in TYPO_CORRECTIONS:
                replacement = TYPO_CORRECTIONS[combined_2]
                if replacement:
                    corrected.append(replacement)
                typos_fixed += 1
                i += 2
                continue

            # Check 1 mot
            if wl in TYPO_CORRECTIONS:
                replacement = TYPO_CORRECTIONS[wl]
                if replacement:
                    # Preserver la majuscule
                    if w[0].isupper():
                        replacement = replacement[0].upper() + replacement[1:]
                    corrected.append(replacement)
                typos_fixed += 1
            else:
                corrected.append(w)

            i += 1

        # Nettoyer les espaces doubles créés par les remplacements
        result = " ".join(corrected)
        result = re.sub(r'\s{2,}', ' ', result)
        return result, typos_fixed

    def _normalize_accents(self, text: str) -> Tuple[str, bool]:
        """Normalise les mots sans accent vers leur forme sans accent pour
        que le matching avec QuickFacts fonctionne meme si l'utilisateur
        tape sans accents (ex: bresil -> bresil, ocean -> ocean)."""
        replacements = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o',
            'û': 'u', 'ù': 'u', 'ü': 'u',
            'ç': 'c', 'œ': 'oe', 'æ': 'ae',
            'ñ': 'n', 'ý': 'y', 'ÿ': 'y',
        }
        result = text
        changed = False
        for acc, plain in replacements.items():
            if acc in result:
                result = result.replace(acc, plain)
                changed = True
        return result, changed

    def _fix_syntax(self, prompt: str) -> str:
        """Corrige la syntaxe : ponctuation, espaces, majuscule."""
        for pattern, replacement in SYNTAX_RULES_FR:
            if callable(replacement):
                prompt = re.sub(pattern, replacement, prompt)
            else:
                prompt = re.sub(pattern, replacement, prompt)
        return prompt.strip()

    def _expand_abbreviations(self, prompt: str) -> Tuple[str, int]:
        """Expanse les abreviations en texte complet."""
        expanded = prompt
        count = 0
        for pattern, replacement in ABBREVIATIONS.items():
            new_text = re.sub(pattern, replacement, expanded)
            if new_text != expanded:
                count += 1
                expanded = new_text
        return expanded, count

    def _convert_implicit(self, prompt: str) -> Tuple[str, bool]:
        """Convertit les questions implicites en questions explicites."""
        for pattern, replacement in IMPLICIT_TO_EXPLICIT:
            match = re.match(pattern, prompt, re.IGNORECASE)
            if match:
                new_prompt = replacement.replace(r'\1', match.group(1).strip())
                # Nettoyer
                new_prompt = re.sub(r'\s+', ' ', new_prompt).strip()
                if not new_prompt.endswith('?'):
                    new_prompt += ' ?'
                return new_prompt, True
        return prompt, False

    def _detect_language(self, prompt: str) -> str:
        """Détecte la langue du prompt (français ou anglais)."""
        # Indices français
        fr_indicators = [
            r'\b(?:le|la|les|un|une|des|de|du|est|sont|etait|dans|sur|pour|avec|pas|plus|moins|très|bien|bon|beau|petit|grand|quoi|qui|que|comment|pourquoi|quand|ou|combien)\b',
            r'[éèêëàâîïôûùçœæ]',
            r'\b(?:c\'est|qu\'est|n\'est|s\'est|l\'a|d\'un|d\'une|j\'ai|t\'as)\b',
        ]
        en_indicators = [
            r'\b(?:the|a|an|is|are|was|were|in|on|at|for|with|not|more|less|very|good|bad|big|small|what|who|which|how|why|when|where|how many)\b',
        ]

        fr_score = sum(1 for p in fr_indicators if re.search(p, prompt, re.IGNORECASE))
        en_score = sum(1 for p in en_indicators if re.search(p, prompt, re.IGNORECASE))

        if fr_score > en_score:
            return "fr"
        elif en_score > fr_score:
            return "en"
        return "fr"  # Default FR

    def _compute_quality(self, prompt: str, flags: Dict) -> float:
        """Calcule un score de qualite du prompt (0-1)."""
        score = 1.0

        # Trop court
        if len(prompt) < 10:
            score -= 0.3
        elif len(prompt) < 20:
            score -= 0.1

        # Ratio alpha
        alpha = sum(1 for c in prompt if c.isalpha()) / max(len(prompt), 1)
        if alpha < 0.5:
            score -= 0.3

        # Termine par ?
        if prompt.strip().endswith('?'):
            score += 0.05

        # Contient des mots significatifs
        significant_words = re.findall(r'[a-zA-Z]{4,}', prompt)
        if len(significant_words) < 2:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "correction_rate": (
                self.stats["corrected"] / max(self.stats["total_processed"], 1)
            ),
            "rejection_rate": (
                self.stats["rejected"] / max(self.stats["total_processed"], 1)
            ),
        }


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pn = PromptNormalizer()

    tests = [
        "c koi la capital du bresil ?",
        "pk le ciel est bleu",
        "je voudrais savoir qui a construit la pyramide de kheops",
        "parle-moi de napoleon",
        "explique moi la relativité",
        "wtf ???!!!!",
        "donne-moi des infos sur le cameroun stp merci",
        "",  # doit etre rejete
        "azertyuiop",  # gibberish
        "SELECT * FROM users",  # injection
        "tu peux me dire comment mieux dormir ?",
        "jsuis fatigue comment dormir stp",
    ]

    print(f"{'ORIGINAL':<55} | {'NORMALISE':<55} | {'QUAL':>5} | FLAGS")
    print("-" * 130)

    for q in tests:
        clean, flags, score = pn.normalize(q)
        if flags["rejected"]:
            print(f"{q[:52]:<55} | [REJETE: {flags['reject_reason']:<20}] | {score:.2f}")
        else:
            change = "*" if flags["corrected"] or flags["implicit_to_explicit"] else " "
            flag_str = []
            if flags["typos_fixed"] > 0: flag_str.append(f"typos:{flags['typos_fixed']}")
            if flags["abbreviations_expanded"] > 0: flag_str.append(f"abbrev:{flags['abbreviations_expanded']}")
            if flags["implicit_to_explicit"]: flag_str.append("implicit→explicit")
            if flags["trailing_noise_removed"]: flag_str.append("noise_removed")
            flags_txt = ", ".join(flag_str) if flag_str else "-"
            print(f"{q[:52]:<55} | {change}{clean[:52]:<54} | {score:.2f} | {flags_txt}")

    print(f"\nStats: {json.dumps(pn.get_stats(), indent=2)}")