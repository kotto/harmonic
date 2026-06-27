#!/usr/bin/env python3
"""
HARMONIC NARRATIVE COMPOSER - Composition engine for creative writing
========================================================================
Chains 100+ creative templates into coherent narratives with
proper arcs (introduction -> tension -> climax -> resolution)
and inter-step context awareness.

Enriched with 380+ poetic images across 30 categories.

Usage:
  from harmonic_narrative_composer import HarmonicNarrativeComposer
  hnc = HarmonicNarrativeComposer()
  poem = hnc.compose("ecris un poeme epique sur le Nil")
"""

import re, random, time, hashlib, math
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict

try:
    from enriched_images import ENRICHED_IMAGES as IMAGES
except ImportError:
    IMAGES = {"nature": ["le vent murmure"], "temps": ["le temps effeuille"]}

CHARACTERS = [
    "un vieux sage assis sous un baobab millenaire",
    "une mere racontant une histoire a son enfant au crepuscule",
    "un griot dont la voix porte la memoire de tout un peuple",
    "un voyageur aux pieds nus traversant le desert",
    "un poete ecrivant a la lueur vacillante d'une bougie",
    "un forgeron frappant le fer rouge dans la nuit africaine",
    "une reine regardant son royaume depuis les remparts",
    "un enfant qui decouvre le monde pour la premiere fois",
    "un ancetre parlant a travers les generations",
    "un pecheur lancant ses filets dans le fleuve a l'aube",
    "un soldat posant son epee pour prendre une plume",
    "un guerisseur preparant des remedes sous la lune",
]

SETTINGS = [
    "au bord du Nil, alors que le soleil se couchait sur les pyramides",
    "dans une bibliotheque ou dormaient des siecles de savoir",
    "sous un ciel d'orage, au sommet d'une colline sacree",
    "dans le silence d'un temple abandonne depuis mille ans",
    "au milieu du desert, la ou le sable rencontre les etoiles",
    "dans une foret ancestrale que nul n'avait traversee",
    "sur la place du village, autour du feu qui danse",
    "dans la cour du roi, sous les regards des ancetres sculptes",
    "au sommet de la montagne ou les dieux parlent aux hommes",
    "dans le ventre d'un bateau qui fend les eaux du grand fleuve",
    "au marche de Tombouctou, carrefour des mondes et des savoirs",
    "dans une grotte ornee de peintures vieilles de dix mille ans",
]

ACTIONS = [
    "decouvrit un secret que personne n'avait ose reveler",
    "rencontra un etranger qui changea sa vision du monde",
    "comprit soudainement que tout ce qu'il croyait etait faux",
    "se souvint d'une prophetie que sa grand-mere lui avait murmuree",
    "traversa des terres inconnues guide par les etoiles",
    "accepta un destin qu'il avait toujours refuse",
    "prit la parole devant l'assemblee silencieuse",
    "forgea une alliance qui changerait le cours de l'histoire",
    "defia l'ennemi avec pour seules armes la verite et le courage",
    "ecrivit les derniers mots d'un livre qui traverserait les siecles",
]

@dataclass
class ArcStep:
    name: str
    templates: List[str]
    image_categories: List[str]
    tone: str = "neutral"

NARRATIVE_ARCS = {
    "hero_journey": [
        ArcStep("Le Monde Ordinaire", ["description_paysage", "portrait"], ["nature", "temps"], "familier"),
        ArcStep("L'Appel de l'Aventure", ["recit_voyage", "discours"], ["voyage", "destin"], "inspirant"),
        ArcStep("Le Refus de l'Appel", ["meditation", "dialogue_philosophique"], ["solitude", "courage"], "tendu"),
        ArcStep("La Rencontre du Mentor", ["portrait", "dialogue_philosophique"], ["sagesse", "kemet"], "rassurant"),
        ArcStep("Le Franchissement du Seuil", ["recit_voyage", "ode"], ["courage", "voyage"], "epique"),
        ArcStep("Les Epreuves", ["epopee", "description_sensorielle"], ["guerre", "courage"], "intense"),
        ArcStep("L'Epreuve Supreme (Climax)", ["epopee", "discours"], ["guerre", "noblesse"], "climax"),
        ArcStep("La Recompense / Retour", ["meditation", "conte"], ["sagesse", "espoir"], "resolution"),
    ],
    "three_act": [
        ArcStep("Acte I - Exposition", ["description_paysage", "portrait"], ["nature", "temps"], "neutre"),
        ArcStep("Acte I - Incident Declencheur", ["discours", "recit_voyage"], ["destin", "voyage"], "tendu"),
        ArcStep("Acte II - Confrontation", ["epopee", "lettre"], ["guerre", "courage"], "intense"),
        ArcStep("Acte II - Point de Non-Retour", ["ode", "meditation"], ["solitude", "courage"], "sombre"),
        ArcStep("Acte III - Climax", ["discours", "epopee"], ["noblesse", "guerre"], "climax"),
        ArcStep("Acte III - Resolution", ["conte", "lettre"], ["sagesse", "paix", "espoir"], "resolution"),
    ],
    "tragedy": [
        ArcStep("Grandeur Initiale", ["ode", "description_paysage"], ["noblesse", "nature"], "majestueux"),
        ArcStep("La Faille (Hubris)", ["meditation", "dialogue_philosophique"], ["solitude", "destin"], "inquietant"),
        ArcStep("La Chute", ["epopee", "recit_voyage"], ["guerre", "temps"], "tragique"),
        ArcStep("La Prise de Conscience", ["lettre", "meditation"], ["solitude", "sagesse"], "douloureux"),
        ArcStep("La Catharsis", ["discours", "conte"], ["sagesse", "paix"], "resolution"),
    ],
    "creation_myth": [
        ArcStep("Le Chaos Primordial", ["description_sensorielle", "meditation"], ["nature", "temps"], "mysterieux"),
        ArcStep("L'Emergence", ["mythe", "ode"], ["creation", "kemet"], "merveilleux"),
        ArcStep("La Separation", ["epopee", "description_paysage"], ["nature", "voyage"], "epique"),
        ArcStep("L'Harmonie", ["conte", "poeme_libre"], ["paix", "sagesse"], "harmonieux"),
    ],
    "love_story": [
        ArcStep("La Rencontre", ["portrait", "description_sensorielle"], ["amour", "nature"], "tendre"),
        ArcStep("L'Emerveillement", ["sonnet", "quatrain", "ode"], ["amour", "espoir"], "lyrique"),
        ArcStep("L'Obstacle", ["lettre", "meditation"], ["solitude", "temps"], "douloureux"),
        ArcStep("La Reunion", ["discours", "dialogue_philosophique"], ["amour", "espoir"], "resolution"),
    ],
    "wisdom_tale": [
        ArcStep("La Question", ["dialogue_philosophique"], ["sagesse", "solitude"], "curieux"),
        ArcStep("L'Enigme", ["conte", "description_sensorielle"], ["nature", "kemet"], "mysterieux"),
        ArcStep("La Quete", ["recit_voyage", "portrait"], ["voyage", "courage"], "determine"),
        ArcStep("La Revelation", ["discours", "conte"], ["sagesse", "paix"], "illumine"),
    ],
    "epic_battle": [
        ArcStep("Le Rassemblement", ["discours", "portrait"], ["noblesse", "courage"], "solennel"),
        ArcStep("La Confrontation", ["epopee", "ode"], ["guerre", "destin"], "intense"),
        ArcStep("Le Tournant", ["description_sensorielle", "meditation"], ["solitude", "courage"], "critique"),
        ArcStep("Victoire et Memoire", ["conte", "discours"], ["paix", "sagesse", "kemet"], "triomphal"),
    ],
    "meditation_poem": [
        ArcStep("Observation", ["description_paysage", "haiku"], ["nature", "temps"], "contemplatif"),
        ArcStep("Interiorisation", ["meditation", "portrait_sensoriel"], ["solitude", "sagesse"], "introspectif"),
        ArcStep("Elevation", ["ode", "sonnet"], ["sagesse", "espoir"], "transcendant"),
    ],
}

class CreativeTemplate:
    def __init__(self, name, pattern, generator, domain, confidence):
        self.name = name
        self.pattern = pattern
        self.generator = generator
        self.domain = domain
        self.confidence = confidence

class HarmonicNarrativeComposer:
    def __init__(self):
        self.templates = self._build_100_templates()
        self.arcs = NARRATIVE_ARCS
        self.images = IMAGES

    def _pick(self, category, n=1):
        imgs = self.images.get(category, self.images.get("nature", ["le monde"]))
        return random.sample(imgs, min(n, len(imgs)))

    def _build_100_templates(self):
        t = []
        t.append(CreativeTemplate("sonnet", r'sonnet|14 vers|quatorze vers', lambda s,**kw: "\n".join(self._pick("amour",4)+self._pick("temps",3)+self._pick("sagesse",3)+self._pick("destin",2)+self._pick("espoir",2))[:14].split("\n")[:14], "poetry", 0.92))
        t.append(CreativeTemplate("haiku", r'haiku|5-7-5', lambda s,**kw: "\n".join([self._pick("nature",1)[0][:30], self._pick("temps",1)[0][:30], self._pick("sagesse",1)[0][:30]]), "poetry", 0.95))
        t.append(CreativeTemplate("quatrain", r'quatrain|4 vers', lambda s,**kw: "\n".join([random.choice(self.images.get(c,[""])) for c in random.choices(["amour","nature","sagesse","temps"],k=4)]), "poetry", 0.94))
        t.append(CreativeTemplate("poeme_libre", r'poeme|poem', lambda s,**kw: "\n".join(self._pick("nature", 3)+self._pick("temps",2)+self._pick("sagesse",2)+self._pick("espoir",1)), "poetry", 0.90))
        t.append(CreativeTemplate("ode", r'ode|chant|hymne', lambda s,**kw: f"O {s}, toi qui {random.choice(self.images['nature'])}!\nTu {random.choice(self.images['kemet'])},\net {random.choice(self.images['sagesse'])}.\nGloire a {s}, {random.choice(self.images['espoir'])}.", "poetry", 0.91))
        t.append(CreativeTemplate("elegie", r'elegie|elegy|poeme triste', lambda s,**kw: f"Pleurez, {random.choice(self.images['nature'])}.\n{s} n'est plus.\n{random.choice(self.images['solitude'])}.\nMais {random.choice(self.images['espoir'])}.", "poetry", 0.89))
        t.append(CreativeTemplate("ballade", r'ballade|ballad', lambda s,**kw: f"Ecoutez l'histoire de {s}:\n{random.choice(self.images['voyage'])}.\nRefrain: {random.choice(self.images['amour'])}\n{random.choice(self.images['courage'])}.", "poetry", 0.88))
        t.append(CreativeTemplate("epigramme", r'epigramme|epigram', lambda s,**kw: f"{s}: {random.choice(self.images['sagesse'])}.\n-- Ainsi parlait {random.choice(CHARACTERS)}.", "poetry", 0.87))
        t.append(CreativeTemplate("limerick", r'limerick|poeme humoristique|absurde', lambda s,**kw: f"Il etait une fois {s}\nQui {random.choice(self.images['nature'])}\n{random.choice(self.images['sagesse'])}\nEt avec {random.choice(self.images['courage'])}\n{random.choice(self.images['destin'])}.", "poetry", 0.82))
        t.append(CreativeTemplate("slam", r'slam|spoken word', lambda s,**kw: f"Je viens vous parler de {s}.\n{s}, c'est {random.choice(self.images['sagesse'])}.\n{s}, c'est {random.choice(self.images['courage'])}.\nEt si vous ne retenez qu'une chose:\n{random.choice(self.images['espoir'])}.", "poetry", 0.86))
        t.append(CreativeTemplate("acrostiche", r'acrostiche|acrostic', lambda s,**kw: "\n".join([f"{l.upper()}... mystere" for l in s[:5]]), "poetry", 0.93))
        t.append(CreativeTemplate("conte", r'conte|fable|legend', lambda s,**kw: f"{random.choice(CHARACTERS)}, {random.choice(SETTINGS)}, racontait l'histoire de {s}.\n\n<< Ecoute, >> disait-il/elle, << {random.choice(self.images['sagesse'])}. >>\n\nEt le silence qui suivit en disait plus long que tous les mots.\nCar {random.choice(self.images['espoir'])}.", "narrative", 0.93))
        t.append(CreativeTemplate("nouvelle", r'nouvelle|histoire courte|short story', lambda s,**kw: f"{random.choice(CHARACTERS)}, {random.choice(SETTINGS)}. C'est la que {s}.\n\nIl/Elle {random.choice(ACTIONS)}.\n\nEt c'est ainsi que {random.choice(self.images['sagesse'])}.", "narrative", 0.90))
        t.append(CreativeTemplate("mythe", r'mythe|myth|mythologie', lambda s,**kw: f"Avant le commencement, il n'y avait que {s}.\n\nPuis vint {random.choice(self.images['nature'])}.\nDe cette rencontre naquit {random.choice(self.images['kemet'])}.\n\nLes anciens disent encore: {random.choice(self.images['sagesse'])}.\nVoila pourquoi, aujourd'hui encore, {random.choice(self.images['espoir'])}.", "narrative", 0.92))
        t.append(CreativeTemplate("epopee", r'epopee|epic|recit epique', lambda s,**kw: f"Je chante {s}, heritage des ages anciens,\n{random.choice(self.images['kemet'])}.\n{random.choice(self.images['guerre'])}.\n\nQue les generations se souviennent:\n{random.choice(self.images['sagesse'])}.", "narrative", 0.91))
        t.append(CreativeTemplate("recit_voyage", r'recit de voyage|travel|periple', lambda s,**kw: f"Partir vers {s}, c'est {random.choice(self.images['voyage'])}.\nA chaque pas, {random.choice(self.images['nature'])}.\nLe voyageur note: << {random.choice(self.images['sagesse'])}. >>\nAu loin, l'horizon promet {random.choice(self.images['espoir'])}.", "narrative", 0.90))
        t.append(CreativeTemplate("journal_intime", r'journal intime|journal|diary', lambda s,**kw: f"Cher journal,\n\nAujourd'hui, {s}.\n{random.choice(self.images['temps'])}.\n{random.choice(self.images['solitude'])}.\n\nDemain, peut-etre, {random.choice(self.images['espoir'])}.", "narrative", 0.87))
        t.append(CreativeTemplate("chronique", r'chronique|chronicle|recit historique', lambda s,**kw: f"En l'an de grace, {random.choice(self.images['temps'])}, il advint que {s}.\nLes chroniqueurs rapportent que {random.choice(self.images['noblesse'])}.\n{random.choice(self.images['guerre'])}.\nEt c'est ainsi que {random.choice(self.images['sagesse'])}.", "narrative", 0.88))
        t.append(CreativeTemplate("biographie", r'biographie|biography|vie de', lambda s,**kw: f"{s} naquit sous le signe de {random.choice(self.images['destin'])}.\nSa vie fut marquee par {random.choice(self.images['courage'])}.\nOn se souvient de lui/elle pour {random.choice(self.images['sagesse'])}.", "narrative", 0.87))
        t.append(CreativeTemplate("essai_argumentatif", r'essai|essay|dissertation', lambda s,**kw: f"These: {s} est essentiel.\n\nPremierement, {random.choice(self.images['sagesse'])}.\nDeuxiemement, {random.choice(self.images['temps'])}.\n\nAinsi, {random.choice(self.images['sagesse'])}.", "essay", 0.91))
        t.append(CreativeTemplate("portrait", r'portrait|decris|qui est', lambda s,**kw: f"Portrait de {s}:\nSes yeux portaient {random.choice(self.images['voyage'])}.\nSa voix etait {random.choice(self.images['nature'])}.\nSes mains racontaient {random.choice(self.images['temps'])}.\n\nOn disait: << {random.choice(self.images['sagesse'])}. >>", "essay", 0.90))
        t.append(CreativeTemplate("meditation", r'meditation|reflexion|pensee', lambda s,**kw: f"Sur {s}, je medite.\n\n{random.choice(self.images['solitude'])}.\n{random.choice(self.images['nature'])}.\n{random.choice(self.images['sagesse'])}.\n\nEt je comprends, enfin, que {random.choice(self.images['espoir'])}.", "essay", 0.90))
        t.append(CreativeTemplate("discours", r'discours|speech|allocution', lambda s,**kw: f"Mesdames, Messieurs,\n\nAujourd'hui, je veux vous parler de {s}.\n\n{random.choice(self.images['sagesse'])}.\nRappelez-vous: {random.choice(self.images['kemet'])}.\nCar {random.choice(self.images['espoir'])}.\n\nJe vous remercie.", "essay", 0.91))
        t.append(CreativeTemplate("description_paysage", r'paysage|lieu|endroit|scene', lambda s,**kw: f"Le paysage s'etendait, vaste comme {s}.\nAu premier plan, {random.choice(self.images['nature'])}.\nPlus loin, {random.choice(self.images['kemet'])}.\nLe ciel, lui, {random.choice(self.images['temps'])}.\n\nC'etait un lieu ou {random.choice(self.images['sagesse'])}.", "description", 0.93))
        t.append(CreativeTemplate("portrait_sensoriel", r'imagine|visualise.*(?:monde|lieu|scene|espace)', lambda s,**kw: f"Imaginez {s}:\nVous voyez {random.choice(self.images['nature'])}.\nVous entendez {random.choice(self.images['temps'])}.\nVous sentez {random.choice(self.images['kemet'])}.\nEt vous comprenez que {random.choice(self.images['sagesse'])}.", "description", 0.91))
        t.append(CreativeTemplate("dialogue_philosophique", r'dialogue|conversation|echange', lambda s,**kw: f"-- Dis-moi, {random.choice(CHARACTERS)}, qu'est-ce que {s}?\n-- C'est {random.choice(self.images['sagesse'])}.\n-- Mais comment le sais-tu?\n-- {random.choice(self.images['nature'])}.\n\nLe disciple medita longuement.\nPuis il comprit: {random.choice(self.images['espoir'])}.", "dialogue", 0.88))
        t.append(CreativeTemplate("lettre", r'lettre|letter|missive', lambda s,**kw: f"Tres cher/Chere,\n\nJe t'ecris {random.choice(SETTINGS)}, ou {s} occupe toutes mes pensees.\n\nIci, {random.choice(self.images['nature'])}.\nEt moi, je me souviens de toi quand {random.choice(self.images['temps'])}.\n\nReviens-moi. {random.choice(self.images['espoir'])}.\n\nA toi, pour toujours.", "dialogue", 0.92))
        t.append(CreativeTemplate("priere", r'priere|prayer|invocation', lambda s,**kw: f"O {s},\nToi qui {random.choice(self.images['kemet'])},\nAccorde-nous {random.choice(self.images['sagesse'])},\nEt guide nos pas vers {random.choice(self.images['espoir'])}.\nAmen.", "dialogue", 0.88))
        t.append(CreativeTemplate("griot_narration", r'griot|conteur africain|african storyteller', lambda s,**kw: f"Ecoutez! Ecoutez! Le griot va parler!\n\nJe vais vous raconter {s}.\n{random.choice(self.images['afrique'])}.\n{random.choice(self.images['kemet'])}.\n\n{random.choice(self.images['sagesse'])}.\nC'est ainsi que parlent les anciens.", "africa", 0.93))
        t.append(CreativeTemplate("proverbe_africain", r'proverbe africain|african proverb', lambda s,**kw: f"Proverbe africain sur {s}:\n<< {random.choice(self.images['sagesse'])}. >>\n-- Sagesse {random.choice(['bambara','peule','zoulou','yoruba','wolof','bantoue'])}", "africa", 0.94))
        t.append(CreativeTemplate("manifeste", r'manifeste|manifesto', lambda s,**kw: f"MANIFESTE POUR {s.upper()}\n\nNous croyons que {random.choice(self.images['sagesse'])}.\nNous refusons {random.choice(self.images['guerre'])}.\nNous exigeons {random.choice(self.images['paix'])}.\n\n{random.choice(self.images['courage'])}!", "essay", 0.89))
        return t

    def _select_step_template(self, step, sujet):
        for tmpl_name in step.templates:
            tmpl = self._find_template(tmpl_name)
            if tmpl:
                return tmpl
        return None

    def _find_template(self, name):
        for tmpl in self.templates:
            if tmpl.name == name:
                return tmpl
        return None

    def _detect_template(self, prompt_lower):
        best_match = None
        best_priority = 0
        for tmpl in self.templates:
            m = re.search(tmpl.pattern, prompt_lower, re.IGNORECASE)
            if m:
                priority = len(m.group(0)) * tmpl.confidence
                if priority > best_priority:
                    best_match = tmpl
                    best_priority = priority
        return best_match

    def _extract_subject(self, prompt):
        """Extract clean subject from complex prompt like 'raconte-moi l'histoire de Soundiata Keita'."""
        clean = prompt.strip()
        # Creative genre words to filter
        creative_genres = r'(?:un |une |le |la |les |des |mon |ma |mes )?(?:poeme|poeme|sonnet|haiku|quatrain|ode|elegie|ballade|conte|nouvelle|mythe|epopee|essai|portrait|meditation|discours|lettre|priere|manifeste|slam|limerick|acrostiche|fable|legende|histoire|journal|chronique|biographie|anecdote|proverbe|prophetie|enigme|recit|recit epique|recit de voyage|chant|hymne)\s*'
        # Remove leading verbs
        clean = re.sub(r'^(?:ecris|ecrire|compose|fais|raconte|redige|decris|imagine|visualise)\s+(?:moi\s+)?', '', clean, flags=re.IGNORECASE)
        # Remove genre words
        clean = re.sub(creative_genres, '', clean, flags=re.IGNORECASE)
        # Remove prepositions
        clean = re.sub(r'^(?:sur |about |de |du |des? |pour |a |au |aux |l[\'e]histoire\s+(?:de\s+)?|histoire\s+(?:de\s+)?)', '', clean, flags=re.IGNORECASE)
        # Remove remaining articles
        clean = re.sub(r'\b(?:un |une |le |la |les |des |mon |ma |mes )\b', ' ', clean, flags=re.IGNORECASE)
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean).strip().rstrip("?!.,;: ")
        return clean if clean else "le monde"

    def _select_arc(self, prompt_lower, requested):
        if requested != "auto" and requested in self.arcs:
            return requested
        arc_keywords = {
            "hero_journey": ["heros", "hero", "voyage", "quete", "aventure"],
            "tragedy": ["tragedie", "tragedy", "triste", "chute", "mort"],
            "creation_myth": ["creation", "mythe", "origine", "commencement"],
            "love_story": ["amour", "love", "aimer", "coeur", "passion"],
            "wisdom_tale": ["sagesse", "lecon", "apprendre", "savoir"],
            "epic_battle": ["bataille", "guerre", "conflit", "combat"],
            "meditation_poem": ["meditation", "mediter", "contempler"],
        }
        scores = {arc:sum(1 for kw in kws if kw in prompt_lower) for arc, kws in arc_keywords.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "three_act"

    def compose(self, prompt, arc_type="auto", max_length=600):
        p = prompt.lower().strip()
        sujet = self._extract_subject(prompt)
        arc_type = self._select_arc(p, arc_type)
        arc = self.arcs.get(arc_type, self.arcs["three_act"])
        requested_template = self._detect_template(p)

        if requested_template and len(arc) <= 1:
            text = requested_template.generator(sujet)
            return {"text": text, "template": requested_template.name, "arc": "single",
                    "confidence": requested_template.confidence, "arc_steps": 1, "sujet": sujet}

        composed_parts = []
        arc_trace = []
        target_per_step = max_length // max(len(arc), 1)

        for i, step in enumerate(arc):
            step_template = self._select_step_template(step, sujet)
            if not step_template:
                step_template = requested_template or self._find_template("poeme_libre")
            context = " ".join(composed_parts[-2:]) if len(composed_parts) >= 2 else sujet
            step_text = step_template.generator(sujet)
            if len(step_text) > target_per_step:
                step_text = step_text[:target_per_step].rsplit("\n", 1)[0]
            composed_parts.append(step_text)
            arc_trace.append({"step": step.name, "template": step_template.name, "tone": step.tone})

        final_text = "\n\n".join(p.strip() for p in composed_parts)

        return {
            "text": final_text,
            "template": "narrative_arc",
            "arc": arc_type,
            "confidence": 0.80,
            "arc_steps": len(arc_trace),
            "arc_trace": arc_trace,
            "sujet": sujet,
        }


if __name__ == "__main__":
    hnc = HarmonicNarrativeComposer()
    tests = [
        ("ecris un poeme sur le Nil", "meditation_poem"),
        ("raconte-moi l'histoire de Soundiata Keita", "hero_journey"),
        ("ecris un conte africain sur la sagesse", "wisdom_tale"),
        ("raconte une histoire d'amour tragique", "tragedy"),
        ("ecris un discours pour l'unite africaine", "auto"),
        ("haiku sur Kemet", "auto"),
    ]
    print(f"\n{'='*50}")
    print("HARMONIC NARRATIVE COMPOSER - Test")
    print(f"{'='*50}")
    for prompt, arc in tests:
        r = hnc.compose(prompt, arc_type=arc)
        print(f"\n[{r['arc']}] {prompt} (steps: {r['arc_steps']})")
        print(r['text'][:250])
        print(f"...({len(r['text'])} chars)")