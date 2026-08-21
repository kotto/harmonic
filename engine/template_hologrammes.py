#!/usr/bin/env python3
"""
template_hologrammes.py — Hologrammes pré-remplis pour que KA soit
le compagnon intelligent dès la première utilisation.

Chaque template est un hologramme prêt à l'emploi, avec des exemples
que l'utilisateur peut personnaliser. Il suffit de remplacer les valeurs
par les siennes.

Usage :
  from template_hologrammes import TEMPLATES
  # Affiche les templates disponibles
  for t in TEMPLATES: print(t.nom, t.domaine)
  
  # Crée un hologramme à partir d'un template
  template.generer_hologramme("Sophie", {"A": 50000})
"""

import json, os, random
from typing import List, Dict, Optional

class TemplateHologramme:
    """Un template d'hologramme pré-rempli."""
    
    def __init__(self, nom: str, domaine: str, icone: str,
                 description: str, exemples: List[Dict[str, str]],
                 questions_type: List[str]):
        self.nom = nom
        self.domaine = domaine
        self.icone = icone
        self.description = description
        self.exemples = exemples  # [{'input': ..., 'target': ...}, ...]
        self.questions_type = questions_type  # Exemples de questions possibles
    
    def generer_hologramme(self, personnalisation: Optional[Dict] = None) -> List[Dict]:
        """Génère les exemples de l'hologramme avec personnalisation."""
        if not personnalisation:
            return self.exemples
        
        exemples = []
        for ex in self.exemples:
            inp = ex['input']
            tgt = ex['target']
            for k, v in personnalisation.items():
                inp = inp.replace('{' + k + '}', str(v))
                tgt = tgt.replace('{' + k + '}', str(v))
            exemples.append({'input': inp, 'target': tgt})
        return exemples


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATES PRÉ-REMPLIS
# ═══════════════════════════════════════════════════════════════════════════

TEMPLATES = [
    # ─── 1. SANTÉ / SUIVI MÉDICAL ───
    TemplateHologramme(
        nom="Santé & Bien-être",
        domaine="sante",
        icone="🏥",
        description="Votre santé, vos constantes, votre suivi médical personnalisé",
        exemples=[
            {"input": "Ma tension au repos est de 12/8", "target": "INIT(120) DIV(80)"},
            {"input": "Mon rythme cardiaque au repos est 68 BPM", "target": "INIT(68)"},
            {"input": "Je cours 30 minutes par jour, je perds 300 calories", "target": "INIT(30) MUL(10)"},
            {"input": "Mon poids est 75 kg, je veux perdre 5 kg", "target": "INIT(75) SUB(5)"},
            {"input": "Je dors 7 heures par nuit", "target": "INIT(7)"},
        ],
        questions_type=[
            "Quelle est ma tension idéale ?",
            "Combien de calories je brûle en courant ?",
            "Quel poids vise-je ?",
        ]
    ),

    # ─── 2. FINANCES PERSONNELLES ───
    TemplateHologramme(
        nom="Finances & Budget",
        domaine="finance",
        icone="💰",
        description="Votre budget, vos dépenses, vos investissements personnels",
        exemples=[
            {"input": "Mon salaire mensuel est 3000 euros", "target": "INIT(3000)"},
            {"input": "Mon loyer est 800 euros par mois", "target": "INIT(800) MUL(12)"},
            {"input": "J'épargne 10% de mon salaire chaque mois", "target": "INIT(3000) MUL(0.1) MUL(12)"},
            {"input": "Mes charges fixes mensuelles sont 1200 euros", "target": "INIT(1200) MUL(12)"},
            {"input": "J'ai un investissement de 5000 euros qui rapporte 5%", "target": "INIT(5000) MUL(0.05)"},
        ],
        questions_type=[
            "Combien j'épargne par an ?",
            "Quel est mon loyer annuel ?",
            "Combien me rapportent mes investissements ?",
        ]
    ),

    # ─── 3. RELATIONS & PROCHES ───
    TemplateHologramme(
        nom="Relations & Proches",
        domaine="relations",
        icone="💜",
        description="Vos contacts, leurs anniversaires, vos relations importantes",
        exemples=[
            {"input": "Sophie est ma compagne, anniversaire le 12 mars", "target": "INIT(1203)"},
            {"input": "Mon père s'appelle Jean, anniversaire le 5 juillet", "target": "INIT(507)"},
            {"input": "Ma mère s'appelle Marie, anniversaire le 23 novembre", "target": "INIT(2311)"},
            {"input": "Mon meilleur ami est Thomas, anniversaire le 30 janvier", "target": "INIT(3001)"},
            {"input": "Ma sœur s'appelle Julie, anniversaire le 18 septembre", "target": "INIT(1809)"},
        ],
        questions_type=[
            "Quel est l'anniversaire de Sophie ?",
            "Qui est né en mars ?",
            "Rappelle-moi les anniversaires de cette semaine",
        ]
    ),

    # ─── 4. MÉMOIRE & SOUVENIRS ───
    TemplateHologramme(
        nom="Mémoire & Souvenirs",
        domaine="memoire",
        icone="🧠",
        description="Vos voyages, vos moments importants, votre histoire",
        exemples=[
            {"input": "Voyage à Rome avec Sophie du 14 au 17 septembre 2024", "target": "INIT(20240914) ADD(3)"},
            {"input": "J'ai visité Tokyo en mars 2023 pendant 10 jours", "target": "INIT(202303) ADD(10)"},
            {"input": "Mariage le 20 juin 2020", "target": "INIT(20200620)"},
            {"input": "Achat de la maison le 15 janvier 2022 pour 250000 euros", "target": "INIT(20220115) MUL(250000)"},
            {"input": "Naissance de mon fils le 8 octobre 2023", "target": "INIT(20231008)"},
        ],
        questions_type=[
            "Quand est-ce que je suis allé à Rome ?",
            "Combien de jours as-tu passés à Tokyo ?",
            "Quelle est la date de mon mariage ?",
        ]
    ),

    # ─── 5. TRAVAIL & CARRIÈRE ───
    TemplateHologramme(
        nom="Travail & Carrière",
        domaine="travail",
        icone="💼",
        description="Votre carrière, vos objectifs, vos projets professionnels",
        exemples=[
            {"input": "Mon salaire annuel est 45000 euros", "target": "INIT(45000)"},
            {"input": "Je travaille 35 heures par semaine", "target": "INIT(35) MUL(52)"},
            {"input": "J'ai 25 jours de congés par an", "target": "INIT(25)"},
            {"input": "Mon objectif d'épargne retraite est 500000 euros", "target": "INIT(500000)"},
            {"input": "Je consacre 5 heures par semaine à la formation", "target": "INIT(5) MUL(52)"},
        ],
        questions_type=[
            "Combien d'heures je travaille par an ?",
            "Quel est mon objectif d'épargne retraite ?",
            "Combien de jours de congés ai-je ?",
        ]
    ),

    # ─── 6. CUISINE & ALIMENTATION ───
    TemplateHologramme(
        nom="Cuisine & Alimentation",
        domaine="cuisine",
        icone="🍳",
        description="Vos recettes, vos régimes, vos préférences alimentaires",
        exemples=[
            {"input": "Recette de gâteau au chocolat : 200g chocolat, 100g beurre, 3 œufs", "target": "INIT(200) ADD(100) ADD(3)"},
            {"input": "Mon régime : 1800 calories par jour", "target": "INIT(1800)"},
            {"input": "Je bois 2 litres d'eau par jour", "target": "INIT(2)"},
            {"input": "Recette de pâtes : 300g pâtes, 200g sauce tomate", "target": "INIT(300) ADD(200)"},
            {"input": "Je mange 5 fruits et légumes par jour", "target": "INIT(5)"},
        ],
        questions_type=[
            "Quelle est ma recette de gâteau au chocolat ?",
            "Combien de calories par jour ?",
            "Quels sont mes ingrédients pour les pâtes ?",
        ]
    ),

    # ─── 7. PROJETS & OBJECTIFS ───
    TemplateHologramme(
        nom="Projets & Objectifs",
        domaine="projets",
        icone="🎯",
        description="Vos objectifs, vos projets, vos résolutions",
        exemples=[
            {"input": "Objectif : lire 20 livres en 2025", "target": "INIT(20)"},
            {"input": "Projet : économiser 10000 euros pour un voyage", "target": "INIT(10000)"},
            {"input": "Objectif sport : courir 500 km dans l'année", "target": "INIT(500)"},
            {"input": "Projet professionnel : lancer mon entreprise en 2026", "target": "INIT(2026)"},
            {"input": "Objectif : apprendre le piano, 30 minutes par jour", "target": "INIT(30) MUL(365)"},
        ],
        questions_type=[
            "Combien de livres je veux lire ?",
            "Quel est mon objectif d'épargne voyage ?",
            "Combien de minutes de piano par an ?",
        ]
    ),

    # ─── 8. DÉCISIONS & CHOIX ───
    TemplateHologramme(
        nom="Aide à la Décision",
        domaine="decision",
        icone="🤔",
        description="Comparez des options, pesez le pour et le contre",
        exemples=[
            {"input": "Option A : appartement 800€/mois, 35m², centre-ville", "target": "INIT(800) MUL(35)"},
            {"input": "Option B : maison 1000€/mois, 70m², banlieue", "target": "INIT(1000) MUL(70)"},
            {"input": "Option C : studio 600€/mois, 25m², proche travail", "target": "INIT(600) MUL(25)"},
            {"input": "Comparaison A vs B : 28000 points vs 70000", "target": "INIT(28000) SUB(70000)"},
            {"input": "Comparaison A vs C : 28000 points vs 15000", "target": "INIT(28000) SUB(15000)"},
        ],
        questions_type=[
            "Quel logement a le meilleur rapport qualité-prix ?",
            "Compare l'option A et l'option B",
            "Quelle est la meilleure option pour moi ?",
        ]
    ),
]


def initialiser_hologrammes_personnels(nom_utilisateur: str = "Moi") -> List[dict]:
    """Génère les hologrammes pré-remplis pour un nouvel utilisateur.
    
    Retourne une liste de dicts prêts à être utilisés par hologramme.py
    """
    personnalisation = {
        "NOM": nom_utilisateur,
        "A": str(random.randint(3000, 5000)),  # salaire
    }
    
    generes = []
    for t in TEMPLATES:
        exemples = t.generer_hologramme(personnalisation)
        generes.append({
            'nom': t.nom,
            'icone': t.icone,
            'description': t.description,
            'exemples': exemples,
            'questions_type': t.questions_type,
        })
    return generes


def afficher_templates():
    """Affiche les templates disponibles."""
    print(f"{'═'*60}")
    print(f"  HOLOGRAMMES PRÉ-REMPLIS POUR KA — {len(TEMPLATES)} TEMPLATES")
    print(f"{'═'*60}\n")
    
    for t in TEMPLATES:
        print(f"  {t.icone} {t.nom} ({t.domaine})")
        print(f"     {t.description}")
        print(f"     Exemples : {len(t.exemples)}")
        print(f"     Questions types : {t.questions_type[0]}")
        print()


if __name__ == '__main__':
    afficher_templates()
    # Générer les hologrammes pour un utilisateur
    mes_hologrammes = initialiser_hologrammes_personnels()
    print(f"  8 hologrammes générés pour vous — prêts à personnaliser !\n")
    for h in mes_hologrammes:
        print(f"  {h['icone']} {h['nom']} : {len(h['exemples'])} exemples")
    print(f"\n  8 hologrammes — 40 exemples — prêts en 0 seconde")