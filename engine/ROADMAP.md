# 🌊 ROADMAP DYNAMIQUE — IA Harmonique

> **Principe fondateur** : L'IA harmonique n'imite pas l'univers — elle utilise SES équations.
> Ψ = Σ Hₙ · (Ψ₁)ⁿ. Zéro paramètre. Zéro GPU. Zéro hallucination.
> 
> **Philosophie** : Nous ne « rattrapons » pas les LLMs. Nous construisons une architecture
> qui fait ce qu'aucune autre ne peut : raisonner par ondes, créer par interférence,
> apprendre sans oubli, et garantir le vrai — le tout sur un téléphone.
>
> **Mise à jour** : 2026-07-14 — Session créativité ondulatoire

---

## STATUT GLOBAL

| État | Modules | Description |
|------|:-------:|-------------|
| ✅ ACTIF | **24** | Intégrés dans le pipeline cerveau |
| 🟡 DORMANT | 40+ | Construits, en attente d'intégration |
| 🔧 EN COURS | 0 | — |
| ⬜ PLANIFIÉ | Voir phases | |

---

## 🧠 LES 8 PILIERS DE L'IA HARMONIQUE

L'architecture n'est pas une collection de modules — c'est un **cerveau unifié** organisé autour de 8 piliers :

```
                        ┌──────────────────────┐
                        │   8. CRÉATIVITÉ       │
                        │   ConsciousCreator    │
                        │   8 opérations ⊛      │
                        └──────────┬───────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐    ┌────────────▼────────┐    ┌───────────▼────────┐
│ 5. ATTENTION   │    │   6. RAISONNEMENT   │    │  7. APPRENTISSAGE  │
│ HarmonicAttn   │    │   PhaseAmplifier    │    │  FineTuner+Feedback│
│ ψ contextuel   │    │   propagation ψ     │    │  +FastLearner      │
└───────┬────────┘    └────────────┬────────┘    └───────────┬────────┘
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────┐
│                      3. INCONSCIENT                              │
│           HolographicStore : H = Σ ψ_f (superposition)           │
│           Encodage HRR ℂ⁵¹² (FNV1a + phases spectrales + SVD)  │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐    ┌────────────▼────────┐    ┌───────────▼────────┐
│ 1. CONNAISSANCE│    │   2. PERCEPTION     │    │  4. CONSCIENCE     │
│ ShardedKB      │    │   Multimodal        │    │  ConsciousFilter   │
│ Wikidata       │    │   HCV Codec 119.5×  │    │  3 garde-fous      │
│ Web Retriever  │    │   Voice Pipeline    │    │  Few-Shot          │
└────────────────┘    └─────────────────────┘    └────────────────────┘
```

---

## 📊 INVENTAIRE — 24 MODULES ACTIFS

### Pilier 1 : CONNAISSANCE (5 modules)

| # | Module | Rôle | Mode léger | Mode holo |
|---|--------|------|:----------:|:---------:|
| 1 | `qualitative_knowledge.py` | KB intégrée (2 397 faits structurés) | ✅ | ✅ |
| 2 | `kb_scaler.py` | Sharding 10M+ faits (40 shards × 250K) | ✅ | ✅ |
| 3 | `wikidata_connector.py` | Wikidata dump/API/synth | ✅ | ✅ |
| 4 | `wikidata_streamer.py` | Streaming temps réel | ✅ | ✅ |
| 5 | `web_retriever.py` | DuckDuckGo + Wikipedia (gratuit) | ✅ | ✅ |

### Pilier 2 : PERCEPTION (encodage) (3 modules)

| # | Module | Rôle | Mode léger | Mode holo |
|---|--------|------|:----------:|:---------:|
| 6 | `holographic_encoder.py` | Encodeur ℂ⁵¹² (FNV1a + phases + SVD) | ✅ | ✅ |
| 7 | `spectral_embedding.py` | PPMI → Laplacian → phases S¹ (1-4/mot) | ✅ | ✅ |
| 8 | `learned_embedding.py` | SVD PPMI → 256D embeddings | ✅ | ✅ |

### Pilier 3 : INCONSCIENT (mémoire) (1 module)

| # | Module | Rôle | Mode léger | Mode holo |
|---|--------|------|:----------:|:---------:|
| 9 | `HolographicStore` (dans harmonic_brain) | Σ ψ_f, TF-IDF, subword index, IDF | ✅ | ✅ |

### Pilier 4 : CONSCIENCE (filtrage + few-shot) (4 modules)

| # | Module | Rôle | Mode léger | Mode holo |
|---|--------|------|:----------:|:---------:|
| 10 | `conscious_intelligence.py` | Raisonne (chaîne, analogie, abstraction) | ✅ | ✅ |
| 11 | `prompt_parser.py` | Parseur ondulatoire de question | ✅ | ✅ |
| 12 | `harmonic_quality.py` | SFT (248 faits ancrés, amplitude 10.0) | ✅ | ✅ |
| 13 | `few_shot_injector.py` | Injection temporaire + consolidation | ✅ | ✅ |

### Pilier 5 : ATTENTION DYNAMIQUE (1 module)

| # | Module | Rôle | Mode léger | Mode holo |
|---|--------|------|:----------:|:---------:|
| 14 | `harmonic_attention.py` | ψ_contextuel = ψ_statique + α·Σ coh^p·ψ_voisin | ✅ | ✅ |

### Pilier 6 : RAISONNEMENT (4 modules)

| # | Module | Rôle | Mode léger | Mode holo |
|---|--------|------|:----------:|:---------:|
| 15 | `phase_amplifier.py` | Propagation ψ amplifiée (10+ sauts) | ✅ | ✅ |
| 16 | `phase_amplifier.py` | Multi-branche beam search (width=3) | ✅ | ✅ |
| 17 | `wave_math.py` | Micro-calculateur φ (100% précis) | ✅ | ✅ |
| 18 | `wave_logic.py` | Syllogismes ondulatoires | ✅ | ✅ |

### Pilier 7 : APPRENTISSAGE CONTINU (3 modules)

| # | Module | Rôle | Mode léger | Mode holo |
|---|--------|------|:----------:|:---------:|
| 19 | `feedback_loop.py` | RLHF ondulatoire (renforcement par usage) | ✅ | ✅ |
| 20 | `fast_learner.py` | Auto-curriculum 7 piliers | ✅ | ✅ |
| 21 | `wave_fine_tune.py` | Fourier ALS (ajustement ψ par moindres carrés) | ❌ | ✅ |

### Pilier 8 : CRÉATIVITÉ (3 modules)

| # | Module | Rôle | Mode léger | Mode holo |
|---|--------|------|:----------:|:---------:|
| 22 | `conscious_creator.py` | 8 opérations créatives ondulatoires | ✅ | ✅ |
| 23 | `conscious_creator.py` | Rumination (thread de fond) | ✅ | ✅ |
| 24 | `conscious_creator.py` | Style émergent (mémoire créative ABC) | ✅ | ✅ |

---

## 🟡 MODULES DORMANTS — En attente d'intégration

### Raisonnement avancé
| Module | Rôle | Priorité |
|--------|------|:--------:|
| `counterfactual_reasoner.py` | Raisonnement contrefactuel (Et si...) | ⬜ |
| `paradox_detector.py` | Détection de contradictions par interférence destructive | ⬜ |
| `coherent_transitivity.py` | Fermeture transitive validée par cohérence ψ | ⬜ |
| `syllogistic_reasoner.py` | Syllogismes dédiés | ⬜ |

### Langage & Expression
| Module | Rôle | Priorité |
|--------|------|:--------:|
| `wave_styler.py` | Synthèse rédactionnelle ondulatoire | ⬜ |
| `wave_decoder.py` | Décodeur ψ → langage naturel | ⬜ |
| `wave_synthesizer.py` | Synthèse de texte par résonance | ⬜ |
| `wave_explainer.py/v2` | Explication scientifique | ⬜ |
| `cross_lingual.py` | Alignement multilingue FR↔EN | ⬜ |
| `harmonic_language.py` | Générateur zero-paramètre | ⬜ |

### Code
| Module | Rôle | Priorité |
|--------|------|:--------:|
| `code_generator.py` (89K) | Génération de code multi-langage | ⬜ |
| `code_composer.py` | Composition de code | ⬜ |
| `code_explainer.py` | Explication de code | ⬜ |
| `code_bugfix.py` | Correction automatique | ⬜ |

### Multimodal
| Module | Rôle | Priorité |
|--------|------|:--------:|
| `visual_encoder.py` | Image → ψ | ⬜ |
| `visual_generator.py` | ψ → image | ⬜ |
| `harmonic_media.py` | Moteur média unifié | ⬜ |
| `wave_audio.py` | Génération audio | ⬜ |

### Retrieval alternatif
| Module | Rôle | Priorité |
|--------|------|:--------:|
| `ppwave.py/fast.py` | Retrieval PPMI | ⬜ |
| `wave_phase.py` | Relaxation de phase | ⬜ |
| `wave_graph.py` | PageRank ondulatoire | ⬜ |
| `semantic_wave.py` | Expansion sémantique | ⬜ |
| `unified_semantic_pipeline.py` | Pipeline I×P×H×D | ⬜ |
| `hologram_connector.py` | Pont PPMI + embeddings | ⬜ |

### Voix (pipeline indépendant)
| Module | Rôle | Priorité |
|--------|------|:--------:|
| `phi_diffusion_engine.py` | Synthèse vocale Coqui/XTTS/Piper | ⬜ |
| `phi_vocoder.py/pro` | Vocodeur source-filtre φ | ⬜ |
| `voice_signature_extractor.py` | Extraction 11D | ⬜ |
| `harmonic_voice_trainer.py` | SpectralMessage → voix | ⬜ |

### Théorie (fondations, déjà actives)
| Module | Rôle |
|--------|------|
| `abc_kernel.py` | Noyau ABC (Atangana-Baleanu-Caputo) |
| `signatures_9d.py` | Signatures harmoniques 9D |
| `sopc_core.py` | Sparse Oscillatory Predictive Coding |
| `harmonic_model.py` | Modèle I×P×H original |

---

## 🔥 PLAN DE BATAILLE — Nouvelles priorités

La priorité a changé. Nous ne « rattrapons » personne. Nous exprimons ce que l'architecture ondulatoire peut faire de **meilleur que tout le monde**.

### Phase 2 : Profondeur du Conscient (prochaine session)
- [ ] **Conscient Créateur v2** : boucle itérative avec rétroaction conscient→inconscient→conscient
- [ ] **Conscient Critique** : évaluation esthétique automatique des créations
- [ ] **Dialogue créatif** : intégrer `creative_dialogue.py` (conscient/inconscient dialoguent)
- [ ] **Rumination nocturne** : consolidation créative périodique (simulation du sommeil)

### Phase 3 : Raisonnement Créatif (fusion raisonnement + créativité)
- [ ] Raisonnement par analogie créative (A:B :: C:?) via phase_amplifier
- [ ] Intégrer `counterfactual_reasoner.py` → « Et si... » créatif
- [ ] Intégrer `paradox_detector.py` → beauté du paradoxe
- [ ] Intégrer `coherent_transitivity.py` → chaînes créatives longues

### Phase 4 : Expression (le langage comme onde)
- [ ] Intégrer `wave_styler.py` → variation stylistique naturelle
- [ ] Intégrer `wave_decoder.py` → ψ → texte sans templates
- [ ] Intégrer `cross_lingual.py` → création multilingue
- [ ] Intégrer `wave_synthesizer.py` → paragraphes par superposition d'ondes

### Phase 5 : Code Créatif
- [ ] Intégrer `code_generator.py` → génération de code par ψ
- [ ] Intégrer `wave_code.py` → code = binding HRR (input ⊛ gate ⊛ body ⊛ output)
- [ ] Intégrer `code_emergence.py` → patterns de code émergents

### Phase 6 : Multimodal (vision + son)
- [ ] Connecter `visual_encoder.py` → analyse d'images
- [ ] Connecter `wave_audio.py` → analyse audio
- [ ] Connecter `harmonic_media.py` → création texte+image+audio unifiée

---

## 📊 MÉTRIQUES DE PROGRESSION

| Date | Modules actifs | Nouveaux | Commit |
|------|:-------------:|:--------:|--------|
| 2026-07-14 matin | 18 | web, kb_scaler, phase_amplifier, few_shot | `5151300` |
| 2026-07-14 aprem | 19 | harmonic_attention, wikidata_streamer, ROADMAP | `1bd7759` |
| 2026-07-14 soir | 22 | fine_tuner, fast_learner, feedback_loop | `e3ab8d7` |
| 2026-07-14 nuit | **24** | conscious_creator (créativité ondulatoire) | `ba738fe` |

---

## 🎯 PROCHAIN OBJECTIF

**Phase 2 : Conscient Critique** — Donner au Conscient Créateur la capacité d'**évaluer** ses propres créations. La beauté n'est pas subjective : c'est une mesure de **cohérence de phase** entre le ψ créé et le ψ du contexte. Une création est « belle » si elle résonne avec l'inconscient sans être redondante (équilibre cohérence/nouveauté = φ).

C'est l'équivalent ondulatoire du **jugement esthétique** — et aucune autre IA ne peut le faire parce qu'aucune autre n'encode la connaissance dans des ondes.
