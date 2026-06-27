#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session d'Apprentissage Continue
==================================
Intègre l'apprentissage récursif dans l'assistant final
et lance une session d'entraînement multi-domaines.

Objectif : améliorer la qualité des réponses à chaque utilisation,
sans aucune supervision humaine.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import sys, os, time, json, glob, random
sys.path.insert(0, os.path.dirname(__file__))

from assistant_final_harmonique import AssistantFinal, DOMAINE_MOTS_CLES
from moteur_apprentissage_recursif import ApprentissageRecursif

class AssistantApprenant:
    """
    Assistant final avec apprentissage intégré.
    Chaque réponse améliore le système automatiquement.
    """
    
    def __init__(self):
        self.faits = None  # MoteurFaits
        self.langage = None  # MoteurLangage
        self.apprentissage = ApprentissageRecursif()
        self._initialise = False
    
    def initialiser(self):
        from assistant_final_harmonique import MoteurFaits
        from moteur_langage import MoteurLangage
        
        print("Initialisation de l'assistant apprenant...")
        self.faits = MoteurFaits()
        n = self.faits.charger()
        self.langage = MoteurLangage()
        print(f"  {n:,} connaissances | {len(self.faits.idf):,} mots IDF")
        
        stats = self.apprentissage.stats()
        if stats['iterations'] > 0:
            print(f"  Apprentissage : {stats['iterations']} itérations passées, "
                  f"score moyen {stats['score_moyen']:.3f}")
        print()
        self._initialise = True
        return n
    
    def repondre(self, question):
        """Répond ET apprend de la réponse donnée."""
        if not self._initialise:
            self.initialiser()
        
        # 1. Rechercher les faits
        resultats = self.faits.rechercher(question, top_k=5)
        faits_bruts = [r[0] for r in resultats]
        
        # 2. Filtrer via l'apprentissage (si des faits ont déjà été évalués)
        if self.apprentissage.iterations > 10:
            faits_filtres = self.apprentissage.filtrer_faits(
                [(f, r[2]) for f, _, r in zip(faits_bruts, resultats, resultats)]
            )
            if faits_filtres:
                faits_bruts = faits_filtres
        else:
            faits_bruts = [r[0] for r in resultats[:3]]
        
        # 3. Reformuler
        reponse = self.langage.reformuler(faits_bruts)
        
        # 4. Apprendre de cette réponse
        domaine = self.faits._detecter_domaine(question) or "general"
        score = self.apprentissage.evaluer_et_apprendre(
            question, reponse, faits_bruts, domaine
        )
        
        return reponse, domaine, score


def generer_questions_diverses(n=20):
    """Génère des questions variées couvrant plusieurs domaines."""
    
    # Questions par domaine
    questions_science = [
        "quelle est la constante de Planck",
        "qui a découvert la relativité",
        "comment fonctionne la photosynthèse",
        "qu'est-ce que l'entropie",
        "quelle est la vitesse de la lumière",
        "qu'est-ce que le boson de Higgs",
        "comment fonctionne la fission nucléaire",
        "qui est Marie Curie",
        "quelle est la masse du proton",
        "qu'est-ce que la supraconductivité",
        "comment fonctionne l'effet photoélectrique",
        "qui a découvert la structure de l'ADN",
        "qu'est-ce que le principe d'incertitude",
        "quelle est la charge de l'électron",
        "comment fonctionne un laser",
    ]
    
    questions_histoire = [
        "quand a eu lieu la Révolution française",
        "qui était Napoléon Bonaparte",
        "qu'est-ce que la Renaissance",
        "quand a commencé la Première Guerre mondiale",
        "qui a découvert l'Amérique",
    ]
    
    questions_geographie = [
        "quelle est la capitale de la France",
        "quel est le plus grand océan",
        "quelle est la population de la Chine",
        "quel est le plus haut sommet du monde",
        "dans quel pays se trouve le Sahara",
    ]
    
    # Mélanger et prendre n questions
    toutes = []
    toutes.extend([(q, "science") for q in questions_science])
    toutes.extend([(q, "histoire") for q in questions_histoire])
    toutes.extend([(q, "geographie") for q in questions_geographie])
    
    random.shuffle(toutes)
    return toutes[:n]


# ================================
# SESSION D'APPRENTISSAGE
# ================================
print("=" * 70)
print("SESSION D'APPRENTISSAGE CONTINUE")
print("Assistant auto-améliorant")
print("=" * 70)
print()

assistant = AssistantApprenant()
assistant.initialiser()

# Générer des questions variées
questions = generer_questions_diverses(n=25)
print(f"Session : {len(questions)} questions multi-domaines")
print()

scores = []
domaines_count = {}
for i, (q, domaine_attendu) in enumerate(questions):
    debut = time.time()
    reponse, domaine, score = assistant.repondre(q)
    duree = (time.time() - debut) * 1000
    
    scores.append(score)
    domaines_count[domaine] = domaines_count.get(domaine, 0) + 1
    
    emoji = "✅" if score > 0.7 else "⚠️" if score > 0.4 else "❌"
    print(f"  {emoji} #{i+1:02d} [{domaine:<12s}] score={score:.2f} | {duree:.0f}ms")
    print(f"     Q: {q}")
    print(f"     R: {reponse[:150]}...")
    print()

# ================================
# RÉSULTATS
# ================================
print("=" * 70)
print("RÉSULTATS DE LA SESSION")
print("=" * 70)
print()

stats = assistant.apprentissage.stats()
print(f"  Questions traitées : {len(scores)}")
print(f"  Score moyen        : {sum(scores)/len(scores):.3f}")
print(f"  Score min          : {min(scores):.3f}")
print(f"  Score max          : {max(scores):.3f}")
print(f"  Itérations totales : {stats['iterations']}")
print(f"  Faits appris       : {stats['faits_appris']}")
print(f"  Tendance           : {stats['tendance']}")
print(f"  Seuil adaptatif    : {stats['seuil_secondaire']:.3f}")
print()

print("Distribution par domaine :")
for dom, count in sorted(domaines_count.items(), key=lambda x: x[1], reverse=True):
    boost = assistant.apprentissage.boost_domaine_actuel(dom)
    print(f"  {dom:<15s} : {count} questions | boost={boost:.2f}")
print()

# Test : le système refuse-t-il les mauvais faits ?
print("=" * 70)
print("TEST DE FILTRAGE POST-APPRENTISSAGE")
print("=" * 70)
print()

faits_test = [
    ("Einstein a découvert le vaccin contre la rage.", 0.5),
    ("La constante de Planck h = 6.626×10⁻³⁴ J·s.", 0.9),
    ("La Terre est plate.", 0.1),
    ("Max Planck a introduit le quantum en 1900.", 0.7),
]
filtres = assistant.apprentissage.filtrer_faits(faits_test)
print(f"  Faits avant filtrage : {len(faits_test)}")
print(f"  Faits après filtrage : {len(filtres)}")
for f in filtres:
    fiab = assistant.apprentissage.fiabilite_fait(f)
    print(f"    [{fiab:.2f}] {f[:80]}...")
if len(filtres) < len(faits_test):
    print(f"  ❌ {len(faits_test) - len(filtres)} faits rejetés (peu fiables)")

print()
print("=" * 70)
print("✅ SESSION TERMINÉE — L'APPRENTISSAGE CONTINUE")
print("=" * 70)