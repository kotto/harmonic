#!/usr/bin/env python3
"""
Vérification des résultats de compression
"""

# Données affichées
original_mb = 4.41
compressed_mb = 2.81
ratio_displayed = 184.50
space_saving_displayed = 99.5

# Calculs corrects
ratio_correct = original_mb / compressed_mb
space_saving_correct = ((original_mb - compressed_mb) / original_mb) * 100

print("=" * 60)
print("VÉRIFICATION DES RÉSULTATS DE COMPRESSION")
print("=" * 60)
print()
print("DONNÉES AFFICHÉES:")
print(f"  Fichier Original: {original_mb} MB")
print(f"  Fichier Compressé: {compressed_mb} MB")
print(f"  Ratio affiché: {ratio_displayed}:1")
print(f"  Économie affichée: {space_saving_displayed}%")
print()
print("CALCULS CORRECTS:")
print(f"  Ratio correct: {ratio_correct:.2f}:1")
print(f"  Économie correcte: {space_saving_correct:.1f}%")
print()
print("=" * 60)
print("ANALYSE:")
print("=" * 60)

if abs(ratio_correct - ratio_displayed) > 1:
    print(f"❌ ERREUR: Ratio de compression INCORRECT")
    print(f"   Affiché: {ratio_displayed}:1")
    print(f"   Correct: {ratio_correct:.2f}:1")
    print(f"   Différence: {ratio_displayed - ratio_correct:.2f}:1")
else:
    print(f"✓ Ratio de compression correct")

if abs(space_saving_correct - space_saving_displayed) > 1:
    print(f"❌ ERREUR: Économie d'espace INCORRECTE")
    print(f"   Affichée: {space_saving_displayed}%")
    print(f"   Correcte: {space_saving_correct:.1f}%")
    print(f"   Différence: {space_saving_displayed - space_saving_correct:.1f}%")
else:
    print(f"✓ Économie d'espace correcte")

print()
print("CONCLUSION:")
print("=" * 60)
if abs(ratio_correct - ratio_displayed) > 1 or abs(space_saving_correct - space_saving_displayed) > 1:
    print("⚠️  LES RÉSULTATS AFFICHÉS SONT INCORRECTS!")
    print()
    print("CAUSE PROBABLE:")
    print("Les métriques sont calculées sur les données COMPRESSÉES")
    print("au lieu des données ORIGINALES.")
    print()
    print("EXEMPLE:")
    print(f"  Si le fichier original était ~{ratio_displayed * compressed_mb:.1f} MB")
    print(f"  Alors le ratio {ratio_displayed}:1 serait correct")
    print()
    print("SOLUTION:")
    print("Vérifier la fonction get_metrics() dans web_app.py")
    print("pour s'assurer qu'elle utilise les bonnes tailles de fichier.")
else:
    print("✓ Les résultats affichés sont corrects")
