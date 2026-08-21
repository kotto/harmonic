---
name: langage-ondulatoire
description: >-
  Écrire, lire et exécuter des programmes en langage ondulatoire (Théorie Harmonique Universelle,
  ordinateur harmonique, Univers-Holistique). Utilise ce skill dès que l'utilisateur veut exprimer
  un problème « en ondes », manipuler les primitives encode/bind/superpose/resonate/interfere/emerge,
  écrire un programme ENCODE → QUERY → DECODE, encoder un concept en vecteur d'onde ℂ⁵¹², traduire
  un mot/un fait/un concept en onde, ou mentionne le langage ondulatoire, les primitives universelles,
  les hologrammes de connaissances, le langage harmonique, φ-spacing, binding HRR, noyau ABC —
  même s'il ne dit pas explicitement « écris un programme ondulatoire ».
---

# Langage Ondulatoire — écrire des programmes en ondes

Le langage ondulatoire est la langue de l'ordinateur harmonique : un langage de programmation dont
toutes les primitives sont des opérations sur des ondes. Tout problème se résout en **trois temps** :

```
ENCODE → MANIPULER → DÉCODER
(monde → ψ)  (ψ → ψ')   (ψ' → solution)
```

Les vecteurs d'onde vivent dans **ℂ⁵¹²** (limite de Bekenstein) ; ils sont toujours **normalisés**
(‖ψ‖ = 1, l'information est dans la direction). L'implémentation de référence vit dans
`vital-ka/core/python/wave_lang.py` (+ `wave_ir.py`, `wave_compiler.py`).

## Quand utiliser ce skill

- L'utilisateur veut écrire ou corriger un programme ondulatoire (texte en `ENCODE`/`BIND`/`QUERY`…).
- Il faut encoder un concept (mot, fait, phonème, entité) en vecteur d'onde, ou décoder une onde en concept.
- Il faut choisir la ou les primitives adaptées à un problème (mémoire, raisonnement, créativité, comparaison…).
- Il faut lire un programme ondulatoire existant et expliquer ce qu'il fait.

## Les 13 primitives (aperçu)

| # | Primitive | Rôle |
|---|---|---|
| 1 | `encode(entité)` | monde → ψ (déterministe : FNV-1a + φ-spacing) |
| 2 | `decode(ψ)` | ψ → entité (plus proche voisin dans le vocabulaire) |
| 3 | `bind(a, b)` | lie deux concepts (convolution circulaire, réversible) |
| 4 | `unbind(c, b)` | délie : `unbind(bind(a,b), b) ≈ a` |
| 5 | `superpose(...)` | additionne des ondes (mémoire holographique) |
| 6 | `resonate(a, b)` | similarité ∈ [-1, 1] (attention, retrieval, diagnostic) |
| 7 | `rotate(ψ, θ)` | change de perspective, préserve la norme |
| 8 | `normalize(ψ)` | projection sur le cercle unité |
| 9 | `interfere(a, b, ε)` | mélange contrôlé — primitive de **créativité** |
| 10 | `diffract(ψ)` | FFT (dualité temps-fréquence) |
| 11 | `filter(ψ, cutoff)` | passe-bas / haut / bande |
| 12 | `phase_shift(ψ, Δ)` | décalage de phase par dimension |
| 13 | `emerge(..., temperature)` | émergence pondérée par cohérence mutuelle |

Primitives avancées : `oppose(a, b)` (contraste), `amplify(ψ, comp, boost)` (faire émerger l'invisible),
`bind_many(a, b, c, ...)` (faits complexes), `coherence(a, b)` (similarité non-directionnelle).

## Règles d'écriture

1. **Tout est normalisé.** Chaque primitive retourne un ψ avec ‖ψ‖ = 1 — ne normalise pas deux fois.
2. **Déterminisme.** Même entité → même ψ, sur n'importe quelle machine. Ne pas mélanger hash aléatoire.
3. **Un programme = 3 temps.** Si un programme n'a pas de `ENCODE` en tête ou de `DECODE` en queue, c'est
   probablement incomplet : vérifie que le monde entre et sort du domaine ondulatoire.
4. **Structure des faits :** un fait est `bind_many(sujet, relation, objet, [contexte])` — délier se fait
   avec `unbind` sur la relation ou le sujet.
5. **Le décodage a besoin d'un vocabulaire** : `decode` cherche le plus proche voisin parmi les entités
   connues. Si le vocabulaire manque, l'utilisateur doit le fournir (ex. `encode_many([...])`).
6. **Choix de primitive par intention** (raccourci : voir le skill `wave-code-generator`) :
   - question → `encode` → `query` (résonance sur l'hologramme) → `decode`
   - raisonnement → `superpose` + `emerge`
   - créativité → `interfere` (ε ≈ 0.15 pour une connexion subtile)
   - comparaison → `resonate` + `oppose`
   - analogie → `bind` + `unbind`

## Exemple canonique

```
ψ_q = ENCODE "Qu'est-ce que la lumière ?"
QUERY ψ_r = ψ_q FROM H_connaissances
reponse = DECODE(ψ_r)
RETURN reponse
```

## Exécuter un programme

Deux chemins, selon ce que l'utilisateur fournit :

1. **Code ondulatoire (texte)** → parse + compile + exécute :
   ```python
   from wave_ir import parse
   from wave_compiler import WaveCompiler
   program = parse(source)            # source = texte en ENCODE/BIND/QUERY...
   ast = WaveCompiler().compile(program)  # 4 passes d'optimisation
   env = WaveCompiler().execute(program, holograms={"H_connaissances": mem})
   ```
Les modules `wave_ir` / `wave_compiler` sont dans `vital-ka/core/python/`. Pour les importer,
ajouter au `sys.path` les 3 dossiers suivants (ensemble minimal vérifié) :
`vital-ka/core/python`, `vital-ka/backend/hologram` (holographic_encoder), `vital-ka/backend/inference`
(prompt_parser).

2. **Primitives directes** (calcul en une passe, sans passer par le texte) :
   ```python
   from wave_lang import encode, decode, bind, resonate, superpose, HolographicMemory
   ψ_question = encode("Qu'est-ce que la lumière ?")
   mem = HolographicMemory()
   mem.store(encode("lumière"), encode("est"), encode("une onde électromagnétique"))
   ψ_réponse = mem.query(ψ_question)
   ```

## Vérification

- Valide les invariants : `‖encode(x)‖ = 1`, `resonate(encode(x), encode(x)) = 1.0`.
- Vérifie les valeurs de référence du document fondateur : `unbind(bind(a,b), b)` → recovery ≥ 0.7 ;
  `rotate(ψ, π)` → resonance -1.0 ; `phase_shift(ψ, π/2)` → orthogonal (0.0).
- Si le programme passe par le texte : roundtrip `parse(print) ` bit-à-bit identique (voir
  `wave-ir-compiler`).

## Détails

- Tableau complet des 13 primitives (formules, domaines d'usage, ε typiques) : `references/primitives.md`
- Fondements : ℂ⁵¹², φ-spacing (1.618…), binding HRR (Plate 1995), noyau ABC (α = 1/φ ≈ 0.618).
