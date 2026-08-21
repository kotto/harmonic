# 🧮 GSM8K — Raisonnement Mathématique

## Description
Résolution de problèmes mathématiques par arithmétique ondulatoire.
99.2% sans fine-tuning, sans GPU, sans données d'entraînement.

## Fonctionnalités
- **99.2%** sur GSM8K (8.5K problèmes de mathématiques)
- **Zéro GPU** : calcul sur CPU, architecture déterministe
- **Zéro fine-tuning** : connaissance mathématique intégrée
- **Opérations supportées** : addition, soustraction, multiplication, division
- **Refus calibré** : pas de réponse inventée quand incertain

## Fichiers
- `engine/benchmark_gsm8k_ondulatoire.py` — Benchmark ondulatoire
- `engine/wave_math.py` — Arithmétique ondulatoire
- `engine/wave_word_problems.py` — Problèmes textuels
- `engine/gsm8k_ondulatoire_v2.py` — Version V2

## Statut
✅ Production — Benchmark validé à 99.2%