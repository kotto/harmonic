# Contrats des adaptateurs wave_bridge — référence de validation

Ce document détaille les **contrats** que chaque adaptateur doit respecter.
Le wave-validator (niveau 2) vérifie ces contrats automatiquement.

## Contrats communs (tous les adaptateurs)

1. **Drop-in** : même API publique que le module remplacé (signatures, noms, types)
2. **Délégation** : l'implémentation interne appelle les primitives wave_lang
   (pas de réimplémentation numpy de bind/resonate/FFT)
3. **Normalisation** : tout ψ retourné a ‖ψ‖ = 1 (tolérance 1e-6)
4. **Bornes** : les scores ∈ [-1, 1] pour resonate, ∈ [0, 1] pour coherence
5. **Déterminisme** : mêmes entrées → mêmes sorties (à 1e-6)
6. **Fini** : aucune NaN/Inf dans les sorties

## Contrats par adaptateur

| # | Adaptateur | Contrat spécifique |
|---|-----------|-------------------|
| 1 | PsiDiphoneBank | store/query retourne des résultats triés par score décroissant ; `size` = nombre stocké |
| 2 | ABCMemoryKernel | `__call__(t)` = abc_kernel(t) ; force effective de même shape que l'entrée |
| 3 | HarmonicEnergyCore | `compute()` fini ; E négatif = conformation favorable (convention) |
| 4 | SpectralAnalyzer | roundtrip analyse→synthèse : MSE < 1e-6 ; filtrage préserve la shape |
| 5 | VoiceSignature | ψ extrait unitaire ; `compare` ∈ [0, 1] |
| 6 | GlottalSource | waveform de longueur duration×sample_rate ; amplitude max > 0 |
| 7 | HarmonicCloner | `clone()` retourne un signal de même shape que la source |
| 8 | CoherenceAttention | chaque ψ contextuel unitaire ; `contextualize_query` unitaire |
| 9 | HolographicEncoderBridge | bind/unbind : recovery > 0.5 ; store_fact/query fonctionnels |
| 10 | PhasePropagator | `propagate()` produit ≥ 1 étape ; conclusion textuelle |
| 11 | WaveDecoderBridge | `compute_signature()` contient les 9 dimensions + type |
| 12 | HolographicRAG | ingest/retrieve fonctionnels ; psi_dominant unitaire ; rumination bornée |
| 13 | FewShotPhaseLock | `inject()` retourne un pattern_id non-None |
| 14 | CoherenceGate | `reason()` retourne (answer, confidence, method) avec method connu |
| 15 | FeedbackLoopBridge | score > 0.7 → reinforce ; score < 0.3 → weaken ; `evaluate` ∈ [0, 1] |
| 16 | WaveSamplingBridge | `deterministic()` ∈ vocabulaire ; perplexity > 0 finie |
| 17 | WaveToolUseBridge | `resolve()` retourne ToolCall ou None ; `execute()` gère les erreurs |
| 18 | WaveBeamSearchBridge | `best_sequence()` non vide ; amplitudes ≥ 0 |
| 19 | WavePerplexityBridge | entropie > 0 finie ; confidence ∈ [0, 1] ; margins ∈ [-2, 2] |

## Tables d'équivalence (niveau 3)

| Table | Équivalences | Règle |
|-------|-------------|-------|
| TRADUCTION_ONDULATOIRE_LLM.md | 36 | ✅ → fichier doit exister ; 🆕 → fichier doit être absent |
| TRADUCTION_ONDULATOIRE_TTS.md | 25 | idem |

Cas spéciaux :
- `Partout`, `Architecture` → pas des fichiers, ignorés
- `fichier.py:method()` → méthode, vérifie `fichier.py`
- Les fichiers peuvent vivre à la racine, dans `vital-ka/core/python/`, `ka_sonic/` ou `alphafold/`

## Dérive root vs vital-ka

- Ratio vital-ka/root > 1.5 → extensions légitimes dans vital-ka (note, pas un échec)
- Ratio < 0.8 → vital-ka plus petit que root (**régression** → échec)
- Idéalement : synchroniser la copie racine avec vital-ka (canonique)

## Critères de release

| Critère | Seuil |
|---------|-------|
| Tests niveau 1 (primitives) | 100% |
| Tests niveau 2 (adaptateurs) | 100% |
| Tests niveau 3 (équivalences) | 100% |
| Dérive root/vital-ka | ratio ≥ 0.8 partout |
| Exit code | 0 |
