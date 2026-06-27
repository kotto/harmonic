#!/usr/bin/env python3
"""
LITERARY STYLER — Post-processeur stylistique pour l'écriture créative
=========================================================================
Prend la sortie brute du HarmonicNarrativeComposer et la raffine
pour atteindre une qualité littéraire proche de celle des LLMs.

4 couches de raffinement :
  1. LISSAGE PROSODIQUE — variation de longueur de phrase, rythme
  2. ENRICHISSEMENT LEXICAL — remplacement de mots communs
  3. FIGURES RHÉTORIQUES — anaphores, allitérations, métaphores
  4. COHÉSION NARRATIVE — transitions fluides, rappels thématiques

Usage :
  from literary_styler import LiteraryStyler
  ls = LiteraryStyler()
  refined = ls.refine(raw_composed_text, style="lyrique")
"""

import re, random, textwrap
from typing import List, Dict, Optional, Tuple

# ══════════════════════════════════════════════════════════════════════════
# 1. PROSODY — Variation rythmique
# ══════════════════════════════════════════════════════════════════════════

SENTENCE_STARTERS = {
    "observation": [
        "Je vois", "Voici", "Regarde", "Contemple", "Il y a", "C'est",
        "Là-bas", "Au loin", "Devant moi", "Soudain",
    ],
    "reflection": [
        "Peut-être", "Sans doute", "Il me semble", "Je crois", "Car",
        "Et pourtant", "Cependant", "N'est-ce pas", "En vérité",
    ],
    "action": [
        "Alors", "Puis", "Soudain", "Et voilà que", "C'est ainsi que",
        "À cet instant", "D'un coup", "Sans attendre",
    ],
    "conclusion": [
        "Ainsi", "Voilà pourquoi", "C'est pour cela que", "En fin de compte",
        "Et c'est ainsi", "Finalement", "Tout compte fait",
    ],
    "emotion": [
        "Ô", "Hélas", "Quelle merveille", "Quel mystère", "Doucement",
        "Violemment", "Avec tendresse", "Dans un souffle",
    ],
}

RHYTHM_PATTERNS = [
    [15, 8, 12, 5, 20, 8, 10],     # Long-short-long-short variation
    [10, 10, 10, 18, 25, 6],         # Steady build to long then short
    [8, 12, 5, 15, 22, 8, 12, 6],   # Wave-like rhythm
    [20, 5, 15, 8, 25, 6, 10],      # Dramatic variation
]

# ══════════════════════════════════════════════════════════════════════════
# 2. LEXICAL ENRICHMENT — Word substitution
# ══════════════════════════════════════════════════════════════════════════

LEXICAL_ELEVATIONS = {
    # Verbes communs → plus expressifs
    "est": ["demeure", "reste", "se tient", "existe", "brille comme"],
    "était": ["demeurait", "restait", "se tenait", "existait", "brillait comme"],
    "sont": ["demeurent", "restent", "se tiennent", "existent", "brillent comme"],
    "il y a": ["l'on trouve", "l'on découvre", "se dresse", "réside"],
    "a": ["possède", "détient", "porte en lui", "abrite"],
    "fait": ["accomplit", "réalise", "forge", "façonne"],
    "dit": ["murmure", "déclare", "proclame", "chuchote"],
    "va": ["s'avance", "se dirige", "s'élance", "progresse"],
    "vient": ["surgit", "apparaît", "émerge", "s'approche"],
    
    # Adjectifs communs → plus évocateurs
    "grand": ["immense", "vaste", "majestueux", "colossal", "infini"],
    "beau": ["splendide", "magnifique", "resplendissant", "enchanteur"],
    "vieux": ["ancien", "millénaire", "séculaire", "ancestral"],
    "petit": ["minuscule", "infime", "ténu", "fragile"],
    "fort": ["puissant", "imposant", "redoutable", "indomptable"],
    "doux": ["suave", "velouté", "caressant", "mélodieux"],
    "sombre": ["ténébreux", "obscur", "crépusculaire", "nocturne"],
    "brillant": ["éclatant", "étincelant", "resplendissant", "lumineux"],
}

# ══════════════════════════════════════════════════════════════════════════
# 3. RHETORICAL DEVICES
# ══════════════════════════════════════════════════════════════════════════

def anaphora(subject: str, count: int = 3) -> str:
    """Create an anaphora (repeated beginning)."""
    verbs = ["porte", "garde", "chante", "raconte", "sait", "connaît", "cache", "révèle"]
    targets = ['le secret des ages', 'la memoire du monde', 'le souffle des ancetres', 'la lumiere des origines', 'le silence des siecles', 'la promesse de l aube', 'le chant du possible']
    phrases = [f"{subject} {random.choice(verbs)} {random.choice(targets)}" for _ in range(count)]
    return ",\n".join(phrases) + "."

def metaphor_chain(theme: str, length: int = 3) -> str:
    """Create a chain of related metaphors."""
    like_options = ["le Nil qui jamais ne s arrete", "le vent qui ignore les frontieres", 
                    "le baobab qui plonge ses racines dans le temps", "le soleil qui renait chaque matin"]
    est_options = ["un fleuve", "un souffle", "une racine", "une flamme", "une etoile"]
    qui_options = ["traverse les ages", "defie l oubli", "eclaire la nuit", "nourrit l espoir"]
    return f"Comme {random.choice(like_options)}, {theme} est {random.choice(est_options)} qui {random.choice(qui_options)}."

def alliteration(subject: str) -> str:
    """Create alliterative phrase."""
    letter = subject[0].lower() if subject else 'l'
    adjectives = [w for w in ["lumineux", "lointain", "libre", "lent", "léger", "large", "limpide", "loyal"] if w.startswith(letter)]
    nouns = [w for w in ["lueur", "légende", "liberté", "lumière", "lien", "langage"] if w.startswith(letter)]
    if adjectives and nouns:
        return f"{random.choice(adjectives)} {random.choice(nouns)}"
    return f"{subject} lumineux"

# ══════════════════════════════════════════════════════════════════════════
# 4. TRANSITION ENHANCER
# ══════════════════════════════════════════════════════════════════════════

POETIC_TRANSITIONS = [
    "\n\nSous le même ciel,\n\n",
    "\n\nLe temps suspendu,\n\n",
    "\n\nEt dans ce silence,\n\n",
    "\n\nLes pierres se souviennent :\n\n",
    "\n\nÉcoute à présent :\n\n",
    "\n\nMais voici que\n\n",
    "\n\nAlors, comme une vague,\n\n",
    "\n\nPuis, lentement,\n\n",
    "\n\nLà, dans cette immensité,\n\n",
    "\n\nC'est ici que tout bascule :\n\n",
    "\n\nRegarde :\n\n",
    "\n\nEntre deux souffles,\n\n",
]


class LiteraryStyler:
    """
    Post-processeur de qualité littéraire.
    Raffine le texte brut pour atteindre une qualité proche des LLMs.
    """

    def __init__(self):
        self.elevations = LEXICAL_ELEVATIONS
        self.starters = SENTENCE_STARTERS
        self.rhythms = RHYTHM_PATTERNS
        self.transitions = POETIC_TRANSITIONS

    def refine(self, text: str, style: str = "lyrique", sujet: str = "") -> str:
        """
        Raffine un texte brut en appliquant 4 couches de qualité littéraire.
        
        Args:
            text: Texte brut du HarmonicNarrativeComposer
            style: "lyrique", "épique", "intimiste", "oratoire", "méditatif"
            sujet: Thème central pour la cohérence métaphorique
            
        Returns:
            Texte raffiné avec qualité littéraire
        """
        if not text or len(text) < 20:
            return text

        # Step 1: Clean raw text
        text = self._clean_text(text)

        # Step 2: Apply prosodic smoothing
        text = self._prosodic_smoothing(text)

        # Step 3: Lexical enrichment
        text = self._lexical_enrich(text)

        # Step 4: Add rhetorical devices for longer texts
        if len(text) > 100:
            text = self._add_rhetorical_devices(text, sujet)

        # Step 5: Opening hook
        text = self._add_opening_hook(text, sujet, style)

        # Step 6: Closing cadence
        text = self._add_closing_cadence(text, style)

        return text

    def _clean_text(self, text: str) -> str:
        """Clean raw composed text."""
        # Remove excessive blank lines
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        # Remove trailing punctuation duplicates
        text = re.sub(r'([.!?])\1+', r'\1', text)
        # Ensure spacing
        text = re.sub(r' +', ' ', text)
        return text.strip()

    def _prosodic_smoothing(self, text: str) -> str:
        """Apply rhythmic variation to create a natural flow."""
        sentences = re.split(r'(?<=[.!?\n])\s*', text)
        if len(sentences) < 3:
            return text

        # Select a rhythm pattern
        pattern = random.choice(self.rhythms)

        result = []
        for i, sent in enumerate(sentences):
            sent = sent.strip()
            if not sent:
                result.append("")
                continue

            # Skip very short sentences
            if len(sent) < 5:
                result.append(sent)
                continue

            # Select starter based on position
            starter_type = "observation"
            position_ratio = i / max(len(sentences), 1)
            if position_ratio > 0.7:
                starter_type = "conclusion"
            elif position_ratio > 0.5:
                starter_type = "action"
            elif position_ratio > 0.3:
                starter_type = "reflection"

            # Sometimes add a sentence starter (30% probability)
            if random.random() < 0.3 and sent[0].isalpha():
                starter = random.choice(self.starters.get(starter_type, self.starters["observation"]))
                if not any(sent.lower().startswith(s.lower()[:4]) for s in self.starters.get(starter_type, [])):
                    sent = f"{starter}, {sent[0].lower()}{sent[1:]}" if sent[0].isupper() else sent

            result.append(sent)

        return "\n".join(result)

    def _lexical_enrich(self, text: str) -> str:
        """Replace common words with more expressive alternatives."""
        words = text.split()
        result = []
        for i, word in enumerate(words):
            # Only replace occasionally (30% chance) to keep natural feel
            word_lower = word.lower().rstrip(".,;:!?-")
            if word_lower in self.elevations and random.random() < 0.3:
                replacement = random.choice(self.elevations[word_lower])
                # Preserve capitalization
                if word[0].isupper():
                    replacement = replacement[0].upper() + replacement[1:]
                # Preserve trailing punctuation
                suffix = word[len(word.rstrip(".,;:!?-")):]
                result.append(replacement + suffix)
            else:
                result.append(word)
        return " ".join(result)

    def _add_rhetorical_devices(self, text: str, sujet: str) -> str:
        """Insert rhetorical devices for longer texts."""
        if not sujet:
            # Try to extract subject from text
            words = re.findall(r'\b[A-ZÀ-Ú][a-zà-ú]{3,}\b', text[:200])
            sujet = random.choice(words) if words else "le monde"

        # Add one rhetorical device (randomly chosen)
        device_type = random.choice(["metaphor", "anaphora", "alliteration"])

        if device_type == "metaphor":
            insertion = "\n" + metaphor_chain(sujet) + "\n"
        elif device_type == "anaphora" and len(sujet) > 2:
            insertion = "\n" + anaphora(sujet, 3) + "\n"
        else:
            insertion = f"\n{alliteration(sujet).capitalize()}.\n"

        # Insert in the second half of the text
        sentences = text.split("\n")
        if len(sentences) >= 4:
            insert_pos = random.randint(len(sentences)//2, len(sentences)-1)
            sentences.insert(insert_pos, insertion)
            text = "\n".join(sentences)

        return text

    def _add_opening_hook(self, text: str, sujet: str, style: str) -> str:
        """Add an engaging opening hook."""
        hooks = {
            "lyrique": [
                f"Laisse-moi te parler de {sujet}.",
                f"Connais-tu {sujet} ? Écoute.",
            ],
            "epique": [
                f"Je vais te raconter l'histoire de {sujet}.",
                f"Que les siècles se souviennent de {sujet}.",
            ],
            "intimiste": [
                f"J'ai gardé ce secret sur {sujet}.",
                f"Personne ne t'a jamais dit la vérité sur {sujet}.",
            ],
            "meditatif": [
                f"Asseyons-nous et contemplons {sujet}.",
                f"Dans le silence, {sujet} se révèle.",
            ],
        }
        hooks_for_style = hooks.get(style, hooks["lyrique"])
        hook = random.choice(hooks_for_style) if sujet else ""

        if hook and len(text) > 50:
            return f"{hook}\n\n{text}"
        return text

    def _add_closing_cadence(self, text: str, style: str) -> str:
        """Add a resonant closing sentence."""
        cadences = {
            "lyrique": [
                "\n\nEt le silence, après ces mots, était plus éloquent que tous les discours.",
                "\n\nAinsi va le monde, entre mémoire et promesse.",
            ],
            "epique": [
                "\n\nVoilà l'histoire que les griots chanteront pour les siècles à venir.",
                "\n\nQue les générations futures s'en souviennent.",
            ],
            "intimiste": [
                "\n\nC'est tout. Le reste appartient au silence.",
                "\n\nJe te confie ces mots comme on confie une clé.",
            ],
            "meditatif": [
                "\n\nEt dans ce silence, peut-être as-tu entendu ce que je n'ai pas su dire.",
                "\n\nLa réponse n'est pas dans les mots, mais dans l'écho qu'ils laissent.",
            ],
        }
        cads = cadences.get(style, cadences["lyrique"])
        if random.random() < 0.6 and len(text) > 80:
            return text + random.choice(cads)
        return text


# ══════════════════════════════════════════════════════════════════════════
# INTEGRATION WITH NARRATIVE COMPOSER
# ══════════════════════════════════════════════════════════════════════════

def compose_with_style(prompt: str, arc_type: str = "auto", style: str = "lyrique", length: int = 500) -> Dict:
    """
    One-shot function: compose narrative arc + apply literary style.
    Combines HarmonicNarrativeComposer + LiteraryStyler.
    """
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from harmonic_narrative_composer import HarmonicNarrativeComposer

    composer = HarmonicNarrativeComposer()
    result = composer.compose(prompt, arc_type=arc_type, max_length=length)

    styler = LiteraryStyler()
    sujet = result.get("sujet", "")
    result["raw_text"] = result["text"]
    result["text"] = styler.refine(result["text"], style=style, sujet=sujet)
    result["style"] = style

    return result


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ls = LiteraryStyler()

    raw_poem = """Le paysage s'étendait, vaste comme le Nil.
Au premier plan, le vent murmure à travers les feuilles dorées.
Plus loin, les pyramides percent le ciel de leur géométrie sacrée.
Le ciel, lui, le temps effeuille les saisons une à une.

Sur le Nil, je médite.
le silence est le langage que parlent les âmes profondes.
la mer soupire contre les falaises éternelles.
le savoir est une lampe dans la nuit de l'ignorance.

Ô le Nil, toi qui le vent murmure à travers les feuilles dorées !
Tu les pyramides percent le ciel de leur géométrie sacrée,
et le savoir est une lampe dans la nuit de l'ignorance.
Gloire à le Nil, l'espoir est la dernière étoile qui refuse de s'éteindre."""

    print("RAW TEXT:")
    print(raw_poem[:200])
    print("\n" + "=" * 50)
    print("REFINED TEXT (lyrique):")
    refined = ls.refine(raw_poem, style="lyrique", sujet="le Nil")
    print(refined[:400])
    print(f"\nLength: {len(refined)} chars (was {len(raw_poem)})")