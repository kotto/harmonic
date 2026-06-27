# Rapport de validation HCV SDI

## Contexte

Ce rapport présente les résultats de la validation initiale de la chaîne HCV SDI sur une vidéo déjà compressée en H.264 (`B3.mp4`). L'objectif était de vérifier si HCV pouvait atteindre un ratio de compression significatif tout en conservant une haute qualité visuelle.

## Objectif

- Valider la capacité de HCV SDI à recomprimer un flux vidéo H.264 existant.
- Mesurer le ratio de compression HCV / H.264.
- Vérifier la qualité de reconstruction à l'aide du PSNR.
- Confirmer que la référence RAW non compressée est une base valide.

## Méthode

- Vidéo d'entrée : `B3.mp4` (fichier H.264 déjà compressé)
- Nombre de frames utilisé pour le test : 10
- Format interne : simulation SDI YUV 4:2:2 10-bit
- Référence chromatique utilisée : les composantes Cb/Cr du premier frame
- Entropie codée avec Zstandard
- Paramètres de quantification : QP = 3

## Résultats actuels

- Taille originale H.264 : **11,31 MB**
- Taille du flux HCV compressé : **1,33 MB**
- Ratio `Original H.264 -> HCV` : **8,51×**
- PSNR Y moyen : **51,22 dB**

## Interprétation

- Le ratio obtenu est très élevé pour un flux déjà compressé.
- Le PSNR de 51 dB indique une reconstruction de très haute qualité, bien au-dessus de l'objectif de 40 dB.
- La comparaison est effectuée avec une base H.264 déjà optimisée, ce qui renforce la valeur du résultat.

## Référence RAW

- La référence RAW non compressée est déjà validée et constitue la base ultime de qualité.
- La preuve de concept actuelle ne vise pas à concurrencer directement le RAW, mais à démontrer que HCV peut surpasser un flux H.264 compressé tout en préservant une excellente qualité.

## Limites actuelles

- Le test a porté uniquement sur **10 frames**.
- Il faut confirmer ces résultats sur un échantillon plus large, idéalement sur toute la vidéo.
- Le ratio et le PSNR peuvent varier selon le contenu et le mode de compression.
- L’algorithme est encore expérimental et demande une validation complète en production.

## Conclusions

- Le résultat actuel est très prometteur et justifie la poursuite du développement.
- Si la performance se confirme sur des tests complets, cela représente une avancée majeure.
- Le rapport RAW fournit une référence qualité solide pour toutes les validations futures.

## Prochaines étapes recommandées

1. Exécuter la validation sur un nombre plus important de frames (50, 100, ou toute la vidéo).
2. Comparer directement avec le RAW non compressé pour mesurer la qualité absolue.
3. Étendre les tests à des contenus divers : studio, natural, textures complexes.
4. Formaliser un tableau de ratios et PSNR par mode de compression.
5. Préparer un benchmark de performance pour évaluer le temps d'encodage.
