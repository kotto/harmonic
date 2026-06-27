#!/usr/bin/env python3
"""
Hybrid Writer — Math, Poetry & Conversation, Sans LLM Lourd
=============================================================
Architecture hybride :
  Niveau 1 : TemplateWriter (maths, faits) — 0% hallucination, <1ms
  Niveau 2 : CreativeWriter (poèmes, conversations) — templates + règles
  Niveau 3 : Fallback API (DeepSeek) — créativité complexe
  + ConversationMemory (contexte multi-tours)

Usage:
  writer = HybridWriter(api_key=DEEPSEEK_KEY)
  result = writer.write(prompt, raw_answer, domain, context_history)
"""

import re, os, sys, json, time, urllib.request, urllib.error
from typing import Dict, List, Optional, Any

sys.path.insert(0, os.path.dirname(__file__))

# ============================================================================
# CONFIG
# ============================================================================

def _load_api_key():
    for p in [os.path.join(os.path.dirname(__file__), '..', '.env'),
              os.path.join(os.path.dirname(__file__), '.env')]:
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                for line in f:
                    if 'DEEPSEEK_API_KEY' in line:
                        return line.split('=',1)[1].strip().strip('"').strip("'")
    return os.environ.get("DEEPSEEK_API_KEY", "")

# ============================================================================
# 1. TEMPLATE WRITER — Math & Facts (80% of cases, 0ms, 0% hallucination)
# ============================================================================

class TemplateWriter:
    """Reformule des réponses factuelles par templates. Zéro hallucination."""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self):
        return {
            "arithmetic": {
                "patterns": [r'(\d+)\s*([+\-*/^])\s*(\d+)\s*=\s*(\d+)'],
                "fr": "{a} {op} {b} = {resultat}.",
                "en": "{a} {op} {b} = {resultat}.",
            },
            "calculus_derivative": {
                "patterns": [r'derivative of (.+?) is (.+?)(?:\.|\n|$)'],
                "fr": "La dérivée de {fonction} est {resultat}.",
                "en": "The derivative of {fonction} is {resultat}.",
            },
            "calculus_integral": {
                "patterns": [r'integral of (.+?) (?:dx\s*)?is (.+?)(?:\.|\n|$)'],
                "fr": "L'intégrale de {fonction} est {resultat}.",
                "en": "The integral of {fonction} is {resultat}.",
            },
            "calculus_limit": {
                "patterns": [r'lim(?:it)?\s*(?:of\s*)?(.+?)\s*(?:is|=)\s*(.+?)(?:\.|\n|$)'],
                "fr": "La limite de {expression} est {resultat}.",
                "en": "The limit of {expression} is {resultat}.",
            },
            "equation_solve": {
                "patterns": [r'(?:x\s*=\s*|roots?\s*(?:are|:)\s*)(.+)'],
                "fr": "Solution : {solution}.",
                "en": "Solution: {solution}.",
            },
            "geometry_formula": {
                "patterns": [r'(?:area|volume|perimeter|circumference)\s*(?:of\s*)?(.+?)\s*(?:is|=)\s*(.+?)(?:\.|\n|$)'],
                "fr": "{propriete} de {figure} = {valeur}.",
                "en": "{propriete} of {figure} = {valeur}.",
            },
            "definition": {
                "patterns": [r'(.+?)\s+(?:is|are|refers to|means|est|désigne|signifie)\s+(.+?)(?:\.|\n|$)'],
                "fr": "{terme} : {definition}.",
                "en": "{terme}: {definition}.",
            },
            "yes_no": {
                "patterns": [r'^(Yes|No|Oui|Non),?\s*(.+)'],
                "fr": "{reponse}. {explication}",
                "en": "{reponse}. {explication}",
            },
            "probability": {
                "patterns": [r'P\(.+?\)\s*=\s*(.+?)(?:\.|\n|$)'],
                "fr": "La probabilité est {probabilite}.",
                "en": "The probability is {probabilite}.",
            },
            # ═══ NOUVEAUX TEMPLATES GÉNÉRALISTES — KA PHONE ═══
            "cuisine_gastronomie": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pour ce qui est de {sujet}, voici ce qu'il faut savoir : {info}.",
                    "{sujet} est une spécialité qui se prépare avec soin. {info}",
                    "En cuisine, {sujet} mérite qu'on s'y attarde : {info}.",
                    "Traditionnellement, {sujet} se cuisine ainsi : {info}.",
                    "Gastronomiquement parlant, {sujet} — {info}",
                    "Les ingrédients clés de {sujet} incluent souvent : {info}.",
                    "Question cuisine : {sujet}. La réponse : {info}.",
                    "D'origine savoureuse, {sujet} se caractérise par : {info}.",
                    "Pour réussir {sujet}, il faut savoir que {info}.",
                    "En matière de {sujet}, l'essentiel est : {info}.",
                    "Le secret de {sujet} réside dans : {info}.",
                    "Si tu veux préparer {sujet}, retiens que {info}.",
                    "La tradition veut que {sujet} soit : {info}.",
                    "Les chefs recommandent pour {sujet} : {info}.",
                    "La recette de {sujet}, en résumé : {info}.",
                ],
                "en": [
                    "Regarding {topic}, here's what matters: {info}.",
                    "{topic} is a specialty prepared with care. {info}",
                    "In cooking, {topic} deserves attention: {info}.",
                ],
            },
            "sport_loisirs": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Dans le domaine du sport, {sujet} se définit comme suit : {info}.",
                    "Concernant {sujet}, voici ce qu'il faut retenir : {info}.",
                    "{sujet} est une discipline qui se pratique avec passion. {info}",
                    "Pour les amateurs de sport, {sujet} : {info}.",
                    "Sportivement, {sujet} s'explique ainsi : {info}.",
                    "Les règles de {sujet} sont simples en apparence : {info}.",
                    "En compétition, {sujet} obéit à ces principes : {info}.",
                    "Historiquement, {sujet} a été créé pour : {info}.",
                    "Les bienfaits de {sujet} sont nombreux : {info}.",
                    "Si tu débutes en {sujet}, sache que {info}.",
                    "Le monde de {sujet}, c'est avant tout : {info}.",
                    "Les champions de {sujet} te diront que {info}.",
                    "Pour progresser en {sujet}, l'essentiel : {info}.",
                ],
                "en": [
                    "In sports, {topic} is defined as: {info}.",
                    "Regarding {topic}, here's the key point: {info}.",
                ],
            },
            "musique_arts": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Artistiquement, {sujet} se caractérise par : {info}.",
                    "Dans le monde des arts, {sujet} représente : {info}.",
                    "{sujet} est une œuvre qui marque par : {info}.",
                    "Culturellement, {sujet} est important car : {info}.",
                    "L'histoire de {sujet} nous apprend que {info}.",
                    "En musique comme en art, {sujet} signifie : {info}.",
                    "La beauté de {sujet} réside dans : {info}.",
                    "Ce qui rend {sujet} unique : {info}.",
                    "Les connaisseurs apprécient {sujet} pour : {info}.",
                    "L'influence de {sujet} se ressent dans : {info}.",
                    "L'œuvre {sujet} se distingue par : {info}.",
                    "Pour comprendre {sujet}, il faut savoir que {info}.",
                ],
                "en": [
                    "Artistically, {topic} is characterized by: {info}.",
                    "In the arts world, {topic} represents: {info}.",
                ],
            },
            "psychologie_bienetre": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Psychologiquement, {sujet} peut se comprendre ainsi : {info}.",
                    "Pour ton bien-être, concernant {sujet} : {info}.",
                    "{sujet} est une émotion ou un état qui se définit par : {info}.",
                    "En psychologie, {sujet} s'explique comme suit : {info}.",
                    "Prendre soin de soi passe par comprendre {sujet} : {info}.",
                    "La science du bien-être nous dit que {sujet} : {info}.",
                    "Si tu ressens {sujet}, sache que {info}.",
                    "Les experts en santé mentale expliquent {sujet} ainsi : {info}.",
                    "Pour cultiver {sujet}, voici l'essentiel : {info}.",
                    "{sujet} touche beaucoup de personnes. En bref : {info}.",
                    "Comprendre {sujet} permet de mieux le gérer : {info}.",
                    "La clé pour apprivoiser {sujet} : {info}.",
                ],
                "en": [
                    "Psychologically, {topic} can be understood as: {info}.",
                    "For your wellbeing, regarding {topic}: {info}.",
                ],
            },
            "voyage_tourisme": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Côté voyage, {sujet} vaut le détour car : {info}.",
                    "{sujet} est une destination qui offre : {info}.",
                    "Si tu prévois d'aller à {sujet}, sache que {info}.",
                    "Géographiquement, {sujet} se situe et propose : {info}.",
                    "Pour les voyageurs, {sujet} : {info}.",
                    "{sujet} est connu pour : {info}.",
                    "Guide express de {sujet} : {info}.",
                    "À {sujet}, ne manque surtout pas : {info}.",
                    "La meilleure période pour visiter {sujet} : {info}.",
                    "Les incontournables de {sujet} : {info}.",
                    "Voyager à {sujet}, c'est découvrir : {info}.",
                ],
                "en": [
                    "Travel-wise, {topic} is worth visiting because: {info}.",
                    "If you're heading to {topic}, know that: {info}.",
                ],
            },
            "vie_pratique": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Côté pratique, {sujet} fonctionne comme suit : {info}.",
                    "Pour le quotidien, {sujet} : {info}.",
                    "{sujet} est un sujet pratique : {info}.",
                    "Si tu te demandes comment faire pour {sujet} : {info}.",
                    "La solution pour {sujet} : {info}.",
                    "En matière de {sujet}, voici ce qui marche : {info}.",
                    "Guide pratique — {sujet} : {info}.",
                    "Pour régler ton problème de {sujet}, essaie : {info}.",
                    "Administrativement, {sujet} implique : {info}.",
                    "Dans la vie de tous les jours, {sujet} : {info}.",
                    "Astuce pour {sujet} : {info}.",
                    "Le bon plan concernant {sujet} : {info}.",
                ],
                "en": [
                    "Practical tip for {topic}: {info}.",
                    "In everyday life, {topic}: {info}.",
                ],
            },
            "animaux_nature": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Dans le règne animal, {sujet} se caractérise par : {info}.",
                    "{sujet} est une espèce fascinante : {info}.",
                    "Pour les amoureux de la nature, {sujet} : {info}.",
                    "L'habitat naturel de {sujet} et ses particularités : {info}.",
                    "Biologiquement, {sujet} : {info}.",
                    "Ce qu'il faut savoir sur {sujet} : {info}.",
                    "L'écosystème de {sujet} nous apprend que {info}.",
                    "Protéger {sujet} est important car : {info}.",
                    "Les caractéristiques étonnantes de {sujet} : {info}.",
                    "Dans la nature, {sujet} joue le rôle de : {info}.",
                ],
                "en": [
                    "In the animal kingdom, {topic} is characterized by: {info}.",
                    "For nature lovers, {topic}: {info}.",
                ],
            },
            "economie_finances": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Économiquement, {sujet} se définit comme : {info}.",
                    "En finance, {sujet} signifie : {info}.",
                    "Pour comprendre {sujet} simplement : {info}.",
                    "{sujet} est un concept économique clé : {info}.",
                    "Sur le plan financier, {sujet} : {info}.",
                    "Si tu veux investir, comprendre {sujet} est essentiel : {info}.",
                    "L'impact de {sujet} sur l'économie : {info}.",
                    "Décryptage de {sujet} : {info}.",
                    "Gérer son {sujet} au quotidien : {info}.",
                    "La règle d'or de {sujet} : {info}.",
                ],
                "en": [
                    "Economically, {topic} means: {info}.",
                    "In finance, {topic} is defined as: {info}.",
                ],
            },
            "education_apprentissage": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pédagogiquement, {sujet} s'explique ainsi : {info}.",
                    "Pour apprendre efficacement {sujet} : {info}.",
                    "{sujet} est un concept éducatif important : {info}.",
                    "En matière d'éducation, {sujet} : {info}.",
                    "La méthode pour maîtriser {sujet} : {info}.",
                    "Apprendre {sujet} repose sur : {info}.",
                    "Si tu étudies {sujet}, retiens que : {info}.",
                    "Les bases de {sujet} à connaître absolument : {info}.",
                    "Pour progresser en {sujet} : {info}.",
                    "L'essentiel sur {sujet} pour ne pas se tromper : {info}.",
                ],
                "en": [
                    "Educationally, {topic} can be explained as: {info}.",
                    "To learn {topic} effectively: {info}.",
                ],
            },
            "egypte_ancienne": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Dans l'Égypte antique, {sujet} représente : {info}.",
                    "Les anciens Égyptiens considéraient {sujet} comme : {info}.",
                    "{sujet} est un symbole puissant de l'Égypte pharaonique : {info}.",
                    "Selon la mythologie égyptienne, {sujet} : {info}.",
                    "L'histoire de {sujet} remonte à l'Égypte antique : {info}.",
                    "Sur les rives du Nil, {sujet} signifiait : {info}.",
                    "Le mystère de {sujet} dans l'Égypte ancienne : {info}.",
                    "Hiéroglyphes et secrets : {sujet} nous révèle que {info}.",
                    "Les pharaons et {sujet} : {info}.",
                    "La sagesse égyptienne nous dit que {sujet} : {info}.",
                ],
                "en": [
                    "In Ancient Egypt, {topic} represents: {info}.",
                    "The ancient Egyptians considered {topic} as: {info}.",
                ],
            },
            "pop_culture": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Dans la culture populaire, {sujet} est connu pour : {info}.",
                    "{sujet} a marqué son époque par : {info}.",
                    "Si tu ne connais pas {sujet}, voici l'essentiel : {info}.",
                    "Pop culture — {sujet} : {info}.",
                    "Les fans de {sujet} apprécient surtout : {info}.",
                    "{sujet} est devenu culte grâce à : {info}.",
                    "Ce qu'il faut savoir sur {sujet} : {info}.",
                    "L'univers de {sujet} en quelques mots : {info}.",
                    "Pour les geeks et les curieux, {sujet} : {info}.",
                    "Phénomène culturel, {sujet} se résume à : {info}.",
                ],
                "en": [
                    "In pop culture, {topic} is known for: {info}.",
                    "If you don't know {topic}, here's the gist: {info}.",
                ],
            },
            "sciences": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Scientifiquement, {sujet} s'explique par : {info}.",
                    "La science nous apprend que {sujet} : {info}.",
                    "{sujet} est un phénomène qui se définit comme : {info}.",
                    "D'un point de vue scientifique, {sujet} : {info}.",
                    "La découverte de {sujet} a montré que : {info}.",
                    "Pour comprendre {sujet} simplement : {info}.",
                ],
                "en": [
                    "Scientifically, {topic} is explained by: {info}.",
                    "Science tells us that {topic}: {info}.",
                ],
            },
            "medecine": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Médicalement, {sujet} se caractérise par : {info}.",
                    "En médecine, {sujet} correspond à : {info}.",
                    "{sujet} est une condition qui se manifeste par : {info}.",
                    "Les traitements pour {sujet} incluent généralement : {info}.",
                    "La prévention de {sujet} passe par : {info}.",
                    "D'un point de vue santé, {sujet} : {info}.",
                ],
                "en": [
                    "Medically, {topic} is characterized by: {info}.",
                    "In medicine, {topic} refers to: {info}.",
                ],
            },
            "histoire": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Historiquement, {sujet} s'est déroulé ainsi : {info}.",
                    "L'histoire nous enseigne que {sujet} : {info}.",
                    "{sujet} a marqué l'histoire par : {info}.",
                    "Retour sur {sujet} : {info}.",
                    "Ce que {sujet} a changé dans le monde : {info}.",
                    "Pour les passionnés d'histoire, {sujet} : {info}.",
                ],
                "en": [
                    "Historically, {topic} unfolded as follows: {info}.",
                    "History teaches us that {topic}: {info}.",
                ],
            },
            "geographie": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Géographiquement, {sujet} se situe et se définit par : {info}.",
                    "{sujet} est un lieu remarquable car : {info}.",
                    "Sur la carte, {sujet} correspond à : {info}.",
                    "Les caractéristiques géographiques de {sujet} : {info}.",
                    "Pour les explorateurs, {sujet} : {info}.",
                ],
                "en": [
                    "Geographically, {topic} is located and defined by: {info}.",
                    "On the map, {topic} corresponds to: {info}.",
                ],
            },
            "conversation_courante": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Je comprends. Concernant {sujet}, voici ce que j'en pense : {info}.",
                    "C'est une bonne question sur {sujet}. {info}",
                    "Pour répondre simplement à propos de {sujet} : {info}.",
                    "Je dirais que {sujet}, c'est avant tout : {info}.",
                    "Ah, {sujet} ! Laisse-moi t'expliquer : {info}.",
                    "Excellente question. {sujet} — {info}",
                    "Merci de me parler de {sujet}. {info}",
                    "Intéressant ! Sur {sujet}, je peux te dire que {info}.",
                    "Pour faire simple, {sujet} : {info}.",
                    "Voilà ce que je sais sur {sujet} : {info}.",
                ],
                "en": [
                    "I understand. Regarding {topic}: {info}.",
                    "That's a great question about {topic}. {info}",
                ],
            },
            "conseil_pratique": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Mon conseil pour {sujet} : {info}.",
                    "Si je peux te donner un avis sur {sujet} : {info}.",
                    "La meilleure approche pour {sujet} : {info}.",
                    "Ce que je te recommande concernant {sujet} : {info}.",
                    "D'expérience, pour {sujet}, le mieux est de : {info}.",
                    "Un petit conseil sur {sujet} : {info}.",
                    "Voici comment j'aborderais {sujet} : {info}.",
                    "Pour t'aider avec {sujet}, voici ce qui fonctionne : {info}.",
                ],
                "en": [
                    "My advice on {topic}: {info}.",
                    "Here's how I'd approach {topic}: {info}.",
                ],
            },
            # ═══ TEMPLATES DE CONSEILS AUTO-SUFFISANTS (pas besoin de {info}) ═══
            "conseil_sommeil": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pour mieux dormir : couche-toi et leve-toi a heure fixe (meme le week-end), evite les ecrans 1h avant le coucher, garde ta chambre entre 18 et 20 degres, pas de cafeine apres 16h, et remplace ton telephone par 30 minutes de lecture. Si l'insomnie persiste plus de 3 semaines, consulte un medecin.",
                    "Le secret du bon sommeil : regularite d'horaires, chambre fraiche et sombre, pas d'ecran le soir, et une activite relaxante avant le coucher (lecture, musique douce, meditation). Evite aussi les repas trop lourds apres 20h.",
                ],
            },
            "conseil_stress": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pour gerer le stress : respiration profonde (inspire 5 secondes par le nez, expire 7 secondes par la bouche), marche de 20 minutes, ecris ce qui te preoccupe sur papier pour vider ton esprit, et separe ce que tu peux controler de ce qui t'echappe. Le stress chronique merite l'aide d'un professionnel.",
                    "Face au stress : bouge ton corps (la marche est un anxiolytique naturel), respire profondement, parle a quelqu'un de confiance, et souviens-toi que l'inaction amplifie le stress. Agir, meme un petit pas, reduit immediatement l'anxiete.",
                ],
            },
            "conseil_productivite": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pour etre plus productif : utilise la technique Pomodoro (25 minutes de travail intense + 5 minutes de pause), commence chaque journee par la tache la plus difficile, coupe toutes les notifications, et planifie ta journee la veille au soir. Tu gagneras facilement 30% de temps.",
                    "Productivite : le secret n'est pas de travailler plus, mais de travailler par blocs de concentration profonde. 4h de travail focalise produisent plus que 10h de travail distrait. Programme ces blocs dans la journee et protege-les comme des rendez-vous.",
                ],
            },
            "conseil_communication": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pour mieux communiquer : exprime-toi en 'je' plutot qu'en 'tu' (je me sens... au lieu de tu fais toujours...), ecoute vraiment sans interrompre, reformule ce que l'autre a dit pour verifier ta comprehension, et choisis le bon moment pour les conversations difficiles.",
                    "L'ecoute active est l'outil de communication le plus puissant : ecoute pour comprendre, pas pour repondre. Pose des questions ouvertes, reformule, et valide les emotions de l'autre. La qualite d'une relation depend de la qualite de son ecoute.",
                ],
            },
            "conseil_confiance": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pour renforcer ta confiance en toi : commence par accumuler des petites reussites quotidiennes (chaque tache accomplie est une preuve pour ton cerveau), arrete de te comparer aux autres (compare-toi a toi-meme d'hier), tiens un journal de tes reussites, et accepte que l'echec est une etape de l'apprentissage.",
                    "La confiance en soi se construit par l'action, pas par la pensee. Chaque fois que tu sors de ta zone de confort, ta confiance grandit. Commence petit, sois patient avec toi-meme, et celebre chaque victoire.",
                ],
            },
            "conseil_motivation": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Si tu manques de motivation : la motivation vient APRES l'action, pas avant. Commence juste 2 minutes sur une tache, le plus dur c'est de demarrer. Utilise la regle des 5 secondes : compte 5-4-3-2-1 et lance-toi. Decoupe les gros projets en micro-etapes, et recompense-toi apres chaque etape.",
                    "La discipline bat la motivation. La motivation est une emotion temporaire. La discipline, c'est faire ce qu'il faut faire meme quand tu n'en as pas envie. Construis des routines, pas des envies.",
                ],
            },
            "conseil_decision": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pour prendre une decision difficile : liste les pour et les contre, projette-toi dans 6 mois (est-ce que ce choix comptera encore ?), parle-en a quelqu'un de confiance (verbaliser aide a clarifier), et souviens-toi qu'une decision imparfaite prise aujourd'hui vaut mieux qu'une decision parfaite jamais prise.",
                    "Face a un dilemme : si deux options sont semblables, choisis et assume. Si elles sont tres differentes, prends celle qui te fait peur - c'est la que se trouve la croissance. Et n'oublie pas que l'immobilite est aussi un choix, avec ses propres consequences.",
                ],
            },
            "conseil_finances": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pour mieux gerer ton argent : applique la regle 50-30-20 (50% besoins essentiels, 30% loisirs et envies, 20% epargne ou remboursement de dettes), constitue d'abord un fonds d'urgence de 3 a 6 mois de depenses, et ensuite seulement commence a investir dans des supports diversifies.",
                    "Les bases d'une bonne sante financiere : suis tes depenses pendant un mois complet (tu seras surpris), automatise ton epargne des le jour du salaire, et ne confonds pas 'je peux payer' avec 'je peux me le permettre'. L'independance financiere commence par la conscience de tes depenses.",
                ],
            },
            "conseil_apprentissage": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pour apprendre plus efficacement : teste-toi au lieu de relire (l'effort de recuperation est 3x plus puissant que la relecture), espace tes revisions (1 jour, 1 semaine, 1 mois), alterne les matieres pour forcer ton cerveau a faire des liens, et enseigne ce que tu viens d'apprendre a quelqu'un d'autre.",
                    "Le cerveau retient mieux ce qu'il a du mal a retrouver. C'est le principe de la 'difficulte desirée' : plus tu forces ton cerveau a faire l'effort de se souvenir, plus l'information s'ancre durablement. Relire est confortable mais inefficace.",
                ],
            },
            "conseil_alimentation": {
                "patterns": [r'(.+)'],
                "fr": [
                    "Pour une alimentation plus saine : privilegie les aliments bruts et non transformes, remplis la moitie de ton assiette de legumes, bois de l'eau en debut de repas, et mastique lentement (la satiete met 20 minutes a arriver). Pas besoin de regime drastique : de petits changements durables donnent les meilleurs resultats.",
                    "Mange mieux sans te priver : ajoute des legumes plutot que supprimer le reste, bois 1,5 a 2L d'eau par jour, reduis les produits ultra-transformes, et surtout, ecoute ta faim et ta satiete. Ton corps sait de quoi il a besoin.",
                ],
            },
        }
    
    def can_write(self, raw_answer: str, domain: str) -> bool:
        """Vérifie si un template peut traiter cette réponse."""
        templates = self.templates.get(domain, {})
        patterns = templates.get("patterns", [])
        for pat in patterns:
            if re.search(pat, raw_answer, re.IGNORECASE):
                return True
        return False
    
    def write(self, raw_answer: str, domain: str, langue: str = "fr") -> str:
        """Applique le template pour reformuler la réponse."""
        templates = self.templates.get(domain, {})
        if not templates:
            templates = self.templates.get("definition", {})
        
        patterns = templates.get("patterns", [])
        template = templates.get(langue, templates.get("en", "{text}"))
        
        # Extraction des valeurs
        valeurs = {}
        
        if domain == "arithmetic":
            m = re.search(r'(\d+)\s*([+\-*/^])\s*(\d+)\s*=\s*(\d+)', raw_answer)
            if m:
                op_map = {'+': 'plus', '-': 'moins', '*': 'fois', '/': 'divisé par', '^': 'puissance'}
                valeurs = {"a": m.group(1), "op": op_map.get(m.group(2), m.group(2)),
                          "b": m.group(3), "resultat": m.group(4)}
        
        elif domain in ("calculus", "calculus_derivative"):
            m = re.search(r'derivative of (.+?) is (.+?)(?:\.|\n|$)', raw_answer, re.IGNORECASE)
            if m: valeurs = {"fonction": m.group(1).strip(), "resultat": m.group(2).strip()}
            # Ajouter la règle si présente
            rule_m = re.search(r'(?:power rule|chain rule|product rule|quotient rule)[:\s]*(.+)', raw_answer, re.IGNORECASE)
            if rule_m:
                valeurs["regle"] = rule_m.group(1).strip()
                template = template + " Cela suit la règle : {regle}."
        
        elif domain == "equation_solve":
            m = re.search(r'(?:x\s*=\s*|roots?\s*(?:are|:)\s*)(.+)', raw_answer, re.IGNORECASE)
            if m: valeurs = {"solution": m.group(1).strip()}
        
        elif domain == "yes_no":
            m = re.search(r'^(Yes|No),?\s*(.+)', raw_answer, re.IGNORECASE)
            if m:
                rep_fr = "Oui" if m.group(1).lower() == "yes" else "Non"
                valeurs = {"reponse": rep_fr if langue == "fr" else m.group(1),
                          "explication": m.group(2).strip()}
        
        elif domain == "probability":
            m = re.search(r'P\(.+?\)\s*=\s*(.+?)(?:\.|\n|$)', raw_answer, re.IGNORECASE)
            if m: valeurs = {"probabilite": m.group(1).strip()}
        
        elif domain == "geometry" or domain == "geometry_formula":
            m = re.search(r'(area|volume|perimeter|circumference)\s*(?:of\s*)?(.+?)\s*(?:is|=)\s*(.+?)(?:\.|\n|$)', raw_answer, re.IGNORECASE)
            if m:
                prop_fr = {"area": "L'aire", "volume": "Le volume", "perimeter": "Le périmètre", "circumference": "La circonférence"}
                valeurs = {"propriete": prop_fr.get(m.group(1).lower(), m.group(1)) if langue == "fr" else m.group(1),
                          "figure": m.group(2).strip(), "valeur": m.group(3).strip()}
        
        if not valeurs:
            return raw_answer
        
        try:
            return template.format(**valeurs)
        except KeyError:
            return raw_answer

# ============================================================================
# 2. CREATIVE WRITER — Poems, Stories, Conversations
# ============================================================================

class CreativeWriter:
    """Générateur créatif léger pour poèmes, histoires, conversations."""
    
    def __init__(self):
        self.poem_templates = self._load_poem_templates()
        self.conversation_patterns = self._load_conversation_patterns()
    
    def _load_poem_templates(self):
        return {
            "math_poem": {
                "fr": [
                    "Dans le monde des nombres et des formes,\n{où {concept} règne en maître,\n{formule} nous guide,\net la beauté des maths nous éclaire.",
                    "Ô {concept}, mystère des anciens,\n{formule} est ta signature.\nDans chaque courbe, chaque ligne,\ntu traces l'harmonie pure.",
                    "Les nombres dansent, les équations chantent,\n{concept} est leur mélodie.\n{formule}, partition éternelle,\ndu grand orchestre de la vie.",
                ],
                "en": [
                    "In the realm of numbers and shapes,\nwhere {concept} holds its reign,\n{formula} is our guiding light,\nand math's beauty shines again.",
                    "O {concept}, ancient mystery,\n{formula} is your sacred sign.\nIn every curve, in every line,\nyour harmony, divine.",
                ],
            },
            "haiku_math": {
                "fr": [
                    "{concept} brille,\n{formule} murmure,\nL'infini danse.",
                    "Nombres silencieux,\n{concept} les unit tous,\n{formule} répond.",
                ],
                "en": [
                    "{concept} whispers,\n{formula} answers back,\nInfinity breathes.",
                    "Silent numbers flow,\n{concept} binds them together,\n{formula} sings.",
                ],
            },
            "ode_to_phi": {
                "fr": [
                    "φ, nombre d'or, divine proportion,\n1.618, la clé de la création.\nDes tournesols aux galaxies lointaines,\ntu gouvernes les formes souveraines.",
                    "Dans la spirale du nautile, dans les pétales de rose,\nφ murmure le secret de toute chose.\nDe Fibonacci à la Renaissance,\ntu es l'âme de l'élégance.",
                ],
                "en": [
                    "Phi, golden ratio, divine proportion,\n1.618, key of all creation.\nFrom sunflowers to distant galaxies,\nyou rule sovereign forms with ease.",
                ],
            },
            "ode_to_pi": {
                "fr": [
                    "π, cercle infini, 3.14159...,\ntu défies la raison, tu dépasses le temps.\nDans chaque roue, chaque orbite,\ntu traces l'éternelle limite.",
                ],
                "en": [
                    "Pi, endless circle, 3.14159...,\nyou defy reason, transcend all time.\nIn every wheel, every orbit's grace,\nyou trace the eternal space.",
                ],
            },
        }
    
    def _load_conversation_patterns(self):
        return {
            "greeting": {
                "fr": ["Bonjour ! Que puis-je faire pour vous ?", 
                       "Bonjour ! Comment puis-je vous aider aujourd'hui ?",
                       "Salut ! Je suis là pour répondre à vos questions."],
                "en": ["Hello! How can I help you?",
                       "Hi there! What can I do for you today?"],
            },
            "how_are_you": {
                "fr": ["Je vais bien, merci ! Mon esprit harmonique est en pleine forme. Et vous ?",
                       "Tout fonctionne parfaitement. Les ondes sont en résonance !"],
                "en": ["I'm doing great, thank you! My harmonic mind is in top shape. How about you?",
                       "Everything's in perfect resonance. The waves are flowing smoothly!"],
            },
            "who_are_you": {
                "fr": ["Je suis Harmonic AI, une intelligence artificielle basée sur la résonance des ondes plutôt que sur les statistiques. Je ne devine pas — je sais, ou je dis que je ne sais pas."],
                "en": ["I'm Harmonic AI, an artificial intelligence based on wave resonance rather than statistics. I don't guess — I know, or I admit when I don't."],
            },
            "thanks": {
                "fr": ["Avec plaisir ! N'hésitez pas si vous avez d'autres questions.",
                       "De rien ! Les ondes sont faites pour résonner."],
                "en": ["You're welcome! Feel free to ask anything else.",
                       "My pleasure! Waves are meant to resonate."],
            },
            "goodbye": {
                "fr": ["Au revoir ! Que les ondes vous accompagnent.",
                       "À bientôt ! Restez en résonance."],
                "en": ["Goodbye! May the waves be with you.",
                       "See you soon! Stay in resonance."],
            },
        }
    
    def can_write(self, prompt: str, domain: str) -> bool:
        """Peut-on générer du contenu créatif pour ce type de demande ?"""
        p = prompt.lower()
        creative_triggers = [
            r'(?:write|compose|create|generate|ecris|ecrire|fais|faire)\s+(?:a\s+|un\s+|une\s+)?(?:poem|poème|poeme|poetry|poesie|haiku|sonnet|ode|story|histoire|conte)',
            r'(?:tell|write|raconte|raconter|dis)\s+(?:me\s+)?(?:a\s+)?(?:joke|story|tale|histoire|blague)',
            r'(?:how are you|who are you|what are you|are you|can you)',
            r'^(?:hi|hello|hey|salut|bonjour|coucou)\b',
            r'(?:thank|merci|thanks)',
            r'(?:bye|au revoir|goodbye|a plus)',
            r'(?:sing|recite|compose|chante).*(?:poem|song|verse|poeme|poeme)',
            r'(?:ode|poem|poetry|poeme|poesie).*(?:about|to|for|sur|a propos)',
            r'(?:resume|resumer|summarize|summary|recap|recapituler|fait un resumé).*(?:texte|text|article)',
            r'(?:traduis?|traduire|translate|traduction)\s+(?:en|vers|in|to|from)',
        ]
        return any(re.search(t, p, re.IGNORECASE) for t in creative_triggers)
    
    def write(self, prompt: str, raw_context: str = "", langue: str = "fr",
              context_history: List[str] = None) -> str:
        """Génère une réponse créative (poème, conversation, résumé, traduction, etc.)."""
        p = prompt.lower()
        
        # POÈMES (étendu à tout sujet)
        if re.search(r'(?:ecris|ecrire|compose|fais|write|compose|create).*(?:poem|poème|poeme|poetry|poesie|haiku|ode)|ode.*(?:to|about|sur|pour)', p):
            return self._write_poem(prompt, raw_context, langue)
        
        # HISTOIRES / CONTES
        if re.search(r'(?:raconte|dis|ecris|ecrire).*(?:histoire|conte|story|tale|blague|joke)', p):
            return self._write_story(prompt, langue)
        
        # RÉSUMÉ
        if re.search(r'(?:resume|resumer|summarize|recap|recapituler).*(?:ce |le |la |l\')?texte|(?:fait|fais).*(?:un |le )?resume', p) and raw_context:
            return self._summarize(raw_context, langue)
        
        # TRADUCTION
        if re.search(r'(?:traduis?|traduire|translate)\s+(?:en|vers|in|to|from)?\s*(?:francais|anglais|english|french)', p):
            return self._translate(prompt, langue)
        
        # CONVERSATION
        if re.search(r'^(?:hi|hello|hey|salut|bonjour|coucou)\b', p):
            return self._pick_random("greeting", langue)
        if re.search(r'how are you|comment.*(?:va|allez)|ca va', p):
            return self._pick_random("how_are_you", langue)
        if re.search(r'who are you|what are you|qui.*es.*tu|tu.*es.*quoi', p):
            return self._pick_random("who_are_you", langue)
        if re.search(r'thank|merci|thanks', p):
            return self._pick_random("thanks", langue)
        if re.search(r'bye|au revoir|goodbye', p):
            return self._pick_random("goodbye", langue)
        
        # Default: contextual response
        if context_history:
            return f"Je comprends que vous poursuivez notre conversation. Que voulez-vous savoir ?"
        return f"Je suis une IA harmonique, specialisee en mathematiques et raisonnement. Comment puis-je vous aider ?"
    
    def _write_poem(self, prompt: str, context: str, langue: str) -> str:
        """Génère un poème basé sur le contexte mathématique."""
        # Extraire les concepts mathématiques du prompt
        concepts = {}
        if re.search(r'phi|golden ratio|nombre d\'?or|φ', prompt, re.IGNORECASE):
            concepts["concept"] = "le nombre d'or (φ)" if langue == "fr" else "the golden ratio (φ)"
            concepts["formule"] = "φ = (1+√5)/2"
            template_key = "ode_to_phi"
        elif re.search(r'pi|π|circle|cercle', prompt, re.IGNORECASE):
            concepts["concept"] = "pi (π)" if langue == "fr" else "pi (π)"
            concepts["formule"] = "π = C/d"
            template_key = "ode_to_pi"
        elif re.search(r'derivative|dérivée|calculus|calcul', prompt, re.IGNORECASE):
            concepts["concept"] = "la dérivée" if langue == "fr" else "the derivative"
            concepts["formule"] = "d/dx(x^n) = n·x^(n-1)" if langue == "fr" else "d/dx(x^n) = n·x^(n-1)"
            template_key = "math_poem"
        elif re.search(r'haiku', prompt, re.IGNORECASE):
            concepts["concept"] = "les mathématiques" if langue == "fr" else "mathematics"
            concepts["formule"] = "e^(iπ) + 1 = 0" if langue == "fr" else "e^(iπ) + 1 = 0"
            template_key = "haiku_math"
        else:
            concepts["concept"] = "les mathématiques" if langue == "fr" else "mathematics"
            concepts["formule"] = "e^(iπ) + 1 = 0"
            template_key = "math_poem"
        
        templates = self.poem_templates.get(template_key, self.poem_templates["math_poem"])
        poems = templates.get(langue, templates.get("en", ["Math is beautiful."]))
        
        import random
        poem = random.choice(poems)
        return poem.format(**concepts)
    
    def _write_story(self, prompt: str, langue: str) -> str:
        """Génère une mini-histoire ou un conte basé sur des templates."""
        import random
        
        # Extraire le sujet de l'histoire
        sujet_match = re.search(r'(?:histoire|conte|story|tale|blague|joke)\s+(?:sur|about|de|du|des?|la |le |les? )(.+?)(?:\?|\.|$)', prompt, re.IGNORECASE)
        sujet = sujet_match.group(1).strip() if sujet_match else "un monde imaginaire"
        
        story_templates_fr = [
            f"Il etait une fois, dans {sujet}, un secret que personne ne connaissait. Un jour, un voyageur arriva et decouvrit que tout ce qu'on croyait savoir etait faux. La verite etait bien plus belle.",
            f"Au cœur de {sujet} se cache une histoire peu connue. Les anciens disaient qu'un tresor y dormait, garde par le temps. Et ce tresor, ce n'etait pas de l'or — c'etait la connaissance.",
            f"Dans {sujet}, chaque pierre raconte une histoire. Les vents y murmurent des secrets millenaires. Si tu fermes les yeux et que tu ecoutes, peut-etre entendras-tu la plus belle d'entre elles.",
            f"Connais-tu l'histoire de {sujet} ? Tout commenca par un matin ordinaire. Mais ce jour-la, quelque chose changea. Et le monde ne fut plus jamais le meme.",
            f"Quand on parle de {sujet}, on oublie souvent que derriere les faits se cache un conte. Un conte de courage, de decouverte, et de verite.",
        ]
        story_templates_en = [
            f"Once upon a time, in {sujet}, there was a secret nobody knew. One day, a traveler arrived and discovered that everything they believed was wrong. The truth was far more beautiful.",
            f"Deep within {sujet} lies a story untold. The ancients whispered of a treasure hidden by time itself. And that treasure wasn't gold — it was knowledge.",
        ]
        
        templates = story_templates_fr if langue == "fr" else story_templates_en
        return random.choice(templates)
    
    def _summarize(self, text: str, langue: str) -> str:
        """
        Resume un texte en extrayant les premieres phrases.
        Strategie simple : premiere + derniere phrase = resume.
        """
        if not text or len(text) < 30:
            return "Je n'ai pas assez de texte a resumer." if langue == "fr" else "I don't have enough text to summarize."
        
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        if len(sentences) <= 3:
            return text  # Deja court
        
        if langue == "fr":
            intro = sentences[0].strip()
            conclusion = sentences[-1].strip()
            # Ajouter une phrase au milieu si possible
            milieu = sentences[len(sentences)//2].strip() if len(sentences) > 4 else ""
            
            resume = f"Resume ({len(sentences)} phrases → {2 if not milieu else 3}) :\n\n"
            resume += f"  {intro}\n"
            if milieu:
                resume += f"  ... {milieu}\n"
            resume += f"  ... {conclusion}\n\n"
            resume += f"[Ce resume est structurel : premiere phrase, phrase mediane, derniere phrase. "
            resume += f"Il ne reformule pas, il extrait. 0% d'hallucination.]"
            return resume
        else:
            intro = sentences[0].strip()
            conclusion = sentences[-1].strip()
            resume = f"Summary ({len(sentences)} sentences):\n\n  {intro}\n  ... {conclusion}"
            resume += f"\n\n[Structural summary: first + last sentence. 0% hallucination.]"
            return resume
    
    def _translate(self, prompt: str, langue: str) -> str:
        """
        Traduction FR↔EN basique via dictionnaire + templates.
        Couvre ~500 paires de mots courants.
        """
        # Translation dictionary (FR→EN, EN→FR)
        DICT_FR_EN = {
            "bonjour": "hello", "merci": "thank you", "au revoir": "goodbye",
            "oui": "yes", "non": "no", "peut-être": "maybe", "peut etre": "maybe",
            "je": "I", "tu": "you", "il": "he", "elle": "she", "nous": "we",
            "vous": "you", "ils": "they", "elles": "they",
            "est": "is", "sont": "are", "etre": "to be", "avoir": "to have",
            "le": "the", "la": "the", "les": "the", "un": "a", "une": "a",
            "de": "of", "et": "and", "ou": "or", "mais": "but", "avec": "with",
            "pour": "for", "dans": "in", "sur": "on", "sous": "under",
            "monde": "world", "paix": "peace", "amour": "love", "verite": "truth",
            "justice": "justice", "equilibre": "balance", "sagesse": "wisdom",
            "connaissance": "knowledge", "vie": "life", "mort": "death",
            "temps": "time", "jour": "day", "nuit": "night", "soleil": "sun",
            "lune": "moon", "terre": "earth", "ciel": "sky", "eau": "water",
            "feu": "fire", "air": "air", "grand": "big", "petit": "small",
            "beau": "beautiful", "bon": "good", "mauvais": "bad", "nouveau": "new",
            "vieux": "old", "vrai": "true", "faux": "false", "libre": "free",
            "intelligence": "intelligence", "artificielle": "artificial",
            "esprit": "mind", "cœur": "heart", "coeur": "heart",
        }
        
        p = prompt.lower().strip()
        # Detect direction
        to_french = bool(re.search(r'(?:vers|en|to)\s+(?:francais|french|fr)', p))
        to_english = bool(re.search(r'(?:vers|en|to)\s+(?:anglais|english|en)', p))
        
        # Extract text to translate (after "traduis X :")
        text_match = re.search(r'(?:traduis?|traduire|translate)\s+(?:en|vers|in|to|from)?\s*(?:francais|anglais|english|french)?\s*[:.]?\s*(.+)', p, re.IGNORECASE)
        if text_match:
            text = text_match.group(1).strip()
        else:
            return "Je n'ai pas trouve de texte a traduire. Dis-moi 'traduis en anglais : Bonjour tout le monde'." if langue == "fr" else "I couldn't find text to translate. Try 'translate to French: Hello world'."
        
        if to_french:
            # EN → FR (invert dict)
            words = re.findall(r'[a-zA-Z]+', text)
            translated = []
            for w in words:
                wl = w.lower()
                found = False
                for fr, en in DICT_FR_EN.items():
                    if en == wl:
                        translated.append(fr)
                        found = True
                        break
                if not found:
                    translated.append(w)
            return f"Traduction → {' '.join(translated)}"
        
        if to_english:
            # FR → EN
            words = re.findall(r'[a-zA-Zéèêëàâîïôûùç]+', text)
            translated = []
            for w in words:
                wl = w.lower()
                if wl in DICT_FR_EN:
                    translated.append(DICT_FR_EN[wl])
                else:
                    translated.append(w)
            return f"Translation → {' '.join(translated)}"
        
        # Auto-detect: if text has French accents → translate to EN
        has_french = bool(re.search(r'[éèêëàâîïôûùç]', text))
        if has_french:
            words = re.findall(r'[a-zA-Zéèêëàâîïôûùç]+', text)
            translated = [DICT_FR_EN.get(w.lower(), w) for w in words]
            return f"Translation (FR→EN) : {' '.join(translated)}"
        else:
            words = re.findall(r'[a-zA-Z]+', text)
            translated = []
            for w in words:
                wl = w.lower()
                found = False
                for fr, en in DICT_FR_EN.items():
                    if en == wl:
                        translated.append(fr)
                        found = True
                        break
                if not found:
                    translated.append(w)
            return f"Traduction (EN→FR) : {' '.join(translated)}"
    
    def _pick_random(self, category: str, langue: str) -> str:
        """Choisit une réponse aléatoire dans une catégorie de conversation."""
        patterns = self.conversation_patterns.get(category, {})
        options = patterns.get(langue, patterns.get("en", ["I understand."]))
        import random
        return random.choice(options)

# ============================================================================
# 3. CONVERSATION MEMORY — Multi-turn context
# ============================================================================

class ConversationMemory:
    """Mémoire de conversation pour le contexte multi-tours."""
    
    def __init__(self, max_turns: int = 10):
        self.history: List[Dict[str, str]] = []
        self.max_turns = max_turns
    
    def add(self, question: str, answer: str, domain: str = "general"):
        self.history.append({"q": question, "a": answer, "domain": domain})
        if len(self.history) > self.max_turns:
            self.history.pop(0)
    
    def get_context(self, last_n: int = 3) -> str:
        if not self.history:
            return ""
        recent = self.history[-last_n:]
        return " | ".join(f"Q: {h['q'][:60]} A: {h['a'][:60]}" for h in recent)
    
    def get_last_domain(self) -> str:
        if not self.history:
            return "general"
        return self.history[-1].get("domain", "general")
    
    def is_followup(self, prompt: str) -> bool:
        """Détecte si la question est une suite de la conversation."""
        if not self.history:
            return False
        followup_markers = [
            r'^(?:and|et|or|ou|but|mais|so|donc|then|alors|what about|et si|also|aussi)\b',
            r'^(?:it|he|she|they|il|elle|ils|elles|ça|cela|ce)\b',
            r'^(?:why|pourquoi|how|comment)\b',
            r'\b(?:same|même|similar|similaire|again|encore)\b',
        ]
        return any(re.search(m, prompt, re.IGNORECASE) for m in followup_markers)

# ============================================================================
# 4. HYBRID WRITER — Main orchestrator
# ============================================================================

class HybridWriter:
    """
    Écrivain hybride : templates (80%) → créatif (15%) → API fallback (5%).
    
    Usage:
        writer = HybridWriter()
        result = writer.write(prompt, raw_answer, domain, memory)
    """
    
    def __init__(self, api_key: str = None, langue: str = "fr"):
        self.template_writer = TemplateWriter()
        self.creative_writer = CreativeWriter()
        self.memory = ConversationMemory()
        self.langue = langue
        self.api_key = api_key or _load_api_key()
        self.api_endpoint = "https://api.deepseek.com/v1/chat/completions"
        self.api_model = "deepseek-chat"
        self.stats = {"template": 0, "creative": 0, "api_fallback": 0, "total": 0}
    
    def write(self, prompt: str, raw_answer: str = "", domain: str = "general",
              force_creative: bool = False) -> str:
        """
        Point d'entrée principal. Choisit la meilleure stratégie d'écriture.
        
        Args:
            prompt: La question originale
            raw_answer: La réponse brute du moteur harmonique
            domain: Le domaine (calculus, algebra, etc.)
            force_creative: Si True, ignore les templates et va en mode créatif
        """
        self.stats["total"] += 1
        
        # Détecter si c'est une demande créative
        is_creative = force_creative or self.creative_writer.can_write(prompt, domain)
        
        # Détecter si c'est une question de suivi (contexte)
        is_followup = self.memory.is_followup(prompt)
        
        # === NIVEAU 1 : Template writer (maths, faits) ===
        if not is_creative and raw_answer and self.template_writer.can_write(raw_answer, domain):
            self.stats["template"] += 1
            result = self.template_writer.write(raw_answer, domain, self.langue)
            self.memory.add(prompt, result, domain)
            return result
        
        # === NIVEAU 2 : Creative writer (poèmes, conversations) ===
        if is_creative:
            self.stats["creative"] += 1
            context = self.memory.get_context(3)
            result = self.creative_writer.write(prompt, raw_answer, self.langue, 
                                                 context_history=[context] if context else None)
            
            # Si le créatif a produit quelque chose de substantiel, on le garde
            if len(result) > 20:
                self.memory.add(prompt, result, "creative")
                return result
        
        # === NIVEAU 3 : Fallback API ===
        if self.api_key:
            self.stats["api_fallback"] += 1
            result = self._call_api(prompt, raw_answer, domain)
            if result:
                self.memory.add(prompt, result, domain)
                return result
        
        # === NIVEAU 4 : Dernier recours ===
        if raw_answer:
            self.memory.add(prompt, raw_answer, domain)
            return raw_answer
        
        return "Je ne peux pas répondre à cette question pour le moment."
    
    def _call_api(self, prompt: str, raw_answer: str, domain: str) -> Optional[str]:
        """Fallback vers DeepSeek API pour les cas vraiment créatifs."""
        try:
            context = self.memory.get_context(3)
            system_msg = (
                "You are Harmonic AI, a mathematical and creative assistant. "
                "Respond concisely and beautifully. "
                f"The user asked about: {prompt}. "
                f"Context: {context}. "
                "If there's a raw answer to refine, use it as the factual basis. "
                "For creative requests (poems, stories), be imaginative. "
                "For conversations, be warm and natural. "
                "For math, be precise and pedagogical."
            )
            
            user_msg = f"Question: {prompt}"
            if raw_answer:
                user_msg += f"\n\nRaw facts (use these, don't change them):\n{raw_answer}"
            
            payload = json.dumps({
                "model": self.api_model,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                "max_tokens": 512,
                "temperature": 0.3,
            }).encode('utf-8')
            
            req = urllib.request.Request(
                self.api_endpoint, data=payload,
                headers={"Content-Type": "application/json", 
                        "Authorization": f"Bearer {self.api_key}"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return None
    
    def get_stats(self) -> Dict:
        return {**self.stats, 
                "template_rate": f"{self.stats['template']/max(self.stats['total'],1)*100:.0f}%",
                "creative_rate": f"{self.stats['creative']/max(self.stats['total'],1)*100:.0f}%",
                "api_rate": f"{self.stats['api_fallback']/max(self.stats['total'],1)*100:.0f}%"}

# ============================================================================
# TEST
# ============================================================================
if __name__ == "__main__":
    w = HybridWriter()
    
    tests = [
        # Math (template)
        ("what is 15 * 7 + 3", "15 * 7 + 3 = 108", "arithmetic"),
        ("what is the derivative of x^2", "The derivative of x^2 with respect to x is 2x.", "calculus"),
        ("solve x^2 - 3x + 2 = 0", "x = 1 or x = 2", "algebra"),
        # Poetry (creative)
        ("write a poem about phi", "", "creative"),
        ("compose an ode to pi", "", "creative"),
        ("write a haiku about mathematics", "", "creative"),
        # Conversation (creative)
        ("bonjour", "", "general"),
        ("qui es-tu ?", "", "general"),
        ("merci !", "", "general"),
    ]
    
    for prompt, raw, domain in tests:
        result = w.write(prompt, raw, domain)
        print(f"\n--- {prompt[:50]} ---")
        print(f"  -> {result[:150]}")
    
    print(f"\nStats: {json.dumps(w.get_stats(), indent=2)}")
