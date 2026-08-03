# 🎨 VISUELS — Ce qu'il faut créer pour les réseaux

Chaque visuel doit tenir en une phrase et se partager sans contexte.

## 1 · La carte du défi (le visuel principal)

> **« 2^40 = ? »**
> GPT-4o : (réponse réelle collectée)
> KA Enterprise : **1 099 511 627 776 — exact, en 1 ms, 0 GPU**

Format carré (1:1), fond sombre #0a0a0f, or #c9a84c. Deux colonnes :
les LLM d'un côté (leurs réponses réelles aux 33 calculs), KA de
l'autre (33/33). C'est le visuel de partage principal.

## 2 · Le comparatif certitude (infographie)

Le tableau COMPARATIF_CERTITUDE.md en infographie : 6 lignes maximum —
Calcul exact 100 % vs variable · Refus vs hallucination · Déterminisme
100 % · Sources systématiques · 20 €/mois vs par token · 0 GPU vs
milliards.

## 3 · La question piège (la vidéo de 30 secondes)

> « Quelle est la couleur du paradis fiscal ? »
> ChatGPT : « Le paradis fiscal… » (réponse plausible — fausse)
> KA Enterprise : « Je ne trouve pas cette information. »

Écran partagé, deux colonnes, la différence en direct. C'est LE moment
de vente en vidéo.

## 4 · Le 0 GPU (le visuel « impossible »)

Un Raspberry Pi (ou un VPS à 20 €) avec « 33/33 · 0 GPU · 0 paramètre
entraîné · < 10 Mo » — le contraste avec les datacenters. La presse
économique adore ce visuel.

## 5 · L'auto-apprentissage (le GIF de démo)

Dashboard KA Enterprise : une question sans réponse → 3 questions →
l'enrichissement se déclenche → la question répond. La boucle visible
en 20 secondes.

## 6 · Le post LinkedIn prêt (texte)

```
🧮 L'IA qui ne se trompe JAMAIS en calcul.

33 calculs exacts posés à KA Enterprise et aux IA généralistes :
grands nombres (2^40, factorielle 25), priorités, racines.

KA Enterprise : 33/33 — exact, déterministe, ~1 ms, 0 GPU.
[LLM testé] : X/33.

Pourquoi ? KA Enterprise ne génère pas : elle CALCULE, elle rappelle,
elle VÉRIFIE — et elle refuse quand elle ne sait pas.

Testez : [lien /defi-calcul]
#IA #CalculExact #ZeroHallucination #0GPU #Souveraineté
```

(le post est généré automatiquement avec les chiffres réels par
`python benchmark_compare_llm.py`)

## 7 · Le logo du défi

Un « = » exact avec la mention « vérifié » : le symbole de la catégorie
— la preuve au lieu de la plausibilité.
