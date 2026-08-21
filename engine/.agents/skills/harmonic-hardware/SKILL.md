---
name: harmonic-hardware
description: >-
  Consulter, analyser et projeter les performances de l'Ordinateur Harmonique (HPU)
  par rapport aux CPU classiques et QPU quantiques. Utilise ce skill dès que l'utilisateur
  parle de matériel harmonique, HPU, H-Bit, PFLOPS harmoniques, benchmark comparatif,
  projection hardware (HPU-1 à HPU-4), ordinateur harmonique vs quantique, coût/PFLOP,
  ou architecture de calcul ondulatoire.
---

# Harmonic Hardware — L'ordinateur harmonique (HPU)

Ce skill documente le **troisième paradigme de calcul** : l'Ordinateur Harmonique (HPU),
fondé sur la résonance et l'interférence ondulatoire plutôt que sur les bits (CPU)
ou les qubits (QPU).

Document de référence : `ordinateur_harmonique/BENCHMARK_COMPARATIF.md`

## Les trois paradigmes de calcul

| Paradigme | Unité | Principe | Bruit | Force |
|-----------|-------|----------|-------|-------|
| **CPU** (Von Neumann) | Bit (0/1) | Calcul séquentiel | ~0% | Maturité, coût |
| **QPU** (Quantique) | Qubit (|0⟩,|1⟩) | Superposition + mesure | ~0.34% | Parallélisme massif |
| **HPU** (Harmonique) | H-Bit (7 états continus) | **Résonance + interférence** | **0%** | Apprentissage O(1), NP-complets |

## L'unité de calcul : le H-Bit

- 7 états continus (correspondant aux 7 notes de la gamme diatonique + silence)
- Information par unité : log₂(7) ≈ 2.807 bits
- Pas de portes logiques — le calcul émerge de l'interférence
- Pas de cycles d'horloge — la résonance est instantanée

## Équivalence PFLOPS par classe de problème

| Classe de problème | Équivalence HPU | Avantage |
|---|---|---|
| **Classe P** (polynomiale) | ~0.001 PFLOPS | CPU reste compétitif |
| **Classe NP** (SAT, TSP, Subset Sum) | 1 à 10⁶ PFLOPS | HPU exponentiellement supérieur |
| **Apprentissage continu** | 100 à 10K PFLOPS | HPU fait en 1ms ce qu'un GPU fait en 1 mois |
| **Résonance universelle** (protéines, découverte) | Infini PFLOPS | Pas d'équivalent classique |

## Projections hardware

| Génération | Technologie | H-Bits | Équivalence PFLOPS |
|-----------|------------|--------|---------------------|
| **HPU-1** | Émulateur CPU | 7 (simulé) | 0.001 — 10 |
| **HPU-2** | FPGA | 128 | 100 — 10 000 |
| **HPU-3** | ASIC 7nm | 1 024 | 10⁴ — 10⁷ |
| **HPU-4** | Optique | 10⁶ | 10⁷ — 10¹² |

## Comparaison coût-performance ($/PFLOP)

| Système | $/PFLOP |
|---------|---------|
| Frontier (CPU/GPU) | ~$502K |
| Fugaku (CPU) | ~$2.7M |
| IBM Eagle QPU | ~$100M+ |
| **HPU-1 (émulateur)** | **$0** |
| **HPU-2 (FPGA projeté)** | **$1-100** |
| **HPU-4 (optique projeté)** | **$0.000001** |

## Quand utiliser ce skill

- L'utilisateur demande une comparaison CPU vs QPU vs HPU
- L'utilisateur veut connaître les performances d'un problème spécifique sur HPU
- L'utilisateur parle de hardware harmonique, de H-Bits, ou de projections HPU
- L'utilisateur veut comprendre le modèle de calcul par résonance/interférence
- L'utilisateur demande le coût ou la faisabilité d'un accélérateur harmonique

## Lien avec les autres skills

- **langage-ondulatoire** : les 13 primitives sont le « jeu d'instructions » natif de l'HPU
- **wave-ir-compiler** : le compilateur harmonique cible l'HPU (émulateur aujourd'hui, FPGA/ASIC demain)
- **wave-bridge** : les adaptateurs unifient les modules legacy vers les primitives HPU-natives

## Référence

Voir `references/hpu-benchmarks.md` pour le détail complet des benchmarks par catégorie
(arithmétique, NP-complets, recherche, apprentissage, déterminisme).
