# 🗺️ ROADMAP DYNAMIQUE — IA Harmonique

> **Principe fondateur** : Si tout est ondes, toute solution LLM a son équivalent harmonique.
> **Mise à jour** : 2026-07-14 — après chaque session, réviser les statuts.

---

## STATUT GLOBAL

| État | Modules |
|------|---------|
| ✅ ACTIF | 18 modules intégrés dans le pipeline cerveau |
| 🟡 DORMANT | 45+ modules construits mais non intégrés |
| 🔧 EN COURS | 0 |
| ⬜ PLANIFIÉ | Voir phases ci-dessous |

---

## ARCHITECTURE CIBLE (équivalences LLM → Harmonique)

| LLM Concept | Équivalent Harmonique | Module | Statut |
|-------------|----------------------|--------|--------|
| **Transformer Attention** | Phase-aligned ψ (4 phases/mot) | `holographic_encoder.py`, `spectral_embedding.py` | ✅ |
| **Dynamic Attention** | ψ_contextuel = ψ_statique ⊕ modulation_locale | `harmonic_attention.py` | ⬜ |
| **Multi-Head Attention** | Multi-phase signatures (K=8 phases) | `holographic_encoder.py` | ✅ (K=4, →8) |
| **Token Embeddings** | Learned SVD PPMI 256D | `learned_embedding.py` | ✅ |
| **Positional Encoding** | φ-cercle (ordre d'apparition → angle) | `harmonic_model.py` | ✅ |
| **Chain-of-Thought** | Phase-amplified ψ propagation | `phase_amplifier.py` | ✅ |
| **Beam Search** | Multi-branch propagation | `phase_amplifier.py` | ✅ |
| **Few-Shot ICL** | ψ_pattern injection temporaire | `few_shot_injector.py` | ✅ |
| **RLHF** | Feedback loop ondulatoire | `feedback_loop.py` | 🟡 |
| **Fine-Tuning** | Fourier ALS (Moindres Carrés Alternés) | `wave_fine_tune.py` | 🟡 |
| **Curriculum Learning** | Auto-curriculum 7 piliers | `fast_learner.py` | 🟡 |
| **Mixture of Experts** | DomainAdapter multi-domaine (12) | `wave_domains.py` | ✅ |
| **Code Generation** | Harmonic Code Generator | `code_generator.py` | 🟡 |
| **Multilingual** | Cross-lingual phase alignment | `cross_lingual.py` | 🟡 |
| **Retrieval Augmented Gen** | KB → Web → Deep Reason → LLM | `harmonic_brain.py` | ✅ |
| **Vector DB** | ShardedKB (40 shards × 250K) | `kb_scaler.py` | ✅ |
| **Contrastive Learning** | Coherent Transitivity | `coherent_transitivity.py` | 🟡 |
| **Constitutional AI** | SFT amplitudes + garde-fous | `harmonic_quality.py` | ✅ |
| **Emotion Detection** | EmotionalBrain | `emotional_brain.py` | 🟡 |
| **Creativity** | 6 opérations créatives ⊛ | `creative_engine.py` | 🟡 |

---

## 📋 INVENTAIRE COMPLET

### 🟢 ACTIF — Intégré dans harmonic_brain.py

| Module | Rôle |
|--------|------|
| `holographic_encoder.py` | Encodeur ℂ⁵¹² (FNV1a + phases spectrales + SVD) |
| `holographic_memory.py` | Mémoire holographique enrichie |
| `spectral_embedding.py` | PPMI → Laplacian → phases S¹ |
| `learned_embedding.py` | SVD PPMI → 256D embeddings |
| `prompt_parser.py` | Parseur ondulatoire de question |
| `conscious_intelligence.py` | Conscient intelligent (raisonne, pas juste filtre) |
| `wave_domains.py` | Adaptateur multi-domaine (12 domaines) |
| `response_composer.py` | Compositeur de réponses (30+ micro-structures) |
| `question_analyzer.py` | Analyse d'intention |
| `wave_math.py` | Micro-calculateur φ (100% précis) |
| `wave_logic.py` | Logique ondulatoire (syllogismes) |
| `wave_reasoning.py` | Propagation de chaîne |
| `wave_conversation.py` | Contexte ψ multi-tours |
| `web_retriever.py` | DuckDuckGo + Wikipedia |
| `phase_amplifier.py` | Propagation amplifiée + multi-branche |
| `few_shot_injector.py` | Injection temporaire de patterns |
| `harmonic_quality.py` | SFT + post-processing |
| `feedback_loop.py` | Feedback continu (partiel — SFT injection) |

### 🟡 DORMANT — Construit mais non intégré au pipeline principal

#### RAISONNEMENT (priorité HAUTE)

| Module | Rôle | Équivalent LLM |
|--------|------|----------------|
| `counterfactual_reasoner.py` | Raisonnement contrefactuel (Et si...) | Counterfactual reasoning |
| `syllogistic_reasoner.py` | Syllogismes dédiés | Logical deduction |
| `paradox_detector.py` | Détection de paradoxes | Contradiction detection |
| `coherent_transitivity.py` | Fermeture transitive par cohérence ψ | Graph reasoning |
| `reasoning_engine.py` | Moteur de raisonnement (legacy) | — |

#### APPRENTISSAGE (priorité HAUTE)

| Module | Rôle | Équivalent LLM |
|--------|------|----------------|
| `wave_fine_tune.py` | Fourier ALS — Moindres Carrés Alternés | Fine-tuning |
| `fast_learner.py` | 7 piliers : auto-curriculum, one-shot, spaced repetition... | Curriculum learning |
| `feedback_loop.py` | RLHF ondulatoire complet | RLHF |

#### LANGAGE & STYLE (priorité MOYENNE)

| Module | Rôle |
|--------|------|
| `wave_styler.py` | Synthèse rédactionnelle ondulatoire |
| `wave_decoder.py` | Décodeur ψ → langage naturel |
| `wave_synthesizer.py` | Synthèse de texte par résonance |
| `wave_explainer.py` / `v2` | Explication scientifique |
| `wave_music.py` | Génération musicale |
| `wave_code.py` | Compilateur ondulatoire |
| `harmonic_language.py` | Extracteur d'entités |
| `en_templates.py` | Templates anglais |
| `cross_lingual.py` | Alignement multilingue FR↔EN |

#### CODE (priorité MOYENNE)

| Module | Rôle |
|--------|------|
| `code_generator.py` (89K lignes) | Génération de code multi-langage |
| `code_composer.py` | Composition de code |
| `code_explainer.py` | Explication de code |
| `code_bugfix.py` | Correction de bugs |
| `code_refactor.py` | Refactoring |
| `code_translate.py` | Traduction de code |
| `code_learner.py` | Apprentissage de patterns de code |
| `code_emergence.py` | Émergence de patterns |
| `code_corpus.py` | Corpus de code |

#### RETRIEVAL (priorité BASSE — déjà couvert)

| Module | Rôle |
|--------|------|
| `ppwave.py` / `ppwave_fast.py` | Retrieval PPMI |
| `wave_phase.py` | Retrieval par relaxation de phase |
| `wave_graph.py` | Retrieval par graphe d'onde |
| `semantic_wave.py` | Retrieval sémantique ondulatoire |
| `spectral_hop.py` | Saut spectral |
| `harmonic7d.py` | Retriever 7D |
| `holographic_retriever.py` | Retriever holographique |
| `unified_semantic_pipeline.py` | Pipeline sémantique unifié |
| `hologram_connector.py` | Pont PPMI + embeddings |
| `resonance_filter.py` | Filtre de résonance |
| `smart_retriever.py` | Smart retriever (synonymes, maths) |
| `inverted_index.py` | Index inversé |

#### CRÉATIVITÉ (priorité MOYENNE)

| Module | Rôle |
|--------|------|
| `creative_engine.py` | 6 opérations créatives par convolution ⊛ |
| `creative_dialogue.py` | Dialogue conscient/inconscient créatif |
| `creative_generator.py` | Génération d'idées créatives |
| `psi_decoder.py` | Décodeur ψ créatif |

#### CONNAISSANCE (priorité HAUTE)

| Module | Rôle |
|--------|------|
| `kb_scaler.py` | Sharding 10M+ faits |
| `wikidata_connector.py` | Connecteur Wikidata |
| `wikidata_streamer.py` | Streamer temps réel |
| `knowledge_enricher.py` | Enrichisseur de savoir (blocs explicatifs) |
| `bootstrapper.py` | Sevrage LLM + extraction triplets |

#### MULTIMODAL (priorité BASSE — autre pipeline)

| Module | Rôle |
|--------|------|
| `visual_encoder.py` | Image → ψ |
| `visual_generator.py` | ψ → image |
| `visual_memory.py` | Mémoire visuelle |
| `visual_trainer.py` | Entraînement visuel |
| `harmonic_codec.py` | Codec unifié HCV |
| `harmonic_database.py` | Base shardée DFT (1.2M patches) |
| `harmonic_media.py` | Moteur média unifié |
| `wave_audio.py` | Génération audio |
| `wave_renderer.py` | Rendu ondulatoire |
| `analyzers.py` | Analyseurs image/audio/vidéo |
| `nature_wave_engine.py` | Génération de scènes naturelles |

#### THÉORIE

| Module | Rôle |
|--------|------|
| `abc_kernel.py` | Noyau ABC (Atangana-Baleanu) |
| `signatures_9d.py` | Signatures harmoniques 9D |
| `sopc_core.py` | Sparse Oscillatory Predictive Coding |
| `math_bridge.py` | Pont mathématique |
| `harmonic_model.py` | Modèle I×P×H |
| `harmonic_engine.py` | Moteur harmonique (legacy) |
| `harmonic_resonator.py` | 7 principes du raisonnement ondulatoire |
| `jepa_connector.py` | Prédicteur JEPA-like |
| `abc_predictor_connector.py` | Prédicteur ABC pur |
| `harmonic7d.py` | Dimensions harmoniques |

#### VOIX (autre pipeline)

| Module | Rôle |
|--------|------|
| `phi_diffusion_engine.py` | Synthèse vocale Coqui/XTTS/Piper |
| `phi_piper_engine.py` | Wrapper Piper TTS |
| `phi_vocoder.py` | Vocodeur source-filtre |
| `phi_vocoder_calibrator.py` | Auto-calibration |
| `phi_vocoder_pro.py` | Post-filtre adaptatif φ |
| `phi_voice_cloner.py` | Clonage vocal |
| `voice_signature_extractor.py` | Extraction 11D |
| `harmonic_voice_trainer.py` | Entraîneur SpectralMessage → voix |
| `spectral_voice_pipeline.py` | Pipeline vocal complet |

---

## 🔥 PLAN DE BATAILLE — Par priorité

### PHASE 0 : Fondations (EN COURS)
- [x] Internet (web_retriever)
- [x] KB scalable (kb_scaler)
- [x] Raisonnement profond (phase_amplifier)
- [x] Few-shot (few_shot_injector)
- [ ] **Attention dynamique** (`harmonic_attention.py`) ← **MAINTENANT**

### PHASE 1 : Apprentissage continu (prochaine)
- [ ] Intégrer `wave_fine_tune.py` → Fourier ALS actif en continu
- [ ] Intégrer `fast_learner.py` → Auto-curriculum + spaced repetition
- [ ] Activer `feedback_loop.py` → RLHF ondulatoire complet
- [ ] Connecter `consolidate()` few-shot → fine-tune → feedback

### PHASE 2 : Raisonnement avancé
- [ ] Intégrer `counterfactual_reasoner.py` → « Et si... »
- [ ] Intégrer `paradox_detector.py` → Contradictions
- [ ] Intégrer `coherent_transitivity.py` → Fermeture transitive active
- [ ] Multi-branche avec backtracking

### PHASE 3 : Langage & Code
- [ ] Intégrer `wave_styler.py` → Style naturel varié
- [ ] Intégrer `cross_lingual.py` → Multilingue véritable
- [ ] Intégrer `code_generator.py` → Génération de code (89K lignes!)
- [ ] WaveDecoder → remonter dans le pipeline

### PHASE 4 : Couverture KB
- [ ] Wikidata dump réel → 10M+ faits
- [ ] Web crawling automatique → triplets
- [ ] `knowledge_enricher.py` → blocs explicatifs pour tous les sujets

### PHASE 5 : Multimodal
- [ ] Connecter `visual_encoder.py` → analyse d'images dans le chat
- [ ] Connecter `wave_audio.py` → analyse audio
- [ ] `harmonic_media.py` → unifié texte + image + audio

### PHASE 6 : Créativité & Émotion
- [ ] Intégrer `emotional_brain.py` → ton émotionnel
- [ ] Intégrer `creative_engine.py` → 6 opérations ⊛
- [ ] Intégrer `creative_dialogue.py` → dialogue créatif

---

## 📊 MÉTRIQUES DE PROGRESSION

| Phase | Modules intégrés | Nouveaux | Cumul |
|-------|:----------------:|:--------:|:-----:|
| 0 | 18 | — | 18 |
| 1 | +4 (fine-tune, learner, feedback, consolidate) | 4 | 22 |
| 2 | +3 (counterfactual, paradox, transitivity) | 3 | 25 |
| 3 | +4 (styler, cross-lingual, code, decoder) | 4 | 29 |
| 4 | +3 (wikidata, web crawl, enricher) | 3 | 32 |
| 5 | +3 (visual, audio, media) | 3 | 35 |
| 6 | +2 (emotional, creative) | 2 | 37 |

*Dernière mise à jour : 2026-07-14 10:45 — Après intégration web + kb + deep reason + few-shot*

---

## 🎯 PROCHAIN OBJECTIF : Attention Dynamique

**Équivalent LLM** : Transformer self-attention  
**Équivalent Harmonique** : ψ_contextuel = ψ_statique ⊕ modulation_locale(contexte)

**Pourquoi c'est critique** : La désambiguïsation (« avocat » fruit vs métier) et la compréhension fine du contexte dépendent de cela. Toute la Phase 1 (apprentissage) et Phase 2 (raisonnement avancé) bénéficieront d'une meilleure représentation contextuelle.

**Fichier à créer** : `engine/harmonic_attention.py`
