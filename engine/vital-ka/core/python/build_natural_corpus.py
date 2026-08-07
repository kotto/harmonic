"""
📚 build_natural_corpus.py — Génère un corpus français NATUREL
===============================================================
Transforme les triplets KB en phrases naturelles +
ajoute du texte varié (sciences, histoire, philosophie).

Usage : python build_natural_corpus.py
Sortie : data/corpus_natural_fr.txt
"""

import sys, os, random, re
from pathlib import Path

_ENGINE = Path(__file__).resolve().parent

# ════════════════════════════════════════════════════════════════
# 1. CHARGER LES TRIPLETS KB
# ════════════════════════════════════════════════════════════════

def load_kb_triplets(path=None) -> list:
    """Charge les triplets (sujet, relation, objet) depuis corpus_universal."""
    if path is None:
        path = _ENGINE / "data" / "corpus_universal" / "corpus_universal_20260720_1007.txt"
    triplets = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # Format: sujet relation objet (la relation est un seul token avec _)
            # Ex: "théorème de Pythagore est_un_concept_de Mathématiques"
            # Recherche du token avec _
            rel_idx = None
            for i, w in enumerate(parts):
                if '_' in w and i > 0 and i < len(parts) - 1:
                    rel_idx = i
                    break
            if rel_idx is None:
                continue
            sujet = ' '.join(parts[:rel_idx])
            relation = parts[rel_idx]
            objet = ' '.join(parts[rel_idx + 1:])
            triplets.append((sujet, relation, objet))
    return triplets


# ════════════════════════════════════════════════════════════════
# 2. TEMPLATES DE PHRASES NATURELLES
# ════════════════════════════════════════════════════════════════

KB_TEMPLATES = {
    "est_un_concept_de": [
        "{sujet} est un concept fondamental du domaine {objet}.",
        "En {objet}, {sujet} joue un rôle essentiel.",
        "{sujet} appartient au champ des {objet}.",
        "Le concept de {sujet} relève des {objet}.",
        "Dans le domaine des {objet}, on trouve {sujet}.",
        "{sujet} constitue un pilier des {objet}.",
        "Les {objet} incluent notamment {sujet}.",
    ],
    "a_decouvert": [
        "{sujet} a découvert {objet}, une avancée majeure.",
        "La découverte de {objet} par {sujet} a marqué l'histoire.",
        "{sujet} est célèbre pour avoir découvert {objet}.",
        "Grâce à {sujet}, nous connaissons aujourd'hui {objet}.",
        "{objet} fut mis au jour par les travaux de {sujet}.",
    ],
    "a_écrit": [
        "{sujet} a écrit {objet}, une œuvre influente.",
        "L'ouvrage {objet} a été rédigé par {sujet}.",
        "{sujet} est l'auteur de {objet}.",
    ],
    "a_inventé": [
        "{sujet} a inventé {objet}, révolutionnant son époque.",
        "L'invention de {objet} par {sujet} a changé le monde.",
        "{sujet} est l'inventeur de {objet}.",
    ],
    "est_une_partie_de": [
        "{sujet} fait partie intégrante de {objet}.",
        "{sujet} est une composante essentielle de {objet}.",
        "{objet} comprend notamment {sujet}.",
    ],
    "DEFAULT": [
        "{sujet} est lié à {objet}.",
        "Il existe un rapport entre {sujet} et {objet}.",
        "{sujet} et {objet} sont étroitement liés.",
    ]
}


# ════════════════════════════════════════════════════════════════
# 3. TEXTE NATUREL ADDITIONNEL
# ════════════════════════════════════════════════════════════════

NATURAL_FRENCH = """
La lumière est une onde électromagnétique qui se propage à environ trois cent mille kilomètres par seconde dans le vide. Elle est composée de photons, des particules sans masse qui transportent l'énergie lumineuse. La fréquence de la lumière détermine sa couleur. Les ondes radio, les micro-ondes, les infrarouges, la lumière visible, les ultraviolets, les rayons X et les rayons gamma forment le spectre électromagnétique.

L'univers a commencé il y a environ treize milliards d'années lors du Big Bang. Cette explosion primordiale a donné naissance à l'espace, au temps et à la matière. Les galaxies se sont formées progressivement par l'action de la gravité. Notre galaxie, la Voie Lactée, contient des centaines de milliards d'étoiles. Le Soleil est l'étoile centrale de notre système planétaire.

L'eau est une molécule composée de deux atomes d'hydrogène et d'un atome d'oxygène. Elle existe sous trois états : solide, liquide et gazeux. La Terre est la seule planète connue à abriter de l'eau liquide en surface. Les océans couvrent plus de soixante-dix pour cent de la surface terrestre.

La photosynthèse est le processus par lequel les plantes convertissent la lumière solaire en énergie chimique. Elle produit de l'oxygène comme sous-produit, essentiel à la respiration des animaux. Les chloroplastes sont les organites cellulaires où se déroule cette réaction.

Le nombre d'or, noté phi, vaut environ un virgule six cent dix-huit. On le retrouve dans la nature, dans la disposition des feuilles sur une tige, dans la spirale des coquillages et dans les proportions du corps humain. Les mathématiciens de la Grèce antique étudiaient déjà cette proportion divine.

La conscience est l'un des plus grands mystères de la science moderne. Elle émerge de l'activité complexe du cerveau humain, mais sa nature exacte reste débattue. Les neurosciences explorent les corrélats neuronaux de la conscience. La philosophie s'interroge sur la nature subjective de l'expérience consciente.

La musique est l'art de combiner les sons de manière harmonieuse. Elle utilise les notes, le rythme et la mélodie pour créer des émotions. Chaque culture a développé ses propres traditions musicales. La musique classique européenne a produit des compositeurs comme Mozart, Beethoven et Bach.

L'apprentissage automatique est une branche de l'intelligence artificielle qui permet aux ordinateurs d'apprendre à partir de données. Les réseaux de neurones artificiels s'inspirent du fonctionnement du cerveau biologique. L'apprentissage profond a permis des avancées remarquables en vision par ordinateur et en traitement du langage naturel.

La théorie de la relativité d'Einstein a révolutionné notre compréhension de l'espace et du temps. Elle montre que le temps n'est pas absolu mais dépend de la vitesse de l'observateur. La relativité générale explique la gravitation comme une courbure de l'espace-temps causée par la masse.

Les mathématiques sont le langage de la nature. Elles décrivent les lois physiques avec une précision remarquable. Du théorème de Pythagore aux équations de Maxwell, les mathématiques fournissent un cadre rigoureux pour comprendre l'univers.
"""


# ════════════════════════════════════════════════════════════════
# 4. GÉNÉRATION DU CORPUS
# ════════════════════════════════════════════════════════════════

def build_corpus(output_path=None):
    if output_path is None:
        output_path = _ENGINE / "data" / "corpus_natural_fr.txt"

    random.seed(42)
    triplets = load_kb_triplets()
    print(f"  Triplets chargés : {len(triplets)}")

    sentences = []

    # Convertir les triplets en phrases naturelles
    for sujet, rel, objet in triplets:
        templates = KB_TEMPLATES.get(rel, KB_TEMPLATES["DEFAULT"])
        tmpl = random.choice(templates)
        sent = tmpl.format(sujet=sujet, objet=objet)
        sentences.append(sent)

    print(f"  Phrases KB générées : {len(sentences)}")

    # Ajouter le texte naturel
    natural_sents = [s.strip() for s in NATURAL_FRENCH.split('.')
                    if len(s.strip()) > 20]
    for s in natural_sents:
        sentences.append(s.strip() + '.')

    print(f"  Phrases naturelles ajoutées : {len(natural_sents)}")

    # Mélanger pour éviter les clusters
    random.shuffle(sentences)

    # Écrire
    text = '\n'.join(sentences)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"\n  ✅ Corpus sauvegardé : {output_path}")
    print(f"     {len(sentences)} phrases, {len(text):,} caractères")
    return str(output_path)


if __name__ == "__main__":
    build_corpus()
