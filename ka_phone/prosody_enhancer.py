#!/usr/bin/env python3
"""
PROSODY ENHANCER — Intonations naturelles pour la voix TTS
============================================================
Ajoute des intonations naturelles à n'importe quel texte avant synthèse TTS.
Travaille à 3 niveaux :
  1. ENRICHISSEMENT TEXTE — ajout de ponctuation expressive, pauses, emphase
  2. SSML WRAPPER — balises <prosody> pour contrôler pitch/rate/volume
  3. MODULATION AUDIO — variation de pitch et vitesse par segment (post-TTS)

Usage :
    from prosody_enhancer import ProsodyEnhancer
    pe = ProsodyEnhancer()
    enhanced_text = pe.enhance_text("Bonjour, je suis KA.")  # → texte enrichi
    ssml = pe.wrap_ssml(enhanced_text, style="chaleureux")    # → SSML pour Edge-TTS
    # ou directement :
    final_text = pe.enhance_for_tts("Bonjour, je suis KA.", style="chaleureux")
"""

import re
import random
import numpy as np
from typing import Optional, List, Tuple, Dict

# ══════════════════════════════════════════════════════════════════════════
# STYLES PROSODIQUES
# ══════════════════════════════════════════════════════════════════════════

PROSODY_STYLES = {
    "chaleureux": {
        "prefix": "Bon, écoute... ",
        "suffix": " Voilà, j'espère que ça t'aide !",
        "rate": "+3%",        # Légèrement plus rapide
        "pitch": "+5%",       # Légèrement plus aigu (enthousiaste)
        "volume": "loud",
        "pauses_between_sentences": True,
        "emphasis_words": True,
    },
    "calme": {
        "prefix": "",
        "suffix": "",
        "rate": "-5%",        # Plus lent
        "pitch": "-3%",       # Plus grave (apaisant)
        "volume": "medium",
        "pauses_between_sentences": True,
        "emphasis_words": False,
    },
    "enthousiaste": {
        "prefix": "Ah, super question ! ",
        "suffix": " C'est passionnant, non ?",
        "rate": "+8%",
        "pitch": "+12%",
        "volume": "loud",
        "pauses_between_sentences": False,
        "emphasis_words": True,
    },
    "professionnel": {
        "prefix": "",
        "suffix": "",
        "rate": "+2%",
        "pitch": "+0%",
        "volume": "medium",
        "pauses_between_sentences": True,
        "emphasis_words": False,
    },
    "conteur": {
        "prefix": "Écoute bien... ",
        "suffix": " Et voilà l'histoire.",
        "rate": "-3%",
        "pitch": "-2%",
        "volume": "medium",
        "pauses_between_sentences": True,
        "emphasis_words": True,
    },
    "naturel": {
        "prefix": "",
        "suffix": "",
        "rate": "+0%",
        "pitch": "+2%",
        "volume": "medium",
        "pauses_between_sentences": True,
        "emphasis_words": True,
    },
}

# ══════════════════════════════════════════════════════════════════════════
# DÉTECTION DU TYPE DE PHRASE POUR INTONATION
# ══════════════════════════════════════════════════════════════════════════

def detect_sentence_type(text: str) -> str:
    """Détecte le type de phrase pour adapter l'intonation."""
    t = text.strip().lower()
    
    if t.endswith("?"):
        return "question"
    if t.endswith("!"):
        return "exclamation"
    if t.endswith("..."):
        return "hesitation"
    if re.match(r"^(bonjour|salut|coucou|bonsoir|hello|hey)", t):
        return "greeting"
    if re.match(r"^(merci|thanks|super|génial|parfait|cool)", t):
        return "thanks"
    if re.match(r"^(au revoir|bye|adieu|ciao|à plus|bonne nuit)", t):
        return "farewell"
    if re.match(r"^(oui|non|d'accord|ok|bien sûr|absolument)", t):
        return "confirmation"
    if re.match(r"^(désolé|pardon|excuse|je regrette)", t):
        return "apology"
    if re.match(r"^(attention|alerte|urgence|danger|stop)", t):
        return "alert"
    if len(t.split()) <= 3:
        return "short"
    return "statement"


# ══════════════════════════════════════════════════════════════════════════
# PROSODY ENHANCER
# ══════════════════════════════════════════════════════════════════════════

class ProsodyEnhancer:
    """
    Enrichit le texte pour des intonations naturelles.
    Peut être utilisé en mode texte seul ou avec SSML pour Edge-TTS.
    """

    def __init__(self, style: str = "naturel"):
        self.style = style
        self.style_config = PROSODY_STYLES.get(style, PROSODY_STYLES["naturel"])

    def set_style(self, style: str):
        self.style = style
        self.style_config = PROSODY_STYLES.get(style, PROSODY_STYLES["naturel"])

    # ═══ ENRICHISSEMENT TEXTE ═══

    def enhance_text(self, text: str, style: str = None) -> str:
        """
        Enrichit un texte pour lui donner des intonations naturelles.
        Sans SSML — juste du texte amélioré que n'importe quel TTS peut lire.
        """
        if style:
            self.set_style(style)
        cfg = self.style_config

        original = text.strip()
        if not original:
            return original

        # 1. Ajouter préfixe/suffixe stylistiques (30% du temps pour éviter monotonie)
        enhanced = original
        if cfg["prefix"] and random.random() < 0.3:
            enhanced = cfg["prefix"] + enhanced[0].lower() + enhanced[1:]
        if cfg["suffix"] and random.random() < 0.2 and not enhanced.rstrip().endswith(("?", "!", ".")):
            enhanced = enhanced.rstrip(".,;: ") + "."
            enhanced += " " + cfg["suffix"]

        # 2. Ajouter des virgules pour les pauses naturelles dans les longues phrases
        words = enhanced.split()
        if len(words) > 12 and "," not in enhanced and ";" not in enhanced:
            # Insérer une virgule après le 5ème ou 6ème mot
            insert_pos = min(6, len(words) // 2)
            words.insert(insert_pos, ",")
            enhanced = " ".join(words)
            # Nettoyer les doubles espaces/virgules
            enhanced = re.sub(r'\s+,', ',', enhanced)

        # 3. Ajouter des "..." pour les phrases qui semblent incomplètes
        if len(words) <= 4 and not enhanced.rstrip().endswith(("?", "!", ".", "...")):
            if random.random() < 0.15:
                enhanced = enhanced.rstrip() + "..."

        # 4. Emphase : mettre en majuscule le premier mot important
        if cfg["emphasis_words"] and len(words) > 4:
            important_words = [w for w in words[2:] if len(w) > 3 and w.isalpha()]
            if important_words and random.random() < 0.25:
                word_to_emphasize = random.choice(important_words[:3])
                enhanced = enhanced.replace(f" {word_to_emphasize} ", f" {word_to_emphasize.upper()} ", 1)

        return enhanced

    # ═══ SSML WRAPPER ═══

    def wrap_ssml(self, text: str, style: str = None) -> str:
        """
        Enveloppe le texte dans des balises SSML pour Edge-TTS.
        Edge-TTS supporte partiellement le SSML (prosody, break, emphasis).
        """
        if style:
            self.set_style(style)
        cfg = self.style_config

        sentence_type = detect_sentence_type(text)

        # Ajuster le pitch selon le type de phrase
        pitch = cfg["pitch"]
        rate = cfg["rate"]

        if sentence_type == "question":
            pitch = "+15%"  # Montée en fin de phrase
            rate = "+2%"
        elif sentence_type == "exclamation":
            pitch = "+20%"
            rate = "+5%"
        elif sentence_type == "hesitation":
            rate = "-10%"
        elif sentence_type == "greeting":
            pitch = "+8%"
            rate = "+3%"
        elif sentence_type == "thanks":
            pitch = "+5%"
            rate = "+0%"
        elif sentence_type == "farewell":
            pitch = "-3%"
            rate = "-2%"
        elif sentence_type == "apology":
            pitch = "-5%"
            rate = "-5%"
        elif sentence_type == "alert":
            pitch = "+25%"
            rate = "+15%"
            cfg["volume"] = "x-loud"

        # Construire le SSML
        ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="fr-FR">'
        ssml += f'<prosody rate="{rate}" pitch="{pitch}" volume="{cfg["volume"]}">'
        ssml += text
        ssml += '</prosody>'
        ssml += '</speak>'

        return ssml

    def wrap_ssml_multisentence(self, text: str, style: str = None) -> str:
        """
        SSML avec contrôle prosodique par phrase.
        Chaque phrase a sa propre intonation.
        """
        if style:
            self.set_style(style)

        # Découper en phrases
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        if len(sentences) <= 1:
            return self.wrap_ssml(text, style)

        ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="fr-FR">'

        for i, sentence in enumerate(sentences):
            stype = detect_sentence_type(sentence)
            cfg = self.style_config.copy()

            if stype == "question":
                cfg["pitch"] = "+15%"
                cfg["rate"] = "+2%"
            elif stype == "exclamation":
                cfg["pitch"] = "+20%"
                cfg["rate"] = "+5%"

            ssml += f'<prosody rate="{cfg["rate"]}" pitch="{cfg["pitch"]}" volume="{cfg["volume"]}">'
            ssml += sentence.strip()
            ssml += '</prosody>'

            # Pause entre phrases (sauf la dernière)
            if i < len(sentences) - 1:
                ssml += '<break time="400ms"/>'

        ssml += '</speak>'
        return ssml

    # ═══ ENHANCE FOR TTS (combine tout) ═══

    def enhance_for_tts(self, text: str, style: str = "naturel", use_ssml: bool = True) -> str:
        """
        Point d'entrée principal : enrichit le texte pour le TTS.
        Si use_ssml=True, retourne du SSML pour Edge-TTS.
        Sinon, retourne du texte enrichi simple.
        """
        if style:
            self.set_style(style)

        # Étape 1 : Enrichir le texte
        enhanced = self.enhance_text(text, style)

        # Étape 2 : Wrapper SSML si demandé
        if use_ssml:
            return self.wrap_ssml_multisentence(enhanced, style)

        return enhanced

    # ═══ MODULATION AUDIO POST-TTS ═══

    @staticmethod
    def modulate_pitch_along_sentence(audio: np.ndarray, sample_rate: int,
                                       start_pitch_shift: float = 0.0,
                                       end_pitch_shift: float = 0.3) -> np.ndarray:
        """
        Fait varier le pitch progressivement le long de la phrase.
        Utile pour les questions (montée en fin de phrase) ou
        les affirmations (descente).
        
        Args:
            audio: signal audio mono float32 [-1, 1]
            sample_rate: fréquence d'échantillonnage
            start_pitch_shift: décalage au début (en demi-tons)
            end_pitch_shift: décalage à la fin (en demi-tons)
        """
        if len(audio) < 1000 or abs(end_pitch_shift - start_pitch_shift) < 0.01:
            return audio

        n = len(audio)
        # Créer un pitch shift linéaire le long du signal
        pitch_curve = np.linspace(start_pitch_shift, end_pitch_shift, n)

        # Appliquer par segments (plus efficace que sample par sample)
        segment_size = 1024
        result = np.zeros_like(audio)

        for i in range(0, n, segment_size):
            end = min(i + segment_size, n)
            seg = audio[i:end]
            seg_len = end - i

            if seg_len < 128:
                result[i:end] = seg
                continue

            # Pitch shift moyen pour ce segment
            shift = float(np.mean(pitch_curve[i:end]))
            if abs(shift) < 0.001:
                result[i:end] = seg
                continue

            # Rééchantillonnage simple pour le pitch shift
            factor = 2.0 ** (shift / 12.0)
            new_len = int(seg_len / factor)
            indices = np.linspace(0, seg_len - 1, new_len)
            shifted = np.interp(indices, np.arange(seg_len), seg)

            # Ajuster la taille
            if len(shifted) < seg_len:
                shifted = np.pad(shifted, (0, seg_len - len(shifted)), mode='edge')
            else:
                shifted = shifted[:seg_len]

            result[i:end] = shifted

        return result.astype(np.float32)

    @staticmethod
    def add_micro_pauses(audio: np.ndarray, sample_rate: int,
                          pause_every_s: float = 2.5,
                          pause_duration_ms: int = 80) -> np.ndarray:
        """
        Ajoute des micro-pauses (silence) pour un rythme plus naturel.
        Simule la respiration entre les groupes de mots.
        """
        pause_samples = int(pause_duration_ms * sample_rate / 1000)
        segment_samples = int(pause_every_s * sample_rate)

        if len(audio) < segment_samples * 2:
            return audio

        result = []
        pos = 0
        while pos < len(audio):
            end = min(pos + segment_samples, len(audio))
            result.append(audio[pos:end])
            if end < len(audio):
                result.append(np.zeros(pause_samples, dtype=np.float32))
            pos = end

        return np.concatenate(result)


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pe = ProsodyEnhancer(style="naturel")

    tests = [
        "Bonjour, je suis KA, ton double numérique.",
        "Quelle est la capitale du Sénégal ?",
        "Je n'ai pas trouvé de réponse dans ma base.",
        "Merci pour ta question !",
        "Il était une fois, dans le royaume de Kemet, un pharaon qui aimait la sagesse.",
    ]

    print("=" * 60)
    print("PROSODY ENHANCER — Test")
    print("=" * 60)

    for text in tests:
        stype = detect_sentence_type(text)
        print(f"\n[{stype}] {text[:60]}...")
        print(f"  Enhanced:  {pe.enhance_text(text)[:80]}...")
        print(f"  SSML:      {pe.wrap_ssml(text)[:100]}...")
        print(f"  MultiSSML: {pe.wrap_ssml_multisentence(text)[:120]}...")

    print("\n✅ Prosody Enhancer fonctionnel")