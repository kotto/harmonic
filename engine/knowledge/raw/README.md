# Sources brutes — Couche `raw/`

> La couche `raw/` contient les **documents sources immutables** qui ont
> servi à construire le wiki. Chaque fichier `.md` dans `knowledge/**/*.md`
> peut référencer sa source via le champ `source:` du frontmatter.

## Pourquoi une couche raw ?

Le pattern d'Andrej Karpathy (LLM Wiki) distingue trois couches :

| Couche | Rôle | Qui écrit | Modifiable ? |
|--------|------|-----------|--------------|
| `raw/` | Documents sources (articles, notes, extraits) | Humain | ❌ (immutable) |
| `knowledge/**/*.md` | Wiki compilé (concepts, faits) | Compilateur | ✅ (via --file) |
| Hologramme ℂ⁵¹² | Format d'exécution | `okf_compiler.py` | ❌ (régénéré) |

## Format d'un fichier source

Un fichier source peut être :
- Un article ou une note en Markdown
- Un extrait d'encyclopédie
- Un document PDF converti en Markdown
- N'importe quel texte structuré

Chaque source DOIT avoir un frontmatter avec au moins un `id` :

```markdown
---
id: wikipedia-hologramme
title: Hologramme — Wikipédia
url: https://fr.wikipedia.org/wiki/Hologramme
date: 2026-08-26
---

# Hologramme

Un hologramme est une figure d'interférence qui stocke une image...
```

## Traçabilité

Un fichier de connaissance dans `knowledge/**/*.md` référence sa source :

```markdown
---
id: hologramme
domain: physique
title: Hologramme
source: wikipedia-hologramme
---
```

Le compilateur OKF vérifie que la source référencée existe dans `raw/`.
Si elle manque, un avertissement est émis (pas une erreur bloquante).

## Index

`raw/index.md` liste toutes les sources disponibles, généré automatiquement
par `okf_compiler.py --validate`.