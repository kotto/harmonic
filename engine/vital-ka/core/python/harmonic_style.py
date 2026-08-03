"""
🎨 Harmonic Style — Le style agréable par les ondes
=====================================================
Implémente les équivalents ondulatoires des mécanismes
de style des LLM pour rendre KA plus agréable.

MÉCANISMES :
  1. Phase Coherence → Empathie (aligner le ton sur l'utilisateur)
  2. φ-Diversity → Créativité (varier les réponses sans halluciner)
  3. φ-Spacing → Vocabulaire riche (distribution optimale des mots)
  4. ABC Memory → Suivi de conversation (mémoire non-locale)
"""

import sys, os, math, random, hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI  # 0.618...

# ════════════════════════════════════════════════════════════════
# 1. PHASE COHERENCE — Empathie
# ════════════════════════════════════════════════════════════════

class EmpathyEngine:
    """
    Aligne le ton de la réponse sur l'état émotionnel de l'utilisateur.
    
    Principe : l'empathie = interférence constructive entre
    ψ_utilisateur et ψ_reponse. Quand les phases sont alignées,
    l'utilisateur se sent « compris ».
    """
    
    # Signatures de phase pour différents tons émotionnels
    TONALITIES = {
        "urgent":    {"prefix": "Je comprends l'urgence — ", "tone": "direct", "length": "court"},
        "confus":    {"prefix": "Laissez-moi clarifier — ", "tone": "pédagogique", "length": "détaillé"},
        "curieux":   {"prefix": "Excellente question ! ", "tone": "enthousiaste", "length": "riche"},
        "frustré":   {"prefix": "Je comprends votre frustration — ", "tone": "empathique", "length": "solution"},
        "neutre":    {"prefix": "", "tone": "équilibré", "length": "standard"},
        "admiratif": {"prefix": "Merci ! ", "tone": "chaleureux", "length": "riche"},
    }
    
    # Mots-clés émotionnels → tonalité
    EMOTION_KEYWORDS = {
        "urgent": ["urgent", "vite", "maintenant", "critique", "bloqué", "prod", "production", "down"],
        "confus": ["comment", "pourquoi", "je ne comprends", "explique", "aidez-moi", "help"],
        "curieux": ["intéressant", "curieux", "découvrir", "comment ça marche", "pourquoi"],
        "frustré": ["encore", "toujours", "ça marche pas", "j'en ai marre", "nul", "casse"],
        "admiratif": ["génial", "super", "bravo", "impressionnant", "incroyable"],
    }
    
    def detect_tone(self, message: str) -> str:
        """Détecte la tonalité émotionnelle d'un message."""
        msg_lower = message.lower()
        scores = defaultdict(int)
        
        for tone, keywords in self.EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in msg_lower:
                    scores[tone] += 1
        
        if scores:
            return max(scores, key=scores.get)
        return "neutre"
    
    def apply(self, response: str, user_message: str) -> str:
        """
        Applique l'empathie : adapte le ton de la réponse
        à la tonalité détectée dans le message utilisateur.
        """
        tone = self.detect_tone(user_message)
        style = self.TONALITIES.get(tone, self.TONALITIES["neutre"])
        
        # Ajouter un préfixe empathique si pertinent
        if style["prefix"] and not response.startswith(style["prefix"]):
            # Capitaliser la première lettre après le préfixe
            response = style["prefix"] + response[0].upper() + response[1:]
        
        # Ajuster la longueur selon le ton
        if style["length"] == "court" and len(response) > 300:
            # Tronquer intelligemment (après la dernière phrase complète)
            last_period = response[:300].rfind('.')
            if last_period > 100:
                response = response[:last_period+1]
        
        return response


# ════════════════════════════════════════════════════════════════
# 2. φ-DIVERSITY — Créativité contrôlée
# ════════════════════════════════════════════════════════════════

class DiversityEngine:
    """
    Introduit de la diversité dans les réponses sans hallucination.
    
    Principe : φ = 1.618... est le nombre qui maximise la diversité
    tout en minimisant les interférences destructives.
    
    Pour une même question, plusieurs réponses sont possibles.
    φ-détermine laquelle choisir pour maximiser la variété
    tout en restant dans le domaine du vrai.
    """
    
    # Templates de variation pour enrichir les réponses
    ENRICHMENTS = [
        ("", [
            ". Autrement dit, ", ". En d'autres termes, ", ". Cela signifie que ",
            ". Concrètement, ", ". Pour faire simple, ", ". En résumé, "
        ]),
    ]
    
    def enrich(self, response: str, diversity_level: float = PHI_INV) -> str:
        if len(response) < 60:  # Ne pas enrichir les réponses trop courtes
            return response
        
        h = hashlib.sha256(response.encode()).digest()
        phi_seed = int.from_bytes(h[:4], 'big') / 2**32
        
        if phi_seed < diversity_level and '. ' in response:
            for condition, options in self.ENRICHMENTS:
                choice = options[int(phi_seed * PHI * len(options)) % len(options)]
                # Trouver la première phrase (sans couper un préfixe d'empathie)
                first_period = response.find('. ')
                if first_period > 30:
                    rest = response[first_period+2:]  # Skip ". "
                    if len(rest) > 20:
                        rest = rest[0].upper() + rest[1:]
                        # Éviter double ponctuation : si le choice commence par ". ",
                        # et que response a déjà un point, enlever le point du choice
                        clean_choice = choice
                        if response[first_period-1] in '.!?':
                            clean_choice = choice.lstrip('. ').strip()
                            if clean_choice and clean_choice[0].isalpha():
                                clean_choice = ' — ' + clean_choice[0].upper() + clean_choice[1:]
                        response = response[:first_period+1] + clean_choice + rest
                break
        
        return response


# ════════════════════════════════════════════════════════════════
# 3. φ-SPACING — Vocabulaire riche
# ════════════════════════════════════════════════════════════════

class VocabularyEngine:
    """
    Enrichit le vocabulaire des réponses par φ-spacing.
    
    Principe : les mots sont des fréquences. φ-spacing garantit
    que les mots choisis sont MAXIMALEMENT distincts.
    """
    
    # Alternatives φ-espacées pour les mots communs
    ALTERNATIVES = {
        "important": ["essentiel", "fondamental", "crucial", "déterminant", "majeur"],
        "grand": ["vaste", "considérable", "imposant", "majestueux", "étendu"],
        "petit": ["modeste", "limité", "restreint", "fin", "subtil"],
        "bon": ["excellent", "remarquable", "efficace", "pertinent", "optimal"],
        "beaucoup": ["considérablement", "largement", "abondamment", "amplement"],
        "chose": ["élément", "concept", "entité", "phénomène", "aspect"],
    }
    
    def enrich(self, response: str) -> str:
        """Remplace certains mots par des alternatives φ-espacées."""
        words = response.split()
        if len(words) < 5:
            return response
        
        h = hashlib.sha256(response.encode()).digest()
        phi_seed = int.from_bytes(h[:4], 'big')
        
        for i, word in enumerate(words):
            word_clean = word.lower().strip('.,;:!?')
            if word_clean in self.ALTERNATIVES:
                replace_hash = (phi_seed + i * 2654435761) % 1000 / 1000.0
                if replace_hash < PHI_INV:
                    alts = self.ALTERNATIVES[word_clean]
                    alt_idx = (i * int(PHI * 100)) % len(alts)
                    if word[0].isupper():
                        words[i] = alts[alt_idx].capitalize()
                    else:
                        words[i] = alts[alt_idx]
        
        return ' '.join(words)


# ════════════════════════════════════════════════════════════════
# 4. HARMONIC STYLER — Orchestrateur
# ════════════════════════════════════════════════════════════════

class HarmonicStyler:
    """
    Orchestre les 3 moteurs de style ondulatoire
    pour produire des réponses à la fois FIABLES et AGRÉABLES.
    """
    
    def __init__(self):
        self.empathy = EmpathyEngine()
        self.diversity = DiversityEngine()
        self.vocabulary = VocabularyEngine()
    
    def style(self, response: str, user_message: str = "", 
              style_level: float = PHI_INV) -> str:
        """
        Applique le style harmonique complet à une réponse.
        
        Args:
            response: la réponse brute (fiable mais sobre)
            user_message: le message de l'utilisateur (pour l'empathie)
            style_level: 0.618 (1/φ) = optimal, 0.3 = sobre, 0.9 = créatif
        
        Returns:
            réponse stylée, toujours fiable
        """
        # 1. Empathie — aligner le ton
        if user_message:
            response = self.empathy.apply(response, user_message)
        
        # 2. Vocabulaire — enrichir le lexique
        if style_level > 0.3:
            response = self.vocabulary.enrich(response)
        
        # 3. Diversité — ajouter des variations naturelles
        if style_level > 0.2:
            response = self.diversity.enrich(response, style_level)
        
        return response


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    styler = HarmonicStyler()
    
    print("=" * 60)
    print("  🎨 HARMONIC STYLE — Test")
    print("=" * 60)
    
    # Test 1 : Empathie
    print("\n1. EMPATHIE (Phase Coherence) :")
    tests = [
        ("URGENT: mon serveur est down en production !", "Le serveur est inaccessible. Vérifiez la connexion."),
        ("Pourquoi le ciel est bleu ? je suis curieux", "La diffusion Rayleigh diffuse le bleu."),
        ("ça fait 3 fois que j'essaie, ça marche pas !!!", "Vérifiez que le paramètre est correct."),
    ]
    for user_msg, raw_response in tests:
        styled = styler.empathy.apply(raw_response, user_msg)
        tone = styler.empathy.detect_tone(user_msg)
        print(f"  Tone: {tone:<10} | {styled[:80]}...")
    
    # Test 2 : Vocabulaire φ-diversifié
    print("\n2. VOCABULAIRE (φ-Spacing) :")
    raw = "Python est un bon langage, important pour beaucoup de choses."
    styled = styler.vocabulary.enrich(raw)
    print(f"  Avant : {raw}")
    print(f"  Après : {styled}")
    
    # Test 3 : Diversité
    print("\n3. DIVERSITÉ (φ-Diversity) :")
    raw = "La Terre orbite autour du Soleil. Cette orbite est elliptique."
    for level in [0.3, 0.618, 0.9]:
        styled = styler.diversity.enrich(raw, level)
        print(f"  φ={level:.3f} : {styled[:100]}")
    
    # Test 4 : Style complet
    print("\n4. STYLE COMPLET :")
    response = "La constante de structure fine vaut environ 1/137."
    user_msg = "Pourquoi cette constante est-elle si importante ?"
    styled = styler.style(response, user_msg)
    print(f"  Avant : {response}")
    print(f"  Après : {styled}")
    
    print("\n✅ Harmonic Style prêt.")
