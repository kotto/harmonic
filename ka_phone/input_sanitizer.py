#!/usr/bin/env python3
"""
INPUT SANITIZER — Normalisation intelligente des prompts
=========================================================
Corrige les variations d'écriture AVANT le traitement par le système :
  - Normalisation des accents (Bénin ↔ Benin)
  - Mapping synonymes (c koi → c'est quoi)
  - Correction des abréviations (cad → c'est-à-dire)
  - Auto-complétion des questions elliptiques
  - Mapping des variantes de mots

Objectif : zéro rejet dû à une variation orthographique.

Usage :
  from input_sanitizer import InputSanitizer
  sanitizer = InputSanitizer()
  clean, corrections = sanitizer.sanitize("capitale du Benin")
  # → "capitale du Bénin", [{"original":"Benin","corrected":"Bénin","reason":"accent"}]
"""

import re, unicodedata, os, json
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# ══════════════════════════════════════════════════════════════════════════
# ACCENT NORMALIZATION MAPS
# ══════════════════════════════════════════════════════════════════════════

# Mots fréquents SANS accent dans la base QuickFacts 
# → on les remplace par leur forme AVEC accent (canonique)
ACCENT_MAP = {
    # Capitales / Pays
    "benin": "Bénin",
    "benin.": "Bénin",
    "senegal": "Sénégal",
    "cameroun": "Cameroun",
    "cote d'ivoire": "Côte d'Ivoire",
    "cote d ivoire": "Côte d'Ivoire",
    "côte d'ivoire": "Côte d'Ivoire",
    "ethiopie": "Éthiopie",
    "éthiopie": "Éthiopie",
    "egypte": "Égypte",
    "égypte": "Égypte",
    "mali": "Mali",
    "burkina faso": "Burkina Faso",
    "republique": "République",
    "r.d.c.": "RDC",
    "rdc": "RDC",
    "états-unis": "États-Unis",
    "etats-unis": "États-Unis",
    "états unis": "États-Unis",
    "etats unis": "États-Unis",
    "royaume uni": "Royaume-Uni",
    "royaume-uni": "Royaume-Uni",
    "pays bas": "Pays-Bas",
    "pays-bas": "Pays-Bas",
    
    # Mathématiques
    "derivee": "dérivée",
    "derivees": "dérivées",
    "derivée": "dérivée",
    "dérivée": "dérivée",
    "integrale": "intégrale",
    "integral": "intégrale",
    "intégrale": "intégrale",
    "equation": "équation",
    "équation": "équation",
    "equations": "équations",
    "théorème": "théorème",
    "theoreme": "théorème",
    "théorème": "théorème",
    "probabilite": "probabilité",
    "probabilité": "probabilité",
    "probabilites": "probabilités",
    "trigonometrie": "trigonométrie",
    "trigonométrie": "trigonométrie",
    "geometrie": "géométrie",
    "géométrie": "géométrie",
    "algebre": "algèbre",
    "algèbre": "algèbre",
    "exponentielle": "exponentielle",
    "exponentiel": "exponentiel",
    "logarithme": "logarithme",
    "logarithm": "logarithme",
    "differentielle": "différentielle",
    "differentiel": "différentiel",
    "fractionnaire": "fractionnaire",
    "fractionnaire": "fractionnaire",
    
    # Sciences
    "medecine": "médecine",
    "médecine": "médecine",
    "medicament": "médicament",
    "médicament": "médicament",
    "energie": "énergie",
    "énergie": "énergie",
    "energies": "énergies",
    "electron": "électron",
    "électron": "électron",
    "electrons": "électrons",
    "atome": "atome",
    "atomes": "atomes",
    "nucleaire": "nucléaire",
    "nucléaire": "nucléaire",
    "molecule": "molécule",
    "molécule": "molécule",
    "molecules": "molécules",
    "temperature": "température",
    "température": "température",
    "phenomene": "phénomène",
    "phénomène": "phénomène",
    "phenomenes": "phénomènes",
    
    # Histoire / Géographie
    "revolution": "révolution",
    "révolution": "révolution",
    "siecle": "siècle",
    "siècle": "siècle",
    "siecles": "siècles",
    "empereur": "empereur",
    "empire": "empire",
    "pharaon": "pharaon",
    "pharaons": "pharaons",
    "pyramide": "pyramide",
    "pyramides": "pyramides",
    "obelisque": "obélisque",
    "obélisque": "obélisque",
    "hieroglyphe": "hiéroglyphe",
    "hiéroglyphe": "hiéroglyphe",
    "hiéroglyphes": "hiéroglyphes",
    "karnak": "Karnak",
    
    # Général
    "reponse": "réponse",
    "réponse": "réponse",
    "systeme": "système",
    "système": "système",
    "probleme": "problème",
    "problème": "problème",
    "problemes": "problèmes",
    "methode": "méthode",
    "méthode": "méthode",
    "methodes": "méthodes",
    "interet": "intérêt",
    "intérêt": "intérêt",
    "developpement": "développement",
    "développement": "développement",
    "economie": "économie",
    "économie": "économie",
    "ecologie": "écologie",
    "écologie": "écologie",
    "education": "éducation",
    "éducation": "éducation",
}

# ══════════════════════════════════════════════════════════════════════════
# SYNONYM / ABBREVIATION MAP
# ══════════════════════════════════════════════════════════════════════════

SYNONYM_MAP = {
    # Abréviations → forme complète
    "c koi": "c'est quoi",
    "c quoi": "c'est quoi",
    "c ki": "c'est qui",
    "keske": "qu'est-ce que",
    "kesk": "qu'est-ce que",
    "kestu": "qu'est-ce que",
    "pk": "pourquoi",
    "pq": "pourquoi",
    "cad": "c'est-à-dire",
    "cad.": "c'est-à-dire",
    "jsp": "je ne sais pas",
    "stp": "s'il te plaît",
    "svp": "s'il vous plaît",
    "dsl": "désolé",
    "mrc": "merci",
    
    # Anglicismes → français
    "what is": "qu'est-ce que",
    "what's": "qu'est-ce que",
    "how to": "comment",
    "how many": "combien",
    "how much": "combien",
    "where is": "où est",
    "where's": "où est",
    "who is": "qui est",
    "who's": "qui est",
    "when is": "quand",
    "why is": "pourquoi",
    "explain": "explique",
    "describe": "décris",
    "compute": "calcule",
    "calculate": "calcule",
    "find": "trouve",
    "solve": "résous",
    "factor": "factorise",
    "expand": "développe",
    
    # Variantes courantes
    "c'est quoi la capitale de": "quelle est la capitale de",
    "c'est quoi le nom de la capitale de": "quelle est la capitale de",
    "donne moi la capitale de": "quelle est la capitale de",
    "dis moi la capitale de": "quelle est la capitale de",
    "donne la capitale de": "quelle est la capitale de",
    "quel est le nom de la capitale de": "quelle est la capitale de",
    "capitale du": "capitale de",
    "capital de": "capitale de",
    "capitale d'": "capitale de",
    "la population de": "population de",
    "nb d'habitants": "population",
    "nombre d'habitants": "population",
    "combien d'habitants": "population",
    "c'est quand": "quand",
    "ça date de quand": "quand",
    "en quelle année": "quand",
}

# ══════════════════════════════════════════════════════════════════════════
# GENERIC ACCENT STRIPPER + RE-ADDER
# ══════════════════════════════════════════════════════════════════════════

class InputSanitizer:
    """
    Normalise les prompts avant traitement.
    Corrige accents, synonymes, abréviations.
    """

    def __init__(self):
        self.accent_map = ACCENT_MAP
        self.synonym_map = SYNONYM_MAP
        self.stats = {"total_sanitized": 0, "corrections_applied": 0}

    def sanitize(self, prompt: str) -> Tuple[str, List[Dict]]:
        """
        Normalise un prompt.
        
        Returns:
            (prompt_normalisé, liste_des_corrections)
        """
        self.stats["total_sanitized"] += 1
        corrections = []
        result = prompt.strip()
        
        # Étape 1 : Synonymes / abréviations (correction de phrases entières)
        result, corrections_syn = self._apply_synonyms(result)
        corrections.extend(corrections_syn)
        
        # Étape 2 : Correction des accents mot par mot
        result, corrections_acc = self._apply_accents(result)
        corrections.extend(corrections_acc)
        
        # Étape 3 : Nettoyage final (espaces multiples, ponctuation)
        result = self._clean_final(result)
        
        if corrections:
            self.stats["corrections_applied"] += 1
        
        return result, corrections

    def _apply_synonyms(self, text: str) -> Tuple[str, List[Dict]]:
        """Remplace les synonymes et abréviations."""
        corrections = []
        result = text
        
        for pattern, replacement in sorted(self.synonym_map.items(), 
                                           key=lambda x: -len(x[0])):  # Longest first
            if pattern in result.lower():
                old = result
                result = re.sub(r'\b' + re.escape(pattern) + r'\b', 
                               replacement, result, flags=re.IGNORECASE)
                if result != old:
                    corrections.append({
                        "original": pattern,
                        "corrected": replacement,
                        "reason": "synonym"
                    })
        
        return result, corrections

    def _apply_accents(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Corrige les mots sans accent vers leur forme accentuée.
        Travaille mot par mot pour éviter les faux positifs.
        """
        corrections = []
        words = text.split()
        corrected_words = []
        
        for word in words:
            word_lower = word.lower().rstrip(".,;:!?")
            
            # Chercher dans la map d'accents
            if word_lower in self.accent_map:
                replacement = self.accent_map[word_lower]
                # Si le mot original a une majuscule, préserver
                if word[0].isupper():
                    replacement = replacement[0].upper() + replacement[1:]
                # Préserver la ponctuation finale
                suffix = word[len(word.rstrip(".,;:!?")):]
                replacement += suffix
                
                if replacement != word:
                    corrections.append({
                        "original": word,
                        "corrected": replacement,
                        "reason": "accent"
                    })
                corrected_words.append(replacement)
            else:
                corrected_words.append(word)
        
        return " ".join(corrected_words), corrections

    def _clean_final(self, text: str) -> str:
        """Nettoyage final du texte."""
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Supprimer les espaces avant la ponctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        # Capitaliser la première lettre
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        return text.strip()

    @staticmethod
    def strip_accents(text: str) -> str:
        """Enlève tous les accents d'un texte."""
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )

    def get_stats(self) -> Dict:
        return self.stats


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sanitizer = InputSanitizer()
    
    tests = [
        "capitale du Benin",
        "capitale du Bénin",
        "capitale du benin",
        "c koi la capitale de Senegal",
        "keske c'est une derivee",
        "la population de cameroun",
        "donne moi la capitale de egypte",
        "what is the capital of cote d'ivoire",
        "explain integrale",
        "c quoi une equation differentielle",
        "capitale du Burkina Faso",
        "c'est qui le pharaon de karnak",
        "c'est quoi la derivee de x^2",
        "pk la revolution francaise",
        "cad la methode de resolution",
    ]
    
    print("=" * 70)
    print("INPUT SANITIZER — Test de normalisation")
    print("=" * 70)
    
    for prompt in tests:
        clean, corrections = sanitizer.sanitize(prompt)
        print(f"\nOriginal : '{prompt}'")
        print(f"Corrigé  : '{clean}'")
        for c in corrections:
            print(f"  → {c['original']} → {c['corrected']} ({c['reason']})")
    
    print(f"\nStats: {sanitizer.get_stats()}")