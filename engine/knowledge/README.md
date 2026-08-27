# KA Knowledge Wiki — Source de Vérité (format OKF-like)

> **Format d'auteur** de la connaissance de KA. Inspiré du pattern « LLM Wiki »
> (Andrej Karpathy) et de l'Open Knowledge Format (OKF) de Google Cloud.
>
> Ce dossier est la **vérité organisationnelle** : lisible, revue (git),
> déterministe. Il est **compilé** en hologrammes wave-native ℂ⁵¹² par
> `okf_compiler.py` — jamais l'inverse.

---

## Pourquoi ce format ?

| Problème (RAG / vector DB) | Solution (ce wiki) |
|----------------------------|--------------------|
| Chunks + embeddings chaotiques | Fichiers Markdown structurés |
| Recherche approximative | Lecture déterministe du chemin |
| Boîte noire, difficile à auditer | Git, diff, revue humaine |
| Hallucination (recomposition) | Faits exacts, lus tels quels |
| Vérité dupliquée | Une source canonique par concept |

Le pipeline de KA devient :

```
knowledge/*.md  ──(compile)──►  hologramme ℂ⁵¹²  ──(rappel)──►  réponse
   source de vérité              format d'exécution            zéro hallucination
   lisible + versionnée          rapide + offline              cohérence vérifiée
```

---

## Structure

```
knowledge/
├── README.md          # ce fichier (la spec)
├── .schema.json       # schéma JSON de validation
├── phys/              # Physique
│   ├── hologramme.md
│   ├── lumiere.md
│   └── ...
├── astro/             # Astronomie
├── bio/               # Biologie
├── info/              # Informatique
├── geo/               # Géographie
├── chimie/            # Chimie
├── math/              # Mathématiques
└── medecine/          # Médecine
```

Le nom du dossier = le **domaine**. Le nom du fichier = l'**id** du concept.

---

## Format d'un fichier

Frontmatter YAML (délimité par `---`), puis le corps avec les faits.

```markdown
---
id: lumiere
domain: physique
title: La Lumière
type: concept
---

# La Lumière

- lumiere | est une | onde electromagnetique
- lumiere | est composee de | photons
- lumiere | a pour vitesse | 299 792 458 metres par seconde dans le vide
```

### Règles

1. **Frontmatter obligatoire** : `id`, `domain`, `title`. Optionnel : `type`.
2. **Un fait par ligne** au format `sujet | relation | objet` (pipe séparateur).
3. **Sans accents** dans les faits (le pipeline wave normalise les accents).
4. **Une seule vérité par concept** : si deux fichiers définissent le même
   triplet, le compilateur signale un conflit (dédoublonnage).
5. **Relations verbales** de préférence (`est une`, `a pour`, `cause`, …) —
   elles sont éligibles à la phraséologie naturelle (surface_grammar).

### Types de fichiers (champ `type`)

| `type` | Usage |
|--------|-------|
| `concept` | Définition d'un concept (`est une`, `signifie`, …) |
| `entity`  | Une entité (pays, personne, organisation) |
| `fact`    | Un fait isolé (pas une définition) |

---

## Compilation

```bash
# Compiler tout le wiki en hologrammes (un par domaine)
python ka_server/services/okf_compiler.py

# Valider uniquement (sans compiler)
python ka_server/services/okf_compiler.py --validate

# Lister les concepts présents
python ka_server/services/okf_compiler.py --list
```

Le compilateur :
1. Parcourt `knowledge/**/*.md`
2. Valide le frontmatter + les faits (contre `.schema.json`)
3. Encode chaque fait en ψ (binding HRR `ψ_s ⊛ ψ_r ⊛ ψ_o`)
4. Construit l'hologramme `H = Σ ψ_fait` par domaine
5. Sauvegarde NPZ + registre → prêt pour le rappel

---

## Cycle de vie

```
1. Auteur  : écrire/éditer un .md (git commit)
2. Revue   : pull request, relecture humaine, diff
3. Compile : okf_compiler.py → hologramme mis à jour
4. Exécute : rappel holographique (offline, < 1 ms)
```

**La source de vérité, c'est le Markdown.** L'hologramme n'est qu'un cache
compilé — il peut être reconstruit à tout moment, déterministiquement.
