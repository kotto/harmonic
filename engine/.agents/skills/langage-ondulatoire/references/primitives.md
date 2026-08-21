# Les 13 primitives universelles — référence complète

Source : `DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md` §5, implémentation `vital-ka/core/python/wave_lang.py`.

## Fondements mathématiques

- **Espace :** ℂ⁵¹² — résolution minimale pour un phénomène complexe sans perte (~40 000 mots sans collision).
- **φ-spacing :** `θ_k = {k·φ mod 1} · 2π` avec φ = 1.618033988749895 (nombre le plus irrationnel :
  fraction continue [1;1,1,…], discrépance O(log N/N), Three-Gap Theorem ≤ 3 écarts, ratio max φ² ≈ 2.618).
  Conséquence : l'espacement φ minimise l'énergie de Riesz → **>3000x** meilleur que le hasard,
  **>100 000x** meilleur que les configurations groupées.
- **Binding HRR :** `bind(ψa, ψb) = IFFT(FFT(ψa) · FFT(ψb))` — réversible, associatif, commutatif, O(D log D).
- **Noyau ABC :** dérivée fractionnaire Atangana-Baleanu-Caputo, ordre α = 1/φ ≈ 0.618 (équilibre
  mémoire infinie / amnésie). `K(t) = B(α)·E_α(−α·t^α/(1−α))` ; K(0)=1, K(100)→0.
- **Factorisation canonique :** `ψ = A·e^{iφ}` — l'amplitude porte la sémantique, la phase la syntaxe.

## Tableau complet

| # | Primitive | Signature Python | Formule | Propriété clé |
|---|---|---|---|---|
| 1 | encode | `encode(entity, dim=512, use_cache=True) -> np.ndarray` | FNV-1a + φ-spacing | Déterministe, ‖ψ‖ = 1 |
| 2 | decode | `decode(ψ, vocabulary=None, top_k=...) -> ...` | plus proche voisin | `decode(encode(x)) ≈ x` |
| 3 | bind | `bind(ψa, ψb) -> ψ` | `IFFT(FFT(a)·FFT(b))` | Réversible, associatif, commutatif |
| 4 | unbind | `unbind(ψa, ψb) -> ψ` | `IFFT(FFT(a)·conj(FFT(b)))` | Réciproque de bind |
| 5 | superpose | `superpose(*ψs, weights=None) -> ψ` | Σ ψᵢ | Linéaire, commutative, norme préservée |
| 6 | resonate | `resonate(ψa, ψb) -> float` | Re(⟨a\|b⟩) ∈ [-1, 1] | +1 identique · 0 orthogonal · −1 opposé |
| 7 | rotate | `rotate(ψ, angle) -> ψ` | ψ·e^{iθ} | Préserve ‖ψ‖, groupe U(1) |
| 8 | normalize | `normalize(ψ) -> ψ` | ψ/‖ψ‖ | Projection sur le cercle unité |
| 9 | interfere | `interfere(ψa, ψb, epsilon=0.1) -> ψ` | ψa + ε·ψb | Créativité : ε≈0.15 subtil, 0.5 équilibré, >1.0 domine |
| 10 | diffract | `diffract(ψ, inverse=False) -> ψ` | FFT / IFFT | Dualité temps-fréquence (Gabor) |
| 11 | filter | `filter_wave(ψ, ...)` (LP/HP/BP) | FFT → masque → IFFT | Débruitage, extraction, formants |
| 12 | phase_shift | `phase_shift(ψ, shift) -> ψ` | ψd·e^{iΔd} | Scalaire = rotate ; vecteur = décalage fin |
| 13 | emerge | `emerge(*ψs, temperature=0.5) -> ψ` | Σ wᵢψᵢ, wᵢ ∝ exp(centralité/T) | Émergence par cohérence mutuelle |

## Primitives avancées

| Primitive | Définition | Usage |
|---|---|---|
| `oppose(ψa, ψb)` | ψa − ψb | Contraste, tension dialectique |
| `amplify(ψ, comp, boost=3.0)` | ψ + boost·comp | Faire émerger l'invisible |
| `bind_many(a, b, c, ...)` | bind(bind(a,b), c) | Faits complexes (sujet, relation, objet, contexte) |
| `coherence(ψa, ψb)` | \|resonate(a,b)\| ∈ [0, 1] | Similarité non-directionnelle |

## Utilitaires de la mémoire holographique (`HolographicMemory`)

- `store(ψ_sujet, ψ_relation, ψ_objet, amplitude=1.0)` — enregistre un fait en superposition
- `store_raw(ψ, amplitude=1.0)` — ajoute une onde brute
- `query(ψ_query) -> ψ` — récupération par résonance (onde superposée des faits cohérents)
- `query_scores(ψ_query) -> [(idx, score)]` — scores de résonance
- `energy()`, `forget(t, learning_rate=0.1)` (oubli ABC), `clear()`

Autres utilitaires : `encode_many(entities)`, `resonate_batch(query, candidates)`,
`norm(ψ)`, `energy(ψ)`, `spectrum(ψ)`, `stats(ψ)`, `abc_kernel(t)`, `abc_forget(memory, t, lr)`.

## Encodage par domaine

| Domaine | Entité | encode() |
|---|---|---|
| Langage | Mot | FNV1a(mot) × φ-spacing → ψ |
| Parole | Phonème | enveloppe spectrale → ψ |
| Image | Patch | DCT → dictionnaire ψ |
| Protéine | Acide aminé | masse + hydrophobicité → ψ |
| Son | Frame 80 ms | FFT → ψ |

Règle : toute entité discrète a un ψ ; tout continu se segmente en entités discrètes.

## Valeurs de référence (validations expérimentales, doc §10)

| Test | Attendu |
|---|---|
| \|encode(x)\| | 1.000 |
| decode après encode de "lumiere" | score 1.0 |
| unbind(bind(a,b), b) | recovery ≈ 0.73 |
| resonate(ψ, ψ) / orthogonal | 1.0 / ≈ 0.04 |
| rotate(ψ, π) | résonance −1.000 |
| interfere ε=0.15 | préserve la base (0.99) |
| diffract → diffract(inverse=True) | identité 1.000 |
| phase_shift(ψ, π/2) | orthogonal 0.000 |
| abc_kernel | K(0)=1, K(100)→0 |

## Domaines couverts par les mêmes primitives

| Domaine | Pipeline |
|---|---|
| NLP | ENCODE → BIND → RESONATE → DECODE (98.6 %) |
| Audio | FFT → ENVELOPPE → SUPERPOSE → IFFT (compression 64.6:1) |
| Protéines | ENCODE → RESONATE → EMERGE (Rama 0.71–0.78) |
| TTS | ENCODE → BIND → PHASE_SHIFT → SUPERPOSE |
| Mémoire | STORE → SUPERPOSE → QUERY (hologramme 40K mots) |
