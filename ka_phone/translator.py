#!/usr/bin/env python3
"""
TRANSLATOR — Module de traduction EN↔FR pour Harmonic AI
==========================================================
Traductions via dictionnaire bilingue enrichi + patterns grammaticaux.
Zéro dépendance externe, 100% local.

Usage:
  from translator import Translator
  t = Translator()
  t.translate("Hello, how are you?", target="fr")  # → "Bonjour, comment allez-vous ?"
"""

import re
from typing import Optional, Tuple

# ══════════════════════════════════════════════════════════════════════════
# DICTIONNAIRE BILINGUE (EN↔FR)
# ══════════════════════════════════════════════════════════════════════════

EN_FR_DICT = {
    # Salutations et formules
    "hello": "bonjour", "hi": "salut", "goodbye": "au revoir", "bye": "salut",
    "good morning": "bonjour", "good evening": "bonsoir", "good night": "bonne nuit",
    "thank you": "merci", "thanks": "merci", "please": "s'il vous plaît",
    "sorry": "désolé", "excuse me": "excusez-moi", "you're welcome": "de rien",
    "yes": "oui", "no": "non", "maybe": "peut-être", "okay": "d'accord",
    
    # Pronoms
    "i": "je", "you": "tu/vous", "he": "il", "she": "elle", "it": "il/elle",
    "we": "nous", "they": "ils/elles", "me": "me/moi", "him": "le/lui",
    "her": "la/lui", "us": "nous", "them": "les/leur",
    "my": "mon/ma/mes", "your": "ton/ta/tes/votre/vos", "his": "son/sa/ses",
    "her (possessive)": "son/sa/ses", "our": "notre/nos", "their": "leur/leurs",
    
    # Verbes courants
    "to be": "être", "am": "suis", "is": "est", "are": "sommes/êtes/sont",
    "was": "étais/était", "were": "étions/étiez/étaient",
    "to have": "avoir", "have": "ai/as/a/avons/avez/ont",
    "has": "a", "had": "avais/avait/avions/aviez/avaient",
    "to do": "faire", "do": "fais/fait/faisons/faites/font",
    "does": "fait", "to go": "aller", "go": "vais/va/allons/allez/vont",
    "to come": "venir", "come": "viens/vient/venons/venez/viennent",
    "to see": "voir", "see": "vois/voit/voyons/voyez/voient",
    "to know": "savoir/connaître", "know": "sais/sait/savons/savez/savent",
    "to think": "penser", "think": "pense/penses/pensons/pensez/pensent",
    "to want": "vouloir", "want": "veux/veut/voulons/voulez/veulent",
    "to like": "aimer", "like": "aime/aimes/aimons/aimez/aiment",
    "to love": "aimer/adorer", "to hate": "détester",
    "to need": "avoir besoin de", "need": "ai besoin de",
    "to make": "faire/fabriquer", "to take": "prendre",
    "to give": "donner", "to tell": "dire/raconter",
    "to ask": "demander", "to help": "aider",
    "to work": "travailler", "to live": "vivre/habiter",
    "to eat": "manger", "to drink": "boire",
    "to sleep": "dormir", "to read": "lire",
    "to write": "écrire", "to speak": "parler",
    "to learn": "apprendre", "to teach": "enseigner",
    "to understand": "comprendre", "to forget": "oublier",
    "to remember": "se souvenir", "to find": "trouver",
    "to lose": "perdre", "to win": "gagner",
    "to buy": "acheter", "to sell": "vendre",
    "to open": "ouvrir", "to close": "fermer",
    "to start": "commencer", "to finish": "finir/terminer",
    "to stop": "arrêter", "to continue": "continuer",
    "to change": "changer", "to become": "devenir",
    
    # Noms communs
    "world": "monde", "people": "personnes/gens", "man": "homme",
    "woman": "femme", "child": "enfant", "children": "enfants",
    "family": "famille", "friend": "ami", "friends": "amis",
    "house": "maison", "home": "maison/foyer", "city": "ville",
    "country": "pays", "street": "rue", "road": "route",
    "school": "école", "work": "travail", "job": "emploi/métier",
    "money": "argent", "time": "temps", "day": "jour",
    "night": "nuit", "morning": "matin", "evening": "soir",
    "week": "semaine", "month": "mois", "year": "année/an",
    "life": "vie", "death": "mort", "love": "amour",
    "war": "guerre", "peace": "paix", "government": "gouvernement",
    "problem": "problème", "question": "question", "answer": "réponse",
    "idea": "idée", "story": "histoire", "book": "livre",
    "food": "nourriture", "water": "eau", "air": "air",
    "music": "musique", "art": "art", "science": "science",
    "technology": "technologie", "computer": "ordinateur",
    "internet": "internet", "phone": "téléphone", "car": "voiture",
    "language": "langue/langage", "word": "mot", "name": "nom",
    "place": "endroit/lieu", "reason": "raison", "way": "chemin/manière",
    
    # Adjectifs
    "good": "bon/bien", "bad": "mauvais", "big": "grand/gros",
    "small": "petit", "new": "nouveau", "old": "vieux/ancien",
    "young": "jeune", "happy": "heureux", "sad": "triste",
    "angry": "en colère/fâché", "afraid": "effrayé/peur",
    "beautiful": "beau/belle", "ugly": "laid/moche",
    "important": "important", "difficult": "difficile",
    "easy": "facile", "possible": "possible", "impossible": "impossible",
    "true": "vrai", "false": "faux", "right": "correct/droit",
    "wrong": "incorrect/tort", "same": "même", "different": "différent",
    "high": "haut/élevé", "low": "bas", "long": "long",
    "short": "court", "hot": "chaud", "cold": "froid",
    "fast": "rapide", "slow": "lent", "strong": "fort",
    "weak": "faible", "rich": "riche", "poor": "pauvre",
    "free": "libre/gratuit", "full": "plein", "empty": "vide",
    "clean": "propre", "dirty": "sale", "safe": "en sécurité/sûr",
    "dangerous": "dangereux", "real": "réel/vrai", "special": "spécial",
    
    # Adverbes
    "very": "très", "too": "trop/aussi", "always": "toujours",
    "never": "jamais", "often": "souvent", "sometimes": "parfois",
    "here": "ici", "there": "là/là-bas", "everywhere": "partout",
    "now": "maintenant", "today": "aujourd'hui", "tomorrow": "demain",
    "yesterday": "hier", "soon": "bientôt", "later": "plus tard",
    "early": "tôt", "late": "tard", "quickly": "rapidement",
    "slowly": "lentement", "well": "bien", "badly": "mal",
    "together": "ensemble", "alone": "seul", "already": "déjà",
    "also": "aussi/également", "only": "seulement", "really": "vraiment",
    
    # Prépositions et conjonctions
    "in": "dans/en", "on": "sur", "at": "à", "to": "à/vers",
    "from": "de/depuis", "with": "avec", "without": "sans",
    "for": "pour", "about": "à propos de/sur", "between": "entre",
    "under": "sous", "over": "au-dessus de", "before": "avant",
    "after": "après", "during": "pendant", "until": "jusqu'à",
    "and": "et", "or": "ou", "but": "mais", "because": "parce que",
    "if": "si", "when": "quand", "where": "où", "who": "qui",
    "what": "quoi/quel", "why": "pourquoi", "how": "comment",
    "which": "lequel/laquelle", "that": "que/cela",
    
    # Questions
    "how are you": "comment allez-vous",
    "what is your name": "quel est votre nom",
    "where are you from": "d'où venez-vous",
    "how old are you": "quel âge avez-vous",
    "what time is it": "quelle heure est-il",
    "where is": "où est",
    "how much": "combien",
    "how many": "combien de",
    
    # Nombres et couleurs
    "one": "un", "two": "deux", "three": "trois", "four": "quatre",
    "five": "cinq", "six": "six", "seven": "sept", "eight": "huit",
    "nine": "neuf", "ten": "dix", "hundred": "cent", "thousand": "mille",
    "million": "million", "billion": "milliard",
    "first": "premier", "second": "deuxième", "third": "troisième",
    "red": "rouge", "blue": "bleu", "green": "vert", "yellow": "jaune",
    "black": "noir", "white": "blanc", "orange (color)": "orange",
    "purple": "violet/pourpre", "pink": "rose", "brown": "marron/brun",
    "gray": "gris", "grey": "gris",
    
    # Jours, mois
    "monday": "lundi", "tuesday": "mardi", "wednesday": "mercredi",
    "thursday": "jeudi", "friday": "vendredi", "saturday": "samedi",
    "sunday": "dimanche",
    "january": "janvier", "february": "février", "march": "mars",
    "april": "avril", "may": "mai", "june": "juin",
    "july": "juillet", "august": "août", "september": "septembre",
    "october": "octobre", "november": "novembre", "december": "décembre",
    
    # Pays et capitales (EN→FR)
    "france": "France", "spain": "Espagne", "germany": "Allemagne",
    "italy": "Italie", "united kingdom": "Royaume-Uni", "england": "Angleterre",
    "united states": "États-Unis", "america": "Amérique/États-Unis",
    "canada": "Canada", "japan": "Japon", "china": "Chine",
    "india": "Inde", "brazil": "Brésil", "russia": "Russie",
    "australia": "Australie", "mexico": "Mexique",
    "paris": "Paris", "london": "Londres", "berlin": "Berlin",
    "madrid": "Madrid", "rome": "Rome", "tokyo": "Tokyo",
    "washington": "Washington", "ottawa": "Ottawa", "beijing": "Pékin",
    "moscow": "Moscou", "new delhi": "New Delhi",
    
    # Expressions utiles
    "i am": "je suis", "i have": "j'ai",
    "i want": "je veux", "i need": "j'ai besoin de",
    "i think": "je pense", "i know": "je sais",
    "i don't know": "je ne sais pas",
    "i don't understand": "je ne comprends pas",
    "can you help me": "pouvez-vous m'aider",
    "what is this": "qu'est-ce que c'est",
    "where is the bathroom": "où sont les toilettes",
    "i would like": "je voudrais",
}

FR_EN_DICT = {v.split("/")[0]: k for k, v in EN_FR_DICT.items() if "/" not in v and " " not in v}

# ══════════════════════════════════════════════════════════════════════════
# TRANSLATOR
# ══════════════════════════════════════════════════════════════════════════

class Translator:
    """Traducteur EN↔FR basé sur un dictionnaire enrichi."""
    
    def __init__(self):
        self.en_fr = EN_FR_DICT
        self.fr_en = FR_EN_DICT
        self.name = "Dictionary Translator (EN↔FR)"
        self.languages = ["en", "fr"]
    
    def translate(self, text: str, target: str = "fr", source: str = None) -> Tuple[str, float]:
        """
        Traduit un texte.
        
        Args:
            text: Texte à traduire
            target: Langue cible ('fr' ou 'en')
            source: Langue source (auto-détecté si None)
        
        Returns:
            (traduction, confiance)
        """
        if target == "fr":
            return self._translate_to_fr(text)
        elif target == "en":
            return self._translate_to_en(text)
        else:
            return text, 0.0
    
    def _translate_to_fr(self, text: str) -> Tuple[str, float]:
        """Traduit EN → FR."""
        text_lower = text.lower().strip()
        words = text_lower.split()
        translated_words = []
        matched = 0
        total = len(words)
        
        # Chercher d'abord les expressions multi-mots
        i = 0
        while i < len(words):
            matched_phrase = False
            # Essayer les expressions de 4, 3, 2 mots
            for span in [4, 3, 2]:
                if i + span <= len(words):
                    phrase = " ".join(words[i:i+span])
                    if phrase in self.en_fr:
                        translated_words.append(self.en_fr[phrase])
                        matched += span
                        i += span
                        matched_phrase = True
                        break
            if not matched_phrase:
                word = words[i]
                # Enlever la ponctuation
                clean_word = word.strip(".,!?;:'\"")
                if clean_word in self.en_fr:
                    translation = self.en_fr[clean_word]
                    # Garder la ponctuation
                    if word != clean_word:
                        suffix = word[len(clean_word):]
                        translated_words.append(translation + suffix)
                    else:
                        translated_words.append(translation)
                    matched += 1
                else:
                    # Mot inconnu : le passer tel quel
                    translated_words.append(word)
                i += 1
        
        result = " ".join(translated_words)
        confidence = min(0.95, matched / max(total, 1))
        
        # Capitaliser la première lettre
        if result and text[0].isupper():
            result = result[0].upper() + result[1:]
        
        return result, confidence
    
    def _translate_to_en(self, text: str) -> Tuple[str, float]:
        """Traduit FR → EN (dictionnaire inversé)."""
        text_lower = text.lower().strip()
        words = text_lower.split()
        translated_words = []
        matched = 0
        total = len(words)
        
        for word in words:
            clean_word = word.strip(".,!?;:'\"")
            if clean_word in self.fr_en:
                translation = self.fr_en[clean_word]
                if word != clean_word:
                    suffix = word[len(clean_word):]
                    translated_words.append(translation + suffix)
                else:
                    translated_words.append(translation)
                matched += 1
            elif clean_word in self.en_fr.values():
                # Mot français trouvé dans les valeurs du dict
                # Chercher la clé anglaise
                for en, fr in self.en_fr.items():
                    if fr == clean_word or fr.startswith(clean_word):
                        translated_words.append(en)
                        matched += 1
                        break
                else:
                    translated_words.append(word)
            else:
                translated_words.append(word)
        
        result = " ".join(translated_words)
        confidence = min(0.90, matched / max(total, 1))
        
        if result and text[0].isupper():
            result = result[0].upper() + result[1:]
        
        return result, confidence
    
    def detect_language(self, text: str) -> str:
        """Détecte si le texte est en anglais ou français."""
        text_lower = text.lower()
        en_count = 0
        fr_count = 0
        words = text_lower.split()
        
        for word in words:
            clean = word.strip(".,!?;:'\"")
            if clean in self.en_fr:
                en_count += 1
            if clean in self.en_fr.values() or clean in self.fr_en:
                fr_count += 1
        
        return "en" if en_count > fr_count else "fr"
    
    def is_translation_request(self, prompt: str) -> Tuple[bool, str, str]:
        """
        Détecte si un prompt est une demande de traduction.
        Retourne (is_translation, target_lang, text_to_translate).
        """
        p = prompt.lower()
        
        # Patterns de traduction FR→EN
        patterns_fr_to_en = [
            r"traduis?\s+(?:en|vers l[' ]|to)\s*(?:anglais|english)\s*:?\s*(.+)",
            r"translate\s+(?:to|into|in)\s*(?:english|anglais)\s*:?\s*(.+)",
            r"(?:traduis?|translate)\s+(.+?)\s+(?:en|to|vers)\s*(?:anglais|english)",
        ]
        
        # Patterns de traduction EN→FR
        patterns_en_to_fr = [
            r"traduis?\s+(?:en|vers le|vers|to)\s*(?:fran[cç]ais|french)\s*:?\s*(.+)",
            r"translate\s+(?:to|into|in)\s*(?:french|fran[cç]ais)\s*:?\s*(.+)",
            r"(?:traduis?|translate)\s+(.+?)\s+(?:en|to|vers)\s*(?:fran[cç]ais|french)",
        ]
        
        # Pattern générique : "traduis X" sans langue spécifiée
        pattern_generic = r"traduis?\s+(.+?)(?:$|\?)"
        
        for pat in patterns_fr_to_en:
            m = re.search(pat, p)
            if m:
                return True, "en", m.group(1).strip()
        
        for pat in patterns_en_to_fr:
            m = re.search(pat, p)
            if m:
                return True, "fr", m.group(1).strip()
        
        # Si on trouve "traduis" sans direction, détecter la langue source
        m = re.search(pattern_generic, p)
        if m:
            text = m.group(1).strip()
            src = self.detect_language(text)
            target = "fr" if src == "en" else "en"
            return True, target, text
        
        return False, "", ""


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t = Translator()
    
    tests = [
        ("Hello, how are you today?", "fr"),
        ("I love Paris in the morning", "fr"),
        ("Where is the train station?", "fr"),
        ("The big black dog is sleeping", "fr"),
        ("Good morning my friend", "fr"),
        ("Bonjour, comment allez-vous aujourd'hui?", "en"),
        ("J'aime Paris le matin", "en"),
    ]
    
    for text, target in tests:
        result, conf = t.translate(text, target)
        print(f"  {target.upper()}: '{text}' → '{result}' ({conf:.0%})")
    
    print(f"\n  Détection de langue: 'I am happy' → {t.detect_language('I am happy')}")
    print(f"  Détection de langue: 'Je suis heureux' → {t.detect_language('Je suis heureux')}")
    
    # Test détection requête traduction
    test_requests = [
        "traduis en français : Hello world",
        "traduis en anglais : Bonjour le monde",
        "translate to french: I am a student",
        "Comment dit-on 'hello' en français?",
    ]
    for req in test_requests:
        is_trans, target, text = t.is_translation_request(req)
        print(f"  Requête: '{req}' → is_trans={is_trans}, target={target}, text='{text}'")