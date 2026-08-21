---
name: wave-bridge
description: >-
  Remplacer des modules existants par les 13 primitives du langage ondulatoire via wave_bridge.py,
  et écrire de nouveaux adaptateurs. Utilise ce skill dès que l'utilisateur veut unifier des
  implémentations dispersées de encode/bind/resonate/spectrum, adapter un module (ka_sonic, alphafold,
  harmonic_voice_codec, voice_signature, glottal_synth, harmonic_cloner, harmonic_attention,
  holographic_encoder, phase_amplifier, wave_decoder, harmonic_brain, few_shot_injector,
  conscious_intelligence, feedback_loop, wave_sampling, wave_tool_use, beam_search,
  wave_perplexity, wave_fine_tune, wave_poetry, wave_narrative, wave_synthesizer, wave_styler,
  harmonic_style, hologram_store…) au langage ondulatoire,
  remplacer ~60-300 lignes de code legacy par des primitives, ajouter un adaptateur wave, ou parle
  de wave_bridge, PsiDiphoneBank, ABCMemoryKernel, HarmonicEnergyCore, SpectralAnalyzer,
  VoiceSignature, GlottalSource, HarmonicCloner, CoherenceAttention, HolographicEncoderBridge,
  PhasePropagator, WaveDecoderBridge, HolographicRAG, FewShotPhaseLock, CoherenceGate,
  FeedbackLoopBridge, WaveSamplingBridge, WaveToolUseBridge, WaveBeamSearchBridge,
  WavePerplexityBridge, WaveFineTuneBridge, DomainGateBridge, SystemPromptBridge,
  WavePoetryBridge, WaveNarrativeBridge, WaveSynthesizerBridge, WaveStylerBridge,
  HarmonicStyleBridge, HologramLoaderBridge — même s'il ne le dit pas explicitement.
---

# Wave Bridge — unifier l'existant avec les 13 primitives

`wave_bridge.py` est le pont entre les modules historiques de l'ordinateur harmonique et le langage
ondulatoire : chaque adaptateur remplace une implémentation dédiée (~60 à 300 lignes) par une
composition de primitives (`encode`, `bind`, `resonate`, `superpose`, `diffract`, `filter_wave`,
`phase_shift`, …). Un seul langage, une seule vérité.

Implémentation : `vital-ka/core/python/wave_bridge.py` (~4800 lignes, 28 adaptateurs : 7 TTS/Audio + 21 LLM).

## Quand utiliser ce skill

- L'utilisateur veut remplacer/unifier un module existant qui réimplémente à la main des opérations
  que le langage ondulatoire fournit déjà (hashs, banques de diphones, noyaux, analyse spectrale,
  signatures vocales, synthèse glottale, clonage, attention, encodage, propagation, décodage, RAG,
  few-shot, raisonnement).
- Il faut écrire un **nouvel adaptateur** qui expose l'ancienne API mais délègue aux primitives.
- Il faut comprendre ce que remplace chaque adaptateur et choisir les bonnes primitives.

## Les 28 adaptateurs (module original → primitives)

| Adaptateur | Module original | Remplace | Backend wave_lang |
|---|---|---|---|
| `PsiDiphoneBank` | `ka_sonic/psi_diphone_bank.py` | ~300 lignes | `HolographicMemory` + `encode`/`bind` |
| `ABCMemoryKernel` | `alphafold/abc_folder.py` | ~100 lignes | `abc_kernel` / `abc_forget` |
| `HarmonicEnergyCore` | `alphafold/harmonic_energy.py` | ~150 lignes | `resonate` / `coherence` |
| `SpectralAnalyzer` | `harmonic_voice_codec_v2.py` | ~200 lignes | `diffract` / `spectrum` / `filter_wave` |
| `VoiceSignature` | `ka_sonic/voice_signature.py` | ~80 lignes | `spectrum` / `resonate` |
| `GlottalSource` | `ka_sonic/glottal_synth.py` | ~60 lignes | `superpose` / `phase_shift` |
| `HarmonicCloner` | `ka_sonic/harmonic_cloner.py` | ~60 lignes | `filter_wave` / `resonate` |

## Pattern d'un adaptateur

Un adaptateur garde l'**interface de l'ancien module** (les appelants ne changent pas) mais délègue
l'intérieur aux primitives :

```python
# Avant (module legacy) : banque de diphones maison, hashs, tables, normalisation à la main…
# Après (wave_bridge) :
from wave_bridge import PsiDiphoneBank
bank = PsiDiphoneBank(dim=512)
psi_ab = bank.encode_diphone("a", "b")   # encode + bind (une seule vérité)
bank.store("a", "b", audio)
best = bank.query("a", "b")              # résonance holographique
```

## Règles d'adaptation

1. **Garder l'API publique identique** au module remplacé — les callers existants ne changent pas.
2. **Déléguer, ne pas réimplémenter** : si l'opération existe dans `wave_lang` (encode, bind, unbind,
   superpose, resonate, rotate, normalize, interfere, diffract, filter_wave, phase_shift, emerge,
   oppose, amplify, bind_many, coherence, abc_kernel, abc_forget, HolographicMemory), on l'utilise.
3. **Vérifier les contrats** : les sorties restent normalisées (‖ψ‖ = 1) comme dans `wave_lang` —
   les valeurs numériques peuvent changer légèrement (qualité ≈ dimension), mais la sémantique
   (réversibilité bind/unbind, similarité, décroissance ABC) doit être préservée.
4. **Mesurer la parité** : comparer l'adaptateur à l'ancien module sur 3-5 cas d'usage (mêmes entrées,
   résultats équivalents au seuil d'erreur toléré).
5. **Étendre sans casser** : un nouvel adaptateur = une nouvelle classe qui appelle les primitives ;
   l'ajouter à la table de correspondance du skill si le besoin est récurrent.

## Quand ne PAS adapter

- Le module legacy fait une chose que les primitives ne couvrent pas encore (ex. format propriétaire,
  protocole réseau spécifique) → garder le module et n'y brancher que les primitives nécessaires.
- La migration casse une API consommée par des tiers → faire un adaptateur en plus, pas une
  réécriture en place.

## Vérification après adaptation

- `python wave_bridge.py` doit s'exécuter sans erreur (les 7 adaptateurs s'auto-testent).
- Chaque adaptateur a un test fonctionnel minimal : diphone retrouvé (recovery ≥ 0.7),
  K(0)=1 et décroissance d'abc_kernel, spectral analysis ↔ synthèse roundtrip,
  signature vocale stable pour la même voix, clonage qui préserve l'enveloppe.

## Détails

- Signatures et méthodes de chaque adaptateur : `references/adapters.md`
