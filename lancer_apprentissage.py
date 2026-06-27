#!/usr/bin/env python3
"""Lance l'apprentissage récursif sur 10 questions et persiste l'état."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from assistant_final_harmonique import AssistantFinal
from moteur_apprentissage_recursif import ApprentissageRecursif

print("=" * 70)
print("APPRENTISSAGE RÉCURSIF — Session d'entraînement")
print("=" * 70)
print()

# Initialiser
assistant = AssistantFinal()
assistant.initialiser()
apprentissage = ApprentissageRecursif()
print()

questions = [
    "quelle est la constante de Planck",
    "qui a découvert la relativité",
    "comment fonctionne la photosynthèse",
    "quelle est la vitesse de la lumière",
    "qu'est-ce que le Big Bang",
    "qui est Albert Einstein",
    "quelle est la masse de l'électron",
    "qu'est-ce que l'entropie en thermodynamique",
    "qui a formulé la théorie de l'évolution",
    "qu'est-ce que le boson de Higgs",
]

print("=" * 70)
print("APPRENTISSAGE SUR 10 QUESTIONS")
print("=" * 70)
print()

scores = []
for i, q in enumerate(questions):
    reponse, domaine = assistant.repondre(q)
    resultats = assistant.faits.rechercher(q, top_k=5)
    faits_sources = [r[0] for r in resultats]
    
    score = apprentissage.evaluer_et_apprendre(q, reponse, faits_sources, domaine or "general")
    scores.append(score)
    
    emoji = "✅" if score > 0.6 else "⚠️" if score > 0.4 else "❌"
    print(f"  {emoji} Q{i+1}: score={score:.2f} | domaine={domaine}")
    print(f"     {reponse[:120]}...")
    print()

# Stats finales
print("=" * 70)
print("RÉSULTATS DE L'APPRENTISSAGE")
print("=" * 70)
stats = apprentissage.stats()
for k, v in stats.items():
    print(f"  {k}: {v}")
print(f"  score_session: {sum(scores)/len(scores):.3f}")
print(f"  état sauvegardé: data/apprentissage_harmonique.json")
print()

# Test de la mémoire
print("=" * 70)
print("TEST — LE SYSTÈME A-T-IL APPRIS ?")
print("=" * 70)
print()
print("Faits les plus fiables appris :")
fiables = sorted(apprentissage.fiabilite_faits.items(), key=lambda x: x[1], reverse=True)[:5]
for h, score in fiables:
    # Chercher le texte correspondant
    for c in assistant.faits.connaissances[:1000]:
        if apprentissage._hash_texte(c['texte']) == h:
            print(f"  [{score:.3f}] {c['texte'][:100]}...")
            break

print()
print("=" * 70)
print("✅ APPRENTISSAGE TERMINÉ")
print("=" * 70)