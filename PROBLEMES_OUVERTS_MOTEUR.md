# 🔴 PROBLÈMES OUVERTS — Moteur de Raisonnement Ondulatoire

## Faiblesses actuelles formulées comme problèmes à résoudre

**Date :** 13 Juin 2026

---

## Problème 1 : PLONGEMENT SÉMANTIQUE À GRANDE ÉCHELLE

**Énoncé :** Le SSE (Spectral Semantic Embedding) fonctionne sur 4 concepts et 24 instances avec une similarité basée sur le partage de vocabulaire. Pour un moteur général, il faut plonger **des milliers de concepts** dans S¹ en préservant leur structure de voisinage sémantique.

**Contraintes :**
- Le plongement doit préserver : `sim(A,B) élevée ⇔ |θ(A)-θ(B)| faible`
- Doit fonctionner pour des concepts hors vocabulaire (noms propres, néologismes)
- Doit être calculable sans graphe de connaissances externe (ou avec un graphe léger)
- La phase θ(c) doit être stable : deux exécutions → même θ pour le même concept

**Question ouverte :** Comment obtenir une matrice de similarité W pour N concepts (N > 10 000) sans Word2Vec/GloVe pré-entraîné ? Peut-on utiliser les co-occurrences dans un corpus textuel brut (Wikipedia) pour construire W directement, puis appliquer Laplacian Eigenmaps ?

---

## Problème 2 : INSTABILITÉ DE L'EXPONENTIATION `(Ψ_a)^b`

**Énoncé :** La multiplication `a × b` est encodée comme `(Ψ_a)^b = exp(i·a·b·φ·2π·x/L)`. Mathématiquement correct, mais numériquement instable pour les grands nombres. L'exponentiation complexe accumule des erreurs d'arrondi qui déforment la phase.

**Contraintes :**
- Doit fonctionner pour `a, b ∈ [0, 1000]` au minimum
- Ne doit pas nécessiter de stockage explicite (principe d'émergence)
- La solution doit être compatible avec l'extraction DFT Harmonique

**Question ouverte :** Existe-t-il une opération ondulatoire stable pour la multiplication qui préserve la propriété d'émergence ? Par exemple : utiliser les logarithmes spectraux (`ln(Ψ_a) = i·a·φ·2π·x/L`) pour transformer la multiplication en addition dans l'espace logarithmique, puis exponentiater le résultat ?

---

## Problème 3 : RAISONNEMENT CONCEPTUEL MULTI-SAUTS

**Énoncé :** Le raisonnement « Quelle est la capitale du pays où se trouve Tombouctou ? » nécessite 2 sauts : (1) Tombouctou → Mali, (2) Mali → Bamako. Avec SHA-256, le moteur unifié échoue (interférences quasi-nulles). Avec SSE sur 4 concepts, le test n'a pas été fait.

**Contraintes :**
- Chaque saut doit modifier l'onde de manière cumulative : `Ψ_question → Ψ_1 → Ψ_2 → réponse`
- Le mécanisme doit être le même que pour l'arithmétique (évolution ABC+GAGUT)
- Doit fonctionner avec des concepts non vus pendant l'entraînement du plongement

**Question ouverte :** Comment encoder la relation « est situé dans » (Tombouctou → Mali) et « a pour capitale » (Mali → Bamako) de manière à ce que l'onde évolue naturellement de la question vers la réponse ? Faut-il un hologramme de relations (graphe de connaissances) où chaque fait est une onde, et le raisonnement est une propagation dans ce graphe ?

---

## Problème 4 : ÉMERGENCE DE PRÉDICATS SANS SUPERVISION

**Énoncé :** Le SSE démontre l'émergence du prédicat « est-capitale-de » par superposition de 4 instances. Mais ces instances ont été **sélectionnées manuellement**. Dans un système réel, comment le système découvre-t-il LUI-MÊME qu'un ensemble de phrases partage un prédicat commun ?

**Contraintes :**
- Pas de supervision humaine pour grouper les instances
- Le système doit détecter automatiquement les régularités spectrales
- Doit fonctionner sans connaissance a priori des prédicats existants

**Question ouverte :** Peut-on utiliser le clustering spectral sur les ondes des phrases pour faire émerger automatiquement les groupes d'instances qui partagent un prédicat ? Le Laplacian Eigenmaps appliqué aux phrases (pas aux concepts) ferait-il émerger les prédicats comme les vecteurs propres ?

---

## Problème 5 : COMPOSITIONNALITÉ TENSORIELLE COMPLÈTE

**Énoncé :** La formule `Ψ_{R(A,B)} = Ψ_R · Ψ_A · conj(Ψ_B)` est une simplification 1D du produit tensoriel `Ψ_R(x) ⊗ Ψ_A(x) ⊗ Ψ_B(y)`. Pour des phrases complexes (plus de 2 arguments, propositions subordonnées, négation), il faut un cadre tensoriel complet.

**Contraintes :**
- Doit gérer des prédicats à N arguments (N > 2)
- Doit gérer la négation, la quantification, les modaux
- La dimensionalité doit rester contrôlable (pas d'explosion combinatoire)

**Question ouverte :** Quel est le cadre mathématique minimal pour la compositionnalité tensorielle qui couvre la langue naturelle ? La grammaire catégorielle (Lambek) avec des espaces de Hilbert est-elle la bonne direction ? Ou faut-il un formalisme plus simple, inspiré directement de la mécanique quantique (états produits, intrication) ?

---

## Problème 6 : EXTRACTION UNIVERSELLE SANS FFT NI DFT

**Énoncé :** La DFT Harmonique est exacte mais coûteuse : O(n_max · N) où n_max = nombre de bins, N = taille de la grille. Pour un moteur interactif, l'extraction doit être **instantanée** (O(N) ou O(1)).

**Contraintes :**
- Temps d'extraction < 1 ms pour N = 1024
- Précision : erreur < 10⁻⁶ sur la fréquence extraite
- Doit fonctionner pour les ondes numériques ET les ondes conceptuelles

**Question ouverte :** L'extraction par démodulation de phase (régression linéaire sur la phase dépliée) fonctionne en O(N) mais échoue au-delà de n ≈ 500 à cause du repliement de phase. Peut-on résoudre ce repliement par une technique de « phase unwrapping 2D » ou par une transformée de Hilbert ? Ou faut-il une approche complètement différente (filtrage adapté, boucle à verrouillage de phase) ?

---

## Problème 7 : CONVERGENCE DU POINT FIXE POUR LES CONCEPTS

**Énoncé :** Le moteur ABC+GAGUT converge proprement pour les nombres (Ψ_a · Ψ_b → Ψ_{a+b} → stable). Pour les concepts, la convergence est prouvée en théorie (N ≈ 27 itérations) mais la qualité dépend crucialement de la force du signal d'interférence. Avec SHA-256, les signaux sont trop faibles pour converger.

**Contraintes :**
- Le critère de convergence `|interf(Ψ_{k+1}, Ψ_k) - 1| < ε` doit être fiable
- La convergence ne doit pas dépendre de la qualité du plongement initial
- Doit gérer les cas où AUCUN fait pertinent n'est trouvé (réponse « Je ne sais pas »)

**Question ouverte :** Faut-il un mécanisme de **renforcement spectral** où l'interférence répétée avec un concept amplifie progressivement sa signature dans l'onde ? (Inspiré de la résonance stochastique ou du feedback positif dans les systèmes dynamiques)

---

## Problème 8 : MÉMOIRE ET CONNAISSANCES

**Énoncé :** Pour les nombres, la mémoire est O(1) — la formule suffit. Pour les concepts, il faut un hologramme de connaissances. Mais comment stocker/encoder des millions de faits sans perte de la propriété d'interférence ?

**Contraintes :**
- L'hologramme doit permettre la recherche par résonance (pas par index)
- L'ajout d'un fait ne doit pas dégrader les faits existants (anti-collision)
- La taille doit rester raisonnable (< 1 Go pour 10M faits)

**Question ouverte :** Le positionnement des faits dans l'hologramme via `position(n) = (n · φ) mod 1` garantit l'anti-collision pour les nombres. Comment généraliser ce positionnement aux concepts ? Faut-il une **grille de phase 2D** où chaque concept occupe une cellule déterminée par ses coordonnées Laplacian Eigenmaps, et φ espace les cellules ?

---

## Résumé — Priorité des problèmes

| # | Problème | Impact | Difficulté | Statut |
|---|----------|--------|------------|--------|
| 1 | Plongement sémantique grande échelle | 🔴 Bloquant | Moyenne | 🔴 Ouvert |
| 2 | Exponentiation stable | 🟡 Important | Élevée | 🟡 Piste (log spectral) |
| 3 | Raisonnement multi-sauts conceptuel | 🔴 Bloquant | Moyenne | 🟢 **RÉSOLU** — `spectral_hop()` + score de résolution, PROUVÉ |
| 4 | Émergence non supervisée | 🟢 Recherche | Élevée | 🟢 Ouvert |
| 5 | Compositionnalité tensorielle | 🟢 Recherche | Élevée | 🟢 Ouvert |
| 6 | Extraction universelle O(N) | 🟡 Important | Moyenne | 🟡 Partiel (DFT Harmonique = exacte, O(n_max·N)) |
| 7 | Convergence concepts | 🟡 Important | Moyenne | 🟡 Piste (renforcement spectral) |
| 8 | Hologramme de connaissances | 🟡 Important | Moyenne | 🟢 **RÉSOLU** — Architecture N×64×64 (NOTE_HOLOGRAMME_Nx64x64.md) |

---

## Mise à jour — 14 Juin 2026

### Problème 3 résolu
`test_raisonnement_multisauts_ppmi.py` démontre le raisonnement multi-sauts via `spectral_hop()` avec score de résolution (interférence_locale^α × ancrage_question^(1-α)). La question "Quelle est la capitale du pays où se trouve Tombouctou ?" est résolue avec α=0.6, max_hops=8, stop_threshold=0.55. Le mécanisme de sauts séquentiels (k=0,1,2,3) et le problème d'arrêt sont PROUVÉS.

### Problème 8 résolu
L'architecture N × hologramme 64×64 (NOTE_HOLOGRAMME_Nx64x64.md) permet une scalabilité linéaire : N=1000 hologrammes = 64 Mo pour 144 000 concepts. La recherche est sub-linéaire : O(log N) routage + O(144) interférence. Déjà architecturé dans `holographic_ensemble.py`.

### Intégration dans KA Phone
Le Moteur Universel (`moteur_raisonnement_universel.py`) est intégré comme Step 5d dans `unified_server.py` (14 juin 2026). Source: `harmonic_reasoning`, exclu du ConsciousnessController.

---

**Document mis à jour le 14 Juin 2026**
