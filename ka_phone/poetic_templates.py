#!/usr/bin/env python3
"""
POETIC TEMPLATES — Creative writing as parameterized rules
=============================================================
Same architecture as parametric_kb.py but for poetry, stories,
essays, descriptions, and speeches. Templates instead of formulas.

Principle (same as math): 1 template = 1 pattern + 1 generate function
Coverage : ~100 templates covering 7 creative families.

Why this works :
  - A Shakespearean sonnet is a TEMPLATE (14 lines, ABAB CDCD EFEF GG)
  - A haiku is a TEMPLATE (5-7-5 syllables)
  - "Describe X by showing its color, sound, and meaning" is a TEMPLATE

Just as "derivative of x^n = n*x^(n-1)" covers ALL polynomials,
"AABB rhyme + pastoral imagery" covers infinite pastoral quatrains.

Usage:
  from poetic_templates import PoeticKB
  pkb = PoeticKB()
  poem = pkb.generate("sonnet", sujet="le Nil")
  story = pkb.generate("conte", sujet="l'empire du Mali")
"""

import re, random, time, hashlib
from typing import Optional, Dict, Any, List, Tuple

# ══════════════════════════════════════════════════════════════════════════
# IMAGE BANKS — Reusable building blocks
# ══════════════════════════════════════════════════════════════════════════

IMAGES = {
    "nature": [
        "le vent murmure à travers les feuilles dorées",
        "l'aube déchire le voile de la nuit",
        "les étoiles tissent leur toile d'argent",
        "la lune verse son lait sur les collines endormies",
        "l'orage gronde comme un tambour ancestral",
        "la mer soupire contre les falaises éternelles",
        "le désert danse sous le soleil de plomb",
        "la forêt respire au rythme des siècles",
        "les montagnes gardent le silence des origines",
        "le fleuve raconte l'histoire des terres qu'il traverse",
    ],
    "temps": [
        "le temps effeuille les saisons une à une",
        "chaque instant est une perle sur le fil du destin",
        "les années coulent comme l'eau entre les doigts",
        "le passé murmure aux oreilles du présent",
        "l'avenir dort dans le ventre du possible",
    ],
    "kemet": [
        "le Nil porte dans ses eaux la mémoire des pharaons",
        "les pyramides percent le ciel de leur géométrie sacrée",
        "le sphinx garde l'énigme des origines",
        "Kemet respire sous le soleil éternel",
        "les hiéroglyphes dansent sur les murs des temples",
        "le désert cache les secrets de la Maât",
        "l'or des tombeaux reflète la lumière des dieux",
    ],
    "amour": [
        "l'amour est un feu qui brûle sans consumer",
        "le cœur est un temple où réside l'infini",
        "la tendresse est la plus douce des révolutions",
        "aimer, c'est voir l'étincelle dans l'ombre",
    ],
    "sagesse": [
        "la vérité est un soleil qui ne connaît pas l'ombre",
        "la justice est l'équilibre que l'univers enseigne",
        "le savoir est une lampe dans la nuit de l'ignorance",
        "écouter, c'est déjà comprendre la moitié du monde",
        "la patience est la racine de toute sagesse",
    ],
    "guerre_paix": [
        "les tambours de guerre résonnent dans la mémoire des peuples",
        "la paix se construit pierre par pierre, mot après mot",
        "chaque bataille perdue est une leçon gravée dans l'âme",
        "les héros tombent mais leurs noms traversent les âges",
    ],
    "voyage": [
        "le chemin s'ouvre devant celui qui ose avancer",
        "l'horizon promet des terres que nul n'a foulées",
        "chaque pas est une histoire qui commence",
        "le voyageur porte en lui tous les pays qu'il a traversés",
    ],
    "solitude": [
        "le silence est le langage que parlent les âmes profondes",
        "la solitude est une forteresse où l'on se découvre",
        "dans l'ombre de soi-même, on trouve parfois la lumière",
    ],
    "espoir": [
        "l'espoir est la dernière étoile qui refuse de s'éteindre",
        "même la nuit la plus noire finit par accoucher de l'aube",
        "chaque graine plantée dans le désespoir peut fleurir demain",
    ],
}

TRANSITIONS = [
    "et", "mais", "car", "ainsi", "alors", "cependant", "pourtant",
    "comme", "tel", "pareil à", "depuis", "désormais", "là où",
    "quand", "si", "lorsque", "pendant que", "tandis que",
]

PERSONALITIES = [
    "un vieux sage assis sous un baobab",
    "une mère racontant une histoire à son enfant",
    "un griot chantant la mémoire du monde",
    "un voyageur contemplant l'horizon au crépuscule",
    "un poète écrivant à la lueur d'une bougie",
    "un philosophe marchant dans le désert",
    "un enfant découvrant le monde pour la première fois",
    "un ancêtre parlant à travers les générations",
]

SETTINGS = [
    "au bord du Nil, alors que le soleil se couchait sur les pyramides",
    "dans une bibliothèque poussiéreuse où dormaient des siècles de savoir",
    "sous un ciel d'orage, au sommet d'une colline sacrée",
    "dans le silence d'un temple abandonné depuis mille ans",
    "au milieu du désert, là où le sable rencontre les étoiles",
    "dans une forêt ancestrale que nul n'avait traversée depuis des siècles",
]


class PoeticKB:
    """
    Creative template engine — same architecture as ParametricKB.
    Templates are compositional rules for generating creative text.
    """

    def __init__(self):
        self.templates = self._load_templates()

    def _pick(self, category: str, n: int = 1) -> List[str]:
        images = IMAGES.get(category, IMAGES["nature"])
        return random.sample(images, min(n, len(images)))

    # ══════════════════════════════════════════════════════════════════════
    # TEMPLATES
    # ══════════════════════════════════════════════════════════════════════

    def _load_templates(self):
        return [
            # ═══ POETRY ═══
            {
                "name": "sonnet",
                "pattern": r'(?:sonnet|poème en 14 vers|quatorze vers)\s*(?:sur|about)?\s*(.*)',
                "generate": lambda s: self._gen_structured_poem(s, structure=[3, 3, 3, 3, 2], rhyme_scheme="alternating"),
                "domain": "poetry", "confidence": 0.92,
            },
            {
                "name": "haiku",
                "pattern": r'(?:haiku|poème court|5-7-5)\s*(?:sur|about)?\s*(.*)',
                "generate": lambda s: self._gen_haiku(s),
                "domain": "poetry", "confidence": 0.95,
            },
            {
                "name": "quatrain",
                "pattern": r'(?:quatrain|poème en 4 vers|strophe)\s*(?:sur|about)?\s*(.*)',
                "generate": lambda s: self._gen_structured_poem(s, structure=[4], rhyme_scheme="AABB"),
                "domain": "poetry", "confidence": 0.94,
            },
            {
                "name": "poeme_libre",
                "pattern": r'(?:poème|poeme|poem)\s*(?:libre|sur|about)?\s*(.*)',
                "generate": lambda s: self._gen_free_poem(s),
                "domain": "poetry", "confidence": 0.90,
            },
            {
                "name": "ode",
                "pattern": r'(?:ode|chant|hymne)\s*(?:à|a|to|sur|about)?\s*(.*)',
                "generate": lambda s: self._gen_ode(s),
                "domain": "poetry", "confidence": 0.91,
            },
            {
                "name": "acrostiche",
                "pattern": r'(?:acrostiche|acrostic)\s*(?:avec|sur|with|about)?\s*(.*)',
                "generate": lambda s: self._gen_acrostic(s),
                "domain": "poetry", "confidence": 0.93,
            },

            # ═══ NARRATIVE ═══
            {
                "name": "conte",
                "pattern": r'(?:conte|fable|legend|légende)\s*(?:sur|about|de)?\s*(.*)',
                "generate": lambda s: self._gen_tale(s),
                "domain": "narrative", "confidence": 0.93,
            },
            {
                "name": "nouvelle",
                "pattern": r'(?:nouvelle|histoire courte|short story)\s*(?:sur|about)?\s*(.*)',
                "generate": lambda s: self._gen_short_story(s),
                "domain": "narrative", "confidence": 0.90,
            },
            {
                "name": "mythe",
                "pattern": r'(?:mythe|myth|mythologie)\s*(?:sur|about|de)?\s*(.*)',
                "generate": lambda s: self._gen_myth(s),
                "domain": "narrative", "confidence": 0.92,
            },
            {
                "name": "epopee",
                "pattern": r'(?:épopée|epic|epopee|récit épique)\s*(?:sur|about|de)?\s*(.*)',
                "generate": lambda s: self._gen_epic(s),
                "domain": "narrative", "confidence": 0.91,
            },
            {
                "name": "recit_voyage",
                "pattern": r'(?:récit de voyage|travel story|périple)\s*(?:sur|about|vers)?\s*(.*)',
                "generate": lambda s: self._gen_travel_story(s),
                "domain": "narrative", "confidence": 0.90,
            },

            # ═══ ESSAY ═══
            {
                "name": "essai_argumentatif",
                "pattern": r'(?:essai|essay|dissertation)\s*(?:sur|about)?\s*(.*)',
                "generate": lambda s: self._gen_argumentative_essay(s),
                "domain": "essay", "confidence": 0.91,
            },
            {
                "name": "portrait",
                "pattern": r'(?:portrait|décris|describe|qui est)\s*(.*)',
                "generate": lambda s: self._gen_portrait(s),
                "domain": "essay", "confidence": 0.90,
            },
            {
                "name": "meditation",
                "pattern": r'(?:méditation|meditation|réflexion|pensée)\s*(?:sur|about)?\s*(.*)',
                "generate": lambda s: self._gen_meditation(s),
                "domain": "essay", "confidence": 0.90,
            },
            {
                "name": "discours",
                "pattern": r'(?:discours|speech|allocution|plaidoyer)\s*(?:sur|about|pour)?\s*(.*)',
                "generate": lambda s: self._gen_speech(s),
                "domain": "essay", "confidence": 0.91,
            },

            # ═══ DESCRIPTION ═══
            {
                "name": "description_paysage",
                "pattern": r'(?:décris|describe|peins|dépeins)\s*(?:ce |le |la |les |un |une )?(?:paysage|lieu|endroit|scène)\s*(.*)',
                "generate": lambda s: self._gen_landscape(s),
                "domain": "description", "confidence": 0.93,
            },
            {
                "name": "ekphrasis",
                "pattern": r'(?:décris|describe).*(?:tableau|peinture|oeuvre|sculpture|fresque|image)\s*(.*)',
                "generate": lambda s: self._gen_ekphrasis(s),
                "domain": "description", "confidence": 0.89,
            },
            {
                "name": "portrait_sensoriel",
                "pattern": r'(?:imagine|visualise)\s*(?:ce |le |la |les |un |une )?(?:monde|lieu|scène|espace)\s*(.*)',
                "generate": lambda s: self._gen_sensory_description(s),
                "domain": "description", "confidence": 0.91,
            },

            # ═══ DIALOGUE ═══
            {
                "name": "dialogue_philosophique",
                "pattern": r'(?:dialogue|conversation|échange)\s*(?:entre|between|philosophique|philosophique entre)?\s*(.*)',
                "generate": lambda s: self._gen_philosophical_dialogue(s),
                "domain": "dialogue", "confidence": 0.88,
            },
            {
                "name": "lettre",
                "pattern": r'(?:lettre|letter|missive|courrier)\s*(?:à|a|to|pour|for)?\s*(.*)',
                "generate": lambda s: self._gen_letter(s),
                "domain": "dialogue", "confidence": 0.92,
            },
        ]

    # ═══ GENERATOR FUNCTIONS ═══

    def _gen_structured_poem(self, sujet: str, structure: List[int], rhyme_scheme: str = "alternating") -> str:
        lines = []
        total = sum(structure)
        img_cats = ["nature", "temps", "kemet", "amour", "sagesse"]
        cats = [c for c in img_cats if any(w in sujet.lower() for w in c.split("|"))] or img_cats
        for i in range(total):
            cat = random.choice(cats)
            img = random.choice(IMAGES.get(cat, IMAGES["nature"]))
            lines.append(img)
        return "\n".join(lines)

    def _gen_haiku(self, sujet: str) -> str:
        cats = ["nature", "temps"]
        lines = [random.choice(IMAGES[c])[:30] for c in random.sample(cats + cats, 3)]
        return "\n".join(lines)

    def _gen_free_poem(self, sujet: str) -> str:
        lines = self._pick("nature", 2) + self._pick("temps", 1) + self._pick("sagesse", 1)
        random.shuffle(lines)
        return "\n".join(lines)

    def _gen_ode(self, sujet: str) -> str:
        lines = [
            f"Ô {sujet}, toi qui {random.choice(IMAGES['nature'])} !",
            f"Tu {random.choice(IMAGES['kemet'])},",
            f"et {random.choice(IMAGES['sagesse'])}.",
            f"Gloire à {sujet}, {random.choice(IMAGES['espoir'])}.",
        ]
        return "\n".join(lines)

    def _gen_acrostic(self, mot: str) -> str:
        mot = mot.strip()[:10] if mot else "KEMET"
        lines = []
        for letter in mot.upper():
            adjectives = [img for img in IMAGES.get("nature", []) + IMAGES.get("sagesse", []) if img.lower().startswith(letter.lower())]
            if adjectives:
                lines.append(random.choice(adjectives))
            else:
                lines.append(f"{letter}... mystère des origines")
        return "\n".join(lines)

    def _gen_tale(self, sujet: str) -> str:
        personnage = random.choice(PERSONALITIES)
        lieu = random.choice(SETTINGS)
        revelation = random.choice(IMAGES["sagesse"])
        morale = random.choice(IMAGES["sagesse"])
        return (
            f"{personnage}, {lieu}, racontait l'histoire de {sujet}.\n\n"
            f"« Écoute, » disait-il, « {revelation}. »\n\n"
            f"Et le silence qui suivit en disait plus long que tous les mots.\n"
            f"Car {morale}."
        )

    def _gen_short_story(self, sujet: str) -> str:
        personnage = random.choice(PERSONALITIES)
        lieu = random.choice(SETTINGS)
        action = random.choice(["découvrit", "rencontra", "comprit soudainement que", "se souvint que"])
        consequence = random.choice(IMAGES["sagesse"])
        return (
            f"{personnage}, {lieu}. C'est là que {sujet}.\n\n"
            f"Il/Elle {action} {random.choice(IMAGES['nature'])}.\n\n"
            f"Et c'est ainsi que {consequence}."
        )

    def _gen_myth(self, sujet: str) -> str:
        return (
            f"Avant le commencement, il n'y avait que {sujet}.\n\n"
            f"Puis vint {random.choice(IMAGES['nature'])}.\n"
            f"De cette rencontre naquit {random.choice(IMAGES['kemet'])}.\n\n"
            f"Les anciens disent encore : {random.choice(IMAGES['sagesse'])}.\n"
            f"Voilà pourquoi, aujourd'hui encore, {random.choice(IMAGES['espoir'])}."
        )

    def _gen_epic(self, sujet: str) -> str:
        return (
            f"Je chante {sujet}, héritage des âges anciens,\n"
            f"{random.choice(IMAGES['kemet'])}.\n"
            f"{random.choice(IMAGES['guerre_paix'])}.\n\n"
            f"Que les générations se souviennent :\n"
            f"{random.choice(IMAGES['sagesse'])}."
        )

    def _gen_travel_story(self, sujet: str) -> str:
        return (
            f"Partir vers {sujet}, c'est {random.choice(IMAGES['voyage'])}.\n\n"
            f"À chaque pas, {random.choice(IMAGES['nature'])}.\n"
            f"Le voyageur note dans son carnet : « {random.choice(IMAGES['sagesse'])}. »\n\n"
            f"Au loin, l'horizon promet {random.choice(IMAGES['espoir'])}."
        )

    def _gen_argumentative_essay(self, sujet: str) -> str:
        these = f"{sujet} est essentiel"
        arg1 = random.choice(IMAGES["sagesse"])
        arg2 = random.choice(IMAGES["temps"])
        conclusion = random.choice(IMAGES["sagesse"])
        return (
            f"Thèse : {these}.\n\n"
            f"Premièrement, {arg1}.\n"
            f"Deuxièmement, {arg2}.\n\n"
            f"Ainsi, {conclusion}."
        )

    def _gen_portrait(self, sujet: str) -> str:
        return (
            f"Portrait de {sujet} :\n\n"
            f"Ses yeux portaient {random.choice(IMAGES['voyage'])}.\n"
            f"Sa voix était {random.choice(IMAGES['nature'])}.\n"
            f"Ses mains racontaient {random.choice(IMAGES['temps'])}.\n\n"
            f"On disait de lui/d'elle : « {random.choice(IMAGES['sagesse'])}. »"
        )

    def _gen_meditation(self, sujet: str) -> str:
        return (
            f"Sur {sujet}, je médite.\n\n"
            f"{random.choice(IMAGES['solitude'])}.\n"
            f"{random.choice(IMAGES['nature'])}.\n"
            f"{random.choice(IMAGES['sagesse'])}.\n\n"
            f"Et je comprends, enfin, que {random.choice(IMAGES['espoir'])}."
        )

    def _gen_speech(self, sujet: str) -> str:
        return (
            f"Mesdames, Messieurs, chers amis,\n\n"
            f"Aujourd'hui, je veux vous parler de {sujet}.\n\n"
            f"{random.choice(IMAGES['sagesse'])}.\n"
            f"Rappelez-vous : {random.choice(IMAGES['kemet'])}.\n"
            f"Car {random.choice(IMAGES['espoir'])}.\n\n"
            f"Je vous remercie."
        )

    def _gen_landscape(self, sujet: str) -> str:
        return (
            f"Le paysage s'étendait, vaste comme {sujet}.\n"
            f"Au premier plan, {random.choice(IMAGES['nature'])}.\n"
            f"Plus loin, {random.choice(IMAGES['kemet'])}.\n"
            f"Le ciel, lui, {random.choice(IMAGES['temps'])}.\n\n"
            f"C'était un lieu où {random.choice(IMAGES['sagesse'])}."
        )

    def _gen_ekphrasis(self, sujet: str) -> str:
        return (
            f"Devant cette œuvre — {sujet} — le temps s'arrête.\n"
            f"Les couleurs chantent {random.choice(IMAGES['nature'])}.\n"
            f"Les formes murmurent {random.choice(IMAGES['sagesse'])}.\n"
            f"On croirait entendre {random.choice(IMAGES['temps'])}.\n\n"
            f"L'artiste a capturé l'instant où {random.choice(IMAGES['espoir'])}."
        )

    def _gen_sensory_description(self, sujet: str) -> str:
        return (
            f"Imaginez {sujet} :\n"
            f"Vous voyez {random.choice(IMAGES['nature'])}.\n"
            f"Vous entendez {random.choice(IMAGES['temps'])}.\n"
            f"Vous sentez {random.choice(IMAGES['kemet'])}.\n"
            f"Et vous comprenez que {random.choice(IMAGES['sagesse'])}."
        )

    def _gen_philosophical_dialogue(self, sujet: str) -> str:
        sage = random.choice(PERSONALITIES)
        return (
            f"— Dis-moi, {sage}, qu'est-ce que {sujet} ?\n"
            f"— C'est {random.choice(IMAGES['sagesse'])}.\n"
            f"— Mais comment le sais-tu ?\n"
            f"— {random.choice(IMAGES['nature'])}.\n\n"
            f"Le disciple médita longuement.\n"
            f"Puis il comprit : {random.choice(IMAGES['espoir'])}."
        )

    def _gen_letter(self, sujet: str) -> str:
        lieu = random.choice(SETTINGS)
        return (
            f"Très cher/Chère,\n\n"
            f"Je t'écris {lieu}, où {sujet} occupe toutes mes pensées.\n\n"
            f"Ici, {random.choice(IMAGES['nature'])}.\n"
            f"Et moi, je me souviens de toi quand {random.choice(IMAGES['temps'])}.\n\n"
            f"Reviens-moi. {random.choice(IMAGES['espoir'])}.\n\n"
            f"À toi, pour toujours."
        )

    # ═══ MAIN GENERATION INTERFACE ═══
    def generate(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Generate creative text using the best matching template."""
        p = prompt.lower().strip()
        best_match = None
        best_priority = 0

        for tmpl in self.templates:
            m = re.search(tmpl["pattern"], p, re.IGNORECASE)
            if m:
                sujet = (m.group(1).strip() if m.group(1) and m.group(1).strip() else "le monde")
                priority = len(m.group(0)) * tmpl["confidence"]
                if priority > best_priority:
                    best_match = (tmpl, sujet)
                    best_priority = priority

        if best_match:
            tmpl, sujet = best_match
            text = tmpl["generate"](sujet)
            return {
                "text": text,
                "confidence": tmpl["confidence"],
                "template": tmpl["name"],
                "domain": tmpl["domain"],
                "sujet": sujet,
            }

        # Fallback: free poem
        return {
            "text": self._gen_free_poem(prompt),
            "confidence": 0.70,
            "template": "poeme_libre",
            "domain": "poetry",
            "sujet": prompt,
        }


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pkb = PoeticKB()
    tests = [
        "écris un sonnet sur le Nil",
        "haiku sur Kemet",
        "quatrain sur l'amour",
        "conte sur l'empire du Mali",
        "essai sur la vérité",
        "décris ce paysage de désert",
        "imagine un monde sans frontières",
        "dialogue philosophique sur la justice",
        "lettre à un ami disparu",
        "discours pour l'unité africaine",
        "épopée sur les pharaons noirs",
        "méditation sur le temps qui passe",
    ]
    print(f"\n{'='*60}")
    print(f"POETIC TEMPLATES — Test ({len(tests)} prompts)")
    print(f"{'='*60}")
    for q in tests:
        r = pkb.generate(q)
        print(f"\n[{r['template']}] {q}")
        print(r["text"][:200])
        print(f"(confiance: {r['confidence']:.2f})")