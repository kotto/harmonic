"""
🌊 WaveStylizer — Stylisation Ondulatoire de Texte
===================================================
Filtre de réécriture qui transforme une réponse technique
en un message chaleureux et élégant.

Stratégie : transformations conservatrices
  1. Règles de phrases (salutations, remerciements, adieux)
  2. Substitutions ciblées de mots techniques (stockage → espace, analyse → vérification)
  3. Emoji de contexte en fin de phrase

Usage :
    from wave_stylizer import get_stylizer, stylize

    styled = stylize("Stockage plein sur le téléphone", style='warm')
    # → "Espace précieux plein sur votre fidèle compagnon. 💫"
"""

import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION PAR STYLE
# ═══════════════════════════════════════════════════════════════════════════════

SENTENCE_REWRITES = {
    'warm': [
        (r'^Bonjour[!\s]', "Hé ! Ravie de vous voir ! "),
        (r'^Salut[!\s]', "Coucou ! 😊 "),
        (r'\bau\s+revoir\b', "À très vite, prenez soin de vous 🌸"),
        (r'\bmerci\b\s+\w+', "Merci infiniment"),
        (r'\bmerci\b', "Merci infiniment"),
        (r'\bdésolé\b', "Oh, toutes mes excuses"),
        (r'\bdesole\b', "Oh, toutes mes excuses"),
    ],
    'balanced': [
        (r'^Bonjour[!\s]', "Bonjour ! "),
        (r'^Salut[!\s]', "Salut ! "),
        (r'\bau\s+revoir\b', "Au revoir"),
    ],
    'elegant': [
        (r'^Bonjour[!\s]', "Je vous salue. "),
        (r'^Salut[!\s]', "Mes respects. "),
        (r'\bau\s+revoir\b', "Je vous souhaite une excellente journée"),
        (r'\bmerci\b\s+\w+', "Je vous remercie"),
        (r'\bmerci\b', "Je vous remercie"),
        (r'\bdésolé\b', "Je vous présente mes excuses"),
        (r'\bdesole\b', "Je vous présente mes excuses"),
    ],
    'poetic': [
        (r'^Bonjour[!\s]', "Que la lumière vous accompagne ! 🌅 "),
        (r'^Salut[!\s]', "Douce rencontre ! 🌸 "),
        (r'\bau\s+revoir\b', "Que les ondes vous portent doucement"),
        (r'\bmerci\b\s+\w+', "Merci, douce étoile ✨"),
        (r'\bmerci\b', "Merci, douce étoile ✨"),
        (r'\bdésolé\b', "Que le silence pardonne"),
        (r'\bdesole\b', "Que le silence pardonne"),
    ],
}

# ═══ Substitutions mot-à-mot (uniquement en word boundary) ═══
WORD_REPLACEMENTS = {
    'warm': {
        r'\bstockage\b': "espace précieux",
        r'\btéléphone\b': "fidèle compagnon",
        r'\btelephone\b': "fidèle compagnon",
        r'\bportable\b': "cher appareil",
        r"\bl[' ]analyse\b": "petit coup d'œil",
        r'\bcompresser\b': "faire de la place",
        r'\bnettoie\b': "fais briller",
        r'\bnettoyer\b': "faire briller",
        r'\bnettoyage\b': "grand nettoyage",
        r'\bcompression\b': "ménage de printemps",
        r'\berreur\b': "petite gêne passagère",
        r'\bdésol[ée]\b': "oh, toutes mes excuses",
        r'\bdesol[ée]\b': "oh, toutes mes excuses",
    },
    'balanced': {
        r'\bstockage\b': "espace précieux",
        r'\btéléphone\b': "appareil",
        r'\btelephone\b': "appareil",
        r'\bportable\b': "appareil",
        r"\bl[' ]analyse\b": "vérification",
        r'\bcompresser\b': "optimiser",
        r'\bnettoie\b': "rafraîchis",
        r'\bnettoyer\b': "rafraîchir",
        r'\bnettoyage\b': "rafraîchissement",
        r'\bcompression\b': "optimisation",
        r'\berreur\b': "petit contretemps",
        r'\bdésol[ée]\b': "toutes mes excuses",
        r'\bdesol[ée]\b': "toutes mes excuses",
    },
    'elegant': {
        r'\bstockage\b': "espace numérique",
        r'\btéléphone\b': "appareil",
        r'\btelephone\b': "appareil",
        r'\bportable\b': "appareil",
        r"\bl[' ]analyse\b": "examen approfondi",
        r'\bcompresser\b': "optimiser avec soin",
        r'\bnettoie\b': "restaure la clarté de",
        r'\bnettoyer\b': "restaurer la clarté",
        r'\bnettoyage\b': "restauration",
        r'\bcompression\b': "optimisation raisonnée",
        r'\berreur\b': "incident mineur",
        r'\bdésol[ée]\b': "je vous présente mes excuses",
        r'\bdesol[ée]\b': "je vous présente mes excuses",
    },
    'poetic': {
        r'\bstockage\b': "horizon de votre mémoire",
        r'\btéléphone\b': "compagnon de route",
        r'\btelephone\b': "compagnon de route",
        r'\bportable\b': "compagnon de voyage",
        r"\bl[' ]analyse\b": "exploration des profondeurs",
        r'\bcompresser\b': "tisser plus serré",
        r'\bnettoie\b': "balaye les ombres de",
        r'\bnettoyer\b': "balayer les ombres",
        r'\bnettoyage\b': "cérémonie de clarté",
        r'\bcompression\b': "danse des atomes numériques",
        r'\berreur\b': "voile de brume",
        r'\bdésol[ée]\b': "que le silence pardonne",
        r'\bdesol[ée]\b': "que le silence pardonne",
    },
}

# ═══ Emojis par contexte détecté ═══
EMOJI_MAP = {
    'greeting': {'warm': '😊', 'balanced': '👋', 'elegant': '🎩', 'poetic': '🌅'},
    'thanks': {'warm': '💖', 'balanced': '🙏', 'elegant': '♡', 'poetic': '✨'},
    'goodbye': {'warm': '🌸', 'balanced': '👋', 'elegant': '🎩', 'poetic': '🌊'},
    'success': {'warm': '🎉', 'balanced': '✅', 'elegant': '✦', 'poetic': '✨'},
    'error': {'warm': '💛', 'balanced': '⚠️', 'elegant': '◈', 'poetic': '🌫️'},
    'thinking': {'warm': '💭', 'balanced': '💭', 'elegant': '◇', 'poetic': '🌙'},
    'action': {'warm': '✨', 'balanced': '→', 'elegant': '→', 'poetic': '🌸'},
}

CONTEXT_PATTERNS = [
    ('greeting', [r'^Bonjour', r'^Salut', r'^Coucou', r'^Hello']),
    ('thanks', [r'\bmerci\b', r'\bremercie\b']),
    ('goodbye', [r'\bau revoir\b', r'\bbye\b', r'\bà bientôt\b', r'\bà plus\b']),
    ('success', [r'\bvoilà\b', r'\bterminé\b', r'\bfait\b', r'\bprêt\b',
                 r'\bsuper\b', r'\bgénial\b', r'\bparfait\b']),
    ('error', [r'\bdésol\b', r'\bdesol\b', r'\b(?:désole|desole)\b',
               r'\berreur\b', r'\bproblème\b']),
    ('thinking', [r'\bje réfléchis\b', r'\blaissez-moi\b', r'\bun instant\b']),
]


def _detect_context(text: str) -> str:
    """Détecte le contexte émotionnel dominant."""
    text_lower = text.lower()
    for ctx, patterns in CONTEXT_PATTERNS:
        for p in patterns:
            if re.search(p, text_lower):
                return ctx
    return 'thinking'  # défaut


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE STYLIZER
# ═══════════════════════════════════════════════════════════════════════════════

class WaveStylizer:
    """
    Filtre de réécriture ondulatoire conservateur.
    """

    def __init__(self):
        log.info(f"🌊 WaveStylizer actif ({len(WORD_REPLACEMENTS)} styles)")

    def render(self, text: str, style: str = 'balanced',
               context: str = None) -> str:
        """
        Stylise un texte selon le style choisi.

        Args:
            text: Texte brut à styliser
            style: 'warm', 'balanced', 'elegant', 'poetic', 'minimal'
            context: Contexte émotionnel (auto-détecté si None)

        Returns:
            Texte stylisé
        """
        if not text or not text.strip():
            return text

        if style == 'minimal':
            return text.strip()

        # 1. Appliquer les réécritures de phrases
        result = self._apply_sentence_rewrites(text, style)

        # 2. Appliquer les substitutions mot-à-mot
        result = self._apply_word_replacement(result, style)

        # 3. Nettoyer
        result = re.sub(r'\s+', ' ', result).strip()
        result = re.sub(r'\s([?.!,;:\'])', r'\1', result)
        result = re.sub(r'\.\.+', '.', result)
        result = re.sub(r'!!+', '!', result)
        result = re.sub(r'\?\?+', '?', result)
        # Contractions
        result = re.sub(r'\ble\s+(appareil|analyse|espace)\b', r"l'\1", result)
        result = re.sub(r'\bde\s+(appareil|analyse|espace)\b', r"d'\1", result)
        result = re.sub(r"\bl[\s']+analyse\b", "l'analyse", result)

        # 4. Ajouter emoji
        if context is None:
            context = _detect_context(result)
        result = self._add_emoji(result, style, context)

        return result

    def _apply_sentence_rewrites(self, text: str, style: str) -> str:
        """Applique les réécritures de phrases complètes."""
        rewrites = SENTENCE_REWRITES.get(style, [])
        for pattern, replacement in rewrites:
            try:
                if callable(replacement):
                    result = re.sub(pattern, replacement, text, count=1,
                                    flags=re.IGNORECASE | re.DOTALL)
                else:
                    result = re.sub(pattern, replacement, text, count=1,
                                    flags=re.IGNORECASE | re.DOTALL)
                if result != text:
                    return result
            except re.error:
                pass
        return text

    def _apply_word_replacement(self, text: str, style: str) -> str:
        """Remplace les mots techniques par équivalents stylisés."""
        replacements = WORD_REPLACEMENTS.get(style, {})
        result = text
        for pattern_str, replacement in replacements.items():
            try:
                result = re.sub(pattern_str, replacement, result,
                               count=1, flags=re.IGNORECASE)
            except re.error:
                pass
        return result

    def _add_emoji(self, text: str, style: str, context: str) -> str:
        """Ajoute une emoji de contexte si pas déjà présente."""
        emoji_map = EMOJI_MAP.get(context, {})
        emoji = emoji_map.get(style, '')

        if not emoji:
            return text

        # Vérifier si une emoji existe déjà
        if any(c in text[-10:] for c in
               ['\U0001F600', '\U0001F60A', '\U0001F44B', '\U0001F389',
                '\U0001F31F', '\U0001F338', '\U0001F30A', '\U0001F49B',
                '\u2728', '\u2714', '\u25B6', '\u2661', '\U0001F48E',
                '\U0001F30D', '\U0001F4AD', '\u25C6', '\u2726']):
            return text

        # Ajouter l'emoji
        text = text.rstrip()
        if not text[-1] in ('.', '!', '?'):
            text += '.'
        return f"{text} {emoji}"

    def stats(self) -> dict:
        return {
            'styles': list(WORD_REPLACEMENTS.keys()),
            'word_rules': sum(len(v) for v in WORD_REPLACEMENTS.values()),
            'sentence_rules': sum(len(v) for v in SENTENCE_REWRITES.values()),
        }


# ═══ Singleton ═══
_stylizer = None


def get_stylizer():
    global _stylizer
    if _stylizer is None:
        _stylizer = WaveStylizer()
    return _stylizer


def stylize(text: str, style: str = 'balanced') -> str:
    """Fonction d'accès rapide."""
    return get_stylizer().render(text, style=style)