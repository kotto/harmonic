---
name: wave-orchestrator
description: >-
  Orchestrer l'écosystème ondulatoire : lire les tables d'équivalence comme cahier des charges,
  détecter les gaps (modules manquants, adaptateurs absents), router vers les skills appropriés
  (wave-bridge, wave-code-generator, wave-ir-compiler, langage-ondulatoire, harmonic-hardware),
  et maintenir la cohérence globale. Utilise ce skill dès que l'utilisateur veut vérifier l'état
  de l'écosystème, combler des lacunes, synchroniser les tables d'équivalence, ou orchestrer
  plusieurs skills ondulatoires.
---

# Wave Orchestrator — Chef d'orchestre de l'écosystème ondulatoire

Le **Wave Orchestrator** est le meta-skill qui unifie tout l'écosystème ondulatoire.
Il lit les tables d'équivalence comme un « cahier des charges exécutable », détecte les
écarts, et active les skills appropriés pour les combler.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     WAVE ORCHESTRATOR                               │
│                                                                     │
│  1. LIT les tables d'équivalence                                    │
│     ┌──────────────────────────────────────────────────────────┐   │
│     │ TRADUCTION_ONDULATOIRE_LLM.md  (36 équivalences)         │   │
│     │ TRADUCTION_ONDULATOIRE_TTS.md  (25 équivalences)         │   │
│     │ BENCHMARK_COMPARATIF.md        (HPU vs CPU vs QPU)       │   │
│     └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  2. DÉTECTE les gaps                                                │
│     ├── Modules marqués 🆕 (à créer)                                │
│     ├── Modules sans adaptateur wave-bridge                         │
│     ├── Intentions non couvertes par wave-code-generator            │
│     └── Documents orphelins (git seulement, pas dans le workspace)  │
│                                                                     │
│  3. ROUTE vers les skills appropriés                                │
│     ├── 🆕 → wave-code-generator (générer le squelette)             │
│     ├── Module legacy → wave-bridge (créer adaptateur)              │
│     ├── Code à optimiser → wave-ir-compiler                         │
│     ├── Question NL → wave-code-generator                           │
│     └── Hardware/HPU → harmonic-hardware                            │
│                                                                     │
│  4. MET À JOUR les tables                                           │
│     └── 🆕 → ✅ avec le nom du fichier créé                        │
│                                                                     │
│  5. VÉRIFIE la cohérence globale                                    │
│     ├── Tous les modules listés existent-ils ?                      │
│     ├── Les adaptateurs couvrent-ils tous les domaines ?            │
│     └── Les skills sont-ils synchronisés avec les tables ?          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Écosystème de skills

| Skill | Rôle | Domaine |
|-------|------|---------|
| `langage-ondulatoire` | 13 primitives universelles | Fondation |
| `wave-bridge` | 14 adaptateurs drop-in (7 TTS + 7 LLM) | Adaptation |
| `wave-code-generator` | NL → 10 intentions → AST → code | Génération |
| `wave-ir-compiler` | Parse → AST → Optimize → Execute | Compilation |
| `harmonic-hardware` | Benchmarks HPU, projections matérielles | Hardware |

## Tables d'équivalence (sources de vérité)

| Table | Équivalences | Dernière synchro |
|-------|-------------|-----------------|
| `TRADUCTION_ONDULATOIRE_LLM.md` | 36 LLM → Ondulatoire | 2026-08-02 |
| `TRADUCTION_ONDULATOIRE_TTS.md` | 25 TTS → Ondulatoire | Original |
| `ordinateur_harmonique/BENCHMARK_COMPARATIF.md` | HPU PFLOPS | 2026-08-02 (restauré) |
| **`DOCUMENT_FONDATEUR_LLM_ONDULATOIRE.md`** | **Modèle idéal (10 couches, 8 principes, registre des 28 composants)** | **2026-08-02** |

## État actuel de l'écosystème

| Indicateur | Valeur |
|---|---|
| Modules LLM existants | 35/36 |
| Modules LLM manquants | 1 (`feedback_loop.py`) |
| Adaptateurs wave-bridge | 14 (7 TTS + 7 LLM) |
| Intentions wave-code-generator | 10 |
| Skills actifs | 5 |
| Domaines couverts | LLM, TTS, Audio, Protéines, HPU |

## Commandes

### Vérifier l'état de l'écosystème
```
wave-orchestrator status
```
→ Affiche le statut de chaque table, les gaps, et la couverture des skills.

### Mode CI (gates de release)
```
wave-orchestrator status --check           # exit 0 si cohérent, 1 si gaps
wave-orchestrator status --check --verbose # rapport complet + exit code
wave-orchestrator verify                   # lance wave-validator (3 niveaux)
```
→ Dans un pipeline CI : `python orchestrator.py status --check` bloque la release
si des gaps existent. `verify` exécute le validator complet (primitives + adaptateurs + tables).

### Combler un gap spécifique
```
wave-orchestrator fill --gap feedback_loop.py
```
→ Détecte que c'est un module 🆕, route vers wave-code-generator.

### Synchroniser toutes les tables
```
wave-orchestrator sync
```
→ Vérifie chaque équivalence, met à jour les statuts, détecte les fichiers orphelins.

### Créer les adaptateurs manquants pour un domaine
```
wave-orchestrator bridge --domain LLM
```
→ Détecte les modules LLM sans adaptateur, route vers wave-bridge.

## État actuel de l'écosystème (2 août 2026)

| Indicateur | Valeur |
|---|---|
| Modules LLM existants | **36/36 (100%)** |
| Adaptateurs wave-bridge | **19** (7 TTS + 12 LLM) |
| Intentions wave-code-generator | 10 |
| Skills actifs | 7 (dont wave-validator) |
| Tests wave-validator | 100/100 |
| Domaines couverts | LLM, TTS, Audio, Protéines, HPU |

## Référence

Voir `references/equivalence-registry.md` pour le registre complet des équivalences
et leur mapping vers les skills.
